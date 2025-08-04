"""
Enhanced Spellcasting Calculator with new interface compliance.

This module provides an enhanced implementation of the spellcasting calculator
that implements the new calculator interfaces and provides improved functionality.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import time

from .interfaces.core import (
    ICalculator, IRuleAwareCalculator, ICachedCalculator, 
    CalculatorType, CalculationError, ValidationError, CalculatorConfig
)
from .services.interfaces import CalculationContext, CalculationResult, CalculationStatus
from .utils.math import DnDMath, MathUtils
from .utils.validation import CharacterDataValidator
from .base import RuleAwareCalculator
from ..rules.version_manager import RuleVersionManager


logger = logging.getLogger(__name__)


@dataclass
class SpellSlotData:
    """Data class for spell slot information."""
    level: int
    total_slots: int
    used_slots: int
    remaining_slots: int
    
    def __post_init__(self):
        if self.level < 1 or self.level > 9:
            raise ValueError(f"Spell level must be between 1 and 9, got {self.level}")
        if self.used_slots > self.total_slots:
            raise ValueError(f"Used slots ({self.used_slots}) cannot exceed total ({self.total_slots})")
        if self.remaining_slots != self.total_slots - self.used_slots:
            logger.warning(f"Remaining slots calculation mismatch: {self.remaining_slots} vs {self.total_slots - self.used_slots}")


@dataclass
class SpellcastingData:
    """Data class for comprehensive spellcasting information."""
    spellcasting_ability: str
    spellcasting_modifier: int
    spell_save_dc: int
    spell_attack_bonus: int
    spell_slots: Dict[int, SpellSlotData]
    cantrips_known: int
    spells_known: int
    spells_prepared: int
    highest_spell_level: int
    total_caster_level: int
    multiclass_caster_level: int
    ritual_casting: bool
    spellcasting_focus: List[str]
    
    def __post_init__(self):
        if self.spell_save_dc < 8 or self.spell_save_dc > 30:
            raise ValueError(f"Spell save DC must be between 8 and 30, got {self.spell_save_dc}")
        if self.highest_spell_level < 0 or self.highest_spell_level > 9:
            raise ValueError(f"Highest spell level must be between 0 and 9, got {self.highest_spell_level}")


class EnhancedSpellcastingCalculator(RuleAwareCalculator, ICachedCalculator):
    """
    Enhanced spellcasting calculator with new interface compliance.
    
    Features:
    - Full interface compliance with ICalculator, IRuleAwareCalculator, ICachedCalculator
    - Comprehensive spellcasting mechanics calculation
    - Multiclass spellcaster support
    - Enhanced validation and error handling
    - Performance monitoring and caching
    - Rule version support for spellcasting differences
    """
    
    def __init__(self, config_manager=None, rule_manager: Optional[RuleVersionManager] = None):
        """
        Initialize the enhanced spellcasting calculator.
        
        Args:
            config_manager: Configuration manager instance
            rule_manager: Rule version manager instance
        """
        super().__init__(config_manager, rule_manager)
        # Load configuration from main config system (uses performance.enable_caching)
        self.config = self.create_calculator_config_from_main(config_manager)
        self.validator = CharacterDataValidator()
        self.cache = {}
        self.cache_stats = {'hits': 0, 'misses': 0}
        
        # Initialize spellcasting constants
        self._setup_spellcasting_constants()
        
        # Performance tracking
        self.metrics = {
            'total_calculations': 0,
            'total_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'validation_failures': 0
        }
    
    def _setup_spellcasting_constants(self):
        """Setup spellcasting calculation constants."""
        # Spellcaster class progression
        self.full_casters = {
            'cleric': {'ability': 'wisdom', 'preparation': 'prepared'},
            'druid': {'ability': 'wisdom', 'preparation': 'prepared'},
            'sorcerer': {'ability': 'charisma', 'preparation': 'known'},
            'wizard': {'ability': 'intelligence', 'preparation': 'prepared'},
            'bard': {'ability': 'charisma', 'preparation': 'known'}
        }
        
        self.half_casters = {
            'paladin': {'ability': 'charisma', 'preparation': 'prepared', 'start_level': 2},
            'ranger': {'ability': 'wisdom', 'preparation': 'known', 'start_level': 2}
        }
        
        self.third_casters = {
            'eldritch knight': {'ability': 'intelligence', 'preparation': 'known', 'start_level': 3},
            'arcane trickster': {'ability': 'intelligence', 'preparation': 'known', 'start_level': 3}
        }
        
        self.warlock_progression = {
            'warlock': {'ability': 'charisma', 'preparation': 'known'}
        }
        
        # Spell slot progression tables
        self.full_caster_slots = {
            1: [2, 0, 0, 0, 0, 0, 0, 0, 0],
            2: [3, 0, 0, 0, 0, 0, 0, 0, 0],
            3: [4, 2, 0, 0, 0, 0, 0, 0, 0],
            4: [4, 3, 0, 0, 0, 0, 0, 0, 0],
            5: [4, 3, 2, 0, 0, 0, 0, 0, 0],
            6: [4, 3, 3, 0, 0, 0, 0, 0, 0],
            7: [4, 3, 3, 1, 0, 0, 0, 0, 0],
            8: [4, 3, 3, 2, 0, 0, 0, 0, 0],
            9: [4, 3, 3, 3, 1, 0, 0, 0, 0],
            10: [4, 3, 3, 3, 2, 0, 0, 0, 0],
            11: [4, 3, 3, 3, 2, 1, 0, 0, 0],
            12: [4, 3, 3, 3, 2, 1, 0, 0, 0],
            13: [4, 3, 3, 3, 2, 1, 1, 0, 0],
            14: [4, 3, 3, 3, 2, 1, 1, 0, 0],
            15: [4, 3, 3, 3, 2, 1, 1, 1, 0],
            16: [4, 3, 3, 3, 2, 1, 1, 1, 0],
            17: [4, 3, 3, 3, 2, 1, 1, 1, 1],
            18: [4, 3, 3, 3, 3, 1, 1, 1, 1],
            19: [4, 3, 3, 3, 3, 2, 1, 1, 1],
            20: [4, 3, 3, 3, 3, 2, 2, 1, 1]
        }
        
        # Ability ID mappings
        self.ability_id_map = {
            1: 'strength',
            2: 'dexterity', 
            3: 'constitution',
            4: 'intelligence',
            5: 'wisdom',
            6: 'charisma'
        }
    
    # ICalculator interface implementation
    @property
    def calculator_type(self) -> CalculatorType:
        """Get the type of this calculator."""
        return CalculatorType.SPELLCASTING
    
    @property
    def name(self) -> str:
        """Get the human-readable name of this calculator."""
        return "Enhanced Spellcasting Calculator"
    
    @property
    def version(self) -> str:
        """Get the version of this calculator."""
        return "2.0.0"
    
    @property
    def dependencies(self) -> List[CalculatorType]:
        """Get the list of calculator types this calculator depends on."""
        return [CalculatorType.ABILITY_SCORE]  # Needs ability scores for spellcasting modifier
    
    def calculate(self, character_data: Dict[str, Any], context: CalculationContext) -> CalculationResult:
        """
        Perform the calculation using the provided character data.
        
        Args:
            character_data: Raw character data from D&D Beyond
            context: Calculation context and configuration
            
        Returns:
            CalculationResult with computed data and metadata
        """
        start_time = time.time()
        self.metrics['total_calculations'] += 1
        
        try:
            # Validate input data
            is_valid, validation_errors = self.validate_input(character_data)
            if not is_valid:
                self.metrics['validation_failures'] += 1
                return CalculationResult(
                    service_name=self.name,
                    status=CalculationStatus.FAILED,
                    data={},
                    errors=validation_errors,
                    execution_time=time.time() - start_time
                )
            
            # Check cache
            cache_key = self.get_cache_key(character_data, context)
            if self.config.enable_caching:
                cached_result = self.get_from_cache(cache_key)
                if cached_result:
                    self.metrics['cache_hits'] += 1
                    self.cache_stats['hits'] += 1
                    return cached_result
            
            self.metrics['cache_misses'] += 1
            self.cache_stats['misses'] += 1
            
            # Perform calculation
            rule_version = self.get_rule_version(character_data)
            logger.debug(f"Calculating spellcasting with {rule_version.version.value} rules")
            
            # Calculate spellcasting
            spellcasting_data = self._calculate_spellcasting(character_data, rule_version)
            
            # Build result
            result_data = {
                'spellcasting_ability': spellcasting_data.spellcasting_ability,
                'spellcasting_modifier': spellcasting_data.spellcasting_modifier,
                'spell_save_dc': spellcasting_data.spell_save_dc,
                'spell_attack_bonus': spellcasting_data.spell_attack_bonus,
                'spell_slots': {
                    level: {
                        'total': slot_data.total_slots,
                        'used': slot_data.used_slots,
                        'remaining': slot_data.remaining_slots
                    } for level, slot_data in spellcasting_data.spell_slots.items()
                },
                'cantrips_known': spellcasting_data.cantrips_known,
                'spells_known': spellcasting_data.spells_known,
                'spells_prepared': spellcasting_data.spells_prepared,
                'highest_spell_level': spellcasting_data.highest_spell_level,
                'total_caster_level': spellcasting_data.total_caster_level,
                'multiclass_caster_level': spellcasting_data.multiclass_caster_level,
                'ritual_casting': spellcasting_data.ritual_casting,
                'spellcasting_focus': spellcasting_data.spellcasting_focus,
                'rule_version': rule_version.version.value
            }
            
            result = CalculationResult(
                service_name=self.name,
                status=CalculationStatus.COMPLETED,
                data=result_data,
                execution_time=time.time() - start_time
            )
            
            # Cache result
            if self.config.enable_caching:
                self.store_in_cache(cache_key, result)
            
            # Update metrics
            self.metrics['total_time'] += result.execution_time
            
            return result
            
        except Exception as e:
            logger.error(f"Error in spellcasting calculation: {str(e)}")
            return CalculationResult(
                service_name=self.name,
                status=CalculationStatus.FAILED,
                data={},
                errors=[str(e)],
                execution_time=time.time() - start_time
            )
    
    def validate_input(self, character_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that the input data is suitable for this calculator.
        
        Args:
            character_data: Character data to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check basic structure
        if not isinstance(character_data, dict):
            errors.append("Character data must be a dictionary")
            return False, errors
        
        # Check for classes (needed to determine spellcasting)
        if 'classes' not in character_data:
            errors.append("Missing required 'classes' field for spellcasting calculation")
        else:
            classes = character_data['classes']
            if not isinstance(classes, list):
                errors.append("'classes' field must be a list")
        
        # Check for stats (needed for spellcasting ability modifier)
        if 'stats' not in character_data:
            errors.append("Missing required 'stats' field for spellcasting modifier calculation")
        else:
            stats = character_data['stats']
            if not isinstance(stats, list):
                errors.append("'stats' field must be a list")
        
        # Use validator for additional checks
        validation_result = self.validator.validate(character_data)
        if not validation_result.is_valid:
            errors.extend([msg.message for msg in validation_result.messages])
        
        return len(errors) == 0, errors
    
    def get_output_schema(self) -> Dict[str, Any]:
        """
        Get the schema for data this calculator produces.
        
        Returns:
            JSONSchema describing the output data structure
        """
        return {
            "type": "object",
            "properties": {
                "spellcasting_ability": {"type": "string", "enum": ["intelligence", "wisdom", "charisma", "none"]},
                "spellcasting_modifier": {"type": "integer", "minimum": -5, "maximum": 15},
                "spell_save_dc": {"type": "integer", "minimum": 8, "maximum": 30},
                "spell_attack_bonus": {"type": "integer", "minimum": -5, "maximum": 25},
                "spell_slots": {
                    "type": "object",
                    "patternProperties": {
                        "^[1-9]$": {
                            "type": "object",
                            "properties": {
                                "total": {"type": "integer", "minimum": 0},
                                "used": {"type": "integer", "minimum": 0},
                                "remaining": {"type": "integer", "minimum": 0}
                            },
                            "required": ["total", "used", "remaining"]
                        }
                    }
                },
                "cantrips_known": {"type": "integer", "minimum": 0},
                "spells_known": {"type": "integer", "minimum": 0},
                "spells_prepared": {"type": "integer", "minimum": 0},
                "highest_spell_level": {"type": "integer", "minimum": 0, "maximum": 9},
                "total_caster_level": {"type": "integer", "minimum": 0},
                "multiclass_caster_level": {"type": "integer", "minimum": 0},
                "ritual_casting": {"type": "boolean"},
                "spellcasting_focus": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "rule_version": {"type": "string", "enum": ["2014", "2024"]}
            },
            "required": ["spellcasting_ability", "spellcasting_modifier", "spell_save_dc", "spell_attack_bonus", "spell_slots", "cantrips_known", "spells_known", "spells_prepared", "highest_spell_level", "total_caster_level", "multiclass_caster_level", "ritual_casting", "spellcasting_focus", "rule_version"]
        }
    
    def get_required_fields(self) -> List[str]:
        """
        Get the list of required fields in the input data.
        
        Returns:
            List of required field names
        """
        return ['classes', 'stats']
    
    def get_optional_fields(self) -> List[str]:
        """
        Get the list of optional fields in the input data.
        
        Returns:
            List of optional field names
        """
        return ['spells', 'race', 'feats', 'modifiers']
    
    def supports_rule_version(self, rule_version: str) -> bool:
        """
        Check if this calculator supports the specified rule version.
        
        Args:
            rule_version: Rule version to check (e.g., "2014", "2024")
            
        Returns:
            True if rule version is supported
        """
        return rule_version in ["2014", "2024"]
    
    def get_cache_key(self, character_data: Dict[str, Any], context: CalculationContext) -> str:
        """
        Generate a cache key for the given inputs.
        
        Args:
            character_data: Character data
            context: Calculation context
            
        Returns:
            Cache key string
        """
        import hashlib
        import json
        
        # Extract relevant fields for caching
        cache_data = {
            'classes': character_data.get('classes', []),
            'stats': character_data.get('stats', []),
            'spells': character_data.get('spells', []),
            'modifiers': character_data.get('modifiers', {}),
            'rule_version': context.rule_version,
            'character_id': context.character_id
        }
        
        # Sort keys for consistent hashing
        cache_json = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_json.encode()).hexdigest()
        
        return f"spellcasting_{cache_hash}"
    
    # ICachedCalculator interface implementation
    def get_from_cache(self, cache_key: str) -> Optional[CalculationResult]:
        """Get calculation result from cache."""
        return self.cache.get(cache_key)
    
    def store_in_cache(self, cache_key: str, result: CalculationResult, ttl: Optional[int] = None) -> None:
        """Store calculation result in cache."""
        self.cache[cache_key] = result
        
        # Simple cache size management
        if len(self.cache) > 1000:
            keys_to_remove = list(self.cache.keys())[:100]
            for key in keys_to_remove:
                del self.cache[key]
    
    def invalidate_cache(self, cache_key: str) -> None:
        """Invalidate cached result."""
        if cache_key in self.cache:
            del self.cache[cache_key]
    
    def clear_cache(self) -> None:
        """Clear all cached results for this calculator."""
        self.cache.clear()
        self.cache_stats = {'hits': 0, 'misses': 0}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'hit_rate': self.cache_stats['hits'] / (self.cache_stats['hits'] + self.cache_stats['misses']) if (self.cache_stats['hits'] + self.cache_stats['misses']) > 0 else 0,
            'cache_size': len(self.cache)
        }
    
    def configure(self, config: CalculatorConfig) -> None:
        """Configure calculator behavior."""
        self.config = config
        self.validator = CharacterDataValidator()
    
    def get_configuration(self) -> CalculatorConfig:
        """Get current calculator configuration."""
        return self.config
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for this calculator."""
        return {
            'total_calculations': self.metrics['total_calculations'],
            'total_time': self.metrics['total_time'],
            'average_time': self.metrics['total_time'] / self.metrics['total_calculations'] if self.metrics['total_calculations'] > 0 else 0,
            'cache_hits': self.metrics['cache_hits'],
            'cache_misses': self.metrics['cache_misses'],
            'validation_failures': self.metrics['validation_failures']
        }
    
    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self.metrics = {
            'total_calculations': 0,
            'total_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'validation_failures': 0
        }
    
    # Core calculation methods
    def _calculate_spellcasting(self, character_data: Dict[str, Any], rule_version) -> SpellcastingData:
        """
        Calculate spellcasting with comprehensive breakdown.
        
        Args:
            character_data: Character data from D&D Beyond
            rule_version: Detected rule version
            
        Returns:
            SpellcastingData object with complete breakdown
        """
        # Check if character has spellcasting
        spellcasting_classes = self._get_spellcasting_classes(character_data)
        
        if not spellcasting_classes:
            # No spellcasting
            return self._create_non_caster_data()
        
        # Determine primary spellcasting ability
        primary_ability = self._get_primary_spellcasting_ability(spellcasting_classes)
        
        # Get spellcasting modifier
        spellcasting_modifier = self._get_spellcasting_modifier(character_data, primary_ability)
        proficiency_bonus = self._get_proficiency_bonus(character_data)
        
        # Calculate spell save DC and attack bonus
        spell_save_dc = 8 + proficiency_bonus + spellcasting_modifier
        spell_attack_bonus = proficiency_bonus + spellcasting_modifier
        
        # Calculate caster levels
        total_caster_level, multiclass_caster_level = self._calculate_caster_levels(spellcasting_classes)
        
        # Calculate spell slots
        spell_slots = self._calculate_spell_slots(spellcasting_classes, multiclass_caster_level)
        
        # Calculate spells known/prepared
        cantrips_known = self._calculate_cantrips_known(spellcasting_classes)
        spells_known = self._calculate_spells_known(spellcasting_classes)
        spells_prepared = self._calculate_spells_prepared(spellcasting_classes, spellcasting_modifier)
        
        # Get highest spell level
        highest_spell_level = max(spell_slots.keys()) if spell_slots else 0
        
        # Check for ritual casting
        ritual_casting = self._has_ritual_casting(spellcasting_classes)
        
        # Get spellcasting focus
        spellcasting_focus = self._get_spellcasting_focus(spellcasting_classes, character_data)
        
        return SpellcastingData(
            spellcasting_ability=primary_ability,
            spellcasting_modifier=spellcasting_modifier,
            spell_save_dc=spell_save_dc,
            spell_attack_bonus=spell_attack_bonus,
            spell_slots=spell_slots,
            cantrips_known=cantrips_known,
            spells_known=spells_known,
            spells_prepared=spells_prepared,
            highest_spell_level=highest_spell_level,
            total_caster_level=total_caster_level,
            multiclass_caster_level=multiclass_caster_level,
            ritual_casting=ritual_casting,
            spellcasting_focus=spellcasting_focus
        )
    
    def _get_spellcasting_classes(self, character_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get list of classes that grant spellcasting."""
        classes = character_data.get('classes', [])
        spellcasting_classes = []
        
        for class_data in classes:
            class_name = class_data.get('definition', {}).get('name', '').lower()
            class_level = class_data.get('level', 1)
            
            # Check if class grants spellcasting
            if any(caster in class_name for caster in self.full_casters.keys()):
                spellcasting_classes.append({
                    'class_data': class_data,
                    'class_name': class_name,
                    'class_level': class_level,
                    'caster_type': 'full'
                })
            elif any(caster in class_name for caster in self.half_casters.keys()):
                spellcasting_classes.append({
                    'class_data': class_data,
                    'class_name': class_name,
                    'class_level': class_level,
                    'caster_type': 'half'
                })
            elif any(caster in class_name for caster in self.third_casters.keys()):
                spellcasting_classes.append({
                    'class_data': class_data,
                    'class_name': class_name,
                    'class_level': class_level,
                    'caster_type': 'third'
                })
            elif 'warlock' in class_name:
                spellcasting_classes.append({
                    'class_data': class_data,
                    'class_name': class_name,
                    'class_level': class_level,
                    'caster_type': 'warlock'
                })
        
        return spellcasting_classes
    
    def _create_non_caster_data(self) -> SpellcastingData:
        """Create spellcasting data for non-spellcasters."""
        return SpellcastingData(
            spellcasting_ability="none",
            spellcasting_modifier=0,
            spell_save_dc=8,
            spell_attack_bonus=0,
            spell_slots={},
            cantrips_known=0,
            spells_known=0,
            spells_prepared=0,
            highest_spell_level=0,
            total_caster_level=0,
            multiclass_caster_level=0,
            ritual_casting=False,
            spellcasting_focus=[]
        )
    
    def _get_primary_spellcasting_ability(self, spellcasting_classes: List[Dict[str, Any]]) -> str:
        """Get primary spellcasting ability for multiclass characters."""
        if not spellcasting_classes:
            return "none"
        
        # For single class, return that class's ability
        if len(spellcasting_classes) == 1:
            class_name = spellcasting_classes[0]['class_name']
            return self._get_class_spellcasting_ability(class_name)
        
        # For multiclass, prioritize full casters, then highest level
        full_casters = [c for c in spellcasting_classes if c['caster_type'] == 'full']
        if full_casters:
            highest_level_caster = max(full_casters, key=lambda x: x['class_level'])
            return self._get_class_spellcasting_ability(highest_level_caster['class_name'])
        
        # Fall back to highest level caster
        highest_level_caster = max(spellcasting_classes, key=lambda x: x['class_level'])
        return self._get_class_spellcasting_ability(highest_level_caster['class_name'])
    
    def _get_class_spellcasting_ability(self, class_name: str) -> str:
        """Get spellcasting ability for a specific class."""
        class_name = class_name.lower()
        
        for caster_dict in [self.full_casters, self.half_casters, self.third_casters, self.warlock_progression]:
            for caster_class, info in caster_dict.items():
                if caster_class in class_name:
                    return info['ability']
        
        return "intelligence"  # Default fallback
    
    def _get_spellcasting_modifier(self, character_data: Dict[str, Any], ability_name: str) -> int:
        """Get spellcasting modifier for the specified ability."""
        if ability_name == "none":
            return 0
        
        stats = character_data.get('stats', [])
        
        # Map ability name to ID
        ability_id = None
        for aid, aname in self.ability_id_map.items():
            if aname == ability_name:
                ability_id = aid
                break
        
        if ability_id is None:
            return 0
        
        # Find the ability score
        for stat in stats:
            if stat.get('id') == ability_id:
                score = stat.get('value', 10)
                return DnDMath.ability_modifier(score)
        
        return 0
    
    def _get_proficiency_bonus(self, character_data: Dict[str, Any]) -> int:
        """Get character's proficiency bonus based on level."""
        classes = character_data.get('classes', [])
        total_level = sum(cls.get('level', 0) for cls in classes) or 1
        return DnDMath.proficiency_bonus(total_level)
    
    def _calculate_caster_levels(self, spellcasting_classes: List[Dict[str, Any]]) -> Tuple[int, int]:
        """Calculate total and multiclass caster levels."""
        total_caster_level = 0
        multiclass_caster_level = 0
        
        for class_info in spellcasting_classes:
            class_level = class_info['class_level']
            caster_type = class_info['caster_type']
            
            total_caster_level += class_level
            
            if caster_type == 'full':
                multiclass_caster_level += class_level
            elif caster_type == 'half':
                multiclass_caster_level += max(1, class_level // 2)
            elif caster_type == 'third':
                multiclass_caster_level += max(1, class_level // 3)
            # Warlock doesn't contribute to multiclass caster level
        
        return total_caster_level, multiclass_caster_level
    
    def _calculate_spell_slots(self, spellcasting_classes: List[Dict[str, Any]], multiclass_caster_level: int) -> Dict[int, SpellSlotData]:
        """Calculate spell slots for all spell levels."""
        spell_slots = {}
        
        # Use multiclass caster level for spell slot calculation
        if multiclass_caster_level > 0:
            caster_level = min(multiclass_caster_level, 20)
            if caster_level in self.full_caster_slots:
                slots_by_level = self.full_caster_slots[caster_level]
                
                for level, total_slots in enumerate(slots_by_level, 1):
                    if total_slots > 0:
                        spell_slots[level] = SpellSlotData(
                            level=level,
                            total_slots=total_slots,
                            used_slots=0,  # Would need to track usage
                            remaining_slots=total_slots
                        )
        
        # Add Warlock spell slots (separate progression)
        warlock_classes = [c for c in spellcasting_classes if c['caster_type'] == 'warlock']
        if warlock_classes:
            warlock_level = max(c['class_level'] for c in warlock_classes)
            warlock_slots = self._calculate_warlock_slots(warlock_level)
            
            # Warlock slots don't stack with other classes
            if not spell_slots:  # Only if no other spell slots
                spell_slots.update(warlock_slots)
        
        return spell_slots
    
    def _calculate_warlock_slots(self, warlock_level: int) -> Dict[int, SpellSlotData]:
        """Calculate Warlock pact magic slots."""
        # Warlock spell slot progression
        if warlock_level < 1:
            return {}
        elif warlock_level == 1:
            slot_level, num_slots = 1, 1
        elif warlock_level <= 2:
            slot_level, num_slots = 1, 2
        elif warlock_level <= 4:
            slot_level, num_slots = 2, 2
        elif warlock_level <= 6:
            slot_level, num_slots = 3, 2
        elif warlock_level <= 8:
            slot_level, num_slots = 4, 2
        elif warlock_level <= 10:
            slot_level, num_slots = 5, 2
        elif warlock_level <= 16:
            slot_level, num_slots = 5, 3
        else:
            slot_level, num_slots = 5, 4
        
        return {
            slot_level: SpellSlotData(
                level=slot_level,
                total_slots=num_slots,
                used_slots=0,
                remaining_slots=num_slots
            )
        }
    
    def _calculate_cantrips_known(self, spellcasting_classes: List[Dict[str, Any]]) -> int:
        """Calculate total cantrips known."""
        # Simplified calculation - would need class-specific tables
        total_cantrips = 0
        
        for class_info in spellcasting_classes:
            class_level = class_info['class_level']
            caster_type = class_info['caster_type']
            
            if caster_type == 'full':
                total_cantrips += min(4, 2 + (class_level - 1) // 4)
            elif caster_type in ['half', 'third']:
                total_cantrips += min(3, 1 + (class_level - 1) // 8)
            elif caster_type == 'warlock':
                total_cantrips += min(4, 2 + (class_level - 1) // 4)
        
        return total_cantrips
    
    def _calculate_spells_known(self, spellcasting_classes: List[Dict[str, Any]]) -> int:
        """Calculate total spells known (for known casters)."""
        # Simplified calculation - would need class-specific tables
        total_spells = 0
        
        for class_info in spellcasting_classes:
            class_level = class_info['class_level']
            class_name = class_info['class_name']
            
            # Only count for classes that learn spells
            if any(known_class in class_name for known_class in ['sorcerer', 'bard', 'ranger', 'warlock']):
                total_spells += class_level + 1
        
        return total_spells
    
    def _calculate_spells_prepared(self, spellcasting_classes: List[Dict[str, Any]], spellcasting_modifier: int) -> int:
        """Calculate total spells prepared (for prepared casters)."""
        total_prepared = 0
        
        for class_info in spellcasting_classes:
            class_level = class_info['class_level']
            class_name = class_info['class_name']
            
            # Only count for classes that prepare spells
            if any(prep_class in class_name for prep_class in ['cleric', 'druid', 'wizard', 'paladin']):
                prepared = class_level + max(1, spellcasting_modifier)
                total_prepared += prepared
        
        return total_prepared
    
    def _has_ritual_casting(self, spellcasting_classes: List[Dict[str, Any]]) -> bool:
        """Check if character has ritual casting."""
        for class_info in spellcasting_classes:
            class_name = class_info['class_name']
            # Most full casters have ritual casting
            if any(ritual_class in class_name for ritual_class in ['cleric', 'druid', 'wizard', 'bard']):
                return True
        
        return False
    
    def _get_spellcasting_focus(self, spellcasting_classes: List[Dict[str, Any]], character_data: Dict[str, Any]) -> List[str]:
        """Get list of valid spellcasting foci."""
        foci = []
        
        for class_info in spellcasting_classes:
            class_name = class_info['class_name']
            
            if 'cleric' in class_name or 'paladin' in class_name:
                foci.append('Holy Symbol')
            elif 'druid' in class_name:
                foci.append('Druidic Focus')
            elif 'sorcerer' in class_name or 'warlock' in class_name:
                foci.append('Arcane Focus')
            elif 'wizard' in class_name:
                foci.extend(['Arcane Focus', 'Spellbook'])
            elif 'bard' in class_name:
                foci.append('Musical Instrument')
        
        return list(set(foci))  # Remove duplicates