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
import os
from pathlib import Path
from typing import List, Optional, Set, Tuple, Dict, Any
from datetime import datetime, timedelta
import yaml
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
from shared.models.change_detection import ChangePriority
from services.webhook_manager import WebhookManager
from services.configuration_validator import ConfigurationValidator, SecurityLevel
from services.discord_logger import DiscordLogger, OperationType, LogLevel, log_configuration_event

from scraper.enhanced_dnd_scraper import EnhancedDnDScraper
from shared.config.manager import get_config_manager
from discord.core.storage.archiving import SnapshotArchiver

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
    
    def __init__(self, config_path: str, use_party_mode: bool = False, character_id_override: str = None):
        self.config_path = Path(config_path)
        self.config = None
        self.notification_manager = None
        self.storage = None
        self.scraper = None
        self.running = False
        self.character_ids = []
        self.archiver = None
        self.use_party_mode = use_party_mode
        self.character_id_override = character_id_override
        
        # Initialize enhanced logging
        self.discord_logger = DiscordLogger('discord.monitor')
        
        # Load configuration
        self._load_config()
        
        logger.info(f"Discord monitor initialized with config: {config_path}")
    
    def _load_config(self):
        """Load configuration from YAML file with environment variable support."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            raw_config = yaml.safe_load(f)
        
        # Process environment variables and apply security enhancements
        self.config = self._process_config_with_env_vars(raw_config)
        
        # Validate required fields after environment variable processing
        required_fields = ['webhook_url']
        for field in required_fields:
            if field not in self.config or not self.config[field]:
                raise ValueError(f"Required configuration field missing or empty: {field}")
        
        logger.info("Configuration loaded successfully")
        
        # Log configuration loading event
        self.discord_logger.log_configuration_event(
            "config_loaded",
            f"Configuration loaded from {self.config_path}",
            config_details={
                'config_file': str(self.config_path),
                'has_webhook_url': bool(self.config.get('webhook_url')),
                'character_count': len(self.character_ids) if hasattr(self, 'character_ids') else 0
            }
        )
    
    def _process_config_with_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process configuration with environment variable substitution and security enhancements.
        
        Args:
            config: Raw configuration dictionary
            
        Returns:
            Processed configuration with environment variables resolved
        """
        processed_config = config.copy()
        
        # Track which values came from environment variables
        env_sourced_keys = set()
        
        # Environment variable mappings (prioritized over config file)
        env_mappings = {
            'webhook_url': ['DISCORD_WEBHOOK_URL', 'WEBHOOK_URL'],
            'session_cookie': ['DND_SESSION_COOKIE', 'SESSION_COOKIE'],
            'log_level': ['LOG_LEVEL']
        }
        
        # Apply environment variables with priority
        for config_key, env_vars in env_mappings.items():
            for env_var in env_vars:
                env_value = os.getenv(env_var)
                if env_value:
                    processed_config[config_key] = env_value
                    env_sourced_keys.add(config_key)
                    logger.info(f"Using environment variable {env_var} for {config_key}")
                    break
        
        # Process string interpolation for remaining values
        processed_config = self._interpolate_env_vars(processed_config)
        
        # Security warnings for hardcoded sensitive values
        self._check_config_security_warnings(processed_config, env_sourced_keys)
        
        return processed_config
    
    def _interpolate_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpolate environment variables in configuration values.
        Supports ${VAR_NAME} and %VAR_NAME% formats.
        """
        import re
        
        def replace_env_vars(value):
            if not isinstance(value, str):
                return value
            
            # Handle ${VAR_NAME} format
            def replace_bash_style(match):
                var_name = match.group(1)
                return os.getenv(var_name, match.group(0))  # Keep original if not found
            
            # Handle %VAR_NAME% format  
            def replace_windows_style(match):
                var_name = match.group(1)
                return os.getenv(var_name, match.group(0))  # Keep original if not found
            
            value = re.sub(r'\$\{([^}]+)\}', replace_bash_style, value)
            value = re.sub(r'%([^%]+)%', replace_windows_style, value)
            
            return value
        
        def process_dict(d):
            if isinstance(d, dict):
                return {k: process_dict(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [process_dict(item) for item in d]
            else:
                return replace_env_vars(d)
        
        return process_dict(config)
    
    def _check_config_security_warnings(self, config: Dict[str, Any], env_sourced_keys: set = None):
        """Check for security issues in configuration and log warnings."""
        if env_sourced_keys is None:
            env_sourced_keys = set()
            
        webhook_url = config.get('webhook_url', '')
        session_cookie = config.get('session_cookie', '')
        
        # Check for hardcoded webhook URLs (but skip if it came from environment variables)
        if webhook_url and isinstance(webhook_url, str):
            if webhook_url.startswith('https://discord') and 'webhooks' in webhook_url:
                # Only warn if this URL was NOT loaded from an environment variable
                if 'webhook_url' not in env_sourced_keys:
                    logger.warning("⚠️  SECURITY WARNING: Hardcoded webhook URL detected in configuration!")
                    logger.warning("   Recommendation: Use environment variable DISCORD_WEBHOOK_URL instead")
                    logger.warning("   Example: export DISCORD_WEBHOOK_URL='your-webhook-url'")
                    
                    # Enhanced logging for security events
                    self.discord_logger.log_configuration_event(
                        "security_warning",
                        "Hardcoded webhook URL detected in configuration",
                        security_level="HIGH"
                    )
                else:
                    # URL came from environment variable - this is good practice
                    logger.debug("✅ Webhook URL loaded from environment variable (secure)")
        
        # Check for hardcoded session cookies (but skip if it came from environment variables)
        if session_cookie and isinstance(session_cookie, str):
            if len(session_cookie) > 20 and not session_cookie.startswith('${') and not session_cookie.startswith('%'):
                # Only warn if this cookie was NOT loaded from an environment variable
                if 'session_cookie' not in env_sourced_keys:
                    logger.warning("⚠️  SECURITY WARNING: Hardcoded session cookie detected in configuration!")
                    logger.warning("   Recommendation: Use environment variable DND_SESSION_COOKIE instead")
                    logger.warning("   Example: export DND_SESSION_COOKIE='your-session-cookie'")
                    
                    # Enhanced logging for security events
                    self.discord_logger.log_configuration_event(
                        "security_warning",
                        "Hardcoded session cookie detected in configuration",
                        security_level="HIGH"
                    )
                else:
                    # Cookie came from environment variable - this is good practice
                    logger.debug("✅ Session cookie loaded from environment variable (secure)")
    
    async def initialize(self, skip_webhook_test=False):
        """Initialize all services and connections."""
        # Set up logging level
        log_level = self.config.get('log_level', 'INFO')
        logging.getLogger().setLevel(getattr(logging, log_level.upper()))
        
        # Configure storage directory - use character_data/discord for new architecture
        configured_storage_dir = self.config.get('storage_directory', self.config.get('storage_dir', '../character_data'))
        if Path(configured_storage_dir).is_absolute():
            # Absolute path - use discord subdirectory within it
            base_storage_dir = Path(configured_storage_dir)
            self.storage_dir = base_storage_dir / "discord"
        else:
            # Relative path - use character_data/discord from project root
            base_storage_dir = project_root / configured_storage_dir.lstrip('../')
            self.storage_dir = base_storage_dir / "discord"
        
        self.storage_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"Using Discord storage directory: {self.storage_dir}")
        self.storage = None
        
        # Initialize scraper configuration
        self.session_cookie = self.config.get('session_cookie')
        self.config_manager = get_config_manager()
        
        # Prepare character IDs based on mode and overrides
        if self.character_id_override:
            # Command line override takes precedence
            self.character_ids = [int(self.character_id_override)]
            logger.info(f"Using character ID override from command line: {self.character_ids[0]}")
        elif self.use_party_mode:
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
        
        # Quick startup validation
        self._validate_startup_config()
        
        logger.info("All services initialized successfully")
    
    def _create_notification_config(self) -> NotificationConfig:
        """Create notification configuration from loaded config."""
        # Parse format type
        
        
        # Parse minimum priority from YAML configuration
        min_priority_name = self.config.get('discord', {}).get('min_priority', 'MEDIUM')
        
        try:
            min_priority = ChangePriority[min_priority_name.upper()]
            logger.info(f"Using minimum priority for Discord: {min_priority_name.upper()}")
        except KeyError:
            logger.warning(f"Invalid priority '{min_priority_name}', using MEDIUM")
            min_priority = ChangePriority.MEDIUM
        
        # Parse filtering configuration - support both new and legacy formats
        include_groups = None
        exclude_groups = None
        
        # Check for new format: change_types at top level (config/discord.yaml format)
        if 'change_types' in self.config:
            change_types = self.config['change_types']
            if isinstance(change_types, list):
                include_groups = self._convert_change_types_to_groups(change_types)
                logger.info(f"Using change types filter: {sorted(change_types)}")
            else:
                logger.warning("change_types must be a list, ignoring")
        
        # Check for legacy format: filtering section (discord_config.yml format)
        elif 'filtering' in self.config:
            filtering = self.config.get('filtering', {})
            
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
        
        # Default to all change types if no filtering specified
        if include_groups is None and exclude_groups is None:
            logger.info("No filtering configured - all change types will be included")
        
        # Parse Discord settings
        discord_config = self.config.get('discord', {})
        rate_limit = discord_config.get('rate_limit', {})
        
        return NotificationConfig(
            webhook_url=self.config['webhook_url'],
            username=discord_config.get('username', 'D&D Beyond Monitor'),
            avatar_url=discord_config.get('avatar_url'),
            max_changes_per_notification=discord_config.get('maximum_changes_per_notification', discord_config.get('max_changes_per_notification', 20)),
            min_priority=min_priority,
            include_groups=include_groups,
            exclude_groups=exclude_groups,
            rate_limit_requests_per_minute=rate_limit.get('requests_per_minute', 3),
            rate_limit_burst=rate_limit.get('maximum_burst_requests', rate_limit.get('burst_limit', 1)),
            timezone=discord_config.get('timezone', 'UTC'),
            send_summary_for_multiple=len(self.character_ids) > 1,
            delay_between_messages=discord_config.get('delay_between_messages', 2.0)
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
            'max_hp': ['combat'],  # Maximum hit points
            'armor_class': ['combat'],
            'ability_scores': ['abilities'],
            'spells_known': ['spells'],
            'spells': ['spells'],  # General spells category
            'spell_slots': ['spells'],
            'spellcasting_stats': ['spells'],  # Spell attack bonuses, spell save DC
            'inventory_items': ['inventory'],
            'inventory': ['inventory'],  # General inventory category
            'equipment': ['inventory'],
            'currency': ['inventory'],
            'skills': ['skills'],
            'passive_skills': ['skills'],  # Passive perception, investigation, etc.
            'proficiencies': ['skills'],
            'feats': ['skills'],
            'class_features': ['basic'],
            'subclass': ['basic'],  # Subclass selection/changes
            'multiclass': ['basic'],  # Multiclassing changes
            'race_species': ['basic'],  # Race/species changes
            'initiative': ['combat'],  # Initiative modifier
            'movement_speed': ['basic'],  # Speed changes
            'size': ['basic'],  # Character size
            'alignment': ['appearance'],  # Character alignment
            'personality': ['appearance'],  # Personality traits
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
            
            # Create scraper for this character with discord_output enabled
            scraper = EnhancedDnDScraper(
                character_id=str(character_id), 
                session_cookie=self.session_cookie,
                discord_output=True  # Always save to discord directory
            )
            
            # Check rate limiting before API call
            scraper._check_rate_limit()
            
            # Fetch character data
            if not scraper.fetch_character_data():
                logger.warning(f"Failed to fetch data for character {character_id}")
                return False
            
            # Save character data - this will automatically save to discord directory
            output_path = scraper.save_character_data()
            logger.info(f"Character data saved via scraper to: {output_path}")
            
            # Archive old snapshots and clean up scraper files per retention config
            self.archiver.archive_old_snapshots(character_id, self.storage_dir)
            self.archiver.cleanup_scraper_files(character_id, project_root)
            
            logger.info(f"Successfully scraped and stored character {character_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error scraping character {character_id}: {e}")
            return False
    
    
    async def monitor_loop(self):
        """Main monitoring loop."""
        check_interval = self.config.get('check_interval_seconds', self.config.get('check_interval', 600))
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
    
    async def validate_webhook(self):
        """Validate webhook configuration and connectivity."""
        logger.info("Validating Discord webhook...")
        
        webhook_url = self.config.get('webhook_url')
        if not webhook_url:
            logger.error("No webhook URL configured")
            return False
        
        async with WebhookManager() as manager:
            result = await manager.test_webhook_connectivity(webhook_url, send_test_message=False)
            
            if result.is_valid:
                logger.info("✅ Webhook validation successful!")
                if result.webhook_info:
                    logger.info(f"Webhook Name: {result.webhook_info.name}")
                    logger.info(f"Channel ID: {result.webhook_info.channel_id}")
                    logger.info(f"Guild ID: {result.webhook_info.guild_id}")
                return True
            else:
                logger.error(f"❌ Webhook validation failed: {result.error_message}")
                logger.error(f"Error Type: {result.error_type.value if result.error_type else 'unknown'}")
                
                if result.troubleshooting_steps:
                    logger.info("Troubleshooting steps:")
                    for step in result.troubleshooting_steps:
                        logger.info(f"  - {step}")
                
                return False
    
    def validate_config(self):
        """Validate configuration file for errors and security issues."""
        logger.info("Validating configuration...")
        
        validator = ConfigurationValidator()
        result = validator.validate_discord_config(self.config, str(self.config_path))
        
        # Report results
        if result.is_valid:
            logger.info("✅ Configuration validation successful!")
        else:
            logger.error("❌ Configuration validation failed!")
        
        # Show errors
        if result.errors:
            logger.error("Configuration errors:")
            for error in result.errors:
                logger.error(f"  - {error}")
        
        # Show warnings
        if result.warnings:
            logger.warning("Configuration warnings:")
            for warning in result.warnings:
                logger.warning(f"  - {warning}")
        
        # Show security warnings
        if result.security_warnings:
            logger.warning("Security warnings:")
            for warning in result.security_warnings:
                severity_icon = "🔴" if warning.severity.value == "HIGH" else "🟡" if warning.severity.value == "MEDIUM" else "🔵"
                logger.warning(f"  {severity_icon} [{warning.severity.value}] {warning.message}")
                logger.warning(f"    Recommendation: {warning.recommendation}")
                if warning.file_path:
                    logger.warning(f"    File: {warning.file_path}")
        
        # Show suggestions
        if result.suggestions:
            logger.info("Suggestions for improvement:")
            for suggestion in result.suggestions:
                logger.info(f"  - {suggestion}")
        
        return result.is_valid
    
    def security_check(self):
        """Perform comprehensive security audit."""
        logger.info("Performing security audit...")
        
        validator = ConfigurationValidator()
        
        # Check configuration
        config_result = validator.validate_discord_config(self.config, str(self.config_path))
        
        # Scan project files for webhooks
        project_root = Path(__file__).parent.parent
        file_warnings = validator.scan_files_for_webhooks(str(project_root))
        
        all_warnings = config_result.security_warnings + file_warnings
        
        if not all_warnings:
            logger.info("✅ No security issues found!")
            return True
        
        logger.warning(f"Found {len(all_warnings)} security issue(s):")
        
        high_count = sum(1 for w in all_warnings if w.severity == SecurityLevel.HIGH)
        medium_count = sum(1 for w in all_warnings if w.severity == SecurityLevel.MEDIUM)
        low_count = sum(1 for w in all_warnings if w.severity == SecurityLevel.LOW)
        
        logger.warning(f"  🔴 High: {high_count}")
        logger.warning(f"  🟡 Medium: {medium_count}")
        logger.warning(f"  🔵 Low: {low_count}")
        
        for warning in all_warnings:
            severity_icon = "🔴" if warning.severity.value == "HIGH" else "🟡" if warning.severity.value == "MEDIUM" else "🔵"
            logger.warning(f"{severity_icon} [{warning.severity.value}] {warning.message}")
            logger.warning(f"  Recommendation: {warning.recommendation}")
            if warning.file_path:
                location = f"{warning.file_path}"
                if warning.line_number:
                    location += f":{warning.line_number}"
                logger.warning(f"  Location: {location}")
        
        # Environment variable suggestions
        env_suggestions = validator.suggest_environment_variables(self.config)
        if env_suggestions:
            logger.info("Recommended environment variables:")
            for suggestion in env_suggestions:
                logger.info(f"  - {suggestion}")
        
        return high_count == 0  # Return success if no high-severity issues
    
    async def run_diagnostic(self):
        """Run comprehensive diagnostic tests."""
        logger.info("Running comprehensive diagnostic tests...")
        
        results = {
            'config_validation': False,
            'security_check': False,
            'webhook_validation': False,
            'webhook_test': False,
            'character_access': False
        }
        
        # 1. Configuration validation
        logger.info("1. Validating configuration...")
        results['config_validation'] = self.validate_config()
        
        # 2. Security check
        logger.info("2. Performing security audit...")
        results['security_check'] = self.security_check()
        
        # 3. Webhook validation
        logger.info("3. Validating webhook...")
        results['webhook_validation'] = await self.validate_webhook()
        
        # 4. Webhook test message
        if results['webhook_validation']:
            logger.info("4. Testing webhook with message...")
            webhook_url = self.config.get('webhook_url')
            async with WebhookManager() as manager:
                test_result = await manager.test_webhook_connectivity(webhook_url, send_test_message=True)
                results['webhook_test'] = test_result.is_valid
                if not test_result.is_valid:
                    logger.error(f"Webhook test failed: {test_result.error_message}")
        else:
            logger.warning("4. Skipping webhook test due to validation failure")
        
        # 5. Character access test
        logger.info("5. Testing character data access...")
        try:
            # Test scraping one character
            if self.character_ids:
                test_char_id = self.character_ids[0]
                scrape_success = await self.scrape_character(test_char_id)
                results['character_access'] = scrape_success
                if scrape_success:
                    logger.info(f"✅ Successfully accessed character {test_char_id}")
                else:
                    logger.error(f"❌ Failed to access character {test_char_id}")
            else:
                logger.warning("No character IDs configured for testing")
        except Exception as e:
            logger.error(f"Character access test failed: {e}")
        
        # Summary
        logger.info("Diagnostic Results Summary:")
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {test_name.replace('_', ' ').title()}: {status}")
        
        logger.info(f"Overall: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All diagnostic tests passed! System is ready for monitoring.")
        else:
            logger.warning("⚠️ Some diagnostic tests failed. Please address the issues above.")
        
        return passed == total
    
    def show_logging_stats(self):
        """Display comprehensive logging and error statistics."""
        logger.info("Discord Logging Statistics")
        logger.info("=" * 50)
        
        # Get statistics from Discord logger
        stats = self.discord_logger.get_operation_stats()
        
        # Operation statistics
        if stats['operation_counts']:
            logger.info("Operation Statistics:")
            for operation, counts in stats['operation_counts'].items():
                total = counts['total']
                errors = counts['errors']
                success_rate = ((total - errors) / total * 100) if total > 0 else 0
                logger.info(f"  {operation}: {total} total, {errors} errors ({success_rate:.1f}% success)")
        else:
            logger.info("No operations logged yet")
        
        # Error statistics
        if stats['error_counts']:
            logger.info("\nError Type Statistics:")
            for error_type, count in stats['error_counts'].items():
                logger.info(f"  {error_type}: {count} occurrences")
        else:
            logger.info("\nNo errors logged")
        
        # Rate limiting statistics
        rate_limit_count = stats['recent_rate_limits']
        if rate_limit_count > 0:
            logger.info(f"\nRate Limiting: {rate_limit_count} events in last 24 hours")
            if stats['rate_limit_events']:
                logger.info("Recent rate limit events:")
                for event in stats['rate_limit_events'][-5:]:  # Show last 5
                    timestamp = event['timestamp']
                    retry_after = event['retry_after']
                    operation = event['operation']
                    logger.info(f"  {timestamp}: {operation} rate limited for {retry_after}s")
        else:
            logger.info("\nNo recent rate limiting")
        
        # Configuration events
        logger.info(f"\nConfiguration Events: Check logs for security warnings and config loading events")
        
        logger.info("\n" + "=" * 50)
    
    def _validate_startup_config(self):
        """Quick validation of critical configuration on startup."""
        issues = []
        
        # Check webhook URL
        webhook_url = self.config.get('webhook_url')
        if not webhook_url:
            issues.append("Missing webhook_url in configuration")
        elif webhook_url.startswith('${') and webhook_url.endswith('}'):
            env_var = webhook_url[2:-1]
            if not os.getenv(env_var):
                issues.append(f"Environment variable {env_var} is not set")
        
        # Check character IDs
        if not self.character_ids:
            issues.append("No character IDs configured")
        
        # Check change types - check both top level and filtering section
        change_types = self.config.get('change_types', [])
        if not change_types and 'filtering' in self.config:
            filtering = self.config.get('filtering', {})
            change_types = filtering.get('change_types', [])
        
        if not change_types:
            logger.warning("No change types configured - all changes will be ignored")
        
        # Report issues
        if issues:
            logger.error("Configuration validation failed:")
            for issue in issues:
                logger.error(f"  - {issue}")
            raise ValueError(f"Configuration validation failed: {'; '.join(issues)}")
        
        logger.debug("Startup configuration validation passed")
    



async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Discord Character Monitor')
    parser.add_argument(
        '--config',
        default='config/discord.yaml',
        help='Path to configuration file (default: config/discord.yaml)'
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
    parser.add_argument(
        '--character-id',
        help='Override character ID from config (for single character monitoring)'
    )
    parser.add_argument(
        '--validate-webhook',
        action='store_true',
        help='Validate webhook configuration and connectivity'
    )
    parser.add_argument(
        '--validate-config',
        action='store_true',
        help='Validate configuration file for errors and security issues'
    )
    parser.add_argument(
        '--security-check',
        action='store_true',
        help='Perform security audit of configuration and files'
    )
    parser.add_argument(
        '--diagnostic',
        action='store_true',
        help='Run comprehensive diagnostic tests'
    )
    parser.add_argument(
        '--logging-stats',
        action='store_true',
        help='Show logging and error statistics'
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
        monitor = DiscordMonitor(args.config, use_party_mode=args.party, character_id_override=getattr(args, 'character_id', None))
        
        if args.test:
            # Test mode
            success = await monitor.test_notifications()
            sys.exit(0 if success else 1)
        
        if args.test_detailed:
            # Detailed test mode
            success = await monitor.test_notifications(detailed=True)
            sys.exit(0 if success else 1)
        
        if args.validate_webhook:
            # Webhook validation mode
            success = await monitor.validate_webhook()
            sys.exit(0 if success else 1)
        
        if args.validate_config:
            # Configuration validation mode
            success = monitor.validate_config()
            sys.exit(0 if success else 1)
        
        if args.security_check:
            # Security audit mode
            success = monitor.security_check()
            sys.exit(0 if success else 1)
        
        if args.diagnostic:
            # Comprehensive diagnostic mode
            success = await monitor.run_diagnostic()
            sys.exit(0 if success else 1)
        
        if args.logging_stats:
            # Show logging statistics
            monitor.show_logging_stats()
            sys.exit(0)
        

        
        if args.check_only:
            success = await monitor.run_once(skip_scraping=True)
            
            # Wait for any pending background tasks (like change logging) to complete
            loop = asyncio.get_running_loop()
            if hasattr(loop, '_change_log_tasks') and loop._change_log_tasks:
                logger.info(f"Waiting for {len(loop._change_log_tasks)} background change logging tasks to complete...")
                await asyncio.gather(*loop._change_log_tasks, return_exceptions=True)
                logger.info("All background tasks completed")
            
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