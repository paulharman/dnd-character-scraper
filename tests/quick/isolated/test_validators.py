"""
Isolated validator tests for quick validation.

Tests validation components without requiring full character processing.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from validators.character_validator import CharacterValidator
from validators.ability_score_validator import AbilityScoreValidator
from validators.spell_validator import SpellValidator

from ..factories.character_archetypes import CharacterArchetypeFactory
from ..factories.edge_cases import EdgeCaseFactory

class TestCharacterValidator:
    """Tests for CharacterValidator."""
    
    @pytest.mark.quick
    def test_valid_character_validation(self):
        """Test validation of valid character data."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        validator = CharacterValidator()
        
        result = validator.validate(character_data)
        
        assert result is not None
        assert hasattr(result, 'is_valid')
        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.quick
    def test_invalid_character_validation(self):
        """Test validation of invalid character data."""
        character_data = {
            "name": "",  # Empty name
            "level": 0,  # Invalid level
            "classes": [],  # No classes
            "ability_scores": {
                "strength": 50,  # Invalid score
                "dexterity": -5   # Invalid score
            }
        }
        validator = CharacterValidator()
        
        result = validator.validate(character_data)
        
        assert result is not None
        assert hasattr(result, 'is_valid')
        assert result.is_valid is False
        assert len(result.errors) > 0

    @pytest.mark.quick
    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        character_data = {
            "name": "Test Character"
            # Missing level, classes, ability_scores
        }
        validator = CharacterValidator()
        
        result = validator.validate(character_data)
        
        assert result is not None
        assert result.is_valid is False
        assert len(result.errors) > 0
        
        # Check for specific missing field errors
        error_messages = [error.message for error in result.errors]
        assert any("level" in msg.lower() for msg in error_messages)

    @pytest.mark.quick
    def test_character_level_validation(self):
        """Test character level validation."""
        validator = CharacterValidator()
        
        # Test valid levels
        for level in [1, 10, 20]:
            character_data = CharacterArchetypeFactory.create_fighter(level=level)
            result = validator.validate(character_data)
            assert result.is_valid is True
        
        # Test invalid levels
        for level in [0, -1, 21, 100]:
            character_data = CharacterArchetypeFactory.create_fighter(level=1)
            character_data["level"] = level
            result = validator.validate(character_data)
            assert result.is_valid is False

    @pytest.mark.quick
    def test_multiclass_validation(self):
        """Test validation of multiclass characters."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        validator = CharacterValidator()
        
        result = validator.validate(character_data)
        
        assert result is not None
        assert result.is_valid is True
        
        # Verify multiclass-specific validations
        total_levels = sum(cls["level"] for cls in character_data["classes"])
        assert total_levels == character_data["level"]

    @pytest.mark.quick
    def test_character_name_validation(self):
        """Test character name validation."""
        validator = CharacterValidator()
        
        # Test valid names
        valid_names = ["Test Character", "Élven Mage", "O'Reilly", "Character-Name"]
        for name in valid_names:
            character_data = CharacterArchetypeFactory.create_fighter(level=1)
            character_data["name"] = name
            result = validator.validate(character_data)
            assert result.is_valid is True
        
        # Test invalid names
        invalid_names = ["", "   ", None, "A" * 1000]  # Empty, whitespace, None, too long
        for name in invalid_names:
            character_data = CharacterArchetypeFactory.create_fighter(level=1)
            character_data["name"] = name
            result = validator.validate(character_data)
            assert result.is_valid is False

class TestAbilityScoreValidator:
    """Tests for AbilityScoreValidator."""
    
    @pytest.mark.quick
    def test_valid_ability_scores(self):
        """Test validation of valid ability scores."""
        ability_scores = {
            "strength": 16,
            "dexterity": 14,
            "constitution": 15,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 8
        }
        validator = AbilityScoreValidator()
        
        result = validator.validate(ability_scores)
        
        assert result is not None
        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.quick
    def test_invalid_ability_scores(self):
        """Test validation of invalid ability scores."""
        ability_scores = {
            "strength": 50,  # Too high
            "dexterity": -5,  # Too low
            "constitution": 15,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 8
        }
        validator = AbilityScoreValidator()
        
        result = validator.validate(ability_scores)
        
        assert result is not None
        assert result.is_valid is False
        assert len(result.errors) > 0

    @pytest.mark.quick
    def test_missing_ability_scores(self):
        """Test validation with missing ability scores."""
        ability_scores = {
            "strength": 16,
            "dexterity": 14
            # Missing constitution, intelligence, wisdom, charisma
        }
        validator = AbilityScoreValidator()
        
        result = validator.validate(ability_scores)
        
        assert result is not None
        assert result.is_valid is False
        assert len(result.errors) > 0

    @pytest.mark.quick
    def test_ability_score_boundaries(self):
        """Test ability score boundary validation."""
        validator = AbilityScoreValidator()
        
        # Test boundary values
        boundary_tests = [
            (1, True),   # Minimum valid
            (30, True),  # Maximum valid
            (0, False),  # Below minimum
            (31, False), # Above maximum
            (15, True),  # Normal value
        ]
        
        for score, should_be_valid in boundary_tests:
            ability_scores = {
                "strength": score,
                "dexterity": 10,
                "constitution": 10,
                "intelligence": 10,
                "wisdom": 10,
                "charisma": 10
            }
            result = validator.validate(ability_scores)
            assert result.is_valid == should_be_valid

    @pytest.mark.quick
    def test_ability_score_types(self):
        """Test ability score type validation."""
        validator = AbilityScoreValidator()
        
        # Test with non-integer values
        invalid_types = [
            "16",      # String
            16.5,      # Float
            None,      # None
            [16],      # List
            {"val": 16} # Dict
        ]
        
        for invalid_value in invalid_types:
            ability_scores = {
                "strength": invalid_value,
                "dexterity": 10,
                "constitution": 10,
                "intelligence": 10,
                "wisdom": 10,
                "charisma": 10
            }
            result = validator.validate(ability_scores)
            assert result.is_valid is False

class TestSpellValidator:
    """Tests for SpellValidator."""
    
    @pytest.mark.quick
    def test_valid_spell_data(self):
        """Test validation of valid spell data."""
        spell_data = {
            "spell_slots": {
                "1": 4,
                "2": 3,
                "3": 2
            },
            "spells_known": [
                {
                    "name": "Magic Missile",
                    "level": 1,
                    "school": "Evocation"
                },
                {
                    "name": "Fireball",
                    "level": 3,
                    "school": "Evocation"
                }
            ]
        }
        validator = SpellValidator()
        
        result = validator.validate(spell_data)
        
        assert result is not None
        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.quick
    def test_invalid_spell_slots(self):
        """Test validation of invalid spell slots."""
        spell_data = {
            "spell_slots": {
                "1": -1,  # Negative slots
                "2": 100,  # Too many slots
                "10": 1   # Invalid spell level
            }
        }
        validator = SpellValidator()
        
        result = validator.validate(spell_data)
        
        assert result is not None
        assert result.is_valid is False
        assert len(result.errors) > 0

    @pytest.mark.quick
    def test_spell_level_validation(self):
        """Test spell level validation."""
        validator = SpellValidator()
        
        # Test valid spell levels
        for level in range(0, 10):  # 0 (cantrips) to 9
            spell_data = {
                "spells_known": [{
                    "name": f"Test Spell Level {level}",
                    "level": level,
                    "school": "Evocation"
                }]
            }
            result = validator.validate(spell_data)
            assert result.is_valid is True
        
        # Test invalid spell levels
        for level in [-1, 10, 100]:
            spell_data = {
                "spells_known": [{
                    "name": f"Test Spell Level {level}",
                    "level": level,
                    "school": "Evocation"
                }]
            }
            result = validator.validate(spell_data)
            assert result.is_valid is False

    @pytest.mark.quick
    def test_spell_school_validation(self):
        """Test spell school validation."""
        validator = SpellValidator()
        
        # Test valid schools
        valid_schools = [
            "Abjuration", "Conjuration", "Divination", "Enchantment",
            "Evocation", "Illusion", "Necromancy", "Transmutation"
        ]
        
        for school in valid_schools:
            spell_data = {
                "spells_known": [{
                    "name": "Test Spell",
                    "level": 1,
                    "school": school
                }]
            }
            result = validator.validate(spell_data)
            assert result.is_valid is True
        
        # Test invalid school
        spell_data = {
            "spells_known": [{
                "name": "Test Spell",
                "level": 1,
                "school": "InvalidSchool"
            }]
        }
        result = validator.validate(spell_data)
        assert result.is_valid is False

    @pytest.mark.quick
    def test_non_spellcaster_validation(self):
        """Test validation for non-spellcaster characters."""
        spell_data = {
            "spell_slots": {},
            "spells_known": []
        }
        validator = SpellValidator()
        
        result = validator.validate(spell_data)
        
        assert result is not None
        assert result.is_valid is True

class TestValidatorErrorHandling:
    """Tests for validator error handling."""
    
    @pytest.mark.quick
    def test_validator_with_none_data(self):
        """Test validator handling of None data."""
        validators = [
            CharacterValidator(),
            AbilityScoreValidator(),
            SpellValidator()
        ]
        
        for validator in validators:
            result = validator.validate(None)
            assert result is not None
            assert result.is_valid is False
            assert len(result.errors) > 0

    @pytest.mark.quick
    def test_validator_with_empty_data(self):
        """Test validator handling of empty data."""
        validators = [
            CharacterValidator(),
            AbilityScoreValidator(),
            SpellValidator()
        ]
        
        for validator in validators:
            result = validator.validate({})
            assert result is not None
            assert result.is_valid is False
            assert len(result.errors) > 0

    @pytest.mark.quick
    def test_validator_with_malformed_data(self):
        """Test validator handling of malformed data."""
        malformed_data = {
            "name": ["This", "should", "be", "a", "string"],
            "level": "not_a_number",
            "classes": "should_be_list",
            "ability_scores": "should_be_dict"
        }
        
        validator = CharacterValidator()
        result = validator.validate(malformed_data)
        
        assert result is not None
        assert result.is_valid is False
        assert len(result.errors) > 0

    @pytest.mark.quick
    def test_validator_performance(self):
        """Test validator performance."""
        import time
        
        character_data = CharacterArchetypeFactory.create_level_20_barbarian()
        validator = CharacterValidator()
        
        start_time = time.time()
        result = validator.validate(character_data)
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 0.1  # Should complete in under 100ms
        assert result is not None

class TestValidatorIntegration:
    """Integration tests for validators."""
    
    @pytest.mark.quick
    def test_validators_with_edge_cases(self):
        """Test validators with edge case data."""
        edge_cases = [
            EdgeCaseFactory.create_level_1_character(),
            EdgeCaseFactory.create_level_20_character(),
            EdgeCaseFactory.create_extreme_stats_character()
        ]
        
        validator = CharacterValidator()
        
        for edge_case in edge_cases:
            result = validator.validate(edge_case)
            assert result is not None
            # Some edge cases may fail validation intentionally
            if not result.is_valid:
                assert len(result.errors) > 0

    @pytest.mark.quick
    def test_validators_with_all_archetypes(self):
        """Test validators with all character archetypes."""
        archetypes = [
            CharacterArchetypeFactory.create_fighter(level=5),
            CharacterArchetypeFactory.create_wizard(level=5),
            CharacterArchetypeFactory.create_rogue(level=5),
            CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        ]
        
        validator = CharacterValidator()
        
        for archetype in archetypes:
            result = validator.validate(archetype)
            assert result is not None
            assert result.is_valid is True
            assert len(result.errors) == 0