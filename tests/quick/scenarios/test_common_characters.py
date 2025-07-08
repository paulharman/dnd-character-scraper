"""
Scenario tests for common character types.

Tests typical character configurations that developers encounter frequently.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from ..factories.character_archetypes import CharacterArchetypeFactory
from ..factories.scenarios import ScenarioFactory

class TestFighterScenarios:
    """Test scenarios for Fighter characters."""
    
    @pytest.mark.quick
    def test_level_1_fighter(self):
        """Test level 1 fighter scenario."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        
        # Basic validations
        assert character_data["name"] == "Test Fighter"
        assert character_data["level"] == 1
        assert character_data["classes"][0]["name"] == "Fighter"
        assert character_data["classes"][0]["level"] == 1
        assert character_data["classes"][0]["hit_die"] == 10
        
        # Fighter-specific validations
        assert character_data["is_spellcaster"] is False
        assert character_data["proficiency_bonus"] == 2
        assert character_data["armor_class"] == 16  # Chain mail
        assert character_data["hit_points"] >= 10  # d10 + con mod

    @pytest.mark.quick
    def test_level_5_fighter(self):
        """Test level 5 fighter scenario."""
        character_data = CharacterArchetypeFactory.create_fighter(level=5)
        
        # Level progression validations
        assert character_data["level"] == 5
        assert character_data["proficiency_bonus"] == 3
        assert character_data["hit_points"] >= 30  # Reasonable HP for level 5
        
        # Fighter gets Extra Attack at level 5
        # This would be verified in actual implementation

    @pytest.mark.quick
    def test_level_11_fighter(self):
        """Test level 11 fighter scenario."""
        character_data = CharacterArchetypeFactory.create_fighter(level=11)
        
        # High level validations
        assert character_data["level"] == 11
        assert character_data["proficiency_bonus"] == 4
        assert character_data["hit_points"] >= 70  # Reasonable HP for level 11

    @pytest.mark.quick
    def test_level_20_fighter(self):
        """Test level 20 fighter scenario."""
        character_data = CharacterArchetypeFactory.create_fighter(level=20)
        
        # Maximum level validations
        assert character_data["level"] == 20
        assert character_data["proficiency_bonus"] == 6
        assert character_data["hit_points"] >= 100  # Reasonable HP for level 20

class TestWizardScenarios:
    """Test scenarios for Wizard characters."""
    
    @pytest.mark.quick
    def test_level_1_wizard(self):
        """Test level 1 wizard scenario."""
        character_data = CharacterArchetypeFactory.create_wizard(level=1)
        
        # Basic validations
        assert character_data["name"] == "Test Wizard"
        assert character_data["level"] == 1
        assert character_data["classes"][0]["name"] == "Wizard"
        assert character_data["classes"][0]["hit_die"] == 6
        
        # Wizard-specific validations
        assert character_data["is_spellcaster"] is True
        assert character_data["proficiency_bonus"] == 2
        assert character_data["armor_class"] == 12  # Mage armor
        assert character_data["hit_points"] >= 6  # d6 + con mod
        assert "spell_slots" in character_data
        assert character_data["spell_slots"]["1"] >= 2  # Level 1 has 2 spell slots

    @pytest.mark.quick
    def test_level_3_wizard(self):
        """Test level 3 wizard scenario."""
        character_data = CharacterArchetypeFactory.create_wizard(level=3)
        
        # Level progression validations
        assert character_data["level"] == 3
        assert character_data["proficiency_bonus"] == 2
        assert character_data["spell_slots"]["1"] == 4  # 4 first level slots
        assert character_data["spell_slots"]["2"] == 2  # 2 second level slots
        
        # Wizard gets subclass at level 2
        if character_data["classes"][0].get("subclass"):
            assert character_data["classes"][0]["subclass"] == "School of Evocation"

    @pytest.mark.quick
    def test_level_9_wizard(self):
        """Test level 9 wizard scenario."""
        character_data = CharacterArchetypeFactory.create_wizard(level=9)
        
        # High level spell slots
        assert character_data["level"] == 9
        assert character_data["proficiency_bonus"] == 4
        assert character_data["spell_slots"]["1"] == 4
        assert character_data["spell_slots"]["2"] == 3
        assert character_data["spell_slots"]["3"] == 3
        assert character_data["spell_slots"]["4"] == 3
        assert character_data["spell_slots"]["5"] == 1  # 5th level slots at level 9

    @pytest.mark.quick
    def test_level_20_wizard(self):
        """Test level 20 wizard scenario."""
        character_data = CharacterArchetypeFactory.create_wizard(level=20)
        
        # Maximum level validations
        assert character_data["level"] == 20
        assert character_data["proficiency_bonus"] == 6
        assert character_data["hit_points"] >= 60  # Reasonable HP for level 20 wizard
        
        # High level spell slots
        assert character_data["spell_slots"]["9"] >= 1  # 9th level slots

