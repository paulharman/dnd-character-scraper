#!/usr/bin/env python3
"""
D&D Beyond JSON to Markdown Parser v6.0.0 - Refactored with Factory Pattern

Converts enhanced_dnd_scraper.py JSON output to D&D UI Toolkit markdown format
using the new modular architecture with dependency injection.

This is the refactored version that uses the factory pattern for better
maintainability and testability.

Author: Assistant
Version: 6.0.0-refactored
License: MIT
"""

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import subprocess
import unicodedata
from pathlib import Path
from typing import Dict, Any, Optional
import functools

# Force all print statements to flush immediately for subprocess compatibility
print = functools.partial(print, flush=True)

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Import the config systems (make optional for basic functionality)
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
try:
    from shared.config.manager import ConfigManager
    from discord.core.storage.archiving import SnapshotArchiver
    from scraper.core.calculators.character_calculator import CharacterCalculator
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Parser:   Advanced features not available due to missing dependencies: {e}")
    ConfigManager = None
    SnapshotArchiver = None
    CharacterCalculator = None
    ADVANCED_FEATURES_AVAILABLE = False

# Import Discord integration (optional)
try:
    from discord.services.parser_integration import send_discord_notifications, send_party_inventory_notification
    DISCORD_INTEGRATION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Parser:   Discord integration not available: {e}")
    DISCORD_INTEGRATION_AVAILABLE = False

# Handle relative imports for both direct execution and module import
try:
    from shared.config import ParserConfigManager
    from .factories.generator_factory import GeneratorFactory
except ImportError:
    # When run directly, use absolute imports
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    from config import ParserConfigManager
    from factories.generator_factory import GeneratorFactory

# Logging already configured above


class CharacterMarkdownGenerator:
    """
    Wrapper class for compatibility with existing code.
    
    This class provides the same interface as the original but uses
    the new factory pattern internally.
    """
    
    def __init__(self, character_data: Dict[str, Any], parser_config: ParserConfigManager = None,
                 spells_path: str = None, use_enhanced_spells: bool = None):
        """
        Initialize the markdown generator.
        
        Args:
            character_data: Complete character data from scraper
            parser_config: Parser configuration manager (if None, creates default)
            spells_path: Path to enhanced spell files (overrides config)
            use_enhanced_spells: Whether to use enhanced spell data (overrides config)
        """
        # Store character data directly
        self.character_data = character_data
        
        # Initialize config
        self.config = parser_config or ParserConfigManager()
        
        # Resolve paths using config system
        paths = self.config.resolve_paths()
        
        # Use provided values or fall back to config defaults
        self.spells_path = spells_path or str(paths["spells"])
        self.use_enhanced_spells = use_enhanced_spells if use_enhanced_spells is not None else self.config.get_default("enhance_spells", True)
        
        # These are now always enabled for consistent behavior
        self.use_dnd_ui_toolkit = True      # Always use DnD UI Toolkit blocks
        self.use_yaml_frontmatter = True    # Always include YAML frontmatter
        
        # Extract character info from current v6.0.0 structure
        # Try current format first (character_info), then backup format (basic_info)
        character_info = self.character_data.get('character_info', {})
        basic_info = self.character_data.get('basic_info', {})
        meta_info = self.character_data.get('meta', {})
        
        # Use character_info if available (current format), otherwise basic_info (backup format)
        info_source = character_info if character_info else basic_info
        self.character_name = info_source.get('name', 'Unknown Character')
        self.character_level = info_source.get('level', 1)
        self.rule_version = meta_info.get('rule_version', character_info.get('rule_version', 'unknown'))
        
        # Create the generator using the factory
        self.factory = GeneratorFactory()
        template_type = 'ui_toolkit' if self.use_dnd_ui_toolkit else 'obsidian'
        
        self.generator = self.factory.create_generator(
            use_yaml_frontmatter=self.use_yaml_frontmatter,
            use_enhanced_spells=self.use_enhanced_spells,
            template_type=template_type
        )
        
        logger.info(f"Parser:   Initialized CharacterMarkdownGenerator for {self.character_name} (Level {self.character_level})")
    
    def generate_markdown(self) -> str:
        """
        Generate complete character markdown.
        
        Returns:
            Complete markdown content
        """
        try:
            return self.generator.generate_markdown(self.character_data)
        except Exception as e:
            logger.error(f"Parser:   Failed to generate markdown for {self.character_name}: {e}")
            raise
    
    def generate_section(self, section_name: str) -> str:
        """
        Generate a specific section of the character sheet.
        
        Args:
            section_name: Name of the section to generate
            
        Returns:
            Generated section content
        """
        try:
            return self.generator.generate_section(section_name, self.character_data)
        except Exception as e:
            logger.error(f"Parser:   Failed to generate {section_name} section for {self.character_name}: {e}")
            raise
    
    def get_available_sections(self) -> list:
        """
        Get list of available section names.
        
        Returns:
            List of available section names
        """
        return self.generator.get_available_sections()
    
    def validate_character_data(self) -> bool:
        """
        Validate character data.
        
        Returns:
            True if data is valid, False otherwise
        """
        return self.generator.validate_character_data(self.character_data)
    
    def get_validation_errors(self) -> list:
        """
        Get validation errors from the last validation.
        
        Returns:
            List of validation error messages
        """
        return self.generator.get_validation_errors()


