"""
Enhanced Hit Points Calculator with new interface compliance.

This module provides an enhanced implementation of the hit points calculator
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
class HitPointsData:
    """Data class for hit points information."""
    current_hp: int
    max_hp: int
    temp_hp: int
    hit_dice_total: int
    hit_dice_used: int
    hit_dice_remaining: int
    hit_die_type: str
    hp_calculation_method: str
    hp_breakdown: Dict[str, int]
    
    def __post_init__(self):
        if self.max_hp < 1:
            raise ValueError(f"Max HP must be at least 1, got {self.max_hp}")
        if self.current_hp < 0:
            raise ValueError(f"Current HP cannot be negative, got {self.current_hp}")
        if self.temp_hp < 0:
            raise ValueError(f"Temporary HP cannot be negative, got {self.temp_hp}")
        if self.hit_dice_used > self.hit_dice_total:
            raise ValueError(f"Used hit dice ({self.hit_dice_used}) cannot exceed total ({self.hit_dice_total})")


class EnhancedHitPointsCalculator(RuleAwareCalculator, ICachedCalculator):
    """
    Enhanced hit points calculator with new interface compliance.
    
    Features:
    - Full interface compliance with ICalculator, IRuleAwareCalculator, ICachedCalculator
    - Comprehensive HP calculation methods (manual, rolled, average)
    - Hit dice tracking and management
    - Enhanced validation and error handling
    - Performance monitoring and caching
    - Rule version support for HP calculation differences
    """
    
    def __init__(self, config_manager=None, rule_manager: Optional[RuleVersionManager] = None):
        """
        Initialize the enhanced hit points calculator.
        
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
        
        # Initialize HP constants
        self._setup_hp_constants()
        
        # Performance tracking
        self.metrics = {
            'total_calculations': 0,
            'total_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'validation_failures': 0
        }
    
    def _setup_hp_constants(self):
        """Setup HP calculation constants."""
        # Hit die sizes by class
        self.hit_dice_by_class = {
            'barbarian': 12,
            'fighter': 10,
            'paladin': 10,
            'ranger': 10,
            'bard': 8,
            'cleric': 8,
            'druid': 8,
            'monk': 8,
            'rogue': 8,
            'warlock': 8,
            'sorcerer': 6,
            'wizard': 6
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
        return CalculatorType.HIT_POINTS
    
    @property
    def name(self) -> str:
        """Get the human-readable name of this calculator."""
        return "Enhanced Hit Points Calculator"
    
    @property
    def version(self) -> str:
        """Get the version of this calculator."""
        return "2.0.0"
    
    @property
    def dependencies(self) -> List[CalculatorType]:
        """Get the list of calculator types this calculator depends on."""
        return [CalculatorType.ABILITY_SCORE]  # Needs CON for HP calculation
    
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
            logger.debug(f"Calculating hit points with {rule_version.version.value} rules")
            
            # Calculate hit points
            hp_data = self._calculate_hit_points(character_data, rule_version)
            
            # Build result
            result_data = {
                'current_hp': hp_data.current_hp,
                'max_hp': hp_data.max_hp,
                'temp_hp': hp_data.temp_hp,
                'hit_dice': {
                    'total': hp_data.hit_dice_total,
                    'used': hp_data.hit_dice_used,
                    'remaining': hp_data.hit_dice_remaining,
                    'type': hp_data.hit_die_type
                },
                'hp_breakdown': hp_data.hp_breakdown,
                'calculation_method': hp_data.hp_calculation_method,
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
            logger.error(f"Error in hit points calculation: {str(e)}")
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
        
        # Check for required data
        if 'stats' not in character_data:
            errors.append("Missing required 'stats' field for CON modifier calculation")
        else:
            stats = character_data['stats']
            if not isinstance(stats, list):
                errors.append("'stats' field must be a list")
            else:
                # Check for CON specifically
                con_found = any(stat.get('id') == 3 for stat in stats if isinstance(stat, dict))
                if not con_found:
                    errors.append("Constitution score not found in stats")
        
        if 'classes' not in character_data:
            errors.append("Missing required 'classes' field for hit die calculation")
        else:
            classes = character_data['classes']
            if not isinstance(classes, list) or len(classes) == 0:
                errors.append("'classes' field must be a non-empty list")
        
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
                "current_hp": {"type": "integer", "minimum": 0},
                "max_hp": {"type": "integer", "minimum": 1},
                "temp_hp": {"type": "integer", "minimum": 0},
                "hit_dice": {
                    "type": "object",
                    "properties": {
                        "total": {"type": "integer", "minimum": 1},
                        "used": {"type": "integer", "minimum": 0},
                        "remaining": {"type": "integer", "minimum": 0},
                        "type": {"type": "string", "pattern": "^d(4|6|8|10|12)$"}
                    },
                    "required": ["total", "used", "remaining", "type"]
                },
                "hp_breakdown": {
                    "type": "object",
                    "properties": {
                        "base_hp": {"type": "integer"},
                        "con_bonus": {"type": "integer"},
                        "class_bonus": {"type": "integer"},
                        "feat_bonus": {"type": "integer"},
                        "item_bonus": {"type": "integer"},
                        "misc_bonus": {"type": "integer"}
                    }
                },
                "calculation_method": {"type": "string"},
                "rule_version": {"type": "string", "enum": ["2014", "2024"]}
            },
            "required": ["current_hp", "max_hp", "temp_hp", "hit_dice", "hp_breakdown", "calculation_method", "rule_version"]
        }
    
    def get_required_fields(self) -> List[str]:
        """
        Get the list of required fields in the input data.
        
        Returns:
            List of required field names
        """
        return ['stats', 'classes']
    
    def get_optional_fields(self) -> List[str]:
        """
        Get the list of optional fields in the input data.
        
        Returns:
            List of optional field names
        """
        return ['modifiers', 'feats', 'race', 'hitPointInfo']
    
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
            'classes': character_data.get('classes', []),
            'modifiers': character_data.get('modifiers', {}),
            'hitPointInfo': character_data.get('hitPointInfo', {}),
            'rule_version': context.rule_version,
            'character_id': context.character_id
        }
        
        # Sort keys for consistent hashing
        cache_json = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_json.encode()).hexdigest()
        
        return f"hit_points_{cache_hash}"
    
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
    def _calculate_hit_points(self, character_data: Dict[str, Any], rule_version) -> HitPointsData:
        """
        Calculate hit points with comprehensive breakdown.
        
        Args:
            character_data: Character data from D&D Beyond
            rule_version: Detected rule version
            
        Returns:
            HitPointsData object with complete breakdown
        """
        # Get character level and CON modifier
        total_level, con_modifier = self._get_level_and_con_modifier(character_data)
        
        # Check for rolled HP first (overrideHitPoints in raw data)
        raw_data = character_data.get('_raw_data', {})
        override_hp = raw_data.get('overrideHitPoints', 0) or 0

        # Get removed HP and temp HP directly from raw data (more reliable than data transformer)
        removed_hp = raw_data.get('removedHitPoints', 0) or 0
        temp_hp = raw_data.get('temporaryHitPoints', 0) or 0

        # Get hit point info if available (from data transformer) - use as fallback only
        hp_info = character_data.get('hit_points', character_data.get('hitPointInfo', {}))
        max_hp_from_info = hp_info.get('maximum', 0) or 0

        # Check if we have baseHitPoints (rolled HP without modifiers)
        base_hp_raw = raw_data.get('baseHitPoints', 0) or 0

        # Priority order: overrideHitPoints (true override) > calculate from baseHitPoints > hitPointInfo.maximum > calculated
        if override_hp > 0:
            # True override from DDB
            max_hp = override_hp
            calculation_method = "rolled_override"
            base_hp = max_hp - (con_modifier * total_level)
        elif base_hp_raw > 0:
            # We have rolled HP (baseHitPoints) - need to add Con and other bonuses
            calculation_method = "rolled"
            base_hp = base_hp_raw
            # Start with base rolled HP, add con modifier
            max_hp = base_hp + (con_modifier * total_level)
        elif max_hp_from_info > 0:
            # Manual override or pre-calculated
            calculation_method = "manual_override"
            base_hp = max_hp_from_info - (con_modifier * total_level)
            max_hp = max_hp_from_info
        else:
            # Calculate HP from class and CON
            max_hp, base_hp, calculation_method = self._calculate_max_hp(character_data, total_level, con_modifier)

        # Calculate current HP from max HP and removed HP (always recalculate from raw data)
        current_hp = max(0, max_hp - removed_hp)
        
        # Get hit dice information
        hit_dice_info = self._calculate_hit_dice_info(character_data)
        
        # Build HP breakdown
        hp_breakdown = {
            'base_hp': base_hp or 0,
            'con_bonus': (con_modifier * total_level) or 0,
            'race_bonus': self._get_race_hp_bonus(character_data, total_level) or 0,
            'class_bonus': self._get_class_hp_bonus(character_data) or 0,
            'feat_bonus': self._get_feat_hp_bonus(character_data) or 0,
            'item_bonus': self._get_item_hp_bonus(character_data) or 0,
            'misc_bonus': self._get_misc_hp_bonus(character_data) or 0
        }

        # Adjust max HP with bonuses
        total_bonuses = (hp_breakdown['race_bonus'] + hp_breakdown['class_bonus'] +
                        hp_breakdown['feat_bonus'] + hp_breakdown['item_bonus'] +
                        hp_breakdown['misc_bonus'])
        max_hp += total_bonuses
        
        return HitPointsData(
            current_hp=max(0, current_hp),
            max_hp=max(1, max_hp),
            temp_hp=max(0, temp_hp),
            hit_dice_total=hit_dice_info['total'],
            hit_dice_used=hit_dice_info['used'],
            hit_dice_remaining=hit_dice_info['remaining'],
            hit_die_type=hit_dice_info['type'],
            hp_calculation_method=calculation_method,
            hp_breakdown=hp_breakdown
        )
    
    def _get_level_and_con_modifier(self, character_data: Dict[str, Any]) -> Tuple[int, int]:
        """Get total character level and constitution modifier."""
        # Get total level from classes
        classes = character_data.get('classes', [])
        total_level = sum(cls.get('level', 0) for cls in classes)
        if total_level == 0:
            total_level = 1  # Default to level 1
        
        # Get CON modifier
        con_modifier = self._get_ability_modifier(character_data, 3)  # Constitution ID = 3
        
        return total_level, con_modifier
    
    def _get_ability_modifier(self, character_data: Dict[str, Any], ability_id: int) -> int:
        """Get ability modifier for a specific ability, including feat/item bonuses."""
        # Map ability ID to name and subType
        ability_map = {
            1: ('strength', 'strength-score'),
            2: ('dexterity', 'dexterity-score'),
            3: ('constitution', 'constitution-score'),
            4: ('intelligence', 'intelligence-score'),
            5: ('wisdom', 'wisdom-score'),
            6: ('charisma', 'charisma-score')
        }

        # First try to get from calculated ability scores (includes bonuses from feats, items, etc.)
        ability_scores = character_data.get('ability_scores', {})
        if ability_scores and ability_id in ability_map:
            ability_name = ability_map[ability_id][0]
            ability_score = ability_scores.get(ability_name)
            if isinstance(ability_score, dict):
                # If it's a dict with score/modifier, use it
                if 'score' in ability_score:
                    return DnDMath.ability_modifier(ability_score['score'])
            elif isinstance(ability_score, int):
                # If it's just a number, need to check for bonuses
                score = ability_score
                # Add bonuses from feats, items, etc.
                score += self._get_ability_bonuses_from_modifiers(character_data, ability_id, ability_map[ability_id][1])
                return DnDMath.ability_modifier(score)

        # Fallback: get from raw stats and add bonuses
        stats = character_data.get('stats', [])
        base_score = 10
        for stat in stats:
            if stat.get('id') == ability_id:
                base_score = stat.get('value', 10)
                break

        # Add bonuses from modifiers
        if ability_id in ability_map:
            base_score += self._get_ability_bonuses_from_modifiers(character_data, ability_id, ability_map[ability_id][1])

        return DnDMath.ability_modifier(base_score)

    def _get_ability_bonuses_from_modifiers(self, character_data: Dict[str, Any], ability_id: int, sub_type_pattern: str) -> int:
        """Get total bonuses to an ability score from all modifier sources."""
        total_bonus = 0
        modifiers = character_data.get('modifiers', {})

        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue

            for modifier in modifier_list:
                # Check if this modifier affects the specific ability
                mod_sub_type = modifier.get('subType', '')
                mod_stat_id = modifier.get('statId')
                mod_type = modifier.get('type', '')

                # Skip "set" type modifiers (those are handled elsewhere)
                if mod_type == 'set':
                    continue

                # Check if this modifier matches the ability
                if mod_sub_type == sub_type_pattern or mod_stat_id == ability_id:
                    bonus = modifier.get('value', 0) or modifier.get('fixedValue', 0) or modifier.get('bonus', 0)
                    if bonus:
                        total_bonus += bonus

        return total_bonus
    
    def _calculate_max_hp(self, character_data: Dict[str, Any], total_level: int, con_modifier: int) -> Tuple[int, int, str]:
        """Calculate maximum hit points from class levels."""
        classes = character_data.get('classes', [])
        
        if not classes:
            # No class data, use default
            base_hp = total_level * 6  # d8 average
            return base_hp + (con_modifier * total_level), base_hp, "estimated"
        
        total_base_hp = 0
        calculation_method = "calculated"
        
        for class_data in classes:
            class_name = class_data.get('definition', {}).get('name', '').lower()
            class_level = class_data.get('level', 1)
            
            # Get hit die size for this class
            hit_die_size = self._get_hit_die_size(class_name)
            
            # First level gets max hit die + CON
            first_level_hp = hit_die_size
            
            # Subsequent levels - for now assume average
            if class_level > 1:
                avg_hp_per_level = DnDMath.hit_dice_average(hit_die_size)
                remaining_levels_hp = (class_level - 1) * avg_hp_per_level
                total_base_hp += first_level_hp + remaining_levels_hp
            else:
                total_base_hp += first_level_hp
        
        total_hp = int(total_base_hp) + (con_modifier * total_level)
        
        return total_hp, int(total_base_hp), calculation_method
    
    def _get_hit_die_size(self, class_name: str) -> int:
        """Get hit die size for a class."""
        class_name = class_name.lower()
        
        # Check exact matches first
        if class_name in self.hit_dice_by_class:
            return self.hit_dice_by_class[class_name]
        
        # Check partial matches
        for known_class, hit_die in self.hit_dice_by_class.items():
            if known_class in class_name:
                return hit_die
        
        # Default to d8 if unknown
        return 8
    
    def _calculate_hit_dice_info(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate hit dice information."""
        classes = character_data.get('classes', [])
        
        if not classes:
            return {'total': 1, 'used': 0, 'remaining': 1, 'type': 'd8'}
        
        # For multiclass, use the primary class hit die
        primary_class = max(classes, key=lambda c: c.get('level', 0))
        primary_class_name = primary_class.get('definition', {}).get('name', '').lower()
        hit_die_size = self._get_hit_die_size(primary_class_name)
        
        # Total hit dice equals total level
        total_level = sum(cls.get('level', 0) for cls in classes)
        
        # Get used hit dice from character data if available
        hit_dice_used = character_data.get('hitDiceUsed', 0)
        
        return {
            'total': total_level,
            'used': hit_dice_used,
            'remaining': total_level - hit_dice_used,
            'type': f'd{hit_die_size}'
        }
    
    def _get_class_hp_bonus(self, character_data: Dict[str, Any]) -> int:
        """Get HP bonus from class features."""
        # Check for class-based HP bonuses (like Draconic Resilience)
        bonus = 0
        
        # Method 1: Check subclass definition (for raw data)
        classes = character_data.get('classes', [])
        for class_data in classes:
            class_name = class_data.get('definition', {}).get('name', '').lower()
            class_level = class_data.get('level', 1)
            
            # Draconic Resilience: +3 HP + 1 HP per additional Sorcerer level beyond 3rd
            if 'sorcerer' in class_name and class_level >= 3:
                subclass = class_data.get('subclassDefinition', {}).get('name', '')
                if 'draconic' in subclass.lower():
                    # Base +3 HP at level 3, plus +1 for each level beyond 3rd
                    bonus += 3 + (class_level - 3)
        
        # Method 2: Check features directly (for processed data)
        if bonus == 0:  # Only check features if not found via subclass
            features = character_data.get('features', {})
            class_features = features.get('class_features', [])
            
            for feature in class_features:
                feature_name = feature.get('name', '').lower()
                if 'draconic resilience' in feature_name:
                    # Get sorcerer level - look for any sorcerer class
                    sorcerer_level = 0
                    
                    # Check character_info.classes (processed data format)
                    character_info = character_data.get('character_info', {})
                    info_classes = character_info.get('classes', [])
                    for cls in info_classes:
                        if 'sorcerer' in cls.get('name', '').lower():
                            sorcerer_level = cls.get('level', 1)
                            break
                    
                    # Fallback to raw classes format
                    if sorcerer_level == 0:
                        for class_data in classes:
                            class_name = class_data.get('definition', {}).get('name', '').lower()
                            if 'sorcerer' in class_name:
                                sorcerer_level = class_data.get('level', 1)
                                break
                    
                    if sorcerer_level >= 3:  # Feature starts at level 3
                        # Draconic Resilience: +3 HP + 1 HP per additional Sorcerer level beyond 3rd
                        bonus += 3 + (sorcerer_level - 3)
                        break
        
        return bonus
    
    def _get_feat_hp_bonus(self, character_data: Dict[str, Any]) -> int:
        """Get HP bonus from feats (e.g., Tough)."""
        modifiers = character_data.get('modifiers', {})
        feat_modifiers = modifiers.get('feat', [])
        bonus = 0

        # Get total level for per-level bonuses
        classes = character_data.get('classes', [])
        total_level = sum(cls.get('level', 0) for cls in classes) or 1

        for modifier in feat_modifiers:
            sub_type = modifier.get('subType', '').lower()

            # Check for hit-points-per-level (e.g., Tough feat: +2 HP per level)
            if 'hit-point' in sub_type and 'per-level' in sub_type:
                value_per_level = modifier.get('value', 0) or modifier.get('fixedValue', 0)
                bonus += value_per_level * total_level
            # Check for flat HP modifiers
            elif self._is_hp_modifier(modifier):
                bonus += modifier.get('value', 0) or modifier.get('fixedValue', 0)

        return bonus
    
    def _get_item_hp_bonus(self, character_data: Dict[str, Any]) -> int:
        """Get HP bonus from magic items (only equipped/worn items)."""
        modifiers = character_data.get('modifiers', {})
        item_modifiers = modifiers.get('item', [])
        inventory = character_data.get('inventory', [])
        bonus = 0

        for modifier in item_modifiers:
            if self._is_hp_modifier(modifier):
                # Get the item component ID to check if it's equipped
                component_id = modifier.get('componentId')

                # Check if this item is equipped
                is_equipped = False
                for item in inventory:
                    item_def_id = item.get('definition', {}).get('id')
                    if item_def_id == component_id:
                        is_equipped = item.get('equipped', False)
                        break

                # Only add bonus if item is equipped (worn items like rings, belts, etc.)
                # This excludes potions and other consumables
                if is_equipped:
                    bonus += modifier.get('value', 0) or modifier.get('fixedValue', 0)

        return bonus

    def _get_race_hp_bonus(self, character_data: Dict[str, Any], total_level: int) -> int:
        """Get HP bonus from race/species features (e.g., Dwarf Toughness)."""
        modifiers = character_data.get('modifiers', {})
        race_modifiers = modifiers.get('race', [])
        bonus = 0

        for modifier in race_modifiers:
            sub_type = modifier.get('subType', '').lower()

            # Check for hit-points-per-level (e.g., Dwarf Toughness)
            if 'hit-point' in sub_type and 'per-level' in sub_type:
                value_per_level = modifier.get('value', 0) or modifier.get('fixedValue', 0)
                bonus += value_per_level * total_level
            # Check for flat HP modifiers
            elif self._is_hp_modifier(modifier):
                bonus += modifier.get('value', 0) or modifier.get('fixedValue', 0)

        return bonus

    def _get_misc_hp_bonus(self, character_data: Dict[str, Any]) -> int:
        """Get HP bonus from other sources."""
        modifiers = character_data.get('modifiers', {})
        bonus = 0
        
        for source_type, modifier_list in modifiers.items():
            if source_type in ['feat', 'item', 'class', 'race']:
                continue  # Already handled
                
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                if self._is_hp_modifier(modifier):
                    bonus += modifier.get('value', 0)
        
        return bonus
    
    def _is_hp_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if modifier affects hit points."""
        modifies_type_id = modifier.get('modifiesTypeId')
        sub_type = modifier.get('subType', '').lower()
        
        # HP modifier type ID
        if modifies_type_id == 1:  # Assuming 1 is HP in D&D Beyond
            return True
            
        # Check subtype for HP modifiers
        if 'hit-point' in sub_type or 'hp' in sub_type or 'hitpoint' in sub_type:
            return True
            
        return False