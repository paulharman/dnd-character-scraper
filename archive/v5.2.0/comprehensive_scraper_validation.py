#!/usr/bin/env python3
"""
Comprehensive Scraper Validation Script
Compares scraper JSON output against manual validation data for all 12 characters
"""

import json
import os
from pathlib import Path

def load_json_file(file_path):
    """Load and parse JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def safe_get(data, path, default="NOT_FOUND"):
    """Safely get nested dictionary values using dot notation."""
    if not isinstance(path, str):
        return path  # Return the value directly if it's not a path string
        
    keys = path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

def compare_character(char_id, char_name):
    """Compare scraper output against validation data for a single character."""
    
    # Load files
    validation_file = f"/mnt/c/Users/alc_u/Documents/DnD/CharacterScraper/validation_data/{char_id}_validation.json"
    scraper_file = f"/mnt/c/Users/alc_u/Documents/DnD/CharacterScraper/archive/v5.2.0/validation_scraper_{char_id}.json"
    
    validation = load_json_file(validation_file)
    scraper = load_json_file(scraper_file)
    
    if not validation or not scraper:
        return None
        
    results = {
        "character_id": char_id,
        "name": char_name,
        "matches": 0,
        "total": 0,
        "errors": [],
        "discrepancies": []
    }
    
    # Define comparisons
    comparisons = [
        ("Level", "level", "basic_info.level"),
        ("AC", "armor_class", "basic_info.armor_class.total"),
        ("Max HP", "max_hp", "basic_info.hit_points.maximum"),
        ("Initiative", "initiative", "basic_info.initiative.total"),
        ("Speed", "speed", "basic_info.speed.walking.total"),
        ("STR", "ability_scores.strength", "ability_scores.strength.score"),
        ("DEX", "ability_scores.dexterity", "ability_scores.dexterity.score"),
        ("CON", "ability_scores.constitution", "ability_scores.constitution.score"),
        ("INT", "ability_scores.intelligence", "ability_scores.intelligence.score"),
        ("WIS", "ability_scores.wisdom", "ability_scores.wisdom.score"),
        ("CHA", "ability_scores.charisma", "ability_scores.charisma.score"),
    ]
    
    # Add spellcasting comparisons if character is a spellcaster
    if validation.get("spellcasting", {}).get("is_spellcaster"):
        # Count total spells from scraper
        scraper_spells = scraper.get("spells", {})
        if isinstance(scraper_spells, dict):
            scraper_spell_count = sum(len(spell_list) for spell_list in scraper_spells.values() if isinstance(spell_list, list))
        else:
            scraper_spell_count = len(scraper_spells) if isinstance(scraper_spells, list) else 0
            
        # Get validation spell count
        val_spell_count = validation.get("spellcasting", {}).get("total_spells")
        
        # Create manual comparison for spells (not using safe_get)
        results["total"] += 1
        if isinstance(val_spell_count, str) and "UNCLEAR" in val_spell_count:
            results["matches"] += 1  # Don't penalize unclear validation data
        elif val_spell_count == scraper_spell_count:
            results["matches"] += 1
        else:
            results["discrepancies"].append({
                "field": "Total Spells",
                "validation": val_spell_count,
                "scraper": scraper_spell_count,
                "val_path": "spellcasting.total_spells",
                "scraper_path": "spells (counted)"
            })
    
    # Perform comparisons
    for field_name, val_path, scraper_path in comparisons:
        results["total"] += 1
        
        val_value = safe_get(validation, val_path)
        scraper_value = safe_get(scraper, scraper_path)
        
        # Handle special cases
        if val_value == "UNCLEAR":
            results["matches"] += 1  # Don't penalize unclear validation data
            continue
            
        if val_value == scraper_value:
            results["matches"] += 1
        else:
            results["discrepancies"].append({
                "field": field_name,
                "validation": val_value,
                "scraper": scraper_value,
                "val_path": val_path,
                "scraper_path": scraper_path
            })
    
    # Check for scraper errors
    if scraper_value == "NOT_FOUND":
        results["errors"].append(f"Missing field: {scraper_path}")
    
    return results

def main():
    """Run comprehensive validation for all characters."""
    
    # Character data: (ID, Name)
    characters = [
        ("29682199", "Redgrave"),
        ("66356596", "Dor'ren Uroprax"), 
        ("68622804", "Zemfur Folle"),
        ("103214475", "Seluvis Felo'melorn"),
        ("103814449", "Yevelda Ovak"),
        ("103873194", "Marin"),
        ("105635812", "Faerah Duskrane"),
        ("116277190", "[GI] Kaeda"),
        ("141875964", "Baldrin Highfoot"),
        ("144986992", "Vaelith Duskthorn"),
        ("145079040", "Thuldus Blackblade"),
        ("145081718", "Ilarion Veles"),
        ("147061783", "ZuB Public Demo")
    ]
    
    print("=== COMPREHENSIVE SCRAPER VALIDATION REPORT ===")
    print(f"Testing {len(characters)} characters against manual validation data")
    print()
    
    all_results = []
    total_matches = 0
    total_comparisons = 0
    
    for char_id, char_name in characters:
        print(f"=== {char_name} ({char_id}) ===")
        
        result = compare_character(char_id, char_name)
        if result:
            all_results.append(result)
            accuracy = (result["matches"] / result["total"]) * 100 if result["total"] > 0 else 0
            print(f"Accuracy: {result['matches']}/{result['total']} ({accuracy:.1f}%)")
            
            total_matches += result["matches"]
            total_comparisons += result["total"]
            
            if result["discrepancies"]:
                print("Discrepancies:")
                for disc in result["discrepancies"]:
                    print(f"  • {disc['field']}: Validation={disc['validation']}, Scraper={disc['scraper']}")
            
            if result["errors"]:
                print("Errors:")
                for error in result["errors"]:
                    print(f"  • {error}")
                    
            if not result["discrepancies"] and not result["errors"]:
                print("✅ Perfect match!")
        else:
            print("❌ Failed to load data")
            
        print()
    
    # Overall summary
    overall_accuracy = (total_matches / total_comparisons) * 100 if total_comparisons > 0 else 0
    print("=== OVERALL SUMMARY ===")
    print(f"Total Accuracy: {total_matches}/{total_comparisons} ({overall_accuracy:.1f}%)")
    print(f"Characters Tested: {len(all_results)}")
    
    # Characters by accuracy
    sorted_results = sorted(all_results, key=lambda x: (x["matches"] / x["total"]) if x["total"] > 0 else 0, reverse=True)
    
    print("\n=== CHARACTERS BY ACCURACY ===")
    for result in sorted_results:
        accuracy = (result["matches"] / result["total"]) * 100 if result["total"] > 0 else 0
        status = "✅" if accuracy == 100 else "⚠️" if accuracy >= 90 else "❌"
        print(f"{status} {result['name']}: {accuracy:.1f}% ({result['matches']}/{result['total']})")
    
    # Issue summary
    print("\n=== COMMON ISSUES ===")
    issue_counts = {}
    for result in all_results:
        for disc in result["discrepancies"]:
            field = disc["field"]
            issue_counts[field] = issue_counts.get(field, 0) + 1
    
    if issue_counts:
        for field, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"{field}: {count} characters affected")
    else:
        print("No common issues found!")

if __name__ == "__main__":
    main()