class TestRogueScenarios:
    """Test scenarios for Rogue characters."""
    
    @pytest.mark.quick
    def test_level_1_rogue(self):
        """Test level 1 rogue scenario."""
        character_data = CharacterArchetypeFactory.create_rogue(level=1)
        
        # Basic validations
        assert character_data["name"] == "Test Rogue"
        assert character_data["level"] == 1
        assert character_data["classes"][0]["name"] == "Rogue"
        assert character_data["classes"][0]["hit_die"] == 8
        
        # Rogue-specific validations
        assert character_data["is_spellcaster"] is False
        assert character_data["proficiency_bonus"] == 2
        assert character_data["armor_class"] == 13  # Leather armor + dex
        assert character_data["hit_points"] >= 8  # d8 + con mod

    @pytest.mark.quick
    def test_level_3_rogue(self):
        """Test level 3 rogue scenario."""
        character_data = CharacterArchetypeFactory.create_rogue(level=3)
        
        # Level progression validations
        assert character_data["level"] == 3
        assert character_data["proficiency_bonus"] == 2
        
        # Rogue gets subclass at level 3
        if character_data["classes"][0].get("subclass"):
            assert character_data["classes"][0]["subclass"] == "Thief"

    @pytest.mark.quick
    def test_level_5_rogue(self):
        """Test level 5 rogue scenario."""
        character_data = CharacterArchetypeFactory.create_rogue(level=5)
        
        # Level progression validations
        assert character_data["level"] == 5
        assert character_data["proficiency_bonus"] == 3
        assert character_data["hit_points"] >= 25  # Reasonable HP for level 5

    @pytest.mark.quick
    def test_level_20_rogue(self):
        """Test level 20 rogue scenario."""
        character_data = CharacterArchetypeFactory.create_rogue(level=20)
        
        # Maximum level validations
        assert character_data["level"] == 20
        assert character_data["proficiency_bonus"] == 6
        assert character_data["hit_points"] >= 80  # Reasonable HP for level 20 rogue

