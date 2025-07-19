"""
Data validation utilities for the calculator system.

This module provides comprehensive validation for character data,
calculation results, and system constraints.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation messages."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationCategory(Enum):
    """Categories of validation checks."""
    STRUCTURE = "structure"
    TYPE = "type"
    RANGE = "range"
    CONSTRAINT = "constraint"
    CONSISTENCY = "consistency"
    BUSINESS_RULE = "business_rule"
    PERFORMANCE = "performance"


@dataclass
class ValidationMessage:
    """A validation message with details."""
    severity: ValidationSeverity
    category: ValidationCategory
    message: str
    field_path: Optional[str] = None
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    messages: List[ValidationMessage] = field(default_factory=list)
    validated_data: Optional[Dict[str, Any]] = None
    validation_time: Optional[float] = None
    
    def add_message(self, severity: ValidationSeverity, category: ValidationCategory,
                   message: str, field_path: str = None, **kwargs):
        """Add a validation message."""
        msg = ValidationMessage(
            severity=severity,
            category=category,
            message=message,
            field_path=field_path,
            **kwargs
        )
        self.messages.append(msg)
        
        # Update validity based on severity
        if severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
            self.is_valid = False
    
    def has_errors(self) -> bool:
        """Check if there are any error or critical messages."""
        return any(msg.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL] 
                  for msg in self.messages)
    
    def has_warnings(self) -> bool:
        """Check if there are any warning messages."""
        return any(msg.severity == ValidationSeverity.WARNING for msg in self.messages)
    
    def get_errors(self) -> List[ValidationMessage]:
        """Get all error and critical messages."""
        return [msg for msg in self.messages 
                if msg.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]]
    
    def get_warnings(self) -> List[ValidationMessage]:
        """Get all warning messages."""
        return [msg for msg in self.messages 
                if msg.severity == ValidationSeverity.WARNING]
    
    def get_messages_by_category(self, category: ValidationCategory) -> List[ValidationMessage]:
        """Get messages by category."""
        return [msg for msg in self.messages if msg.category == category]


class ValidationRule:
    """Base class for validation rules."""
    
    def __init__(self, name: str, description: str, severity: ValidationSeverity,
                 category: ValidationCategory):
        self.name = name
        self.description = description
        self.severity = severity
        self.category = category
    
    def validate(self, data: Any, context: Dict[str, Any] = None) -> List[ValidationMessage]:
        """
        Validate data against this rule.
        
        Args:
            data: Data to validate
            context: Additional context for validation
            
        Returns:
            List of validation messages
        """
        raise NotImplementedError("Subclasses must implement validate method")


class RequiredFieldRule(ValidationRule):
    """Rule to validate required fields."""
    
    def __init__(self, field_path: str, field_name: str = None):
        super().__init__(
            name=f"required_field_{field_path}",
            description=f"Field '{field_path}' is required",
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.STRUCTURE
        )
        self.field_path = field_path
        self.field_name = field_name or field_path
    
    def validate(self, data: Any, context: Dict[str, Any] = None) -> List[ValidationMessage]:
        """Validate that required field exists."""
        messages = []
        
        if not self._field_exists(data, self.field_path):
            messages.append(ValidationMessage(
                severity=self.severity,
                category=self.category,
                message=f"Required field '{self.field_name}' is missing",
                field_path=self.field_path,
                suggestion=f"Ensure '{self.field_name}' is included in the data"
            ))
        
        return messages
    
    def _field_exists(self, data: Any, field_path: str) -> bool:
        """Check if field exists in data."""
        if not isinstance(data, dict):
            return False
        
        keys = field_path.split('.')
        current = data
        
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return False
            current = current[key]
        
        return current is not None


class TypeValidationRule(ValidationRule):
    """Rule to validate field types."""
    
    def __init__(self, field_path: str, expected_type: type, field_name: str = None):
        super().__init__(
            name=f"type_validation_{field_path}",
            description=f"Field '{field_path}' must be of type {expected_type.__name__}",
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.TYPE
        )
        self.field_path = field_path
        self.expected_type = expected_type
        self.field_name = field_name or field_path
    
    def validate(self, data: Any, context: Dict[str, Any] = None) -> List[ValidationMessage]:
        """Validate field type."""
        messages = []
        
        value = self._get_field_value(data, self.field_path)
        if value is not None and not isinstance(value, self.expected_type):
            messages.append(ValidationMessage(
                severity=self.severity,
                category=self.category,
                message=f"Field '{self.field_name}' must be of type {self.expected_type.__name__}",
                field_path=self.field_path,
                expected=self.expected_type.__name__,
                actual=type(value).__name__,
                suggestion=f"Convert '{self.field_name}' to {self.expected_type.__name__}"
            ))
        
        return messages
    
    def _get_field_value(self, data: Any, field_path: str) -> Any:
        """Get field value from data."""
        if not isinstance(data, dict):
            return None
        
        keys = field_path.split('.')
        current = data
        
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        
        return current


class RangeValidationRule(ValidationRule):
    """Rule to validate numeric ranges."""
    
    def __init__(self, field_path: str, min_value: float = None, max_value: float = None,
                 field_name: str = None):
        super().__init__(
            name=f"range_validation_{field_path}",
            description=f"Field '{field_path}' must be within valid range",
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.RANGE
        )
        self.field_path = field_path
        self.min_value = min_value
        self.max_value = max_value
        self.field_name = field_name or field_path
    
    def validate(self, data: Any, context: Dict[str, Any] = None) -> List[ValidationMessage]:
        """Validate numeric range."""
        messages = []
        
        value = self._get_field_value(data, self.field_path)
        if value is None:
            return messages
        
        if not isinstance(value, (int, float)):
            messages.append(ValidationMessage(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.TYPE,
                message=f"Field '{self.field_name}' must be numeric for range validation",
                field_path=self.field_path,
                actual=type(value).__name__
            ))
            return messages
        
        if self.min_value is not None and value < self.min_value:
            messages.append(ValidationMessage(
                severity=self.severity,
                category=self.category,
                message=f"Field '{self.field_name}' value {value} is below minimum {self.min_value}",
                field_path=self.field_path,
                expected=f">= {self.min_value}",
                actual=value,
                suggestion=f"Ensure '{self.field_name}' is at least {self.min_value}"
            ))
        
        if self.max_value is not None and value > self.max_value:
            messages.append(ValidationMessage(
                severity=self.severity,
                category=self.category,
                message=f"Field '{self.field_name}' value {value} is above maximum {self.max_value}",
                field_path=self.field_path,
                expected=f"<= {self.max_value}",
                actual=value,
                suggestion=f"Ensure '{self.field_name}' is at most {self.max_value}"
            ))
        
        return messages
    
    def _get_field_value(self, data: Any, field_path: str) -> Any:
        """Get field value from data."""
        if not isinstance(data, dict):
            return None
        
        keys = field_path.split('.')
        current = data
        
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        
        return current


class PatternValidationRule(ValidationRule):
    """Rule to validate string patterns."""
    
    def __init__(self, field_path: str, pattern: str, field_name: str = None):
        super().__init__(
            name=f"pattern_validation_{field_path}",
            description=f"Field '{field_path}' must match pattern",
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.CONSTRAINT
        )
        self.field_path = field_path
        self.pattern = pattern
        self.regex = re.compile(pattern)
        self.field_name = field_name or field_path
    
    def validate(self, data: Any, context: Dict[str, Any] = None) -> List[ValidationMessage]:
        """Validate string pattern."""
        messages = []
        
        value = self._get_field_value(data, self.field_path)
        if value is None:
            return messages
        
        if not isinstance(value, str):
            messages.append(ValidationMessage(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.TYPE,
                message=f"Field '{self.field_name}' must be string for pattern validation",
                field_path=self.field_path,
                actual=type(value).__name__
            ))
            return messages
        
        if not self.regex.match(value):
            messages.append(ValidationMessage(
                severity=self.severity,
                category=self.category,
                message=f"Field '{self.field_name}' value '{value}' does not match required pattern",
                field_path=self.field_path,
                expected=self.pattern,
                actual=value,
                suggestion=f"Ensure '{self.field_name}' matches pattern: {self.pattern}"
            ))
        
        return messages
    
    def _get_field_value(self, data: Any, field_path: str) -> Any:
        """Get field value from data."""
        if not isinstance(data, dict):
            return None
        
        keys = field_path.split('.')
        current = data
        
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        
        return current


class CharacterDataValidator:
    """Comprehensive validator for character data."""
    
    def __init__(self):
        """Initialize the validator with default rules."""
        self.rules = []
        self.custom_validators = {}
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Set up default validation rules for character data."""
        # Basic info validation
        self.rules.extend([
            RequiredFieldRule("basic_info", "Basic Information"),
            RequiredFieldRule("basic_info.name", "Character Name"),
            RequiredFieldRule("basic_info.level", "Character Level"),
            TypeValidationRule("basic_info.name", str, "Character Name"),
            TypeValidationRule("basic_info.level", int, "Character Level"),
            RangeValidationRule("basic_info.level", 1, 20, "Character Level"),
        ])
        
        # Ability scores validation
        for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            self.rules.extend([
                RequiredFieldRule(f"ability_scores.{ability}", f"{ability.title()} Score"),
                TypeValidationRule(f"ability_scores.{ability}", int, f"{ability.title()} Score"),
                RangeValidationRule(f"ability_scores.{ability}", 1, 30, f"{ability.title()} Score"),
            ])
        
        # Hit points validation
        self.rules.extend([
            RequiredFieldRule("hit_points.current", "Current Hit Points"),
            RequiredFieldRule("hit_points.maximum", "Maximum Hit Points"),
            TypeValidationRule("hit_points.current", int, "Current Hit Points"),
            TypeValidationRule("hit_points.maximum", int, "Maximum Hit Points"),
            RangeValidationRule("hit_points.current", 0, None, "Current Hit Points"),
            RangeValidationRule("hit_points.maximum", 1, None, "Maximum Hit Points"),
        ])
        
        # Armor class validation
        self.rules.extend([
            RequiredFieldRule("armor_class", "Armor Class"),
            TypeValidationRule("armor_class", int, "Armor Class"),
            RangeValidationRule("armor_class", 1, 30, "Armor Class"),
        ])
        
        # Speed validation
        self.rules.extend([
            RequiredFieldRule("speed", "Speed"),
            TypeValidationRule("speed", int, "Speed"),
            RangeValidationRule("speed", 0, 120, "Speed"),
        ])
    
    def add_rule(self, rule: ValidationRule):
        """Add a custom validation rule."""
        self.rules.append(rule)
    
    def add_custom_validator(self, name: str, validator_func: Callable):
        """Add a custom validator function."""
        self.custom_validators[name] = validator_func
    
    def validate(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> ValidationResult:
        """
        Validate character data against all rules.
        
        Args:
            data: Character data to validate
            context: Additional context for validation
            
        Returns:
            ValidationResult with messages and validity status
        """
        start_time = datetime.now()
        result = ValidationResult(is_valid=True)
        context = context or {}
        
        # Apply all validation rules
        for rule in self.rules:
            try:
                messages = rule.validate(data, context)
                result.messages.extend(messages)
            except Exception as e:
                logger.error(f"Error in validation rule {rule.name}: {e}")
                result.add_message(
                    ValidationSeverity.ERROR,
                    ValidationCategory.STRUCTURE,
                    f"Validation rule '{rule.name}' failed: {str(e)}"
                )
        
        # Apply custom validators
        for name, validator_func in self.custom_validators.items():
            try:
                custom_messages = validator_func(data, context)
                if custom_messages:
                    result.messages.extend(custom_messages)
            except Exception as e:
                logger.error(f"Error in custom validator {name}: {e}")
                result.add_message(
                    ValidationSeverity.ERROR,
                    ValidationCategory.STRUCTURE,
                    f"Custom validator '{name}' failed: {str(e)}"
                )
        
        # Check for errors to set validity
        result.is_valid = not result.has_errors()
        
        # Calculate validation time
        end_time = datetime.now()
        result.validation_time = (end_time - start_time).total_seconds()
        
        return result
    
    def validate_calculation_result(self, result: Dict[str, Any], 
                                   context: Dict[str, Any] = None) -> ValidationResult:
        """
        Validate calculation results.
        
        Args:
            result: Calculation result to validate
            context: Additional context for validation
            
        Returns:
            ValidationResult with messages and validity status
        """
        validation_result = ValidationResult(is_valid=True)
        context = context or {}
        
        # Validate calculation result structure
        if not isinstance(result, dict):
            validation_result.add_message(
                ValidationSeverity.ERROR,
                ValidationCategory.TYPE,
                "Calculation result must be a dictionary"
            )
            return validation_result
        
        # Check for required calculation fields
        required_fields = ["character_id", "timestamp", "data"]
        for field in required_fields:
            if field not in result:
                validation_result.add_message(
                    ValidationSeverity.ERROR,
                    ValidationCategory.STRUCTURE,
                    f"Required field '{field}' missing in calculation result"
                )
        
        # Validate calculated data if present
        if "data" in result:
            data_validation = self.validate(result["data"], context)
            validation_result.messages.extend(data_validation.messages)
        
        # Validate timestamp format if present
        if "timestamp" in result:
            timestamp = result["timestamp"]
            if not isinstance(timestamp, (str, datetime)):
                validation_result.add_message(
                    ValidationSeverity.ERROR,
                    ValidationCategory.TYPE,
                    "Timestamp must be string or datetime object"
                )
        
        validation_result.is_valid = not validation_result.has_errors()
        return validation_result
    
    def validate_rule_version(self, data: Dict[str, Any], 
                             expected_version: str = None) -> ValidationResult:
        """
        Validate rule version compatibility.
        
        Args:
            data: Character data to validate
            expected_version: Expected rule version
            
        Returns:
            ValidationResult with messages and validity status
        """
        validation_result = ValidationResult(is_valid=True)
        
        # Check if rule version is specified
        rule_version = data.get("meta", {}).get("rule_version")
        if not rule_version:
            validation_result.add_message(
                ValidationSeverity.WARNING,
                ValidationCategory.STRUCTURE,
                "Rule version not specified in character data",
                suggestion="Add rule version to meta.rule_version"
            )
        elif expected_version and rule_version != expected_version:
            validation_result.add_message(
                ValidationSeverity.WARNING,
                ValidationCategory.CONSISTENCY,
                f"Rule version mismatch: expected {expected_version}, got {rule_version}",
                expected=expected_version,
                actual=rule_version
            )
        
        # Validate rule-specific constraints
        if rule_version == "2024":
            # Add 2024-specific validation rules
            validation_result.messages.extend(self._validate_2024_rules(data))
        elif rule_version == "2014":
            # Add 2014-specific validation rules
            validation_result.messages.extend(self._validate_2014_rules(data))
        
        validation_result.is_valid = not validation_result.has_errors()
        return validation_result
    
    def _validate_2024_rules(self, data: Dict[str, Any]) -> List[ValidationMessage]:
        """Validate 2024-specific rules."""
        messages = []
        
        # Example 2024 rule: New spell system
        if "spells" in data:
            spells_data = data["spells"]
            if not isinstance(spells_data, dict):
                messages.append(ValidationMessage(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.STRUCTURE,
                    message="2024 rules require spells data to be a dictionary",
                    field_path="spells"
                ))
        
        return messages
    
    def _validate_2014_rules(self, data: Dict[str, Any]) -> List[ValidationMessage]:
        """Validate 2014-specific rules."""
        messages = []
        
        # Example 2014 rule: Legacy spell system
        if "spells" in data:
            spells_data = data["spells"]
            if not isinstance(spells_data, dict):
                messages.append(ValidationMessage(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.STRUCTURE,
                    message="2014 rules require spells data to be a dictionary",
                    field_path="spells"
                ))
        
        return messages
    
    def generate_validation_report(self, result: ValidationResult) -> str:
        """
        Generate a human-readable validation report.
        
        Args:
            result: Validation result to report on
            
        Returns:
            Formatted validation report
        """
        report = ["Validation Report", "=" * 40]
        
        if result.is_valid:
            report.append("✅ Validation PASSED")
        else:
            report.append("❌ Validation FAILED")
        
        if result.validation_time:
            report.append(f"Validation Time: {result.validation_time:.3f}s")
        
        if result.messages:
            report.append("\nMessages:")
            
            # Group messages by severity
            by_severity = {}
            for msg in result.messages:
                if msg.severity not in by_severity:
                    by_severity[msg.severity] = []
                by_severity[msg.severity].append(msg)
            
            for severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR, 
                           ValidationSeverity.WARNING, ValidationSeverity.INFO]:
                if severity in by_severity:
                    report.append(f"\n{severity.value.upper()}:")
                    for msg in by_severity[severity]:
                        report.append(f"  - {msg.message}")
                        if msg.field_path:
                            report.append(f"    Field: {msg.field_path}")
                        if msg.suggestion:
                            report.append(f"    Suggestion: {msg.suggestion}")
        
        return "\n".join(report)


# Global validator instance
global_validator = CharacterDataValidator()


def validate_character_data(data: Dict[str, Any], 
                          context: Dict[str, Any] = None) -> ValidationResult:
    """
    Validate character data using the global validator.
    
    Args:
        data: Character data to validate
        context: Additional context for validation
        
    Returns:
        ValidationResult with messages and validity status
    """
    return global_validator.validate(data, context)


def validate_calculation_result(result: Dict[str, Any], 
                               context: Dict[str, Any] = None) -> ValidationResult:
    """
    Validate calculation result using the global validator.
    
    Args:
        result: Calculation result to validate
        context: Additional context for validation
        
    Returns:
        ValidationResult with messages and validity status
    """
    return global_validator.validate_calculation_result(result, context)


def add_validation_rule(rule: ValidationRule):
    """Add a validation rule to the global validator."""
    global_validator.add_rule(rule)


def add_custom_validator(name: str, validator_func: Callable):
    """Add a custom validator function to the global validator."""
    global_validator.add_custom_validator(name, validator_func)