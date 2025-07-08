#!/usr/bin/env python3
"""
Generate validation markdown files for all test characters with proper API rate limiting.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Test character IDs from CLAUDE.md
TEST_CHARACTER_IDS = [
    145081718, 29682199, 147061783, 66356596, 144986992,
    145079040, 141875964, 68622804, 105635812, 103873194,
    103214475, 103814449, 116277190
]

API_DELAY_SECONDS = 20  # Required delay between API calls


def generate_markdown_with_delay(character_id: int, output_dir: Path) -> bool:
    """
    Generate markdown for a single character with proper error handling.
    
    Args:
        character_id: Character ID to process
        output_dir: Output directory for markdown files
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create output filename (will be updated by the script based on character name)
        output_file = output_dir / f"{character_id}_Character.md"
        
        # Build command (with enhanced spells to match v5.2.0 behavior)
        cmd = [
            sys.executable, 
            "dnd_json_to_markdown.py",
            str(character_id),
            str(output_file),
            "--scraper-path", "enhanced_dnd_scraper.py",
            "--verbose"
        ]
        
        # Run the command
        import subprocess
        logger.info(f"Processing character {character_id}...")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout
        )
        
        if result.returncode == 0:
            logger.info(f"✅ Successfully generated markdown for character {character_id}")
            return True
        else:
            logger.error(f"❌ Failed to generate markdown for character {character_id}")
            logger.error(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"❌ Timeout processing character {character_id}")
        return False
    except Exception as e:
        logger.error(f"❌ Exception processing character {character_id}: {e}")
        return False


def main():
    """Main function to generate all validation markdown files."""
    # Create output directory
    output_dir = Path("validation_output")
    output_dir.mkdir(exist_ok=True)
    
    logger.info(f"Starting validation markdown generation for {len(TEST_CHARACTER_IDS)} characters")
    logger.info(f"API delay: {API_DELAY_SECONDS} seconds between calls")
    logger.info("=" * 60)
    
    successful = 0
    failed = 0
    
    for i, character_id in enumerate(TEST_CHARACTER_IDS):
        # Add delay before each API call (except the first)
        if i > 0:
            logger.info(f"Waiting {API_DELAY_SECONDS} seconds before next API call...")
            time.sleep(API_DELAY_SECONDS)
        
        success = generate_markdown_with_delay(character_id, output_dir)
        
        if success:
            successful += 1
        else:
            failed += 1
        
        # Progress update
        remaining = len(TEST_CHARACTER_IDS) - i - 1
        if remaining > 0:
            estimated_time = remaining * API_DELAY_SECONDS
            logger.info(f"Progress: {i+1}/{len(TEST_CHARACTER_IDS)} - Estimated remaining time: {estimated_time//60}m {estimated_time%60}s")
    
    logger.info("=" * 60)
    logger.info(f"Generation complete! Success: {successful}, Failed: {failed}")
    
    if failed > 0:
        logger.warning("Some characters failed to generate. Check the error messages above.")
        sys.exit(1)
    else:
        logger.info("All validation markdown files generated successfully!")
        
        # List generated files
        md_files = list(output_dir.glob("*.md"))
        logger.info(f"Generated files ({len(md_files)}):")
        for md_file in sorted(md_files):
            file_size = md_file.stat().st_size
            logger.info(f"  - {md_file.name} ({file_size:,} bytes)")


if __name__ == "__main__":
    main()