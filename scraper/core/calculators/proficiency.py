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
        self.logger = logger  # Add instance logger
        
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
            # Skip validation for enhanced scraper data as it's already validated
            if not ('proficiencies' in character_data and 'character_info' in character_data):
                # Only validate raw D&D Beyond data
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
            
            # Check if this is enhanced scraper data (vs raw D&D Beyond data)
            if 'proficiencies' in character_data and 'character_info' in character_data:
                logger.debug("Detected enhanced scraper data format, using direct extraction")
                # Extract proficiency data directly from enhanced scraper format
                scraper_profs = character_data.get('proficiencies', {})
                
                # Get armor proficiencies from D&D Beyond modifiers
                armor_proficiencies = self._get_armor_proficiencies(character_data)
                
                result_data = {
                    'proficiency_bonus': scraper_profs.get('proficiency_bonus', 2),
                    'skill_proficiencies': scraper_profs.get('skill_proficiencies', []),
                    'saving_throw_proficiencies': scraper_profs.get('saving_throw_proficiencies', []),
                    'tool_proficiencies': scraper_profs.get('tool_proficiencies', []),
                    'language_proficiencies': scraper_profs.get('language_proficiencies', []),
                    'weapon_proficiencies': scraper_profs.get('weapon_proficiencies', []),
                    'weapon_masteries': scraper_profs.get('weapon_masteries', []),
                    'armor_proficiencies': armor_proficiencies,
                    'expertise_skills': [],  # Extract from skill_proficiencies
                    'half_proficiencies': [],  # Not in current scraper format
                    'double_proficiencies': [],  # Not in current scraper format
                    'skills_by_ability': scraper_profs.get('skills_by_ability', {}),
                    'rule_version': '2024'  # Assume 2024 for enhanced scraper data
                }
                
                # Extract expertise skills from skill proficiencies
                expertise_skills = []
                for skill in result_data['skill_proficiencies']:
                    if isinstance(skill, dict) and skill.get('expertise', False):
                        expertise_skills.append(skill.get('name', ''))
                result_data['expertise_skills'] = expertise_skills
                
            else:
                logger.debug("Detected raw D&D Beyond data format, using full calculation pipeline")
                # Perform calculation
                rule_version = self.get_rule_version(character_data)
                logger.debug(f"Calculating proficiencies with {rule_version.version.value} rules")
                
                # Calculate proficiencies (pass context for access to calculated abilities)
                proficiency_data = self._calculate_proficiencies(character_data, rule_version, context)
                
                # Build result
                result_data = {
                    'proficiency_bonus': proficiency_data.proficiency_bonus,
                    'skill_proficiencies': proficiency_data.skill_proficiencies,
                    'saving_throw_proficiencies': proficiency_data.saving_throw_proficiencies,
                    'tool_proficiencies': proficiency_data.tool_proficiencies,
                    'language_proficiencies': proficiency_data.language_proficiencies,
                    'weapon_proficiencies': proficiency_data.weapon_proficiencies,
                    'weapon_masteries': getattr(proficiency_data, '_weapon_masteries', []),
                    'armor_proficiencies': proficiency_data.armor_proficiencies,
                    'expertise_skills': proficiency_data.expertise_skills,
                    'half_proficiencies': proficiency_data.half_proficiencies,
                    'double_proficiencies': proficiency_data.double_proficiencies,
                    'rule_version': rule_version.version.value,
                    # Add passive skills
                    'passive_perception': getattr(proficiency_data, '_passive_skills', {}).get('perception', 10),
                    'passive_investigation': getattr(proficiency_data, '_passive_skills', {}).get('investigation', 10),
                    'passive_insight': getattr(proficiency_data, '_passive_skills', {}).get('insight', 10),
                    # Add change detection compatible data
                    'proficiencies_for_change_detection': self._build_change_detection_data(proficiency_data, character_data)
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
        # Accept either raw D&D Beyond format ('classes') or enhanced scraper format ('character_info')
        if 'classes' not in character_data and 'character_info' not in character_data:
            errors.append("Missing required 'classes' field for proficiency calculation")
        elif 'classes' in character_data:
            classes = character_data['classes']
            if not isinstance(classes, list):
                errors.append("'classes' field must be a list")
        
        # Check for stats (needed for skill bonuses) - only for raw D&D Beyond data
        if 'stats' not in character_data and 'abilities' not in character_data:
            errors.append("Missing required 'stats' or 'abilities' field for skill bonus calculation")
        elif 'stats' in character_data:
            stats = character_data['stats']
            if not isinstance(stats, list):
                errors.append("'stats' field must be a list")
        
        # Use validator for additional checks - only for enhanced scraper data
        # Skip for raw D&D Beyond data as it has a different format
        if 'proficiencies' in character_data and 'character_info' in character_data:
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
    def _calculate_proficiencies(self, character_data: Dict[str, Any], rule_version, context=None) -> ProficiencyData:
        """
        Calculate proficiencies with comprehensive breakdown.

        Args:
            character_data: Character data from D&D Beyond
            rule_version: Detected rule version
            context: Calculation context (contains calculated abilities)

        Returns:
            ProficiencyData object with complete breakdown
        """
        # Calculate proficiency bonus
        proficiency_bonus = self._get_proficiency_bonus(character_data)

        # Get ability modifiers (from context if available, otherwise from character_data)
        ability_modifiers = self._get_ability_modifiers(character_data, context)
        
        # Calculate skill proficiencies
        skill_proficiencies = self._calculate_skill_proficiencies(character_data, ability_modifiers, proficiency_bonus)
        
        # Calculate saving throw proficiencies
        saving_throw_proficiencies = self._calculate_saving_throw_proficiencies(character_data, ability_modifiers, proficiency_bonus)
        
        # Get other proficiencies
        tool_proficiencies = self._get_tool_proficiencies(character_data)
        language_proficiencies = self._get_language_proficiencies(character_data)
        weapon_proficiencies = self._get_weapon_proficiencies(character_data)
        armor_proficiencies = self._get_armor_proficiencies(character_data)

        # Get weapon masteries (2024 rules feature)
        weapon_masteries = self._get_weapon_masteries(character_data)

        # Get special proficiency types
        expertise_skills = self._get_expertise_skills(character_data)
        half_proficiencies = self._get_half_proficiencies(character_data)
        double_proficiencies = self._get_double_proficiencies(character_data)

        # Calculate passive skills (10 + skill bonus)
        passive_perception = 10 + skill_proficiencies.get('perception', {}).get('total_bonus', 0)
        passive_investigation = 10 + skill_proficiencies.get('investigation', {}).get('total_bonus', 0)
        passive_insight = 10 + skill_proficiencies.get('insight', {}).get('total_bonus', 0)
        print(f"[DEBUG] Passive skills: Perception={passive_perception}, Investigation={passive_investigation}, Insight={passive_insight}")

        proficiency_data = ProficiencyData(
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

        # Store passive skills and weapon masteries in metadata (not part of ProficiencyData dataclass)
        # These will be added to the result in the calculate() method
        proficiency_data._passive_skills = {
            'perception': passive_perception,
            'investigation': passive_investigation,
            'insight': passive_insight
        }
        proficiency_data._weapon_masteries = weapon_masteries

        return proficiency_data
    
    def _get_proficiency_bonus(self, character_data: Dict[str, Any]) -> int:
        """Get character's proficiency bonus based on level."""
        classes = character_data.get('classes', [])
        total_level = sum(cls.get('level', 0) for cls in classes) or 1
        return DnDMath.proficiency_bonus(total_level)
    
    def _get_ability_modifiers(self, character_data: Dict[str, Any], context=None) -> Dict[str, int]:
        """Get all ability modifiers from context, pre-calculated abilities, or fallback to raw stats."""
        ability_modifiers = {}

        # Try to get from context first (from abilities coordinator)
        if context and hasattr(context, 'metadata') and context.metadata:
            abilities_data = context.metadata.get('abilities', {})
            if 'ability_modifiers' in abilities_data:
                self.logger.debug(f"Using ability modifiers from context: {abilities_data['ability_modifiers']}")
                return abilities_data['ability_modifiers']
            elif 'ability_scores' in abilities_data:
                for ability_name, ability_data in abilities_data['ability_scores'].items():
                    if isinstance(ability_data, dict) and 'modifier' in ability_data:
                        ability_modifiers[ability_name] = ability_data['modifier']
                if ability_modifiers:
                    self.logger.debug(f"Using ability_scores from context: {ability_modifiers}")
                    return ability_modifiers

        # Try to get from pre-calculated abilities data in character_data
        if 'abilities' in character_data:
            abilities = character_data['abilities']
            if 'ability_modifiers' in abilities:
                self.logger.debug(f"Using pre-calculated ability modifiers from abilities: {abilities['ability_modifiers']}")
                return abilities['ability_modifiers']
            # Try ability_scores structure
            elif 'ability_scores' in abilities:
                for ability_name, ability_data in abilities['ability_scores'].items():
                    if isinstance(ability_data, dict) and 'modifier' in ability_data:
                        ability_modifiers[ability_name] = ability_data['modifier']
                if ability_modifiers:
                    self.logger.debug(f"Using pre-calculated ability modifiers from ability_scores: {ability_modifiers}")
                    return ability_modifiers

        # Fallback: calculate from raw stats (base scores only - NOT recommended)
        self.logger.warning("Falling back to raw stats calculation for ability modifiers - this may not include bonuses from items/feats!")
        stats = character_data.get('stats', [])

        for stat in stats:
            ability_id = stat.get('id')
            if ability_id in self.ability_id_map:
                ability_name = self.ability_id_map[ability_id]
                score = stat.get('value', 10)
                ability_modifiers[ability_name] = DnDMath.ability_modifier(score)

        return ability_modifiers

    def _get_ability_check_bonus(self, character_data: Dict[str, Any]) -> tuple[int, list[dict]]:
        """
        Get bonus to ability checks from modifiers (Stone of Good Luck, etc.).
        D&D Beyond provides these as modifiers with subType 'ability-checks'.
        Only counts bonuses from equipped items.

        Args:
            character_data: Character data from D&D Beyond

        Returns:
            Tuple of (total_bonus, list of item details with 'name' and 'bonus')
        """
        ability_check_bonus = 0
        item_bonuses = []

        # Check modifiers for ability check bonuses (Stone of Good Luck, etc.)
        modifiers = character_data.get('modifiers', {})
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue

            for modifier in modifier_list:
                # Look for ability check bonuses
                if modifier.get('subType') == 'ability-checks' and modifier.get('isGranted', False):
                    bonus = modifier.get('fixedValue') or modifier.get('value', 0)
                    if bonus:
                        # Find item name from componentId and check if equipped
                        component_id = modifier.get('componentId')
                        item_name = "Unknown Item"
                        is_equipped = False

                        if component_id:
                            # Search inventory for the item - try both raw and enhanced format
                            inventory = character_data.get('inventory', [])
                            equipment = character_data.get('equipment', {})
                            enhanced_equipment = equipment.get('enhanced_equipment', [])

                            # Check raw inventory format
                            for item in inventory:
                                if item.get('definition', {}).get('id') == component_id:
                                    item_name = item['definition'].get('name', 'Unknown Item')
                                    is_equipped = item.get('equipped', False)
                                    break

                            # Check enhanced equipment format if not found
                            if not is_equipped and item_name == "Unknown Item":
                                for item in enhanced_equipment:
                                    # Enhanced format uses definition_key like "112130694:4773"
                                    def_key = item.get('definition_key', '')
                                    if str(component_id) in def_key:
                                        item_name = item.get('name', 'Unknown Item')
                                        is_equipped = item.get('equipped', False)
                                        break

                        # Only add bonus if item is equipped
                        if is_equipped:
                            ability_check_bonus += bonus
                            item_bonuses.append({'name': item_name, 'bonus': bonus})
                            self.logger.debug(f"Found ability check bonus from equipped {item_name}: +{bonus}")
                        else:
                            self.logger.debug(f"Ignoring ability check bonus from unequipped {item_name}: +{bonus}")

        return ability_check_bonus, item_bonuses

    def _get_saving_throw_bonus(self, character_data: Dict[str, Any]) -> tuple[int, list[dict]]:
        """
        Get bonus to saving throws from modifiers (Stone of Good Luck, etc.).
        D&D Beyond provides these as modifiers with subType 'saving-throws'.
        Only counts bonuses from equipped items.

        Args:
            character_data: Character data from D&D Beyond

        Returns:
            Tuple of (total_bonus, list of item details with 'name' and 'bonus')
        """
        saving_throw_bonus = 0
        item_bonuses = []

        # Check modifiers for saving throw bonuses (Stone of Good Luck, etc.)
        modifiers = character_data.get('modifiers', {})
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue

            for modifier in modifier_list:
                # Look for saving throw bonuses
                if modifier.get('subType') == 'saving-throws' and modifier.get('isGranted', False):
                    bonus = modifier.get('fixedValue') or modifier.get('value', 0)
                    if bonus:
                        # Find item name from componentId and check if equipped
                        component_id = modifier.get('componentId')
                        item_name = "Unknown Item"
                        is_equipped = False

                        if component_id:
                            # Search inventory for the item - try both raw and enhanced format
                            inventory = character_data.get('inventory', [])
                            equipment = character_data.get('equipment', {})
                            enhanced_equipment = equipment.get('enhanced_equipment', [])

                            # Check raw inventory format
                            for item in inventory:
                                if item.get('definition', {}).get('id') == component_id:
                                    item_name = item['definition'].get('name', 'Unknown Item')
                                    is_equipped = item.get('equipped', False)
                                    break

                            # Check enhanced equipment format if not found
                            if not is_equipped and item_name == "Unknown Item":
                                for item in enhanced_equipment:
                                    # Enhanced format uses definition_key like "112130694:4773"
                                    def_key = item.get('definition_key', '')
                                    if str(component_id) in def_key:
                                        item_name = item.get('name', 'Unknown Item')
                                        is_equipped = item.get('equipped', False)
                                        break

                        # Only add bonus if item is equipped
                        if is_equipped:
                            saving_throw_bonus += bonus
                            item_bonuses.append({'name': item_name, 'bonus': bonus})
                            self.logger.debug(f"Found saving throw bonus from equipped {item_name}: +{bonus}")
                        else:
                            self.logger.debug(f"Ignoring saving throw bonus from unequipped {item_name}: +{bonus}")

        return saving_throw_bonus, item_bonuses

    def _get_skill_specific_bonuses(self, character_data: Dict[str, Any]) -> Dict[str, tuple[int, list[dict]]]:
        """
        Get bonuses for specific skills from modifiers (Gloves of Thievery, etc.).
        D&D Beyond provides these as modifiers with skill-specific subTypes like 'sleight-of-hand'.

        Args:
            character_data: Character data from D&D Beyond

        Returns:
            Dict mapping skill name to tuple of (total_bonus, list of item details with 'name' and 'bonus')
        """
        skill_bonuses = {}  # skill_name -> (total_bonus, [item_details])

        # Map modifier subTypes to skill names
        modifier_to_skill = {
            'acrobatics': 'acrobatics',
            'animal-handling': 'animal_handling',
            'arcana': 'arcana',
            'athletics': 'athletics',
            'deception': 'deception',
            'history': 'history',
            'insight': 'insight',
            'intimidation': 'intimidation',
            'investigation': 'investigation',
            'medicine': 'medicine',
            'nature': 'nature',
            'perception': 'perception',
            'performance': 'performance',
            'persuasion': 'persuasion',
            'religion': 'religion',
            'sleight-of-hand': 'sleight_of_hand',
            'stealth': 'stealth',
            'survival': 'survival'
        }

        # Check equipment for skill-specific modifiers
        # Try enhanced scraper format first (equipment.enhanced_equipment)
        equipment = character_data.get('equipment', {})
        enhanced_equipment = equipment.get('enhanced_equipment', [])

        # If not found, try raw D&D Beyond format (inventory)
        if not enhanced_equipment:
            enhanced_equipment = character_data.get('inventory', [])

        for item in enhanced_equipment:
            if not item.get('equipped', False):
                continue

            # Handle both formats: enhanced scraper (item.name) and raw D&D Beyond (item.definition.name)
            item_name = item.get('name')
            if not item_name:
                item_name = item.get('definition', {}).get('name', 'Unknown Item')

            # Get modifiers from either format
            granted_mods = item.get('granted_modifiers', [])
            if not granted_mods:
                granted_mods = item.get('definition', {}).get('grantedModifiers', [])

            for modifier in granted_mods:
                # Look for skill bonuses (type='bonus', subType='<skill-name>')
                if modifier.get('type') == 'bonus' and modifier.get('isGranted', False):
                    sub_type = modifier.get('subType', '')

                    # Check if this is a skill-specific bonus
                    if sub_type in modifier_to_skill:
                        skill_name = modifier_to_skill[sub_type]
                        bonus = modifier.get('fixedValue') or modifier.get('value', 0)

                        if bonus:
                            if skill_name not in skill_bonuses:
                                skill_bonuses[skill_name] = (0, [])

                            total, items = skill_bonuses[skill_name]
                            total += bonus
                            items.append({'name': item_name, 'bonus': bonus})
                            skill_bonuses[skill_name] = (total, items)
                            self.logger.debug(f"Found skill-specific bonus: {item_name} +{bonus} to {skill_name}")

        return skill_bonuses

    def _calculate_skill_proficiencies(self, character_data: Dict[str, Any], ability_modifiers: Dict[str, int], proficiency_bonus: int) -> Dict[str, Any]:
        """Calculate skill proficiency bonuses with change detection compatibility."""
        skill_proficiencies = {}

        # Get proficient skills with their sources
        proficient_skills, skill_sources = self._get_proficient_skills(character_data)
        expertise_skills = self._get_expertise_skills(character_data)
        half_prof_skills = self._get_half_proficiencies(character_data)

        # Check for ability check bonuses from modifiers (Stone of Good Luck, etc.)
        luck_bonus, general_item_bonuses = self._get_ability_check_bonus(character_data)
        self.logger.debug(f"Ability check bonus from modifiers: {luck_bonus} from {len(general_item_bonuses)} items")

        # Get skill-specific bonuses (Gloves of Thievery, etc.)
        skill_specific_bonuses = self._get_skill_specific_bonuses(character_data)
        self.logger.debug(f"Found skill-specific bonuses for {len(skill_specific_bonuses)} skills")

        # Calculate bonuses for all skills
        for skill, ability in self.skill_abilities.items():
            ability_mod = ability_modifiers.get(ability, 0)

            is_proficient = skill in proficient_skills
            has_expertise = skill in expertise_skills
            has_half_prof = skill in half_prof_skills

            if has_expertise:
                # Expertise: double proficiency bonus
                bonus = ability_mod + (proficiency_bonus * 2)
                if skill == 'acrobatics':
                    print(f"[DEBUG ACROBATICS] ability_mod={ability_mod}, prof_bonus={proficiency_bonus}, expertise_bonus={(proficiency_bonus*2)}, before_luck={bonus}")
            elif is_proficient:
                # Regular proficiency
                bonus = ability_mod + proficiency_bonus
            elif has_half_prof:
                # Half proficiency (Jack of All Trades, etc.)
                bonus = ability_mod + (proficiency_bonus // 2)
            else:
                # No proficiency
                bonus = ability_mod

            # Combine general and skill-specific item bonuses
            all_item_bonuses = list(general_item_bonuses)  # Copy general bonuses
            total_item_bonus = luck_bonus  # Start with general ability check bonus

            # Add skill-specific bonus if present
            if skill in skill_specific_bonuses:
                specific_bonus, specific_items = skill_specific_bonuses[skill]
                total_item_bonus += specific_bonus
                all_item_bonuses.extend(specific_items)

            # Add total item bonus
            bonus += total_item_bonus
            if skill == 'acrobatics':
                print(f"[DEBUG ACROBATICS] luck_bonus={luck_bonus}, final_bonus={bonus}")

            # Store both total bonus and proficiency flags for change detection compatibility
            skill_proficiencies[skill] = {
                'total_bonus': bonus,
                'proficient': is_proficient or has_expertise,  # Expertise implies proficiency
                'expertise': has_expertise,
                'half_proficiency': has_half_prof,
                'ability_modifier': ability_mod,
                'proficiency_bonus': proficiency_bonus if (is_proficient or has_expertise) else (proficiency_bonus // 2 if has_half_prof else 0),
                'item_bonus': total_item_bonus,  # Total bonus from all items (general + specific)
                'item_bonus_details': all_item_bonuses,  # List of items providing bonuses
                'source': skill_sources.get(skill, 'Unknown')  # Where the proficiency comes from
            }

        return skill_proficiencies
    
    def _calculate_saving_throw_proficiencies(self, character_data: Dict[str, Any], ability_modifiers: Dict[str, int], proficiency_bonus: int) -> Dict[str, Any]:
        """Calculate saving throw proficiency bonuses with change detection compatibility."""
        saving_throw_proficiencies = {}

        # Get proficient saving throws
        proficient_saves = self._get_proficient_saving_throws(character_data)

        # Check for saving throw bonuses from modifiers (Stone of Good Luck affects saves too)
        save_bonus, save_item_bonuses = self._get_saving_throw_bonus(character_data)
        self.logger.debug(f"Saving throw bonus from modifiers: {save_bonus} from {len(save_item_bonuses)} items")

        # Calculate bonuses for all abilities
        for ability in self.ability_id_map.values():
            ability_mod = ability_modifiers.get(ability, 0)
            is_proficient = ability in proficient_saves

            if is_proficient:
                bonus = ability_mod + proficiency_bonus
            else:
                bonus = ability_mod

            # Add item bonus (Stone of Good Luck, etc.)
            bonus += save_bonus

            # Store both total bonus and proficiency flag for change detection compatibility
            saving_throw_proficiencies[ability] = {
                'total_bonus': bonus,
                'proficient': is_proficient,
                'ability_modifier': ability_mod,
                'proficiency_bonus': proficiency_bonus if is_proficient else 0,
                'item_bonus': save_bonus,
                'item_bonus_details': save_item_bonuses
            }

        return saving_throw_proficiencies
    
    def _get_proficient_skills(self, character_data: Dict[str, Any]) -> tuple[Set[str], Dict[str, str]]:
        """
        Get set of skills the character is proficient in.

        Returns:
            Tuple of (set of proficient skills, dict mapping skill->source)
        """
        proficient_skills = set()
        skill_sources = {}  # Track where each skill proficiency comes from

        # Extract skill proficiencies from modifiers (D&D Beyond API structure)
        modifiers = character_data.get('modifiers', {})

        # Process modifiers from all sources
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue

            for modifier in modifier_list:
                if self._is_skill_proficiency_modifier(modifier):
                    skill_name = self._extract_skill_from_modifier(modifier)
                    if skill_name:
                        proficient_skills.add(skill_name)
                        # Store the source (first one wins if multiple sources)
                        if skill_name not in skill_sources:
                            skill_sources[skill_name] = source_type
                        logger.debug(f"Found skill proficiency: {skill_name} (source: {source_type})")

        return proficient_skills, skill_sources
    
    def _is_skill_proficiency_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier grants skill proficiency."""
        if not isinstance(modifier, dict):
            return False
        
        subtype = modifier.get('subType', '').lower()
        friendly_type = modifier.get('friendlyTypeName', '').lower()
        
        # Don't include expertise-only modifiers here (they'll be handled separately)
        skill_keywords = ['skill', 'proficiency']
        return any(keyword in subtype or keyword in friendly_type for keyword in skill_keywords)
    
    def _extract_skill_from_modifier(self, modifier: Dict[str, Any]) -> Optional[str]:
        """Extract skill name from a modifier."""
        friendly_subtype = modifier.get('friendlySubtypeName', '')
        
        # Try to extract skill name by matching against known skills
        for skill in self.skill_abilities.keys():
            skill_display = skill.replace('_', ' ').title()  # e.g., "sleight_of_hand" -> "Sleight Of Hand"
            if skill_display.lower() in friendly_subtype.lower() or skill in friendly_subtype.lower():
                return skill
        
        return None
    
    def _get_proficient_saving_throws(self, character_data: Dict[str, Any]) -> Set[str]:
        """Get set of saving throws the character is proficient in."""
        proficient_saves = set()
        
        # Extract saving throw proficiencies from modifiers (D&D Beyond API structure)
        modifiers = character_data.get('modifiers', {})
        
        # Process modifiers from all sources
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                if self._is_saving_throw_modifier(modifier):
                    ability_name = self._extract_saving_throw_from_modifier(modifier)
                    if ability_name:
                        # For saving throw proficiencies, use a targeted approach based on actual D&D Beyond UI behavior
                        # Since the API vs UI discrepancy is specific to multiclass saving throws
                        if self._should_allow_saving_throw_proficiency(modifier, character_data):
                            proficient_saves.add(ability_name)
                            logger.debug(f"Found saving throw proficiency: {ability_name} (source: {source_type})")
                        else:
                            logger.debug(f"Rejected saving throw proficiency: {ability_name} (source: {source_type}) - does not match D&D Beyond UI behavior")
        
        return proficient_saves
    
    def _should_allow_saving_throw_proficiency(self, modifier: Dict[str, Any], character_data: Dict[str, Any]) -> bool:
        """Determine if a saving throw proficiency should be allowed based on D&D 5e multiclass rules."""
        available_to_multiclass = modifier.get('availableToMulticlass', True)
        
        # Check if multiclass
        classes = character_data.get('classes', [])
        is_multiclass = len(classes) > 1
        
        # For single class characters, allow all proficiencies
        if not is_multiclass:
            return True
        
        # For multiclass characters: if availableToMulticlass is True, allow it
        if available_to_multiclass:
            return True
        
        # For multiclass characters with availableToMulticlass=False:
        # Apply D&D 5e rule - only allow saving throws from the first/starting class
        component_id = modifier.get('componentId')
        if not component_id:
            return False
            
        return self._is_from_starting_class(component_id, character_data)
    
    def _is_from_starting_class(self, component_id: int, character_data: Dict[str, Any]) -> bool:
        """Check if a component ID belongs to the character's starting/first class."""
        classes = character_data.get('classes', [])
        if not classes:
            return False
        
        # Find the starting class using the isStartingClass flag from D&D Beyond API
        starting_class = None
        for cls in classes:
            if cls.get('isStartingClass', False):
                starting_class = cls
                break
        
        if not starting_class:
            # Fallback: if no isStartingClass flag found, use highest level class
            starting_class = max(classes, key=lambda cls: cls.get('level', 0))
        
        starting_class_name = starting_class.get('definition', {}).get('name', 'Unknown')
        
        # Check known component IDs for validation
        # 10292347 = Core Sorcerer Traits, 10292323 = Core Rogue Traits
        if starting_class_name == 'Sorcerer' and component_id == 10292347:
            logger.debug(f"Component {component_id} belongs to starting class {starting_class_name}")
            return True
        elif starting_class_name == 'Rogue' and component_id == 10292323:
            logger.debug(f"Component {component_id} belongs to starting class {starting_class_name}")  
            return True
        
        logger.debug(f"Component {component_id} does not belong to starting class {starting_class_name}")
        return False
    
    def _is_valid_multiclass_proficiency(self, modifier: Dict[str, Any], character_data: Dict[str, Any]) -> bool:
        """Check if a proficiency modifier should be applied considering multiclass rules."""
        available_to_multiclass = modifier.get('availableToMulticlass', True)
        
        # If availableToMulticlass is True, it's always valid
        if available_to_multiclass:
            return True
        
        # Check if this is a multiclass character
        classes = character_data.get('classes', [])
        is_multiclass = len(classes) > 1
        
        # If not multiclass, all proficiencies are valid
        if not is_multiclass:
            logger.debug(f"Single class character, allowing proficiency")
            return True
        
        # For multiclass characters with availableToMulticlass=False,
        # we need to determine which proficiencies to allow
        # Based on D&D Beyond UI behavior: allow proficiencies from the primary/starting class
        component_id = modifier.get('componentId')
        
        # Determine which class this proficiency comes from based on component ID
        # This is a more general approach than hardcoding specific component IDs
        primary_class_components = self._get_primary_class_components(character_data)
        
        if component_id in primary_class_components:
            logger.debug(f"Multiclass character: allowing proficiency from primary class (component {component_id})")
            return True
        else:
            logger.debug(f"Multiclass character: rejecting proficiency from secondary class (component {component_id})")
            return False
    
    def _is_saving_throw_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier grants saving throw proficiency."""
        if not isinstance(modifier, dict):
            return False
        
        # Only accept type="proficiency" modifiers to avoid false positives from advantage/resistance
        if modifier.get('type') != 'proficiency':
            return False
            
        # Must be granted
        if not modifier.get('isGranted'):
            return False
        
        # Must have saving throw subtype
        subtype = modifier.get('subType', '')
        return subtype.endswith('-saving-throws')
    
    def _extract_saving_throw_from_modifier(self, modifier: Dict[str, Any]) -> Optional[str]:
        """Extract ability name from a saving throw modifier."""
        friendly_subtype = modifier.get('friendlySubtypeName', '').lower()
        
        # Map ability names to their full names in modifiers
        abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        
        for ability in abilities:
            if ability in friendly_subtype:
                return ability
                
        return None
    
    def _get_tool_proficiencies(self, character_data: Dict[str, Any]) -> List[str]:
        """Get list of tool proficiencies from D&D Beyond data."""
        tools = []
        seen_tools = set()
        
        # Check for tools in modifiers
        modifiers = character_data.get('modifiers', {})
        
        # Process modifiers from different sources
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
            
            for modifier in modifier_list:
                if self._is_tool_modifier(modifier):
                    tool_name = self._extract_tool_from_modifier(modifier, source_type, character_data)
                    if tool_name and tool_name not in seen_tools:
                        tools.append(tool_name)
                        seen_tools.add(tool_name)
                        logger.debug(f"Tool proficiency: {tool_name} (source: {source_type})")
        
        return sorted(tools)
    
    def _get_language_proficiencies(self, character_data: Dict[str, Any]) -> List[str]:
        """Get list of language proficiencies from D&D Beyond data."""
        languages = []
        seen_languages = set()
        
        # Check for languages in modifiers
        modifiers = character_data.get('modifiers', {})
        
        # Process modifiers from different sources
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
            
            for modifier in modifier_list:
                if self._is_language_modifier(modifier):
                    lang_name = self._extract_language_from_modifier(modifier, source_type, character_data)
                    if lang_name and lang_name != 'Unknown Language' and lang_name not in seen_languages:
                        languages.append(lang_name)
                        seen_languages.add(lang_name)
                        logger.debug(f"Language proficiency: {lang_name} (source: {source_type})")
        
        # Check race/species features for languages
        for data_key in ['race', 'species']:
            data = character_data.get(data_key, {})
            if isinstance(data, dict):
                features = data.get('features', []) + data.get('traits', [])
                
                for feature in features:
                    if self._is_language_feature(feature):
                        lang_name = self._extract_language_from_feature(feature, data_key)
                        if lang_name and lang_name not in seen_languages:
                            languages.append(lang_name)
                            seen_languages.add(lang_name)
                            logger.debug(f"Language proficiency from {data_key}: {lang_name}")
        
        # Add Common by default (every character knows Common)
        if 'Common' not in seen_languages:
            languages.insert(0, 'Common')
        
        # Add basic racial languages if none found in modifiers
        if len(languages) <= 1:  # Only Common found
            racial_languages = self._get_basic_racial_languages(character_data)
            for lang in racial_languages:
                if lang not in seen_languages:
                    languages.append(lang)
                    seen_languages.add(lang)
        
        return sorted(languages)
    
    def _is_language_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier grants language proficiency."""
        subtype = modifier.get('subType', '').lower()
        friendly_subtype = modifier.get('friendlySubtypeName', '').lower()
        friendly_type = modifier.get('friendlyTypeName', '').lower()
        
        # Explicitly exclude tool proficiencies first
        if "thieves' tools" in friendly_subtype or "tools" in friendly_subtype:
            logger.debug(f"Excluding tool proficiency from language detection: {friendly_subtype}")
            return False
        
        # Check for explicit language indicators first
        if ('language' in subtype or 'language' in friendly_subtype or 'language' in friendly_type):
            logger.debug(f"Detected language modifier by keyword: {friendly_subtype}")
            return True
        
        # Check for exact language matches (not partial matches to avoid false positives)
        exact_languages = ['common', 'elvish', 'draconic', 'dwarvish', 'halfling', 'gnomish', 
                          'giant', 'goblin', 'orc', "thieves' cant", 'celestial', 'infernal', 'abyssal']
        
        # Only match if the friendly subtype is exactly one of these languages
        is_language = friendly_subtype in exact_languages
        if is_language:
            logger.debug(f"Detected language modifier by exact match: {friendly_subtype}")
        
        return is_language
    
    def _extract_language_from_modifier(self, modifier: Dict[str, Any], source_type: str, 
                                      character_data: Dict[str, Any] = None) -> str:
        """Extract language name from modifier."""
        language_name = modifier.get('friendlySubtypeName', 'Unknown Language')
        
        # Filter out tool proficiencies that were incorrectly detected as languages
        tool_keywords = ['tools', 'kit', 'supplies', 'instrument', 'vehicle']
        if any(keyword in language_name.lower() for keyword in tool_keywords):
            logger.debug(f"Filtering out tool proficiency detected as language: {language_name}")
            return None
            
        # Specifically filter out "Thieves' Tools" if it somehow gets through
        if language_name.lower() in ["thieves' tools", "thieves tools"]:
            logger.debug(f"Specifically filtering out thieves' tools: {language_name}")
            return None
            
        return language_name
    
    def _is_language_feature(self, feature: Dict[str, Any]) -> bool:
        """Check if a feature grants language proficiency."""
        name = feature.get('name', '').lower()
        description = feature.get('description', '').lower()
        
        # Check for language-related features
        return ('language' in name or 'languages' in description or 
                'speak' in description or 'tongue' in name)
    
    def _extract_language_from_feature(self, feature: Dict[str, Any], source: str) -> str:
        """Extract language name from feature."""
        name = feature.get('name', '')
        description = feature.get('description', '')
        
        # Try to extract specific language from name or description
        import re
        
        # Look for specific language names in description
        language_patterns = [
            r'speak\s+(\w+)', r'(\w+)\s+language', r'languages?\s+of\s+(\w+)',
            r'know\s+(\w+)', r'(\w+)\s+tongue'
        ]
        
        for pattern in language_patterns:
            match = re.search(pattern, description.lower())
            if match:
                lang_name = match.group(1).title()
                if lang_name not in ['The', 'A', 'An', 'Your', 'Their']:
                    return lang_name
        
        # Fallback: extract from feature name if it contains a language
        common_languages = ['Common', 'Elvish', 'Draconic', 'Dwarvish', 'Halfling', 'Gnomish', 
                          'Giant', 'Goblin', 'Orc', 'Infernal', 'Celestial', 'Abyssal']
        
        for lang in common_languages:
            if lang.lower() in name.lower() or lang.lower() in description.lower():
                return lang
        
        return 'Unknown Language'
    
    def _get_basic_racial_languages(self, character_data: Dict[str, Any]) -> List[str]:
        """Get basic racial languages based on character race/species."""
        languages = []
        
        # Get race/species name
        race_name = ''
        for key in ['race', 'species']:
            data = character_data.get(key, {})
            if isinstance(data, dict):
                race_name = data.get('name', '').lower()
                if race_name:
                    break
        
        # Basic race-to-language mapping
        race_language_map = {
            'elf': ['Elvish'],
            'dwarf': ['Dwarvish'],
            'halfling': ['Halfling'],
            'dragonborn': ['Draconic'],
            'tiefling': ['Infernal'],
            'half-elf': ['Elvish'],
            'half-orc': ['Orc'],
            'gnome': ['Gnomish'],
            'orc': ['Orc'],
            'goblin': ['Goblin'],
            'hobgoblin': ['Goblin'],
            'bugbear': ['Goblin']
        }
        
        # Add racial languages
        for race, race_langs in race_language_map.items():
            if race in race_name:
                languages.extend(race_langs)
                break
        
        return languages
    
    def _basic_language_extraction(self, character_data: Dict[str, Any]) -> List[str]:
        """Basic fallback language extraction from character data."""
        languages = []
        
        # Add Common by default (all characters know Common)
        languages.append('Common')
        
        # Check for race/species languages
        race_data = character_data.get('race', {})
        species_data = character_data.get('species', {})
        
        for data in [race_data, species_data]:
            if isinstance(data, dict):
                race_name = data.get('name', '').lower()
                # Basic race-to-language mapping
                race_languages = {
                    'elf': ['Elvish'],
                    'dwarf': ['Dwarvish'], 
                    'halfling': ['Halfling'],
                    'dragonborn': ['Draconic'],
                    'tiefling': ['Infernal'],
                    'human': [],  # Humans get a choice
                    'half-elf': ['Elvish'],
                    'half-orc': ['Orc'],
                    'gnome': ['Gnomish']
                }
                
                for race, race_langs in race_languages.items():
                    if race in race_name:
                        languages.extend(race_langs)
                        break
        
        # Remove duplicates and return
        return list(set(languages))
    
    def _get_weapon_proficiencies(self, character_data: Dict[str, Any]) -> List[str]:
        """Get list of weapon proficiencies from D&D Beyond data."""
        weapon_proficiencies = []
        seen_weapons = set()
        
        # Weapon group to individual weapon mapping
        weapon_groups = {
            'simple-weapons': [
                'club', 'dagger', 'dart', 'javelin', 'mace', 'quarterstaff', 'sickle', 
                'spear', 'crossbow-light', 'shortbow', 'sling', 'handaxe', 'light-hammer'
            ],
            'martial-weapons': [
                'battleaxe', 'flail', 'glaive', 'greataxe', 'greatsword', 'halberd', 
                'lance', 'longsword', 'maul', 'morningstar', 'pike', 'rapier', 'scimitar',
                'shortsword', 'trident', 'war-pick', 'warhammer', 'whip', 'blowgun',
                'crossbow-hand', 'crossbow-heavy', 'longbow', 'net'
            ]
        }
        
        # Extract weapon proficiencies from modifiers
        modifiers = character_data.get('modifiers', {})
        
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                if not isinstance(modifier, dict):
                    continue
                    
                # Only accept proficiency type modifiers
                if modifier.get('type') != 'proficiency':
                    continue
                    
                # Must be granted
                if not modifier.get('isGranted'):
                    continue
                    
                subtype = modifier.get('subType', '')
                friendly_name = modifier.get('friendlySubtypeName', '')
                modifier_subtype_id = modifier.get('modifierSubTypeId', 0)
                
                # Use modifierSubTypeId to identify weapon proficiencies
                # Based on D&D Beyond data: weapon proficiencies appear to have IDs 260+
                # and exclude saving throws (220s) and skills (240s)
                if modifier_subtype_id < 260 or modifier_subtype_id in range(220, 250):
                    continue
                
                # Additional check: must contain weapon-related keywords in subType
                weapon_keywords = ['weapon', 'rapier', 'shortsword', 'crossbow', 'simple-weapons', 'martial-weapons']
                if not any(keyword in subtype.lower() for keyword in weapon_keywords):
                    continue
                
                # Apply multiclass validation for weapon proficiencies
                if not self._should_allow_weapon_proficiency(modifier, character_data):
                    logger.debug(f"Rejected weapon proficiency due to multiclass rules: {friendly_name} (source: {source_type})")
                    continue
                
                # Use the friendlySubtypeName as it matches D&D Beyond exactly
                weapon_name = friendly_name or subtype.replace('-', ' ').title()
                if weapon_name not in seen_weapons:
                    weapon_proficiencies.append(weapon_name)
                    seen_weapons.add(weapon_name)
                    logger.debug(f"Weapon proficiency: {weapon_name} (ID: {modifier_subtype_id}, source: {source_type})")
        
        return sorted(weapon_proficiencies)

    def _get_weapon_masteries(self, character_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract weapon masteries from character choices (2024 rules feature).

        Weapon masteries allow characters to use special properties like Nick, Cleave, Push, etc.
        Available starting at Rogue level 1 and Fighter level 1 in 2024 rules.

        Returns:
            List of dictionaries with 'weapon', 'mastery', and 'description' keys
        """
        weapon_masteries = []

        try:
            choices = character_data.get('choices', {})

            # Get choice definitions that contain mastery options
            choice_defs = choices.get('choiceDefinitions', [])
            mastery_choice_def = None
            mastery_options_map = {}

            # Find the mastery choice definition and build option mapping
            for choice_def in choice_defs:
                opts = choice_def.get('options', [])

                # Check if this choice contains mastery options
                has_mastery = any('mastery' in str(opt.get('label', '')).lower() or
                                 'mastery' in str(opt.get('description', '')).lower()
                                 for opt in opts)

                if has_mastery:
                    mastery_choice_def = choice_def

                    # Build mapping of option ID to mastery info
                    for opt in opts:
                        label = opt.get('label', '')
                        description = opt.get('description', '')

                        # Parse "Weapon (Mastery)" format (e.g., "Scimitar (Nick)")
                        if '(' in label and ')' in label:
                            parts = label.split('(')
                            if len(parts) == 2:
                                weapon = parts[0].strip()
                                mastery = parts[1].replace(')', '').strip()

                                # Only include actual weapon mastery options (not ASI options)
                                mastery_keywords = ['Nick', 'Cleave', 'Graze', 'Push', 'Sap', 'Slow', 'Topple', 'Vex']
                                if mastery in mastery_keywords:
                                    mastery_options_map[opt.get('id')] = {
                                        'weapon': weapon,
                                        'mastery': mastery,
                                        'description': description
                                    }

                    break

            # If no mastery options found, character doesn't have weapon mastery feature
            if not mastery_options_map:
                return []

            # Check class choices for selected masteries
            class_choices = choices.get('class', [])
            for choice in class_choices:
                option_value = choice.get('optionValue')

                # If this option ID matches a mastery option, add it
                if option_value and option_value in mastery_options_map:
                    mastery_info = mastery_options_map[option_value]
                    weapon_masteries.append(mastery_info)
                    self.logger.debug(f"Found weapon mastery: {mastery_info['weapon']} ({mastery_info['mastery']})")

            return weapon_masteries

        except Exception as e:
            self.logger.error(f"Error extracting weapon masteries: {e}")
            return []

    def _should_allow_weapon_proficiency(self, modifier: Dict[str, Any], character_data: Dict[str, Any]) -> bool:
        """Determine if a weapon proficiency should be allowed based on D&D 5e multiclass rules."""
        available_to_multiclass = modifier.get('availableToMulticlass', True)
        
        # Check if multiclass
        classes = character_data.get('classes', [])
        is_multiclass = len(classes) > 1
        
        # For single class characters, allow all proficiencies
        if not is_multiclass:
            return True
        
        # For multiclass characters: if availableToMulticlass is True, allow it
        if available_to_multiclass:
            return True
        
        # For multiclass characters with availableToMulticlass=False:
        # Apply D&D 5e rule - only allow weapon proficiencies from the first/starting class
        component_id = modifier.get('componentId')
        if not component_id:
            return False
            
        return self._is_from_starting_class(component_id, character_data)
    
    def _get_armor_proficiencies(self, character_data: Dict[str, Any]) -> List[str]:
        """Get list of armor proficiencies from D&D Beyond data."""
        armor_proficiencies = []
        seen_armor = set()
        
        # Extract armor proficiencies from modifiers
        modifiers = character_data.get('modifiers', {})
        
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                if not isinstance(modifier, dict):
                    continue
                    
                # Only accept proficiency type modifiers
                if modifier.get('type') != 'proficiency':
                    continue
                    
                # Must be granted
                if not modifier.get('isGranted'):
                    continue
                    
                subtype = modifier.get('subType', '')
                
                # Check for armor proficiencies
                armor_types = ['light-armor', 'medium-armor', 'heavy-armor', 'shields']
                if subtype in armor_types:
                    armor_name = subtype.replace('-', ' ').title()
                    if armor_name not in seen_armor:
                        armor_proficiencies.append(armor_name)
                        seen_armor.add(armor_name)
                        logger.debug(f"Armor proficiency: {armor_name} (source: {source_type})")
        
        return sorted(armor_proficiencies)
    
    def _get_expertise_skills(self, character_data: Dict[str, Any]) -> List[str]:
        """Get list of skills with expertise."""
        expertise_skills = []
        
        # Extract expertise from modifiers (D&D Beyond API structure)
        modifiers = character_data.get('modifiers', {})
        
        # Process modifiers from all sources
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                if self._is_expertise_modifier(modifier):
                    skill_name = self._extract_skill_from_modifier(modifier)
                    if skill_name:
                        expertise_skills.append(skill_name)
                        logger.debug(f"Found skill expertise: {skill_name} (source: {source_type})")
        
        return expertise_skills
    
    def _is_expertise_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier grants skill expertise."""
        if not isinstance(modifier, dict):
            return False
        
        friendly_type = modifier.get('friendlyTypeName', '').lower()
        friendly_subtype = modifier.get('friendlySubtypeName', '').lower()
        
        # Look for expertise keywords
        expertise_keywords = ['expertise', 'double']
        return any(keyword in friendly_type or keyword in friendly_subtype for keyword in expertise_keywords)
    
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
    
    def _is_tool_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier grants tool proficiency."""
        if not isinstance(modifier, dict):
            return False
        
        subtype = modifier.get('subType', '').lower()
        friendly_subtype = modifier.get('friendlySubtypeName', '').lower()
        friendly_type = modifier.get('friendlyTypeName', '').lower()
        
        # Tool keywords to look for
        tool_keywords = ['supplies', 'kit', 'tools', 'set', 'instrument']
        
        # Check if it's a tool type or contains tool keywords
        return ('tool' in friendly_type or 
                any(keyword in friendly_subtype for keyword in tool_keywords))
    
    def _extract_tool_from_modifier(self, modifier: Dict[str, Any], source_type: str, character_data: Dict[str, Any]) -> Optional[str]:
        """Extract tool name from a modifier."""
        friendly_subtype = modifier.get('friendlySubtypeName', '')
        if friendly_subtype:
            return friendly_subtype
        
        subtype = modifier.get('subType', '')
        if subtype:
            return subtype
        
        return None
    
    def _build_change_detection_data(self, proficiency_data: ProficiencyData, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build change detection compatible proficiency data."""
        # Get lists of proficient skills, abilities with saving throw proficiency, etc.
        proficient_skills, _ = self._get_proficient_skills(character_data)  # Ignore sources here
        expertise_skills = self._get_expertise_skills(character_data)
        saving_throw_proficiencies = self._get_proficient_saving_throws(character_data)
        
        # Build nested structure expected by change detection
        change_detection_data = {
            'skills': {},
            'saving_throws': {},
            'languages': {},
            'tools': {},
            'weapons': proficiency_data.weapon_proficiencies,
            'armor': proficiency_data.armor_proficiencies
        }
        
        # Skills with proficiency/expertise flags
        for skill in self.skill_abilities.keys():
            is_proficient = skill in proficient_skills
            has_expertise = skill in expertise_skills
            change_detection_data['skills'][skill] = {
                'proficient': is_proficient,
                'expertise': has_expertise
            }
        
        # Saving throws with proficiency flags  
        for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
            is_proficient = ability in saving_throw_proficiencies
            change_detection_data['saving_throws'][ability] = is_proficient
        
        # Languages as boolean flags
        for language in proficiency_data.language_proficiencies:
            # Normalize language name for field path
            lang_key = language.lower().replace("'", "'").replace(" ", "_")
            change_detection_data['languages'][lang_key] = True
        
        # Tools as boolean flags
        for tool in proficiency_data.tool_proficiencies:
            # Normalize tool name for field path  
            tool_key = tool.lower().replace("'", "'").replace(" ", "_")
            change_detection_data['tools'][tool_key] = True
        
        return change_detection_data