#!/usr/bin/env python3
"""
Real D&D Beyond API Integration Tests

⚠️  WARNING: These tests make REAL API calls to D&D Beyond!
- Respects 20-second minimum delay between requests
- Saves raw responses for future offline testing
- Only run when explicitly requested with --live-api flag

Usage:
  python3 tests/integration/test_real_dndbeyond_api.py --live-api
  python3 tests/integration/test_real_dndbeyond_api.py --use-cached

Test Character IDs (from CLAUDE.md):
  145081718, 29682199, 147061783, 66356596, 144986992, 145079040
"""

import argparse
import json
import time
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import unittest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.clients.dndbeyond_client import DNDBeyondClient
from src.calculators.character_calculator import CharacterCalculator
from src.rules.version_manager import RuleVersionManager
from enhanced_dnd_scraper import EnhancedDnDScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
TEST_CHARACTER_IDS = [
    145081718,  # Known working character
    29682199,   # Another test character
    147061783,  # Third test character
    # Add more as needed, but respect rate limits!
]

CACHE_DIR = project_root / "tests" / "fixtures" / "api_responses"
RATE_LIMIT_DELAY = 20.0  # 20 second minimum delay


class RealDnDBeyondAPITests(unittest.TestCase):
    """
    Real API integration tests with rate limiting and caching.
    
    These tests actually call D&D Beyond's API and should be used sparingly.
    Raw responses are cached for offline testing.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.cache_dir = CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = DNDBeyondClient()
        self.calculator = CharacterCalculator()
        self.rule_manager = RuleVersionManager()
        
        # Track request times for rate limiting
        self.last_request_time = 0
        
        logger.info("Real D&D Beyond API Tests initialized")
        logger.warning("⚠️  These tests make REAL API calls with 20-second delays!")
    
    def _apply_rate_limiting(self):
        """Apply rate limiting between API requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < RATE_LIMIT_DELAY:
            sleep_time = RATE_LIMIT_DELAY - time_since_last
            logger.info(f"⏳ Rate limiting: waiting {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_cache_path(self, character_id: int, suffix: str = "raw") -> Path:
        """Get cache file path for character data."""
        return self.cache_dir / f"character_{character_id}_{suffix}.json"
    
    def _save_to_cache(self, character_id: int, data: Dict[str, Any], suffix: str = "raw"):
        """Save data to cache file."""
        cache_path = self._get_cache_path(character_id, suffix)
        
        # Add metadata
        cached_data = {
            "character_id": character_id,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            "source": "dndbeyond_api",
            "data": data
        }
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cached_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"💾 Cached response to: {cache_path}")
    
    def _load_from_cache(self, character_id: int, suffix: str = "raw") -> Optional[Dict[str, Any]]:
        """Load data from cache file."""
        cache_path = self._get_cache_path(character_id, suffix)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            logger.info(f"📁 Loaded from cache: {cache_path}")
            return cached_data.get("data")
        
        except Exception as e:
            logger.warning(f"Failed to load cache {cache_path}: {e}")
            return None
    
    def test_single_character_api_call(self):
        """Test fetching a single character from D&D Beyond API."""
        character_id = 145081718  # Known working character
        
        logger.info(f"🔍 Testing character {character_id}")
        
        # Check if we should use cached data or make real API call
        use_live_api = getattr(self, '_use_live_api', False)
        
        if use_live_api:
            logger.warning("🌐 Making REAL API call to D&D Beyond!")
            self._apply_rate_limiting()
            
            try:
                # Make real API call
                raw_data = self.client.get_character(character_id)
                
                # Validate we got real data
                self.assertIsInstance(raw_data, dict)
                self.assertIn('id', raw_data)
                self.assertIn('name', raw_data)
                self.assertIn('classes', raw_data)
                self.assertEqual(raw_data['id'], character_id)
                
                # Save raw response
                self._save_to_cache(character_id, raw_data, "raw")
                
                # Test rule detection
                rule_detection = self.rule_manager.detect_rule_version(raw_data, character_id)
                logger.info(f"📖 Rule version detected: {rule_detection.version.value} (confidence: {rule_detection.confidence:.1%})")
                
                # Test character calculation
                calculated_data = self.calculator.calculate_complete_json(raw_data)
                
                # Save calculated response
                self._save_to_cache(character_id, calculated_data, "calculated")
                
                # Validate calculated data
                self.assertIsInstance(calculated_data, dict)
                self.assertIn('armor_class', calculated_data)
                self.assertIn('max_hp', calculated_data)
                self.assertIn('ability_scores', calculated_data)
                
                # Log results
                char_name = calculated_data.get('name', 'Unknown')
                char_level = calculated_data.get('level', 'Unknown')
                char_ac = calculated_data.get('armor_class', 'Unknown')
                char_hp = calculated_data.get('max_hp', 'Unknown')
                
                logger.info(f"✅ Character: {char_name} (Level {char_level})")
                logger.info(f"🛡️  AC: {char_ac}, ❤️  HP: {char_hp}")
                
                return raw_data, calculated_data
                
            except Exception as e:
                self.fail(f"API call failed: {e}")
        
        else:
            # Use cached data
            raw_data = self._load_from_cache(character_id, "raw")
            calculated_data = self._load_from_cache(character_id, "calculated")
            
            if raw_data is None:
                self.skipTest(f"No cached data for character {character_id}. Run with --live-api to fetch.")
            
            logger.info("📁 Using cached data for testing")
            
            # Test with cached data
            self.assertIsInstance(raw_data, dict)
            self.assertEqual(raw_data['id'], character_id)
            
            if calculated_data:
                self.assertIn('armor_class', calculated_data)
                self.assertIn('max_hp', calculated_data)
            
            return raw_data, calculated_data
    
    def test_multiple_characters_rate_limited(self):
        """Test fetching multiple characters with proper rate limiting."""
        use_live_api = getattr(self, '_use_live_api', False)
        
        if not use_live_api:
            self.skipTest("Multiple character test requires --live-api flag")
        
        logger.warning("🌐 Testing multiple characters with rate limiting!")
        logger.warning(f"⏳ This will take at least {len(TEST_CHARACTER_IDS) * RATE_LIMIT_DELAY} seconds")
        
        results = []
        start_time = time.time()
        
        for i, character_id in enumerate(TEST_CHARACTER_IDS[:2]):  # Limit to 2 for testing
            logger.info(f"📊 Testing character {i+1}/{min(2, len(TEST_CHARACTER_IDS))}: {character_id}")
            
            try:
                # Apply rate limiting
                self._apply_rate_limiting()
                
                # Fetch character
                raw_data = self.client.get_character(character_id)
                
                # Validate basic structure
                self.assertIsInstance(raw_data, dict)
                self.assertEqual(raw_data['id'], character_id)
                
                # Save to cache
                self._save_to_cache(character_id, raw_data, "raw")
                
                # Test calculation
                calculated_data = self.calculator.calculate_complete_json(raw_data)
                self._save_to_cache(character_id, calculated_data, "calculated")
                
                results.append({
                    'id': character_id,
                    'name': calculated_data.get('name'),
                    'level': calculated_data.get('level'),
                    'rule_version': calculated_data.get('rule_version'),
                    'armor_class': calculated_data.get('armor_class'),
                    'max_hp': calculated_data.get('max_hp')
                })
                
                logger.info(f"✅ {calculated_data.get('name')} processed successfully")
                
            except Exception as e:
                logger.error(f"❌ Failed to process character {character_id}: {e}")
                # Continue with other characters
        
        end_time = time.time()
        total_time = end_time - start_time
        
        logger.info(f"⏱️  Total time: {total_time:.1f} seconds")
        logger.info(f"📊 Successfully processed {len(results)} characters")
        
        # Validate we respected rate limits
        expected_min_time = (len(results) - 1) * RATE_LIMIT_DELAY
        if len(results) > 1:
            self.assertGreaterEqual(total_time, expected_min_time, 
                                  f"Rate limiting not respected! Expected at least {expected_min_time}s")
        
        return results
    
    def test_end_to_end_scraper(self):
        """Test the complete enhanced scraper end-to-end."""
        character_id = 145081718
        use_live_api = getattr(self, '_use_live_api', False)
        
        if not use_live_api:
            self.skipTest("End-to-end test requires --live-api flag")
        
        logger.info("🔄 Testing complete enhanced scraper pipeline")
        
        try:
            # Create scraper instance
            scraper = EnhancedDnDScraper(character_id)
            
            # Apply rate limiting
            self._apply_rate_limiting()
            
            # Scrape character
            character_data = scraper.scrape_character()
            
            # Validate complete pipeline worked
            self.assertIsInstance(character_data, dict)
            self.assertEqual(character_data['id'], character_id)
            self.assertIn('scraper_version', character_data)
            self.assertIn('rule_version', character_data)
            self.assertIn('rule_detection', character_data)
            
            # Save complete output
            self._save_to_cache(character_id, character_data, "complete")
            
            # Test save functionality
            output_file = scraper.save_character_data(character_data, 
                                                    f"test_output_{character_id}.json")
            
            # Verify file was created
            self.assertTrue(Path(output_file).exists())
            
            # Clean up test file
            Path(output_file).unlink(missing_ok=True)
            
            logger.info(f"✅ End-to-end test completed successfully")
            logger.info(f"📖 Rule version: {character_data.get('rule_version')}")
            logger.info(f"🛡️  AC: {character_data.get('armor_class')}")
            logger.info(f"❤️  HP: {character_data.get('max_hp')}")
            
            return character_data
            
        except Exception as e:
            self.fail(f"End-to-end test failed: {e}")
    
    def test_error_handling(self):
        """Test error handling with invalid character IDs."""
        use_live_api = getattr(self, '_use_live_api', False)
        
        if not use_live_api:
            self.skipTest("Error handling test requires --live-api flag")
        
        logger.info("🚫 Testing error handling with invalid character ID")
        
        # Apply rate limiting
        self._apply_rate_limiting()
        
        # Test with invalid character ID
        invalid_id = 999999999
        
        with self.assertRaises(Exception):
            self.client.get_character(invalid_id)
        
        logger.info("✅ Error handling test passed")


