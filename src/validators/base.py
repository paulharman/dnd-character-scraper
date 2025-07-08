"""
Base Validator Classes

Provides abstract base classes and common functionality for all validators.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    field_comparisons: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    accuracy_score: Optional[float] = None
    
    def add_error(self, error: str):
        """Add an error and mark as invalid."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add a warning (doesn't affect validity)."""
        self.warnings.append(warning)
    
    def add_field_comparison(self, field: str, actual: Any, expected: Any, match: bool = None):
        """Add a field comparison result."""
        if match is None:
            match = actual == expected
        
        self.field_comparisons[field] = {
            'actual': actual,
            'expected': expected,
            'match': match
        }
        
        if not match:
            self.add_error(f"{field}: Expected {expected}, got {actual}")
    
    def merge(self, other: 'ValidationResult'):
        """Merge another validation result into this one."""
        self.is_valid = self.is_valid and other.is_valid
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.field_comparisons.update(other.field_comparisons)
        
        # Recalculate accuracy if both have scores
        if self.accuracy_score is not None and other.accuracy_score is not None:
            total_comparisons = len(self.field_comparisons) + len(other.field_comparisons)
            if total_comparisons > 0:
                total_matches = sum(1 for comp in self.field_comparisons.values() if comp.get('match', False))
                total_matches += sum(1 for comp in other.field_comparisons.values() if comp.get('match', False))
                self.accuracy_score = total_matches / total_comparisons
    
    def calculate_accuracy(self):
        """Calculate accuracy score from field comparisons."""
        if not self.field_comparisons:
            self.accuracy_score = 1.0
            return
        
        matches = sum(1 for comp in self.field_comparisons.values() if comp.get('match', False))
        self.accuracy_score = matches / len(self.field_comparisons)
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the validation result."""
        lines = []
        
        if self.is_valid:
            lines.append("✅ Validation PASSED")
        else:
            lines.append("❌ Validation FAILED")
        
        if self.accuracy_score is not None:
            lines.append(f"Accuracy: {self.accuracy_score:.1%}")
        
        if self.errors:
            lines.append(f"Errors: {len(self.errors)}")
            for error in self.errors[:5]:  # Show first 5 errors
                lines.append(f"  - {error}")
            if len(self.errors) > 5:
                lines.append(f"  ... and {len(self.errors) - 5} more errors")
        
        if self.warnings:
            lines.append(f"Warnings: {len(self.warnings)}")
            for warning in self.warnings[:3]:  # Show first 3 warnings
                lines.append(f"  ⚠️  {warning}")
            if len(self.warnings) > 3:
                lines.append(f"  ... and {len(self.warnings) - 3} more warnings")
        
        return "\n".join(lines)


class BaseValidator(ABC):
    """Abstract base class for all validators."""
    
    @abstractmethod
    def validate(self, data: Any, **kwargs) -> ValidationResult:
        """
        Perform validation on the given data.
        
        Args:
            data: Data to validate
            **kwargs: Additional validation parameters
            
        Returns:
            ValidationResult with details of the validation
        """
        pass
    
    def _validate_field(self, field_name: str, actual: Any, expected: Any, 
                       tolerance: Optional[float] = None) -> Optional[str]:
        """
        Validate a single field value.
        
        Args:
            field_name: Name of the field being validated
            actual: Actual value
            expected: Expected value
            tolerance: Optional tolerance for numeric comparisons
            
        Returns:
            Error message if validation fails, None if valid
        """
        if actual is None and expected is not None:
            return f"{field_name}: Missing value (expected {expected})"
        
        if expected is None:
            return None  # No expected value to validate against
        
        # Handle numeric comparisons with tolerance
        if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
            if tolerance is not None:
                if abs(actual - expected) > tolerance:
                    return f"{field_name}: {actual} differs from expected {expected} by more than {tolerance}"
            else:
                if actual != expected:
                    return f"{field_name}: {actual} != {expected}"
        
        # Handle string comparisons (case-insensitive)
        elif isinstance(actual, str) and isinstance(expected, str):
            if actual.lower() != expected.lower():
                return f"{field_name}: '{actual}' != '{expected}'"
        
        # Handle list comparisons
        elif isinstance(actual, list) and isinstance(expected, list):
            if len(actual) != len(expected):
                return f"{field_name}: Different lengths ({len(actual)} vs {len(expected)})"
            # For now, just check length - could be enhanced
        
        # Handle dict comparisons
        elif isinstance(actual, dict) and isinstance(expected, dict):
            missing_keys = set(expected.keys()) - set(actual.keys())
            if missing_keys:
                return f"{field_name}: Missing keys {missing_keys}"
        
        # Default comparison
        elif actual != expected:
            return f"{field_name}: {actual} != {expected}"
        
        return None
    
    def _validate_range(self, field_name: str, value: Union[int, float], 
                       min_val: Optional[Union[int, float]] = None,
                       max_val: Optional[Union[int, float]] = None) -> Optional[str]:
        """
        Validate that a numeric value is within an expected range.
        
        Args:
            field_name: Name of the field
            value: Value to check
            min_val: Minimum acceptable value
            max_val: Maximum acceptable value
            
        Returns:
            Error message if out of range, None if valid
        """
        if value is None:
            return f"{field_name}: Missing value"
        
        if min_val is not None and value < min_val:
            return f"{field_name}: {value} is below minimum {min_val}"
        
        if max_val is not None and value > max_val:
            return f"{field_name}: {value} is above maximum {max_val}"
        
        return None
    
    def _validate_required_fields(self, data: Dict[str, Any], 
                                 required_fields: List[str]) -> List[str]:
        """
        Validate that all required fields are present.
        
        Args:
            data: Dictionary to check
            required_fields: List of required field names
            
        Returns:
            List of error messages for missing fields
        """
        errors = []
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Missing required field: {field}")
        return errors