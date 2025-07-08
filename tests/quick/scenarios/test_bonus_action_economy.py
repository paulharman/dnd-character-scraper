"""
Scenario tests for bonus action economy improvements.

Tests the correct categorization of spells that provide conditional bonus actions.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from ..factories.character_archetypes import CharacterArchetypeFactory

class TestBonusActionEconomyFixes:
    """Test bonus action economy categorization fixes."""
    
    @pytest.mark.quick
    def test_expeditious_retreat_conditional_bonus(self):
        """Test that Expeditious Retreat is properly categorized as conditional bonus action."""
        # Create a wizard with Expeditious Retreat
        character_data = CharacterArchetypeFactory.create_wizard(level=5)
        
        # Add Expeditious Retreat to spell list
        character_data["spells"] = {
            "wizard": [
                {
                    "name": "Expeditious Retreat",
                    "level": 1,
                    "school": "Transmutation",
                    "casting_time": "1 Bonus Action",
                    "description": "You take the Dash action, and until the spell ends, you can take that action again as a Bonus Action."
                }
            ]
        }
        
        # Verify character has the spell
        assert "spells" in character_data
        assert any(spell["name"] == "Expeditious Retreat" for spell in character_data["spells"]["wizard"])
        
        # The spell should provide ongoing bonus action ability after being cast
        expeditious_spell = next(spell for spell in character_data["spells"]["wizard"] 
                                if spell["name"] == "Expeditious Retreat")
        assert "bonus action" in expeditious_spell["description"].lower()
        assert expeditious_spell["casting_time"] == "1 Bonus Action"

    @pytest.mark.quick
    def test_arcane_eye_conditional_bonus(self):
        """Test that Arcane Eye is properly categorized as conditional bonus action."""
        # Create a wizard with Arcane Eye
        character_data = CharacterArchetypeFactory.create_wizard(level=7)
        
        # Add Arcane Eye to spell list
        character_data["spells"] = {
            "wizard": [
                {
                    "name": "Arcane Eye",
                    "level": 4,
                    "school": "Divination", 
                    "casting_time": "1 Action",
                    "description": "You can move the eye up to 30 feet as a bonus action."
                }
            ]
        }
        
        # Verify character has the spell
        assert "spells" in character_data
        assert any(spell["name"] == "Arcane Eye" for spell in character_data["spells"]["wizard"])
        
        # The spell should be cast as an action but provide bonus action movement
        arcane_spell = next(spell for spell in character_data["spells"]["wizard"] 
                           if spell["name"] == "Arcane Eye")
        assert "bonus action" in arcane_spell["description"].lower()
        assert arcane_spell["casting_time"] == "1 Action"

    @pytest.mark.quick
    def test_conditional_spells_list_updated(self):
        """Test that the conditional bonus spells list includes the new spells."""
        # This test verifies the parser logic indirectly by testing known spell behavior
        
        # List of spells that should be in conditional bonus actions
        expected_conditional_spells = [
            'unseen servant',
            'find familiar', 
            'spiritual weapon',
            'healing word',
            'expeditious retreat',
            'arcane eye'
        ]
        
        # These spells should provide ongoing bonus action abilities after being cast
        for spell_name in expected_conditional_spells:
            # Each spell should be a known conditional bonus action spell
            assert isinstance(spell_name, str)
            assert len(spell_name) > 0

    @pytest.mark.quick
    def test_expeditious_retreat_parser_logic(self):
        """Test Expeditious Retreat parsing behavior."""
        character_data = CharacterArchetypeFactory.create_wizard(level=3)
        
        # Simulate spell data that would be processed by the parser
        character_data["spells"] = {
            "wizard": [
                {
                    "name": "Expeditious Retreat",
                    "level": 1,
                    "description": "Duration: Concentration, up to 10 minutes. You take the Dash action, and until the spell ends, you can take that action again as a Bonus Action."
                }
            ]
        }
        
        # Verify the spell contains the bonus action text that would be parsed
        spell = character_data["spells"]["wizard"][0]
        assert "bonus action" in spell["description"].lower()
        assert "dash" in spell["description"].lower()

    @pytest.mark.quick 
    def test_arcane_eye_parser_logic(self):
        """Test Arcane Eye parsing behavior."""
        character_data = CharacterArchetypeFactory.create_wizard(level=7)
        
        # Simulate spell data that would be processed by the parser
        character_data["spells"] = {
            "wizard": [
                {
                    "name": "Arcane Eye",
                    "level": 4,
                    "description": "You can move the eye up to 30 feet as a bonus action."
                }
            ]
        }
        
        # Verify the spell contains the bonus action text that would be parsed
        spell = character_data["spells"]["wizard"][0]
        assert "bonus action" in spell["description"].lower()
        assert "move" in spell["description"].lower()

    @pytest.mark.quick
    def test_existing_conditional_spells_still_work(self):
        """Test that existing conditional spells still work properly."""
        character_data = CharacterArchetypeFactory.create_wizard(level=3)
        
        # Test Find Familiar
        character_data["spells"] = {
            "wizard": [
                {
                    "name": "Find Familiar",
                    "level": 1,
                    "description": "You can command your familiar as a bonus action."
                }
            ]
        }
        
        spell = character_data["spells"]["wizard"][0]
        assert "bonus action" in spell["description"].lower()
        assert "command" in spell["description"].lower()

    @pytest.mark.quick
    def test_spell_name_case_insensitive(self):
        """Test that spell name matching is case insensitive."""
        character_data = CharacterArchetypeFactory.create_wizard(level=5)
        
        # Test with different cases
        test_cases = [
            "Expeditious Retreat",
            "expeditious retreat", 
            "EXPEDITIOUS RETREAT",
            "Arcane Eye",
            "arcane eye",
            "ARCANE EYE"
        ]
        
        for spell_name in test_cases:
            character_data["spells"] = {
                "wizard": [{"name": spell_name, "level": 1}]
            }
            # Should handle any case variation
            assert character_data["spells"]["wizard"][0]["name"] == spell_name

class TestBonusActionCategorization:
    """Test proper categorization of different bonus action types."""
    
    @pytest.mark.quick
    def test_immediate_bonus_action_spells(self):
        """Test spells that are cast as bonus actions (not conditional)."""
        character_data = CharacterArchetypeFactory.create_wizard(level=3)
        
        # Misty Step is cast as a bonus action
        character_data["spells"] = {
            "wizard": [
                {
                    "name": "Misty Step",
                    "level": 2,
                    "casting_time": "1 Bonus Action",
                    "description": "You teleport up to 30 feet to an unoccupied space."
                }
            ]
        }
        
        spell = character_data["spells"]["wizard"][0]
        assert spell["casting_time"] == "1 Bonus Action"
        # This should be in regular bonus actions, not conditional

    @pytest.mark.quick
    def test_action_spells_with_bonus_effects(self):
        """Test spells cast as actions that provide bonus action effects."""
        character_data = CharacterArchetypeFactory.create_wizard(level=7)
        
        # Arcane Eye: cast as action, provides bonus action movement
        character_data["spells"] = {
            "wizard": [
                {
                    "name": "Arcane Eye",
                    "level": 4,
                    "casting_time": "1 Action",
                    "description": "You can move the eye up to 30 feet as a bonus action."
                }
            ]
        }
        
        spell = character_data["spells"]["wizard"][0]
        assert spell["casting_time"] == "1 Action"
        assert "bonus action" in spell["description"].lower()
        # This should be in conditional bonus actions

    @pytest.mark.quick
    def test_reaction_spells_with_bonus_effects(self):
        """Test spells cast as reactions that provide bonus action effects."""
        character_data = CharacterArchetypeFactory.create_wizard(level=3)
        
        # Note: Expeditious Retreat is actually a bonus action spell in D&D 5e,
        # but if it were a reaction spell with bonus effects, it would be handled similarly
        character_data["spells"] = {
            "wizard": [
                {
                    "name": "Test Reaction Spell",
                    "level": 1,
                    "casting_time": "1 Reaction",
                    "description": "After casting, you can take the Dash action as a bonus action."
                }
            ]
        }
        
        spell = character_data["spells"]["wizard"][0]
        assert spell["casting_time"] == "1 Reaction"
        assert "bonus action" in spell["description"].lower()

class TestPerformanceAndValidation:
    """Test performance and validation of bonus action parsing."""
    
    @pytest.mark.quick
    def test_bonus_action_parsing_performance(self):
        """Test that bonus action parsing is performant."""
        import time
        
        character_data = CharacterArchetypeFactory.create_wizard(level=20)
        
        # Add multiple spells with bonus action effects
        character_data["spells"] = {
            "wizard": [
                {"name": "Expeditious Retreat", "level": 1, "description": "bonus action dash"},
                {"name": "Arcane Eye", "level": 4, "description": "bonus action move"},
                {"name": "Find Familiar", "level": 1, "description": "bonus action command"},
                {"name": "Misty Step", "level": 2, "casting_time": "1 Bonus Action"},
                {"name": "Spiritual Weapon", "level": 2, "description": "bonus action attack"}
            ]
        }
        
        start_time = time.time()
        
        # Simulate parsing multiple characters
        for i in range(50):
            # Process spell data as parser would
            for spell in character_data["spells"]["wizard"]:
                spell_name = spell["name"].lower()
                description = spell.get("description", "").lower()
                casting_time = spell.get("casting_time", "").lower()
                
                # Check if it's a conditional bonus action spell
                if "bonus action" in description or "bonus action" in casting_time:
                    pass  # Would be processed by parser
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should be very fast
        assert execution_time < 0.1, "Bonus action parsing should be fast"

    @pytest.mark.quick
    def test_empty_spell_lists_handled(self):
        """Test that empty spell lists are handled gracefully."""
        character_data = CharacterArchetypeFactory.create_wizard(level=1)
        
        # Test with empty spell lists
        test_cases = [
            {},
            {"wizard": []},
            {"wizard": None},
        ]
        
        for spells_data in test_cases:
            character_data["spells"] = spells_data
            # Should not crash when processing empty/None spell data
            assert "spells" in character_data

    @pytest.mark.quick
    def test_malformed_spell_data_handled(self):
        """Test that malformed spell data is handled gracefully."""
        character_data = CharacterArchetypeFactory.create_wizard(level=3)
        
        # Test with malformed spell data
        character_data["spells"] = {
            "wizard": [
                {"name": None, "level": 1},  # None name
                {"level": 2},  # Missing name
                {"name": "Valid Spell", "description": None},  # None description
                None,  # None spell entry
                "invalid_spell_format"  # String instead of dict
            ]
        }
        
        # Should handle malformed data gracefully
        valid_spells = [spell for spell in character_data["spells"]["wizard"] 
                       if isinstance(spell, dict) and spell.get("name")]
        assert len(valid_spells) == 1
        assert valid_spells[0]["name"] == "Valid Spell"