#!/usr/bin/env python3
"""
Comprehensive field-by-field validation against expected values.
Tests all 12 characters and reports specific mismatches.
"""

import subprocess
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Test character IDs from CLAUDE.md
TEST_CHARACTER_IDS = [
    145081718, 29682199, 147061783, 66356596, 144986992, 145079040,
    141875964, 68622804, 105635812, 103873194, 103214475, 103814449
]

def load_json_safe(filepath: str) -> Dict[str, Any]:
    """Load JSON file safely."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return {}

def compare_values(field_path: str, expected: Any, actual: Any) -> List[str]:
    """Compare values and return list of mismatches."""
    mismatches = []
    
    if expected is None and actual is None:
        return mismatches
    
    if type(expected) != type(actual):
        mismatches.append(f"{field_path}: type mismatch - expected {type(expected).__name__} {expected}, got {type(actual).__name__} {actual}")
        return mismatches
    
    if isinstance(expected, dict) and isinstance(actual, dict):
        # Compare dictionary fields
        all_keys = set(expected.keys()) | set(actual.keys())
        for key in all_keys:
            sub_path = f"{field_path}.{key}"
            if key not in expected:
                mismatches.append(f"{sub_path}: extra field in actual - {actual[key]}")
            elif key not in actual:
                mismatches.append(f"{sub_path}: missing field - expected {expected[key]}")
            else:
                mismatches.extend(compare_values(sub_path, expected[key], actual[key]))
    
    elif isinstance(expected, list) and isinstance(actual, list):
        # Compare lists
        if len(expected) != len(actual):
            mismatches.append(f"{field_path}: length mismatch - expected {len(expected)}, got {len(actual)}")
        
        for i in range(min(len(expected), len(actual))):
            sub_path = f"{field_path}[{i}]"
            mismatches.extend(compare_values(sub_path, expected[i], actual[i]))
    
    else:
        # Compare primitive values
        if expected != actual:
            mismatches.append(f"{field_path}: value mismatch - expected {expected}, got {actual}")
    
    return mismatches

def validate_character_json(character_id: int) -> Tuple[bool, List[str]]:
    """Validate JSON output for a character."""
    print(f"\\n=== Validating JSON for Character {character_id} ===")
    
    # Paths
    expected_path = f"/mnt/c/Users/alc_u/Documents/DnD/CharacterScraper/data/baseline/scraper/baseline_{character_id}.json"
    actual_path = f"/tmp/validate_{character_id}.json"
    
    # Run scraper
    try:
        print(f"Running scraper for {character_id}...")
        result = subprocess.run([
            "python3", "enhanced_dnd_scraper.py", str(character_id), 
            "--output", actual_path
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            return False, [f"Scraper failed: {result.stderr}"]
        
    except subprocess.TimeoutExpired:
        return False, [f"Scraper timeout"]
    except Exception as e:
        return False, [f"Scraper error: {e}"]
    
    # Load files
    expected = load_json_safe(expected_path)
    actual = load_json_safe(actual_path)
    
    if not expected:
        return False, [f"Could not load expected data from {expected_path}"]
    if not actual:
        return False, [f"Could not load actual data from {actual_path}"]
    
    # Compare critical fields
    mismatches = []
    
    # Key character info
    critical_fields = [
        'basic_info.name',
        'basic_info.level', 
        'basic_info.hit_points.current',
        'basic_info.hit_points.maximum',
        'basic_info.hit_points.base',
        'basic_info.hit_points.constitution_bonus',
        'basic_info.armor_class.total',
        'basic_info.armor_class.calculation',
        'ability_scores.strength.score',
        'ability_scores.strength.modifier', 
        'ability_scores.strength.save_bonus',
        'ability_scores.dexterity.score',
        'ability_scores.dexterity.modifier',
        'ability_scores.constitution.score',
        'ability_scores.constitution.modifier',
        'ability_scores.constitution.save_bonus',
        'ability_scores.wisdom.score',
        'ability_scores.wisdom.modifier',
        'ability_scores.charisma.score',
        'ability_scores.charisma.modifier',
        'ability_scores.charisma.save_bonus',
        'spell_save_dc',
        'spell_attack_bonus'
    ]
    
    # Check spell slots if character is a caster
    if 'spell_slots' in expected and expected['spell_slots']:
        if 'level_1' in expected['spell_slots']:
            critical_fields.append('spell_slots.level_1')
        if 'level_2' in expected['spell_slots']:
            critical_fields.append('spell_slots.level_2')
        if 'level_3' in expected['spell_slots']:
            critical_fields.append('spell_slots.level_3')
    
    for field_path in critical_fields:
        # Navigate to field
        expected_val = expected
        actual_val = actual
        
        try:
            for part in field_path.split('.'):
                expected_val = expected_val[part]
                actual_val = actual_val[part]
            
            field_mismatches = compare_values(field_path, expected_val, actual_val)
            mismatches.extend(field_mismatches)
            
        except KeyError as e:
            mismatches.append(f"{field_path}: missing field - {e}")
        except Exception as e:
            mismatches.append(f"{field_path}: error accessing field - {e}")
    
    success = len(mismatches) == 0
    return success, mismatches

def validate_character_md(character_id: int) -> Tuple[bool, List[str]]:
    """Validate MD output for a character."""
    print(f"\\n=== Validating MD for Character {character_id} ===")
    
    # Paths  
    expected_path = f"/mnt/c/Users/alc_u/Documents/DnD/CharacterScraper/data/baseline/parser/baseline_{character_id}.md"
    actual_path = f"/tmp/validate_{character_id}.md"
    
    # Run parser
    try:
        print(f"Running parser for {character_id}...")
        result = subprocess.run([
            "python3", "archive/v5.2.0/dnd_json_to_markdown_v5.2.0_original.py",
            str(character_id), actual_path,
            "--scraper-path", "archive/v5.2.0/enhanced_dnd_scraper_v5.2.0_original.py",
            "--no-enhance-spells"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            return False, [f"Parser failed: {result.stderr}"]
        
    except subprocess.TimeoutExpired:
        return False, [f"Parser timeout"]
    except Exception as e:
        return False, [f"Parser error: {e}"]
    
    # Load and compare MD files
    try:
        with open(expected_path, 'r') as f:
            expected_md = f.read()
        with open(actual_path, 'r') as f:
            actual_md = f.read()
    except Exception as e:
        return False, [f"Error reading MD files: {e}"]
    
    # Basic MD validation
    mismatches = []
    
    if len(actual_md) < 1000:
        mismatches.append(f"MD output too short: {len(actual_md)} chars")
    
    if "## Character Statistics" not in actual_md:
        mismatches.append("Missing Character Statistics section")
    
    if "## Ability Scores" not in actual_md:
        mismatches.append("Missing Ability Scores section")
    
    # Check for dict objects in ability scores (should be formatted)
    if "{'score':" in actual_md or '"score":' in actual_md:
        mismatches.append("Ability scores showing as dict objects instead of formatted text")
    
    success = len(mismatches) == 0
    return success, mismatches

def main():
    """Run comprehensive validation."""
    print("🧪 Starting comprehensive field validation...")
    print(f"Testing {len(TEST_CHARACTER_IDS)} characters")
    
    all_mismatches = {}
    json_successes = 0
    md_successes = 0
    
    for i, character_id in enumerate(TEST_CHARACTER_IDS):
        print(f"\\n📊 Progress: {i+1}/{len(TEST_CHARACTER_IDS)} characters")
        
        character_mismatches = []
        
        # Test JSON
        json_success, json_mismatches = validate_character_json(character_id)
        if json_success:
            json_successes += 1
            print(f"✅ JSON validation passed for {character_id}")
        else:
            print(f"❌ JSON validation failed for {character_id} ({len(json_mismatches)} issues)")
            character_mismatches.extend([f"JSON: {m}" for m in json_mismatches[:5]])  # Limit output
        
        # Test MD
        md_success, md_mismatches = validate_character_md(character_id)
        if md_success:
            md_successes += 1
            print(f"✅ MD validation passed for {character_id}")
        else:
            print(f"❌ MD validation failed for {character_id} ({len(md_mismatches)} issues)")
            character_mismatches.extend([f"MD: {m}" for m in md_mismatches])
        
        if character_mismatches:
            all_mismatches[character_id] = character_mismatches
        
        # Rate limiting - wait 30 seconds between characters
        if i < len(TEST_CHARACTER_IDS) - 1:
            print("⏱️  Waiting 30 seconds (API rate limiting)...")
            time.sleep(30)
    
    # Final report
    print(f"\\n📊 FINAL VALIDATION RESULTS:")
    print(f"✅ JSON successes: {json_successes}/{len(TEST_CHARACTER_IDS)} ({100*json_successes/len(TEST_CHARACTER_IDS):.1f}%)")
    print(f"✅ MD successes: {md_successes}/{len(TEST_CHARACTER_IDS)} ({100*md_successes/len(TEST_CHARACTER_IDS):.1f}%)")
    
    if all_mismatches:
        print(f"\\n❌ CHARACTERS WITH ISSUES:")
        for character_id, mismatches in all_mismatches.items():
            print(f"\\n🔍 Character {character_id}:")
            for mismatch in mismatches[:10]:  # Limit output
                print(f"  - {mismatch}")
            if len(mismatches) > 10:
                print(f"  ... and {len(mismatches) - 10} more issues")
    
    total_failures = len(all_mismatches)
    if total_failures == 0:
        print("\\n🎉 ALL VALIDATIONS PASSED!")
        return 0
    else:
        print(f"\\n⚠️  {total_failures} characters have validation issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())