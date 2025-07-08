#!/usr/bin/env python3
"""
Character Validation Template Creator
Creates validation templates for specific character IDs and helps compare scraper output with ground truth data.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

def create_template_for_character(character_id: int, output_dir: str = "validation_data") -> str:
    """Create a validation template for a specific character ID."""
    
    # Load the base template
    with open("character_validation_template.json", 'r') as f:
        template = json.load(f)
    
    # Customize for this character
    template["character_id"] = character_id
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Save character-specific template
    output_file = f"{output_dir}/{character_id}_validation.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    return output_file

def create_all_templates(character_ids: List[int]) -> None:
    """Create validation templates for all character IDs from CLAUDE.md."""
    
    print(f"Creating validation templates for {len(character_ids)} characters...")
    
    created_files = []
    for char_id in character_ids:
        output_file = create_template_for_character(char_id)
        created_files.append(output_file)
        print(f"✓ Created: {output_file}")
    
    print(f"\nCreated {len(created_files)} validation templates in validation_data/")
    print("\nNext steps:")
    print("1. Open each template file")
    print("2. Fill in the values by checking the D&D Beyond character sheet")
    print("3. Use compare_validation.py to check scraper accuracy")

def compare_with_scraper_output(validation_file: str, scraper_output_file: str) -> Dict[str, Any]:
    """Compare validation data with scraper output to find discrepancies."""
    
    with open(validation_file, 'r') as f:
        validation_data = json.load(f)
    
    with open(scraper_output_file, 'r') as f:
        scraper_data = json.load(f)
    
    discrepancies = []
    matches = []
    
    # Compare basic info
    char_id = validation_data["character_id"]
    
    # Name
    expected_name = validation_data["name"]
    actual_name = scraper_data.get("basic_info", {}).get("name", "")
    if expected_name and expected_name != actual_name:
        discrepancies.append({
            "field": "name",
            "expected": expected_name,
            "actual": actual_name
        })
    elif expected_name == actual_name:
        matches.append("name")
    
    # Level
    expected_level = validation_data["level"]
    actual_level = scraper_data.get("basic_info", {}).get("level", 0)
    if expected_level != actual_level:
        discrepancies.append({
            "field": "level",
            "expected": expected_level,
            "actual": actual_level
        })
    else:
        matches.append("level")
    
    # Ability scores
    for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
        expected_score = validation_data["ability_scores"][ability]
        expected_mod = validation_data["ability_modifiers"][ability]
        
        actual_score = scraper_data.get("ability_scores", {}).get(ability, {}).get("score", 0)
        actual_mod = scraper_data.get("ability_scores", {}).get(ability, {}).get("modifier", 0)
        
        if expected_score and expected_score != actual_score:
            discrepancies.append({
                "field": f"ability_scores.{ability}",
                "expected": expected_score,
                "actual": actual_score
            })
        elif expected_score == actual_score:
            matches.append(f"ability_scores.{ability}")
            
        if expected_mod != actual_mod:
            discrepancies.append({
                "field": f"ability_modifiers.{ability}",
                "expected": expected_mod,
                "actual": actual_mod
            })
        else:
            matches.append(f"ability_modifiers.{ability}")
    
    # Key calculated values
    calc_checks = [
        ("proficiency_bonus", validation_data.get("proficiency_bonus", 0), scraper_data.get("meta", {}).get("proficiency_bonus", 0)),
        ("armor_class", validation_data.get("armor_class", 0), scraper_data.get("basic_info", {}).get("armor_class", 0)),
        ("max_hp", validation_data.get("max_hp", 0), scraper_data.get("basic_info", {}).get("max_hp", 0)),
        ("initiative", validation_data.get("initiative", 0), scraper_data.get("basic_info", {}).get("initiative", "").replace("+", "")),
        ("spell_save_dc", validation_data.get("spellcasting", {}).get("spell_save_dc", 0), scraper_data.get("spells", {}).get("spell_save_dc", 0)),
        ("total_spells", validation_data.get("spellcasting", {}).get("total_spells", 0), scraper_data.get("spells", {}).get("spell_count", 0))
    ]
    
    for field_name, expected, actual in calc_checks:
        # Convert string numbers for initiative
        try:
            if isinstance(actual, str):
                actual = int(actual) if actual.lstrip('-').isdigit() else 0
        except:
            actual = 0
            
        if expected and expected != actual:
            discrepancies.append({
                "field": field_name,
                "expected": expected,
                "actual": actual
            })
        elif expected == actual and expected != 0:
            matches.append(field_name)
    
    return {
        "character_id": char_id,
        "total_checks": len(matches) + len(discrepancies),
        "matches": len(matches),
        "discrepancies": len(discrepancies),
        "match_fields": matches,
        "discrepancy_details": discrepancies
    }

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Create and manage character validation templates")
    parser.add_argument("--create", action="store_true", help="Create templates for all characters")
    parser.add_argument("--character-id", type=int, help="Create template for specific character")
    parser.add_argument("--compare", help="Compare validation file with scraper output")
    parser.add_argument("--scraper-output", help="Scraper output file for comparison")
    
    args = parser.parse_args()
    
    if args.create:
        # Character IDs from CLAUDE.md
        character_ids = [
            145081718, 29682199, 147061783, 66356596, 144986992, 145079040,
            141875964, 68622804, 105635812, 103873194, 103214475, 103814449
        ]
        create_all_templates(character_ids)
        
    elif args.character_id:
        output_file = create_template_for_character(args.character_id)
        print(f"Created validation template: {output_file}")
        
    elif args.compare and args.scraper_output:
        result = compare_with_scraper_output(args.compare, args.scraper_output)
        
        print(f"\nValidation Results for Character {result['character_id']}:")
        print(f"Total checks: {result['total_checks']}")
        print(f"Matches: {result['matches']} ({result['matches']/result['total_checks']*100:.1f}%)")
        print(f"Discrepancies: {result['discrepancies']}")
        
        if result['discrepancy_details']:
            print("\nDiscrepancies found:")
            for disc in result['discrepancy_details']:
                print(f"  {disc['field']}: expected {disc['expected']}, got {disc['actual']}")
        else:
            print("\n✓ All checks passed!")
            
    else:
        parser.print_help()

if __name__ == "__main__":
    main()