def process_character_json(json_file: str, output_dir: str = None, **kwargs) -> str:
    """
    Process a single character JSON file.
    
    Args:
        json_file: Path to the character JSON file
        output_dir: Directory to save the output file (optional)
        **kwargs: Additional configuration options
        
    Returns:
        Generated markdown content
    """
    try:
        # Load character data
        with open(json_file, 'r', encoding='utf-8') as f:
            character_data = json.load(f)
        
        # Create generator
        generator = CharacterMarkdownGenerator(character_data, **kwargs)
        
        # Generate markdown
        markdown = generator.generate_markdown()
        
        # Save to file if output directory is specified
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Create output filename
            character_name = generator.character_name
            safe_name = re.sub(r'[^\w\s-]', '', character_name).strip()
            safe_name = re.sub(r'[-\s]+', '-', safe_name)
            
            output_file = output_path / f"{safe_name}.md"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            logger.info(f"Parser:   Saved {character_name} to {output_file}")
        
        return markdown
        
    except Exception as e:
        logger.error(f"Parser:   Failed to process {json_file}: {e}")
        raise


async def trigger_discord_notifications(character_data: Dict[str, Any], character_id: str, verbose: bool = False) -> Dict[str, bool]:
    """
    Trigger Discord notifications for both character and party inventory changes.

    Args:
        character_data: Complete character data dictionary
        character_id: The character ID
        verbose: Enable verbose logging
    """
    try:
        if not DISCORD_INTEGRATION_AVAILABLE:
            logger.debug("Parser:   Discord integration not available, skipping notifications")
            return {'character': False, 'party_inventory': False}

        # Check if Discord integration is enabled in parser config
        discord_enabled = True  # Default to enabled
        try:
            import yaml
            project_root = Path(__file__).parent.parent
            parser_config_path = project_root / "config" / "parser.yaml"

            if parser_config_path.exists():
                with open(parser_config_path, 'r') as f:
                    parser_config = yaml.safe_load(f) or {}
                discord_enabled = parser_config.get('parser', {}).get('discord', {}).get('enabled', True)
        except Exception as e:
            logger.debug(f"Parser:   Discord config check failed, defaulting to enabled: {e}")

        if not discord_enabled:
            logger.debug("Parser:   Discord integration disabled in parser config")
            return {'character': False, 'party_inventory': False}

        logger.info(f"Parser:   Triggering Discord notifications for character {character_id}")

        # Send both character and party inventory notifications
        results = await send_discord_notifications(character_data)

        # Report results
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)

        if success_count > 0:
            logger.info(f"Parser:   Discord notifications sent: {success_count}/{total_count} successful")

            if results.get('character'):
                print("[NOTIFICATION] Character Discord notification sent successfully", flush=True)

            if results.get('party_inventory'):
                print("[NOTIFICATION] Party inventory Discord notification sent successfully", flush=True)
        else:
            logger.debug("Parser:   No Discord notifications sent (no changes detected)")
            if verbose:
                print("[INFO] No character or party inventory changes detected", flush=True)

        return results

    except Exception as e:
        logger.warning(f"Parser:   Error sending Discord notifications: {e}")
        return {'character': False, 'party_inventory': False}


