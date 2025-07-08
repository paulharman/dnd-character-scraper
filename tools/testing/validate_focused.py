#!/usr/bin/env python3
"""
Focused validation on specific critical fields for a few characters.
"""

import subprocess
import json
from pathlib import Path

def validate_critical_fields(character_id: int):
    """Validate critical fields for one character."""
    print(f"\n=== Character {character_id} ===")
    
    # Run scraper
    actual_path = f"/tmp/focused_{character_id}.json"
    expected_path = f"/mnt/c/Users/alc_u/Documents/DnD/CharacterScraper/data/baseline/scraper/baseline_{character_id}.json"
    
    try:
        result = subprocess.run([
            "python3", "enhanced_dnd_scraper.py", str(character_id), 
            "--output", actual_path
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"❌ Scraper failed: {result.stderr}")
            return
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Load data
    try:
        with open(expected_path) as f:
            expected = json.load(f)
        with open(actual_path) as f:
            actual = json.load(f)
    except Exception as e:
        print(f"❌ File error: {e}")
        return
    
    # Check critical fields
    checks = [
        ("Name", expected['basic_info']['name'], actual['basic_info']['name']),
        ("Level", expected['basic_info']['level'], actual['basic_info']['level']),
        ("Max HP", expected['basic_info']['hit_points']['maximum'], actual['basic_info']['hit_points']['maximum']),
        ("HP Base", expected['basic_info']['hit_points']['base'], actual['basic_info']['hit_points']['base']),
        ("HP Con Bonus", expected['basic_info']['hit_points']['constitution_bonus'], actual['basic_info']['hit_points']['constitution_bonus']),
        ("AC Total", expected['basic_info']['armor_class']['total'], actual['basic_info']['armor_class']['total']),
        ("STR Score", expected['ability_scores']['strength']['score'], actual['ability_scores']['strength']['score']),
        ("STR Save", expected['ability_scores']['strength']['save_bonus'], actual['ability_scores']['strength']['save_bonus']),
        ("CON Score", expected['ability_scores']['constitution']['score'], actual['ability_scores']['constitution']['score']),
        ("CON Save", expected['ability_scores']['constitution']['save_bonus'], actual['ability_scores']['constitution']['save_bonus']),
        ("WIS Score", expected['ability_scores']['wisdom']['score'], actual['ability_scores']['wisdom']['score']),
        ("WIS Save", expected['ability_scores']['wisdom']['save_bonus'], actual['ability_scores']['wisdom']['save_bonus']),
    ]
    
    # Add spell slot checks if caster
    if 'spell_slots' in expected and 'level_1' in expected['spell_slots']:
        checks.append(("Spell L1", expected['spell_slots']['level_1'], actual['spell_slots']['level_1']))
    if 'spell_slots' in expected and 'level_2' in expected['spell_slots']:
        checks.append(("Spell L2", expected['spell_slots']['level_2'], actual['spell_slots']['level_2']))
    
    # Compare
    mismatches = []
    matches = []
    
    for name, exp, act in checks:
        if exp == act:
            matches.append(f"✅ {name}: {act}")
        else:
            mismatches.append(f"❌ {name}: expected {exp}, got {act}")
    
    # Report
    if mismatches:
        print(f"Character {character_id}: {len(mismatches)} mismatches, {len(matches)} matches")
        for m in mismatches[:8]:  # Show first 8 mismatches
            print(f"  {m}")
        if len(mismatches) > 8:
            print(f"  ... and {len(mismatches) - 8} more")
    else:
        print(f"✅ Character {character_id}: All {len(matches)} critical fields match!")

def main():
    # Test a few key characters
    test_chars = [144986992, 29682199, 145081718]  # Start with these
    
    for i, char_id in enumerate(test_chars):
        validate_critical_fields(char_id)
        
        # Wait between characters
        if i < len(test_chars) - 1:
            print("⏱️  Waiting 30 seconds...")
            import time
            time.sleep(30)

if __name__ == "__main__":
    main()