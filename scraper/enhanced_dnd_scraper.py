#!/usr/bin/env python3
"""
Enhanced D&D Beyond Character Scraper v6.0.0

A comprehensive character scraper for D&D Beyond with enhanced 2024/2014 rules support,
sophisticated rule version detection and optimized modular architecture.

Features in v6.0.0:
- Modular architecture with rule-aware calculators
- Sophisticated 2014/2024 rule version detection
- Enhanced Barbarian/Monk Unarmored Defense calculations
- Rule version management with user override options
- Streamlined JSON output optimized for v6.0.0 structure

Features:
- Automatic 2014/2024 rule detection with conservative fallback
- Enhanced spell grouping and deduplication by source
- Comprehensive ability score calculation with source breakdown
- Fixed AC calculations for Barbarian (10+DEX+CON) and Monk (10+DEX+WIS)
- Enhanced multiclass support and spell slot calculations
- Robust error handling with detailed diagnostics
- Complete character data export in structured JSON format

Author: Assistant
Version: 6.0.0
License: MIT
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# JSON encoder for EnhancedSpellInfo objects
class EnhancedSpellJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # Import here to avoid circular imports
        try:
            from scraper.core.calculators.services.spell_processor import EnhancedSpellInfo
            if isinstance(obj, EnhancedSpellInfo):
                return obj.to_dict()
        except ImportError:
            pass
        return super().default(obj)

# Add parent directory to path for module imports
sys.path.append(str(Path(__file__).parent.parent))

# v6.0.0 imports
from scraper.core.clients.factory import ClientFactory
from scraper.core.calculators.character_calculator import CharacterCalculator
from scraper.core.rules.version_manager import RuleVersionManager, RuleVersion
from shared.config.manager import get_config_manager
from discord.core.services.discord_integration import DiscordIntegrationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class EnhancedDnDScraper:
    """
    Main scraper class using v6.0.0 modular architecture.
    
    Provides full backward compatibility with v5.2.0 while leveraging
    the new rule-aware calculator system and enhanced detection.
    """
    
    def __init__(self, character_id: str, force_rule_version: Optional[RuleVersion] = None, 
                 no_html: bool = False, discord_config: Optional[Dict[str, Any]] = None, 
                 storage_dir: Optional[str] = None, discord_output: bool = False):
        """
        Initialize the enhanced scraper.
        
        Args:
            character_id: D&D Beyond character ID
            force_rule_version: Optional rule version override
            no_html: Whether to strip HTML from text fields
            discord_config: Optional Discord configuration for notifications
            storage_dir: Directory for storing character snapshots (for Discord)
            discord_output: Whether to also save JSON to discord directory
        """
        self.character_id = character_id
        self.force_rule_version = force_rule_version
        self.no_html = no_html
        self.discord_output = discord_output
        
        # Initialize Discord integration if config provided
        self.discord_service = None
        if discord_config:
            try:
                self.discord_service = DiscordIntegrationService(discord_config, storage_dir)
                if self.discord_service.is_available():
                    logger.info("Discord integration enabled")
                else:
                    logger.warning("Discord integration requested but services not available")
                    self.discord_service = None
            except Exception as e:
                logger.warning(f"Failed to initialize Discord integration: {e}")
                self.discord_service = None
        
        # Initialize v6.0.0 components
        self.config_manager = get_config_manager()
        self.rule_manager = RuleVersionManager()
        if force_rule_version:
            self.rule_manager.set_force_version(force_rule_version)
        
        self.client = ClientFactory.create_client(
            client_type='real',
            config_manager=self.config_manager
        )
        self.calculator = CharacterCalculator(
            config_manager=self.config_manager,
            rule_manager=self.rule_manager
        )
        
        logger.info(f"Enhanced D&D Scraper v6.0.0 initialized for character {character_id}")
    
    def _find_project_root(self) -> Path:
        """Find the project root directory containing character_data folder."""
        current = Path(__file__).parent.absolute()
        
        # Look for character_data directory going up the directory tree
        while current != current.parent:
            if (current / "character_data").exists():
                return current
            current = current.parent
        
        # If not found, use the parent of the scraper directory as fallback
        # This handles cases where we're running from outside the project
        fallback = Path(__file__).parent.parent.absolute()
        
        # On Windows, ensure we're using the correct path separators
        if fallback.name == "scraper":
            # We're in the scraper directory, go up one level
            fallback = fallback.parent
        
        return fallback
    
    def fetch_character_data(self) -> bool:
        """
        Fetch character data from D&D Beyond API.

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.debug("Fetching character data from API")
            self.raw_data = self.client.get_character(int(self.character_id))
            logger.info("Character data fetched successfully")

            # Check for campaign and fetch party inventory if available
            logger.debug("Checking for campaign data")
            campaign_data = self.raw_data.get('campaign', {})
            if campaign_data and campaign_data.get('id'):
                campaign_id = campaign_data['id']
                logger.info(f"Character is in campaign {campaign_id}, fetching party inventory")

                try:
                    logger.debug("Fetching party inventory")
                    party_inventory = self.client.get_party_inventory(campaign_id)
                    if party_inventory:
                        logger.debug("Assigning party inventory to raw data")
                        self.raw_data['party_inventory'] = party_inventory
                        logger.info("Party inventory fetched successfully")
                    else:
                        logger.info("No party inventory available for this campaign")
                except Exception as e:
                    logger.warning(f"Failed to fetch party inventory: {e}")
                    # Continue without party inventory - this is not a critical failure
            else:
                logger.debug("Character is not in a campaign, skipping party inventory")

            # Check if character has Artificer class or subclass before fetching infusions
            logger.debug("Checking for artificer classes")
            character_classes = self.raw_data.get('classes', [])
            artificer_levels = 0

            for cls in character_classes:
                if cls is None:
                    logger.warning("Encountered None class in classes array")
                    continue

                # Safely get class definition
                definition = cls.get('definition')
                class_name = definition.get('name', '') if definition else ''

                # Safely get subclass definition
                subclass_def = cls.get('subclassDefinition')
                subclass_name = subclass_def.get('name', '') if subclass_def else ''

                # Check for Artificer main class
                if class_name == 'Artificer':
                    artificer_levels += cls.get('level', 0)
                # Check for subclasses that grant infusions (like Armorer Fighter, etc.)
                elif any(keyword in subclass_name.lower() for keyword in ['artificer', 'infusion']):
                    artificer_levels += cls.get('level', 0)

            if artificer_levels > 0:
                logger.info(f"Character has {artificer_levels} Artificer levels, fetching infusion data")
                character_id = int(self.character_id)
                try:
                    # Fetch active infusions
                    infusions = self.client.get_character_infusions(character_id)
                    if infusions:
                        self.raw_data['infusions'] = infusions
                        logger.info("Character infusions fetched successfully")
                    else:
                        logger.debug("No infusions found for character")

                    # Fetch known infusions
                    known_infusions = self.client.get_known_infusions(character_id)
                    if known_infusions:
                        self.raw_data['known_infusions'] = known_infusions
                        logger.info("Known infusions fetched successfully")
                    else:
                        logger.debug("No known infusions found for character")

                except Exception as e:
                    logger.warning(f"Failed to fetch infusion data: {e}")
                    # Continue without infusions - this is not a critical failure
            else:
                logger.debug("Character has no Artificer levels, skipping infusion data")

            return True
        except Exception as e:
            logger.error(f"Failed to fetch character data: {e}")
            return False
    
    def calculate_character_data(self) -> Dict[str, Any]:
        """
        Calculate complete character data using v6.0.0 architecture.
        
        Returns:
            Complete character data dictionary
        """
        logger.info("Calculating complete character data using v6.0.0 architecture")
        
        # Use the enhanced calculator with rule version detection
        complete_data = self.calculator.calculate_complete_json(self.raw_data)
        
        # Add v6.0.0 metadata fields
        complete_data.update({
            'scraper_version': '6.0.0',
            'api_version': 'v5',
            'character_url': f"https://ddb.ac/characters/{self.character_id}",
            'generated_timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        })
        
        # Log rule version detection results
        rule_detection = self.rule_manager.detect_rule_version(self.raw_data, int(self.character_id))
        detection_summary = self.rule_manager.get_detection_summary(rule_detection)
        
        logger.info("Rule Version Detection:")
        for line in detection_summary.split('\n'):
            logger.info(f"  {line}")
        
        return complete_data
    
    def _get_rate_limit_file(self) -> Path:
        """Get path to rate limit tracking file."""
        project_root = self._find_project_root()
        return project_root / "character_data" / ".last_scrape"
    
    def _check_rate_limit(self) -> bool:
        """Check if enough time has passed since last scrape and wait if needed."""
        config_manager = get_config_manager()
        delay_seconds = config_manager.get_config_value('rate_limit', 'delay_between_requests', default=30)
        
        rate_limit_file = self._get_rate_limit_file()
        
        if rate_limit_file.exists():
            try:
                with open(rate_limit_file, 'r') as f:
                    last_scrape_time = float(f.read().strip())
                
                current_time = time.time()
                elapsed = current_time - last_scrape_time
                
                if elapsed < delay_seconds:
                    wait_time = delay_seconds - elapsed
                    logger.info(f"Rate limiting: waiting {wait_time:.1f} seconds since last scrape")
                    time.sleep(wait_time)
                    
            except (ValueError, FileNotFoundError):
                # Invalid or missing file, proceed without waiting
                pass
        
        # Update the last scrape time
        rate_limit_file.parent.mkdir(exist_ok=True)
        with open(rate_limit_file, 'w') as f:
            f.write(str(time.time()))
        
        return True
    
    def save_character_data(self, output_file: Optional[str] = None) -> str:
        """
        Save character data to JSON file with new directory structure.
        
        Args:
            output_file: Optional output filename
            
        Returns:
            Path to saved file
        """
        if not hasattr(self, 'raw_data'):
            raise ValueError("No character data to save. Call fetch_character_data() first.")
        
        # Calculate complete data
        complete_data = self.calculate_character_data()
        
        # Check if raw data should be saved automatically
        config_manager = get_config_manager()
        include_raw_data = config_manager.get_config_value('output', 'include_raw_data', default=False)
        if include_raw_data:
            # Save raw data to scraper/raw directory automatically
            self.save_raw_data()
        
        # Find project root and create directory structure
        project_root = self._find_project_root()
        scraper_dir = project_root / "character_data" / "scraper"
        discord_dir = project_root / "character_data" / "discord"
        scraper_dir.mkdir(exist_ok=True, parents=True)
        
        # Generate timestamp for filename
        from datetime import datetime
        timestamp = datetime.now().isoformat().replace(':', '-')
        
        # Determine output path
        if output_file:
            # Explicit output file specified - use exact path for backward compatibility
            output_path = Path(output_file)
        else:
            # Default: save to scraper directory
            output_file = f"character_{self.character_id}_{timestamp}.json"
            output_path = scraper_dir / output_file
        
        # Save to primary output path (scraper directory or explicit path)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(complete_data, f, indent=2, ensure_ascii=False, cls=EnhancedSpellJSONEncoder)
        
        logger.info(f"Character data saved to: {output_path.absolute()}")
        
        # If --discord flag is set, also save to discord directory
        if self.discord_output:
            discord_dir.mkdir(exist_ok=True, parents=True)
            discord_filename = f"character_{self.character_id}_{timestamp}.json"
            discord_path = discord_dir / discord_filename
            
            with open(discord_path, 'w', encoding='utf-8') as f:
                json.dump(complete_data, f, indent=2, ensure_ascii=False, cls=EnhancedSpellJSONEncoder)
            
            logger.info(f"Discord copy saved to: {discord_path.absolute()}")
        
        # Send Discord notification if Discord service is explicitly configured (CLI)
        if self.discord_service:
            try:
                import asyncio
                # Run Discord notification
                success = asyncio.run(self.discord_service.notify_character_saved(
                    character_id=int(self.character_id),
                    character_data=complete_data,
                    output_path=str(output_path.absolute())
                ))
                if success:
                    logger.info(f"Discord notification sent for character {self.character_id}")
                else:
                    logger.debug(f"Discord notification not sent for character {self.character_id}")
            except Exception as e:
                logger.warning(f"Discord notification failed: {e}")
        
        return str(output_path.absolute())
    
    def save_raw_data(self, raw_output_file: Optional[str] = None) -> str:
        """
        Save raw API response to file for debugging.
        
        Args:
            raw_output_file: Optional output filename (uses scraper/raw/ if not specified)
            
        Returns:
            Path to saved file
        """
        if not hasattr(self, 'raw_data'):
            raise ValueError("No raw data to save. Call fetch_character_data() first.")
        
        if raw_output_file:
            # Explicit file specified
            raw_path = Path(raw_output_file)
        else:
            # Default: save to scraper/raw directory
            project_root = self._find_project_root()
            raw_dir = project_root / "character_data" / "scraper" / "raw"
            raw_dir.mkdir(exist_ok=True, parents=True)
            
            from datetime import datetime
            timestamp = datetime.now().isoformat().replace(':', '-')
            raw_filename = f"character_{self.character_id}_{timestamp}_raw.json"
            raw_path = raw_dir / raw_filename
        
        with open(raw_path, 'w', encoding='utf-8') as f:
            json.dump(self.raw_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Raw API data saved to: {raw_path.absolute()}")
        return str(raw_path.absolute())


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser with full v5.2.0 compatibility."""
    parser = argparse.ArgumentParser(
        description="Enhanced D&D Beyond Character Scraper v6.0.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python enhanced_dnd_scraper.py YOUR_CHARACTER_ID
  python enhanced_dnd_scraper.py YOUR_CHARACTER_ID --output my_character.json
  python enhanced_dnd_scraper.py YOUR_CHARACTER_ID --verbose  # Verbose logging
  python enhanced_dnd_scraper.py YOUR_CHARACTER_ID --force-2024  # Force 2024 rules
  python enhanced_dnd_scraper.py YOUR_CHARACTER_ID --force-2014  # Force 2014 rules
  python enhanced_dnd_scraper.py YOUR_CHARACTER_ID --keep-html   # Preserve HTML in descriptions
  python enhanced_dnd_scraper.py YOUR_CHARACTER_ID --discord-notify --discord-webhook "https://discord.com/api/webhooks/..."

New in v6.0.0:
  - NEW: Modular architecture with rule-aware calculators
  - NEW: Sophisticated 2014/2024 rule version detection
  - NEW: Rule version override options (--force-2014, --force-2024)
  - NEW: HTML cleaning enabled by default for cleaner JSON (use --keep-html to preserve)
  - NEW: Discord integration for character change notifications (--discord-notify)
  - FIXED: Barbarian Unarmored Defense now correctly calculates 10+DEX+CON
  - FIXED: Monk Unarmored Defense now correctly calculates 10+DEX+WIS
  - ENHANCED: Streamlined JSON structure optimized for v6.0.0

Core features:
  - Full 2024 Player's Handbook compatibility with fallback to 2014 rules
  - Advanced spell grouping and deduplication by source
  - Comprehensive ability score calculation with source breakdown
  - Enhanced multiclass support and spell slot calculations
  - Robust error handling with detailed diagnostics
  - Complete character data export in structured JSON format

Dependencies:
  Required: requests, pydantic, pyyaml
  Optional: beautifulsoup4 (for better HTML parsing)

Note: This scraper only supports fetching live data from D&D Beyond.
Local JSON files are not supported.
        """
    )

    parser.add_argument(
        "character_id",
        help="D&D Beyond character ID (from character URL)"
    )

    parser.add_argument(
        "--output", "-o",
        help="Output JSON file (default: character name)"
    )


    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose debug logging"
    )


    parser.add_argument(
        "--raw-output",
        help="Save raw API response to specified file (for debugging/analysis)"
    )
    
    # New v6.0.0 options
    parser.add_argument(
        "--force-2014",
        action="store_true",
        help="Force 2014 rules regardless of character content"
    )
    
    parser.add_argument(
        "--force-2024",
        action="store_true",
        help="Force 2024 rules regardless of character content"
    )
    
    parser.add_argument(
        "--quick-compare",
        help="Quick compare against validation file (Phase 4 feature)"
    )
    
    parser.add_argument(
        "--batch",
        help="Process multiple character IDs from file (one per line) (Phase 4 feature)"
    )
    
    parser.add_argument(
        "--keep-html",
        action="store_true",
        help="Preserve HTML tags in descriptions and text fields (default: strip HTML for cleaner JSON)"
    )
    
    # Discord integration options
    parser.add_argument(
        "--discord-notify",
        action="store_true",
        help="Enable Discord notifications when saving character data"
    )
    
    parser.add_argument(
        "--discord-webhook",
        help="Discord webhook URL for notifications"
    )
    
    parser.add_argument(
        "--discord-config",
        help="Path to Discord configuration file (default: discord/discord_config.yml)"
    )
    
    parser.add_argument(
        "--discord",
        action="store_true",
        help="Save JSON output to discord directory for monitoring (character_data/discord/)"
    )

    return parser


def perform_quick_compare(character_data: Dict[str, Any], validation_file: str):
    """Perform quick comparison against validation data."""
    try:
        import json
        from pathlib import Path
        
        validation_path = Path(validation_file)
        if not validation_path.exists():
            logger.error(f"Validation file not found: {validation_file}")
            return
            
        # Load validation data
        with open(validation_path, 'r') as f:
            validation_data = json.load(f)
            
        # Use our existing data validator
        from scraper.core.validators.data_validator import DataValidator
        validator = DataValidator()
        
        # Quick comparison of key metrics
        character_id = character_data.get('character_id', 'unknown')
        result = validator.validate_character_data(character_id, character_data, validation_data)
        
        # Print summary
        if result.overall_passed:
            logger.info(f"✅ Quick Compare: {result.passed_tests}/{result.total_tests} tests passed")
        else:
            logger.warning(f"❌ Quick Compare: {result.failed_tests}/{result.total_tests} tests failed")
            
            # Show first few failures
            failed_results = [r for r in result.results if not r.passed]
            for i, failure in enumerate(failed_results[:3]):
                logger.warning(f"  FAIL: {failure.message}")
            if len(failed_results) > 3:
                logger.warning(f"  ... and {len(failed_results) - 3} more failures")
                
    except Exception as e:
        logger.error(f"Quick compare failed: {e}")


def process_batch_characters(batch_file: str, args):
    """Process multiple characters from a batch file."""
    import time
    from pathlib import Path
    
    batch_path = Path(batch_file)
    if not batch_path.exists():
        logger.error(f"Batch file not found: {batch_file}")
        return False
    
    # Handle HTML preservation configuration for batch processing
    if args.keep_html:
        config_manager = get_config_manager()
        config_manager.set_setting('output.clean_html', False)
        logger.info("HTML preservation enabled for batch processing (--keep-html flag)")
    
    # Read character IDs from file
    with open(batch_path, 'r') as f:
        character_ids = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    if not character_ids:
        logger.error("No character IDs found in batch file")
        return False
    
    logger.info(f"Processing {len(character_ids)} characters from batch file")
    
    success_count = 0
    failed_characters = []
    
    for i, character_id in enumerate(character_ids, 1):
        logger.info(f"Processing character {i}/{len(character_ids)}: {character_id}")
        
        try:
            # Handle Discord configuration for batch processing
            discord_config = None
            if hasattr(args, 'discord_notify') and args.discord_notify:
                config_manager = get_config_manager()
                discord_config = config_manager.get_config_value('discord', default={})
                
                # Override with command line arguments
                if hasattr(args, 'discord_webhook') and args.discord_webhook:
                    discord_config['webhook_url'] = args.discord_webhook
                    discord_config['enabled'] = True
                
                if hasattr(args, 'discord_config') and args.discord_config:
                    discord_config['config_file'] = args.discord_config
                
                # Enable Discord if webhook is provided
                if discord_config.get('webhook_url'):
                    discord_config['enabled'] = True
                else:
                    discord_config = None
            
            # Create scraper instance for this character
            scraper = EnhancedDnDScraper(
                character_id=character_id,
                force_rule_version=args.force_rule_version if hasattr(args, 'force_rule_version') else None,
                discord_config=discord_config,
                storage_dir="character_data",
                discord_output=getattr(args, 'discord', False)
            )
            
            # Check rate limiting before API call
            scraper._check_rate_limit()
            
            # Fetch character data
            if not scraper.fetch_character_data():
                failed_characters.append(f"{character_id}: Failed to fetch data")
                continue
            
            # Save character data (will use Discord-compatible naming)
            output_path = scraper.save_character_data()
            
            # Save raw data if requested
            if args.raw_output:
                import time
                character_data_dir = Path("character_data")
                character_data_dir.mkdir(exist_ok=True)
                raw_file = str(character_data_dir / f"raw_{character_id}_{int(time.time())}.json")
                scraper.save_raw_data(raw_file)
            
            success_count += 1
            logger.info(f"✅ {character_id}: Saved to {output_path}")
            
        except Exception as e:
            failed_characters.append(f"{character_id}: {str(e)}")
            logger.error(f"❌ Failed to process {character_id}: {e}")
        
        # Rate limiting: wait 30 seconds between API calls (except for last character)
        if i < len(character_ids):
            logger.info("Waiting 30 seconds for API rate limiting...")
            time.sleep(30)
    
    # Summary
    logger.info(f"\n=== Batch Processing Complete ===")
    logger.info(f"Successfully processed: {success_count}/{len(character_ids)} characters")
    
    if failed_characters:
        logger.warning(f"Failed characters:")
        for failure in failed_characters:
            logger.warning(f"  - {failure}")
        return False
    
    return True


def main():
    """Main entry point with full v5.2.0 compatibility."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Set up logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Validate rule version arguments
    if args.force_2014 and args.force_2024:
        logger.error("Cannot specify both --force-2014 and --force-2024")
        sys.exit(1)
    
    # Determine forced rule version
    force_rule_version = None
    if args.force_2014:
        force_rule_version = RuleVersion.RULES_2014
        logger.info("Forcing 2014 rules (user override)")
    elif args.force_2024:
        force_rule_version = RuleVersion.RULES_2024
        logger.info("Forcing 2024 rules (user override)")
    
    # Store for batch processing
    args.force_rule_version = force_rule_version

    # Handle batch processing
    if args.batch:
        try:
            success = process_batch_characters(args.batch, args)
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            logger.info("Batch processing cancelled by user")
            sys.exit(1)
        except Exception as e:
            logger.error(f"❌ Batch processing error: {e}")
            sys.exit(1)
    
    # character_id is now required by argparse, so no need to validate here

    try:
        # Handle HTML preservation configuration
        if args.keep_html:
            # Update config to disable HTML cleaning (preserve HTML)
            config_manager = get_config_manager()
            config_manager.set_setting('output.clean_html', False)
            logger.info("HTML preservation enabled (--keep-html flag)")
        
        # Handle Discord configuration
        discord_config = None
        if args.discord_notify:
            config_manager = get_config_manager()
            discord_config = config_manager.get_config_value('discord', default={})
            
            # Override with command line arguments
            if args.discord_webhook:
                discord_config['webhook_url'] = args.discord_webhook
                discord_config['enabled'] = True
            
            if args.discord_config:
                discord_config['config_file'] = args.discord_config
            
            # Enable Discord if webhook is provided
            if discord_config.get('webhook_url'):
                discord_config['enabled'] = True
                logger.info("Discord notifications enabled via command line")
            else:
                logger.warning("Discord notifications requested but no webhook URL provided")
                discord_config = None
        
        # Create scraper instance
        scraper = EnhancedDnDScraper(
            character_id=args.character_id,
            force_rule_version=force_rule_version,
            discord_config=discord_config,
            storage_dir="character_data",
            discord_output=args.discord
        )

        # Check rate limiting before API call
        scraper._check_rate_limit()

        # Fetch character data
        if not scraper.fetch_character_data():
            logger.error("Failed to fetch character data")
            sys.exit(1)

        # Save character data
        output_path = scraper.save_character_data(args.output)
        
        # Save raw data if requested
        if args.raw_output:
            # Save raw data to character_data directory with consistent naming
            character_data_dir = Path("character_data")
            character_data_dir.mkdir(exist_ok=True)
            raw_file = str(character_data_dir / f"raw_{args.character_id}_{int(time.time())}.json")
            scraper.save_raw_data(raw_file)
            
        # Quick compare if requested
        if args.quick_compare:
            # Get the character data
            character_data = scraper.calculate_character_data()
            perform_quick_compare(character_data, args.quick_compare)

        logger.info(f"✅ Character data successfully processed and saved to: {output_path}")

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error processing character: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()