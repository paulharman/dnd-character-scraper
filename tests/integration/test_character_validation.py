"""
Comprehensive character validation tests using standardized fixtures.

This replaces character-specific validation scripts with proper test fixtures.
"""

import pytest
from typing import Dict, Any, List

from tests.fixtures.characters import (
    CharacterFixtures, RawDataFixtures, ValidationFixtures,
    get_character_fixture, get_all_character_fixtures
)
from tests.factories import CharacterFactory
from src.models.character import Character


class TestCharacterValidation:
    """Test character data validation using standardized fixtures."""
    
    @pytest.mark.parametrize("fixture_name", [
        "BASIC_FIGHTER",
        "WIZARD_SPELLCASTER", 
        "MULTICLASS_FIGHTER_WIZARD",
        "ROGUE_WITH_EXPERTISE",
        "EDGE_CASE_CHARACTER"
    ])
    def test_character_fixture_completeness(self, fixture_name: str):
        """Test that character fixtures have all required fields."""
        fixture = get_character_fixture(fixture_name)
        
        # Required top-level fields
        required_fields = [
            "id", "name", "level", "proficiency_bonus", "rule_version",
            "ability_scores", "classes", "species", "background",
            "hit_points", "armor_class", "spellcasting", "skills",
            "saving_throw_proficiencies"
        ]
        
        for field in required_fields:
            assert field in fixture, f"Missing required field '{field}' in {fixture_name}"
        
        # Validate ability scores
        ability_scores = fixture["ability_scores"]
        abilities = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        for ability in abilities:
            assert ability in ability_scores, f"Missing ability score '{ability}' in {fixture_name}"
            assert isinstance(ability_scores[ability], int), f"Ability score '{ability}' must be integer in {fixture_name}"
            assert 1 <= ability_scores[ability] <= 30, f"Ability score '{ability}' out of range in {fixture_name}"
    
    @pytest.mark.parametrize("fixture_name", [
        "BASIC_FIGHTER",
        "WIZARD_SPELLCASTER",
        "MULTICLASS_FIGHTER_WIZARD", 
        "ROGUE_WITH_EXPERTISE"
    ])
    def test_spell_count_validation(self, fixture_name: str):
        """Test that spell counts match expected values."""
        fixture = get_character_fixture(fixture_name)
        expected_count = ValidationFixtures.EXPECTED_SPELL_COUNTS[fixture_name]
        
        actual_count = len(fixture.get("spells", []))
        assert actual_count == expected_count, (
            f"{fixture_name}: Expected {expected_count} spells, got {actual_count}"
        )
    
    @pytest.mark.parametrize("fixture_name", [
        "BASIC_FIGHTER",
        "WIZARD_SPELLCASTER",
        "MULTICLASS_FIGHTER_WIZARD",
        "ROGUE_WITH_EXPERTISE"
    ])
    def test_skill_count_validation(self, fixture_name: str):
        """Test that skill counts match expected values."""
        fixture = get_character_fixture(fixture_name)
        expected_count = ValidationFixtures.EXPECTED_SKILL_COUNTS[fixture_name]
        
        actual_count = len(fixture.get("skills", []))
        assert actual_count == expected_count, (
            f"{fixture_name}: Expected {expected_count} skills, got {actual_count}"
        )
    
    @pytest.mark.parametrize("fixture_name", [
        "BASIC_FIGHTER",
        "WIZARD_SPELLCASTER", 
        "MULTICLASS_FIGHTER_WIZARD",
        "ROGUE_WITH_EXPERTISE",
        "EDGE_CASE_CHARACTER"
    ])
    def test_armor_class_validation(self, fixture_name: str):
        """Test that armor class values match expected values."""
        fixture = get_character_fixture(fixture_name)
        expected_ac = ValidationFixtures.EXPECTED_AC_VALUES[fixture_name]
        
        actual_ac = fixture["armor_class"]["total"]
        assert actual_ac == expected_ac, (
            f"{fixture_name}: Expected AC {expected_ac}, got {actual_ac}"
        )
    
    def test_spellcaster_spell_validation(self):
        """Test detailed spell validation for spellcasters."""
        wizard = get_character_fixture("WIZARD_SPELLCASTER")
        
        spells = wizard["spells"]
        assert len(spells) == 9, f"Wizard should have 9 spells, got {len(spells)}"
        
        # Check spell sources
        spell_sources = [spell["source"] for spell in spells]
        assert "Racial" in spell_sources, "Should have racial spells"
        assert "Wizard" in spell_sources, "Should have wizard spells"
        
        # Check spell levels
        spell_levels = [spell["level"] for spell in spells]
        assert 0 in spell_levels, "Should have cantrips"
        assert 1 in spell_levels, "Should have 1st level spells"
        assert 2 in spell_levels, "Should have 2nd level spells"
        assert 3 in spell_levels, "Should have 3rd level spells"
        
        # Check for specific expected spells
        spell_names = [spell["name"] for spell in spells]
        expected_spells = ["Fire Bolt", "Magic Missile", "Fireball", "Detect Magic"]
        for expected_spell in expected_spells:
            assert expected_spell in spell_names, f"Should have spell '{expected_spell}'"
    
    def test_multiclass_validation(self):
        """Test multiclass character validation."""
        multiclass = get_character_fixture("MULTICLASS_FIGHTER_WIZARD")
        
        classes = multiclass["classes"]
        assert len(classes) == 2, f"Multiclass should have 2 classes, got {len(classes)}"
        
        class_names = [cls["name"] for cls in classes]
        assert "Fighter" in class_names, "Should have Fighter class"
        assert "Wizard" in class_names, "Should have Wizard class"
        
        # Check total level
        total_level = sum(cls["level"] for cls in classes)
        assert total_level == multiclass["level"], "Class levels should sum to character level"
        
        # Check spellcasting
        assert multiclass["spellcasting"]["is_spellcaster"], "Multiclass should be spellcaster"
        
        # Check saving throw proficiencies (should have both classes)
        saves = multiclass["saving_throw_proficiencies"]
        assert "Strength" in saves, "Should have Fighter save proficiency"
        assert "Constitution" in saves, "Should have Fighter save proficiency"
        assert "Intelligence" in saves, "Should have Wizard save proficiency"
        assert "Wisdom" in saves, "Should have Wizard save proficiency"
    
    def test_rogue_expertise_validation(self):
        """Test rogue expertise mechanics."""
        rogue = get_character_fixture("ROGUE_WITH_EXPERTISE")
        
        skills = rogue["skills"]
        expertise_skills = [skill for skill in skills if skill.get("expertise", False)]
        
        assert len(expertise_skills) >= 3, "Rogue should have at least 3 expertise skills"
        
        # Check that expertise skills have higher bonuses
        for skill in expertise_skills:
            # Expertise should roughly double proficiency bonus
            expected_min_bonus = rogue["proficiency_bonus"] * 2
            assert skill["total_bonus"] >= expected_min_bonus, (
                f"Expertise skill '{skill['name']}' should have high bonus"
            )
    
    def test_edge_case_character_validation(self):
        """Test edge case character with extreme values."""
        edge_case = get_character_fixture("EDGE_CASE_CHARACTER")
        
        # Test extreme ability scores
        abilities = edge_case["ability_scores"]
        assert abilities["strength"] == 30, "Should handle maximum strength"
        assert abilities["dexterity"] == 1, "Should handle minimum dexterity"
        assert abilities["wisdom"] == 30, "Should handle maximum wisdom"
        assert abilities["charisma"] == 1, "Should handle minimum charisma"
        
        # Test high level character
        assert edge_case["level"] == 20, "Should be max level"
        assert edge_case["proficiency_bonus"] == 6, "Should have max proficiency bonus"
        
        # Test extreme HP
        assert edge_case["hit_points"]["maximum"] > 200, "Should have very high HP"
        
        # Test extreme AC
        assert edge_case["armor_class"]["total"] >= 20, "Should have very high AC"


