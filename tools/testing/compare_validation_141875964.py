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
    validation_file = "validation_data/141875964_validation.json"
    baseline_file = "data/baseline/scraper/baseline_141875964.json"
    
    # Load files
    validation = load_json_file(validation_file)
    baseline = load_json_file(baseline_file)
    
    if not validation or not baseline:
        sys.exit(1)
    
    print("=== Character 141875964 (Baldrin Highfoot) Validation Comparison ===")
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
    
    # Speed
    val_speed = validation.get("speed")
    base_speed = baseline["basic_info"]["speed"]["walking"].get("total")
    status, details = compare_values(val_speed, base_speed, "speed")
    print(f"{'Speed':20} {status} {details}")
    total += 1
    if status == "✓":
        matches += 1
    else:
        discrepancies.append(("Speed", val_speed, base_speed))
    
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
    
    print("\n=== ABILITY MODIFIERS ===")
    for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
        val_mod = validation["ability_modifiers"].get(ability)
        base_mod = baseline["ability_scores"][ability].get("modifier")
        status, details = compare_values(val_mod, base_mod, ability)
        print(f"{ability.title() + ' Mod':20} {status} {details}")
        total += 1
        if status == "✓":
            matches += 1
        else:
            discrepancies.append((f"{ability.title()} Modifier", val_mod, base_mod))
    
    print("\n=== SPELLCASTING ===")
    
    # Is spellcaster (inferred from having spells or spell slots)
    val_caster = validation["spellcasting"].get("is_spellcaster")
    base_has_spells = len(baseline.get("spells", [])) > 0
    base_has_slots = any(baseline.get("spell_slots", {}).values()) if baseline.get("spell_slots") else False
    base_caster = base_has_spells or base_has_slots
    status, details = compare_values(val_caster, base_caster, "is_spellcaster")
    print(f"{'Is Spellcaster':20} {status} {details}")
    total += 1
    if status == "✓":
        matches += 1
    else:
        discrepancies.append(("Is Spellcaster", val_caster, base_caster))
    
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
    
    # Summary
    accuracy = (matches / total) * 100 if total > 0 else 0
    print(f"\n=== SUMMARY ===")
    print(f"Accuracy: {matches}/{total} ({accuracy:.1f}%)")
    
    if discrepancies:
        print(f"\n=== DISCREPANCIES FOR VERIFICATION ===")
        print("Please verify these values in D&D Beyond for character 141875964 (Baldrin Highfoot):")
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
    
    # Character notes
    print(f"\n=== NOTES ===")
    print(f"This is the first 2024 rules character tested.")
    print(f"Major discrepancies in ability scores suggest potential 2024 vs 2014 rule differences.")
    print(f"Constitution: {validation['ability_scores']['constitution']} vs {baseline['ability_scores']['constitution']['score']}")
    print(f"Charisma: {validation['ability_scores']['charisma']} vs {baseline['ability_scores']['charisma']['score']}")

if __name__ == "__main__":
    main()