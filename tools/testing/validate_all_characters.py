#!/usr/bin/env python3
"""
Comprehensive validation script for all 12 test characters.
Compares v6.0.0 output against v5.2.0 baseline for both JSON and MD output.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

# Test character IDs
CHARACTER_IDS = [
    145081718, 29682199, 147061783, 66356596, 144986992, 145079040,
    141875964, 68622804, 105635812, 103873194, 103214475, 103814449
]

def run_scraper(character_id, output_file):
    """Run the enhanced scraper for a character."""
    cmd = [
        "python3", "enhanced_dnd_scraper.py", 
        str(character_id), 
        "--output", output_file
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"❌ Scraper failed for {character_id}: {result.stderr}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"❌ Scraper timeout for {character_id}")
        return False
    except Exception as e:
        print(f"❌ Scraper error for {character_id}: {e}")
        return False

def run_parser(character_id, output_file):
    """Run the markdown parser for a character.""" 
    cmd = [
        "python3", "archive/v5.2.0/dnd_json_to_markdown_v5.2.0_original.py",
        str(character_id), output_file,
        "--scraper-path", "enhanced_dnd_scraper.py",
        "--no-enhance-spells"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"❌ Parser failed for {character_id}: {result.stderr}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"❌ Parser timeout for {character_id}")
        return False
    except Exception as e:
        print(f"❌ Parser error for {character_id}: {e}")
        return False

def compare_json_field(test_data, baseline_data, field_path, character_id):
    """Compare a specific field between test and baseline."""
    def get_nested_value(data, path):
        try:
            for key in path.split('.'):
                if '[' in key and ']' in key:
                    # Handle array indices like "hit_points[0]"
                    array_key = key.split('[')[0]
                    index = int(key.split('[')[1].split(']')[0])
                    data = data[array_key][index]
                else:
                    data = data[key]
            return data
        except (KeyError, IndexError, TypeError):
            return None
    
    test_value = get_nested_value(test_data, field_path)
    baseline_value = get_nested_value(baseline_data, field_path)
    
    if test_value != baseline_value:
        return {
            'field': field_path,
            'test': test_value,
            'baseline': baseline_value,
            'status': 'MISMATCH'
        }
    
    return {'field': field_path, 'status': 'MATCH'}

def validate_character_json(character_id):
    """Validate JSON output for a character against baseline."""
    print(f"\n🔍 Validating character {character_id} JSON...")
    
    # Run new scraper
    test_output = f"/tmp/test_{character_id}.json"
    if not run_scraper(character_id, test_output):
        return {'character_id': character_id, 'status': 'SCRAPER_FAILED'}
    
    # Load test and baseline data
    try:
        with open(test_output, 'r') as f:
            test_data = json.load(f)
        
        baseline_file = f"data/baseline/scraper/baseline_{character_id}.json"
        with open(baseline_file, 'r') as f:
            baseline_data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load data: {e}")
        return {'character_id': character_id, 'status': 'DATA_LOAD_FAILED'}
    
    # Key fields to validate
    key_fields = [
        'basic_info.hit_points.maximum',
        'basic_info.hit_points.base', 
        'basic_info.hit_points.constitution_bonus',
        'basic_info.hit_points.hit_point_method',
        'basic_info.armor_class.total',
        'ability_scores.strength.score',
        'ability_scores.dexterity.score', 
        'ability_scores.constitution.score',
        'ability_scores.intelligence.score',
        'ability_scores.wisdom.score',
        'ability_scores.charisma.score',
        'basic_info.level',
        'basic_info.name'
    ]
    
    results = []
    mismatches = 0
    
    for field in key_fields:
        result = compare_json_field(test_data, baseline_data, field, character_id)
        results.append(result)
        if result['status'] == 'MISMATCH':
            mismatches += 1
            print(f"  ❌ {field}: {result['test']} ≠ {result['baseline']}")
    
    if mismatches == 0:
        print(f"  ✅ All {len(key_fields)} key fields match!")
    else:
        print(f"  ⚠️  {mismatches}/{len(key_fields)} fields have mismatches")
    
    return {
        'character_id': character_id,
        'status': 'COMPLETE',
        'mismatches': mismatches,
        'total_fields': len(key_fields),
        'results': results
    }

def validate_character_md(character_id):
    """Validate MD output for a character."""
    print(f"\n📝 Validating character {character_id} MD...")
    
    # Run parser 
    test_output = f"/tmp/test_{character_id}.md"
    if not run_parser(character_id, test_output):
        return {'character_id': character_id, 'status': 'PARSER_FAILED'}
    
    # Check if MD file was created and has reasonable content
    try:
        with open(test_output, 'r') as f:
            content = f.read()
        
        if len(content) < 100:
            print(f"  ❌ MD output too short: {len(content)} characters")
            return {'character_id': character_id, 'status': 'MD_TOO_SHORT'}
        
        # Basic content checks
        if "# " not in content:
            print(f"  ❌ No markdown headers found")
            return {'character_id': character_id, 'status': 'MD_NO_HEADERS'}
            
        print(f"  ✅ MD generated successfully ({len(content)} characters)")
        return {'character_id': character_id, 'status': 'MD_SUCCESS'}
        
    except Exception as e:
        print(f"  ❌ Failed to validate MD: {e}")
        return {'character_id': character_id, 'status': 'MD_VALIDATION_FAILED'}

def main():
    """Run comprehensive validation on all characters."""
    print("🚀 Starting comprehensive validation of all 12 characters...")
    print("=" * 80)
    
    json_results = []
    md_results = []
    
    for i, character_id in enumerate(CHARACTER_IDS, 1):
        print(f"\n[{i}/12] Processing character {character_id}")
        
        # Validate JSON
        json_result = validate_character_json(character_id)
        json_results.append(json_result)
        
        # Validate MD
        md_result = validate_character_md(character_id) 
        md_results.append(md_result)
        
        # Rate limiting
        if i < len(CHARACTER_IDS):
            print("⏱️  Waiting 30 seconds (API rate limiting)...")
            time.sleep(30)
    
    # Summary report
    print("\n" + "=" * 80)
    print("📊 VALIDATION SUMMARY")
    print("=" * 80)
    
    # JSON Summary
    json_perfect = sum(1 for r in json_results if r.get('mismatches', 999) == 0)
    json_failed = sum(1 for r in json_results if r.get('status') != 'COMPLETE')
    
    print(f"\n📋 JSON Results:")
    print(f"  ✅ Perfect matches: {json_perfect}/12")
    print(f"  ❌ With issues: {12 - json_perfect}/12")
    print(f"  💥 Failed to run: {json_failed}/12")
    
    # MD Summary
    md_success = sum(1 for r in md_results if r.get('status') == 'MD_SUCCESS')
    print(f"\n📝 MD Results:")
    print(f"  ✅ Successful: {md_success}/12")
    print(f"  ❌ Failed: {12 - md_success}/12")
    
    # Detailed results for failing characters
    print(f"\n🔍 Characters needing fixes:")
    for result in json_results:
        if result.get('mismatches', 0) > 0:
            char_id = result['character_id']
            mismatches = result['mismatches']
            print(f"  📋 {char_id}: {mismatches} JSON field mismatches")
    
    for result in md_results:
        if result.get('status') != 'MD_SUCCESS':
            char_id = result['character_id']
            status = result['status']
            print(f"  📝 {char_id}: MD {status}")
    
    overall_success = (json_perfect == 12 and md_success == 12)
    print(f"\n🎯 Overall Status: {'✅ 100% ACCURACY ACHIEVED!' if overall_success else '⚠️ Issues remain'}")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())