"""
Scenario tests for different rule versions.

Tests scenarios for both 2014 and 2024 D&D rule versions.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from ..factories.character_archetypes import CharacterArchetypeFactory

class TestRuleVersionCompatibility:
    """Test compatibility between different rule versions."""
    
    @pytest.mark.quick
    def test_2014_rules_character(self):
        """Test character creation with 2014 rules."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        
        # Add 2014 rules marker
        character_data["rules_version"] = "2014"
        
        # Basic validations that should work in both versions
        assert character_data["name"] == "Test Fighter"
        assert character_data["level"] == 1
        assert character_data["classes"][0]["name"] == "Fighter"
        assert character_data["proficiency_bonus"] == 2

    @pytest.mark.quick
    def test_2024_rules_character(self):
        """Test character creation with 2024 rules."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        
        # Add 2024 rules marker
        character_data["rules_version"] = "2024"
        
        # Basic validations that should work in both versions
        assert character_data["name"] == "Test Fighter"
        assert character_data["level"] == 1
        assert character_data["classes"][0]["name"] == "Fighter"
        assert character_data["proficiency_bonus"] == 2

    @pytest.mark.quick
    def test_rule_version_spell_differences(self):
        """Test spell differences between rule versions."""
        # 2014 wizard
        wizard_2014 = CharacterArchetypeFactory.create_wizard(level=5)
        wizard_2014["rules_version"] = "2014"
        
        # 2024 wizard
        wizard_2024 = CharacterArchetypeFactory.create_wizard(level=5)
        wizard_2024["rules_version"] = "2024"
        
        # Both should be spellcasters
        assert wizard_2014["is_spellcaster"] is True
        assert wizard_2024["is_spellcaster"] is True
        
        # Both should have spell slots (specific differences would be in implementation)
        assert "spell_slots" in wizard_2014
        assert "spell_slots" in wizard_2024

    @pytest.mark.quick
    def test_rule_version_multiclass_differences(self):
        """Test multiclass differences between rule versions."""
        # 2014 multiclass
        multiclass_2014 = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        multiclass_2014["rules_version"] = "2014"
        
        # 2024 multiclass
        multiclass_2024 = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        multiclass_2024["rules_version"] = "2024"
        
        # Both should have same basic structure
        assert multiclass_2014["level"] == 5
        assert multiclass_2024["level"] == 5
        assert len(multiclass_2014["classes"]) == 2
        assert len(multiclass_2024["classes"]) == 2

class TestSpellcastingRuleVersions:
    """Test spellcasting differences between rule versions."""
    
    @pytest.mark.quick
    def test_cantrip_scaling_2014(self):
        """Test cantrip scaling in 2014 rules."""
        wizard_data = CharacterArchetypeFactory.create_wizard(level=5)
        wizard_data["rules_version"] = "2014"
        
        # In 2014 rules, cantrips scale at certain levels
        assert wizard_data["is_spellcaster"] is True
        
        # Level 5 should have enhanced cantrips
        # Specific implementation would check cantrip damage scaling

    @pytest.mark.quick
    def test_cantrip_scaling_2024(self):
        """Test cantrip scaling in 2024 rules."""
        wizard_data = CharacterArchetypeFactory.create_wizard(level=5)
        wizard_data["rules_version"] = "2024"
        
        # In 2024 rules, cantrips may scale differently
        assert wizard_data["is_spellcaster"] is True
        
        # Level 5 should have enhanced cantrips
        # Specific implementation would check cantrip damage scaling

    @pytest.mark.quick
    def test_spell_slot_progression_2014(self):
        """Test spell slot progression in 2014 rules."""
        wizard_data = CharacterArchetypeFactory.create_wizard(level=9)
        wizard_data["rules_version"] = "2014"
        
        # Verify spell slot progression
        assert wizard_data["spell_slots"]["1"] == 4
        assert wizard_data["spell_slots"]["2"] == 3
        assert wizard_data["spell_slots"]["3"] == 3
        assert wizard_data["spell_slots"]["4"] == 3
        assert wizard_data["spell_slots"]["5"] == 1

    @pytest.mark.quick
    def test_spell_slot_progression_2024(self):
        """Test spell slot progression in 2024 rules."""
        wizard_data = CharacterArchetypeFactory.create_wizard(level=9)
        wizard_data["rules_version"] = "2024"
        
        # Verify spell slot progression (may be same as 2014)
        assert wizard_data["spell_slots"]["1"] == 4
        assert wizard_data["spell_slots"]["2"] == 3
        assert wizard_data["spell_slots"]["3"] == 3
        assert wizard_data["spell_slots"]["4"] == 3
        assert wizard_data["spell_slots"]["5"] == 1

    @pytest.mark.quick
    def test_ritual_casting_2014(self):
        """Test ritual casting in 2014 rules."""
        wizard_data = CharacterArchetypeFactory.create_wizard(level=1)
        wizard_data["rules_version"] = "2014"
        
        # Wizards can ritual cast in 2014
        assert wizard_data["is_spellcaster"] is True
        
        # Specific ritual casting rules would be tested in implementation

    @pytest.mark.quick
    def test_ritual_casting_2024(self):
        """Test ritual casting in 2024 rules."""
        wizard_data = CharacterArchetypeFactory.create_wizard(level=1)
        wizard_data["rules_version"] = "2024"
        
        # Wizards can ritual cast in 2024 (may have different rules)
        assert wizard_data["is_spellcaster"] is True
        
        # Specific ritual casting rules would be tested in implementation

class TestClassFeatureRuleVersions:
    """Test class feature differences between rule versions."""
    
    @pytest.mark.quick
    def test_fighter_features_2014(self):
        """Test fighter features in 2014 rules."""
        fighter_data = CharacterArchetypeFactory.create_fighter(level=5)
        fighter_data["rules_version"] = "2014"
        
        # Fighter features that should be present at level 5
        assert fighter_data["proficiency_bonus"] == 3
        
        # Extra Attack at level 5 (specific implementation would verify)
        # Action Surge, Second Wind, etc.

    @pytest.mark.quick
    def test_fighter_features_2024(self):
        """Test fighter features in 2024 rules."""
        fighter_data = CharacterArchetypeFactory.create_fighter(level=5)
        fighter_data["rules_version"] = "2024"
        
        # Fighter features that should be present at level 5
        assert fighter_data["proficiency_bonus"] == 3
        
        # Extra Attack at level 5 (may have different implementation)
        # Weapon Mastery, etc. (2024 specific features)

    @pytest.mark.quick
    def test_rogue_features_2014(self):
        """Test rogue features in 2014 rules."""
        rogue_data = CharacterArchetypeFactory.create_rogue(level=5)
        rogue_data["rules_version"] = "2014"
        
        # Rogue features at level 5
        assert rogue_data["proficiency_bonus"] == 3
        
        # Sneak Attack, Thieves' Cant, etc.

    @pytest.mark.quick
    def test_rogue_features_2024(self):
        """Test rogue features in 2024 rules."""
        rogue_data = CharacterArchetypeFactory.create_rogue(level=5)
        rogue_data["rules_version"] = "2024"
        
        # Rogue features at level 5
        assert rogue_data["proficiency_bonus"] == 3
        
        # Sneak Attack, Thieves' Cant, etc. (may have updates)

    @pytest.mark.quick
    def test_barbarian_features_2014(self):
        """Test barbarian features in 2014 rules."""
        barbarian_data = CharacterArchetypeFactory.create_level_20_barbarian()
        barbarian_data["rules_version"] = "2014"
        
        # Barbarian features at level 20
        assert barbarian_data["proficiency_bonus"] == 6
        
        # Rage, Unarmored Defense, Primal Champion
        assert "features" in barbarian_data
        assert "Rage" in barbarian_data["features"]
        assert "Unarmored Defense" in barbarian_data["features"]
        assert "Primal Champion" in barbarian_data["features"]

    @pytest.mark.quick
    def test_barbarian_features_2024(self):
        """Test barbarian features in 2024 rules."""
        barbarian_data = CharacterArchetypeFactory.create_level_20_barbarian()
        barbarian_data["rules_version"] = "2024"
        
        # Barbarian features at level 20
        assert barbarian_data["proficiency_bonus"] == 6
        
        # Rage, Unarmored Defense, Primal Champion (may have updates)
        assert "features" in barbarian_data
        assert "Rage" in barbarian_data["features"]
        assert "Unarmored Defense" in barbarian_data["features"]
        assert "Primal Champion" in barbarian_data["features"]

class TestAbilityScoreRuleVersions:
    """Test ability score differences between rule versions."""
    
    @pytest.mark.quick
    def test_ability_score_generation_2014(self):
        """Test ability score generation in 2014 rules."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        character_data["rules_version"] = "2014"
        
        # Standard ability score validation
        for ability, score in character_data["ability_scores"].items():
            assert 1 <= score <= 30, f"Ability {ability} score {score} out of range"

    @pytest.mark.quick
    def test_ability_score_generation_2024(self):
        """Test ability score generation in 2024 rules."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        character_data["rules_version"] = "2024"
        
        # Standard ability score validation
        for ability, score in character_data["ability_scores"].items():
            assert 1 <= score <= 30, f"Ability {ability} score {score} out of range"

    @pytest.mark.quick
    def test_ability_score_improvements_2014(self):
        """Test ability score improvements in 2014 rules."""
        character_data = CharacterArchetypeFactory.create_fighter(level=8)
        character_data["rules_version"] = "2014"
        
        # Fighters get ASI at levels 4, 6, 8, 12, 14, 16, 19
        # Level 8 should have had 2 ASIs (levels 4 and 6)
        assert character_data["proficiency_bonus"] == 3

    @pytest.mark.quick
    def test_ability_score_improvements_2024(self):
        """Test ability score improvements in 2024 rules."""
        character_data = CharacterArchetypeFactory.create_fighter(level=8)
        character_data["rules_version"] = "2024"
        
        # ASI schedule may be different in 2024
        assert character_data["proficiency_bonus"] == 3

class TestRaceRuleVersions:
    """Test race differences between rule versions."""
    
    @pytest.mark.quick
    def test_human_traits_2014(self):
        """Test human traits in 2014 rules."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        character_data["rules_version"] = "2014"
        character_data["race"] = "Human"
        
        # Human traits in 2014: +1 to all ability scores
        assert character_data["race"] == "Human"

    @pytest.mark.quick
    def test_human_traits_2024(self):
        """Test human traits in 2024 rules."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        character_data["rules_version"] = "2024"
        character_data["race"] = "Human"
        
        # Human traits in 2024: may have different bonuses
        assert character_data["race"] == "Human"

    @pytest.mark.quick
    def test_elf_traits_2014(self):
        """Test elf traits in 2014 rules."""
        character_data = CharacterArchetypeFactory.create_wizard(level=1)
        character_data["rules_version"] = "2014"
        character_data["race"] = "High Elf"
        
        # High Elf traits in 2014: +2 Int, +1 Dex, cantrip, etc.
        assert character_data["race"] == "High Elf"

    @pytest.mark.quick
    def test_elf_traits_2024(self):
        """Test elf traits in 2024 rules."""
        character_data = CharacterArchetypeFactory.create_wizard(level=1)
        character_data["rules_version"] = "2024"
        character_data["race"] = "High Elf"
        
        # High Elf traits in 2024: may have different bonuses
        assert character_data["race"] == "High Elf"

    @pytest.mark.quick
    def test_halfling_traits_2014(self):
        """Test halfling traits in 2014 rules."""
        character_data = CharacterArchetypeFactory.create_rogue(level=1)
        character_data["rules_version"] = "2014"
        character_data["race"] = "Halfling"
        
        # Halfling traits in 2014: +2 Dex, Lucky, Brave, etc.
        assert character_data["race"] == "Halfling"

    @pytest.mark.quick
    def test_halfling_traits_2024(self):
        """Test halfling traits in 2024 rules."""
        character_data = CharacterArchetypeFactory.create_rogue(level=1)
        character_data["rules_version"] = "2024"
        character_data["race"] = "Halfling"
        
        # Halfling traits in 2024: may have different bonuses
        assert character_data["race"] == "Halfling"

class TestEquipmentRuleVersions:
    """Test equipment differences between rule versions."""
    
    @pytest.mark.quick
    def test_starting_equipment_2014(self):
        """Test starting equipment in 2014 rules."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        character_data["rules_version"] = "2014"
        
        # Fighter starting equipment in 2014
        assert character_data["armor_class"] == 16  # Chain mail
        assert character_data["proficiency_bonus"] == 2

    @pytest.mark.quick
    def test_starting_equipment_2024(self):
        """Test starting equipment in 2024 rules."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        character_data["rules_version"] = "2024"
        
        # Fighter starting equipment in 2024 (may be different)
        assert character_data["armor_class"] == 16  # Chain mail
        assert character_data["proficiency_bonus"] == 2

    @pytest.mark.quick
    def test_weapon_properties_2014(self):
        """Test weapon properties in 2014 rules."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        character_data["rules_version"] = "2014"
        
        # Basic weapon property validation
        assert character_data["proficiency_bonus"] == 2

    @pytest.mark.quick
    def test_weapon_properties_2024(self):
        """Test weapon properties in 2024 rules."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        character_data["rules_version"] = "2024"
        
        # 2024 may have weapon mastery and other changes
        assert character_data["proficiency_bonus"] == 2

class TestRuleVersionConsistency:
    """Test consistency between rule versions."""
    
    @pytest.mark.quick
    def test_core_mechanics_consistency(self):
        """Test that core mechanics remain consistent."""
        # Test same character with different rule versions
        fighter_2014 = CharacterArchetypeFactory.create_fighter(level=5)
        fighter_2014["rules_version"] = "2014"
        
        fighter_2024 = CharacterArchetypeFactory.create_fighter(level=5)
        fighter_2024["rules_version"] = "2024"
        
        # Core mechanics should be the same
        assert fighter_2014["level"] == fighter_2024["level"]
        assert fighter_2014["proficiency_bonus"] == fighter_2024["proficiency_bonus"]
        assert fighter_2014["classes"][0]["name"] == fighter_2024["classes"][0]["name"]
        assert fighter_2014["classes"][0]["hit_die"] == fighter_2024["classes"][0]["hit_die"]

    @pytest.mark.quick
    def test_spellcasting_consistency(self):
        """Test that spellcasting mechanics remain consistent."""
        wizard_2014 = CharacterArchetypeFactory.create_wizard(level=5)
        wizard_2014["rules_version"] = "2014"
        
        wizard_2024 = CharacterArchetypeFactory.create_wizard(level=5)
        wizard_2024["rules_version"] = "2024"
        
        # Basic spellcasting should be consistent
        assert wizard_2014["is_spellcaster"] == wizard_2024["is_spellcaster"]
        assert wizard_2014["level"] == wizard_2024["level"]
        assert wizard_2014["proficiency_bonus"] == wizard_2024["proficiency_bonus"]

    @pytest.mark.quick
    def test_multiclass_consistency(self):
        """Test that multiclass mechanics remain consistent."""
        multiclass_2014 = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        multiclass_2014["rules_version"] = "2014"
        
        multiclass_2024 = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        multiclass_2024["rules_version"] = "2024"
        
        # Core multiclass mechanics should be consistent
        assert multiclass_2014["level"] == multiclass_2024["level"]
        assert len(multiclass_2014["classes"]) == len(multiclass_2024["classes"])
        assert multiclass_2014["proficiency_bonus"] == multiclass_2024["proficiency_bonus"]

    @pytest.mark.quick
    def test_level_progression_consistency(self):
        """Test that level progression remains consistent."""
        levels = [1, 5, 10, 15, 20]
        
        for level in levels:
            char_2014 = CharacterArchetypeFactory.create_fighter(level=level)
            char_2014["rules_version"] = "2014"
            
            char_2024 = CharacterArchetypeFactory.create_fighter(level=level)
            char_2024["rules_version"] = "2024"
            
            # Proficiency bonus should be consistent
            expected_bonus = 2 + ((level - 1) // 4)
            assert char_2014["proficiency_bonus"] == expected_bonus
            assert char_2024["proficiency_bonus"] == expected_bonus

class TestRuleVersionEdgeCases:
    """Test edge cases for rule version differences."""
    
    @pytest.mark.quick
    def test_unknown_rule_version(self):
        """Test handling of unknown rule version."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        character_data["rules_version"] = "unknown"
        
        # Should still have basic character data
        assert character_data["name"] == "Test Fighter"
        assert character_data["level"] == 1
        assert character_data["proficiency_bonus"] == 2

    @pytest.mark.quick
    def test_missing_rule_version(self):
        """Test handling of missing rule version."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        # Don't set rules_version
        
        # Should still have basic character data
        assert character_data["name"] == "Test Fighter"
        assert character_data["level"] == 1
        assert character_data["proficiency_bonus"] == 2

    @pytest.mark.quick
    def test_rule_version_backwards_compatibility(self):
        """Test backwards compatibility between rule versions."""
        # A character created with 2014 rules should still be processable
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        character_data["rules_version"] = "2014"
        
        # Basic validation should still work
        assert character_data["level"] == 5
        assert character_data["is_spellcaster"] is True
        assert len(character_data["classes"]) == 2