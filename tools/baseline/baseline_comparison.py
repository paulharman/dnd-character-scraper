#!/usr/bin/env python3
"""
Baseline Comparison Script

Compare current v5.2.0 output with new v6.0.0 calculator output.
"""

import sys
import json
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.calculators.character_calculator import CharacterCalculator
from src.clients.factory import ClientFactory


async def compare_character_calculations(character_id: int):
    """Compare v5.2.0 vs v6.0.0 calculations for a character."""
    print(f"🔍 Baseline Comparison for Character {character_id}")
    print("=" * 60)
    
    # Load v5.2.0 baseline data
    baseline_file = Path("baseline_test.json")
    if not baseline_file.exists():
        print(f"❌ Baseline file not found: {baseline_file}")
        return False
    
    with open(baseline_file, 'r') as f:
        v5_data = json.load(f)
    
    print(f"📊 v5.2.0 Baseline Data:")
    basic_info = v5_data.get('basic_info', {})
    print(f"   Name: {basic_info.get('name')}")
    print(f"   Level: {basic_info.get('level')}")
    
    hit_points = basic_info.get('hit_points', {})
    print(f"   HP: {hit_points.get('current')}/{hit_points.get('maximum')}")
    
    armor_class = basic_info.get('armor_class', {})
    print(f"   AC: {armor_class.get('total')}")
    
    ability_scores = v5_data.get('ability_scores', {})
    print(f"   Ability Scores: STR {ability_scores.get('strength', {}).get('score')} DEX {ability_scores.get('dexterity', {}).get('score')} CON {ability_scores.get('constitution', {}).get('score')}")
    
    spellcasting = v5_data.get('spellcasting', {})
    if spellcasting.get('is_spellcaster'):
        print(f"   Spellcasting: DC {spellcasting.get('spell_save_dc')}, Attack +{spellcasting.get('spell_attack_bonus')}")
        print(f"   Spell Slots: {spellcasting.get('spell_slots', {})}")
    
    # Now test our new calculator
    print(f"\n🧮 v6.0.0 Calculator Results:")
    
    try:
        # Load raw data directly from Raw/ directory
        raw_file = Path(f"Raw/{character_id}.json")
        if not raw_file.exists():
            raise FileNotFoundError(f"Raw data file not found: {raw_file}")
        
        with open(raw_file, 'r') as f:
            api_response = json.load(f)
        
        # Extract character data from API response
        raw_data = api_response.get('data', {})
        
        # Calculate with new system
        calculator = CharacterCalculator()
        v6_data = calculator.calculate_complete_json(raw_data)
        
        print(f"   Name: {v6_data.get('name')}")
        print(f"   Level: {v6_data.get('level')}")
        print(f"   HP: {v6_data.get('current_hp')}/{v6_data.get('max_hp')}")
        print(f"   AC: {v6_data.get('armor_class')}")
        
        ability_scores = v6_data.get('ability_scores', {})
        print(f"   Ability Scores: STR {ability_scores.get('strength')} DEX {ability_scores.get('dexterity')} CON {ability_scores.get('constitution')}")
        
        if v6_data.get('is_spellcaster'):
            print(f"   Spellcasting: DC {v6_data.get('spell_save_dc')}, Attack +{v6_data.get('spell_attack_bonus')}")
            print(f"   Spell Slots: {v6_data.get('spell_slots')}")
        
        # Compare key values
        print(f"\n📋 Comparison:")
        
        # Compare basic info
        basic_info = v5_data.get('basic_info', {})
        name_match = basic_info.get('name') == v6_data.get('name')
        level_match = basic_info.get('level') == v6_data.get('level')
        
        print(f"   Name: {'✅' if name_match else '❌'} v5: {basic_info.get('name')} vs v6: {v6_data.get('name')}")
        print(f"   Level: {'✅' if level_match else '❌'} v5: {basic_info.get('level')} vs v6: {v6_data.get('level')}")
        
        # Compare HP
        v5_hp = basic_info.get('hit_points', {})
        v5_max_hp = v5_hp.get('maximum')
        v6_max_hp = v6_data.get('max_hp')
        hp_match = v5_max_hp == v6_max_hp
        
        print(f"   Max HP: {'✅' if hp_match else '❌'} v5: {v5_max_hp} vs v6: {v6_max_hp}")
        
        # Compare AC
        v5_ac_info = basic_info.get('armor_class', {})
        v5_ac = v5_ac_info.get('total')
        v6_ac = v6_data.get('armor_class')
        ac_match = v5_ac == v6_ac
        
        print(f"   AC: {'✅' if ac_match else '❌'} v5: {v5_ac} vs v6: {v6_ac}")
        
        # Compare ability scores
        print(f"   Ability Scores:")
        v5_abilities = v5_data.get('ability_scores', {})
        v6_abilities = v6_data.get('ability_scores', {})
        
        abilities_match = True
        for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
            v5_ability_data = v5_abilities.get(ability, {})
            v5_val = v5_ability_data.get('score') if isinstance(v5_ability_data, dict) else v5_ability_data
            v6_val = v6_abilities.get(ability)
            match = v5_val == v6_val
            if not match:
                abilities_match = False
            print(f"     {ability.upper()}: {'✅' if match else '❌'} v5: {v5_val} vs v6: {v6_val}")
        
        # Compare spellcasting if applicable
        v5_spell = v5_data.get('spellcasting', {})
        if v5_spell.get('is_spellcaster') or v6_data.get('is_spellcaster'):
            print(f"   Spellcasting:")
            
            dc_match = v5_spell.get('spell_save_dc') == v6_data.get('spell_save_dc')
            attack_match = v5_spell.get('spell_attack_bonus') == v6_data.get('spell_attack_bonus')
            
            print(f"     Save DC: {'✅' if dc_match else '❌'} v5: {v5_spell.get('spell_save_dc')} vs v6: {v6_data.get('spell_save_dc')}")
            print(f"     Attack Bonus: {'✅' if attack_match else '❌'} v5: {v5_spell.get('spell_attack_bonus')} vs v6: {v6_data.get('spell_attack_bonus')}")
        
        # Overall assessment
        key_matches = [name_match, level_match, hp_match, ac_match, abilities_match]
        total_matches = sum(key_matches)
        
        print(f"\n🎯 Overall Compatibility: {total_matches}/{len(key_matches)} key values match")
        
        if total_matches == len(key_matches):
            print(f"✅ Perfect match! New calculator produces identical results.")
        elif total_matches >= len(key_matches) - 1:
            print(f"⚠️  Nearly perfect match. Minor discrepancies to investigate.")
        else:
            print(f"❌ Significant discrepancies found. Calculator needs adjustment.")
        
        return total_matches >= len(key_matches) - 1
        
    except Exception as e:
        print(f"❌ Error running new calculator: {str(e)}")
        return False


async def main():
    """Run baseline comparison."""
    character_id = 144986992  # Vaelith Duskthorn
    
    success = await compare_character_calculations(character_id)
    
    if success:
        print(f"\n🎉 Baseline comparison successful!")
        print(f"📋 Next steps:")
        print(f"   1. The new calculator produces results very close to v5.2.0")
        print(f"   2. Any minor discrepancies should be investigated")
        print(f"   3. Manual validation data will help verify accuracy")
        return 0
    else:
        print(f"\n💥 Baseline comparison failed!")
        print(f"📋 Action needed:")
        print(f"   1. Investigate calculation discrepancies")
        print(f"   2. Fix calculator logic before proceeding")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)