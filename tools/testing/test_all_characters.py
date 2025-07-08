#!/usr/bin/env python3
"""
Test All Characters Script
Tests the enhanced DnD scraper and markdown converter on all verified character IDs from CLAUDE.md

This script runs both the scraper and converter on each character ID, 
respecting the 30-second API rate limit mentioned in CLAUDE.md.
"""

import subprocess
import time
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Character IDs from CLAUDE.md - verified test characters
CHARACTER_IDS = [
    145081718,
    29682199,  
    147061783,
    66356596,
    144986992,
    145079040,
    141875964,
    68622804,
    105635812,
    103873194,
    103214475,
    103814449
]

# Configuration
API_RATE_LIMIT_SECONDS = 20  # From CLAUDE.md: "call API max once per 20 seconds"
OUTPUT_DIR = "test_results_full"
SCRAPER_SCRIPT = "enhanced_dnd_scraper.py"
CONVERTER_SCRIPT = "dnd_json_to_markdown.py"

def ensure_output_directory():
    """Create output directory if it doesn't exist."""
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    logger.info(f"Output directory: {OUTPUT_DIR}")

def run_scraper(character_id: int) -> bool:
    """Run the enhanced scraper for a character ID."""
    enhanced_output_file = f"{OUTPUT_DIR}/{character_id}.json"
    raw_output_file = f"{OUTPUT_DIR}/{character_id}_raw.json"
    
    try:
        logger.info(f"Running scraper for character {character_id}...")
        result = subprocess.run([
            "python3", SCRAPER_SCRIPT, 
            str(character_id),
            "--output", enhanced_output_file,
            "--raw-output", raw_output_file,  # Save raw API data
            "--verbose"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            logger.info(f"✓ Scraper completed successfully for {character_id}")
            # Verify both files were created
            if os.path.exists(enhanced_output_file) and os.path.exists(raw_output_file):
                logger.info(f"  Enhanced data: {enhanced_output_file}")
                logger.info(f"  Raw API data: {raw_output_file}")
                return True
            else:
                logger.warning(f"Output files not found for {character_id}")
                return False
        else:
            logger.error(f"✗ Scraper failed for {character_id}: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"✗ Scraper timeout for {character_id}")
        return False
    except Exception as e:
        logger.error(f"✗ Scraper error for {character_id}: {e}")
        return False

def run_converter(character_id: int) -> bool:
    """Run the markdown converter for a character ID."""
    output_file = f"{OUTPUT_DIR}/{character_id}.md"
    
    try:
        logger.info(f"Running converter for character {character_id}...")
        result = subprocess.run([
            "python3", CONVERTER_SCRIPT,
            str(character_id),
            output_file
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            logger.info(f"✓ Converter completed successfully for {character_id}")
            return True
        else:
            logger.error(f"✗ Converter failed for {character_id}: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"✗ Converter timeout for {character_id}")
        return False
    except Exception as e:
        logger.error(f"✗ Converter error for {character_id}: {e}")
        return False

def validate_output_files(character_id: int) -> Dict[str, Any]:
    """Validate that output files were created and contain expected data."""
    enhanced_json_file = f"{OUTPUT_DIR}/{character_id}.json"
    raw_json_file = f"{OUTPUT_DIR}/{character_id}_raw.json"
    md_file = f"{OUTPUT_DIR}/{character_id}.md"
    
    validation = {
        "character_id": character_id,
        "enhanced_json_exists": False,
        "raw_json_exists": False,
        "md_exists": False,
        "enhanced_json_valid": False,
        "raw_json_valid": False,
        "md_valid": False,
        "character_name": None,
        "enhanced_json_size": 0,
        "raw_json_size": 0,
        "md_size": 0
    }
    
    # Check Enhanced JSON file
    if os.path.exists(enhanced_json_file):
        validation["enhanced_json_exists"] = True
        validation["enhanced_json_size"] = os.path.getsize(enhanced_json_file)
        
        try:
            with open(enhanced_json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "basic_info" in data and "name" in data["basic_info"]:
                    validation["enhanced_json_valid"] = True
                    validation["character_name"] = data["basic_info"]["name"]
        except Exception as e:
            logger.warning(f"Enhanced JSON validation failed for {character_id}: {e}")
    
    # Check Raw JSON file
    if os.path.exists(raw_json_file):
        validation["raw_json_exists"] = True
        validation["raw_json_size"] = os.path.getsize(raw_json_file)
        
        try:
            with open(raw_json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Raw data should have 'data' field with character info
                if "data" in data and isinstance(data["data"], dict):
                    validation["raw_json_valid"] = True
        except Exception as e:
            logger.warning(f"Raw JSON validation failed for {character_id}: {e}")
    
    # Check MD file
    if os.path.exists(md_file):
        validation["md_exists"] = True
        validation["md_size"] = os.path.getsize(md_file)
        
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Basic validation: check for YAML frontmatter and character name
                if content.startswith('---') and '---' in content[3:]:
                    validation["md_valid"] = True
        except Exception as e:
            logger.warning(f"MD validation failed for {character_id}: {e}")
    
    return validation

def print_summary(results: List[Dict[str, Any]]):
    """Print a summary of test results."""
    total = len(results)
    successful_scrapers = sum(1 for r in results if r.get("scraper_success", False))
    successful_converters = sum(1 for r in results if r.get("converter_success", False))
    valid_enhanced_json = sum(1 for r in results if r.get("validation", {}).get("enhanced_json_valid", False))
    valid_raw_json = sum(1 for r in results if r.get("validation", {}).get("raw_json_valid", False))
    valid_md = sum(1 for r in results if r.get("validation", {}).get("md_valid", False))
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total characters tested: {total}")
    print(f"Successful scraper runs: {successful_scrapers}/{total}")
    print(f"Successful converter runs: {successful_converters}/{total}")
    print(f"Valid Enhanced JSON files: {valid_enhanced_json}/{total}")
    print(f"Valid Raw JSON files: {valid_raw_json}/{total}")
    print(f"Valid MD files: {valid_md}/{total}")
    print()
    
    print("Character Details:")
    print("-" * 70)
    print("Character | Name                 | S  C  E  R  M")
    print("----------|----------------------|---------------")
    for result in results:
        char_id = result["character_id"]
        validation = result.get("validation", {})
        char_name = validation.get("character_name", "Unknown")[:20]
        scraper_ok = "✓" if result.get("scraper_success", False) else "✗"
        converter_ok = "✓" if result.get("converter_success", False) else "✗"
        enhanced_ok = "✓" if validation.get("enhanced_json_valid", False) else "✗"
        raw_ok = "✓" if validation.get("raw_json_valid", False) else "✗"
        md_ok = "✓" if validation.get("md_valid", False) else "✗"
        
        print(f"{char_id:>9} | {char_name:<20} | {scraper_ok}  {converter_ok}  {enhanced_ok}  {raw_ok}  {md_ok}")
    
    print("\nLegend: S=Scraper, C=Converter, E=Enhanced JSON, R=Raw JSON, M=Markdown")

def main():
    """Main test function."""
    logger.info(f"Starting comprehensive test of {len(CHARACTER_IDS)} characters")
    logger.info(f"API rate limit: {API_RATE_LIMIT_SECONDS} seconds between calls")
    
    ensure_output_directory()
    
    results = []
    
    for i, character_id in enumerate(CHARACTER_IDS, 1):
        logger.info(f"\n{'='*50}")
        logger.info(f"Processing character {i}/{len(CHARACTER_IDS)}: {character_id}")
        logger.info(f"{'='*50}")
        
        result = {"character_id": character_id}
        
        # Run scraper
        result["scraper_success"] = run_scraper(character_id)
        
        # Wait for API rate limit (except after last character)
        if i < len(CHARACTER_IDS):
            logger.info(f"Waiting {API_RATE_LIMIT_SECONDS} seconds for API rate limit...")
            time.sleep(API_RATE_LIMIT_SECONDS)
        
        # Run converter
        result["converter_success"] = run_converter(character_id)
        
        # Validate outputs
        result["validation"] = validate_output_files(character_id)
        
        results.append(result)
        
        # Quick status
        scraper_status = "✓" if result["scraper_success"] else "✗"
        converter_status = "✓" if result["converter_success"] else "✗"
        logger.info(f"Character {character_id}: Scraper {scraper_status}, Converter {converter_status}")
    
    # Print final summary
    print_summary(results)
    
    # Save detailed results
    results_file = f"{OUTPUT_DIR}/test_results_summary.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Detailed results saved to {results_file}")

if __name__ == "__main__":
    main()