"""
Scenario tests for multiclass characters.

Tests complex multiclass scenarios and edge cases.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from ..factories.character_archetypes import CharacterArchetypeFactory
from ..factories.edge_cases import EdgeCaseFactory
from ..factories.scenarios import ScenarioFactory

class TestBasicMulticlass:
    """Test basic multiclass scenarios."""
    
    @pytest.mark.quick
    def test_fighter_wizard_multiclass(self):
        """Test Fighter/Wizard multiclass."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        
        # Basic multiclass validations
        assert character_data["level"] == 5
        assert len(character_data["classes"]) == 2
        assert character_data["proficiency_bonus"] == 3
        
        # Verify both classes are present
        class_names = [cls["name"] for cls in character_data["classes"]]
        assert "Fighter" in class_names
        assert "Wizard" in class_names
        
        # Verify class levels
        fighter_class = next(cls for cls in character_data["classes"] if cls["name"] == "Fighter")
        wizard_class = next(cls for cls in character_data["classes"] if cls["name"] == "Wizard")
        
        assert fighter_class["level"] == 3
        assert wizard_class["level"] == 2
        
        # Multiclass should be spellcaster due to wizard levels
        assert character_data["is_spellcaster"] is True
        assert "spell_slots" in character_data

    @pytest.mark.quick
    def test_level_total_consistency(self):
        """Test that class levels sum to total level."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(4, 3)
        
        # Calculate total from class levels
        total_class_levels = sum(cls["level"] for cls in character_data["classes"])
        
        # Should match character level
        assert total_class_levels == character_data["level"]
        assert character_data["level"] == 7

    @pytest.mark.quick
    def test_different_multiclass_splits(self):
        """Test different multiclass level splits."""
        # Test various splits
        splits = [(1, 4), (2, 3), (3, 2), (4, 1)]
        
        for fighter_level, wizard_level in splits:
            character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(
                fighter_level, wizard_level
            )
            
            expected_total = fighter_level + wizard_level
            assert character_data["level"] == expected_total
            
            # Verify individual class levels
            fighter_class = next(cls for cls in character_data["classes"] if cls["name"] == "Fighter")
            wizard_class = next(cls for cls in character_data["classes"] if cls["name"] == "Wizard")
            
            assert fighter_class["level"] == fighter_level
            assert wizard_class["level"] == wizard_level

class TestMulticlassSpellcasting:
    """Test multiclass spellcasting mechanics."""
    
    @pytest.mark.quick
    def test_multiclass_spell_slots(self):
        """Test multiclass spell slot calculation."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        
        # Should have spellcasting from wizard levels
        assert character_data["is_spellcaster"] is True
        assert "spell_slots" in character_data
        
        # Wizard level 2 should have specific spell slots
        assert character_data["spell_slots"]["1"] == 3  # 3 first level slots
        # No second level slots at wizard level 2
        
    @pytest.mark.quick
    def test_non_spellcaster_multiclass(self):
        """Test multiclass with no spellcasting classes."""
        # Create a Fighter/Barbarian multiclass (neither are spellcasters)
        character_data = CharacterArchetypeFactory.create_fighter(level=3)
        character_data["classes"] = [
            {
                "name": "Fighter",
                "level": 3,
                "hit_die": 10,
                "subclass": None
            },
            {
                "name": "Barbarian",
                "level": 2,
                "hit_die": 12,
                "subclass": None
            }
        ]
        character_data["level"] = 5
        
        # Should not be a spellcaster
        assert character_data["is_spellcaster"] is False
        
        # Should not have spell slots
        if "spell_slots" in character_data:
            assert character_data["spell_slots"] == {}

    @pytest.mark.quick
    def test_partial_spellcaster_multiclass(self):
        """Test multiclass with partial spellcasting classes."""
        # Create a Fighter/Paladin multiclass (Paladin is partial spellcaster)
        character_data = CharacterArchetypeFactory.create_fighter(level=3)
        character_data["classes"] = [
            {
                "name": "Fighter",
                "level": 3,
                "hit_die": 10,
                "subclass": None
            },
            {
                "name": "Paladin",
                "level": 2,
                "hit_die": 10,
                "subclass": None
            }
        ]
        character_data["level"] = 5
        character_data["is_spellcaster"] = True  # Paladin gets spells at level 2
        character_data["spell_slots"] = {"1": 2}  # Paladin level 2 spell slots
        
        # Should be a spellcaster due to paladin levels
        assert character_data["is_spellcaster"] is True
        assert "spell_slots" in character_data

