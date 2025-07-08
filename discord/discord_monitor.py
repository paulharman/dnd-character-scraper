#!/usr/bin/env python3
"""
Discord Character Monitor - Main Script

Monitors D&D Beyond characters for changes and sends Discord notifications.
Supports single character monitoring, multiple characters, and configurable
filtering and formatting options.
"""

import asyncio
import argparse
import logging
import sys
import signal
from pathlib import Path
from typing import List, Optional, Set, Tuple
from datetime import datetime, timedelta
import yaml
import os
import functools

# Force all print statements to flush immediately for subprocess compatibility
print = functools.partial(print, flush=True)

def setup_console_encoding():
    """Configure console encoding for Windows compatibility."""
    if sys.platform == "win32":
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='windows-1252', errors='replace')
                sys.stderr.reconfigure(encoding='windows-1252', errors='replace')
                return True
        except Exception:
            return False
    return True

console_supports_utf8 = setup_console_encoding()

class SafeFormatter(logging.Formatter):
    """Custom formatter that safely handles Unicode characters for console output."""
    
    def format(self, record):
        try:
            return super().format(record)
        except UnicodeEncodeError:
            record.msg = self._make_safe_for_console(str(record.msg))
            if record.args:
                record.args = tuple(self._make_safe_for_console(str(arg)) for arg in record.args)
            return super().format(record)
    
    def _make_safe_for_console(self, text):
        """Replace Unicode characters with safe console equivalents."""
        emoji_replacements = {
            '🎲': '[DICE]',
            '🔴': '[CRIT]',
            '🟠': '[HIGH]',
            '🟡': '[MED]',
            '🔵': '[LOW]',
            '⬆️': '[UP]',
            '⬇️': '[DOWN]',
            '🔄': '[MOD]',
            '➕': '[ADD]',
            '➖': '[REM]',
            '✨': '[MAGIC]',
            '❤️': '[HP]',
            '🛡️': '[AC]',
            '💪': '[STR]',
            '🎯': '[LVL]',
            '⭐': '[EXP]',
            '🎱': '[SLOTS]',
            '🎒': '[INV]',
            '⚔️': '[EQUIP]',
            '💰': '[GOLD]',
            '🎨': '[SKILL]',
            '🔧': '[PROF]',
            '🏆': '[FEAT]',
            '📚': '[CLASS]',
            '🆕': '[NEW]',
            '📋': '[OTHER]',
            '✅': '[OK]',
            '❌': '[FAIL]'
        }
        
        safe_text = text
        for emoji, replacement in emoji_replacements.items():
            safe_text = safe_text.replace(emoji, replacement)
        
        return safe_text

# Setup module paths
project_root = Path(__file__).absolute().parent.parent
discord_root = Path(__file__).absolute().parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(discord_root) not in sys.path:
    sys.path.insert(0, str(discord_root))

from services.notification_manager import NotificationManager, NotificationConfig
from services.discord_service import DiscordService
from formatters.discord_formatter import FormatType
from services.change_detection_service import ChangePriority

from scraper.enhanced_dnd_scraper import EnhancedDnDScraper
from src.config.manager import get_config_manager
from src.storage.archiving import SnapshotArchiver

logger = logging.getLogger(__name__)