class TestRawDataProcessing:
    """Test processing of raw D&D Beyond data using fixtures."""
    
    def test_basic_fighter_raw_processing(self):
        """Test processing raw fighter data."""
        raw_data = RawDataFixtures.get_basic_fighter_raw()
        
        # Validate raw data structure
        assert "id" in raw_data
        assert "name" in raw_data
        assert "level" in raw_data
        assert "stats" in raw_data
        assert "classes" in raw_data
        assert "race" in raw_data
        
        # Validate stats structure
        stats = raw_data["stats"]
        assert len(stats) == 6, "Should have 6 ability scores"
        
        for i, stat in enumerate(stats, 1):
            assert stat["id"] == i, f"Stat {i} should have correct ID"
            assert "value" in stat, f"Stat {i} should have value"
            assert isinstance(stat["value"], int), f"Stat {i} value should be integer"
    
    def test_wizard_spellcaster_raw_processing(self):
        """Test processing raw wizard spellcaster data."""
        raw_data = RawDataFixtures.get_wizard_spellcaster_raw()
        
        # Validate spellcasting data
        assert "spells" in raw_data
        assert "classSpells" in raw_data
        
        spells = raw_data["spells"]
        assert "race" in spells, "Should have racial spells"
        assert "class" in spells, "Should have class spells"
        assert "feat" in spells, "Should have feat spells"
        
        # Check racial spells
        racial_spells = spells["race"]
        assert len(racial_spells) > 0, "Should have racial spells"
        
        for spell in racial_spells:
            assert "definition" in spell, "Spell should have definition"
            definition = spell["definition"]
            assert "name" in definition, "Spell should have name"
            assert "level" in definition, "Spell should have level"
            assert "school" in definition, "Spell should have school"
        
        # Check class spells
        class_spells = raw_data["classSpells"]
        assert len(class_spells) > 0, "Should have class spells"
        
        for class_spell_group in class_spells:
            assert "characterClassId" in class_spell_group
            assert "spells" in class_spell_group
            
            for spell in class_spell_group["spells"]:
                assert "definition" in spell
                definition = spell["definition"]
                assert "name" in definition
                assert "level" in definition