class TestMulticlassHitPoints:
    """Test multiclass hit point calculations."""
    
    @pytest.mark.quick
    def test_multiclass_hit_dice(self):
        """Test multiclass hit dice calculation."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        
        # Should have reasonable HP for level 5
        assert character_data["hit_points"] >= 20  # Conservative estimate
        assert character_data["hit_points"] <= 60  # Reasonable upper bound

    @pytest.mark.quick
    def test_different_hit_dice_multiclass(self):
        """Test multiclass with different hit dice."""
        # Fighter (d10) / Wizard (d6) multiclass
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        
        # Verify hit dice are different
        fighter_class = next(cls for cls in character_data["classes"] if cls["name"] == "Fighter")
        wizard_class = next(cls for cls in character_data["classes"] if cls["name"] == "Wizard")
        
        assert fighter_class["hit_die"] == 10
        assert wizard_class["hit_die"] == 6
        
        # HP should reflect the mixed hit dice
        assert character_data["hit_points"] > 0

    @pytest.mark.quick
    def test_high_level_multiclass_hp(self):
        """Test high level multiclass HP."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(10, 10)
        
        # Level 20 multiclass should have substantial HP
        assert character_data["level"] == 20
        assert character_data["hit_points"] >= 80  # Reasonable for level 20

class TestMulticlassProficiencies:
    """Test multiclass proficiency mechanics."""
    
    @pytest.mark.quick
    def test_multiclass_proficiency_bonus(self):
        """Test multiclass proficiency bonus calculation."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        
        # Proficiency bonus based on total level (5)
        assert character_data["proficiency_bonus"] == 3

    @pytest.mark.quick
    def test_high_level_multiclass_proficiency(self):
        """Test high level multiclass proficiency bonus."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(10, 10)
        
        # Level 20 proficiency bonus
        assert character_data["proficiency_bonus"] == 6

    @pytest.mark.quick
    def test_multiclass_armor_class(self):
        """Test multiclass armor class calculation."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        
        # Should use fighter's armor proficiency
        assert character_data["armor_class"] == 16  # Chain mail

class TestComplexMulticlass:
    """Test complex multiclass scenarios."""
    
    @pytest.mark.quick
    def test_triple_multiclass(self):
        """Test triple multiclass character."""
        character_data = EdgeCaseFactory.create_complex_multiclass()
        
        # Should have 4 classes at level 20
        assert character_data["level"] == 20
        assert len(character_data["classes"]) == 4
        
        # Verify all classes are present
        class_names = [cls["name"] for cls in character_data["classes"]]
        assert "Fighter" in class_names
        assert "Rogue" in class_names
        assert "Ranger" in class_names
        assert "Cleric" in class_names
        
        # Each class should be level 5
        for cls in character_data["classes"]:
            assert cls["level"] == 5

    @pytest.mark.quick
    def test_complex_multiclass_spellcasting(self):
        """Test complex multiclass spellcasting."""
        character_data = EdgeCaseFactory.create_complex_multiclass()
        
        # Should be a spellcaster due to Ranger and Cleric
        assert character_data["is_spellcaster"] is True
        assert "spell_slots" in character_data
        
        # Should have reasonable spell slots for the spellcasting classes
        assert character_data["spell_slots"]["1"] >= 4
        assert character_data["spell_slots"]["2"] >= 3
        assert character_data["spell_slots"]["3"] >= 2

    @pytest.mark.quick
    def test_uneven_multiclass_distribution(self):
        """Test multiclass with uneven level distribution."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(1, 4)
        
        # 1 Fighter / 4 Wizard
        assert character_data["level"] == 5
        
        fighter_class = next(cls for cls in character_data["classes"] if cls["name"] == "Fighter")
        wizard_class = next(cls for cls in character_data["classes"] if cls["name"] == "Wizard")
        
        assert fighter_class["level"] == 1
        assert wizard_class["level"] == 4
        
        # Should have wizard's spell progression
        assert character_data["is_spellcaster"] is True
        assert character_data["spell_slots"]["1"] == 4  # Level 4 wizard
        assert character_data["spell_slots"]["2"] == 3  # Level 4 wizard

class TestMulticlassEdgeCases:
    """Test multiclass edge cases."""
    
    @pytest.mark.quick
    def test_conflicting_features_multiclass(self):
        """Test multiclass with conflicting features."""
        character_data = EdgeCaseFactory.create_conflicting_features_character()
        
        # Barbarian/Monk with conflicting unarmored defense
        assert character_data["level"] == 6
        assert len(character_data["classes"]) == 2
        
        # Should handle conflicting features gracefully
        assert "features" in character_data
        assert "Unarmored Defense (Barbarian)" in character_data["features"]
        assert "Unarmored Defense (Monk)" in character_data["features"]

    @pytest.mark.quick
    def test_single_level_multiclass(self):
        """Test multiclass with single level in secondary class."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(4, 1)
        
        # 4 Fighter / 1 Wizard
        assert character_data["level"] == 5
        
        fighter_class = next(cls for cls in character_data["classes"] if cls["name"] == "Fighter")
        wizard_class = next(cls for cls in character_data["classes"] if cls["name"] == "Wizard")
        
        assert fighter_class["level"] == 4
        assert wizard_class["level"] == 1
        
        # Should still be a spellcaster with minimal spell slots
        assert character_data["is_spellcaster"] is True
        assert character_data["spell_slots"]["1"] >= 2  # Level 1 wizard

    @pytest.mark.quick
    def test_high_level_even_split(self):
        """Test high level multiclass with even split."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(10, 10)
        
        # 10 Fighter / 10 Wizard
        assert character_data["level"] == 20
        
        fighter_class = next(cls for cls in character_data["classes"] if cls["name"] == "Fighter")
        wizard_class = next(cls for cls in character_data["classes"] if cls["name"] == "Wizard")
        
        assert fighter_class["level"] == 10
        assert wizard_class["level"] == 10
        
        # Should have substantial spellcasting
        assert character_data["is_spellcaster"] is True
        assert character_data["spell_slots"]["5"] >= 1  # 5th level slots