class DiscordMonitor:
    """
    Main Discord monitoring application.
    
    Features:
    - Single or multiple character monitoring
    - Configurable check intervals
    - Automatic scraping and change detection
    - Graceful shutdown handling
    - Configuration file support
    """
    
    def __init__(self, config_path: str, use_party_mode: bool = False):
        self.config_path = Path(config_path)
        self.config = None
        self.notification_manager = None
        self.storage = None
        self.scraper = None
        self.running = False
        self.character_ids = []
        self.archiver = None
        self.use_party_mode = use_party_mode
        
        # Load configuration
        self._load_config()
        
        logger.info(f"Discord monitor initialized with config: {config_path}")
    
    def _load_config(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            raw_config = yaml.safe_load(f)
        
        # Validate required fields
        required_fields = ['webhook_url']
        for field in required_fields:
            if field not in raw_config:
                raise ValueError(f"Required configuration field missing: {field}")
        
        self.config = raw_config
        logger.info("Configuration loaded successfully")
    
    async def initialize(self, skip_webhook_test=False):
        """Initialize all services and connections."""
        # Set up logging level
        log_level = self.config.get('log_level', 'INFO')
        logging.getLogger().setLevel(getattr(logging, log_level.upper()))
        
        # Configure storage directory
        configured_storage_dir = self.config.get('storage_dir', '../character_data')
        if Path(configured_storage_dir).is_absolute():
            self.storage_dir = Path(configured_storage_dir)
        else:
            self.storage_dir = project_root / configured_storage_dir.lstrip('../')
        self.storage_dir.mkdir(exist_ok=True)
        self.storage = None
        
        # Initialize scraper configuration
        self.session_cookie = self.config.get('session_cookie')
        self.config_manager = get_config_manager()
        
        # Prepare character IDs based on mode
        if self.use_party_mode:
            # Party mode: use party config
            if 'party' in self.config and self.config['party']:
                self.character_ids = [int(char['character_id']) for char in self.config['party']]
                logger.info(f"Using party mode with {len(self.character_ids)} characters")
            else:
                raise ValueError("Party mode requested but no party configuration found")
        else:
            # Single character mode (default)
            if 'character_id' in self.config:
                self.character_ids = [int(self.config['character_id'])]
                logger.info(f"Using single character mode: {self.character_ids[0]}")
            elif 'characters' in self.config:
                # Legacy multiple character support (deprecated - use party instead)
                self.character_ids = [int(char['character_id']) for char in self.config['characters']]
                logger.warning("Using deprecated 'characters' config. Consider using 'party' with --party flag instead.")
            else:
                raise ValueError("No character_id specified in configuration")
        
        # Initialize archiver
        self.archiver = SnapshotArchiver()
        
        # Set up notification configuration
        notification_config = self._create_notification_config()
        self.notification_manager = NotificationManager(
            self.storage, 
            notification_config,
            str(self.storage_dir)
        )
        
        # Test Discord connection if needed
        if not skip_webhook_test:
            async with DiscordService(
                webhook_url=notification_config.webhook_url,
                username=notification_config.username
            ) as discord:
                test_success = await discord.test_webhook()
                if not test_success:
                    raise RuntimeError("Discord webhook test failed")
        
        logger.info("All services initialized successfully")
    
    def _create_notification_config(self) -> NotificationConfig:
        """Create notification configuration from loaded config."""
        # Parse format type
        format_type = FormatType(self.config.get('format_type', 'detailed'))
        
        # Parse minimum priority
        min_priority_name = self.config.get('min_priority', 'LOW')
        min_priority = ChangePriority[min_priority_name.upper()]
        
        # Parse filtering configuration
        filtering = self.config.get('filtering', {})
        include_groups = None
        exclude_groups = None
        
        if 'change_types' in filtering:
            change_types = filtering['change_types']
            if isinstance(change_types, list):
                include_groups = self._convert_change_types_to_groups(change_types)
                logger.info(f"Using change types filter: {sorted(change_types)}")
            else:
                logger.warning("change_types must be a list, ignoring")
        elif 'preset' in filtering:
            preset_name = filtering['preset']
            include_groups, exclude_groups = self._get_preset_groups(preset_name)
            logger.info(f"Using filtering preset: '{preset_name}'")
        else:
            if 'include_groups' in filtering:
                include_groups = set(filtering['include_groups'])
                logger.info(f"Using custom include groups: {sorted(include_groups)}")
            if 'exclude_groups' in filtering:
                exclude_groups = set(filtering['exclude_groups'])
                logger.info(f"Using custom exclude groups: {sorted(exclude_groups)}")
        
        # Default to all change types (excluding meta) if no filtering specified
        if not filtering:
            default_change_types = [ct for ct in self._get_all_change_types() if ct != 'meta']
            include_groups = self._convert_change_types_to_groups(default_change_types)
            logger.info(f"No filtering configured - using default change types: {sorted(default_change_types)}")
        
        # Parse notifications settings
        notifications = self.config.get('notifications', {})
        advanced = self.config.get('advanced', {})
        rate_limit = advanced.get('rate_limit', {})
        
        return NotificationConfig(
            webhook_url=self.config['webhook_url'],
            username=notifications.get('username', 'D&D Beyond Monitor'),
            avatar_url=notifications.get('avatar_url'),
            format_type=format_type,
            max_changes_per_notification=advanced.get('max_changes_per_notification', 20),
            min_priority=min_priority,
            include_groups=include_groups,
            exclude_groups=exclude_groups,
            rate_limit_requests_per_minute=rate_limit.get('requests_per_minute', 3),
            rate_limit_burst=rate_limit.get('burst_limit', 1),
            timezone=notifications.get('timezone', 'UTC'),
            send_summary_for_multiple=len(self.character_ids) > 1,
            delay_between_messages=advanced.get('delay_between_messages', 2.0)
        )
    
    def _get_all_change_types(self) -> List[str]:
        """Get all available change types."""
        return [
            'level',
            'experience',
            'hit_points',
            'armor_class',
            'ability_scores',
            'spells_known',
            'spell_slots',
            'inventory_items',
            'equipment',
            'currency',
            'skills',
            'proficiencies',
            'feats',
            'class_features',
            'appearance',
            'background',
            'meta'
        ]
    
    def _convert_change_types_to_groups(self, change_types: List[str]) -> Set[str]:
        """Convert change types to group patterns for filtering."""
        change_type_to_groups = {
            'level': ['basic'],
            'experience': ['basic'],
            'hit_points': ['combat'],
            'armor_class': ['combat'],
            'ability_scores': ['abilities'],
            'spells_known': ['spells'],
            'spell_slots': ['spells'],
            'inventory_items': ['inventory'],
            'equipment': ['inventory'],
            'currency': ['inventory'],
            'skills': ['skills'],
            'proficiencies': ['skills'],
            'feats': ['skills'],
            'class_features': ['basic'],
            'appearance': ['appearance'],
            'background': ['backstory'],
            'meta': ['meta']
        }
        
        groups = set()
        for change_type in change_types:
            if change_type in change_type_to_groups:
                groups.update(change_type_to_groups[change_type])
            else:
                logger.warning(f"Unknown change type: {change_type}")
        
        return groups
    
    def _get_preset_groups(self, preset: str) -> Tuple[Optional[Set[str]], Optional[Set[str]]]:
        """Get include/exclude groups for a preset filter."""
        presets = {
            'combat_only': (
                {'combat', 'spells.slots'},
                {'meta', 'appearance', 'backstory'}
            ),
            'level_up': (
                {'basic', 'combat', 'abilities', 'spells', 'skills'},
                {'meta', 'appearance'}
            ),
            'roleplay_session': (
                {'basic', 'inventory', 'currency'},
                {'meta', 'abilities'}
            ),
            'shopping_trip': (
                {'inventory', 'currency', 'equipment'},
                {'meta', 'spells', 'abilities'}
            ),
            'minimal': (
                {'basic'},
                {'meta', 'appearance', 'backstory'}
            ),
            'debug': (
                None,  # Include all
                None   # Exclude none
            )
        }
        
        return presets.get(preset, (None, None))
    
    async def scrape_character(self, character_id: int) -> bool:
        """
        Scrape a character and store the data.
        
        Args:
            character_id: Character ID to scrape
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Scraping character {character_id}")
            
            # Create scraper for this character
            scraper = EnhancedDnDScraper(
                character_id=str(character_id), 
                session_cookie=self.session_cookie
            )
            
            # Fetch and calculate character data
            if not scraper.fetch_character_data():
                logger.warning(f"Failed to fetch data for character {character_id}")
                return False
            
            character_data = scraper.calculate_character_data()
            
            if not character_data:
                logger.warning(f"No data returned for character {character_id}")
                return False
            
            # Save current snapshot with timestamp
            timestamp = datetime.now().isoformat()
            filename = f"character_{character_id}_{timestamp.replace(':', '-')}.json"
            
            with open(self.storage_dir / filename, 'w') as f:
                import json
                json.dump(character_data, f, indent=2, default=str)
            
            logger.info(f"Saved character snapshot: {filename}")
            
            # Archive old snapshots if configured
            self.archiver.archive_old_snapshots(character_id, self.storage_dir)
            
            logger.info(f"Successfully scraped and stored character {character_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error scraping character {character_id}: {e}")
            return False
    
    
    async def monitor_loop(self):
        """Main monitoring loop."""
        check_interval = self.config.get('check_interval', 600)
        min_change_interval = timedelta(minutes=check_interval // 60)
        
        logger.info(f"Starting monitoring loop with {check_interval}s interval")
        
        await self.notification_manager.send_startup_notification()
        
        while self.running:
            try:
                logger.debug(f"Checking {len(self.character_ids)} characters for updates")
                
                # Scrape all characters
                scrape_tasks = [
                    self.scrape_character(char_id) for char_id in self.character_ids
                ]
                scrape_results = await asyncio.gather(*scrape_tasks, return_exceptions=True)
                
                successful_scrapes = sum(1 for result in scrape_results if result is True)
                logger.info(f"Scraped {successful_scrapes}/{len(self.character_ids)} characters successfully")
                
                # Check for changes and send notifications
                if len(self.character_ids) == 1:
                    await self.notification_manager.check_and_notify_character_changes(
                        self.character_ids[0],
                        min_change_interval
                    )
                else:
                    await self.notification_manager.check_and_notify_multiple_characters(
                        self.character_ids,
                        min_change_interval
                    )
                
                # Wait for next check with periodic shutdown checks
                sleep_time = 0
                shutdown_check_interval = self.config.get('shutdown_check_interval', 30)
                while sleep_time < check_interval and self.running:
                    await asyncio.sleep(min(shutdown_check_interval, check_interval - sleep_time))
                    sleep_time += shutdown_check_interval
                
                if not self.running:
                    logger.info("Monitor loop exiting due to shutdown signal")
                    break
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                error_retry_delay = self.config.get('error_retry_delay', 60)
                await asyncio.sleep(error_retry_delay)
    
    async def start(self):
        """Start the monitoring service."""
        if self.running:
            logger.warning("Monitor is already running")
            return
        
        await self.initialize(skip_webhook_test=True)  # Skip webhook test during normal monitoring
        
        self.running = True
        logger.info("Discord monitor started")
        
        try:
            await self.monitor_loop()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Monitor crashed: {e}")
        finally:
            logger.info("Executing shutdown sequence...")
            await self.stop()
    
    async def stop(self):
        """Stop the monitoring service."""
        if getattr(self, '_shutdown_sent', False):
            logger.info("Shutdown already sent, skipping")
            return
        
        logger.info("Stopping Discord monitor...")
        self.running = False
        
        # Send shutdown notification
        if self.notification_manager:
            try:
                logger.info("Sending shutdown notification...")
                await self.notification_manager.send_shutdown_notification()
                logger.info("Shutdown notification sent successfully")
            except Exception as e:
                logger.error(f"Failed to send shutdown notification: {e}")
        else:
            logger.warning("No notification manager available for shutdown notification")
        
        logger.info("Discord monitor stopped")
        self._shutdown_sent = True
    
    async def run_once(self, skip_scraping=False):
        """Run a single check for changes and send notifications if any."""
        await self.initialize(skip_webhook_test=True)  # Skip webhook test during normal runs
        
        if skip_scraping:
            logger.info("Checking existing snapshots for changes...")
        else:
            logger.info("Running one-shot character change check...")
            
            # Scrape all characters
            scrape_tasks = [
                self.scrape_character(char_id) for char_id in self.character_ids
            ]
            scrape_results = await asyncio.gather(*scrape_tasks, return_exceptions=True)
            
            # Log scrape results
            successful_scrapes = sum(1 for result in scrape_results if result is True)
            logger.info(f"Scraped {successful_scrapes}/{len(self.character_ids)} characters successfully")
            
            if successful_scrapes == 0:
                logger.error("No characters could be scraped successfully")
                return False
        
        # Check for changes and send notifications
        notifications_sent = 0
        min_change_interval = timedelta(minutes=0)  # No minimum interval for one-shot
        
        if len(self.character_ids) == 1:
            if skip_scraping:
                result = await self.notification_manager.check_and_notify_character_changes(
                    self.character_ids[0],
                    min_change_interval,
                    return_message_content=True
                )
                success, message_content = result
                if success:
                    notifications_sent += 1
                    if message_content:
                        try:
                            print("\n=== Discord Notification Content ===")
                            print(message_content)
                            print("=====================================\n")
                        except UnicodeEncodeError:
                            print("\n=== Discord Notification Content ===")
                            safe_content = message_content.replace('🎲', '[DICE]').replace('🔴', '[HIGH]').replace('🟡', '[MED]').replace('🟢', '[LOW]').replace('⬆️', '[UP]').replace('⬇️', '[DOWN]').replace('🔄', '[MOD]').replace('➕', '[ADD]').replace('➖', '[REM]')
                            print(safe_content)
                            print("=====================================\n")
            else:
                success = await self.notification_manager.check_and_notify_character_changes(
                    self.character_ids[0],
                    min_change_interval
                )
                if success:
                    notifications_sent += 1
        else:
            results = await self.notification_manager.check_and_notify_multiple_characters(
                self.character_ids,
                min_change_interval
            )
            notifications_sent = sum(1 for success in results.values() if success)
        
        if notifications_sent > 0:
            logger.info(f"Sent {notifications_sent} notification(s)")
            return True
        else:
            logger.info("No changes detected or notifications sent")
            return True

    async def test_notifications(self, detailed=False):
        """Test the notification system."""
        await self.initialize()
        
        if detailed:
            logger.info("Sending detailed test notification...")
            test_success = await self.notification_manager.send_detailed_test()
            
            if test_success:
                logger.info("Detailed test notification sent successfully!")
                return True
            else:
                logger.error("Detailed test notification failed!")
                return False
        else:
            logger.info("Testing Discord webhook connection...")
            test_success = await self.notification_manager.test_notification_system()
            
            if test_success:
                logger.info("Discord webhook test successful!")
                return True
            else:
                logger.error("Discord webhook test failed!")
                return False


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Discord Character Monitor')
    parser.add_argument(
        '--config',
        default='discord_config.yml',
        help='Path to configuration file (default: discord_config.yml)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test Discord webhook and exit'
    )
    parser.add_argument(
        '--test-detailed',
        action='store_true',
        help='Send detailed test notification with sample data'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--monitor',
        action='store_true',
        help='Run continuously as a monitor (overrides config setting)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (overrides config setting)'
    )
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Check existing snapshots without scraping'
    )
    parser.add_argument(
        '--party',
        action='store_true',
        help='Monitor all characters in party config instead of single character_id'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    formatter = SafeFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logging.basicConfig(
        level=log_level,
        handlers=[console_handler],
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    try:
        monitor = DiscordMonitor(args.config, use_party_mode=args.party)
        
        if args.test:
            # Test mode
            success = await monitor.test_notifications()
            sys.exit(0 if success else 1)
        
        if args.test_detailed:
            # Detailed test mode
            success = await monitor.test_notifications(detailed=True)
            sys.exit(0 if success else 1)
        
        if args.check_only:
            success = await monitor.run_once(skip_scraping=True)
            sys.exit(0 if success else 1)
        
        # Determine run mode: CLI args override config setting
        run_continuous = False
        if args.monitor:
            run_continuous = True
        elif args.once:
            run_continuous = False
        else:
            run_continuous = monitor.config.get('run_continuous', False)
        
        if run_continuous:
            logger.info("Starting continuous monitoring mode")
            
            def signal_handler():
                logger.info("Received shutdown signal")
                if hasattr(monitor, 'running'):
                    monitor.running = False
            
            # Set up signal handlers
            loop = asyncio.get_event_loop()
            for sig in [signal.SIGINT, signal.SIGTERM]:
                try:
                    loop.add_signal_handler(sig, signal_handler)
                except NotImplementedError:
                    signal.signal(sig, lambda s, f: signal_handler())
            
            await monitor.start()
        else:
            logger.info("Running in one-shot mode")
            success = await monitor.run_once()
            sys.exit(0 if success else 1)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())