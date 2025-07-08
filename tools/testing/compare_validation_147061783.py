#!/usr/bin/env python3

import json
import sys
from pathlib import Path

def load_json_file(file_path):
    """Load and parse JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def compare_values(validation_val, baseline_val, field_name):
    """Compare two values and return comparison result."""
    if validation_val == baseline_val:
        return "✓", "Match"
    else:
        return "✗", f"Validation: {validation_val}, Baseline: {baseline_val}"

def main():
    # File paths
    validation_file = "/mnt/c/Users/alc_u/Documents/DnD/CharacterScraper/validation_data/147061783_validation.json"
    baseline_file = "/mnt/c/Users/alc_u/Documents/DnD/CharacterScraper/data/baseline/scraper/baseline_147061783.json"
    
    # Load files
    validation = load_json_file(validation_file)
    baseline = load_json_file(baseline_file)
    
    if not validation or not baseline:
        sys.exit(1)
    
    print("=== Character 147061783 (ZuB Public Demo) Validation Comparison ===")
    print(f"Character: {validation['name']} (Level {validation['level']} {validation['classes'][0]['name']})")
    print(f"Subclass: {validation['classes'][0]['subclass']}")
    print(f"2024 Rules: {validation['is_2024_rules']}")
    print()
    
    # Track matches and total comparisons
    matches = 0
    total = 0
    discrepancies = []
    
    # Basic info comparison
    print("=== BASIC STATS ===")
    
    # Level
    val_level = validation.get("level")
    base_level = baseline["basic_info"].get("level")
    status, details = compare_values(val_level, base_level, "level")
    print(f"{'Level':20} {status} {details}")
    total += 1
    if status == "✓":
        matches += 1
    else:
        discrepancies.append(("Level", val_level, base_level))
    
    # AC
    val_ac = validation.get("armor_class")
    base_ac = baseline["basic_info"]["armor_class"].get("total")
    status, details = compare_values(val_ac, base_ac, "armor_class")
    print(f"{'Armor Class':20} {status} {details}")
    total += 1
    if status == "✓":
        matches += 1
    else:
        discrepancies.append(("Armor Class", val_ac, base_ac))
    
    # HP
    val_hp = validation.get("max_hp")
    base_hp = baseline["basic_info"]["hit_points"].get("maximum")
    status, details = compare_values(val_hp, base_hp, "max_hp")
    print(f"{'Max HP':20} {status} {details}")
    total += 1
    if status == "✓":
        matches += 1
    else:
        discrepancies.append(("Max HP", val_hp, base_hp))
    
    # Proficiency Bonus
    val_prof = validation.get("proficiency_bonus")
    base_prof = baseline.get("proficiency_bonus")
    status, details = compare_values(val_prof, base_prof, "proficiency_bonus")
    print(f"{'Proficiency Bonus':20} {status} {details}")
    total += 1
    if status == "✓":
        matches += 1
    else:
        discrepancies.append(("Proficiency Bonus", val_prof, base_prof))
    
    print("\n=== ABILITY SCORES ===")
    for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
        val_score = validation["ability_scores"].get(ability)
        base_score = baseline["ability_scores"][ability].get("score")
        status, details = compare_values(val_score, base_score, ability)
        print(f"{ability.title():20} {status} {details}")
        total += 1
        if status == "✓":
            matches += 1
        else:
            discrepancies.append((f"{ability.title()} Score", val_score, base_score))
    
    print("\n=== SPELLCASTING ===")
    
    # Total spells
    val_total_spells = validation["spellcasting"].get("total_spells")
    base_total_spells = len(baseline.get("spells", []))
    status, details = compare_values(val_total_spells, base_total_spells, "total_spells")
    print(f"{'Total Spells':20} {status} {details}")
    total += 1
    if status == "✓":
        matches += 1
    else:
        discrepancies.append(("Total Spells", val_total_spells, base_total_spells))
    
    # Spell save DC
    val_dc = validation["spellcasting"].get("spell_save_dc")
    base_dc = baseline.get("spellcasting", {}).get("spell_save_dc")
    status, details = compare_values(val_dc, base_dc, "spell_save_dc")
    print(f"{'Spell Save DC':20} {status} {details}")
    total += 1
    if status == "✓":
        matches += 1
    else:
        discrepancies.append(("Spell Save DC", val_dc, base_dc))
    
    # High level spell slots
    print("\n=== HIGH LEVEL SPELL SLOTS ===")
    for level in [6, 7, 8, 9]:
        val_slots = validation["spellcasting"].get(f"spell_slots_level_{level}")
        base_slots = baseline.get("spell_slots", {}).get("regular_slots", {}).get(f"level_{level}")
        status, details = compare_values(val_slots, base_slots, f"level_{level}")
        print(f"{'Level ' + str(level) + ' Slots':20} {status} {details}")
        total += 1
        if status == "✓":
            matches += 1
        else:
            discrepancies.append((f"Level {level} Slots", val_slots, base_slots))
    
    # Summary
    accuracy = (matches / total) * 100 if total > 0 else 0
    print(f"\n=== SUMMARY ===")
    print(f"Accuracy: {matches}/{total} ({accuracy:.1f}%)")
    
    if discrepancies:
        print(f"\n=== DISCREPANCIES FOR VERIFICATION ===")
        print("Please verify these values in D&D Beyond for character 147061783 (ZuB Public Demo):")
        for i, (field, val_val, base_val) in enumerate(discrepancies, 1):
            print(f"{i}. {field}: Validation shows {val_val}, Baseline shows {base_val}")
    
    print(f"\n=== HIGH-LEVEL WIZARD NOTES ===")
    print("This is a Level 15 Conjuration Wizard - excellent test case for:")
    print("1. High-level spell slot progression (6th-8th level slots)")
    print("2. Subclass feature parsing (School of Conjuration)")
    print("3. Variant Human feat handling (Lucky, Telekinetic)")
    print("4. Large spellbook (30 total spells)")
    print("5. Arcane Recovery at high levels")

if __name__ == "__main__":
    main()