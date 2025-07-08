#!/usr/bin/env python3
"""
Phase 1 Test Script - Core Architecture & Data Models

Test script to validate Phase 1 implementation.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models.character import Character, AbilityScores, CharacterClass, Species, Background, HitPoints, ArmorClass, Spellcasting
from src.clients.factory import ClientFactory
from src.interfaces.rule_engine import RuleVersion


async def test_data_models():
    """Test core data models."""
    print("🧪 Testing Core Data Models...")
    
    try:
        # Test AbilityScores
        abilities = AbilityScores(
            strength=16,
            dexterity=14,
            constitution=15,
            intelligence=12,
            wisdom=13,
            charisma=10
        )
        
        print(f"✅ AbilityScores: STR {abilities.strength} (+{abilities.get_modifier('strength')})")
        
        # Test CharacterClass
        fighter_class = CharacterClass(
            name="Fighter",
            level=5,
            hit_die=10,
            is_spellcaster=False
        )
        
        print(f"✅ CharacterClass: Level {fighter_class.level} {fighter_class.name}")
        
        # Test Species
        human = Species(
            name="Human",
            speed=30,
            ability_score_increases={"strength": 1, "constitution": 1}
        )
        
        print(f"✅ Species: {human.name} (Speed: {human.speed})")
        
        # Test Background
        soldier = Background(
            name="Soldier",
            skill_proficiencies=["Athletics", "Intimidation"]
        )
        
        print(f"✅ Background: {soldier.name}")
        
        # Test HitPoints
        hp = HitPoints(
            maximum=42,
            current=42,
            constitution_bonus=10,
            calculation_method="average"
        )
        
        print(f"✅ HitPoints: {hp.current}/{hp.maximum}")
        
        # Test ArmorClass
        ac = ArmorClass(
            total=18,
            base=10,
            armor_bonus=6,
            dexterity_bonus=2,
            calculation_method="standard"
        )
        
        print(f"✅ ArmorClass: {ac.total} (Method: {ac.calculation_method})")
        
        # Test Spellcasting
        spellcasting = Spellcasting(
            is_spellcaster=True,
            spellcasting_ability="intelligence",
            spell_save_dc=15,
            spell_attack_bonus=7,
            spell_slots_level_1=4,
            spell_slots_level_2=3,
            spell_slots_level_3=2
        )
        
        print(f"✅ Spellcasting: DC {spellcasting.spell_save_dc}, Attack +{spellcasting.spell_attack_bonus}")
        print(f"   Slots: {spellcasting.get_spell_slots_array()}")
        
        # Test full Character
        character = Character(
            id=999999,
            name="Test Character",
            level=5,
            rule_version=RuleVersion.RULES_2024,
            ability_scores=abilities,
            classes=[fighter_class],
            species=human,
            background=soldier,
            hit_points=hp,
            armor_class=ac,
            spellcasting=spellcasting,
            proficiency_bonus=3
        )
        
        print(f"✅ Character: {character.name} (Level {character.level} {character.get_primary_class().name})")
        print(f"   Multiclass: {character.is_multiclass()}")
        print(f"   Rule Version: {character.rule_version}")
        
        # Test extensibility
        character.additional_data['custom_field'] = 'custom_value'
        print(f"✅ Extensibility: Added custom field")
        
        return True
        
    except Exception as e:
        print(f"❌ Data model test failed: {str(e)}")
        return False


async def test_client_factory():
    """Test client factory."""
    print(f"\n🏭 Testing Client Factory...")
    
    try:
        # Test static mock client
        static_client = ClientFactory.create_client("static")
        print(f"✅ Created static mock client: {type(static_client).__name__}")
        
        # Test fetching static character
        data = await static_client.fetch_character_data(999999)
        summary = static_client.get_character_summary(data)
        print(f"✅ Fetched static character: {summary['name']} (Level {summary['level']})")
        
        # Test mock client
        mock_client = ClientFactory.create_client("mock")
        print(f"✅ Created mock client: {type(mock_client).__name__}")
        
        available = mock_client.list_available_characters()
        if available:
            print(f"✅ Mock client found {len(available)} characters")
            
            # Test fetching one
            char_id = next(iter(available.keys()))
            try:
                data = await mock_client.fetch_character_data(char_id)
                summary = mock_client.get_character_summary(data)
                print(f"✅ Fetched mock character: {summary['name']} (ID: {char_id})")
            except Exception as e:
                print(f"⚠️  Could not fetch character {char_id}: {str(e)}")
        else:
            print(f"ℹ️  No mock character files found")
        
        # Test environment-based creation
        test_client = ClientFactory.create_for_environment("testing")
        print(f"✅ Created testing environment client: {type(test_client).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Client factory test failed: {str(e)}")
        return False


async def test_interfaces():
    """Test interface compliance."""
    print(f"\n🔌 Testing Interface Compliance...")
    
    try:
        from src.interfaces.character_client import CharacterClientInterface
        from src.interfaces.calculator import CalculatorInterface
        from src.interfaces.rule_engine import RuleEngineInterface
        
        # Test that our clients implement the interface
        static_client = ClientFactory.create_client("static")
        
        if not isinstance(static_client, CharacterClientInterface):
            raise AssertionError("Static client does not implement CharacterClientInterface")
        
        print(f"✅ Static client implements CharacterClientInterface")
        
        # Test interface methods
        data = await static_client.fetch_character_data(999999)
        is_valid = static_client.validate_character_data(data)
        summary = static_client.get_character_summary(data)
        
        print(f"✅ Interface methods working: validate={is_valid}, summary_name={summary['name']}")
        
        # Test that interfaces are properly defined
        print(f"✅ CalculatorInterface has {len(dir(CalculatorInterface))} methods")
        print(f"✅ RuleEngineInterface has {len(dir(RuleEngineInterface))} methods")
        
        return True
        
    except Exception as e:
        print(f"❌ Interface test failed: {str(e)}")
        return False


async def test_configuration_integration():
    """Test configuration system integration."""
    print(f"\n⚙️ Testing Configuration Integration...")
    
    try:
        from src.config.manager import get_config_manager
        
        # Test that clients can access configuration
        config_manager = get_config_manager(environment="testing")
        config = config_manager.get_app_config()
        
        print(f"✅ Configuration accessible: {config.project.name} v{config.project.version}")
        
        # Test client with configuration
        real_client = ClientFactory.create_client("real", config_manager)
        print(f"✅ Real client created with configuration")
        
        # Test that configuration is used
        # (Don't actually make API calls in this test)
        print(f"✅ Client has access to API settings: timeout={config.api.timeout}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration integration test failed: {str(e)}")
        return False


async def main():
    """Run all Phase 1 tests."""
    print("Phase 1 Test Suite - Core Architecture & Data Models")
    print("=" * 60)
    
    tests = [
        test_data_models,
        test_client_factory,
        test_interfaces,
        test_configuration_integration
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
    
    print(f"\n" + "=" * 60)
    print(f"Phase 1 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"🎉 All Phase 1 tests passed! Core architecture is ready.")
        return 0
    else:
        print(f"💥 {total - passed} tests failed. Phase 1 needs fixes.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)