"""
Enhanced Encumbrance Calculator with new interface compliance.

This module provides an enhanced implementation of the encumbrance calculator
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
class EncumbranceData:
    """Data class for encumbrance information."""
    current_weight: float
    carrying_capacity: int
    push_drag_lift: int
    encumbrance_level: str
    speed_penalty: int
    disadvantage_on_checks: bool
    weight_breakdown: Dict[str, float]
    capacity_modifiers: Dict[str, int]
    
    def __post_init__(self):
        if self.current_weight < 0:
            raise ValueError(f"Current weight cannot be negative, got {self.current_weight}")
        if self.carrying_capacity < 0:
            raise ValueError(f"Carrying capacity cannot be negative, got {self.carrying_capacity}")
        if self.encumbrance_level not in ['unencumbered', 'encumbered', 'heavily_encumbered', 'overloaded']:
            raise ValueError(f"Invalid encumbrance level: {self.encumbrance_level}")


class EnhancedEncumbranceCalculator(RuleAwareCalculator, ICachedCalculator):
    """
    Enhanced encumbrance calculator with new interface compliance.
    
    Features:
    - Full interface compliance with ICalculator, IRuleAwareCalculator, ICachedCalculator
    - Comprehensive encumbrance calculation with variant rules
    - Enhanced validation and error handling
    - Performance monitoring and caching
    - Rule version support for encumbrance differences
    """
    
    def __init__(self, config_manager=None, rule_manager: Optional[RuleVersionManager] = None):
        """
        Initialize the enhanced encumbrance calculator.
        
        Args:
            config_manager: Configuration manager instance
            rule_manager: Rule version manager instance
        """
        super().__init__(config_manager, rule_manager)
        self.config = CalculatorConfig()
        self.validator = CharacterDataValidator()
        self.cache = {}
        self.cache_stats = {'hits': 0, 'misses': 0}
        
        # Initialize encumbrance constants
        self._setup_encumbrance_constants()
        
        # Performance tracking
        self.metrics = {
            'total_calculations': 0,
            'total_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'validation_failures': 0
        }
    
    def _setup_encumbrance_constants(self):
        """Setup encumbrance calculation constants."""
        # Size multipliers for carrying capacity
        self.size_multipliers = {
            'tiny': 0.5,
            'small': 1,
            'medium': 1,
            'large': 2,
            'huge': 4,
            'gargantuan': 8
        }
        
        # Encumbrance thresholds (as fractions of carrying capacity)
        self.encumbrance_thresholds = {
            'unencumbered': 0.33,  # 0-1/3 capacity
            'encumbered': 0.66,    # 1/3-2/3 capacity
            'heavily_encumbered': 1.0,  # 2/3-full capacity
            'overloaded': float('inf')  # Over capacity
        }
        
        # Speed penalties by encumbrance level
        self.speed_penalties = {
            'unencumbered': 0,
            'encumbered': 10,
            'heavily_encumbered': 20,
            'overloaded': 30
        }
        
        # Ability check disadvantage
        self.disadvantage_levels = ['heavily_encumbered', 'overloaded']
        
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
        return CalculatorType.ENCUMBRANCE
    
    @property
    def name(self) -> str:
        """Get the human-readable name of this calculator."""
        return "Enhanced Encumbrance Calculator"
    
    @property
    def version(self) -> str:
        """Get the version of this calculator."""
        return "2.0.0"
    
    @property
    def dependencies(self) -> List[CalculatorType]:
        """Get the list of calculator types this calculator depends on."""
        return [CalculatorType.ABILITY_SCORE]  # Needs STR for carrying capacity
    
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
            logger.debug(f"Calculating encumbrance with {rule_version.version.value} rules")
            
            # Calculate encumbrance
            encumbrance_data = self._calculate_encumbrance(character_data, rule_version)
            
            # Build result
            result_data = {
                'current_weight': encumbrance_data.current_weight,
                'carrying_capacity': encumbrance_data.carrying_capacity,
                'push_drag_lift': encumbrance_data.push_drag_lift,
                'encumbrance_level': encumbrance_data.encumbrance_level,
                'speed_penalty': encumbrance_data.speed_penalty,
                'disadvantage_on_checks': encumbrance_data.disadvantage_on_checks,
                'weight_breakdown': encumbrance_data.weight_breakdown,
                'capacity_modifiers': encumbrance_data.capacity_modifiers,
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
            logger.error(f"Error in encumbrance calculation: {str(e)}")
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
        
        # Check for stats (needed for STR score)
        if 'stats' not in character_data:
            errors.append("Missing required 'stats' field for STR score calculation")
        else:
            stats = character_data['stats']
            if not isinstance(stats, list):
                errors.append("'stats' field must be a list")
            else:
                # Check for STR specifically
                str_found = any(stat.get('id') == 1 for stat in stats if isinstance(stat, dict))
                if not str_found:
                    errors.append("Strength score not found in stats")
        
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
                "current_weight": {"type": "number", "minimum": 0},
                "carrying_capacity": {"type": "integer", "minimum": 0},
                "push_drag_lift": {"type": "integer", "minimum": 0},
                "encumbrance_level": {
                    "type": "string", 
                    "enum": ["unencumbered", "encumbered", "heavily_encumbered", "overloaded"]
                },
                "speed_penalty": {"type": "integer", "minimum": 0},
                "disadvantage_on_checks": {"type": "boolean"},
                "weight_breakdown": {
                    "type": "object",
                    "properties": {
                        "equipment": {"type": "number"},
                        "currency": {"type": "number"},
                        "containers": {"type": "number"},
                        "other": {"type": "number"}
                    }
                },
                "capacity_modifiers": {
                    "type": "object",
                    "properties": {
                        "base_capacity": {"type": "integer"},
                        "size_modifier": {"type": "integer"},
                        "feat_modifier": {"type": "integer"},
                        "item_modifier": {"type": "integer"},
                        "misc_modifier": {"type": "integer"}
                    }
                },
                "rule_version": {"type": "string", "enum": ["2014", "2024"]}
            },
            "required": ["current_weight", "carrying_capacity", "push_drag_lift", "encumbrance_level", "speed_penalty", "disadvantage_on_checks", "weight_breakdown", "capacity_modifiers", "rule_version"]
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
        return ['inventory', 'currencies', 'race', 'feats', 'modifiers']
    
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
            'currencies': character_data.get('currencies', {}),
            'race': character_data.get('race', {}),
            'modifiers': character_data.get('modifiers', {}),
            'rule_version': context.rule_version,
            'character_id': context.character_id
        }
        
        # Sort keys for consistent hashing
        cache_json = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_json.encode()).hexdigest()
        
        return f"encumbrance_{cache_hash}"
    
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
    def _calculate_encumbrance(self, character_data: Dict[str, Any], rule_version) -> EncumbranceData:
        """
        Calculate encumbrance with comprehensive breakdown.
        
        Args:
            character_data: Character data from D&D Beyond
            rule_version: Detected rule version
            
        Returns:
            EncumbranceData object with complete breakdown
        """
        # Calculate carrying capacity
        carrying_capacity, capacity_modifiers = self._calculate_carrying_capacity(character_data)
        
        # Calculate current weight
        current_weight, weight_breakdown = self._calculate_current_weight(character_data)
        
        # Calculate push/drag/lift capacity
        push_drag_lift = carrying_capacity * 2
        
        # Determine encumbrance level
        encumbrance_level = self._determine_encumbrance_level(current_weight, carrying_capacity)
        
        # Calculate speed penalty
        speed_penalty = self.speed_penalties.get(encumbrance_level, 0)
        
        # Check for disadvantage on ability checks
        disadvantage_on_checks = encumbrance_level in self.disadvantage_levels
        
        return EncumbranceData(
            current_weight=current_weight,
            carrying_capacity=carrying_capacity,
            push_drag_lift=push_drag_lift,
            encumbrance_level=encumbrance_level,
            speed_penalty=speed_penalty,
            disadvantage_on_checks=disadvantage_on_checks,
            weight_breakdown=weight_breakdown,
            capacity_modifiers=capacity_modifiers
        )
    
    def _calculate_carrying_capacity(self, character_data: Dict[str, Any]) -> Tuple[int, Dict[str, int]]:
        """Calculate carrying capacity with modifiers."""
        # Get strength score
        str_score = self._get_strength_score(character_data)
        
        # Base carrying capacity (STR x 15)
        base_capacity = str_score * 15
        
        # Get size modifier
        size_modifier = self._get_size_modifier(character_data)
        
        # Get other modifiers
        feat_modifier = self._get_feat_capacity_modifier(character_data)
        item_modifier = self._get_item_capacity_modifier(character_data)
        misc_modifier = self._get_misc_capacity_modifier(character_data)
        
        # Calculate final capacity
        capacity_with_size = int(base_capacity * size_modifier)
        final_capacity = capacity_with_size + feat_modifier + item_modifier + misc_modifier
        
        capacity_modifiers = {
            'base_capacity': base_capacity,
            'size_modifier': capacity_with_size - base_capacity,
            'feat_modifier': feat_modifier,
            'item_modifier': item_modifier,
            'misc_modifier': misc_modifier
        }
        
        return final_capacity, capacity_modifiers
    
    def _calculate_current_weight(self, character_data: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """Calculate current weight carried."""
        equipment_weight = self._calculate_equipment_weight(character_data)
        currency_weight = self._calculate_currency_weight(character_data)
        container_weight = self._calculate_container_weight(character_data)
        other_weight = self._calculate_other_weight(character_data)
        
        total_weight = equipment_weight + currency_weight + container_weight + other_weight
        
        weight_breakdown = {
            'equipment': equipment_weight,
            'currency': currency_weight,
            'containers': container_weight,
            'other': other_weight
        }
        
        return total_weight, weight_breakdown
    
    def _get_strength_score(self, character_data: Dict[str, Any]) -> int:
        """Get character's strength score."""
        stats = character_data.get('stats', [])
        
        for stat in stats:
            if stat.get('id') == 1:  # Strength ID
                return stat.get('value', 10)
        
        return 10  # Default
    
    def _get_size_modifier(self, character_data: Dict[str, Any]) -> float:
        """Get size modifier for carrying capacity."""
        race_data = character_data.get('race', {})
        
        if race_data:
            race_definition = race_data.get('definition', {})
            size = race_definition.get('size', 'medium').lower()
            return self.size_multipliers.get(size, 1.0)
        
        return 1.0  # Default to medium
    
    def _get_feat_capacity_modifier(self, character_data: Dict[str, Any]) -> int:
        """Get carrying capacity modifier from feats."""
        modifiers = character_data.get('modifiers', {})
        feat_modifiers = modifiers.get('feat', [])
        modifier = 0
        
        for mod in feat_modifiers:
            if self._is_carrying_capacity_modifier(mod):
                modifier += mod.get('value', 0)
        
        return modifier
    
    def _get_item_capacity_modifier(self, character_data: Dict[str, Any]) -> int:
        """Get carrying capacity modifier from magic items."""
        modifiers = character_data.get('modifiers', {})
        item_modifiers = modifiers.get('item', [])
        modifier = 0
        
        for mod in item_modifiers:
            if self._is_carrying_capacity_modifier(mod):
                modifier += mod.get('value', 0)
        
        return modifier
    
    def _get_misc_capacity_modifier(self, character_data: Dict[str, Any]) -> int:
        """Get miscellaneous carrying capacity modifiers."""
        modifiers = character_data.get('modifiers', {})
        modifier = 0
        
        for source_type, modifier_list in modifiers.items():
            if source_type in ['feat', 'item', 'race', 'class']:
                continue  # Already handled
                
            if not isinstance(modifier_list, list):
                continue
                
            for mod in modifier_list:
                if self._is_carrying_capacity_modifier(mod):
                    modifier += mod.get('value', 0)
        
        return modifier
    
    def _calculate_equipment_weight(self, character_data: Dict[str, Any]) -> float:
        """Calculate weight of carried equipment."""
        inventory = character_data.get('inventory', [])
        total_weight = 0.0
        
        for item in inventory:
            if not isinstance(item, dict):
                continue
            
            if item.get('equipped', False) or item.get('isAttuned', False):
                definition = item.get('definition', {})
                weight = definition.get('weight', 0)
                quantity = item.get('quantity', 1)
                total_weight += weight * quantity
        
        return total_weight
    
    def _calculate_currency_weight(self, character_data: Dict[str, Any]) -> float:
        """Calculate weight of carried currency."""
        currencies = character_data.get('currencies', {})
        
        # Standard D&D: 50 coins = 1 pound
        total_coins = 0
        if isinstance(currencies, dict):
            total_coins += currencies.get('cp', 0)
            total_coins += currencies.get('sp', 0)
            total_coins += currencies.get('ep', 0)
            total_coins += currencies.get('gp', 0)
            total_coins += currencies.get('pp', 0)
        
        return total_coins / 50.0
    
    def _calculate_container_weight(self, character_data: Dict[str, Any]) -> float:
        """Calculate weight of containers and their contents."""
        # This would need more sophisticated container tracking
        # For now, return 0 as containers are typically handled in equipment
        return 0.0
    
    def _calculate_other_weight(self, character_data: Dict[str, Any]) -> float:
        """Calculate weight from other sources."""
        # This could include things like summoned items, temporary effects, etc.
        return 0.0
    
    def _determine_encumbrance_level(self, current_weight: float, carrying_capacity: int) -> str:
        """Determine encumbrance level based on weight vs capacity."""
        if current_weight <= 0:
            return 'unencumbered'
        
        weight_ratio = current_weight / carrying_capacity
        
        if weight_ratio <= self.encumbrance_thresholds['unencumbered']:
            return 'unencumbered'
        elif weight_ratio <= self.encumbrance_thresholds['encumbered']:
            return 'encumbered'
        elif weight_ratio <= self.encumbrance_thresholds['heavily_encumbered']:
            return 'heavily_encumbered'
        else:
            return 'overloaded'
    
    def _is_carrying_capacity_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if modifier affects carrying capacity."""
        modifies_type_id = modifier.get('modifiesTypeId')
        sub_type = modifier.get('subType', '').lower()
        
        # Check for carrying capacity modifier type
        if modifies_type_id == 15:  # Assuming 15 is carrying capacity in D&D Beyond
            return True
            
        # Check subtype for carrying capacity modifiers
        if 'carrying-capacity' in sub_type or 'encumbrance' in sub_type:
            return True
            
        return False