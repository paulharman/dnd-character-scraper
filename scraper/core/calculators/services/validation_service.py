"""
Validation Service

Comprehensive validation service for calculator inputs, outputs, and intermediate data.
This service provides centralized validation logic with configurable rules,
detailed error reporting, and performance monitoring.
"""

from typing import Dict, Any, List, Optional, Union, Callable, Set
import logging
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
import json
import re

from ..utils.validation import (
    ValidationResult, ValidationMessage, ValidationSeverity, ValidationCategory,
    ValidationRule, RequiredFieldRule, TypeValidationRule, RangeValidationRule,
    validate_character_data
)
from ..utils.performance import monitor_performance
from shared.models.character import Character

logger = logging.getLogger(__name__)


@dataclass
class ValidationContext:
    """Context for validation operations."""
    rule_version: str
    character_id: Optional[str] = None
    validation_level: str = "standard"  # strict, standard, lenient
    custom_rules: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class IValidationRule(ABC):
    """Interface for validation rules."""
    
    @abstractmethod
    def validate(self, data: Any, context: ValidationContext) -> List[ValidationMessage]:
        """Validate data against this rule."""
        pass
    
    @abstractmethod
    def get_rule_name(self) -> str:
        """Get the name of this rule."""
        pass


class CharacterLevelValidationRule(IValidationRule):
    """Rule for validating character level."""
    
    def validate(self, data: Any, context: ValidationContext) -> List[ValidationMessage]:
        """Validate character level."""
        messages = []
        
        if not isinstance(data, dict):
            return messages
        
        level = data.get('level')
        if level is None:
            messages.append(ValidationMessage(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.STRUCTURE,
                message="Character level is required",
                field_path="level"
            ))
        elif not isinstance(level, int):
            messages.append(ValidationMessage(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.TYPE,
                message=f"Character level must be an integer, got {type(level).__name__}",
                field_path="level",
                actual=type(level).__name__,
                expected="int"
            ))
        elif level < 1 or level > 20:
            messages.append(ValidationMessage(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.RANGE,
                message=f"Character level must be between 1 and 20, got {level}",
                field_path="level",
                actual=level,
                expected="1-20"
            ))
        
        return messages
    
    def get_rule_name(self) -> str:
        return "character_level"


class AbilityScoreValidationRule(IValidationRule):
    """Rule for validating ability scores."""
    
    def validate(self, data: Any, context: ValidationContext) -> List[ValidationMessage]:
        """Validate ability scores."""
        messages = []
        
        if not isinstance(data, dict):
            return messages
        
        ability_scores = data.get('ability_scores', {})
        if not isinstance(ability_scores, dict):
            messages.append(ValidationMessage(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.TYPE,
                message="Ability scores must be a dictionary",
                field_path="ability_scores"
            ))
            return messages
        
        required_abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        
        for ability in required_abilities:
            if ability not in ability_scores:
                messages.append(ValidationMessage(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.STRUCTURE,
                    message=f"Missing required ability score: {ability}",
                    field_path=f"ability_scores.{ability}"
                ))
                continue
            
            score_data = ability_scores[ability]
            if isinstance(score_data, dict):
                score = score_data.get('score')
            else:
                score = score_data
            
            if score is None:
                messages.append(ValidationMessage(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.STRUCTURE,
                    message=f"Ability score value is required for {ability}",
                    field_path=f"ability_scores.{ability}.score"
                ))
            elif not isinstance(score, (int, float)):
                messages.append(ValidationMessage(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.TYPE,
                    message=f"Ability score must be numeric for {ability}, got {type(score).__name__}",
                    field_path=f"ability_scores.{ability}.score",
                    actual=type(score).__name__,
                    expected="int or float"
                ))
            elif score < 1 or score > 30:
                messages.append(ValidationMessage(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.RANGE,
                    message=f"Ability score must be between 1 and 30 for {ability}, got {score}",
                    field_path=f"ability_scores.{ability}.score",
                    actual=score,
                    expected="1-30"
                ))
        
        return messages
    
    def get_rule_name(self) -> str:
        return "ability_scores"