def create_cache_summary():
    """Create a summary of cached API responses."""
    cache_dir = CACHE_DIR
    
    if not cache_dir.exists():
        print("No cache directory found.")
        return
    
    cache_files = list(cache_dir.glob("*.json"))
    
    if not cache_files:
        print("No cached responses found.")
        return
    
    print("\n" + "="*80)
    print("🗂️  CACHED D&D BEYOND API RESPONSES")
    print("="*80)
    
    for cache_file in sorted(cache_files):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            char_data = data.get('data', {})
            char_id = data.get('character_id', 'Unknown')
            timestamp = data.get('timestamp', 'Unknown')
            
            if 'raw' in cache_file.name:
                char_name = char_data.get('name', 'Unknown')
                char_level = sum(cls.get('level', 0) for cls in char_data.get('classes', []))
                print(f"📁 {cache_file.name}")
                print(f"   Character: {char_name} (ID: {char_id}, Level: {char_level})")
                print(f"   Cached: {timestamp}")
                
            elif 'calculated' in cache_file.name:
                char_name = char_data.get('name', 'Unknown')
                char_level = char_data.get('level', 'Unknown')
                char_ac = char_data.get('armor_class', 'Unknown')
                char_hp = char_data.get('max_hp', 'Unknown')
                rule_version = char_data.get('rule_version', 'Unknown')
                print(f"🧮 {cache_file.name}")
                print(f"   Character: {char_name} (Level {char_level})")
                print(f"   Stats: AC {char_ac}, HP {char_hp}")
                print(f"   Rules: {rule_version}")
                print(f"   Processed: {timestamp}")
            
            print()
            
        except Exception as e:
            print(f"❌ Error reading {cache_file}: {e}")
    
    print(f"Total cached responses: {len(cache_files)}")
    print("\nUsage:")
    print("  python3 tests/integration/test_real_dndbeyond_api.py --use-cached")
    print("  python3 tests/integration/test_real_dndbeyond_api.py --live-api")


