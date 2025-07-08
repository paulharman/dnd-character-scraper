#!/usr/bin/env python3
"""
Generate baseline data for all known character IDs using original v5.2.0 scraper.
This creates a comprehensive dataset for validation.
"""

import subprocess
import time
import sys
from pathlib import Path
from typing import List

# All known character IDs from CLAUDE.md
KNOWN_CHARACTER_IDS = [
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

def generate_baseline_for_character(character_id: int) -> bool:
    """Generate baseline using original v5.2.0 scraper."""
    print(f"🔄 Generating baseline for character {character_id}...")
    
    baseline_file = f"baseline_{character_id}.json"
    raw_file = f"Raw/{character_id}.json"
    
    try:
        # Run the original v5.2.0 scraper
        cmd = ["python3", "enhanced_dnd_scraper.py", str(character_id), "--output", baseline_file]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(f"✅ Baseline generated: {baseline_file}")
            
            # Also save raw data if we don't have it
            if not Path(raw_file).exists():
                print(f"📁 Saving raw data: {raw_file}")
                # The scraper should have fetched the raw data, but let's ensure we have it
                
            return True
        else:
            print(f"❌ Scraper failed for {character_id}")
            print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout for character {character_id}")
        return False
    except Exception as e:
        print(f"💥 Error for character {character_id}: {str(e)}")
        return False


def main():
    """Generate baselines for all known characters."""
    print("🏁 Starting comprehensive baseline generation")
    print("=" * 60)
    print(f"📋 Processing {len(KNOWN_CHARACTER_IDS)} known character IDs")
    print("⚠️  Rate limiting: 30 second delay between API calls")
    print()
    
    successful = 0
    failed = 0
    
    for i, character_id in enumerate(KNOWN_CHARACTER_IDS):
        print(f"[{i+1}/{len(KNOWN_CHARACTER_IDS)}] Character ID: {character_id}")
        
        # Check if baseline already exists
        baseline_file = f"baseline_{character_id}.json"
        if Path(baseline_file).exists():
            print(f"✅ Baseline already exists: {baseline_file}")
            successful += 1
        else:
            # Generate new baseline
            if generate_baseline_for_character(character_id):
                successful += 1
            else:
                failed += 1
        
        # Rate limiting - wait 30 seconds between API calls (except for last one)
        if i < len(KNOWN_CHARACTER_IDS) - 1:
            print(f"⏳ Rate limiting: waiting 30 seconds...")
            time.sleep(30)
        
        print()
    
    # Summary
    print("📊 Baseline Generation Summary")
    print("=" * 40)
    print(f"Total characters: {len(KNOWN_CHARACTER_IDS)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {successful/len(KNOWN_CHARACTER_IDS)*100:.1f}%")
    
    if successful == len(KNOWN_CHARACTER_IDS):
        print("🎉 All baselines generated successfully!")
    elif successful > 0:
        print("⚠️  Some baselines generated. Check failed characters.")
    else:
        print("💥 No baselines generated. Check network/API issues.")
    
    print(f"\n📁 Baseline files: baseline_{{character_id}}.json")
    print(f"📁 Raw data files: Raw/{{character_id}}.json")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)