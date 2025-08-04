"""
Enhanced Proficiency Calculator with new interface compliance.

This module provides an enhanced implementation of the proficiency calculator
that implements the new calculator interfaces and provides improved functionality.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Set
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
class ProficiencyData:
    """Data class for proficiency information."""
    proficiency_bonus: int
    skill_proficiencies: Dict[str, int]
    saving_throw_proficiencies: Dict[str, int]
    tool_proficiencies: List[str]
    language_proficiencies: List[str]
    weapon_proficiencies: List[str]
    armor_proficiencies: List[str]
    expertise_skills: List[str]
    half_proficiencies: List[str]
    double_proficiencies: List[str]
    
    def __post_init__(self):
        if self.proficiency_bonus < 2 or self.proficiency_bonus > 6:
            raise ValueError(f"Proficiency bonus must be between 2 and 6, got {self.proficiency_bonus}")


class EnhancedProficiencyCalculator(RuleAwareCalculator, ICachedCalculator):
    """
    Enhanced proficiency calculator with new interface compliance.
    
    Features:
    - Full interface compliance with ICalculator, IRuleAwareCalculator, ICachedCalculator
    - Comprehensive proficiency tracking (skills, saves, tools, languages, weapons, armor)
    - Expertise and half-proficiency support
    - Enhanced validation and error handling
    - Performance monitoring and caching
    - Rule version support for proficiency differences
    """
    
    def __init__(self, config_manager=None, rule_manager: Optional[RuleVersionManager] = None):
        """
        Initialize the enhanced proficiency calculator.
        
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
        
        # Initialize proficiency constants
        self._setup_proficiency_constants()
        
        # Performance tracking
        self.metrics = {
            'total_calculations': 0,
            'total_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'validation_failures': 0
        }
    
    def _setup_proficiency_constants(self):
        """Setup proficiency calculation constants."""
        # Skill to ability mappings
        self.skill_abilities = {
            'acrobatics': 'dexterity',
            'animal_handling': 'wisdom',
            'arcana': 'intelligence',
            'athletics': 'strength',
            'deception': 'charisma',
            'history': 'intelligence',
            'insight': 'wisdom',
            'intimidation': 'charisma',
            'investigation': 'intelligence',
            'medicine': 'wisdom',
            'nature': 'intelligence',
            'perception': 'wisdom',
            'performance': 'charisma',
            'persuasion': 'charisma',
            'religion': 'intelligence',
            'sleight_of_hand': 'dexterity',
            'stealth': 'dexterity',
            'survival': 'wisdom'
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
        
        # Class skill proficiencies
        self.class_skills = {
            'barbarian': ['animal_handling', 'athletics', 'intimidation', 'nature', 'perception', 'survival'],
            'bard': ['any'],  # Bards get any 3 skills
            'cleric': ['history', 'insight', 'medicine', 'persuasion', 'religion'],
            'druid': ['arcana', 'animal_handling', 'insight', 'medicine', 'nature', 'perception', 'religion', 'survival'],
            'fighter': ['acrobatics', 'animal_handling', 'athletics', 'history', 'insight', 'intimidation', 'perception', 'survival'],
            'monk': ['acrobatics', 'athletics', 'history', 'insight', 'religion', 'stealth'],
            'paladin': ['athletics', 'insight', 'intimidation', 'medicine', 'persuasion', 'religion'],
            'ranger': ['animal_handling', 'athletics', 'insight', 'investigation', 'nature', 'perception', 'stealth', 'survival'],
            'rogue': ['acrobatics', 'athletics', 'deception', 'insight', 'intimidation', 'investigation', 'perception', 'performance', 'persuasion', 'sleight_of_hand', 'stealth'],
            'sorcerer': ['arcana', 'deception', 'insight', 'intimidation', 'persuasion', 'religion'],
            'warlock': ['arcana', 'deception', 'history', 'intimidation', 'investigation', 'nature', 'religion'],
            'wizard': ['arcana', 'history', 'insight', 'investigation', 'medicine', 'religion']
        }
        
        # Background skill proficiencies
        self.background_skills = {
            'acolyte': ['insight', 'religion'],
            'criminal': ['deception', 'stealth'],
            'folk_hero': ['animal_handling', 'survival'],
            'noble': ['history', 'persuasion'],
            'sage': ['arcana', 'history'],
            'soldier': ['athletics', 'intimidation']
        }
    
    # ICalculator interface implementation
    @property
    def calculator_type(self) -> CalculatorType:
        """Get the type of this calculator."""
        return CalculatorType.PROFICIENCY
    
    @property
    def name(self) -> str:
        """Get the human-readable name of this calculator."""
        return "Enhanced Proficiency Calculator"
    
    @property
    def version(self) -> str:
        """Get the version of this calculator."""
        return "2.0.0"
    
    @property
    def dependencies(self) -> List[CalculatorType]:
        """Get the list of calculator types this calculator depends on."""
        return [CalculatorType.ABILITY_SCORE]  # Needs ability scores for skill bonuses
    
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
            logger.debug(f"Calculating proficiencies with {rule_version.version.value} rules")
            
            # Calculate proficiencies
            proficiency_data = self._calculate_proficiencies(character_data, rule_version)
            
            # Build result
            result_data = {
                'proficiency_bonus': proficiency_data.proficiency_bonus,
                'skill_proficiencies': proficiency_data.skill_proficiencies,
                'saving_throw_proficiencies': proficiency_data.saving_throw_proficiencies,
                'tool_proficiencies': proficiency_data.tool_proficiencies,
                'language_proficiencies': proficiency_data.language_proficiencies,
                'weapon_proficiencies': proficiency_data.weapon_proficiencies,
                'armor_proficiencies': proficiency_data.armor_proficiencies,
                'expertise_skills': proficiency_data.expertise_skills,
                'half_proficiencies': proficiency_data.half_proficiencies,
                'double_proficiencies': proficiency_data.double_proficiencies,
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
            logger.error(f"Error in proficiency calculation: {str(e)}")
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
        
        # Check for classes (needed for proficiency bonus calculation)
        if 'classes' not in character_data:
            errors.append("Missing required 'classes' field for proficiency calculation")
        else:
            classes = character_data['classes']
            if not isinstance(classes, list):
                errors.append("'classes' field must be a list")
        
        # Check for stats (needed for skill bonuses)
        if 'stats' not in character_data:
            errors.append("Missing required 'stats' field for skill bonus calculation")
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
                "proficiency_bonus": {"type": "integer", "minimum": 2, "maximum": 6},
                "skill_proficiencies": {
                    "type": "object",
                    "patternProperties": {
                        "^[a-z_]+$": {"type": "integer"}
                    }
                },
                "saving_throw_proficiencies": {
                    "type": "object",
                    "properties": {
                        "strength": {"type": "integer"},
                        "dexterity": {"type": "integer"},
                        "constitution": {"type": "integer"},
                        "intelligence": {"type": "integer"},
                        "wisdom": {"type": "integer"},
                        "charisma": {"type": "integer"}
                    }
                },
                "tool_proficiencies": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "language_proficiencies": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "weapon_proficiencies": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "armor_proficiencies": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "expertise_skills": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "half_proficiencies": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "double_proficiencies": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "rule_version": {"type": "string", "enum": ["2014", "2024"]}
            },
            "required": ["proficiency_bonus", "skill_proficiencies", "saving_throw_proficiencies", "tool_proficiencies", "language_proficiencies", "weapon_proficiencies", "armor_proficiencies", "expertise_skills", "half_proficiencies", "double_proficiencies", "rule_version"]
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
        return ['background', 'race', 'feats', 'modifiers']
    
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
            'background': character_data.get('background', {}),
            'race': character_data.get('race', {}),
            'feats': character_data.get('feats', []),
            'modifiers': character_data.get('modifiers', {}),
            'rule_version': context.rule_version,
            'character_id': context.character_id
        }
        
        # Sort keys for consistent hashing
        cache_json = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_json.encode()).hexdigest()
        
        return f"proficiency_{cache_hash}"
    
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
    def _calculate_proficiencies(self, character_data: Dict[str, Any], rule_version) -> ProficiencyData:
        """
        Calculate proficiencies with comprehensive breakdown.
        
        Args:
            character_data: Character data from D&D Beyond
            rule_version: Detected rule version
            
        Returns:
            ProficiencyData object with complete breakdown
        """
        # Calculate proficiency bonus
        proficiency_bonus = self._get_proficiency_bonus(character_data)
        
        # Get ability modifiers
        ability_modifiers = self._get_ability_modifiers(character_data)
        
        # Calculate skill proficiencies
        skill_proficiencies = self._calculate_skill_proficiencies(character_data, ability_modifiers, proficiency_bonus)
        
        # Calculate saving throw proficiencies
        saving_throw_proficiencies = self._calculate_saving_throw_proficiencies(character_data, ability_modifiers, proficiency_bonus)
        
        # Get other proficiencies
        tool_proficiencies = self._get_tool_proficiencies(character_data)
        language_proficiencies = self._get_language_proficiencies(character_data)
        weapon_proficiencies = self._get_weapon_proficiencies(character_data)
        armor_proficiencies = self._get_armor_proficiencies(character_data)
        
        # Get special proficiency types
        expertise_skills = self._get_expertise_skills(character_data)
        half_proficiencies = self._get_half_proficiencies(character_data)
        double_proficiencies = self._get_double_proficiencies(character_data)
        
        return ProficiencyData(
            proficiency_bonus=proficiency_bonus,
            skill_proficiencies=skill_proficiencies,
            saving_throw_proficiencies=saving_throw_proficiencies,
            tool_proficiencies=tool_proficiencies,
            language_proficiencies=language_proficiencies,
            weapon_proficiencies=weapon_proficiencies,
            armor_proficiencies=armor_proficiencies,
            expertise_skills=expertise_skills,
            half_proficiencies=half_proficiencies,
            double_proficiencies=double_proficiencies
        )
    
    def _get_proficiency_bonus(self, character_data: Dict[str, Any]) -> int:
        """Get character's proficiency bonus based on level."""
        classes = character_data.get('classes', [])
        total_level = sum(cls.get('level', 0) for cls in classes) or 1
        return DnDMath.proficiency_bonus(total_level)
    
    def _get_ability_modifiers(self, character_data: Dict[str, Any]) -> Dict[str, int]:
        """Get all ability modifiers."""
        ability_modifiers = {}
        stats = character_data.get('stats', [])
        
        for stat in stats:
            ability_id = stat.get('id')
            if ability_id in self.ability_id_map:
                ability_name = self.ability_id_map[ability_id]
                score = stat.get('value', 10)
                ability_modifiers[ability_name] = DnDMath.ability_modifier(score)
        
        return ability_modifiers
    
    def _calculate_skill_proficiencies(self, character_data: Dict[str, Any], ability_modifiers: Dict[str, int], proficiency_bonus: int) -> Dict[str, int]:
        """Calculate skill proficiency bonuses."""
        skill_proficiencies = {}
        
        # Get proficient skills
        proficient_skills = self._get_proficient_skills(character_data)
        expertise_skills = self._get_expertise_skills(character_data)
        half_prof_skills = self._get_half_proficiencies(character_data)
        
        # Calculate bonuses for all skills
        for skill, ability in self.skill_abilities.items():
            ability_mod = ability_modifiers.get(ability, 0)
            
            if skill in expertise_skills:
                # Expertise: double proficiency bonus
                bonus = ability_mod + (proficiency_bonus * 2)
            elif skill in proficient_skills:
                # Regular proficiency
                bonus = ability_mod + proficiency_bonus
            elif skill in half_prof_skills:
                # Half proficiency (Jack of All Trades, etc.)
                bonus = ability_mod + (proficiency_bonus // 2)
            else:
                # No proficiency
                bonus = ability_mod
            
            skill_proficiencies[skill] = bonus
        
        return skill_proficiencies
    
    def _calculate_saving_throw_proficiencies(self, character_data: Dict[str, Any], ability_modifiers: Dict[str, int], proficiency_bonus: int) -> Dict[str, int]:
        """Calculate saving throw proficiency bonuses."""
        saving_throw_proficiencies = {}
        
        # Get proficient saving throws
        proficient_saves = self._get_proficient_saving_throws(character_data)
        
        # Calculate bonuses for all abilities
        for ability in self.ability_id_map.values():
            ability_mod = ability_modifiers.get(ability, 0)
            
            if ability in proficient_saves:
                bonus = ability_mod + proficiency_bonus
            else:
                bonus = ability_mod
            
            saving_throw_proficiencies[ability] = bonus
        
        return saving_throw_proficiencies
    
    def _get_proficient_skills(self, character_data: Dict[str, Any]) -> Set[str]:
        """Get set of skills the character is proficient in."""
        proficient_skills = set()
        
        # Add class skill proficiencies
        classes = character_data.get('classes', [])
        for class_data in classes:
            class_name = class_data.get('definition', {}).get('name', '').lower()
            # This would need to be parsed from D&D Beyond data
            # For now, using a simplified approach
        
        # Add background skill proficiencies
        background = character_data.get('background', {})
        if background:
            bg_name = background.get('definition', {}).get('name', '').lower()
            bg_skills = self.background_skills.get(bg_name, [])
            proficient_skills.update(bg_skills)
        
        # Add racial skill proficiencies
        race_data = character_data.get('race', {})
        # Would parse racial skills from race data
        
        # Add feat skill proficiencies
        feats = character_data.get('feats', [])
        # Would parse feat skills from feat data
        
        return proficient_skills
    
    def _get_proficient_saving_throws(self, character_data: Dict[str, Any]) -> Set[str]:
        """Get set of saving throws the character is proficient in."""
        proficient_saves = set()
        
        # Add class saving throw proficiencies
        classes = character_data.get('classes', [])
        for class_data in classes:
            class_def = class_data.get('definition', {})
            saving_throws = class_def.get('savingThrows', [])
            
            for save_throw in saving_throws:
                save_id = save_throw.get('id')
                if save_id in self.ability_id_map:
                    ability_name = self.ability_id_map[save_id]
                    proficient_saves.add(ability_name)
        
        return proficient_saves
    
    def _get_tool_proficiencies(self, character_data: Dict[str, Any]) -> List[str]:
        """Get list of tool proficiencies."""
        tool_proficiencies = []
        
        # Parse from various sources (class, background, race, feats)
        # This would need comprehensive parsing of D&D Beyond data
        
        return tool_proficiencies
    
    def _get_language_proficiencies(self, character_data: Dict[str, Any]) -> List[str]:
        """Get list of language proficiencies."""
        language_proficiencies = []
        
        # Parse from various sources (race, background, feats)
        # This would need comprehensive parsing of D&D Beyond data
        
        return language_proficiencies
    
    def _get_weapon_proficiencies(self, character_data: Dict[str, Any]) -> List[str]:
        """Get list of weapon proficiencies."""
        weapon_proficiencies = []
        
        # Parse from class and racial features
        # This would need comprehensive parsing of D&D Beyond data
        
        return weapon_proficiencies
    
    def _get_armor_proficiencies(self, character_data: Dict[str, Any]) -> List[str]:
        """Get list of armor proficiencies."""
        armor_proficiencies = []
        
        # Parse from class features
        # This would need comprehensive parsing of D&D Beyond data
        
        return armor_proficiencies
    
    def _get_expertise_skills(self, character_data: Dict[str, Any]) -> List[str]:
        """Get list of skills with expertise."""
        expertise_skills = []
        
        # Parse from class features (Rogue, Bard) and feats
        # This would need comprehensive parsing of D&D Beyond data
        
        return expertise_skills
    
    def _get_half_proficiencies(self, character_data: Dict[str, Any]) -> List[str]:
        """Get list of skills with half proficiency (Jack of All Trades)."""
        half_proficiencies = []
        
        # Check for Bard's Jack of All Trades
        classes = character_data.get('classes', [])
        for class_data in classes:
            class_name = class_data.get('definition', {}).get('name', '').lower()
            class_level = class_data.get('level', 1)
            
            if 'bard' in class_name and class_level >= 2:
                # Bard gets half proficiency on non-proficient ability checks
                # This would apply to all skills they're not proficient in
                pass
        
        return half_proficiencies
    
    def _get_double_proficiencies(self, character_data: Dict[str, Any]) -> List[str]:
        """Get list of proficiencies with double bonus."""
        double_proficiencies = []
        
        # This would include expertise and other features that double proficiency
        # For now, returning expertise skills
        return self._get_expertise_skills(character_data)