def main():
    """Main entry point with command line options."""
    parser = argparse.ArgumentParser(
        description="Real D&D Beyond API Integration Tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show cached responses
  python3 tests/integration/test_real_dndbeyond_api.py --summary

  # Run tests with cached data (safe, no API calls)
  python3 tests/integration/test_real_dndbeyond_api.py --use-cached

  # Run tests with REAL API calls (slow, respects rate limits)
  python3 tests/integration/test_real_dndbeyond_api.py --live-api

⚠️  WARNING: --live-api makes REAL API calls with 20-second delays!
Use --use-cached for development and --live-api only when needed.
        """
    )
    
    parser.add_argument(
        '--live-api',
        action='store_true',
        help='⚠️  Make REAL API calls to D&D Beyond (slow, respects rate limits)'
    )
    
    parser.add_argument(
        '--use-cached',
        action='store_true',
        help='Use cached API responses (fast, no API calls)'
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show summary of cached API responses'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.summary:
        create_cache_summary()
        return
    
    if not args.live_api and not args.use_cached:
        print("Please specify either --live-api or --use-cached")
        print("Use --help for more information")
        return
    
    if args.live_api and args.use_cached:
        print("Cannot use both --live-api and --use-cached")
        return
    
    if args.live_api:
        print("⚠️  WARNING: You are about to make REAL API calls to D&D Beyond!")
        print("⏳ This will respect the 20-second minimum delay between requests")
        print("💾 Raw responses will be cached for future offline testing")
        response = input("Continue? [y/N]: ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
    
    # Set up test runner
    suite = unittest.TestLoader().loadTestsFromTestCase(RealDnDBeyondAPITests)
    
    # Configure test instances
    for test in suite:
        test._use_live_api = args.live_api
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Show cache summary
    if args.live_api:
        create_cache_summary()
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())