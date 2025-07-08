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
    validation_file = "validation_data/145081718_validation.json"
    baseline_file = "data/baseline/scraper/baseline_145081718.json"
    
    # Load files
    validation = load_json_file(validation_file)
    baseline = load_json_file(baseline_file)
    
    if not validation or not baseline:
        sys.exit(1)
    
    print("=== Character 145081718 (Ilarion Veles) Validation Comparison ===")
    print(f"Character: {validation['name']} (Level {validation['level']} {validation['classes'][0]['name']})")
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
    
    # Initiative
    val_init = validation.get("initiative")
    base_init = baseline["basic_info"]["initiative"].get("total")
    status, details = compare_values(val_init, base_init, "initiative")
    print(f"{'Initiative':20} {status} {details}")
    total += 1
    if status == "✓":
        matches += 1
    else:
        discrepancies.append(("Initiative", val_init, base_init))
    
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
    
    # Summary
    accuracy = (matches / total) * 100 if total > 0 else 0
    print(f"\n=== SUMMARY ===")
    print(f"Accuracy: {matches}/{total} ({accuracy:.1f}%)")
    
    if discrepancies:
        print(f"\n=== DISCREPANCIES FOR VERIFICATION ===")
        print("Please verify these values in D&D Beyond for character 145081718 (Ilarion Veles):")
        for i, (field, val_val, base_val) in enumerate(discrepancies, 1):
            print(f"{i}. {field}: Validation shows {val_val}, Baseline shows {base_val}")
    
    print(f"\n=== SPELL LIST COMPARISON ===")
    val_spells = set(validation.get("key_spells", []))
    base_spells = set(baseline.get("spells", []))
    
    print(f"Validation spells ({len(val_spells)}): {sorted(val_spells)}")
    print(f"Baseline spells ({len(base_spells)}): {sorted(base_spells)}")
    
    if val_spells == base_spells:
        print("✓ Spell lists match perfectly")
    else:
        missing_in_validation = base_spells - val_spells
        extra_in_validation = val_spells - base_spells
        if missing_in_validation:
            print(f"✗ Missing in validation: {sorted(missing_in_validation)}")
        if extra_in_validation:
            print(f"✗ Extra in validation: {sorted(extra_in_validation)}")
    
    print(f"\n=== WIZARD-SPECIFIC NOTES ===")
    print("This is a 2024 Wizard character - excellent test case for:")
    print("1. Ritual spell parsing (4 ritual spells mentioned)")
    print("2. Free spell casting (Detect Magic once per LR)")
    print("3. Magic Initiate feat integration")
    print("4. 2024 rule handling with High Elf racial features")

if __name__ == "__main__":
    main()