class TestMulticlassScenarios:
    """Test scenarios for multiclass characters."""
    
    @pytest.mark.quick
    def test_fighter_wizard_multiclass(self):
        """Test Fighter/Wizard multiclass scenario."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        
        # Multiclass validations
        assert character_data["level"] == 5
        assert len(character_data["classes"]) == 2
        
        # Verify both classes
        class_names = [cls["name"] for cls in character_data["classes"]]
        assert "Fighter" in class_names
        assert "Wizard" in class_names
        
        # Verify class levels
        fighter_class = next(cls for cls in character_data["classes"] if cls["name"] == "Fighter")
        wizard_class = next(cls for cls in character_data["classes"] if cls["name"] == "Wizard")
        
        assert fighter_class["level"] == 3
        assert wizard_class["level"] == 2
        
        # Spellcasting from wizard
        assert character_data["is_spellcaster"] is True
        assert "spell_slots" in character_data
        assert character_data["spell_slots"]["1"] >= 2  # Wizard spell slots

    @pytest.mark.quick
    def test_even_multiclass_split(self):
        """Test even multiclass split scenario."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(2, 3)
        
        # Verify total level
        assert character_data["level"] == 5
        
        # Verify class levels
        fighter_class = next(cls for cls in character_data["classes"] if cls["name"] == "Fighter")
        wizard_class = next(cls for cls in character_data["classes"] if cls["name"] == "Wizard")
        
        assert fighter_class["level"] == 2
        assert wizard_class["level"] == 3
        
        # Wizard is higher level, so more spell slots
        assert character_data["spell_slots"]["1"] >= 4
        assert character_data["spell_slots"]["2"] >= 2

    @pytest.mark.quick
    def test_high_level_multiclass(self):
        """Test high level multiclass scenario."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(10, 10)
        
        # High level multiclass validations
        assert character_data["level"] == 20
        assert character_data["proficiency_bonus"] == 6
        
        # Both classes at significant levels
        fighter_class = next(cls for cls in character_data["classes"] if cls["name"] == "Fighter")
        wizard_class = next(cls for cls in character_data["classes"] if cls["name"] == "Wizard")
        
        assert fighter_class["level"] == 10
        assert wizard_class["level"] == 10
        
        # High level spell slots
        assert character_data["spell_slots"]["5"] >= 1  # 5th level slots

class TestBarbarianScenarios:
    """Test scenarios for Barbarian characters."""
    
    @pytest.mark.quick
    def test_level_20_barbarian(self):
        """Test level 20 barbarian scenario."""
        character_data = CharacterArchetypeFactory.create_level_20_barbarian()
        
        # Maximum level validations
        assert character_data["name"] == "Test Barbarian Max Level"
        assert character_data["level"] == 20
        assert character_data["classes"][0]["name"] == "Barbarian"
        assert character_data["classes"][0]["hit_die"] == 12
        assert character_data["classes"][0]["subclass"] == "Path of the Berserker"
        
        # Barbarian-specific validations
        assert character_data["is_spellcaster"] is False
        assert character_data["proficiency_bonus"] == 6
        assert character_data["race"] == "Half-Orc"
        assert character_data["background"] == "Outlander"
        
        # High level stats
        assert character_data["ability_scores"]["strength"] == 24
        assert character_data["ability_scores"]["constitution"] == 20
        assert character_data["armor_class"] == 17  # Unarmored defense
        assert character_data["hit_points"] == 285  # Max HP
        
        # Barbarian features
        assert "features" in character_data
        assert "Rage" in character_data["features"]
        assert "Unarmored Defense" in character_data["features"]
        assert "Primal Champion" in character_data["features"]

class TestCharacterProgression:
    """Test character progression scenarios."""
    
    @pytest.mark.quick
    def test_proficiency_bonus_progression(self):
        """Test proficiency bonus progression."""
        test_levels = [1, 4, 5, 8, 9, 12, 13, 16, 17, 20]
        expected_bonuses = [2, 2, 3, 3, 4, 4, 5, 5, 6, 6]
        
        for level, expected_bonus in zip(test_levels, expected_bonuses):
            character_data = CharacterArchetypeFactory.create_fighter(level=level)
            assert character_data["proficiency_bonus"] == expected_bonus

    @pytest.mark.quick
    def test_hit_point_progression(self):
        """Test hit point progression."""
        levels = [1, 5, 10, 15, 20]
        
        for level in levels:
            character_data = CharacterArchetypeFactory.create_fighter(level=level)
            
            # HP should increase with level
            min_hp = 10 + (level - 1) * 1  # Minimum possible HP
            max_hp = 10 + (level - 1) * 10  # Maximum possible HP
            
            assert min_hp <= character_data["hit_points"] <= max_hp

    @pytest.mark.quick
    def test_spell_slot_progression(self):
        """Test spell slot progression for wizards."""
        levels = [1, 3, 5, 9, 17, 20]
        
        for level in levels:
            character_data = CharacterArchetypeFactory.create_wizard(level=level)
            
            # Should have spell slots appropriate for level
            assert character_data["is_spellcaster"] is True
            assert "spell_slots" in character_data
            assert character_data["spell_slots"]["1"] >= 2  # Always at least 2 first level slots
            
            # Higher levels should have more spell slots
            if level >= 3:
                assert character_data["spell_slots"]["2"] >= 1
            if level >= 5:
                assert character_data["spell_slots"]["3"] >= 1

class TestEdgeCaseScenarios:
    """Test edge case scenarios."""
    
    @pytest.mark.quick
    def test_minimum_level_character(self):
        """Test minimum level character scenario."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        
        # Level 1 validations
        assert character_data["level"] == 1
        assert character_data["proficiency_bonus"] == 2
        assert character_data["classes"][0]["level"] == 1
        assert character_data["hit_points"] >= 1  # HP never goes below 1

    @pytest.mark.quick
    def test_maximum_level_character(self):
        """Test maximum level character scenario."""
        character_data = CharacterArchetypeFactory.create_fighter(level=20)
        
        # Level 20 validations
        assert character_data["level"] == 20
        assert character_data["proficiency_bonus"] == 6
        assert character_data["classes"][0]["level"] == 20
        assert character_data["hit_points"] >= 100  # Reasonable HP for level 20

    @pytest.mark.quick
    def test_mid_level_character(self):
        """Test mid-level character scenario."""
        character_data = CharacterArchetypeFactory.create_wizard(level=10)
        
        # Level 10 validations
        assert character_data["level"] == 10
        assert character_data["proficiency_bonus"] == 4
        assert character_data["spell_slots"]["5"] >= 1  # 5th level slots at level 10

