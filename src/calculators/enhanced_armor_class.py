"""
Enhanced Armor Class Calculator with new interface compliance.

This module provides an enhanced implementation of the armor class calculator
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
class ArmorClassData:
    """Data class for armor class information."""
    total_ac: int
    base_ac: int
    dex_bonus: int
    armor_bonus: int
    shield_bonus: int
    natural_armor: int
    deflection_bonus: int
    misc_bonus: int
    calculation_method: str
    dex_cap: Optional[int] = None
    
    def __post_init__(self):
        if self.total_ac < 1 or self.total_ac > 50:
            raise ValueError(f"Total AC must be between 1 and 50, got {self.total_ac}")
        
        # Validate that components add up correctly
        calculated_total = (self.base_ac + self.dex_bonus + self.armor_bonus + 
                          self.shield_bonus + self.natural_armor + 
                          self.deflection_bonus + self.misc_bonus)
        
        if abs(calculated_total - self.total_ac) > 1:  # Allow for rounding
            logger.warning(f"AC components don't add up: {calculated_total} vs {self.total_ac}")


class EnhancedArmorClassCalculator(RuleAwareCalculator, ICachedCalculator):
    """
    Enhanced armor class calculator with new interface compliance.
    
    Features:
    - Full interface compliance with ICalculator, IRuleAwareCalculator, ICachedCalculator
    - Comprehensive armor class calculation methods
    - Enhanced validation and error handling
    - Performance monitoring and caching
    - Detailed AC breakdown and method detection
    """
    
    def __init__(self, config_manager=None, rule_manager: Optional[RuleVersionManager] = None):
        """
        Initialize the enhanced armor class calculator.
        
        Args:
            config_manager: Configuration manager instance
            rule_manager: Rule version manager instance
        """
        super().__init__(config_manager, rule_manager)
        self.config = CalculatorConfig()
        self.validator = CharacterDataValidator()
        self.cache = {}
        self.cache_stats = {'hits': 0, 'misses': 0}
        
        # Initialize armor and AC constants
        self._setup_ac_constants()
        
        # Performance tracking
        self.metrics = {
            'total_calculations': 0,
            'total_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'validation_failures': 0
        }
    
    def _setup_ac_constants(self):
        """Setup AC calculation constants."""
        # Ability ID mappings
        self.ability_id_map = {
            1: 'strength',
            2: 'dexterity', 
            3: 'constitution',
            4: 'intelligence',
            5: 'wisdom',
            6: 'charisma'
        }
        
        # Armor types and their properties
        self.armor_types = {
            'light': {'dex_cap': None, 'stealth_disadvantage': False},
            'medium': {'dex_cap': 2, 'stealth_disadvantage': False},
            'heavy': {'dex_cap': 0, 'stealth_disadvantage': True}
        }
        
        # Unarmored Defense class features
        self.unarmored_defense_classes = {
            'barbarian': ['constitution'],
            'monk': ['wisdom'],
            'draconic_sorcerer': ['charisma']
        }
    
    # ICalculator interface implementation
    @property
    def calculator_type(self) -> CalculatorType:
        """Get the type of this calculator."""
        return CalculatorType.ARMOR_CLASS
    
    @property
    def name(self) -> str:
        """Get the human-readable name of this calculator."""
        return "Enhanced Armor Class Calculator"
    
    @property
    def version(self) -> str:
        """Get the version of this calculator."""
        return "2.0.0"
    
    @property
    def dependencies(self) -> List[CalculatorType]:
        """Get the list of calculator types this calculator depends on."""
        return [CalculatorType.ABILITY_SCORE]  # Needs DEX for AC calculation
    
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
            logger.debug(f"Calculating armor class with {rule_version.version.value} rules")
            
            # Calculate armor class
            ac_data = self._calculate_armor_class(character_data, rule_version)
            
            # Build result
            result_data = {
                'armor_class': ac_data.total_ac,
                'ac_breakdown': {
                    'base_ac': ac_data.base_ac,
                    'dex_bonus': ac_data.dex_bonus,
                    'armor_bonus': ac_data.armor_bonus,
                    'shield_bonus': ac_data.shield_bonus,
                    'natural_armor': ac_data.natural_armor,
                    'deflection_bonus': ac_data.deflection_bonus,
                    'misc_bonus': ac_data.misc_bonus
                },
                'calculation_method': ac_data.calculation_method,
                'dex_cap': ac_data.dex_cap,
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
            logger.error(f"Error in armor class calculation: {str(e)}")
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
        
        # Check for stats data (needed for DEX modifier)
        if 'stats' not in character_data:
            errors.append("Missing required 'stats' field for DEX modifier calculation")
        else:
            stats = character_data['stats']
            if not isinstance(stats, list):
                errors.append("'stats' field must be a list")
            elif len(stats) < 6:
                errors.append(f"Expected 6 ability scores, got {len(stats)}")
            else:
                # Check for DEX specifically
                dex_found = any(stat.get('id') == 2 for stat in stats if isinstance(stat, dict))
                if not dex_found:
                    errors.append("Dexterity score not found in stats")
        
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
                "armor_class": {"type": "integer", "minimum": 1, "maximum": 50},
                "ac_breakdown": {
                    "type": "object",
                    "properties": {
                        "base_ac": {"type": "integer"},
                        "dex_bonus": {"type": "integer"},
                        "armor_bonus": {"type": "integer"},
                        "shield_bonus": {"type": "integer"},
                        "natural_armor": {"type": "integer"},
                        "deflection_bonus": {"type": "integer"},
                        "misc_bonus": {"type": "integer"}
                    },
                    "required": ["base_ac", "dex_bonus", "armor_bonus", "shield_bonus", "natural_armor", "deflection_bonus", "misc_bonus"]
                },
                "calculation_method": {"type": "string"},
                "dex_cap": {"type": ["integer", "null"]},
                "rule_version": {"type": "string", "enum": ["2014", "2024"]}
            },
            "required": ["armor_class", "ac_breakdown", "calculation_method", "rule_version"]
        }
    
    def get_required_fields(self) -> List[str]:
        """
        Get the list of required fields in the input data.
        
        Returns:
            List of required field names
        """
        return ['stats']
    
    def get_optional_fields(self) -> List[str]:
        """
        Get the list of optional fields in the input data.
        
        Returns:
            List of optional field names
        """
        return ['inventory', 'equipment', 'modifiers', 'classes', 'feats', 'race']
    
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
            'stats': character_data.get('stats', []),
            'inventory': character_data.get('inventory', []),
            'equipment': character_data.get('equipment', {}),
            'modifiers': character_data.get('modifiers', {}),
            'classes': character_data.get('classes', []),
            'rule_version': context.rule_version,
            'character_id': context.character_id
        }
        
        # Sort keys for consistent hashing
        cache_json = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_json.encode()).hexdigest()
        
        return f"armor_class_{cache_hash}"
    
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
    def _calculate_armor_class(self, character_data: Dict[str, Any], rule_version) -> ArmorClassData:
        """
        Calculate armor class with comprehensive breakdown.
        
        Args:
            character_data: Character data from D&D Beyond
            rule_version: Detected rule version
            
        Returns:
            ArmorClassData object with complete breakdown
        """
        # Check for direct AC override first
        if 'armorClass' in character_data and isinstance(character_data['armorClass'], int):
            total_ac = character_data['armorClass']
            return ArmorClassData(
                total_ac=total_ac,
                base_ac=total_ac,
                dex_bonus=0,
                armor_bonus=0,
                shield_bonus=0,
                natural_armor=0,
                deflection_bonus=0,
                misc_bonus=0,
                calculation_method="api_override"
            )
        
        # Get dexterity modifier
        dex_modifier = self._get_dexterity_modifier(character_data)
        
        # Check for armor
        armor_info = self._get_equipped_armor_info(character_data)
        shield_bonus = self._get_shield_bonus(character_data)
        
        if armor_info['equipped']:
            # Wearing armor
            base_ac = armor_info['base_ac']
            armor_bonus = 0  # Base AC already includes armor
            dex_bonus = min(dex_modifier, armor_info['dex_cap']) if armor_info['dex_cap'] is not None else dex_modifier
            dex_bonus = max(0, dex_bonus)  # Can't be negative
            calculation_method = f"armored_{armor_info['type']}"
            dex_cap = armor_info['dex_cap']
        else:
            # Unarmored
            base_ac = 10
            armor_bonus = 0
            
            # Check for Unarmored Defense
            unarmored_bonus = self._get_unarmored_defense_bonus(character_data)
            if unarmored_bonus > 0:
                base_ac += unarmored_bonus
                calculation_method = "unarmored_defense"
            else:
                calculation_method = "unarmored"
            
            dex_bonus = max(0, dex_modifier)
            dex_cap = None
        
        # Get other bonuses
        natural_armor = self._get_natural_armor_bonus(character_data)
        deflection_bonus = self._get_deflection_bonus(character_data)
        misc_bonus = self._get_misc_ac_bonus(character_data)
        
        # Calculate total
        total_ac = base_ac + dex_bonus + armor_bonus + shield_bonus + natural_armor + deflection_bonus + misc_bonus
        
        return ArmorClassData(
            total_ac=total_ac,
            base_ac=base_ac,
            dex_bonus=dex_bonus,
            armor_bonus=armor_bonus,
            shield_bonus=shield_bonus,
            natural_armor=natural_armor,
            deflection_bonus=deflection_bonus,
            misc_bonus=misc_bonus,
            calculation_method=calculation_method,
            dex_cap=dex_cap
        )
    
    def _get_dexterity_modifier(self, character_data: Dict[str, Any]) -> int:
        """Get dexterity modifier from character stats."""
        stats = character_data.get('stats', [])
        
        for stat in stats:
            if stat.get('id') == 2:  # Dexterity ID
                dex_score = stat.get('value', 10)
                return DnDMath.ability_modifier(dex_score)
        
        return 0  # Default if not found
    
    def _get_equipped_armor_info(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about equipped armor."""
        inventory = character_data.get('inventory', [])
        
        for item in inventory:
            if not isinstance(item, dict):
                continue
                
            if item.get('equipped', False) and item.get('definition', {}).get('filterType') == 'Armor':
                armor_def = item['definition']
                armor_class = armor_def.get('armorClass', 0)
                armor_type = armor_def.get('armorTypeId', 0)
                
                # Map armor type ID to type name and properties
                if armor_type in [1, 2, 3]:  # Light armor
                    armor_type_name = 'light'
                    dex_cap = None
                elif armor_type in [4, 5, 6]:  # Medium armor
                    armor_type_name = 'medium'
                    dex_cap = 2
                elif armor_type in [7, 8, 9]:  # Heavy armor
                    armor_type_name = 'heavy'
                    dex_cap = 0
                else:
                    armor_type_name = 'unknown'
                    dex_cap = None
                
                return {
                    'equipped': True,
                    'base_ac': armor_class,
                    'type': armor_type_name,
                    'dex_cap': dex_cap,
                    'name': armor_def.get('name', 'Unknown Armor')
                }
        
        return {
            'equipped': False,
            'base_ac': 0,
            'type': None,
            'dex_cap': None,
            'name': None
        }
    
    def _get_shield_bonus(self, character_data: Dict[str, Any]) -> int:
        """Get AC bonus from equipped shields."""
        inventory = character_data.get('inventory', [])
        shield_bonus = 0
        
        for item in inventory:
            if not isinstance(item, dict):
                continue
                
            if item.get('equipped', False) and item.get('definition', {}).get('filterType') == 'Armor':
                armor_def = item['definition']
                if armor_def.get('armorTypeId') == 4:  # Shield
                    shield_bonus += armor_def.get('armorClass', 0)
        
        return shield_bonus
    
    def _get_unarmored_defense_bonus(self, character_data: Dict[str, Any]) -> int:
        """Get Unarmored Defense bonus from class features."""
        classes = character_data.get('classes', [])
        bonus = 0
        
        for class_data in classes:
            class_name = class_data.get('definition', {}).get('name', '').lower()
            
            # Check for Barbarian Unarmored Defense (CON)
            if 'barbarian' in class_name:
                con_mod = self._get_ability_modifier(character_data, 3)  # Constitution
                bonus = max(bonus, con_mod)
            
            # Check for Monk Unarmored Defense (WIS)
            elif 'monk' in class_name:
                wis_mod = self._get_ability_modifier(character_data, 5)  # Wisdom
                bonus = max(bonus, wis_mod)
            
            # Check for Draconic Sorcerer (CHA)
            elif 'sorcerer' in class_name:
                # Check for Draconic Bloodline
                subclass = class_data.get('subclassDefinition', {}).get('name', '')
                if 'draconic' in subclass.lower():
                    cha_mod = self._get_ability_modifier(character_data, 6)  # Charisma
                    bonus = max(bonus, cha_mod)
        
        return max(0, bonus)
    
    def _get_ability_modifier(self, character_data: Dict[str, Any], ability_id: int) -> int:
        """Get ability modifier for a specific ability."""
        stats = character_data.get('stats', [])
        
        for stat in stats:
            if stat.get('id') == ability_id:
                score = stat.get('value', 10)
                return DnDMath.ability_modifier(score)
        
        return 0
    
    def _get_natural_armor_bonus(self, character_data: Dict[str, Any]) -> int:
        """Get natural armor bonus from race or other sources."""
        # Check modifiers for natural armor bonuses
        modifiers = character_data.get('modifiers', {})
        bonus = 0
        
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                if self._is_natural_armor_modifier(modifier):
                    bonus += modifier.get('value', 0)
        
        return bonus
    
    def _get_deflection_bonus(self, character_data: Dict[str, Any]) -> int:
        """Get deflection bonus from magic items or spells."""
        # This would typically come from magic items or temporary effects
        # For now, return 0 as this is rare
        return 0
    
    def _get_misc_ac_bonus(self, character_data: Dict[str, Any]) -> int:
        """Get miscellaneous AC bonuses."""
        # Check modifiers for other AC bonuses
        modifiers = character_data.get('modifiers', {})
        bonus = 0
        
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                if self._is_ac_modifier(modifier) and not self._is_natural_armor_modifier(modifier):
                    bonus += modifier.get('value', 0)
        
        return bonus
    
    def _is_natural_armor_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if modifier provides natural armor."""
        sub_type = modifier.get('subType', '').lower()
        return 'natural-armor' in sub_type or 'natural_armor' in sub_type
    
    def _is_ac_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if modifier affects AC."""
        modifies_type_id = modifier.get('modifiesTypeId')
        sub_type = modifier.get('subType', '').lower()
        
        # AC modifier type ID (1 = AC in D&D Beyond)
        if modifies_type_id == 1:
            return True
            
        # Check subtype for AC modifiers
        if 'armor-class' in sub_type or 'ac' in sub_type:
            return True
            
        return False