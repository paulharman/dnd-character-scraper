"""
Enhanced Speed Calculator with new interface compliance.

This module provides an enhanced implementation of the speed calculator
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
class SpeedData:
    """Data class for speed information."""
    walking_speed: int
    climbing_speed: int
    swimming_speed: int
    flying_speed: int
    burrowing_speed: int
    hover: bool
    speed_breakdown: Dict[str, int]
    special_movement: List[str]
    
    def __post_init__(self):
        if self.walking_speed < 0 or self.walking_speed > 200:
            raise ValueError(f"Walking speed must be between 0 and 200, got {self.walking_speed}")
        
        for speed_type, speed in [("climbing", self.climbing_speed), ("swimming", self.swimming_speed), 
                                 ("flying", self.flying_speed), ("burrowing", self.burrowing_speed)]:
            if speed < 0 or speed > 200:
                raise ValueError(f"{speed_type.title()} speed must be between 0 and 200, got {speed}")


class EnhancedSpeedCalculator(RuleAwareCalculator, ICachedCalculator):
    """
    Enhanced speed calculator with new interface compliance.
    
    Features:
    - Full interface compliance with ICalculator, IRuleAwareCalculator, ICachedCalculator
    - Comprehensive speed calculation for all movement types
    - Enhanced validation and error handling
    - Performance monitoring and caching
    - Rule version support for speed calculation differences
    """
    
    def __init__(self, config_manager=None, rule_manager: Optional[RuleVersionManager] = None):
        """
        Initialize the enhanced speed calculator.
        
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
        
        # Initialize speed constants
        self._setup_speed_constants()
        
        # Performance tracking
        self.metrics = {
            'total_calculations': 0,
            'total_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'validation_failures': 0
        }
    
    def _setup_speed_constants(self):
        """Setup speed calculation constants."""
        # Base speeds by race
        self.base_speeds = {
            'human': 30,
            'elf': 30,
            'dwarf': 25,
            'halfling': 25,
            'dragonborn': 30,
            'gnome': 25,
            'half-elf': 30,
            'half-orc': 30,
            'tiefling': 30,
            'aarakocra': 25,  # but has 50 ft fly speed
            'aasimar': 30,
            'bugbear': 30,
            'firbolg': 30,
            'githyanki': 30,
            'githzerai': 30,
            'goblin': 30,
            'goliath': 30,
            'hobgoblin': 30,
            'kenku': 30,
            'kobold': 30,
            'lizardfolk': 30,  # plus 30 ft swim
            'orc': 30,
            'tabaxi': 30,
            'triton': 30,  # plus 30 ft swim
            'yuan-ti': 30
        }
        
        # Special racial speeds
        self.racial_special_speeds = {
            'aarakocra': {'flying_speed': 50},
            'lizardfolk': {'swimming_speed': 30},
            'triton': {'swimming_speed': 30},
            'genasi_air': {'flying_speed': 30},
            'variant_human': {},  # No special speeds
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
        return CalculatorType.SPEED
    
    @property
    def name(self) -> str:
        """Get the human-readable name of this calculator."""
        return "Enhanced Speed Calculator"
    
    @property
    def version(self) -> str:
        """Get the version of this calculator."""
        return "2.0.0"
    
    @property
    def dependencies(self) -> List[CalculatorType]:
        """Get the list of calculator types this calculator depends on."""
        return []  # Speed calculation is generally independent
    
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
            logger.debug(f"Calculating speed with {rule_version.version.value} rules")
            
            # Calculate speed
            speed_data = self._calculate_speed(character_data, rule_version)
            
            # Build result
            result_data = {
                'walking_speed': speed_data.walking_speed,
                'climbing_speed': speed_data.climbing_speed,
                'swimming_speed': speed_data.swimming_speed,
                'flying_speed': speed_data.flying_speed,
                'burrowing_speed': speed_data.burrowing_speed,
                'hover': speed_data.hover,
                'speed_breakdown': speed_data.speed_breakdown,
                'special_movement': speed_data.special_movement,
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
            logger.error(f"Error in speed calculation: {str(e)}")
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
        
        # Speed calculation is quite robust and can work with minimal data
        # We mainly need race information for base speed
        
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
                "walking_speed": {"type": "integer", "minimum": 0, "maximum": 200},
                "climbing_speed": {"type": "integer", "minimum": 0, "maximum": 200},
                "swimming_speed": {"type": "integer", "minimum": 0, "maximum": 200},
                "flying_speed": {"type": "integer", "minimum": 0, "maximum": 200},
                "burrowing_speed": {"type": "integer", "minimum": 0, "maximum": 200},
                "hover": {"type": "boolean"},
                "speed_breakdown": {
                    "type": "object",
                    "properties": {
                        "base_speed": {"type": "integer"},
                        "racial_bonus": {"type": "integer"},
                        "class_bonus": {"type": "integer"},
                        "feat_bonus": {"type": "integer"},
                        "item_bonus": {"type": "integer"},
                        "spell_bonus": {"type": "integer"},
                        "misc_bonus": {"type": "integer"}
                    }
                },
                "special_movement": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "rule_version": {"type": "string", "enum": ["2014", "2024"]}
            },
            "required": ["walking_speed", "climbing_speed", "swimming_speed", "flying_speed", "burrowing_speed", "hover", "speed_breakdown", "special_movement", "rule_version"]
        }
    
    def get_required_fields(self) -> List[str]:
        """
        Get the list of required fields in the input data.
        
        Returns:
            List of required field names
        """
        return []  # Speed calculation can work with minimal data
    
    def get_optional_fields(self) -> List[str]:
        """
        Get the list of optional fields in the input data.
        
        Returns:
            List of optional field names
        """
        return ['race', 'classes', 'modifiers', 'feats', 'inventory']
    
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
            'race': character_data.get('race', {}),
            'classes': character_data.get('classes', []),
            'modifiers': character_data.get('modifiers', {}),
            'feats': character_data.get('feats', []),
            'inventory': character_data.get('inventory', []),
            'rule_version': context.rule_version,
            'character_id': context.character_id
        }
        
        # Sort keys for consistent hashing
        cache_json = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_json.encode()).hexdigest()
        
        return f"speed_{cache_hash}"
    
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
    def _calculate_speed(self, character_data: Dict[str, Any], rule_version) -> SpeedData:
        """
        Calculate speed with comprehensive breakdown.
        
        Args:
            character_data: Character data from D&D Beyond
            rule_version: Detected rule version
            
        Returns:
            SpeedData object with complete breakdown
        """
        # Get base speed from race
        base_speed = self._get_base_speed(character_data)
        
        # Get speed bonuses from various sources
        racial_bonus = self._get_racial_speed_bonus(character_data)
        class_bonus = self._get_class_speed_bonus(character_data)
        feat_bonus = self._get_feat_speed_bonus(character_data)
        item_bonus = self._get_item_speed_bonus(character_data)
        spell_bonus = self._get_spell_speed_bonus(character_data)
        misc_bonus = self._get_misc_speed_bonus(character_data)
        
        # Calculate final walking speed
        walking_speed = base_speed + racial_bonus + class_bonus + feat_bonus + item_bonus + spell_bonus + misc_bonus
        walking_speed = max(0, walking_speed)  # Can't be negative
        
        # Get special movement speeds
        climbing_speed = self._get_climbing_speed(character_data)
        swimming_speed = self._get_swimming_speed(character_data)
        flying_speed = self._get_flying_speed(character_data)
        burrowing_speed = self._get_burrowing_speed(character_data)
        hover = self._has_hover(character_data)
        
        # Get special movement types
        special_movement = self._get_special_movement(character_data)
        
        # Build speed breakdown
        speed_breakdown = {
            'base_speed': base_speed,
            'racial_bonus': racial_bonus,
            'class_bonus': class_bonus,
            'feat_bonus': feat_bonus,
            'item_bonus': item_bonus,
            'spell_bonus': spell_bonus,
            'misc_bonus': misc_bonus
        }
        
        return SpeedData(
            walking_speed=walking_speed,
            climbing_speed=climbing_speed,
            swimming_speed=swimming_speed,
            flying_speed=flying_speed,
            burrowing_speed=burrowing_speed,
            hover=hover,
            speed_breakdown=speed_breakdown,
            special_movement=special_movement
        )
    
    def _get_base_speed(self, character_data: Dict[str, Any]) -> int:
        """Get base walking speed from race."""
        race_data = character_data.get('race', {})
        
        if not race_data:
            return 30  # Default human speed
        
        # Check for explicit speed in race definition
        race_definition = race_data.get('definition', {})
        speed_info = race_definition.get('movementSpeeds', [])
        
        for speed in speed_info:
            if speed.get('movementId') == 1:  # Walking speed ID
                return speed.get('speed', 30)
        
        # Fallback to race name lookup
        race_name = race_definition.get('name', '').lower()
        
        # Handle common race name variations
        for known_race, speed in self.base_speeds.items():
            if known_race in race_name:
                return speed
        
        # Default to 30 feet if unknown
        return 30
    
    def _get_racial_speed_bonus(self, character_data: Dict[str, Any]) -> int:
        """Get racial speed bonuses beyond base speed."""
        # Most racial speed bonuses are handled in base speed
        # This is for additional bonuses like Wood Elf fleet of foot
        race_data = character_data.get('race', {})
        
        if not race_data:
            return 0
        
        race_name = race_data.get('definition', {}).get('name', '').lower()
        
        # Wood Elf fleet of foot
        if 'wood elf' in race_name or 'high elf' in race_name:
            return 5  # +5 ft speed
        
        return 0
    
    def _get_class_speed_bonus(self, character_data: Dict[str, Any]) -> int:
        """Get speed bonuses from class features."""
        classes = character_data.get('classes', [])
        bonus = 0
        
        for class_data in classes:
            class_name = class_data.get('definition', {}).get('name', '').lower()
            class_level = class_data.get('level', 1)
            
            # Monk Unarmored Movement
            if 'monk' in class_name:
                if class_level >= 2:
                    # +10 ft at level 2, +5 ft every 4 levels after
                    unarmored_movement = 10 + ((class_level - 2) // 4) * 5
                    bonus = max(bonus, unarmored_movement)
            
            # Barbarian Fast Movement
            elif 'barbarian' in class_name:
                if class_level >= 5:
                    bonus = max(bonus, 10)
        
        return bonus
    
    def _get_feat_speed_bonus(self, character_data: Dict[str, Any]) -> int:
        """Get speed bonuses from feats."""
        modifiers = character_data.get('modifiers', {})
        feat_modifiers = modifiers.get('feat', [])
        bonus = 0
        
        for modifier in feat_modifiers:
            if self._is_speed_modifier(modifier):
                bonus += modifier.get('value', 0)
        
        return bonus
    
    def _get_item_speed_bonus(self, character_data: Dict[str, Any]) -> int:
        """Get speed bonuses from magic items."""
        modifiers = character_data.get('modifiers', {})
        item_modifiers = modifiers.get('item', [])
        bonus = 0
        
        for modifier in item_modifiers:
            if self._is_speed_modifier(modifier):
                bonus += modifier.get('value', 0)
        
        return bonus
    
    def _get_spell_speed_bonus(self, character_data: Dict[str, Any]) -> int:
        """Get speed bonuses from spells and magical effects."""
        # This would typically come from active spell effects
        # For now, return 0 as this is temporary
        return 0
    
    def _get_misc_speed_bonus(self, character_data: Dict[str, Any]) -> int:
        """Get miscellaneous speed bonuses."""
        modifiers = character_data.get('modifiers', {})
        bonus = 0
        
        for source_type, modifier_list in modifiers.items():
            if source_type in ['feat', 'item', 'class', 'race']:
                continue  # Already handled
                
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                if self._is_speed_modifier(modifier):
                    bonus += modifier.get('value', 0)
        
        return bonus
    
    def _get_climbing_speed(self, character_data: Dict[str, Any]) -> int:
        """Get climbing speed."""
        # Check for explicit climbing speed from race or class features
        race_data = character_data.get('race', {})
        
        if race_data:
            race_definition = race_data.get('definition', {})
            speed_info = race_definition.get('movementSpeeds', [])
            
            for speed in speed_info:
                if speed.get('movementId') == 2:  # Climbing speed ID
                    return speed.get('speed', 0)
        
        # Check for class features that grant climbing speed
        classes = character_data.get('classes', [])
        for class_data in classes:
            class_name = class_data.get('definition', {}).get('name', '').lower()
            class_level = class_data.get('level', 1)
            
            # Monk Wall Running (if unarmored)
            if 'monk' in class_name and class_level >= 9:
                return self._get_base_speed(character_data)  # Equal to walking speed
        
        return 0
    
    def _get_swimming_speed(self, character_data: Dict[str, Any]) -> int:
        """Get swimming speed."""
        race_data = character_data.get('race', {})
        
        if race_data:
            race_definition = race_data.get('definition', {})
            race_name = race_definition.get('name', '').lower()
            speed_info = race_definition.get('movementSpeeds', [])
            
            # Check explicit swimming speed
            for speed in speed_info:
                if speed.get('movementId') == 3:  # Swimming speed ID
                    return speed.get('speed', 0)
            
            # Check racial swimming speeds
            if 'triton' in race_name or 'lizardfolk' in race_name:
                return 30
        
        return 0
    
    def _get_flying_speed(self, character_data: Dict[str, Any]) -> int:
        """Get flying speed."""
        race_data = character_data.get('race', {})
        
        if race_data:
            race_definition = race_data.get('definition', {})
            race_name = race_definition.get('name', '').lower()
            speed_info = race_definition.get('movementSpeeds', [])
            
            # Check explicit flying speed
            for speed in speed_info:
                if speed.get('movementId') == 4:  # Flying speed ID
                    return speed.get('speed', 0)
            
            # Check racial flying speeds
            if 'aarakocra' in race_name:
                return 50
            elif 'aasimar' in race_name:
                # Some aasimar subraces get temporary flight
                return 0  # Not permanent
        
        return 0
    
    def _get_burrowing_speed(self, character_data: Dict[str, Any]) -> int:
        """Get burrowing speed."""
        race_data = character_data.get('race', {})
        
        if race_data:
            race_definition = race_data.get('definition', {})
            speed_info = race_definition.get('movementSpeeds', [])
            
            for speed in speed_info:
                if speed.get('movementId') == 5:  # Burrowing speed ID
                    return speed.get('speed', 0)
        
        return 0
    
    def _has_hover(self, character_data: Dict[str, Any]) -> bool:
        """Check if character has hover ability."""
        # Most D&D 5e races don't have hover by default
        # This would typically come from spells or magic items
        return False
    
    def _get_special_movement(self, character_data: Dict[str, Any]) -> List[str]:
        """Get list of special movement abilities."""
        special_movement = []
        
        race_data = character_data.get('race', {})
        if race_data:
            race_name = race_data.get('definition', {}).get('name', '').lower()
            
            # Add racial movement abilities
            if 'spider' in race_name:
                special_movement.append('Spider Climb')
            if 'lizardfolk' in race_name:
                special_movement.append('Hold Breath (15 minutes)')
        
        # Check class features
        classes = character_data.get('classes', [])
        for class_data in classes:
            class_name = class_data.get('definition', {}).get('name', '').lower()
            class_level = class_data.get('level', 1)
            
            if 'monk' in class_name:
                if class_level >= 4:
                    special_movement.append('Slow Fall')
                if class_level >= 9:
                    special_movement.append('Unarmored Movement (vertical surfaces)')
                if class_level >= 13:
                    special_movement.append('Water Walking')
        
        return special_movement
    
    def _is_speed_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if modifier affects speed."""
        modifies_type_id = modifier.get('modifiesTypeId')
        sub_type = modifier.get('subType', '').lower()
        
        # Speed modifier type ID
        if modifies_type_id == 8:  # Assuming 8 is speed in D&D Beyond
            return True
            
        # Check subtype for speed modifiers
        if 'speed' in sub_type or 'movement' in sub_type:
            return True
            
        return False