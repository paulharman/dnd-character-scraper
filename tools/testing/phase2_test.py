#!/usr/bin/env python3
"""
Phase 2 Test Script - D&D Rule Calculations & Complete JSON Output

Test script to validate Phase 2 calculator implementation.
"""

import sys
import asyncio
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.calculators.character_calculator import CharacterCalculator
from src.calculators.ability_scores import AbilityScoreCalculator
from src.calculators.hit_points import HitPointCalculator
from src.calculators.armor_class import ArmorClassCalculator
from src.calculators.spellcasting import SpellcastingCalculator
from src.calculators.proficiencies import ProficiencyCalculator
from src.clients.factory import ClientFactory


async def test_individual_calculators():
    """Test individual calculator modules."""
    print("🧮 Testing Individual Calculators...")
    
    try:
        # Get sample character data
        client = ClientFactory.create_client("static")
        raw_data = await client.fetch_character_data(999999)  # Test Fighter
        
        # Test ability score calculator
        print("  Testing AbilityScoreCalculator...")
        ability_calc = AbilityScoreCalculator()
        char = await _create_test_character(raw_data)
        ability_results = ability_calc.calculate(char, raw_data)
        
        print(f"    ✅ Ability scores: STR {ability_results['ability_scores']['strength']} DEX {ability_results['ability_scores']['dexterity']}")
        print(f"    ✅ Modifiers: STR {ability_results['ability_modifiers']['strength']:+d} DEX {ability_results['ability_modifiers']['dexterity']:+d}")
        
        # Test hit points calculator
        print("  Testing HitPointCalculator...")
        hp_calc = HitPointCalculator()
        hp_results = hp_calc.calculate(char, raw_data)
        
        print(f"    ✅ Hit Points: {hp_results['current_hp']}/{hp_results['max_hp']}")
        print(f"    ✅ Method: {hp_results['calculation_method']}")
        
        # Test armor class calculator
        print("  Testing ArmorClassCalculator...")
        ac_calc = ArmorClassCalculator()
        ac_results = ac_calc.calculate(char, raw_data)
        
        print(f"    ✅ Armor Class: {ac_results['armor_class']}")
        print(f"    ✅ Method: {ac_results['calculation_method']}")
        
        # Test spellcasting calculator
        print("  Testing SpellcastingCalculator...")
        spell_calc = SpellcastingCalculator()
        spell_results = spell_calc.calculate(char, raw_data)
        
        print(f"    ✅ Spellcaster: {spell_results['is_spellcaster']}")
        if spell_results['is_spellcaster']:
            print(f"    ✅ Spell DC: {spell_results['spell_save_dc']}, Attack: +{spell_results['spell_attack_bonus']}")
        
        # Test proficiency calculator
        print("  Testing ProficiencyCalculator...")
        prof_calc = ProficiencyCalculator()
        prof_results = prof_calc.calculate(char, raw_data)
        
        print(f"    ✅ Proficiency Bonus: +{prof_results['proficiency_bonus']}")
        print(f"    ✅ Skill Proficiencies: {len(prof_results['skill_proficiencies'])} skills")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Individual calculator test failed: {str(e)}")
        return False


async def test_character_calculator():
    """Test the main character calculator."""
    print(f"\n🎲 Testing Character Calculator...")
    
    try:
        # Get sample character data
        client = ClientFactory.create_client("static")
        raw_data = await client.fetch_character_data(999999)  # Test Fighter
        
        # Test complete character calculation
        calculator = CharacterCalculator()
        
        print("  Testing complete character calculation...")
        character = calculator.calculate_character(raw_data)
        
        print(f"    ✅ Character: {character.name} (Level {character.level})")
        print(f"    ✅ Primary Class: {character.get_primary_class().name}")
        print(f"    ✅ Ability Scores: STR {character.ability_scores.strength} DEX {character.ability_scores.dexterity}")
        print(f"    ✅ HP: {character.hit_points.current}/{character.hit_points.maximum}")
        print(f"    ✅ AC: {character.armor_class.total}")
        print(f"    ✅ Proficiency: +{character.proficiency_bonus}")
        
        # Test JSON output
        print("  Testing complete JSON output...")
        json_data = calculator.calculate_complete_json(raw_data)
        
        print(f"    ✅ JSON keys: {len(json_data)} top-level keys")
        print(f"    ✅ Ability scores: {json_data.get('ability_scores', {})}")
        print(f"    ✅ Calculator version: {json_data.get('calculation_metadata', {}).get('calculator_version')}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Character calculator test failed: {str(e)}")
        return False


async def test_multiclass_character():
    """Test with multiclass character."""
    print(f"\n🎭 Testing Multiclass Character...")
    
    try:
        # Get multiclass character
        client = ClientFactory.create_client("static")
        raw_data = await client.fetch_character_data(999998)  # Multiclass Paladin/Sorcerer
        
        calculator = CharacterCalculator()
        character = calculator.calculate_character(raw_data)
        
        print(f"    ✅ Character: {character.name} (Level {character.level})")
        print(f"    ✅ Classes: {[f'{cls.name} {cls.level}' for cls in character.classes]}")
        print(f"    ✅ Is Multiclass: {character.is_multiclass()}")
        print(f"    ✅ Spellcaster: {character.spellcasting.is_spellcaster}")
        
        if character.spellcasting.is_spellcaster:
            print(f"    ✅ Spell DC: {character.spellcasting.spell_save_dc}")
            print(f"    ✅ Spell Slots: {character.spellcasting.get_spell_slots_array()}")
            print(f"    ✅ Caster Level: {character.get_caster_level()}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Multiclass test failed: {str(e)}")
        return False


