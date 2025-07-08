"""
D&D Beyond Character Scraper - Validation Framework

Comprehensive validation system for character data integrity,
calculation accuracy, and regression testing.

Key Components:
- BaseValidator: Abstract base class for all validators
- CharacterValidator: Validates complete character data structure
- CalculationValidator: Validates calculation consistency
- RegressionValidator: Compares against baseline data
"""

from .base import BaseValidator, ValidationResult, ValidationError
from .character import CharacterValidator
from .calculations import CalculationValidator
from .regression import RegressionValidator

__all__ = [
    'BaseValidator',
    'ValidationResult',
    'ValidationError',
    'CharacterValidator',
    'CalculationValidator',
    'RegressionValidator'
]