class TestScenarioFactoryIntegration:
    """Test scenario factory integration."""
    
    @pytest.mark.quick
    def test_new_character_scenario(self):
        """Test new character scenario from factory."""
        scenario = ScenarioFactory.create_new_character_scenario()
        
        # Scenario structure validations
        assert scenario["name"] == "New Character Creation"
        assert "character_data" in scenario
        assert "api_response" in scenario
        assert "expected_outcomes" in scenario
        
        # Character data validations
        character_data = scenario["character_data"]
        assert character_data["name"] == "Test Fighter"
        assert character_data["level"] == 1
        
        # Expected outcomes validations
        expected = scenario["expected_outcomes"]
        assert expected["ac_calculation"] == 16
        assert expected["hp_calculation"] == 12
        assert expected["proficiency_bonus"] == 2
        assert expected["has_spells"] is False

    @pytest.mark.quick
    def test_spellcaster_scenario(self):
        """Test spellcaster scenario from factory."""
        scenario = ScenarioFactory.create_spellcaster_scenario()
        
        # Scenario structure validations
        assert scenario["name"] == "Spellcaster Functionality"
        assert "character_data" in scenario
        assert "expected_outcomes" in scenario
        
        # Character data validations
        character_data = scenario["character_data"]
        assert character_data["name"] == "Test Wizard"
        assert character_data["level"] == 3
        assert character_data["is_spellcaster"] is True
        
        # Expected outcomes validations
        expected = scenario["expected_outcomes"]
        assert expected["has_spells"] is True
        assert expected["spell_slots"]["1"] == 4
        assert expected["spell_slots"]["2"] == 2

    @pytest.mark.quick
    def test_multiclass_scenario(self):
        """Test multiclass scenario from factory."""
        scenario = ScenarioFactory.create_multiclass_scenario()
        
        # Scenario structure validations
        assert scenario["name"] == "Multiclass Character"
        assert "character_data" in scenario
        assert "expected_outcomes" in scenario
        
        # Character data validations
        character_data = scenario["character_data"]
        assert character_data["level"] == 5
        assert len(character_data["classes"]) == 2
        
        # Expected outcomes validations
        expected = scenario["expected_outcomes"]
        assert expected["total_level"] == 5
        assert expected["has_spells"] is True
        assert expected["spell_slots"]["1"] == 3

    @pytest.mark.quick
    def test_all_scenario_types(self):
        """Test all scenario types from factory."""
        scenario_names = ScenarioFactory.get_all_scenarios()
        
        for scenario_name in scenario_names:
            scenario = ScenarioFactory.get_scenario_by_name(scenario_name)
            
            # Basic scenario structure
            assert "name" in scenario
            assert scenario["name"] is not None
            assert "expected_outcomes" in scenario
            
            # Some scenarios have character data, others don't (error scenarios)
            if "character_data" in scenario and scenario["character_data"]:
                character_data = scenario["character_data"]
                assert "name" in character_data
                assert "level" in character_data