#!/usr/bin/env python3

import json
import sys

def load_json_file(file_path):
    """Load and parse JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def test_character_baseline_issues(char_id, char_name):
    """Test a character for baseline structure issues."""
    validation_file = f"/mnt/c/Users/alc_u/Documents/DnD/CharacterScraper/validation_data/{char_id}_validation.json"
    baseline_file = f"/mnt/c/Users/alc_u/Documents/DnD/CharacterScraper/data/baseline/scraper/baseline_{char_id}.json"
    
    validation = load_json_file(validation_file)
    baseline = load_json_file(baseline_file)
    
    if not validation or not baseline:
        return
    
    print(f"=== {char_name} ({char_id}) ===")
    
    # Check proficiency bonus
    val_prof = validation.get("proficiency_bonus")
    base_prof_main = baseline.get("proficiency_bonus")  
    base_prof_meta = baseline.get("meta", {}).get("proficiency_bonus")
    
    print(f"Proficiency Bonus:")
    print(f"  Validation: {val_prof}")
    print(f"  Baseline main: {base_prof_main}")
    print(f"  Baseline meta: {base_prof_meta}")
    print(f"  Issue: {'YES' if base_prof_main is None and base_prof_meta is not None else 'NO'}")
    
    # Check spell save DC
    val_dc = validation.get("spellcasting", {}).get("spell_save_dc")
    base_dc_main = baseline.get("spellcasting", {}).get("spell_save_dc")
    # Calculate expected DC
    prof_bonus = base_prof_meta or 2
    ability_mod = baseline.get("ability_scores", {}).get("intelligence", {}).get("modifier", 0) or \
                  baseline.get("ability_scores", {}).get("wisdom", {}).get("modifier", 0) or \
                  baseline.get("ability_scores", {}).get("charisma", {}).get("modifier", 0)
    expected_dc = 8 + prof_bonus + ability_mod if val_dc else None
    
    print(f"Spell Save DC:")
    print(f"  Validation: {val_dc}")
    print(f"  Baseline main: {base_dc_main}")
    print(f"  Expected (8+prof+mod): {expected_dc}")
    print(f"  Issue: {'YES' if val_dc and base_dc_main is None else 'NO'}")
    
    # Check spell count
    val_spells = validation.get("spellcasting", {}).get("total_spells", 0)
    base_spells = len(baseline.get("spells", []))
    
    print(f"Spell Count:")
    print(f"  Validation: {val_spells}")
    print(f"  Baseline: {base_spells}")
    print(f"  Issue: {'YES' if val_spells > base_spells and val_spells > 2 else 'NO'}")
    
    print()

def main():
    print("=== BASELINE STRUCTURE CONSISTENCY TEST ===")
    print()
    
    # Test multiple characters
    characters = [
        ("105635812", "Faerah (100% accuracy)"),
        ("144986992", "Vaelith (91.7% accuracy)"), 
        ("145079040", "Thuldus (83.3% accuracy)"),
        ("147061783", "ZuB (75.0% accuracy)")
    ]
    
    for char_id, char_name in characters:
        test_character_baseline_issues(char_id, char_name)
    
    print("=== CONCLUSION ===")
    print("If ALL characters show the same baseline issues, then:")
    print("1. The comparison scripts have been using wrong field paths")
    print("2. The accuracy percentages reported are all incorrect")
    print("3. The baseline export structure needs fixing across the board")

if __name__ == "__main__":
    main()