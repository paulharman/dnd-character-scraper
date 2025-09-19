"""
Mathematical utility functions for D&D calculations.

This module provides common mathematical operations and D&D-specific
calculations used throughout the calculator system.
"""

import math
from typing import Dict, Any, List, Optional, Union, Tuple
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from enum import Enum


class RoundingMode(Enum):
    """Different rounding modes for calculations."""
    ROUND_DOWN = "round_down"
    ROUND_UP = "round_up"
    ROUND_HALF_UP = "round_half_up"
    ROUND_HALF_DOWN = "round_half_down"
    ROUND_HALF_EVEN = "round_half_even"


@dataclass
class DiceRoll:
    """Represents a dice roll with count, sides, and modifier."""
    count: int
    sides: int
    modifier: int = 0
    
    def __post_init__(self):
        if self.count < 0:
            raise ValueError("Dice count cannot be negative")
        if self.sides < 1:
            raise ValueError("Dice sides must be at least 1")
    
    def average(self) -> float:
        """Calculate the average value of this dice roll."""
        return self.count * (self.sides + 1) / 2 + self.modifier
    
    def minimum(self) -> int:
        """Calculate the minimum possible value."""
        return self.count + self.modifier
    
    def maximum(self) -> int:
        """Calculate the maximum possible value."""
        return self.count * self.sides + self.modifier
    
    def __str__(self) -> str:
        """String representation of the dice roll."""
        base = f"{self.count}d{self.sides}"
        if self.modifier > 0:
            return f"{base}+{self.modifier}"
        elif self.modifier < 0:
            return f"{base}{self.modifier}"
        return base


