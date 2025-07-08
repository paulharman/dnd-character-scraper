#!/usr/bin/env python3
"""
Complete Baseline Data Collection

Uses the original v5.2.0 scripts to generate complete baseline data:
1. Raw D&D Beyond JSON (via scraper)
2. Scraper output JSON (processed character data)
3. Parser output MD (Obsidian DnD UI Toolkit format)

This creates a complete baseline for all character IDs from CLAUDE.md
"""

import subprocess
import time
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

# All known character IDs from CLAUDE.md
KNOWN_CHARACTER_IDS = [
    29682199,
    66356596,
    68622804,
    103214475,
    103814449,
    103873194,
    105635812,
    141875964,
    144986992,
    145079040,
    145081718,
    147061783
]

def run_command(cmd: List[str], timeout: int = 120) -> Tuple[bool, str, str]:
    """Run a command and return success, stdout, stderr."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def collect_raw_and_scraper_data(character_id: int) -> Dict[str, bool]:
    """Collect raw JSON and scraper JSON for a character."""
    print(f"  📡 Fetching data for character {character_id}...")
    
    results = {"raw": False, "scraper": False}
    
    # File paths
    raw_file = Path(f"Raw/{character_id}.json")
    scraper_file = Path(f"baseline_{character_id}.json")
    
    # Check if files already exist
    if raw_file.exists() and scraper_file.exists():
        print(f"  ✅ Both files already exist")
        return {"raw": True, "scraper": True}
    
    # Run original scraper to get both raw and processed data
    cmd = ["python3", "enhanced_dnd_scraper_v5.2.0_original.py", str(character_id), "--output", f"baseline_{character_id}.json"]
    
    success, stdout, stderr = run_command(cmd)
    
    if success:
        print(f"  ✅ Scraper completed successfully")
        results["scraper"] = scraper_file.exists()
        
        # The scraper fetches raw data - let's save it to Raw/ if we don't have it
        if not raw_file.exists():
            # Try to re-run with Raw output
            cmd_raw = ["python3", "enhanced_dnd_scraper_v5.2.0_original.py", str(character_id), "--output", f"Raw/{character_id}.json"]
            success_raw, _, _ = run_command(cmd_raw)
            results["raw"] = success_raw and raw_file.exists()
        else:
            results["raw"] = True
            
    else:
        print(f"  ❌ Scraper failed: {stderr}")
    
    return results

def generate_parser_output(character_id: int) -> bool:
    """Generate parser MD output for a character."""
    scraper_file = Path(f"baseline_{character_id}.json")
    parser_file = Path(f"baseline_{character_id}.md")
    
    if not scraper_file.exists():
        print(f"  ❌ No scraper file found: {scraper_file}")
        return False
    
    if parser_file.exists():
        print(f"  ✅ Parser file already exists: {parser_file}")
        return True
    
    print(f"  📝 Generating parser output...")
    
    # Run original parser
    cmd = ["python3", "dnd_json_to_markdown_v5.2.0_original.py", str(character_id), f"baseline_{character_id}.md"]
    
    success, stdout, stderr = run_command(cmd)
    
    if success and parser_file.exists():
        print(f"  ✅ Parser completed successfully")
        return True
    else:
        print(f"  ❌ Parser failed: {stderr}")
        return False

def main():
    """Complete baseline data collection for all characters."""
    print("🏁 Complete Baseline Data Collection")
    print("=" * 60)
    print(f"📋 Processing {len(KNOWN_CHARACTER_IDS)} character IDs")
    print("⚠️  Rate limiting: 30 second delay between API calls")
    print()
    
    # Track results
    results = {
        "raw": {"success": 0, "failed": 0},
        "scraper": {"success": 0, "failed": 0},
        "parser": {"success": 0, "failed": 0}
    }
    
    for i, character_id in enumerate(KNOWN_CHARACTER_IDS):
        print(f"[{i+1}/{len(KNOWN_CHARACTER_IDS)}] 🧪 Character ID: {character_id}")
        
        # Step 1: Collect raw and scraper data
        data_results = collect_raw_and_scraper_data(character_id)
        
        if data_results["raw"]:
            results["raw"]["success"] += 1
        else:
            results["raw"]["failed"] += 1
            
        if data_results["scraper"]:
            results["scraper"]["success"] += 1
        else:
            results["scraper"]["failed"] += 1
        
        # Step 2: Generate parser output (only if we have scraper data)
        if data_results["scraper"]:
            if generate_parser_output(character_id):
                results["parser"]["success"] += 1
            else:
                results["parser"]["failed"] += 1
        else:
            results["parser"]["failed"] += 1
        
        # Rate limiting between API calls (except for last one)
        if i < len(KNOWN_CHARACTER_IDS) - 1:
            print(f"  ⏳ Rate limiting: waiting 30 seconds...")
            time.sleep(30)
        
        print()
    
    # Final summary
    print("📊 Complete Baseline Collection Summary")
    print("=" * 50)
    
    total_chars = len(KNOWN_CHARACTER_IDS)
    
    for data_type, counts in results.items():
        success_rate = counts["success"] / total_chars * 100
        print(f"{data_type.upper():>8}: {counts['success']:>2}/{total_chars} ({success_rate:5.1f}%) - {counts['failed']} failed")
    
    # Check for complete pipeline coverage
    complete_pipeline = results["parser"]["success"]
    complete_rate = complete_pipeline / total_chars * 100
    
    print(f"\n🎯 Complete Pipeline Coverage: {complete_pipeline}/{total_chars} ({complete_rate:.1f}%)")
    
    if complete_pipeline == total_chars:
        print("🎉 All baseline data collected successfully!")
        print("✅ Ready for comprehensive validation")
    elif complete_pipeline > total_chars * 0.8:
        print("⚠️  Most baseline data collected. Good for validation.")
    else:
        print("🔧 Significant data missing. Check failed characters.")
    
    print(f"\n📁 Files generated:")
    print(f"   Raw D&D Beyond JSON: Raw/{{character_id}}.json")
    print(f"   Scraper output JSON: baseline_{{character_id}}.json") 
    print(f"   Parser output MD: baseline_{{character_id}}.md")
    
    return 0 if results["parser"]["failed"] == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)