class HitPointsValidationRule(IValidationRule):
    """Rule for validating hit points."""
    
    def validate(self, data: Any, context: ValidationContext) -> List[ValidationMessage]:
        """Validate hit points."""
        messages = []
        
        if not isinstance(data, dict):
            return messages
        
        hit_points = data.get('hit_points', {})
        if not isinstance(hit_points, dict):
            messages.append(ValidationMessage(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.TYPE,
                message="Hit points must be a dictionary",
                field_path="hit_points"
            ))
            return messages
        
        # Validate maximum hit points
        max_hp = hit_points.get('maximum')
        if max_hp is None:
            messages.append(ValidationMessage(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.STRUCTURE,
                message="Maximum hit points is required",
                field_path="hit_points.maximum"
            ))
        elif not isinstance(max_hp, (int, float)):
            messages.append(ValidationMessage(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.TYPE,
                message=f"Maximum hit points must be numeric, got {type(max_hp).__name__}",
                field_path="hit_points.maximum",
                actual=type(max_hp).__name__,
                expected="int or float"
            ))
        elif max_hp < 1:
            messages.append(ValidationMessage(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.RANGE,
                message=f"Maximum hit points must be at least 1, got {max_hp}",
                field_path="hit_points.maximum",
                actual=max_hp,
                expected="≥ 1"
            ))
        
        # Validate current hit points
        current_hp = hit_points.get('current')
        if current_hp is not None:
            if not isinstance(current_hp, (int, float)):
                messages.append(ValidationMessage(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.TYPE,
                    message=f"Current hit points must be numeric, got {type(current_hp).__name__}",
                    field_path="hit_points.current",
                    actual=type(current_hp).__name__,
                    expected="int or float"
                ))
            elif current_hp < 0:
                messages.append(ValidationMessage(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.RANGE,
                    message=f"Current hit points cannot be negative, got {current_hp}",
                    field_path="hit_points.current",
                    actual=current_hp,
                    expected="≥ 0"
                ))
        
        return messages
    
    def get_rule_name(self) -> str:
        return "hit_points"


class SpellValidationRule(IValidationRule):
    """Rule for validating spells."""
    
    def validate(self, data: Any, context: ValidationContext) -> List[ValidationMessage]:
        """Validate spells."""
        messages = []
        
        if not isinstance(data, dict):
            return messages
        
        spells = data.get('spells', [])
        if not isinstance(spells, list):
            messages.append(ValidationMessage(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.TYPE,
                message="Spells must be a list",
                field_path="spells"
            ))
            return messages
        
        for i, spell in enumerate(spells):
            if not isinstance(spell, dict):
                messages.append(ValidationMessage(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.TYPE,
                    message=f"Spell at index {i} must be a dictionary",
                    field_path=f"spells[{i}]"
                ))
                continue
            
            # Validate required spell fields
            required_fields = ['name', 'level']
            for field in required_fields:
                if field not in spell:
                    messages.append(ValidationMessage(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.STRUCTURE,
                        message=f"Spell at index {i} missing required field: {field}",
                        field_path=f"spells[{i}].{field}"
                    ))
            
            # Validate spell level
            spell_level = spell.get('level')
            if spell_level is not None:
                if not isinstance(spell_level, int):
                    messages.append(ValidationMessage(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.TYPE,
                        message=f"Spell level must be an integer for spell at index {i}",
                        field_path=f"spells[{i}].level",
                        actual=type(spell_level).__name__,
                        expected="int"
                    ))
                elif spell_level < 0 or spell_level > 9:
                    messages.append(ValidationMessage(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.RANGE,
                        message=f"Spell level must be between 0 and 9 for spell at index {i}, got {spell_level}",
                        field_path=f"spells[{i}].level",
                        actual=spell_level,
                        expected="0-9"
                    ))
        
        return messages
    
    def get_rule_name(self) -> str:
        return "spells"


