"""
Character Data Validator

Validates complete character data structure and content against
expected formats and known validation data.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base import BaseValidator, ValidationResult

logger = logging.getLogger(__name__)


class CharacterValidator(BaseValidator):
    """
    Validates complete character data against known good values.
    
    Performs structural validation, data integrity checks, and
    comparison against validation files when available.
    """
    
    def __init__(self, validation_data_dir: str = "data/validation_data"):
        """
        Initialize character validator.
        
        Args:
            validation_data_dir: Directory containing validation JSON files
        """
        self.validation_dir = Path(validation_data_dir)
        
    def validate(self, character_data: Dict[str, Any], 
                validation_file: Optional[Path] = None) -> ValidationResult:
        """
        Validate character data structure and content.
        
        Args:
            character_data: Complete character data from scraper
            validation_file: Optional validation file for comparison
            
        Returns:
            ValidationResult with detailed findings
        """
        result = ValidationResult(is_valid=True)
        
        # Step 1: Validate required structure
        logger.debug("Validating character data structure...")
        structure_errors = self._validate_structure(character_data)
        for error in structure_errors:
            result.add_error(error)
        
        # Step 2: Validate data integrity
        logger.debug("Validating data integrity...")
        integrity_errors = self._validate_data_integrity(character_data)
        for error in integrity_errors:
            result.add_error(error)
        
        # Step 3: Validate calculations are reasonable
        logger.debug("Validating calculations...")
        calc_warnings = self._validate_calculations(character_data)
        for warning in calc_warnings:
            result.add_warning(warning)
        
        # Step 4: Check completeness
        logger.debug("Checking data completeness...")
        completeness_warnings = self._check_completeness(character_data)
        for warning in completeness_warnings:
            result.add_warning(warning)
        
        # Step 5: Compare against validation file if provided
        if validation_file:
            logger.debug(f"Comparing against validation file: {validation_file}")
            comparison_result = self._compare_to_validation(character_data, validation_file)
            result.merge(comparison_result)
        
        # Calculate overall accuracy
        result.calculate_accuracy()
        
        return result
    
    def _validate_structure(self, character_data: Dict[str, Any]) -> List[str]:
        """Validate basic data structure."""
        errors = []
        
        # Check for v6.0.0 required fields
        required_fields = [
            "character_id", "name", "level", "classes", 
            "ability_scores", "ability_modifiers"
        ]
        
        for field in required_fields:
            if field not in character_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate classes structure
        if "classes" in character_data:
            classes = character_data["classes"]
            if not isinstance(classes, list):
                errors.append("Classes must be a list")
            else:
                for i, class_info in enumerate(classes):
                    if not isinstance(class_info, dict):
                        errors.append(f"Class {i}: Must be a dictionary")
                    elif "name" not in class_info:
                        errors.append(f"Class {i}: Missing name")
                    elif "level" not in class_info:
                        errors.append(f"Class {i}: Missing level")
        
        # Validate ability scores structure
        if "ability_scores" in character_data:
            scores = character_data["ability_scores"]
            if not isinstance(scores, dict):
                errors.append("Ability scores must be a dictionary")
            else:
                abilities = ["strength", "dexterity", "constitution", 
                           "intelligence", "wisdom", "charisma"]
                for ability in abilities:
                    if ability not in scores:
                        errors.append(f"Missing ability score: {ability}")
        
        return errors
    
    def _validate_data_integrity(self, character_data: Dict[str, Any]) -> List[str]:
        """Validate data integrity and consistency."""
        errors = []
        
        # Validate level consistency
        if "level" in character_data and "classes" in character_data:
            total_level = character_data["level"]
            class_levels = sum(cls.get("level", 0) for cls in character_data["classes"])
            
            if total_level != class_levels:
                errors.append(f"Level mismatch: total {total_level} != sum of class levels {class_levels}")
        
        # Validate ability scores and modifiers consistency
        if "ability_scores" in character_data and "ability_modifiers" in character_data:
            scores = character_data["ability_scores"]
            modifiers = character_data["ability_modifiers"]
            
            for ability, score in scores.items():
                if ability in modifiers:
                    expected_modifier = (score - 10) // 2
                    actual_modifier = modifiers[ability]
                    
                    if expected_modifier != actual_modifier:
                        errors.append(f"{ability} modifier incorrect: "
                                    f"score {score} should give modifier {expected_modifier}, "
                                    f"but got {actual_modifier}")
        
        # Validate proficiency bonus
        if "level" in character_data and "proficiency_bonus" in character_data:
            level = character_data["level"]
            expected_prof = 2 + ((level - 1) // 4)
            actual_prof = character_data["proficiency_bonus"]
            
            if expected_prof != actual_prof:
                errors.append(f"Proficiency bonus incorrect: "
                            f"level {level} should give +{expected_prof}, "
                            f"but got +{actual_prof}")
        
        return errors
    
    def _validate_calculations(self, character_data: Dict[str, Any]) -> List[str]:
        """Validate that calculated values are reasonable."""
        warnings = []
        
        # Check level
        level = character_data.get("level", 0)
        if level < 1 or level > 20:
            warnings.append(f"Unusual level: {level} (expected 1-20)")
        
        # Check hit points
        max_hp = character_data.get("max_hp", 0)
        if max_hp < level:  # Minimum 1 HP per level
            warnings.append(f"Suspiciously low HP: {max_hp} for level {level}")
        elif max_hp > level * 20:  # Very high even for max rolls
            warnings.append(f"Suspiciously high HP: {max_hp} for level {level}")
        
        # Check armor class
        armor_class = character_data.get("armor_class", 10)
        if armor_class < 10:
            warnings.append(f"AC below minimum: {armor_class} (minimum is 10)")
        elif armor_class > 30:
            warnings.append(f"Unusually high AC: {armor_class}")
        
        # Check ability scores
        ability_scores = character_data.get("ability_scores", {})
        for ability, score in ability_scores.items():
            if isinstance(score, (int, float)) and score < 3:
                warnings.append(f"Impossible {ability} score: {score} (minimum is 3)")
            elif isinstance(score, (int, float)) and score > 30:
                warnings.append(f"Unusually high {ability} score: {score} (maximum is usually 30)")
            elif isinstance(score, (int, float)) and score > 20 and level < 20:
                warnings.append(f"High {ability} score {score} for level {level}")
        
        # Check spell save DC and attack bonus
        if character_data.get("spellcasting", {}).get("is_spellcaster", False):
            spellcasting = character_data["spellcasting"]
            save_dc = spellcasting.get("spell_save_dc", 0)
            attack_bonus = spellcasting.get("spell_attack_bonus", 0)
            
            if save_dc > 0:
                # Expected: 8 + prof + ability modifier
                min_dc = 8 + 2 + (-5)  # Min prof +2, worst modifier -5
                max_dc = 8 + 6 + 5     # Max prof +6, best modifier +5
                
                if save_dc < min_dc or save_dc > max_dc:
                    warnings.append(f"Unusual spell save DC: {save_dc} (expected {min_dc}-{max_dc})")
            
            if attack_bonus is not None:
                # Expected: prof + ability modifier
                min_bonus = 2 + (-5)   # Min prof +2, worst modifier -5
                max_bonus = 6 + 5      # Max prof +6, best modifier +5
                
                if attack_bonus < min_bonus or attack_bonus > max_bonus:
                    warnings.append(f"Unusual spell attack bonus: {attack_bonus} (expected {min_bonus}-{max_bonus})")
        
        return warnings
    
    def _check_completeness(self, character_data: Dict[str, Any]) -> List[str]:
        """Check for completeness and warn about missing optional data."""
        warnings = []
        
        # Check for expected optional fields
        optional_fields = {
            "species": "Character species/race",
            "background": "Character background",
            "equipment": "Equipment list",
            "features": "Character features/traits"
        }
        
        for field, description in optional_fields.items():
            if field not in character_data:
                warnings.append(f"Optional field missing: {field} ({description})")
        
        # Check spellcasting completeness
        if character_data.get("spellcasting", {}).get("is_spellcaster", False):
            spellcasting = character_data["spellcasting"]
            spell_fields = ["spellcasting_ability", "spell_save_dc", "spell_attack_bonus"]
            
            for field in spell_fields:
                if field not in spellcasting:
                    warnings.append(f"Spellcaster missing {field}")
        
        # Check if character has no equipment
        if "equipment" in character_data and len(character_data["equipment"]) == 0:
            warnings.append("Character has no equipment listed")
        
        return warnings
    
    def _compare_to_validation(self, character_data: Dict[str, Any], 
                               validation_file: Path) -> ValidationResult:
        """Compare character data against validation file."""
        result = ValidationResult(is_valid=True)
        
        if not validation_file.exists():
            result.add_error(f"Validation file not found: {validation_file}")
            return result
        
        try:
            with open(validation_file, 'r', encoding='utf-8') as f:
                validation_data = json.load(f)
        except Exception as e:
            result.add_error(f"Failed to load validation file: {e}")
            return result
        
        # Compare key fields
        comparisons = [
            ("name", character_data.get("name"), validation_data.get("name")),
            ("level", character_data.get("level"), validation_data.get("level")),
            ("armor_class", character_data.get("armor_class"), validation_data.get("armor_class")),
            ("max_hp", character_data.get("max_hp"), validation_data.get("max_hp")),
            ("proficiency_bonus", character_data.get("proficiency_bonus"), validation_data.get("proficiency_bonus")),
            ("initiative_bonus", character_data.get("initiative_bonus"), validation_data.get("initiative")),
        ]
        
        # Compare ability scores
        char_scores = character_data.get("ability_scores", {})
        val_scores = validation_data.get("ability_scores", {})
        
        for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            comparisons.append((
                f"ability_scores.{ability}",
                char_scores.get(ability),
                val_scores.get(ability)
            ))
        
        # Compare ability modifiers
        char_mods = character_data.get("ability_modifiers", {})
        val_mods = validation_data.get("ability_modifiers", {})
        
        for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            comparisons.append((
                f"ability_modifiers.{ability}",
                char_mods.get(ability),
                val_mods.get(ability)
            ))
        
        # Compare classes
        char_classes = character_data.get("classes", [])
        val_classes = validation_data.get("classes", [])
        
        if len(char_classes) == len(val_classes):
            for i, (char_cls, val_cls) in enumerate(zip(char_classes, val_classes)):
                comparisons.append((
                    f"classes[{i}].name",
                    char_cls.get("name"),
                    val_cls.get("name")
                ))
                comparisons.append((
                    f"classes[{i}].level",
                    char_cls.get("level"),
                    val_cls.get("level")
                ))
        else:
            result.add_error(f"Different number of classes: {len(char_classes)} vs {len(val_classes)}")
        
        # Compare spellcasting if applicable
        if validation_data.get("spellcasting", {}).get("is_spellcaster", False):
            char_spell = character_data.get("spellcasting", {})
            val_spell = validation_data.get("spellcasting", {})
            
            comparisons.extend([
                ("spellcasting.spell_save_dc", char_spell.get("spell_save_dc"), val_spell.get("spell_save_dc")),
                ("spellcasting.spell_attack_bonus", char_spell.get("spell_attack_bonus"), val_spell.get("spell_attack_bonus")),
                ("spellcasting.spellcasting_ability", char_spell.get("spellcasting_ability"), val_spell.get("spellcasting_ability")),
            ])
        
        # Process all comparisons
        for field_name, actual, expected in comparisons:
            if actual is not None and expected is not None:
                result.add_field_comparison(field_name, actual, expected)
        
        return result
    
    def validate_character_file(self, character_id: int) -> ValidationResult:
        """
        Validate a character using its validation file.
        
        Args:
            character_id: Character ID to validate
            
        Returns:
            ValidationResult
        """
        validation_file = self.validation_dir / f"{character_id}_validation.json"
        
        if not validation_file.exists():
            result = ValidationResult(is_valid=False)
            result.add_error(f"No validation file found for character {character_id}")
            return result
        
        # This would normally load the character data from the scraper
        # For now, we'll return a placeholder
        result = ValidationResult(is_valid=True)
        result.add_warning(f"Character validation for {character_id} not yet implemented")
        return result