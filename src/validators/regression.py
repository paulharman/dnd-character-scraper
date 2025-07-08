"""
Regression Validator

Validates v6.0.0 output against v5.2.0 baseline to ensure no regression
in functionality or accuracy.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from .base import BaseValidator, ValidationResult

logger = logging.getLogger(__name__)


class RegressionValidator(BaseValidator):
    """
    Validates v6.0.0 output against v5.2.0 baseline data.
    
    Ensures that the new modular architecture maintains or improves
    upon the accuracy and completeness of v5.2.0.
    """
    
    def __init__(self, baseline_dir: str = "data/baseline/scraper"):
        """
        Initialize regression validator.
        
        Args:
            baseline_dir: Directory containing v5.2.0 baseline JSON files
        """
        self.baseline_dir = Path(baseline_dir)
        
        # Fields that are expected to differ between versions
        self.ignore_fields = {
            "scraper_version",  # Will be different
            "generated_timestamp",  # Will be different
            "calculation_metadata",  # New in v6.0.0
            "rule_version",  # New in v6.0.0
            "_calculation_log",  # Internal field
        }
        
        # Fields that require special comparison
        self.special_fields = {
            "ability_score_breakdown",  # May have different structure
            "hit_point_breakdown",  # May have different structure
            "ac_breakdown",  # May have different structure
        }
    
    def validate(self, character_data: Dict[str, Any], 
                character_id: int = None,
                baseline_file: Optional[Path] = None) -> ValidationResult:
        """
        Validate character data against v5.2.0 baseline.
        
        Args:
            character_data: v6.0.0 character data
            character_id: Character ID for finding baseline
            baseline_file: Optional specific baseline file
            
        Returns:
            ValidationResult with regression findings
        """
        result = ValidationResult(is_valid=True)
        
        # Find baseline file
        if not baseline_file and character_id:
            baseline_file = self.baseline_dir / f"baseline_{character_id}.json"
        
        if not baseline_file or not baseline_file.exists():
            result.add_error(f"No baseline file found for comparison")
            return result
        
        # Load baseline data
        try:
            with open(baseline_file, 'r', encoding='utf-8') as f:
                baseline_data = json.load(f)
        except Exception as e:
            result.add_error(f"Failed to load baseline: {e}")
            return result
        
        logger.info(f"Comparing against baseline: {baseline_file.name}")
        
        # Compare structures
        structure_diffs = self._compare_structure(character_data, baseline_data)
        for diff in structure_diffs:
            result.add_warning(f"Structure difference: {diff}")
        
        # Compare critical fields
        critical_comparisons = self._compare_critical_fields(character_data, baseline_data)
        for field, v6_value, v5_value, matches in critical_comparisons:
            result.add_field_comparison(field, v6_value, v5_value, matches)
        
        # Compare calculated values
        calc_comparisons = self._compare_calculations(character_data, baseline_data)
        for field, v6_value, v5_value, matches in calc_comparisons:
            result.add_field_comparison(field, v6_value, v5_value, matches)
        
        # Check for missing features
        missing_features = self._check_missing_features(character_data, baseline_data)
        for feature in missing_features:
            result.add_error(f"Missing feature from v5.2.0: {feature}")
        
        # Check for improvements
        improvements = self._check_improvements(character_data, baseline_data)
        for improvement in improvements:
            result.add_warning(f"✨ Improvement: {improvement}")
        
        # Calculate regression score
        result.calculate_accuracy()
        
        # Determine if this is a regression
        if result.accuracy_score is not None and result.accuracy_score < 0.95:
            result.add_error(f"Regression detected: accuracy {result.accuracy_score:.1%} < 95%")
            result.is_valid = False
        
        return result
    
    def _compare_structure(self, v6_data: Dict[str, Any], 
                          v5_data: Dict[str, Any]) -> List[str]:
        """Compare data structure between versions."""
        differences = []
        
        # Get top-level keys
        v6_keys = set(v6_data.keys()) - self.ignore_fields
        v5_keys = set(v5_data.keys()) - self.ignore_fields
        
        # Check for missing keys
        missing_in_v6 = v5_keys - v6_keys
        for key in missing_in_v6:
            differences.append(f"Missing field in v6.0.0: {key}")
        
        # Check for new keys (not necessarily bad)
        new_in_v6 = v6_keys - v5_keys
        for key in new_in_v6:
            differences.append(f"New field in v6.0.0: {key}")
        
        return differences
    
    def _compare_critical_fields(self, v6_data: Dict[str, Any], 
                                 v5_data: Dict[str, Any]) -> List[Tuple[str, Any, Any, bool]]:
        """Compare critical character fields."""
        comparisons = []
        
        # Character basics
        critical_fields = [
            "name",
            "level", 
            "hit_points",  # v5.2.0 name
            "max_hp",      # v6.0.0 name
            "armor_class",
            "proficiency_bonus",
            "initiative_bonus",
            "speed",
        ]
        
        for field in critical_fields:
            # Handle field name changes
            v6_field = field
            v5_field = field
            
            if field == "hit_points" and "hit_points" not in v6_data and "max_hp" in v6_data:
                v6_field = "max_hp"
            elif field == "max_hp" and "max_hp" not in v5_data and "hit_points" in v5_data:
                v5_field = "hit_points"
            
            v6_value = v6_data.get(v6_field)
            v5_value = v5_data.get(v5_field)
            
            if v6_value is not None and v5_value is not None:
                matches = v6_value == v5_value
                comparisons.append((field, v6_value, v5_value, matches))
        
        # Ability scores
        v6_scores = v6_data.get("ability_scores", {})
        v5_scores = v5_data.get("ability_scores", {})
        
        for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            v6_value = v6_scores.get(ability)
            v5_value = v5_scores.get(ability)
            
            if v6_value is not None and v5_value is not None:
                matches = v6_value == v5_value
                comparisons.append((f"ability_scores.{ability}", v6_value, v5_value, matches))
        
        # Classes
        v6_classes = v6_data.get("classes", [])
        v5_classes = v5_data.get("classes", [])
        
        if len(v6_classes) == len(v5_classes):
            for i, (v6_cls, v5_cls) in enumerate(zip(v6_classes, v5_classes)):
                # Compare class names
                v6_name = v6_cls.get("definition", {}).get("name") or v6_cls.get("name")
                v5_name = v5_cls.get("definition", {}).get("name") or v5_cls.get("name")
                
                if v6_name and v5_name:
                    matches = v6_name.lower() == v5_name.lower()
                    comparisons.append((f"class[{i}].name", v6_name, v5_name, matches))
                
                # Compare class levels
                v6_level = v6_cls.get("level")
                v5_level = v5_cls.get("level")
                
                if v6_level is not None and v5_level is not None:
                    matches = v6_level == v5_level
                    comparisons.append((f"class[{i}].level", v6_level, v5_level, matches))
        
        return comparisons
    
    def _compare_calculations(self, v6_data: Dict[str, Any], 
                             v5_data: Dict[str, Any]) -> List[Tuple[str, Any, Any, bool]]:
        """Compare calculated values."""
        comparisons = []
        
        # Compare debug_summary if available
        v6_debug = v6_data.get("debug_summary", {})
        v5_debug = v5_data.get("debug_summary", {})
        
        if v6_debug and v5_debug:
            # Spellcasting
            v6_spell = v6_debug.get("spellcasting", {})
            v5_spell = v5_debug.get("spellcasting", {})
            
            spell_fields = [
                "is_spellcaster",
                "spell_save_dc",
                "spell_attack_bonus",
                "spellcasting_ability"
            ]
            
            for field in spell_fields:
                v6_value = v6_spell.get(field)
                v5_value = v5_spell.get(field)
                
                if v6_value is not None and v5_value is not None:
                    matches = v6_value == v5_value
                    comparisons.append((f"spellcasting.{field}", v6_value, v5_value, matches))
            
            # Spell slots
            v6_slots = v6_spell.get("spell_slots", [])
            v5_slots = v5_spell.get("spell_slots", [])
            
            if len(v6_slots) == len(v5_slots):
                for i, (v6_slot, v5_slot) in enumerate(zip(v6_slots, v5_slots)):
                    if v6_slot != v5_slot:
                        comparisons.append((f"spell_slots[{i}]", v6_slot, v5_slot, False))
        
        # Compare spellcasting data directly if debug_summary not available
        elif "spellcasting" in v6_data and "spellcasting" in v5_data:
            v6_spell = v6_data["spellcasting"]
            v5_spell = v5_data["spellcasting"]
            
            for field in ["spell_save_dc", "spell_attack_bonus", "spellcasting_ability"]:
                v6_value = v6_spell.get(field)
                v5_value = v5_spell.get(field)
                
                if v6_value is not None and v5_value is not None:
                    matches = v6_value == v5_value
                    comparisons.append((f"spellcasting.{field}", v6_value, v5_value, matches))
        
        return comparisons
    
    def _check_missing_features(self, v6_data: Dict[str, Any], 
                                v5_data: Dict[str, Any]) -> List[str]:
        """Check for features present in v5.2.0 but missing in v6.0.0."""
        missing = []
        
        # Check for spell data
        if "spells" in v5_data and "spells" not in v6_data:
            if "spell_list" not in v6_data:  # Allow for renamed field
                missing.append("Spell list data")
        
        # Check for inventory
        if "inventory" in v5_data and "inventory" not in v6_data:
            if "equipment" not in v6_data:  # Allow for renamed field
                missing.append("Inventory/equipment data")
        
        # Check for actions
        if "actions" in v5_data and "actions" not in v6_data:
            missing.append("Character actions")
        
        # Check for features
        if "features" in v5_data and "features" not in v6_data:
            missing.append("Character features/traits")
        
        # Check for modifiers
        if "modifiers" in v5_data and "modifiers" not in v6_data:
            missing.append("Character modifiers")
        
        return missing
    
    def _check_improvements(self, v6_data: Dict[str, Any], 
                           v5_data: Dict[str, Any]) -> List[str]:
        """Check for improvements in v6.0.0 over v5.2.0."""
        improvements = []
        
        # Check for new calculation breakdowns
        if "ability_score_breakdown" in v6_data and "ability_score_breakdown" not in v5_data:
            improvements.append("Added ability score breakdown")
        
        if "hit_point_breakdown" in v6_data and "hit_point_breakdown" not in v5_data:
            improvements.append("Added hit point breakdown")
        
        if "ac_breakdown" in v6_data and "ac_breakdown" not in v5_data:
            improvements.append("Added armor class breakdown")
        
        # Check for rule version detection
        if "rule_version" in v6_data:
            improvements.append(f"Added rule version detection: {v6_data['rule_version']}")
        
        # Check for enhanced spell data structure
        v6_spells = v6_data.get("spells", {})
        v5_spells = v5_data.get("spells", {})
        
        if isinstance(v6_spells, dict) and "class_spells" in v6_spells:
            if not isinstance(v5_spells, dict) or "class_spells" not in v5_spells:
                improvements.append("Enhanced spell organization structure")
        
        return improvements
    
    def validate_all_baselines(self) -> Dict[int, ValidationResult]:
        """
        Validate all baseline files in the baseline directory.
        
        Returns:
            Dictionary mapping character ID to validation result
        """
        results = {}
        
        baseline_files = list(self.baseline_dir.glob("baseline_*.json"))
        logger.info(f"Found {len(baseline_files)} baseline files to validate")
        
        for baseline_file in baseline_files:
            # Extract character ID from filename
            try:
                char_id = int(baseline_file.stem.split('_')[1])
            except (IndexError, ValueError):
                logger.warning(f"Skipping invalid baseline filename: {baseline_file}")
                continue
            
            # For this method, we'd need to run v6.0.0 scraper and compare
            # For now, return a placeholder
            result = ValidationResult(is_valid=True)
            result.add_warning(f"Baseline validation for {char_id} not yet implemented")
            results[char_id] = result
        
        return results