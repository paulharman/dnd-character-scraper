"""
Enhanced Ability Score Calculator with new interface compliance.

This module provides an enhanced implementation of the ability score calculator
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
class AbilityScoreData:
    """Data class for ability score information."""
    score: int
    modifier: int
    save_bonus: int
    source_breakdown: Dict[str, int]
    proficient_in_save: bool = False
    
    def __post_init__(self):
        if self.score < 1 or self.score > 50:
            raise ValueError(f"Ability score must be between 1 and 50, got {self.score}")
        
        expected_modifier = DnDMath.ability_modifier(self.score)
        if self.modifier != expected_modifier:
            logger.warning(f"Ability modifier {self.modifier} doesn't match expected {expected_modifier} for score {self.score}")


class EnhancedAbilityScoreCalculator(RuleAwareCalculator, ICachedCalculator):
    """
    Enhanced ability score calculator with new interface compliance.
    
    Features:
    - Full interface compliance with ICalculator, IRuleAwareCalculator, ICachedCalculator
    - Comprehensive rule version support (2014 vs 2024)
    - Enhanced validation and error handling
    - Performance monitoring and caching
    - Detailed source tracking and breakdown
    """
    
    def __init__(self, config_manager=None, rule_manager: Optional[RuleVersionManager] = None):
        """
        Initialize the enhanced ability score calculator.
        
        Args:
            config_manager: Configuration manager instance
            rule_manager: Rule version manager instance
        """
        super().__init__(config_manager, rule_manager)
        # Load configuration from main config system (uses performance.enable_caching)
        self.config = self.create_calculator_config_from_main(config_manager)
        self.validator = None  # Use custom validation instead of full CharacterDataValidator
        self.cache = {}
        self.cache_stats = {'hits': 0, 'misses': 0}
        
        # Initialize ability mappings
        self._setup_ability_mappings()
        
        # Performance tracking
        self.metrics = {
            'total_calculations': 0,
            'total_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'validation_failures': 0
        }
    
    def _setup_ability_mappings(self):
        """Setup ability name mappings and constants."""
        self.ability_names = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        
        # D&D Beyond ability ID mappings
        self.ability_id_map = {
            1: 'strength',
            2: 'dexterity', 
            3: 'constitution',
            4: 'intelligence',
            5: 'wisdom',
            6: 'charisma'
        }
        
        # Choice ID mappings for ASI selections
        self.choice_mappings = {
            # Standard ASI choice IDs from D&D Beyond
            1001: 'strength',
            1002: 'dexterity',
            1003: 'constitution', 
            1004: 'intelligence',
            1005: 'wisdom',
            1006: 'charisma'
        }
    
    # ICalculator interface implementation
    @property
    def calculator_type(self) -> CalculatorType:
        """Get the type of this calculator."""
        return CalculatorType.ABILITY_SCORE
    
    @property
    def name(self) -> str:
        """Get the human-readable name of this calculator."""
        return "Enhanced Ability Score Calculator"
    
    @property
    def version(self) -> str:
        """Get the version of this calculator."""
        return "2.0.0"
    
    @property
    def dependencies(self) -> List[CalculatorType]:
        """Get the list of calculator types this calculator depends on."""
        return []  # Ability scores are fundamental, no dependencies
    
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
            logger.debug(f"Calculating ability scores with {rule_version.version.value} rules")
            
            # Calculate ability scores
            ability_scores = self._calculate_ability_scores(character_data, rule_version)
            
            # Build result
            result_data = {
                'ability_scores': ability_scores,
                'ability_modifiers': {ability: data.modifier for ability, data in ability_scores.items()},
                'save_bonuses': {ability: data.save_bonus for ability, data in ability_scores.items()},
                'rule_version': rule_version.version.value,
                'calculation_method': 'enhanced_comprehensive'
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
            logger.error(f"Error in ability score calculation: {str(e)}")
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
        
        # Check for required stats data
        if 'stats' not in character_data:
            errors.append("Missing required 'stats' field")
            return False, errors
        
        stats = character_data['stats']
        if not isinstance(stats, list):
            errors.append("'stats' field must be a list")
            return False, errors
        
        if len(stats) == 0:
            errors.append("No ability scores provided")
            return False, errors
        
        # Validate each ability score
        for stat in stats:
            if not isinstance(stat, dict):
                errors.append("Each stat must be a dictionary")
                continue
            
            if 'id' not in stat:
                errors.append("Stat missing 'id' field")
                continue
            
            if 'value' not in stat:
                errors.append("Stat missing 'value' field")
                continue
            
            ability_id = stat['id']
            if ability_id not in self.ability_id_map:
                errors.append(f"Unknown ability ID: {ability_id}")
                continue
            
            value = stat['value']
            if not isinstance(value, (int, float)):
                errors.append(f"Ability score value must be numeric, got {type(value)}")
                continue
            
            if value < 1 or value > 50:
                errors.append(f"Ability score {value} out of valid range (1-50)")
        
        # No additional validation needed - we handle what we need above
        
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
                "ability_scores": {
                    "type": "object",
                    "properties": {
                        "strength": {"$ref": "#/definitions/ability_score"},
                        "dexterity": {"$ref": "#/definitions/ability_score"},
                        "constitution": {"$ref": "#/definitions/ability_score"},
                        "intelligence": {"$ref": "#/definitions/ability_score"},
                        "wisdom": {"$ref": "#/definitions/ability_score"},
                        "charisma": {"$ref": "#/definitions/ability_score"}
                    },
                    "required": ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
                },
                "ability_modifiers": {
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
                "save_bonuses": {
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
                "rule_version": {"type": "string", "enum": ["2014", "2024"]},
                "calculation_method": {"type": "string"}
            },
            "definitions": {
                "ability_score": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "integer", "minimum": 1, "maximum": 50},
                        "modifier": {"type": "integer", "minimum": -10, "maximum": 20},
                        "save_bonus": {"type": "integer"},
                        "source_breakdown": {
                            "type": "object",
                            "properties": {
                                "base": {"type": "integer"},
                                "racial": {"type": "integer"},
                                "feat": {"type": "integer"},
                                "asi": {"type": "integer"},
                                "item": {"type": "integer"},
                                "other": {"type": "integer"}
                            }
                        },
                        "proficient_in_save": {"type": "boolean"}
                    },
                    "required": ["score", "modifier", "save_bonus", "source_breakdown"]
                }
            }
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
        return ['modifiers', 'choices', 'classes', 'race', 'feats']
    
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
        # Create a hash based on relevant data
        import hashlib
        import json
        
        # Extract relevant fields for caching
        cache_data = {
            'stats': character_data.get('stats', []),
            'modifiers': character_data.get('modifiers', {}),
            'choices': character_data.get('choices', {}),
            'classes': character_data.get('classes', []),
            'race': character_data.get('race', {}),
            'rule_version': context.rule_version,
            'character_id': context.character_id
        }
        
        # Sort keys for consistent hashing
        cache_json = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_json.encode()).hexdigest()
        
        return f"ability_scores_{cache_hash}"
    
    # ICachedCalculator interface implementation
    def get_from_cache(self, cache_key: str) -> Optional[CalculationResult]:
        """
        Get calculation result from cache.
        
        Args:
            cache_key: Cache key to look up
            
        Returns:
            Cached result or None if not found
        """
        return self.cache.get(cache_key)
    
    def store_in_cache(self, cache_key: str, result: CalculationResult, ttl: Optional[int] = None) -> None:
        """
        Store calculation result in cache.
        
        Args:
            cache_key: Cache key
            result: Result to cache
            ttl: Time to live in seconds (ignored for now)
        """
        self.cache[cache_key] = result
        
        # Simple cache size management
        if len(self.cache) > 1000:
            # Remove oldest entries
            keys_to_remove = list(self.cache.keys())[:100]
            for key in keys_to_remove:
                del self.cache[key]
    
    def invalidate_cache(self, cache_key: str) -> None:
        """
        Invalidate cached result.
        
        Args:
            cache_key: Cache key to invalidate
        """
        if cache_key in self.cache:
            del self.cache[cache_key]
    
    def clear_cache(self) -> None:
        """Clear all cached results for this calculator."""
        self.cache.clear()
        self.cache_stats = {'hits': 0, 'misses': 0}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache hit/miss stats
        """
        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'hit_rate': self.cache_stats['hits'] / (self.cache_stats['hits'] + self.cache_stats['misses']) if (self.cache_stats['hits'] + self.cache_stats['misses']) > 0 else 0,
            'cache_size': len(self.cache)
        }
    
    def configure(self, config: CalculatorConfig) -> None:
        """
        Configure calculator behavior.
        
        Args:
            config: Configuration settings
        """
        self.config = config
        
        # No validator setup needed - using custom validation
    
    def get_configuration(self) -> CalculatorConfig:
        """
        Get current calculator configuration.
        
        Returns:
            Current configuration
        """
        return self.config
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for this calculator.
        
        Returns:
            Dictionary with performance metrics
        """
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
    def _calculate_ability_scores(self, character_data: Dict[str, Any], rule_version) -> Dict[str, AbilityScoreData]:
        """
        Calculate ability scores with comprehensive breakdown.
        
        Args:
            character_data: Character data from D&D Beyond
            rule_version: Detected rule version
            
        Returns:
            Dictionary of ability names to AbilityScoreData objects
        """
        # Get base scores
        base_scores = self._calculate_base_scores(character_data)
        
        # Get all bonuses and set modifiers
        racial_bonuses = self._calculate_racial_bonuses(character_data, rule_version)
        feat_bonuses = self._calculate_feat_bonuses(character_data)
        asi_bonuses = self._calculate_asi_bonuses(character_data)
        item_bonuses = self._calculate_item_bonuses(character_data)
        other_bonuses = self._calculate_other_bonuses(character_data)
        set_modifiers = self._calculate_set_modifiers(character_data)
        
        # Get save proficiencies
        save_proficiencies = self._get_save_proficiencies(character_data)
        proficiency_bonus = self._get_proficiency_bonus(character_data)
        
        # Calculate final scores
        ability_scores = {}
        
        for ability in self.ability_names:
            base = base_scores.get(ability, 10)
            racial = racial_bonuses.get(ability, 0)
            feat = feat_bonuses.get(ability, 0)
            asi = asi_bonuses.get(ability, 0)
            item = item_bonuses.get(ability, 0)
            other = other_bonuses.get(ability, 0)
            set_modifier_info = set_modifiers.get(ability, None)

            # Calculate score without set modifiers first
            calculated_score = base + racial + feat + asi + other

            # Handle set modifiers with restrictions
            if set_modifier_info is not None:
                set_value = set_modifier_info['value']
                restriction = set_modifier_info.get('restriction', '')

                # Check if restriction applies
                if 'if not already higher' in restriction.lower():
                    # Only apply set if calculated score (without item bonus) is lower
                    if calculated_score < set_value:
                        final_score = set_value
                        source_breakdown = {
                            'base': base,
                            'set': set_value
                        }
                        if racial != 0:
                            source_breakdown['racial'] = racial
                        if feat != 0:
                            source_breakdown['feat'] = feat
                        if asi != 0:
                            source_breakdown['asi'] = asi
                        if other != 0:
                            source_breakdown['other'] = other
                    else:
                        # Score without item is already higher, don't apply set
                        final_score = calculated_score
                        source_breakdown = {'base': base}
                        if racial != 0:
                            source_breakdown['racial'] = racial
                        if feat != 0:
                            source_breakdown['feat'] = feat
                        if asi != 0:
                            source_breakdown['asi'] = asi
                        if other != 0:
                            source_breakdown['other'] = other
                else:
                    # No restriction or other restriction - apply set unconditionally
                    final_score = set_value
                    source_breakdown = {'base': base, 'set': set_value}
            else:
                # No set modifier, include item bonuses normally
                final_score = calculated_score + item
                source_breakdown = {'base': base}
                if racial != 0:
                    source_breakdown['racial'] = racial
                if feat != 0:
                    source_breakdown['feat'] = feat
                if asi != 0:
                    source_breakdown['asi'] = asi
                if item != 0:
                    source_breakdown['item'] = item
                if other != 0:
                    source_breakdown['other'] = other

            final_score = MathUtils.clamp(final_score, 1, 50)  # Clamp to valid range
            
            # Calculate modifier
            modifier = DnDMath.ability_modifier(final_score)
            
            # Calculate save bonus
            is_proficient = ability in save_proficiencies
            save_bonus = modifier + (proficiency_bonus if is_proficient else 0)
            
            # Create AbilityScoreData object
            ability_scores[ability] = AbilityScoreData(
                score=final_score,
                modifier=modifier,
                save_bonus=save_bonus,
                source_breakdown=source_breakdown,
                proficient_in_save=is_proficient
            )
        
        return ability_scores
    
    def _calculate_base_scores(self, character_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate base ability scores from character creation."""
        base_scores = {}
        stats = character_data.get('stats', [])
        
        for stat in stats:
            ability_id = stat.get('id')
            base_value = stat.get('value', 10)
            
            if ability_id in self.ability_id_map:
                ability_name = self.ability_id_map[ability_id]
                base_scores[ability_name] = base_value
        
        # Ensure all abilities are present
        for ability in self.ability_names:
            if ability not in base_scores:
                base_scores[ability] = 10
        
        return base_scores
    
    def _calculate_racial_bonuses(self, character_data: Dict[str, Any], rule_version) -> Dict[str, int]:
        """Calculate racial/species ability score bonuses."""
        racial_bonuses = {ability: 0 for ability in self.ability_names}
        
        # Check modifiers for racial bonuses first (common in test data)
        modifiers = character_data.get('modifiers', {})
        race_modifiers = modifiers.get('race', [])

        for modifier in race_modifiers:
            if self._is_ability_score_modifier(modifier):
                ability_name, bonus = self._extract_ability_modifier(modifier)
                if ability_name:
                    racial_bonuses[ability_name] += bonus
        
        # Get race data (full D&D Beyond format)
        race_data = character_data.get('race', {})
        if race_data:
            # Handle racial ability score increases
            race_definition = race_data.get('definition', {})
            asi_increases = race_definition.get('abilityScoreIncreases', [])
            
            for asi in asi_increases:
                ability_id = asi.get('entityId')
                value = asi.get('value', 0)
                
                if ability_id in self.ability_id_map:
                    ability_name = self.ability_id_map[ability_id]
                    racial_bonuses[ability_name] += value
            
            # Handle subrace bonuses
            subrace = race_data.get('subRace')
            if subrace:
                subrace_definition = subrace.get('definition', {})
                subrace_asi = subrace_definition.get('abilityScoreIncreases', [])
                
                for asi in subrace_asi:
                    ability_id = asi.get('entityId')
                    value = asi.get('value', 0)
                    
                    if ability_id in self.ability_id_map:
                        ability_name = self.ability_id_map[ability_id]
                        racial_bonuses[ability_name] += value
        
        return racial_bonuses
    
    def _calculate_feat_bonuses(self, character_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate ability score bonuses from feats."""
        feat_bonuses = {ability: 0 for ability in self.ability_names}

        # Check modifiers for feat-based bonuses
        modifiers = character_data.get('modifiers', {})
        feat_modifiers = modifiers.get('feat', [])

        # Check for 2024 background ASI feats (componentId 1789182 = Sailor ASI)
        # These should only apply in 2024 rules, not 2014 rules
        rule_version = character_data.get('rule_version', '2014')
        is_2024_rules = '2024' in str(rule_version)

        for modifier in feat_modifiers:
            # Skip 2024 background ASI if using 2014 rules
            # ComponentId 1789182 = Sailor Ability Score Improvements (2024 rules)
            if not is_2024_rules and modifier.get('componentId') == 1789182:
                logger.debug(f"Skipping 2024 background ASI modifier in 2014 rules: {modifier.get('friendlySubtypeName')}")
                continue

            if self._is_ability_score_modifier(modifier):
                ability_name, bonus = self._extract_ability_modifier(modifier)
                if ability_name:
                    feat_bonuses[ability_name] += bonus

        return feat_bonuses
    
    def _calculate_asi_bonuses(self, character_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate ability score improvements from ASI choices."""
        asi_bonuses = {ability: 0 for ability in self.ability_names}
        
        # Check modifiers for class ASI bonuses (common in test data)
        modifiers = character_data.get('modifiers', {})
        class_modifiers = modifiers.get('class', [])

        for modifier in class_modifiers:
            if self._is_ability_score_modifier(modifier):
                ability_name, bonus = self._extract_ability_modifier(modifier)
                if ability_name:
                    asi_bonuses[ability_name] += bonus
        
        # Check choices for ASI selections
        choices = character_data.get('choices', {})
        
        for source_type, choice_list in choices.items():
            if not isinstance(choice_list, list):
                continue
                
            for choice in choice_list:
                if self._is_asi_choice(choice):
                    ability_name, bonus = self._extract_asi_choice(choice)
                    if ability_name:
                        asi_bonuses[ability_name] += bonus
        
        return asi_bonuses
    
    def _calculate_item_bonuses(self, character_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate ability score bonuses from magic items."""
        item_bonuses = {ability: 0 for ability in self.ability_names}
        
        # Check modifiers for item-based bonuses
        modifiers = character_data.get('modifiers', {})
        item_modifiers = modifiers.get('item', [])
        
        for modifier in item_modifiers:
            if self._is_ability_score_modifier(modifier):
                ability_name, bonus = self._extract_ability_modifier(modifier)
                if ability_name:
                    item_bonuses[ability_name] += bonus
        
        return item_bonuses
    
    def _calculate_other_bonuses(self, character_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate ability score bonuses from other sources."""
        other_bonuses = {ability: 0 for ability in self.ability_names}
        
        # Check for other modifier sources
        modifiers = character_data.get('modifiers', {})
        
        for source_type, modifier_list in modifiers.items():
            if source_type in ['race', 'feat', 'item', 'class']:
                continue  # Already handled
                
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                if self._is_ability_score_modifier(modifier):
                    ability_name, bonus = self._extract_ability_modifier(modifier)
                    if ability_name:
                        other_bonuses[ability_name] += bonus
        
        return other_bonuses
    
    def _calculate_set_modifiers(self, character_data: Dict[str, Any]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Calculate ability score set modifiers (overrides).

        Returns:
            Dictionary mapping ability names to set modifier info:
            {'value': int, 'restriction': str} or None
        """
        set_modifiers = {ability: None for ability in self.ability_names}

        # Check all modifier sources for set modifiers
        modifiers = character_data.get('modifiers', {})

        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue

            for modifier in modifier_list:
                if self._is_ability_score_modifier(modifier) and modifier.get('type') == 'set':
                    ability_name, set_value = self._extract_ability_modifier(modifier)
                    if ability_name:
                        restriction = modifier.get('restriction', '')
                        set_modifiers[ability_name] = {
                            'value': set_value,
                            'restriction': restriction
                        }

        return set_modifiers
    
    def _is_ability_score_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier affects ability scores."""
        modifies_id = modifier.get('modifiesId')
        modifies_type_id = modifier.get('modifiesTypeId')
        sub_type = modifier.get('subType', '')
        stat_id = modifier.get('statId')

        # Traditional ability score modifiers
        if modifies_type_id == 1 and modifies_id in self.ability_id_map:
            return True

        # New format with subType (e.g., 'ability-score', 'strength-score', etc.)
        if sub_type.endswith('-score'):
            # Check if it's a valid ability score (not armor-class, saving-throw, etc.)
            ability_part = sub_type.replace('-score', '')
            if ability_part in self.ability_names or ability_part == 'ability':
                return True

        # Format with statId (only for modifiers that appear to be ability-related)
        # Exclude modifiers that are clearly not ability scores (e.g., armor-class, saving-throws)
        if stat_id in self.ability_id_map:
            # Only consider it an ability score modifier if subType suggests it
            # or if modifiesTypeId indicates ability score modification
            if 'score' in sub_type or modifies_type_id == 1:
                return True

        return False
    
    def _extract_ability_modifier(self, modifier: Dict[str, Any]) -> Tuple[Optional[str], int]:
        """Extract ability name and bonus from a modifier."""
        modifies_id = modifier.get('modifiesId')
        sub_type = modifier.get('subType', '')
        stat_id = modifier.get('statId')

        # Extract value - prefer fixedValue, then value, then bonus
        bonus = modifier.get('fixedValue')
        if bonus is None:
            bonus = modifier.get('value')
        if bonus is None:
            bonus = modifier.get('bonus', 0)
        if bonus is None:
            bonus = 0

        # Traditional format
        if modifies_id in self.ability_id_map:
            ability_name = self.ability_id_map[modifies_id]
            return ability_name, bonus

        # Format with statId (common in test data)
        if stat_id in self.ability_id_map:
            ability_name = self.ability_id_map[stat_id]
            return ability_name, bonus

        # New format with specific ability in subType (e.g., 'strength-score')
        if sub_type.endswith('-score') and sub_type != 'ability-score':
            ability_name = sub_type.replace('-score', '')
            if ability_name in self.ability_names:
                return ability_name, bonus

        return None, 0
    
    def _is_asi_choice(self, choice: Dict[str, Any]) -> bool:
        """Check if a choice is an ASI selection."""
        choice_id = choice.get('choiceId')
        return choice_id in self.choice_mappings
    
    def _extract_asi_choice(self, choice: Dict[str, Any]) -> Tuple[Optional[str], int]:
        """Extract ability name and bonus from an ASI choice."""
        choice_id = choice.get('choiceId')
        
        if choice_id in self.choice_mappings:
            ability_name = self.choice_mappings[choice_id]
            return ability_name, 1  # ASI choices are typically +1
        
        return None, 0
    
    def _get_save_proficiencies(self, character_data: Dict[str, Any]) -> set:
        """Get set of saving throw proficiencies."""
        save_proficiencies = set()
        
        # Check class proficiencies
        classes = character_data.get('classes', [])
        for class_data in classes:
            class_def = class_data.get('definition', {})
            saving_throws = class_def.get('savingThrows', [])
            
            for save_throw in saving_throws:
                save_id = save_throw.get('id')
                if save_id in self.ability_id_map:
                    ability_name = self.ability_id_map[save_id]
                    save_proficiencies.add(ability_name)
        
        return save_proficiencies
    
    def _get_proficiency_bonus(self, character_data: Dict[str, Any]) -> int:
        """Get character's proficiency bonus based on level."""
        classes = character_data.get('classes', [])
        total_level = sum(cls.get('level', 0) for cls in classes) or 1
        return DnDMath.proficiency_bonus(total_level)