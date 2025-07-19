#!/usr/bin/env python3
"""
Enhanced Scraper Integration Tests

Comprehensive integration tests for the enhanced scraper calculations.
Tests the complete workflow from raw D&D Beyond data through scraper,
parser, and Discord monitor compatibility.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def create_test_character_data() -> Dict[str, Any]:
    """Create comprehensive test character data for integration testing."""
    return {
        'id': 12345,
        'name': 'Integration Test Character',
        'classes': [
            {
                'id': 1,
                'level': 5,
                'name': 'Fighter',
                'definition': {
                    'name': 'Fighter',
                    'hitDie': 10
                }
            },
            {
                'id': 2,
                'level': 3,
                'name': 'Rogue',
                'definition': {
                    'name': 'Rogue',
                    'hitDie': 8
                }
            }
        ],
        'stats': [
            {'id': 1, 'value': 16},  # Strength
            {'id': 2, 'value': 18},  # Dexterity
            {'id': 3, 'value': 14},  # Constitution
            {'id': 4, 'value': 12},  # Intelligence
            {'id': 5, 'value': 13},  # Wisdom
            {'id': 6, 'value': 10}   # Charisma
        ],
        'inventory': [
            {
                'equipped': True,
                'definition': {
                    'name': 'Rapier +1',
                    'type': 'martial weapon',
                    'damage': {
                        'diceString': '1d8',
                        'diceCount': 1,
                        'diceValue': 8
                    },
                    'damageType': 'piercing',
                    'weaponProperties': [
                        {'name': 'finesse'}
                    ],
                    'attackType': 1,  # melee
                    'magicBonus': 1
                }
            },
            {
                'equipped': True,
                'definition': {
                    'name': 'Shortbow',
                    'type': 'simple weapon',
                    'damage': {
                        'diceString': '1d6',
                        'diceCount': 1,
                        'diceValue': 6
                    },
                    'damageType': 'piercing',
                    'weaponProperties': [
                        {'name': 'ammunition'},
                        {'name': 'range'},
                        {'name': 'two-handed'}
                    ],
                    'attackType': 2,  # ranged
                    'range': 80,
                    'longRange': 320
                }
            }
        ],
        'baseHitPoints': 45,
        'bonusHitPoints': 5,
        'temporaryHitPoints': 0,
        'removedHitPoints': 8,
        'sources': [
            {'name': "Player's Handbook (2014)"}
        ]
    }

def test_character_calculator_integration():
    """Test the complete character calculator integration."""
    print("=== Character Calculator Integration Test ===")
    
    try:
        from calculators.character_calculator import CharacterCalculator
        
        # Create calculator
        calculator = CharacterCalculator()
        
        # Create test character data
        character_data = create_test_character_data()
        
        # Calculate complete JSON
        result = calculator.calculate_complete_json(character_data)
        
        # Validate basic structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'character_info' in result, "Should have character_info section"
        assert 'combat' in result, "Should have combat section"
        assert 'proficiencies' in result, "Should have proficiencies section"
        assert 'resources' in result, "Should have resources section"
        
        # Validate character info
        char_info = result['character_info']
        assert char_info['character_id'] == '12345', "Character ID should match"
        assert char_info['level'] == 8, "Total level should be 8 (5+3)"
        
        # Validate combat section
        combat = result['combat']
        assert 'weapon_attacks' in combat or 'attack_actions' in combat, "Should have weapon attacks"
        assert 'armor_class' in combat, "Should have armor class"
        assert 'hit_points' in combat, "Should have hit points"
        
        # Validate weapon attacks
        weapon_attacks = combat.get('weapon_attacks', combat.get('attack_actions', []))
        assert len(weapon_attacks) >= 1, "Should have at least one weapon attack"
        
        # Check for enhanced weapon attack data
        if weapon_attacks:
            attack = weapon_attacks[0]
            assert 'name' in attack, "Attack should have name"
            assert 'attack_bonus' in attack, "Attack should have attack bonus"
            assert 'damage_dice' in attack or 'damage' in attack, "Attack should have damage"
            
            # Check for breakdown if available
            if 'breakdown' in attack:
                breakdown = attack['breakdown']
                assert isinstance(breakdown, dict), "Breakdown should be a dictionary"
                print(f"  ✓ Weapon attack breakdown: {breakdown.get('description', 'No description')}")
        
        # Validate proficiencies section
        proficiencies = result['proficiencies']
        if 'skill_bonuses' in proficiencies:
            skill_bonuses = proficiencies['skill_bonuses']
            assert isinstance(skill_bonuses, list), "Skill bonuses should be a list"
            if skill_bonuses:
                skill = skill_bonuses[0]
                assert 'skill_name' in skill, "Skill should have name"
                assert 'total_bonus' in skill, "Skill should have total bonus"
                print(f"  ✓ Enhanced skill bonus format detected")
        
        # Validate resources section
        resources = result['resources']
        if 'class_resources' in resources:
            class_resources = resources['class_resources']
            assert isinstance(class_resources, list), "Class resources should be a list"
            print(f"  ✓ Class resources: {len(class_resources)} found")
        
        # Validate rule version
        rule_version = result.get('rule_version', 'Unknown')
        assert rule_version in ['2014', '2024'], f"Rule version should be 2014 or 2024, got {rule_version}"
        print(f"  ✓ Rule version: {rule_version}")
        
        print("✅ Character Calculator Integration Test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Character Calculator Integration Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_parser_integration():
    """Test parser integration with enhanced JSON structure."""
    print("\n=== Parser Integration Test ===")
    
    try:
        # Import parser components
        sys.path.insert(0, str(Path(__file__).parent / 'parser'))
        from factories.generator_factory import GeneratorFactory
        from calculators.character_calculator import CharacterCalculator
        
        # Create calculator and generate enhanced JSON
        calculator = CharacterCalculator()
        character_data = create_test_character_data()
        enhanced_json = calculator.calculate_complete_json(character_data)
        
        # Create parser
        factory = GeneratorFactory()
        generator = factory.create_generator()
        
        # Generate markdown
        markdown = generator.generate_markdown(enhanced_json)
        
        # Validate markdown output
        assert isinstance(markdown, str), "Markdown should be a string"
        assert len(markdown) > 100, "Markdown should have substantial content"
        assert '# ' in markdown, "Markdown should have headers"
        
        # Check for enhanced content
        if 'weapon_attacks' in enhanced_json.get('combat', {}):
            # Should contain weapon attack information
            weapon_attacks = enhanced_json['combat']['weapon_attacks']
            if weapon_attacks:
                weapon_name = weapon_attacks[0].get('name', '')
                if weapon_name:
                    assert weapon_name in markdown, f"Markdown should contain weapon name: {weapon_name}"
                    print(f"  ✓ Weapon attack '{weapon_name}' found in markdown")
        
        # Check for skill information
        if 'skill_bonuses' in enhanced_json.get('proficiencies', {}):
            skill_bonuses = enhanced_json['proficiencies']['skill_bonuses']
            if skill_bonuses:
                print(f"  ✓ Enhanced skill bonuses processed by parser")
        
        # Check for class resources
        if 'class_resources' in enhanced_json.get('resources', {}):
            class_resources = enhanced_json['resources']['class_resources']
            if class_resources:
                print(f"  ✓ Class resources processed by parser")
        
        print("✅ Parser Integration Test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Parser Integration Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_discord_monitor_compatibility():
    """Test Discord monitor compatibility with enhanced JSON structure."""
    print("\n=== Discord Monitor Compatibility Test ===")
    
    try:
        # Import Discord change detection components
        sys.path.insert(0, str(Path(__file__).parent / 'discord'))
        from services.change_detection.detectors import CompositeDetector, CombatDetector, SkillDetector
        from services.change_detection.models import CharacterSnapshot, ChangeType, ChangePriority
        from calculators.character_calculator import CharacterCalculator
        
        # Create calculator and generate enhanced JSON
        calculator = CharacterCalculator()
        character_data = create_test_character_data()
        enhanced_json_v1 = calculator.calculate_complete_json(character_data)
        
        # Create a modified version for change detection
        character_data_v2 = character_data.copy()
        character_data_v2['stats'][0]['value'] = 18  # Increase strength from 16 to 18
        enhanced_json_v2 = calculator.calculate_complete_json(character_data_v2)
        
        # Create snapshots
        snapshot_v1 = CharacterSnapshot(
            character_id='12345',
            version='v1',
            timestamp=None,
            character_data=enhanced_json_v1
        )
        
        snapshot_v2 = CharacterSnapshot(
            character_id='12345',
            version='v2',
            timestamp=None,
            character_data=enhanced_json_v2
        )
        
        # Test individual detectors
        combat_detector = CombatDetector()
        skill_detector = SkillDetector()
        
        # Test combat detector
        combat_changes = combat_detector.detect_changes(enhanced_json_v1, enhanced_json_v2, {})
        print(f"  ✓ Combat detector found {len(combat_changes)} changes")
        
        # Test skill detector
        skill_changes = skill_detector.detect_changes(enhanced_json_v1, enhanced_json_v2, {})
        print(f"  ✓ Skill detector found {len(skill_changes)} changes")
        
        # Test composite detector
        composite_detector = CompositeDetector()
        all_changes = composite_detector.detect_changes(enhanced_json_v1, enhanced_json_v2, {})
        print(f"  ✓ Composite detector found {len(all_changes)} total changes")
        
        # Validate change detection
        if all_changes:
            for change in all_changes[:3]:  # Show first 3 changes
                print(f"    - {change.description} (Priority: {change.priority.name})")
        
        print("✅ Discord Monitor Compatibility Test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Discord Monitor Compatibility Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n=== Edge Cases Test ===")
    
    try:
        from calculators.character_calculator import CharacterCalculator
        
        calculator = CharacterCalculator()
        
        # Test with minimal data
        minimal_data = {
            'id': 99999,
            'name': 'Minimal Character',
            'classes': [{'level': 1, 'name': 'Fighter'}],
            'stats': [
                {'id': 1, 'value': 10},
                {'id': 2, 'value': 10},
                {'id': 3, 'value': 10},
                {'id': 4, 'value': 10},
                {'id': 5, 'value': 10},
                {'id': 6, 'value': 10}
            ]
        }
        
        result = calculator.calculate_complete_json(minimal_data)
        assert isinstance(result, dict), "Should handle minimal data"
        print("  ✓ Minimal character data handled correctly")
        
        # Test with empty data
        empty_result = calculator.calculate_complete_json({})
        assert isinstance(empty_result, dict), "Should handle empty data gracefully"
        print("  ✓ Empty data handled gracefully")
        
        # Test with malformed data
        malformed_data = {
            'id': 'not_a_number',
            'classes': 'not_a_list',
            'stats': None
        }
        
        malformed_result = calculator.calculate_complete_json(malformed_data)
        assert isinstance(malformed_result, dict), "Should handle malformed data"
        print("  ✓ Malformed data handled gracefully")
        
        print("✅ Edge Cases Test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Edge Cases Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiclass_calculations():
    """Test multiclass character calculations."""
    print("\n=== Multiclass Calculations Test ===")
    
    try:
        from calculators.character_calculator import CharacterCalculator
        
        calculator = CharacterCalculator()
        character_data = create_test_character_data()  # Fighter 5 / Rogue 3
        
        result = calculator.calculate_complete_json(character_data)
        
        # Validate multiclass handling
        char_info = result['character_info']
        assert char_info['level'] == 8, "Total level should be 8"
        
        # Check proficiency bonus (should be +3 for level 8)
        combat = result['combat']
        prof_bonus = combat.get('proficiency_bonus', 0)
        assert prof_bonus == 3, f"Proficiency bonus should be 3 for level 8, got {prof_bonus}"
        
        # Check class resources (should have both Fighter and Rogue resources if applicable)
        resources = result.get('resources', {})
        class_resources = resources.get('class_resources', [])
        
        # Fighter should have Action Surge and Second Wind
        # Rogue should have Sneak Attack (though this might not be tracked as a resource)
        print(f"  ✓ Multiclass character (Fighter 5/Rogue 3) calculated correctly")
        print(f"  ✓ Total level: {char_info['level']}, Proficiency bonus: +{prof_bonus}")
        print(f"  ✓ Class resources found: {len(class_resources)}")
        
        print("✅ Multiclass Calculations Test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Multiclass Calculations Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_integration_tests():
    """Run all integration tests."""
    print("🧪 Running Enhanced Scraper Integration Tests")
    print("=" * 60)
    
    tests = [
        test_character_calculator_integration,
        test_parser_integration,
        test_discord_monitor_compatibility,
        test_edge_cases,
        test_multiclass_calculations
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Integration Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All integration tests PASSED! Enhanced scraper calculations are working correctly.")
        return True
    else:
        print(f"\n⚠️  {failed} integration test(s) FAILED. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = run_all_integration_tests()
    sys.exit(0 if success else 1)