async def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Convert D&D Beyond JSON to Markdown with YAML frontmatter and DnD UI Toolkit blocks'
    )
    parser.add_argument('character_id', help='D&D Beyond character ID')
    parser.add_argument('output_path', nargs='?', help='Output markdown file path (default: character_data/parser/current_output_{character_id}.md)')
    
    # Core options
    parser.add_argument('--config', help='Path to parser configuration file (default: config/parser.yaml)')
    parser.add_argument('--scraper-path', type=Path, help='Path to enhanced_dnd_scraper.py script')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    # Spell enhancement options
    parser.add_argument('--no-enhance-spells', action='store_true', help='Disable enhanced spell data, use API only')
    parser.add_argument('--spells-path', help='Path to enhanced spell files directory')
    
    # Rule version options
    parser.add_argument('--force-2014', action='store_true', help='Force 2014 rules regardless of character content')
    parser.add_argument('--force-2024', action='store_true', help='Force 2024 rules regardless of character content')
    
    # Legacy compatibility options
    parser.add_argument('-o', '--output-dir', help='Output directory for markdown files')
    parser.add_argument('--enhanced-spells', action='store_true', help='Use enhanced spell data (inverse of --no-enhance-spells)')
    parser.add_argument('--validate-only', action='store_true', help='Only validate the character data')
    parser.add_argument('--section', help='Generate only a specific section')
    parser.add_argument('--list-sections', action='store_true', help='List available sections')
    
    args = parser.parse_args()
    
    # Note: Default output path will be set after loading character data to use character name
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # New architecture: Call scraper first, then read from scraper directory
        character_id = args.character_id
        project_root = Path(__file__).parent.parent
        
        # Step 1: Call the scraper to get fresh data
        logger.info(f"Parser:   Calling scraper for character {character_id})")
        scraper_script = project_root / "scraper" / "enhanced_dnd_scraper.py"
        
        if not scraper_script.exists():
            logger.error(f"Parser:   Scraper script not found at {scraper_script}")
            sys.exit(1)
        
        # Build scraper command
        scraper_cmd = [sys.executable, str(scraper_script), character_id]
        
        # Add verbose flag if requested
        if args.verbose:
            scraper_cmd.append('--verbose')
        
        # Check if Discord is enabled in parser config and add --discord flag
        try:
            import yaml
            parser_config_path = project_root / "config" / "parser.yaml"
            with open(parser_config_path, 'r') as f:
                parser_config = yaml.safe_load(f)
            
            discord_enabled = parser_config.get('parser', {}).get('discord', {}).get('enabled', True)
            logger.debug(f"Parser:   Discord config check: enabled={discord_enabled}")
            if discord_enabled:
                scraper_cmd.append('--discord')
                logger.info("Parser:   Discord enabled: scraper will save copy to discord directory")
            else:
                logger.info("Parser:   Discord disabled in parser config")
        except Exception as e:
            # If config check fails, default to enabling Discord
            scraper_cmd.append('--discord')
            logger.info("Parser:   Discord enabled by default (config check failed)")
            logger.debug(f"Parser:   Config check error: {e}")
        
        # Run the scraper
        logger.info(f"Parser:   Running: {' '.join(scraper_cmd)}")
        try:
            result = subprocess.run(
                scraper_cmd,
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Parser:   Scraper failed with exit code {result.returncode}")
                if result.stderr:
                    logger.error(f"Parser:   Scraper error: {result.stderr}")
                if result.stdout:
                    logger.info(f"Parser:   Scraper output: {result.stdout}")
                print(f"Scraper failed (exit code {result.returncode})", file=sys.stderr)
                sys.exit(1)
            else:
                logger.info("Parser:   Scraper completed successfully")
                if result.stdout:
                    # Show scraper output for transparency
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            logger.info(f"Scraper: {line.strip()}")
                            
        except subprocess.TimeoutExpired:
            logger.error("Parser:   Scraper timed out after 2 minutes")
            print("Scraper timed out", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            logger.error(f"Parser:   Failed to run scraper: {e}")
            print(f"Failed to run scraper: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Step 2: Read the scraped data from scraper directory
        scraper_data_dir = project_root / "character_data" / "scraper"
        
        # Look for the most recent JSON file for this character ID in scraper directory
        pattern = f"character_{character_id}_*.json"
        json_files = list(scraper_data_dir.glob(pattern))
        
        if not json_files:
            logger.error(f"Parser:   No JSON files found in scraper directory for character ID {character_id}")
            logger.info(f"Parser:   Looking in: {scraper_data_dir}")
            print(f"No character data found for ID {character_id}", file=sys.stderr)
            sys.exit(1)
        
        # Use the most recent file (should be the one just created by scraper)
        json_file = str(max(json_files, key=lambda f: f.stat().st_mtime))
        logger.info(f"Parser:   Using scraped character file: {Path(json_file).name}")
        
        # Load character data
        with open(json_file, 'r', encoding='utf-8') as f:
            character_data = json.load(f)
        
        # Set default output path using character name if none provided
        if not args.output_path:
            character_info = character_data.get('character_info', {})
            character_name = character_info.get('name', f'character_{args.character_id}')
            # Clean the character name for use as filename
            safe_name = "".join(c for c in character_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            args.output_path = f"{safe_name}.md"
            logger.info(f"Parser:   No output path provided, using default: {args.output_path}")
        else:
            logger.info(f"Parser:   Output path provided: {args.output_path}")
        
        # Handle spell enhancement logic
        # Default is to use enhanced spells unless explicitly disabled
        use_enhanced_spells = True
        if args.no_enhance_spells:
            use_enhanced_spells = False
        elif args.enhanced_spells:
            use_enhanced_spells = True
        
        # Create generator with specified options
        # YAML frontmatter and DnD UI Toolkit are now always enabled
        generator = CharacterMarkdownGenerator(
            character_data,
            spells_path=args.spells_path,
            use_enhanced_spells=use_enhanced_spells
        )
        
        # Handle different operations
        if args.list_sections:
            sections = generator.get_available_sections()
            print("Available sections:")
            for section in sections:
                print(f"  - {section}")
            return
        
        if args.validate_only:
            is_valid = generator.validate_character_data()
            if is_valid:
                print("[OK] Character data is valid")
            else:
                print("[ERROR] Character data is invalid")
                errors = generator.get_validation_errors()
                for error in errors:
                    print(f"  - {error}")
            return
        
        if args.section:
            # Generate specific section
            section_content = generator.generate_section(args.section)
            print(section_content)
            return
        
        # Generate full markdown
        markdown_content = generator.generate_markdown()
        
        # Determine output path based on new directory structure
        if Path(args.output_path).is_absolute():
            # Absolute path provided - use it directly for backward compatibility
            output_path = Path(args.output_path)
            logger.info(f"Parser:   Using absolute path: {output_path}")
        else:
            # Relative path - save to parser directory
            parser_dir = project_root / "character_data" / "parser"
            parser_dir.mkdir(exist_ok=True, parents=True)
            output_path = parser_dir / args.output_path
            logger.info(f"Parser:   Using relative path in parser dir: {output_path}")

        # Unicode-aware path resolution: if the target file doesn't exist,
        # try to find the correct file despite encoding corruption.
        # Obsidian's Execute Code plugin can mangle Unicode characters in paths
        # (e.g. ü → Ã¼) when UTF-8 bytes pass through a Latin-1 encoding step.
        if not output_path.exists() and output_path.parent.exists():
            # First try: fix UTF-8 mojibake (ü mangled to Ã¼)
            try:
                fixed_name = output_path.name.encode('latin-1').decode('utf-8')
                fixed_path = output_path.parent / fixed_name
                if fixed_path.exists():
                    logger.info(f"Parser:   Fixed mojibake path: {output_path.name} -> {fixed_name}")
                    output_path = fixed_path
            except (UnicodeDecodeError, UnicodeEncodeError):
                pass

            # Second try: accent-stripping fallback
            if not output_path.exists():
                def _strip_accents(s: str) -> str:
                    return ''.join(
                        c for c in unicodedata.normalize('NFKD', s)
                        if not unicodedata.combining(c)
                    )
                target_stripped = _strip_accents(output_path.name.lower())
                for existing_file in output_path.parent.iterdir():
                    if existing_file.is_file() and _strip_accents(existing_file.name.lower()) == target_stripped:
                        logger.info(f"Parser:   Found Unicode-variant match: {existing_file.name}")
                        output_path = existing_file
                        break

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"Parser:   [OK] Character markdown saved to: {output_path.absolute()}")
        
        # Trigger Discord notifications for both character and party inventory changes
        try:
            # Capture stdout from notification system to get change details
            import io
            from contextlib import redirect_stdout

            captured_output = io.StringIO()

            # Capture the notification output which includes PARSER_CHANGES and PARSER_DETAIL
            with redirect_stdout(captured_output):
                results = await trigger_discord_notifications(character_data, args.character_id, verbose=args.verbose)

            notification_output = captured_output.getvalue()

            # Parse change information from the captured output
            character_changes = results.get('character', False)
            party_changes = results.get('party_inventory', False)

            # Extract change count and details from notification output
            change_count = 0
            change_details = []

            for line in notification_output.split('\n'):
                if line.startswith('PARSER_CHANGES:'):
                    try:
                        change_count = int(line.split(':')[1])
                    except:
                        pass
                elif line.startswith('PARSER_DETAIL:'):
                    detail = line.replace('PARSER_DETAIL:', '').strip()
                    if detail:
                        change_details.append(detail)

            # Print status summary to stdout (visible in Obsidian console)
            if character_changes or party_changes or change_count > 0:
                if change_count > 0:
                    print(f"{change_count} change(s) detected:")
                    for detail in change_details[:10]:
                        print(f"  - {detail}")
                    if len(change_details) > 10:
                        print(f"  ... and {len(change_details) - 10} more")
                else:
                    print("Changes detected.")

                if party_changes:
                    print("Party inventory changes detected.")

                print("Discord notification sent.")
            else:
                print("No changes detected.")

            print("Character refreshed!")
            print("Reload file to see changes.")

        except Exception as e:
            logger.warning(f"Parser:   Failed to trigger Discord notifications: {e}")
            print("Discord notification failed.")
            print("Character refreshed!")
            print("Reload file to see changes.")
        
    except Exception as e:
        logger.error(f"Parser:   Error processing character: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())