class MathUtils:
    """Utility class for mathematical operations."""
    
    @staticmethod
    def round_value(value: float, mode: RoundingMode = RoundingMode.ROUND_HALF_UP) -> int:
        """
        Round a value using the specified rounding mode.
        
        Args:
            value: Value to round
            mode: Rounding mode to use
            
        Returns:
            Rounded integer value
        """
        if mode == RoundingMode.ROUND_DOWN:
            return int(math.floor(value))
        elif mode == RoundingMode.ROUND_UP:
            return int(math.ceil(value))
        elif mode == RoundingMode.ROUND_HALF_UP:
            return int(Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
        elif mode == RoundingMode.ROUND_HALF_DOWN:
            return int(value + 0.5) if value >= 0 else int(value - 0.5)
        elif mode == RoundingMode.ROUND_HALF_EVEN:
            return round(value)
        else:
            raise ValueError(f"Unknown rounding mode: {mode}")
    
    @staticmethod
    def clamp(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
        """
        Clamp a value between minimum and maximum bounds.
        
        Args:
            value: Value to clamp
            min_val: Minimum value
            max_val: Maximum value
            
        Returns:
            Clamped value
        """
        return max(min_val, min(value, max_val))
    
    @staticmethod
    def percentage_of(value: Union[int, float], total: Union[int, float]) -> float:
        """
        Calculate what percentage value is of total.
        
        Args:
            value: Value to calculate percentage for
            total: Total value
            
        Returns:
            Percentage (0.0 to 1.0)
        """
        if total == 0:
            return 0.0
        return value / total
    
    @staticmethod
    def apply_percentage(value: Union[int, float], percentage: float) -> Union[int, float]:
        """
        Apply a percentage to a value.
        
        Args:
            value: Base value
            percentage: Percentage to apply (0.0 to 1.0)
            
        Returns:
            Value with percentage applied
        """
        return value * percentage
    
    @staticmethod
    def weighted_average(values: List[Union[int, float]], weights: List[Union[int, float]]) -> float:
        """
        Calculate weighted average of values.
        
        Args:
            values: List of values
            weights: List of weights (same length as values)
            
        Returns:
            Weighted average
        """
        if len(values) != len(weights):
            raise ValueError("Values and weights must have same length")
        
        if not values:
            return 0.0
        
        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0
        
        weighted_sum = sum(v * w for v, w in zip(values, weights))
        return weighted_sum / total_weight
    
    @staticmethod
    def sum_with_overflow_check(values: List[Union[int, float]], max_value: Optional[Union[int, float]] = None) -> Union[int, float]:
        """
        Sum values with optional overflow checking.
        
        Args:
            values: List of values to sum
            max_value: Maximum allowed sum (optional)
            
        Returns:
            Sum of values
            
        Raises:
            OverflowError: If sum exceeds max_value
        """
        total = sum(values)
        if max_value is not None and total > max_value:
            raise OverflowError(f"Sum {total} exceeds maximum {max_value}")
        return total


class DnDMath:
    """D&D-specific mathematical operations."""
    
    @staticmethod
    def ability_modifier(ability_score: int) -> int:
        """
        Calculate ability modifier from ability score.
        
        Args:
            ability_score: Ability score (1-30)
            
        Returns:
            Ability modifier (-5 to +10)
        """
        return MathUtils.round_value((ability_score - 10) / 2, RoundingMode.ROUND_DOWN)
    
    @staticmethod
    def proficiency_bonus(character_level: int) -> int:
        """
        Calculate proficiency bonus from character level.
        
        Args:
            character_level: Character level (1-20)
            
        Returns:
            Proficiency bonus (+2 to +6)
        """
        return MathUtils.clamp(2 + (character_level - 1) // 4, 2, 6)
    
    @staticmethod
    def spell_slots_per_level(caster_level: int, spell_level: int) -> int:
        """
        Calculate spell slots for a given caster level and spell level.
        
        Args:
            caster_level: Caster level (1-20)
            spell_level: Spell level (1-9)
            
        Returns:
            Number of spell slots
        """
        # Standard spell slot progression table
        spell_slots = {
            1: [2, 0, 0, 0, 0, 0, 0, 0, 0],  # Level 1
            2: [3, 0, 0, 0, 0, 0, 0, 0, 0],  # Level 2
            3: [4, 2, 0, 0, 0, 0, 0, 0, 0],  # Level 3
            4: [4, 3, 0, 0, 0, 0, 0, 0, 0],  # Level 4
            5: [4, 3, 2, 0, 0, 0, 0, 0, 0],  # Level 5
            6: [4, 3, 3, 0, 0, 0, 0, 0, 0],  # Level 6
            7: [4, 3, 3, 1, 0, 0, 0, 0, 0],  # Level 7
            8: [4, 3, 3, 2, 0, 0, 0, 0, 0],  # Level 8
            9: [4, 3, 3, 3, 1, 0, 0, 0, 0],  # Level 9
            10: [4, 3, 3, 3, 2, 0, 0, 0, 0],  # Level 10
            11: [4, 3, 3, 3, 2, 1, 0, 0, 0],  # Level 11
            12: [4, 3, 3, 3, 2, 1, 0, 0, 0],  # Level 12
            13: [4, 3, 3, 3, 2, 1, 1, 0, 0],  # Level 13
            14: [4, 3, 3, 3, 2, 1, 1, 0, 0],  # Level 14
            15: [4, 3, 3, 3, 2, 1, 1, 1, 0],  # Level 15
            16: [4, 3, 3, 3, 2, 1, 1, 1, 0],  # Level 16
            17: [4, 3, 3, 3, 2, 1, 1, 1, 1],  # Level 17
            18: [4, 3, 3, 3, 3, 1, 1, 1, 1],  # Level 18
            19: [4, 3, 3, 3, 3, 2, 1, 1, 1],  # Level 19
            20: [4, 3, 3, 3, 3, 2, 2, 1, 1],  # Level 20
        }
        
        caster_level = MathUtils.clamp(caster_level, 1, 20)
        spell_level = MathUtils.clamp(spell_level, 1, 9)
        
        return spell_slots.get(caster_level, [0] * 9)[spell_level - 1]
    
    @staticmethod
    def spell_save_dc(spell_attack_bonus: int) -> int:
        """
        Calculate spell save DC from spell attack bonus.
        
        Args:
            spell_attack_bonus: Spell attack bonus
            
        Returns:
            Spell save DC
        """
        return 8 + spell_attack_bonus
    
    @staticmethod
    def spell_attack_bonus(ability_modifier: int, proficiency_bonus: int) -> int:
        """
        Calculate spell attack bonus.
        
        Args:
            ability_modifier: Spellcasting ability modifier
            proficiency_bonus: Proficiency bonus
            
        Returns:
            Spell attack bonus
        """
        return ability_modifier + proficiency_bonus
    
    @staticmethod
    def carrying_capacity(strength_score: int, size_category: str = "Medium") -> int:
        """
        Calculate carrying capacity based on Strength score and size.
        
        Args:
            strength_score: Strength ability score
            size_category: Size category (Tiny, Small, Medium, Large, etc.)
            
        Returns:
            Carrying capacity in pounds
        """
        base_capacity = strength_score * 15
        
        size_multipliers = {
            "Tiny": 0.5,
            "Small": 1.0,
            "Medium": 1.0,
            "Large": 2.0,
            "Huge": 4.0,
            "Gargantuan": 8.0
        }
        
        multiplier = size_multipliers.get(size_category, 1.0)
        return int(base_capacity * multiplier)
    
    @staticmethod
    def encumbrance_thresholds(carrying_capacity: int) -> Tuple[int, int]:
        """
        Calculate encumbrance thresholds.
        
        Args:
            carrying_capacity: Maximum carrying capacity
            
        Returns:
            Tuple of (heavily_encumbered_threshold, max_capacity)
        """
        heavily_encumbered = carrying_capacity * 2 // 3
        return (heavily_encumbered, carrying_capacity)
    
    @staticmethod
    def hit_dice_average(hit_die_size: int) -> float:
        """
        Calculate average hit die value.
        
        Args:
            hit_die_size: Size of hit die (d4=4, d6=6, d8=8, d10=10, d12=12)
            
        Returns:
            Average hit die value
        """
        return (hit_die_size + 1) / 2
    
    @staticmethod
    def multiclass_spell_slots(class_levels: Dict[str, int]) -> Dict[int, int]:
        """
        Calculate spell slots for multiclass characters.
        
        Args:
            class_levels: Dictionary of class names to levels
            
        Returns:
            Dictionary of spell level to slot count
        """
        # Multiclass spellcasting progression
        full_caster_classes = ["bard", "cleric", "druid", "sorcerer", "wizard"]
        half_caster_classes = ["paladin", "ranger"]
        third_caster_classes = ["arcane_trickster", "eldritch_knight"]
        
        total_caster_level = 0
        
        for class_name, level in class_levels.items():
            class_lower = class_name.lower()
            if class_lower in full_caster_classes:
                total_caster_level += level
            elif class_lower in half_caster_classes:
                total_caster_level += level // 2
            elif class_lower in third_caster_classes:
                total_caster_level += level // 3
        
        # Calculate spell slots based on total caster level
        spell_slots = {}
        for spell_level in range(1, 10):
            spell_slots[spell_level] = DnDMath.spell_slots_per_level(total_caster_level, spell_level)
        
        return spell_slots
    
    @staticmethod
    def parse_dice_string(dice_string: str) -> Optional[DiceRoll]:
        """
        Parse a dice string (e.g., "1d8+2") into a DiceRoll object.
        
        Args:
            dice_string: String representation of dice roll
            
        Returns:
            DiceRoll object or None if parsing fails
        """
        import re
        
        # Pattern to match dice strings like "1d8+2", "2d6", "1d4-1"
        pattern = r'(\d+)d(\d+)([+-]\d+)?'
        match = re.match(pattern, dice_string.strip())
        
        if not match:
            return None
        
        count = int(match.group(1))
        sides = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0
        
        try:
            return DiceRoll(count, sides, modifier)
        except ValueError:
            return None
    
    @staticmethod
    def format_modifier(modifier: int) -> str:
        """
        Format a modifier for display (e.g., +3, -1, +0).
        
        Args:
            modifier: Modifier value
            
        Returns:
            Formatted modifier string
        """
        if modifier >= 0:
            return f"+{modifier}"
        else:
            return str(modifier)
    
    @staticmethod
    def calculate_attack_bonus(ability_modifier: int, proficiency_bonus: int, 
                              is_proficient: bool = True, magic_bonus: int = 0) -> int:
        """
        Calculate attack bonus for weapons.
        
        Args:
            ability_modifier: Relevant ability modifier (STR or DEX)
            proficiency_bonus: Character's proficiency bonus
            is_proficient: Whether character is proficient with weapon
            magic_bonus: Bonus from magic weapon
            
        Returns:
            Total attack bonus
        """
        bonus = ability_modifier + magic_bonus
        if is_proficient:
            bonus += proficiency_bonus
        return bonus
    
    @staticmethod
    def calculate_damage_bonus(ability_modifier: int, magic_bonus: int = 0) -> int:
        """
        Calculate damage bonus for weapons.
        
        Args:
            ability_modifier: Relevant ability modifier (STR or DEX)
            magic_bonus: Bonus from magic weapon
            
        Returns:
            Total damage bonus
        """
        return ability_modifier + magic_bonus


class StatisticsUtils:
    """Utilities for statistical calculations."""
    
    @staticmethod
    def mean(values: List[Union[int, float]]) -> float:
        """Calculate the mean of a list of values."""
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    @staticmethod
    def median(values: List[Union[int, float]]) -> float:
        """Calculate the median of a list of values."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n % 2 == 0:
            return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
        else:
            return sorted_values[n // 2]
    
    @staticmethod
    def mode(values: List[Union[int, float]]) -> List[Union[int, float]]:
        """Calculate the mode(s) of a list of values."""
        if not values:
            return []
        
        from collections import Counter
        counts = Counter(values)
        max_count = max(counts.values())
        
        return [value for value, count in counts.items() if count == max_count]
    
    @staticmethod
    def standard_deviation(values: List[Union[int, float]]) -> float:
        """Calculate the standard deviation of a list of values."""
        if len(values) < 2:
            return 0.0
        
        mean_val = StatisticsUtils.mean(values)
        variance = sum((x - mean_val) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)
    
    @staticmethod
    def percentile(values: List[Union[int, float]], percentile: float) -> float:
        """
        Calculate the specified percentile of a list of values.
        
        Args:
            values: List of values
            percentile: Percentile to calculate (0.0 to 1.0)
            
        Returns:
            Value at the specified percentile
        """
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = percentile * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            weight = index - lower_index
            
            return sorted_values[lower_index] * (1 - weight) + sorted_values[upper_index] * weight