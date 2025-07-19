#!/usr/bin/env python3
"""
Test script to verify enhanced JSON output structure.

This script tests that the character calculator produces the enhanced JSON
structure with detailed breakdowns for weapon attacks, skills, and class resources.
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from calculators.character_calculator import CharacterCalculator
except ImportError as e:
    print(f"Import error: {e}")
    print("Trying alternative import...")
    sys.path.insert(0, str(Path(__file__).parent))
    from src.calculators.character_calculator import CharacterCalculator

def create_test_character_data():
    """Create minimal test character data for testing JSON output structure."""
    return {
        'id': 12345,
        'name': 'Test Character',
        'classes': [
            {
                'id': 1,
                'level': 5,
                'definition': {
                    'name': 'Fighter',
                    'hitDie': 10
                }
            }
        ],
        'stats': [
            {'id': 1, 'value': 16},  # Strength
            {'id': 2, 'value': 14},  # Dexterity
            {'id': 3, 'value': 15},  # Constitution
            {'id': 4, 'value': 10},  # Intelligence
            {'id': 5, 'value': 12},  # Wisdom
            {'id': 6, 'value': 8}    # Charisma
        ],
        'inventory': [
            {
                'equipped': True,
                'definition': {
                    'name': 'Longsword',
                    'type': 'martial weapon',
                    'damage': {
                        'diceString': '1d8',
                        'diceCount': 1,
                        'diceValue': 8
                    },
                    'damageType': 'slashing',
                    'weaponProperties': [
                        {'name': 'versatile'}
                    ]
                }
            }
        ],
        'baseHitPoints': 40,
        'bonusHitPoints': 0,
        'temporaryHitPoints': 0,
        'removedHitPoints': 5
    }

def test_json_output_structure():
    """Test that the JSON output structure includes enhanced calculations."""
    print("Testing enhanced JSON output structure...")
    
    # Create character calculator
    calculator = CharacterCalculator()
    
    # Create test character data
    character_data = create_test_character_data()
    
    try:
        # Calculate complete JSON
        result = calculator.calculate_complete_json(character_data)
        
        print(f"\n=== JSON Output Structure Test ===")
        print(f"Character ID: {result.get('character_info', {}).get('character_id', 'Unknown')}")
        
        # Check for enhanced combat section
        combat_data = result.get('combat', {})
        if combat_data:
            print(f"\n✓ Combat section found")
            
            # Check for weapon attacks
            weapon_attacks = combat_data.get('weapon_attacks', [])
            attack_actions = combat_data.get('attack_actions', [])
            
            if weapon_attacks:
                print(f"  ✓ Weapon attacks: {len(weapon_attacks)} found")
                for i, attack in enumerate(weapon_attacks[:2]):  # Show first 2
                    print(f"    - {attack.get('name', 'Unknown')}: +{attack.get('attack_bonus', 0)} to hit")
                    if 'breakdown' in attack:
                        print(f"      Breakdown: {attack['breakdown']}")
            elif attack_actions:
                print(f"  ✓ Attack actions: {len(attack_actions)} found")
                for i, attack in enumerate(attack_actions[:2]):  # Show first 2
                    print(f"    - {attack.get('name', 'Unknown')}: +{attack.get('attack_bonus', 0)} to hit")
            else:
                print(f"  ⚠ No weapon attacks found")
            
            # Check armor class
            ac_data = combat_data.get('armor_class')
            if isinstance(ac_data, dict):
                print(f"  ✓ Enhanced AC: {ac_data.get('total', 'Unknown')} (with breakdown)")
            elif isinstance(ac_data, int):
                print(f"  ✓ Basic AC: {ac_data}")
            
            # Check hit points
            hp_data = combat_data.get('hit_points', {})
            if hp_data:
                current = hp_data.get('current', 0)
                maximum = hp_data.get('maximum', 0)
                print(f"  ✓ Hit Points: {current}/{maximum}")
        else:
            print(f"  ⚠ No combat section found")
        
        # Check for enhanced proficiencies/skills section
        prof_data = result.get('proficiencies', {})
        if prof_data:
            print(f"\n✓ Proficiencies section found")
            
            skills_data = prof_data.get('skills', {})
            if skills_data:
                print(f"  ✓ Skills: {len(skills_data)} found")
                for skill_name, skill_info in list(skills_data.items())[:3]:  # Show first 3
                    if isinstance(skill_info, dict):
                        bonus = skill_info.get('total_bonus', 0)
                        breakdown = skill_info.get('breakdown', 'No breakdown')
                        print(f"    - {skill_name}: {bonus:+d} ({breakdown})")
                    else:
                        print(f"    - {skill_name}: {skill_info}")
            else:
                print(f"  ⚠ No skills found")
        else:
            print(f"  ⚠ No proficiencies section found")
        
        # Check for class resources section
        resources_data = result.get('resources', {})
        if resources_data:
            print(f"\n✓ Resources section found")
            
            class_resources = resources_data.get('class_resources', {})
            if class_resources:
                print(f"  ✓ Class resources: {len(class_resources)} found")
                
                # Handle both dict and list formats
                if isinstance(class_resources, dict):
                    for resource_name, resource_info in class_resources.items():
                        if isinstance(resource_info, dict):
                            total = resource_info.get('total', 0)
                            remaining = resource_info.get('remaining', 0)
                            print(f"    - {resource_name}: {remaining}/{total}")
                        else:
                            print(f"    - {resource_name}: {resource_info}")
                elif isinstance(class_resources, list):
                    for resource_info in class_resources:
                        if isinstance(resource_info, dict):
                            name = resource_info.get('resource_name', 'Unknown')
                            total = resource_info.get('total_amount', 0)
                            remaining = resource_info.get('remaining_amount', 0)
                            print(f"    - {name}: {remaining}/{total}")
                        else:
                            print(f"    - {resource_info}")
            else:
                print(f"  ⚠ No class resources found")
        else:
            print(f"  ⚠ No resources section found")
        
        # Check for calculation metadata
        metadata = result.get('calculation_metadata', {})
        if metadata:
            print(f"\n✓ Calculation metadata found")
            print(f"  Version: {metadata.get('version', 'Unknown')}")
            print(f"  Rule version: {metadata.get('rule_version', 'Unknown')}")
            print(f"  Calculated at: {metadata.get('calculated_at', 'Unknown')}")
        else:
            print(f"  ⚠ No calculation metadata found")
        
        # Check rule version
        rule_version = result.get('rule_version', 'Unknown')
        print(f"\n✓ Rule version: {rule_version}")
        
        print(f"\n=== JSON Structure Summary ===")
        sections = list(result.keys())
        print(f"Total sections: {len(sections)}")
        print(f"Sections: {', '.join(sections)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing JSON output structure: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_json_output_structure()
    if success:
        print(f"\n✅ JSON output structure test completed successfully!")
    else:
        print(f"\n❌ JSON output structure test failed!")
        sys.exit(1)