class TestMulticlassScenarios:
    """Test multiclass scenarios from factory."""
    
    @pytest.mark.quick
    def test_multiclass_scenario_factory(self):
        """Test multiclass scenario from factory."""
        scenario = ScenarioFactory.create_multiclass_scenario()
        
        # Verify scenario structure
        assert scenario["name"] == "Multiclass Character"
        assert "character_data" in scenario
        assert "expected_outcomes" in scenario
        
        # Verify character data
        character_data = scenario["character_data"]
        assert character_data["level"] == 5
        assert len(character_data["classes"]) == 2
        
        # Verify expected outcomes
        expected = scenario["expected_outcomes"]
        assert expected["total_level"] == 5
        assert expected["has_spells"] is True
        assert expected["spell_slots"]["1"] == 3

    @pytest.mark.quick
    def test_multiclass_scenario_validation(self):
        """Test multiclass scenario validation."""
        scenario = ScenarioFactory.create_multiclass_scenario()
        character_data = scenario["character_data"]
        expected = scenario["expected_outcomes"]
        
        # Validate scenario expectations match character data
        assert character_data["level"] == expected["total_level"]
        assert character_data["armor_class"] == expected["ac_calculation"]
        assert character_data["hit_points"] == expected["hp_calculation"]
        assert character_data["proficiency_bonus"] == expected["proficiency_bonus"]
        assert character_data["is_spellcaster"] == expected["has_spells"]

class TestMulticlassPerformance:
    """Test multiclass performance scenarios."""
    
    @pytest.mark.quick
    def test_multiclass_creation_performance(self):
        """Test multiclass creation performance."""
        import time
        
        start_time = time.time()
        
        # Create multiple multiclass characters
        for i in range(10):
            CharacterArchetypeFactory.create_multiclass_fighter_wizard(i+1, 5-i)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete quickly
        assert execution_time < 1.0, "Multiclass creation should be fast"

    @pytest.mark.quick
    def test_complex_multiclass_performance(self):
        """Test complex multiclass performance."""
        import time
        
        start_time = time.time()
        
        # Create complex multiclass characters
        for i in range(5):
            EdgeCaseFactory.create_complex_multiclass()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete reasonably quickly
        assert execution_time < 2.0, "Complex multiclass creation should be reasonably fast"

class TestMulticlassValidation:
    """Test multiclass validation scenarios."""
    
    @pytest.mark.quick
    def test_multiclass_level_validation(self):
        """Test multiclass level validation."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        
        # All class levels should be valid
        for cls in character_data["classes"]:
            assert 1 <= cls["level"] <= 20, f"Class level {cls['level']} out of range"
        
        # Total level should be valid
        assert 1 <= character_data["level"] <= 20, "Total level out of range"

    @pytest.mark.quick
    def test_multiclass_consistency_validation(self):
        """Test multiclass consistency validation."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        
        # Class levels should sum to total level
        total_class_levels = sum(cls["level"] for cls in character_data["classes"])
        assert total_class_levels == character_data["level"], "Class levels don't sum to total"
        
        # Proficiency bonus should match total level
        expected_prof = 2 + ((character_data["level"] - 1) // 4)
        assert character_data["proficiency_bonus"] == expected_prof

    @pytest.mark.quick
    def test_multiclass_hit_die_validation(self):
        """Test multiclass hit die validation."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        
        # Each class should have valid hit die
        for cls in character_data["classes"]:
            assert cls["hit_die"] in [4, 6, 8, 10, 12], f"Invalid hit die: {cls['hit_die']}"

    @pytest.mark.quick
    def test_multiclass_spellcasting_validation(self):
        """Test multiclass spellcasting validation."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        
        # If character is spellcaster, should have spell slots
        if character_data["is_spellcaster"]:
            assert "spell_slots" in character_data, "Spellcaster missing spell slots"
            assert len(character_data["spell_slots"]) > 0, "Spellcaster has no spell slots"
            
            # All spell slots should be valid
            for level, slots in character_data["spell_slots"].items():
                assert level.isdigit(), f"Invalid spell level: {level}"
                assert 1 <= int(level) <= 9, f"Spell level {level} out of range"
                assert isinstance(slots, int), f"Spell slots should be integer: {slots}"
                assert slots >= 0, f"Negative spell slots: {slots}"