class ValidationService:
    """
    Comprehensive validation service for calculator data.
    
    This service provides:
    - Input validation for raw D&D Beyond data
    - Output validation for calculation results
    - Character object validation
    - Custom rule registration and management
    - Performance monitoring and error reporting
    - Configurable validation levels
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize the validation service.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Rule registry
        self.rules: Dict[str, IValidationRule] = {}
        self.custom_validators: Dict[str, Callable] = {}
        
        # Validation statistics
        self.stats = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'validation_times': [],
            'rule_usage': {}
        }
        
        # Register default rules
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Register default validation rules."""
        default_rules = [
            CharacterLevelValidationRule(),
            AbilityScoreValidationRule(),
            HitPointsValidationRule(),
            SpellValidationRule()
        ]
        
        for rule in default_rules:
            self.register_rule(rule)
    
    def register_rule(self, rule: IValidationRule):
        """
        Register a validation rule.
        
        Args:
            rule: The validation rule to register
        """
        rule_name = rule.get_rule_name()
        self.rules[rule_name] = rule
        self.stats['rule_usage'][rule_name] = 0
        self.logger.info(f"Registered validation rule: {rule_name}")
    
    def unregister_rule(self, rule_name: str):
        """
        Unregister a validation rule.
        
        Args:
            rule_name: Name of the rule to unregister
        """
        if rule_name in self.rules:
            del self.rules[rule_name]
            if rule_name in self.stats['rule_usage']:
                del self.stats['rule_usage'][rule_name]
            self.logger.info(f"Unregistered validation rule: {rule_name}")
    
    def register_custom_validator(self, name: str, validator: Callable):
        """
        Register a custom validator function.
        
        Args:
            name: Name of the validator
            validator: Validator function
        """
        self.custom_validators[name] = validator
        self.logger.info(f"Registered custom validator: {name}")
    
    @monitor_performance("validation_service_validate_input")
    def validate_input(self, raw_data: Dict[str, Any], context: ValidationContext) -> ValidationResult:
        """
        Validate raw input data.
        
        Args:
            raw_data: Raw D&D Beyond data
            context: Validation context
            
        Returns:
            Validation result
        """
        self.stats['total_validations'] += 1
        start_time = datetime.now()
        
        try:
            # Create validation result based on validation level
            result = ValidationResult(is_valid=True)
            
            # Apply validation rules based on context level
            if context.validation_level == "strict":
                # Use the existing validation utility as a base
                strict_result = validate_character_data(raw_data, context.metadata)
                result.messages.extend(strict_result.messages)
                result.is_valid = strict_result.is_valid
                
                # Apply all rules in strict mode
                for rule_name, rule in self.rules.items():
                    try:
                        rule_messages = rule.validate(raw_data, context)
                        result.messages.extend(rule_messages)
                        self.stats['rule_usage'][rule_name] += 1
                    except Exception as e:
                        self.logger.error(f"Error in validation rule {rule_name}: {e}")
                        result.add_message(
                            ValidationSeverity.ERROR,
                            ValidationCategory.STRUCTURE,
                            f"Validation rule '{rule_name}' failed: {str(e)}"
                        )
            elif context.validation_level == "standard":
                # For standard mode, only apply basic validation rules, not full character data validation
                # The validate_character_data function is designed for processed output, not raw input
                pass  # Skip basic validation for now - apply only the basic rules below
                
                # Always apply basic rules for obviously invalid data in standard mode
                basic_rules = ['character_level', 'ability_scores', 'hit_points']
                for rule_name in basic_rules:
                    if rule_name in self.rules:
                        try:
                            rule_messages = self.rules[rule_name].validate(raw_data, context)
                            result.messages.extend(rule_messages)
                            self.stats['rule_usage'][rule_name] += 1
                        except Exception as e:
                            self.logger.error(f"Error in validation rule {rule_name}: {e}")
                            result.add_message(
                                ValidationSeverity.ERROR,
                                ValidationCategory.STRUCTURE,
                                f"Validation rule '{rule_name}' failed: {str(e)}"
                            )
                
                # Apply custom rules if explicitly requested
                for rule_name in context.custom_rules:
                    if rule_name in self.rules and rule_name not in basic_rules:
                        try:
                            rule_messages = self.rules[rule_name].validate(raw_data, context)
                            result.messages.extend(rule_messages)
                            self.stats['rule_usage'][rule_name] += 1
                        except Exception as e:
                            self.logger.error(f"Error in validation rule {rule_name}: {e}")
                            result.add_message(
                                ValidationSeverity.ERROR,
                                ValidationCategory.STRUCTURE,
                                f"Validation rule '{rule_name}' failed: {str(e)}"
                            )
            else:  # lenient mode
                # Only apply custom rules if explicitly requested
                for rule_name in context.custom_rules:
                    if rule_name in self.rules:
                        try:
                            rule_messages = self.rules[rule_name].validate(raw_data, context)
                            result.messages.extend(rule_messages)
                            self.stats['rule_usage'][rule_name] += 1
                        except Exception as e:
                            self.logger.error(f"Error in validation rule {rule_name}: {e}")
                            result.add_message(
                                ValidationSeverity.ERROR,
                                ValidationCategory.STRUCTURE,
                                f"Validation rule '{rule_name}' failed: {str(e)}"
                            )
            
            # Apply custom validators
            for validator_name, validator in self.custom_validators.items():
                try:
                    validator_messages = validator(raw_data, context)
                    if validator_messages:
                        result.messages.extend(validator_messages)
                except Exception as e:
                    self.logger.error(f"Error in custom validator {validator_name}: {e}")
                    result.add_message(
                        ValidationSeverity.ERROR,
                        ValidationCategory.STRUCTURE,
                        f"Custom validator '{validator_name}' failed: {str(e)}"
                    )
            
            # Update validity based on all messages
            result.is_valid = not result.has_errors()
            
            # Update statistics
            if result.is_valid:
                self.stats['successful_validations'] += 1
            else:
                self.stats['failed_validations'] += 1
            
            validation_time = (datetime.now() - start_time).total_seconds()
            self.stats['validation_times'].append(validation_time)
            
            self.logger.info(f"Input validation {'passed' if result.is_valid else 'failed'} "
                           f"for character {context.character_id}")
            
            return result
            
        except Exception as e:
            self.stats['failed_validations'] += 1
            self.logger.error(f"Input validation error: {str(e)}")
            
            error_result = ValidationResult(is_valid=False)
            error_result.add_message(
                ValidationSeverity.ERROR,
                ValidationCategory.STRUCTURE,
                f"Input validation failed: {str(e)}"
            )
            return error_result
    
    @monitor_performance("validation_service_validate_output")
    def validate_output(self, calculation_result: Dict[str, Any], context: ValidationContext) -> ValidationResult:
        """
        Validate calculation output data.
        
        Args:
            calculation_result: Calculation results
            context: Validation context
            
        Returns:
            Validation result
        """
        result = ValidationResult(is_valid=True)
        
        # Validate result structure
        if not isinstance(calculation_result, dict):
            result.add_message(
                ValidationSeverity.ERROR,
                ValidationCategory.TYPE,
                "Calculation result must be a dictionary"
            )
            return result
        
        # Validate coordinator results
        for coordinator_name, coordinator_data in calculation_result.items():
            if not isinstance(coordinator_data, dict):
                result.add_message(
                    ValidationSeverity.ERROR,
                    ValidationCategory.TYPE,
                    f"Coordinator '{coordinator_name}' data must be a dictionary"
                )
                continue
            
            # Apply rules to coordinator data
            for rule_name, rule in self.rules.items():
                try:
                    rule_messages = rule.validate(coordinator_data, context)
                    result.messages.extend(rule_messages)
                    self.stats['rule_usage'][rule_name] += 1
                except Exception as e:
                    self.logger.error(f"Error in validation rule {rule_name} for coordinator {coordinator_name}: {e}")
        
        result.is_valid = not result.has_errors()
        
        self.logger.info(f"Output validation {'passed' if result.is_valid else 'failed'} "
                       f"for character {context.character_id}")
        
        return result
    
    @monitor_performance("validation_service_validate_character")
    def validate_character(self, character: Character, context: ValidationContext) -> ValidationResult:
        """
        Validate a complete Character object.
        
        Args:
            character: Character object to validate
            context: Validation context
            
        Returns:
            Validation result
        """
        result = ValidationResult(is_valid=True)
        
        # Basic character validation
        if not character.name or character.name.strip() == '':
            result.add_message(
                ValidationSeverity.ERROR,
                ValidationCategory.STRUCTURE,
                "Character name cannot be empty"
            )
        
        if character.level < 1 or character.level > 20:
            result.add_message(
                ValidationSeverity.ERROR,
                ValidationCategory.RANGE,
                f"Character level must be between 1 and 20, got {character.level}"
            )
        
        if not character.classes:
            result.add_message(
                ValidationSeverity.ERROR,
                ValidationCategory.STRUCTURE,
                "Character must have at least one class"
            )
        
        # Validate ability scores
        for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
            score = getattr(character.ability_scores, ability)
            if score < 1 or score > 30:
                result.add_message(
                    ValidationSeverity.ERROR,
                    ValidationCategory.RANGE,
                    f"{ability.title()} score must be between 1 and 30, got {score}"
                )
        
        # Validate hit points
        if character.hit_points.maximum < 1:
            result.add_message(
                ValidationSeverity.ERROR,
                ValidationCategory.RANGE,
                "Maximum hit points must be at least 1"
            )
        
        if character.hit_points.current < 0:
            result.add_message(
                ValidationSeverity.ERROR,
                ValidationCategory.RANGE,
                "Current hit points cannot be negative"
            )
        
        # Validate armor class
        if character.armor_class.total < 1:
            result.add_message(
                ValidationSeverity.ERROR,
                ValidationCategory.RANGE,
                "Armor class must be at least 1"
            )
        
        # Rule version specific validation
        if context.rule_version == "2024":
            self._validate_2024_character(character, result)
        elif context.rule_version == "2014":
            self._validate_2014_character(character, result)
        
        result.is_valid = not result.has_errors()
        
        self.logger.info(f"Character validation {'passed' if result.is_valid else 'failed'} "
                       f"for character {character.name}")
        
        return result
    
    def _validate_2024_character(self, character: Character, result: ValidationResult):
        """Validate character against 2024 rules."""
        # Add 2024-specific validation logic
        pass
    
    def _validate_2014_character(self, character: Character, result: ValidationResult):
        """Validate character against 2014 rules."""
        # Add 2014-specific validation logic
        pass
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """
        Get validation statistics.
        
        Returns:
            Dictionary of validation statistics
        """
        stats = {
            'total_validations': self.stats['total_validations'],
            'successful_validations': self.stats['successful_validations'],
            'failed_validations': self.stats['failed_validations'],
            'success_rate': 0.0,
            'average_validation_time': 0.0,
            'rule_usage': self.stats['rule_usage'].copy()
        }
        
        if self.stats['total_validations'] > 0:
            stats['success_rate'] = (self.stats['successful_validations'] / self.stats['total_validations']) * 100
        
        if self.stats['validation_times']:
            stats['average_validation_time'] = sum(self.stats['validation_times']) / len(self.stats['validation_times'])
        
        return stats
    
    def clear_statistics(self):
        """Clear validation statistics."""
        self.stats = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'validation_times': [],
            'rule_usage': {rule_name: 0 for rule_name in self.rules.keys()}
        }
        self.logger.info("Validation statistics cleared")
    
    def list_rules(self) -> List[str]:
        """
        List all registered validation rules.
        
        Returns:
            List of rule names
        """
        return list(self.rules.keys())
    
    def list_custom_validators(self) -> List[str]:
        """
        List all registered custom validators.
        
        Returns:
            List of validator names
        """
        return list(self.custom_validators.keys())
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the validation service.
        
        Returns:
            Health check results
        """
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'rules_registered': len(self.rules),
            'custom_validators_registered': len(self.custom_validators),
            'statistics': self.get_validation_statistics()
        }