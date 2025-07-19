#!/usr/bin/env python3
"""
Full Character Calculation Test

Tests the enhanced scraper calculations with real character data.
"""

import json
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from calculators.enhanced_weapon_attacks import EnhancedWeaponAttackCalculator
from calculators.skill_bonus_calculator import SkillBonusCalculator
from calculators.class_resource_calculator import ClassResourceCalculator
from calculators.coordinators.combat import CombatCoordinator
from calculators.coordinators.proficiencies import ProficienciesCoordinator
from calculators.coordinators.resources import ResourcesCoordinator

def load_character_data(character_file):
    """Load character data from JSON file."""
    with open(character_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def transform_character_data(raw_data):
    """Transform raw D&D Beyond data to format expected by calculators."""
    # Extract ability scores
    ability_scores = {}
    stats = raw_data.get('stats', [])
    
    ability_map = {
        1: 'strength',
        2: 'dexterity', 
        3: 'constitution',
        4: 'intelligence',
        5: 'wisdom',
        6: 'charisma'
    }
    
    for stat in stats:
        ability_id = stat.get('id')
        ability_score = stat.get('value', 10)
        
        if ability_id in ability_map:
            ability_name = ability_map[ability_id]
            modifier = (ability_score - 10) // 2
            ability_scores[ability_name] = {
                'score': ability_score,
                'modifier': modifier
            }
    
    # Extract character level
    classes = raw_data.get('classes', [])
    total_level = sum(cls.get('level', 0) for cls in classes)
    
    # Extract equipped items
    equipped_items = []
    inventory = raw_data.get('inventory', [])
    for item in inventory:
        if item.get('equipped', False):
            equipped_items.append(item)
    
    # Extract proficiencies (simplified)
    weapon_proficiencies = []
    skill_proficiencies = []
    
    # Add class-based proficiencies
    for class_data in classes:
        class_def = class_data.get('definition', {})
        class_name = class_def.get('name', '').lower()
        
        # Add weapon proficiencies based on class
        if class_name in ['fighter', 'barbarian', 'paladin', 'ranger']:
            weapon_proficiencies.extend([
                {'name': 'simple weapons'},
                {'name': 'martial weapons'}
            ])
        elif class_name in ['wizard', 'sorcerer']:
            weapon_proficiencies.append({'name': 'simple weapons'})
        elif class_name in ['bard', 'cleric', 'druid', 'rogue', 'monk', 'warlock']:
            weapon_proficiencies.append({'name': 'simple weapons'})
    
    return {
        'abilities': {
            'ability_scores': ability_scores
        },
        'proficiencies': {
            'weapon_proficiencies': weapon_proficiencies,
            'skill_proficiencies': skill_proficiencies
        },
        'inventory': {
            'equipped_items': equipped_items
        },
        'equipment': {
            'equipped_items': equipped_items
        },
        'character_info': {
            'level': total_level,
            'name': raw_data.get('name', 'Unknown Character')
        },
        'classes': classes
    }

def test_weapon_calculations(character_data):
    """Test weapon attack calculations."""
    print("\n=== WEAPON ATTACK CALCULATIONS ===")
    
    calculator = EnhancedWeaponAttackCalculator()
    result = calculator.calculate(character_data)
    
    weapon_attacks = result.get('weapon_attacks', [])
    
    if not weapon_attacks:
        print("No weapon attacks found.")
        return
    
    for attack in weapon_attacks:
        print(f"\nWeapon: {attack.name}")
        print(f"  Type: {attack.weapon_type}")
        print(f"  Attack Bonus: +{attack.attack_bonus}")
        print(f"  Damage: {attack.damage_dice} + {attack.damage_modifier} {attack.damage_type}")
        print(f"  Properties: {', '.join(attack.properties) if attack.properties else 'None'}")
        
        if attack.range_normal:
            print(f"  Range: {attack.range_normal}/{attack.range_long}")
        
        # Show breakdown
        breakdown = attack.breakdown
        print(f"  Breakdown: {breakdown.get('description', 'N/A')}")
        print(f"    Ability: +{breakdown.get('ability_modifier', 0)} ({breakdown.get('ability_used', 'N/A')})")
        print(f"    Proficiency: +{breakdown.get('proficiency_bonus', 0)}")
        print(f"    Magic: +{breakdown.get('magic_bonus', 0)}")

def test_skill_calculations(character_data):
    """Test skill bonus calculations."""
    print("\n=== SKILL BONUS CALCULATIONS ===")
    
    calculator = SkillBonusCalculator()
    result = calculator.calculate(character_data)
    
    skill_bonuses = result.get('skill_bonuses', [])
    
    # Show only skills with non-zero bonuses or proficiency
    relevant_skills = [
        skill for skill in skill_bonuses 
        if skill.total_bonus != 0 or skill.is_proficient or skill.magic_bonus > 0
    ]
    
    if not relevant_skills:
        print("No relevant skills found.")
        return
    
    print(f"\nShowing {len(relevant_skills)} relevant skills:")
    
    for skill in sorted(relevant_skills, key=lambda s: s.skill_name):
        status_indicators = []
        if skill.is_proficient:
            status_indicators.append("Prof")
        if skill.has_expertise:
            status_indicators.append("Exp")
        if skill.magic_bonus > 0:
            status_indicators.append("Magic")
        
        status = f" ({', '.join(status_indicators)})" if status_indicators else ""
        
        print(f"  {skill.skill_name.replace('_', ' ').title()}: {skill.total_bonus:+d}{status}")
        
        if skill.magic_bonus > 0 or skill.is_proficient:
            print(f"    {skill.bonus_expression}")

def test_class_resources(character_data):
    """Test class resource calculations."""
    print("\n=== CLASS RESOURCE CALCULATIONS ===")
    
    calculator = ClassResourceCalculator()
    result = calculator.calculate(character_data)
    
    class_resources = result.get('class_resources', [])
    
    if not class_resources:
        print("No class resources found.")
        return
    
    for resource in class_resources:
        print(f"\n{resource.resource_name}:")
        print(f"  Total: {resource.total_amount}")
        print(f"  Used: {resource.used_amount}")
        print(f"  Remaining: {resource.remaining_amount}")
        print(f"  Reset: {resource.reset_type}")
        print(f"  Source: {resource.source_class}")

def main():
    """Main test function."""
    # Test with real character data
    character_files = [
        'character_data/raw_145081718_1752619219.json',
        'character_data/raw_143359582_1752525023.json'
    ]
    
    for char_file in character_files:
        if not os.path.exists(char_file):
            print(f"Character file not found: {char_file}")
            continue
        
        print(f"\n{'='*60}")
        print(f"TESTING CHARACTER: {char_file}")
        print(f"{'='*60}")
        
        try:
            # Load and transform character data
            raw_data = load_character_data(char_file)
            character_data = transform_character_data(raw_data)
            
            print(f"Character: {character_data['character_info']['name']}")
            print(f"Level: {character_data['character_info']['level']}")
            
            # Show ability scores
            print(f"\nAbility Scores:")
            for ability, data in character_data['abilities']['ability_scores'].items():
                print(f"  {ability.title()}: {data['score']} ({data['modifier']:+d})")
            
            # Show equipped items
            equipped_items = character_data['inventory']['equipped_items']
            print(f"\nEquipped Items: {len(equipped_items)}")
            for item in equipped_items[:5]:  # Show first 5
                item_name = item.get('definition', {}).get('name', item.get('name', 'Unknown'))
                item_type = item.get('definition', {}).get('filterType', 'unknown')
                print(f"  {item_name} ({item_type})")
            
            if len(equipped_items) > 5:
                print(f"  ... and {len(equipped_items) - 5} more items")
            
            # Run tests
            test_weapon_calculations(character_data)
            test_skill_calculations(character_data)
            test_class_resources(character_data)
            
        except Exception as e:
            print(f"Error testing character {char_file}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()