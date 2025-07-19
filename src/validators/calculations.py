"""
Calculation Validator

Validates calculator outputs for consistency and accuracy, ensuring
all calculations follow D&D rules correctly.
"""

import logging
from typing import Dict, Any, List, Optional

from .base import BaseValidator, ValidationResult
from src.calculators.character_calculator import CharacterCalculator
from src.rules.constants import GameConstants

logger = logging.getLogger(__name__)


class CalculationValidator(BaseValidator):
    """
    Validates calculator outputs for consistency and accuracy.
    
    Ensures that all calculations follow D&D rules correctly and
    that different calculators produce consistent results.
    """
    
    def __init__(self, character_calculator: Optional[CharacterCalculator] = None):
        """
        Initialize calculation validator.
        
        Args:
            character_calculator: Optional character calculator instance
        """
        self.calculator = character_calculator or CharacterCalculator()
        self.constants = GameConstants()
    
    def validate(self, character_data: Dict[str, Any], raw_data: Dict[str, Any] = None) -> ValidationResult:
        """
        Validate all calculations are consistent.
        
        Args:
            character_data: Calculated character data
            raw_data: Optional raw D&D Beyond data for cross-validation
            
        Returns:
            ValidationResult with calculation findings
        """
        result = ValidationResult(is_valid=True)
        
        # Validate ability score calculations
        logger.debug("Validating ability score calculations...")
        ability_errors = self._validate_ability_scores(character_data)
        for error in ability_errors:
            result.add_error(error)
        
        # Validate HP calculations
        logger.debug("Validating hit point calculations...")
        hp_errors = self._validate_hit_points(character_data)
        for error in hp_errors:
            result.add_error(error)
        
        # Validate AC calculations
        logger.debug("Validating armor class calculations...")
        ac_errors = self._validate_armor_class(character_data)
        for error in ac_errors:
            result.add_error(error)
        
        # Validate spellcasting calculations
        if character_data.get("spellcasting", {}).get("is_spellcaster", False):
            logger.debug("Validating spellcasting calculations...")
            spell_errors = self._validate_spellcasting(character_data)
            for error in spell_errors:
                result.add_error(error)
        
        # Validate proficiency calculations
        logger.debug("Validating proficiency calculations...")
        prof_errors = self._validate_proficiencies(character_data)
        for error in prof_errors:
            result.add_error(error)
        
        # Cross-validate with raw data if provided
        if raw_data:
            logger.debug("Cross-validating with raw D&D Beyond data...")
            cross_warnings = self._cross_validate_with_raw(character_data, raw_data)
            for warning in cross_warnings:
                result.add_warning(warning)
        
        return result
    
    def _validate_ability_scores(self, character_data: Dict[str, Any]) -> List[str]:
        """Validate ability score calculations."""
        errors = []
        
        scores = character_data.get("ability_scores", {})
        modifiers = character_data.get("ability_modifiers", {})
        
        # Check each ability
        for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            if ability not in scores:
                errors.append(f"Missing ability score: {ability}")
                continue
            
            score = scores[ability]
            
            # Validate score range
            if score < 1 or score > 30:
                errors.append(f"{ability} score out of range: {score} (expected 1-30)")
            
            # Validate modifier calculation
            if ability in modifiers:
                expected_mod = (score - 10) // 2
                actual_mod = modifiers[ability]
                
                if expected_mod != actual_mod:
                    errors.append(f"{ability} modifier calculation error: "
                                f"score {score} should give {expected_mod}, got {actual_mod}")
        
        # Check for ability score breakdown if available
        breakdown = character_data.get("ability_score_breakdown", {})
        if breakdown:
            for ability, sources in breakdown.items():
                if isinstance(sources, dict):
                    total = sum(sources.values())
                    if total != scores.get(ability, 0):
                        errors.append(f"{ability} breakdown doesn't sum correctly: "
                                    f"{sources} = {total}, expected {scores.get(ability)}")
        
        return errors
    
    def _validate_hit_points(self, character_data: Dict[str, Any]) -> List[str]:
        """Validate hit point calculations."""
        errors = []
        
        max_hp = character_data.get("max_hp", 0)
        level = character_data.get("level", 1)
        con_mod = character_data.get("ability_modifiers", {}).get("constitution", 0)
        
        # Minimum HP check (1 per level minimum)
        if max_hp < level:
            errors.append(f"HP too low: {max_hp} for level {level} (minimum {level})")
        
        # Check against class hit dice if available
        classes = character_data.get("classes", [])
        if classes:
            # Calculate minimum possible HP (all 1s on dice)
            min_possible_hp = 0
            for cls in classes:
                class_name = cls.get("name", "Unknown")
                class_level = cls.get("level", 0)
                hit_die = self.constants.CLASS_HIT_DICE.get(class_name, 8)
                
                # First level gets max hit die
                if min_possible_hp == 0:
                    min_possible_hp += hit_die + con_mod
                    remaining_levels = class_level - 1
                else:
                    remaining_levels = class_level
                
                # Remaining levels get minimum (1) + con mod
                min_possible_hp += remaining_levels * (1 + con_mod)
            
            # Ensure positive HP
            min_possible_hp = max(min_possible_hp, level)
            
            if max_hp < min_possible_hp:
                errors.append(f"HP below minimum possible: {max_hp} "
                            f"(minimum {min_possible_hp} for level {level} with CON mod {con_mod})")
        
        # Check HP breakdown if available
        hp_breakdown = character_data.get("hit_point_breakdown", {})
        if hp_breakdown:
            breakdown_total = (hp_breakdown.get("base_hp", 0) + 
                             hp_breakdown.get("con_bonus", 0) + 
                             hp_breakdown.get("other_bonuses", 0))
            
            if breakdown_total != max_hp:
                errors.append(f"HP breakdown doesn't sum correctly: "
                            f"{hp_breakdown} = {breakdown_total}, expected {max_hp}")
        
        return errors
    
    def _validate_armor_class(self, character_data: Dict[str, Any]) -> List[str]:
        """Validate armor class calculations."""
        errors = []
        
        ac = character_data.get("armor_class", 10)
        
        # Basic range check
        if ac < 10:
            errors.append(f"AC below minimum: {ac} (minimum is 10)")
        elif ac > 30:
            errors.append(f"AC unusually high: {ac} (typical maximum is 30)")
        
        # Check AC breakdown if available
        ac_breakdown = character_data.get("ac_breakdown", {})
        if ac_breakdown:
            # Validate Unarmored Defense calculations
            method = ac_breakdown.get("calculation_method", "")
            
            if "Barbarian" in method:
                # Should be 10 + DEX + CON
                dex_mod = character_data.get("ability_modifiers", {}).get("dexterity", 0)
                con_mod = character_data.get("ability_modifiers", {}).get("constitution", 0)
                expected = 10 + dex_mod + con_mod
                
                if ac < expected:  # Could be higher with shields/magic
                    errors.append(f"Barbarian Unarmored Defense calculation may be wrong: "
                                f"AC {ac} < expected minimum {expected} (10 + {dex_mod} DEX + {con_mod} CON)")
            
            elif "Monk" in method:
                # Should be 10 + DEX + WIS (no shield)
                dex_mod = character_data.get("ability_modifiers", {}).get("dexterity", 0)
                wis_mod = character_data.get("ability_modifiers", {}).get("wisdom", 0)
                expected = 10 + dex_mod + wis_mod
                
                if ac < expected:  # Could be higher with magic
                    errors.append(f"Monk Unarmored Defense calculation may be wrong: "
                                f"AC {ac} < expected minimum {expected} (10 + {dex_mod} DEX + {wis_mod} WIS)")
            
            # Check breakdown sum
            breakdown_total = (ac_breakdown.get("base", 10) + 
                             ac_breakdown.get("dexterity_bonus", 0) +
                             ac_breakdown.get("armor_bonus", 0) +
                             ac_breakdown.get("shield_bonus", 0) +
                             ac_breakdown.get("other_bonuses", 0))
            
            if "breakdown_total" in ac_breakdown and breakdown_total != ac:
                errors.append(f"AC breakdown doesn't sum correctly: "
                            f"{ac_breakdown} = {breakdown_total}, expected {ac}")
        
        return errors
    
    def _validate_spellcasting(self, character_data: Dict[str, Any]) -> List[str]:
        """Validate spellcasting calculations."""
        errors = []
        
        spellcasting = character_data.get("spellcasting", {})
        prof_bonus = character_data.get("proficiency_bonus", 2)
        
        # Get spellcasting ability modifier
        ability = spellcasting.get("spellcasting_ability", "").lower()
        ability_mod = character_data.get("ability_modifiers", {}).get(ability, 0)
        
        # Validate spell save DC
        save_dc = spellcasting.get("spell_save_dc", 0)
        if save_dc > 0:
            expected_dc = 8 + prof_bonus + ability_mod
            if save_dc != expected_dc:
                errors.append(f"Spell save DC calculation error: "
                            f"got {save_dc}, expected {expected_dc} "
                            f"(8 + {prof_bonus} prof + {ability_mod} {ability} mod)")
        
        # Validate spell attack bonus
        attack_bonus = spellcasting.get("spell_attack_bonus")
        if attack_bonus is not None:
            expected_bonus = prof_bonus + ability_mod
            if attack_bonus != expected_bonus:
                errors.append(f"Spell attack bonus calculation error: "
                            f"got {attack_bonus}, expected {expected_bonus} "
                            f"({prof_bonus} prof + {ability_mod} {ability} mod)")
        
        # Validate spell slots
        for level in range(1, 10):
            slot_key = f"spell_slots_level_{level}"
            slots = spellcasting.get(slot_key, 0)
            
            # Basic validation - slots should be non-negative
            if slots < 0:
                errors.append(f"Negative spell slots for level {level}: {slots}")
            
            # High level slots validation
            if level > 5 and slots > 4:
                errors.append(f"Unusually high spell slots for level {level}: {slots}")
        
        # Validate pact slots for Warlocks
        pact_slots = spellcasting.get("pact_slots", 0)
        pact_level = spellcasting.get("pact_slot_level", 0)
        
        if pact_slots > 0:
            if pact_slots > 4:
                errors.append(f"Too many pact slots: {pact_slots} (maximum is 4)")
            if pact_level < 1 or pact_level > 5:
                errors.append(f"Invalid pact slot level: {pact_level} (expected 1-5)")
        
        return errors
    
    def _validate_proficiencies(self, character_data: Dict[str, Any]) -> List[str]:
        """Validate proficiency calculations."""
        errors = []
        
        prof_bonus = character_data.get("proficiency_bonus", 2)
        level = character_data.get("level", 1)
        
        # Validate proficiency bonus
        expected_prof = 2 + ((level - 1) // 4)
        if prof_bonus != expected_prof:
            errors.append(f"Proficiency bonus calculation error: "
                        f"level {level} should give +{expected_prof}, got +{prof_bonus}")
        
        # Validate saving throw proficiencies format
        saving_throws = character_data.get("saving_throw_proficiencies", [])
        valid_abilities = ["Strength", "Dexterity", "Constitution", 
                          "Intelligence", "Wisdom", "Charisma"]
        
        for save in saving_throws:
            if save not in valid_abilities:
                errors.append(f"Invalid saving throw proficiency: {save}")
        
        # Check class-based saving throws
        classes = character_data.get("classes", [])
        if classes and len(saving_throws) == 0:
            errors.append("No saving throw proficiencies listed despite having classes")
        
        return errors
    
    def _cross_validate_with_raw(self, character_data: Dict[str, Any], 
                                 raw_data: Dict[str, Any]) -> List[str]:
        """Cross-validate calculated data with raw D&D Beyond data."""
        warnings = []
        
        # Check if raw data has overrides that might affect calculations
        if raw_data.get("overrideHitPoints"):
            warnings.append("Character has overridden hit points in D&D Beyond")
        
        if raw_data.get("overrideArmorClass"):
            warnings.append("Character has overridden armor class in D&D Beyond")
        
        # Check for temporary effects
        if raw_data.get("temporaryHitPoints", 0) > 0:
            warnings.append(f"Character has {raw_data['temporaryHitPoints']} temporary HP")
        
        # Check for conditions that might affect calculations
        conditions = raw_data.get("conditions", [])
        if conditions:
            warnings.append(f"Character has active conditions: {conditions}")
        
        return warnings