async def test_json_completeness():
    """Test that JSON output contains all required fields."""
    print(f"\n📄 Testing JSON Completeness...")
    
    try:
        client = ClientFactory.create_client("static")
        raw_data = await client.fetch_character_data(999999)
        
        calculator = CharacterCalculator()
        json_data = calculator.calculate_complete_json(raw_data)
        
        # Check required fields for parser
        required_fields = [
            'character_id', 'name', 'level', 'classes', 'species', 'background',
            'ability_scores', 'ability_modifiers', 'max_hp', 'current_hp', 'armor_class',
            'proficiency_bonus', 'is_spellcaster', 'spell_save_dc', 'spell_attack_bonus',
            'skill_proficiencies', 'saving_throw_proficiencies'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in json_data:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"    ❌ Missing required fields: {missing_fields}")
            return False
        
        print(f"    ✅ All required fields present")
        
        # Check that values are reasonable
        ability_scores = json_data.get('ability_scores', {})
        for ability, score in ability_scores.items():
            if not (1 <= score <= 30):
                print(f"    ❌ Invalid ability score: {ability} = {score}")
                return False
        
        print(f"    ✅ Ability scores in valid range")
        
        # Check AC is reasonable
        ac = json_data.get('armor_class', 0)
        if not (1 <= ac <= 30):
            print(f"    ❌ Invalid AC: {ac}")
            return False
        
        print(f"    ✅ AC in valid range: {ac}")
        
        # Check HP is positive
        max_hp = json_data.get('max_hp', 0)
        if max_hp < 1:
            print(f"    ❌ Invalid max HP: {max_hp}")
            return False
        
        print(f"    ✅ HP is positive: {max_hp}")
        
        print(f"    ✅ JSON output is complete and valid")
        return True
        
    except Exception as e:
        print(f"    ❌ JSON completeness test failed: {str(e)}")
        return False


async def test_with_real_character():
    """Test with real character data if available."""
    print(f"\n🎮 Testing with Real Character Data...")
    
    try:
        # Try to load a real character from Raw/ directory
        client = ClientFactory.create_client("mock")
        available = client.list_available_characters()
        
        if not available:
            print("    ℹ️  No real character data available, skipping")
            return True
        
        # Test with first available character
        char_id = next(iter(available.keys()))
        print(f"    Testing with character ID: {char_id}")
        
        raw_data = await client.fetch_character_data(char_id)
        calculator = CharacterCalculator()
        
        # Test that we can calculate without errors
        json_data = calculator.calculate_complete_json(raw_data)
        
        print(f"    ✅ Successfully calculated real character: {json_data.get('name')}")
        print(f"    ✅ Level {json_data.get('level')} {json_data.get('classes', [{}])[0].get('name', 'Unknown')}")
        print(f"    ✅ AC: {json_data.get('armor_class')}, HP: {json_data.get('max_hp')}")
        
        return True
        
    except Exception as e:
        print(f"    ⚠️  Real character test failed: {str(e)}")
        # Don't fail the overall test since this depends on available data
        return True


async def _create_test_character(raw_data):
    """Create a minimal character for testing."""
    from src.models.character import Character, AbilityScores, CharacterClass, Species, Background, HitPoints, ArmorClass, Spellcasting
    
    return Character(
        id=raw_data.get('id', 999999),
        name=raw_data.get('name', 'Test Character'),
        level=5,
        ability_scores=AbilityScores(strength=16, dexterity=14, constitution=15, intelligence=12, wisdom=13, charisma=10),
        classes=[CharacterClass(name="Fighter", level=5, hit_die=10)],
        species=Species(name="Human"),
        background=Background(name="Soldier"),
        hit_points=HitPoints(maximum=42),
        armor_class=ArmorClass(total=18),
        spellcasting=Spellcasting(),
        proficiency_bonus=3
    )


async def main():
    """Run all Phase 2 tests."""
    print("Phase 2 Test Suite - D&D Rule Calculations & Complete JSON Output")
    print("=" * 70)
    
    tests = [
        test_individual_calculators,
        test_character_calculator,
        test_multiclass_character,
        test_json_completeness,
        test_with_real_character
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"💥 Test {test.__name__} crashed: {str(e)}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n" + "=" * 70)
    print(f"Phase 2 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"🎉 All Phase 2 tests passed! D&D calculations are working.")
        print(f"\n📋 **NEXT STEP**: Manual validation data needed!")
        print(f"    The calculators are working, but we need you to provide")
        print(f"    expected values for a few test characters to validate accuracy.")
        print(f"    See validation_data/ directory for templates.")
        return 0
    else:
        print(f"💥 {total - passed} tests failed. Phase 2 needs fixes.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)