class TestFixtureConsistency:
    """Test consistency between different fixture types."""
    
    def test_character_fixture_ids_unique(self):
        """Test that all character fixture IDs are unique."""
        fixtures = get_all_character_fixtures()
        ids = [fixture["id"] for fixture in fixtures]
        
        assert len(ids) == len(set(ids)), "All character fixture IDs should be unique"
    
    def test_validation_fixtures_complete(self):
        """Test that validation fixtures cover all character fixtures."""
        character_fixtures = [
            "BASIC_FIGHTER", "WIZARD_SPELLCASTER", "MULTICLASS_FIGHTER_WIZARD",
            "ROGUE_WITH_EXPERTISE", "EDGE_CASE_CHARACTER"
        ]
        
        # Check spell count expectations
        for fixture_name in character_fixtures:
            assert fixture_name in ValidationFixtures.EXPECTED_SPELL_COUNTS, (
                f"Missing spell count expectation for {fixture_name}"
            )
        
        # Check skill count expectations  
        for fixture_name in character_fixtures:
            assert fixture_name in ValidationFixtures.EXPECTED_SKILL_COUNTS, (
                f"Missing skill count expectation for {fixture_name}"
            )
        
        # Check AC expectations
        for fixture_name in character_fixtures:
            assert fixture_name in ValidationFixtures.EXPECTED_AC_VALUES, (
                f"Missing AC expectation for {fixture_name}"
            )
    
    def test_fixture_data_types(self):
        """Test that fixture data has correct types."""
        fixtures = get_all_character_fixtures()
        
        for fixture in fixtures:
            # Test basic types
            assert isinstance(fixture["id"], int), "ID should be integer"
            assert isinstance(fixture["name"], str), "Name should be string"
            assert isinstance(fixture["level"], int), "Level should be integer"
            assert isinstance(fixture["proficiency_bonus"], int), "Proficiency bonus should be integer"
            
            # Test nested structures
            assert isinstance(fixture["ability_scores"], dict), "Ability scores should be dict"
            assert isinstance(fixture["classes"], list), "Classes should be list"
            assert isinstance(fixture["skills"], list), "Skills should be list"
            assert isinstance(fixture["saving_throw_proficiencies"], list), "Saves should be list"
            
            # Test spell data for spellcasters
            if fixture.get("spells"):
                assert isinstance(fixture["spells"], list), "Spells should be list"
                for spell in fixture["spells"]:
                    assert isinstance(spell, dict), "Each spell should be dict"
                    assert "name" in spell, "Spell should have name"
                    assert "level" in spell, "Spell should have level"
                    assert "source" in spell, "Spell should have source"


class TestFixtureUsageExamples:
    """Examples of how to use fixtures in tests."""
    
    def test_using_character_factory_with_fixture(self):
        """Example: Using character factory with fixture data."""
        fixture_data = get_character_fixture("BASIC_FIGHTER")
        
        # Create character using factory with fixture overrides
        character = CharacterFactory.create_character(
            id=fixture_data["id"],
            name=fixture_data["name"],
            level=fixture_data["level"]
        )
        
        assert character.id == fixture_data["id"]
        assert character.name == fixture_data["name"]
        assert character.level == fixture_data["level"]
    
    def test_comparing_processed_vs_fixture(self):
        """Example: Comparing processed character data to fixture expectations."""
        fixture = get_character_fixture("WIZARD_SPELLCASTER")
        
        # Simulate processing (would normally use actual processor)
        processed_spell_count = len(fixture["spells"])
        expected_spell_count = ValidationFixtures.EXPECTED_SPELL_COUNTS["WIZARD_SPELLCASTER"]
        
        assert processed_spell_count == expected_spell_count, (
            f"Processed spell count {processed_spell_count} doesn't match expected {expected_spell_count}"
        )
    
    def test_fixture_based_regression_testing(self):
        """Example: Using fixtures for regression testing."""
        # Test that all fixtures can be processed without errors
        fixtures = get_all_character_fixtures()
        
        for fixture in fixtures:
            # Simulate character processing (would use actual processor)
            assert fixture["id"] > 0, f"Character {fixture['name']} should have valid ID"
            assert fixture["level"] > 0, f"Character {fixture['name']} should have valid level"
            assert len(fixture["classes"]) > 0, f"Character {fixture['name']} should have classes"
            
            # Test spellcaster validation
            if fixture["spellcasting"]["is_spellcaster"]:
                assert "spellcasting_ability" in fixture["spellcasting"], (
                    f"Spellcaster {fixture['name']} should have spellcasting ability"
                )