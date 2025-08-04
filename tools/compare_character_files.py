#!/usr/bin/env python3
"""
Comprehensive D&D Beyond character comparison tool
Compares two character JSON files and identifies all changes
"""

import json
import sys

def load_json_file(file_path):
    """Load JSON file and handle errors"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def compare_ability_scores(old_data, new_data):
    """Compare ability scores between old and new character data"""
    print("\n=== ABILITY SCORE CHANGES ===")
    
    old_abilities = old_data.get('abilities', {}).get('ability_scores', {})
    new_abilities = new_data.get('abilities', {}).get('ability_scores', {})
    
    abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
    
    changes_found = False
    for ability in abilities:
        old_score = old_abilities.get(ability, {}).get('score', 'N/A')
        new_score = new_abilities.get(ability, {}).get('score', 'N/A')
        
        if old_score != new_score:
            print(f"  {ability.upper()}: {old_score} → {new_score}")
            changes_found = True
    
    if not changes_found:
        print("  No ability score changes detected")

def compare_proficiency_bonus(old_data, new_data):
    """Compare proficiency bonus"""
    print("\n=== PROFICIENCY BONUS CHANGES ===")
    
    # Try multiple locations for proficiency bonus
    old_prof = (old_data.get('basic_info', {}).get('proficiency_bonus') or 
                old_data.get('proficiencies', {}).get('proficiency_bonus') or
                old_data.get('abilities', {}).get('proficiency_bonus'))
    new_prof = (new_data.get('basic_info', {}).get('proficiency_bonus') or 
                new_data.get('proficiencies', {}).get('proficiency_bonus') or
                new_data.get('abilities', {}).get('proficiency_bonus'))
    
    if old_prof != new_prof:
        print(f"  Proficiency Bonus: {old_prof} → {new_prof}")
    else:
        print(f"  No proficiency bonus changes (both: {old_prof})")

def compare_expertise_bonus(old_data, new_data):
    """Compare expertise bonuses which might change due to proficiency increases"""
    print("\n=== EXPERTISE BONUS CHANGES ===")
    
    old_skills = old_data.get('abilities', {}).get('skills', [])
    new_skills = new_data.get('abilities', {}).get('skills', [])
    
    changes_found = False
    
    # Create lookup dictionaries by skill name
    old_skill_dict = {skill.get('name'): skill for skill in old_skills if skill.get('name')}
    new_skill_dict = {skill.get('name'): skill for skill in new_skills if skill.get('name')}
    
    for skill_name in old_skill_dict:
        if skill_name in new_skill_dict:
            old_skill = old_skill_dict[skill_name]
            new_skill = new_skill_dict[skill_name]
            
            old_expertise = old_skill.get('expertise_bonus', 0)
            new_expertise = new_skill.get('expertise_bonus', 0)
            old_total = old_skill.get('total_bonus', 0)
            new_total = new_skill.get('total_bonus', 0)
            
            if old_expertise != new_expertise or old_total != new_total:
                print(f"  {skill_name}: expertise {old_expertise}→{new_expertise}, total {old_total}→{new_total}")
                changes_found = True
    
    if not changes_found:
        print("  No expertise/skill bonus changes detected")

def compare_spell_attack_and_dc(old_data, new_data):
    """Compare spell attack bonus and save DC"""
    print("\n=== SPELL ATTACK & SAVE DC CHANGES ===")
    
    old_spell_attack = old_data.get('spellcasting', {}).get('spell_attack_bonus', 'N/A')
    new_spell_attack = new_data.get('spellcasting', {}).get('spell_attack_bonus', 'N/A')
    
    old_spell_dc = old_data.get('spellcasting', {}).get('spell_save_dc', 'N/A')
    new_spell_dc = new_data.get('spellcasting', {}).get('spell_save_dc', 'N/A')
    
    if old_spell_attack != new_spell_attack:
        print(f"  Spell Attack Bonus: {old_spell_attack} → {new_spell_attack}")
    
    if old_spell_dc != new_spell_dc:
        print(f"  Spell Save DC: {old_spell_dc} → {new_spell_dc}")

def main():
    old_file = "/mnt/c/Users/alc_u/Documents/DnD/CharacterScraper - Kiro/character_data/scraper/character_143359582_2025-07-26T15-23-25.138290.json"
    new_file = "/mnt/c/Users/alc_u/Documents/DnD/CharacterScraper - Kiro/character_data/scraper/character_143359582_2025-07-26T21-00-22.744790.json"
    
    print("Loading character files...")
    old_data = load_json_file(old_file)
    new_data = load_json_file(new_file)
    
    if not old_data or not new_data:
        print("Failed to load one or both files")
        return
    
    print("Character Comparison Report")
    print("=" * 50)
    
    # Basic info changes
    print("\n=== BASIC CHARACTER INFO CHANGES ===")
    old_level = old_data.get('character_info', {}).get('level', 'N/A')
    new_level = new_data.get('character_info', {}).get('level', 'N/A')
    print(f"  Level: {old_level} → {new_level}")
    
    old_hp = old_data.get('combat', {}).get('hit_points', {}).get('maximum', 'N/A')
    new_hp = new_data.get('combat', {}).get('hit_points', {}).get('maximum', 'N/A')
    print(f"  Max HP: {old_hp} → {new_hp}")
    
    # Compare ability scores
    compare_ability_scores(old_data, new_data)
    
    # Compare proficiency bonus
    compare_proficiency_bonus(old_data, new_data)
    
    # Compare expertise bonuses
    compare_expertise_bonus(old_data, new_data)
    
    # Compare spell attack and DC
    compare_spell_attack_and_dc(old_data, new_data)
    
    # Spell slots comparison
    print("\n=== SPELL SLOT CHANGES ===")
    old_slots = old_data.get('spellcasting', {}).get('spell_slots', [])
    new_slots = new_data.get('spellcasting', {}).get('spell_slots', [])
    
    for i, (old_slot, new_slot) in enumerate(zip(old_slots, new_slots)):
        if old_slot != new_slot:
            print(f"  Level {i+1} slots: {old_slot} → {new_slot}")

if __name__ == "__main__":
    main()