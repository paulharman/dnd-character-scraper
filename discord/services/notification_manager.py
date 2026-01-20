#!/usr/bin/env python3
"""
Notification manager for coordinating character change notifications.

Orchestrates change detection, filtering, formatting, and delivery
of Discord notifications for character updates.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Set, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, replace
from pathlib import Path
from copy import deepcopy

from .discord_service import DiscordService, EmbedColor
from .party_inventory_tracker import PartyInventoryTracker
from discord.core.services.change_detection_service import EnhancedChangeDetectionService as ChangeDetectionService
from shared.models.change_detection import ChangePriority, ChangeDetectionResult
from discord.services.change_detection.models import CharacterChangeSet, CharacterSnapshot

# Handle both relative and absolute imports
try:
    from ..formatters.discord_formatter import DiscordFormatter
except (ImportError, ValueError):
    # Fallback for when running as main module or beyond top-level package
    import sys
    import os
    discord_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if discord_dir not in sys.path:
        sys.path.insert(0, discord_dir)
    from formatters.discord_formatter import DiscordFormatter

logger = logging.getLogger(__name__)


@dataclass
class NotificationConfig:
    """Configuration for Discord notifications."""
    webhook_url: str
    username: str = "D&D Beyond Monitor"
    avatar_url: Optional[str] = None
    max_changes_per_notification: int = 20
    min_priority: ChangePriority = ChangePriority.LOW
    include_groups: Optional[Set[str]] = None
    exclude_groups: Optional[Set[str]] = None
    rate_limit_requests_per_minute: int = 3
    rate_limit_burst: int = 1
    timezone: str = "UTC"
    
    # Grouping settings
    send_summary_for_multiple: bool = True
    delay_between_messages: float = 2.0


class NotificationManager:
    """
    Main notification manager for character change notifications.
    
    Features:
    - Multi-character monitoring
    - Change detection and filtering
    - Discord notification formatting and delivery
    - Rate limiting and error handling
    - Configurable filtering and grouping
    """
    
    def __init__(
        self,
        storage: Any,
        config: NotificationConfig,
        storage_dir: Optional[str] = None
    ):
        self.storage = storage
        self.config = config
        # Use provided storage directory or default to character_data directory
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            # Default to character_data/discord directory (where character files are stored)
            self.storage_dir = Path("../character_data/discord")
        
        # Initialize services - using enhanced change detection as primary service
        enhanced_config = self._create_enhanced_change_detection_config()
        self.change_detector = ChangeDetectionService(config=enhanced_config)

        # Initialize party inventory tracker
        self.party_tracker = PartyInventoryTracker(str(self.storage_dir))

        # Load Discord configuration for formatter
        discord_config = self._load_discord_config()
        self.formatter = DiscordFormatter(config=discord_config)

        # Track last notification times to avoid spam
        self.last_notification_times: Dict[int, datetime] = {}
        
        logger.info("Notification manager initialized")
    
    def _load_discord_config(self) -> Dict[str, Any]:
        """Load Discord configuration for formatter."""
        import yaml
        from pathlib import Path
        
        config_path = Path("config/discord.yaml")
        if not config_path.exists():
            logger.warning("discord.yaml not found, using default configuration")
            return {}
        
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading Discord configuration: {e}")
            return {}
    
    def _create_enhanced_change_detection_config(self):
        """Create enhanced change detection configuration from discord config."""
        from discord.core.models.change_detection_models import ChangeDetectionConfig
        
        # Load the discord configuration to get enabled change types
        import yaml
        from pathlib import Path
        
        # Try to load discord.yaml configuration
        config_path = Path("config/discord.yaml")
        if not config_path.exists():
            # Fallback to default configuration
            logger.warning("discord.yaml not found, using default enhanced change detection config")
            return ChangeDetectionConfig()
        
        try:
            with open(config_path, 'r') as f:
                discord_config = yaml.safe_load(f)
            
            # Extract enabled change types from configuration
            enabled_change_types = set()
            
            # Check filtering.change_types (legacy format)
            if 'filtering' in discord_config and 'change_types' in discord_config['filtering']:
                change_types = discord_config['filtering']['change_types']
                if isinstance(change_types, list):
                    enabled_change_types.update(change_types)
            
            # Check enhanced_change_tracking.change_type_config (new format)
            if 'enhanced_change_tracking' in discord_config:
                enhanced_config = discord_config['enhanced_change_tracking']
                if 'change_type_config' in enhanced_config:
                    for change_type, type_config in enhanced_config['change_type_config'].items():
                        if isinstance(type_config, dict) and type_config.get('enabled', True):
                            enabled_change_types.add(change_type)
            
            # If no specific configuration found, use all available types
            if not enabled_change_types:
                logger.info("No change types configured, enabling all enhanced change types")
                enabled_change_types = {
                    'level', 'feats', 'subclass', 'spells', 'inventory', 'background',
                    'max_hp', 'proficiencies', 'ability_scores', 'race_species',
                    'multiclass', 'personality', 'spellcasting_stats', 'initiative',
                    'passive_skills', 'alignment', 'size', 'movement_speed'
                }
            
            # Load field patterns and priority overrides
            field_patterns = discord_config.get('detection', {}).get('field_patterns', {})
            priority_overrides = {}
            
            # Convert field patterns to priority overrides
            for field_path, priority_str in field_patterns.items():
                if priority_str != 'IGNORED':
                    try:
                        from shared.models.change_detection import ChangePriority
                        priority_overrides[field_path] = ChangePriority[priority_str]
                    except KeyError:
                        logger.warning(f"Invalid priority '{priority_str}' for field '{field_path}'")
            
            # Create configuration with loaded settings
            config = ChangeDetectionConfig(
                enabled_change_types=enabled_change_types,
                enable_change_logging=discord_config.get('changelog', {}).get('enabled', True),
                enable_causation_analysis=discord_config.get('causation', {}).get('enabled', True),
                priority_overrides=priority_overrides
            )
            
            logger.info(f"Enhanced change detection configured with {len(enabled_change_types)} change types: {sorted(enabled_change_types)}")
            logger.info(f"Loaded {len(priority_overrides)} field pattern priority overrides")
            
            # Log configuration summary
            changelog_enabled = discord_config.get('changelog', {}).get('enabled', True)
            causation_enabled = discord_config.get('causation', {}).get('enabled', True)
            logger.info(f"Change logging: {'ENABLED' if changelog_enabled else 'DISABLED'}")
            logger.info(f"Causation analysis: {'ENABLED' if causation_enabled else 'DISABLED'}")
            
            return config
            
        except Exception as e:
            logger.error(f"Error loading enhanced change detection config: {e}")
            # Return default configuration on error
            return ChangeDetectionConfig()
    
    async def check_and_notify_character_changes(
        self,
        character_id: int,
        min_change_interval: timedelta = timedelta(minutes=5),
        return_message_content: bool = False
    ) -> Union[bool, Tuple[bool, Optional[str]]]:
        """
        Check for changes to a single character and send notifications if needed.
        Uses enhanced change detection with causation analysis and change logging.
        
        Args:
            character_id: ID of character to check
            min_change_interval: Minimum time between notifications for same character
            return_message_content: Whether to return message content
            
        Returns:
            True if notifications were sent, False otherwise
        """
        try:
            # Check if we've notified about this character recently
            last_notification = self.last_notification_times.get(character_id)
            if (last_notification and 
                datetime.now() - last_notification < min_change_interval):
                logger.debug(f"Skipping character {character_id} - too soon since last notification")
                return False
            
            # Find the most recent snapshot files
            storage_dir = self.storage_dir
            pattern = f"character_{character_id}_*.json"
            
            # Find all snapshot files for this character
            snapshot_files = sorted(storage_dir.glob(pattern), key=lambda p: p.stat().st_mtime)
            
            if len(snapshot_files) == 0:
                logger.info(f"Character {character_id} has no snapshots - this shouldn't happen after scraper runs")
                if return_message_content:
                    return False, ""
                return False
            elif len(snapshot_files) == 1:
                logger.info(f"Character {character_id} has 1 snapshot - sending welcome notification for new character")
                # Send a "character discovered" notification for first snapshot
                await self._send_character_discovered_notification(character_id)
                if return_message_content:
                    return True, "New character discovered notification sent"
                return True
            
            # We have 2+ snapshots, proceed with enhanced change detection
            
            # Load the two most recent snapshots
            try:
                import json
                with open(snapshot_files[-2], 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
                with open(snapshot_files[-1], 'r', encoding='utf-8') as f:
                    new_data = json.load(f)
                
                logger.info(f"Comparing snapshots for character {character_id}")
                logger.debug(f"Old snapshot: {snapshot_files[-2]}")
                logger.debug(f"New snapshot: {snapshot_files[-1]}")
                
            except Exception as e:
                logger.error(f"Failed to load snapshots for character {character_id}: {e}")
                if return_message_content:
                    return False, ""
                return False
            
            # Use consolidated enhanced change detection system
            try:
                # Create snapshot objects for the enhanced service
                class SimpleSnapshot:
                    def __init__(self, data, file_path, version):
                        self.character_data = data
                        self.character_id = character_id
                        self.timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
                        self.version = version
                
                import re
                from pathlib import Path
                
                def extract_timestamp_version(filepath):
                    filename = Path(filepath).stem
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})', filename)
                    if timestamp_match:
                        return timestamp_match.group(1)
                    return filename
                
                old_version = extract_timestamp_version(snapshot_files[-2])
                new_version = extract_timestamp_version(snapshot_files[-1])
                
                old_snapshot = SimpleSnapshot(old_data, snapshot_files[-2], old_version)
                new_snapshot = SimpleSnapshot(new_data, snapshot_files[-1], new_version)
                
                # Use enhanced change detection service (now the primary service)
                change_set = self.change_detector.detect_changes_as_changeset(old_snapshot, new_snapshot)
                
                if not change_set.changes:
                    logger.info(f"No changes detected for character {character_id}")
                    if return_message_content:
                        return False, ""
                    return False
                
                logger.info(f"Enhanced change detection found {len(change_set.changes)} changes for character {character_id}")
                
                # Apply filtering using the enhanced service's filtering method
                filtered_changes = self.change_detector.filter_changes_by_groups(
                    change_set.changes,
                    include_groups=self.config.include_groups,
                    exclude_groups=self.config.exclude_groups
                )
                
                if not filtered_changes:
                    logger.info(f"All changes for character {character_id} were filtered out")
                    if return_message_content:
                        return False, ""
                    return False
                
                # Update change set with filtered changes
                change_set.changes = filtered_changes
                
            except Exception as e:
                logger.error(f"Enhanced change detection failed: {e}", exc_info=True)
                if return_message_content:
                    return False, ""
                return False
            
            # Check minimum priority (handle both enhanced and basic changes)
            qualifying_changes = []
            for change in filtered_changes:
                try:
                    # Handle enhanced changes with priority enum
                    if hasattr(change, 'priority') and hasattr(change.priority, 'value'):
                        priority_value = change.priority.value
                    # Handle basic changes with string priority
                    elif hasattr(change, 'priority') and isinstance(change.priority, str):
                        priority_map = {'low': 1, 'medium': 2, 'high': 3}
                        priority_value = priority_map.get(change.priority.lower(), 2)
                    else:
                        priority_value = 2  # Default to medium
                    
                    # Compare with minimum priority
                    min_priority_value = getattr(self.config.min_priority, 'value', 1)
                    if priority_value >= min_priority_value:
                        qualifying_changes.append(change)
                except Exception as e:
                    logger.debug(f"Priority check failed for change, including anyway: {e}")
                    qualifying_changes.append(change)
            
            if not qualifying_changes:
                logger.info(f"Detected 0 changes for character {character_id}")
                min_priority_name = getattr(self.config.min_priority, 'name', 'medium')
                logger.info(f"No changes meet minimum priority {min_priority_name}")
                
                # Safe priority logging
                priority_info = []
                for change in filtered_changes:
                    try:
                        # Handle both object and dictionary field paths
                        if isinstance(change, dict):
                            field = change.get('field_path', change.get('field', 'unknown'))
                            priority = change.get('priority', 'unknown')
                        else:
                            field = getattr(change, 'field_path', getattr(change, 'field', 'unknown'))
                            priority = getattr(change, 'priority', 'unknown')
                        
                        # Convert priority enum to name if needed
                        if hasattr(priority, 'name'):
                            priority = priority.name
                        elif isinstance(priority, int):
                            # Convert integer priority to name for logging
                            priority_names = {1: 'LOW', 2: 'MEDIUM', 3: 'HIGH', 4: 'CRITICAL'}
                            priority = priority_names.get(priority, f'UNKNOWN({priority})')
                        
                        priority_info.append(f'{field}:{priority}')
                    except:
                        priority_info.append('unknown:unknown')
                
                logger.info(f"Change priorities: {priority_info}")
                if return_message_content:
                    return False, ""
                return False
            
            # Log final count after all filtering is complete
            logger.info(f"Detected {len(qualifying_changes)} changes for character {character_id}")
            min_priority_name = getattr(self.config.min_priority, 'name', 'medium')
            logger.info(f"Sending notification for {len(qualifying_changes)} qualifying changes (min priority: {min_priority_name})")
            
            # Output change summaries for parser integration
            print(f"PARSER_CHANGES:{len(qualifying_changes)}")
            print("PARSER_NOTIFICATION:true")
            for change in qualifying_changes:  # Show all changes
                # Get change description and make it Windows-compatible
                try:
                    desc = str(getattr(change, 'description', 'Change detected'))
                except:
                    desc = 'Change detected'
                
                # Replace Unicode characters with Windows-compatible equivalents
                desc = desc.replace('→', ' -> ').replace('•', '-').replace('–', '-').replace('—', '-')
                # Remove any remaining Unicode replacement characters
                desc = desc.replace('\ufffd', '-').replace('�', '-')
                # Truncate if too long
                if len(desc) > 60:
                    desc = desc[:57] + "..."
                print(f"PARSER_DETAIL:{desc}")
            
            # Send notification
            result = await self._send_character_notification(change_set, return_message_content)
            
            if return_message_content:
                success, message_content = result
                if success:
                    self.last_notification_times[character_id] = datetime.now()
                    logger.info(f"Successfully sent notification for character {character_id}")
                    self._track_delivery_success(character_id)
                return success, message_content
            else:
                success = result
                if success:
                    self.last_notification_times[character_id] = datetime.now()
                    logger.info(f"Successfully sent notification for character {character_id}")
                    self._track_delivery_success(character_id)
                return success
            
        except Exception as e:
            logger.error(f"Error checking character {character_id} for changes: {e}")
            if return_message_content:
                return False, ""
            return False
    
    async def check_and_notify_multiple_characters(
        self,
        character_ids: List[int],
        min_change_interval: timedelta = timedelta(minutes=5)
    ) -> Dict[int, bool]:
        """
        Check multiple characters for changes and send notifications.
        
        Args:
            character_ids: List of character IDs to check
            min_change_interval: Minimum time between notifications
            
        Returns:
            Dictionary mapping character_id to success status
        """
        results = {}
        change_sets_to_notify = []
        
        # Collect all change sets first
        for character_id in character_ids:
            try:
                # Check timing
                last_notification = self.last_notification_times.get(character_id)
                if (last_notification and 
                    datetime.now() - last_notification < min_change_interval):
                    results[character_id] = False
                    continue
                
                # For file-based storage, use the same approach as single character
                # Find all snapshot files for this character
                storage_dir = self.storage_dir
                pattern = f"character_{character_id}_*.json"
                
                # Find all snapshot files for this character
                snapshot_files = sorted(storage_dir.glob(pattern), key=lambda p: p.stat().st_mtime)
                
                if len(snapshot_files) < 2:
                    results[character_id] = False
                    continue
                
                # Load the two most recent snapshots
                try:
                    import json
                    with open(snapshot_files[-2], 'r', encoding='utf-8') as f:
                        old_data = json.load(f)
                    with open(snapshot_files[-1], 'r', encoding='utf-8') as f:
                        new_data = json.load(f)
                    
                    # Create simple snapshot objects for comparison
                    class SimpleSnapshot:
                        def __init__(self, data, file_path, version):
                            self.character_data = data
                            self.character_id = character_id
                            self.timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
                            self.version = version
                    
                    # Use timestamp-based version numbering
                    import re
                    from pathlib import Path
                    
                    def extract_timestamp_version(filepath):
                        """Extract timestamp from filename for version numbering."""
                        filename = Path(filepath).stem
                        # Extract timestamp from filename like "character_143359582_2025-07-04T00-07-38.244679"
                        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})', filename)
                        if timestamp_match:
                            return timestamp_match.group(1)
                        return filename  # Fallback to filename
                    
                    old_version = extract_timestamp_version(snapshot_files[-2])
                    new_version = extract_timestamp_version(snapshot_files[-1])
                    
                    old_snapshot = SimpleSnapshot(old_data, snapshot_files[-2], old_version)
                    new_snapshot = SimpleSnapshot(new_data, snapshot_files[-1], new_version)
                    
                except Exception as e:
                    logger.error(f"Failed to load snapshots for character {character_id}: {e}")
                    results[character_id] = False
                    continue
                
                # Detect changes
                change_set = self.change_detector.detect_changes(old_snapshot, new_snapshot)
                
                if not change_set.changes:
                    results[character_id] = False
                    continue
                
                # Apply filtering
                filtered_changes = self.change_detector.filter_changes_by_groups(
                    change_set.changes,
                    include_groups=self.config.include_groups,
                    exclude_groups=self.config.exclude_groups
                )
                
                if not filtered_changes:
                    results[character_id] = False
                    continue
                
                change_set.changes = filtered_changes
                change_sets_to_notify.append(change_set)
                
            except Exception as e:
                logger.error(f"Error processing character {character_id}: {e}")
                results[character_id] = False
        
        # Send notifications
        if change_sets_to_notify:
            success = await self._send_multiple_character_notifications(change_sets_to_notify)
            
            # Update results and timestamps
            for change_set in change_sets_to_notify:
                results[change_set.character_id] = success
                if success:
                    self.last_notification_times[change_set.character_id] = datetime.now()
        
        logger.info(f"Processed {len(character_ids)} characters, "
                   f"sent notifications for {len(change_sets_to_notify)}")
        
        return results
    
    async def _send_character_notification(self, change_set: CharacterChangeSet, return_content: bool = False) -> Union[bool, Tuple[bool, str]]:
        """Send Discord notification for a single character."""
        try:
            # Get character avatar if available
            avatar_url = await self._get_character_avatar_url(change_set.character_id)

            # Format messages (consolidate to prevent duplicates)
            messages = self.formatter.format_character_changes(
                change_set,
                max_changes=self.config.max_changes_per_notification,
                avatar_url=avatar_url
            )

            # Apply party inventory customizations if this is a party inventory changeset
            is_party_inventory = change_set.metadata.get("is_party_inventory", False)
            logger.info(f"DEBUG: is_party_inventory = {is_party_inventory}, metadata = {change_set.metadata}")
            if is_party_inventory:
                logger.info(f"DEBUG: Applying party inventory customizations to {len(messages)} messages")
                messages = self._customize_party_messages(messages, change_set)
                logger.info(f"DEBUG: Customizations applied successfully")
            
            # Capture message content for console output if requested
            message_content = ""
            if return_content:
                message_content = self._format_messages_for_console(messages)
            
            # Send consolidated message via Discord
            success = True
            async with DiscordService(
                webhook_url=self.config.webhook_url,
                username=self.config.username,
                avatar_url=self.config.avatar_url,
                rate_limit_requests_per_minute=self.config.rate_limit_requests_per_minute,
                rate_limit_burst=self.config.rate_limit_burst
            ) as discord:
                logger.debug(f"Sending {len(messages)} Discord message(s) for character {change_set.character_id}")
                for i, message in enumerate(messages):
                    result = await discord.send_message(message)
                    if not result:
                        success = False
                        logger.warning(f"Failed to send message {i+1}/{len(messages)} for character {change_set.character_id}")
                    
                    # Add delay between multiple messages if needed
                    if i < len(messages) - 1:
                        await asyncio.sleep(self.config.delay_between_messages)
                
                if len(messages) > 1:
                    logger.info(f"Sent {len(messages)} split messages for character {change_set.character_id}")
                
                if return_content:
                    return success, message_content
                return success
                
        except Exception as e:
            logger.error(f"Error sending notification for character {change_set.character_id}: {e}")
            if return_content:
                return False, ""
            return False
    
    def _format_messages_for_console(self, messages: List['DiscordMessage']) -> str:
        """Format Discord messages for console output with Windows-compatible encoding."""
        if not messages:
            return ""
        
        # Import here to avoid circular imports
        from services.discord_service import DiscordMessage
        
        console_output = []
        for i, message in enumerate(messages):
            if len(messages) > 1:
                console_output.append(f"--- Message {i+1}/{len(messages)} ---")
            
            # Add message content
            if message.content:
                console_output.append(self._make_console_safe(message.content))
            
            # Add embeds
            if hasattr(message, 'embeds') and message.embeds:
                for embed in message.embeds:
                    if hasattr(embed, 'title') and embed.title:
                        console_output.append(f"**{self._make_console_safe(embed.title)}**")
                    
                    if hasattr(embed, 'description') and embed.description:
                        console_output.append(self._make_console_safe(embed.description))
                    
                    if hasattr(embed, 'fields') and embed.fields:
                        for field in embed.fields:
                            # Handle field as dict (which is what we're using)
                            if isinstance(field, dict):
                                field_name = field.get('name', '')
                                field_value = field.get('value', '')
                                console_output.append(f"**{self._make_console_safe(field_name)}**")
                                console_output.append(self._make_console_safe(field_value))
                            # Handle field as object with attributes
                            elif hasattr(field, 'name') and hasattr(field, 'value'):
                                console_output.append(f"**{self._make_console_safe(field.name)}**")
                                console_output.append(self._make_console_safe(field.value))
            
            if len(messages) > 1 and i < len(messages) - 1:
                console_output.append("")  # Empty line between messages
        
        return "\n".join(console_output)
    
    async def send_startup_notification(self):
        """Send a notification when the monitor starts."""
        try:
            async with DiscordService(
                webhook_url=self.config.webhook_url,
                username=self.config.username,
                avatar_url=self.config.avatar_url
            ) as discord:
                character_count = len(self.character_ids) if hasattr(self, 'character_ids') else 1
                await discord.send_embed(
                    title="🚀 D&D Beyond Monitor Started",
                    description=f"Monitoring {character_count} character(s) for changes",
                    color=EmbedColor.SUCCESS,
                    footer_text="Monitor started successfully"
                )
                logger.info("Startup notification sent")
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")
    
    async def send_shutdown_notification(self):
        """Send a notification when the monitor shuts down."""
        try:
            async with DiscordService(
                webhook_url=self.config.webhook_url,
                username=self.config.username,
                avatar_url=self.config.avatar_url
            ) as discord:
                await discord.send_embed(
                    title="🛑 D&D Beyond Monitor Stopped",
                    description="Character monitoring has been stopped",
                    color=EmbedColor.WARNING,
                    footer_text="Monitor stopped"
                )
                logger.info("Shutdown notification sent")
        except Exception as e:
            logger.error(f"Failed to send shutdown notification: {e}")
    
    async def test_notification_system(self):
        """Test the notification system with a simple message."""
        try:
            async with DiscordService(
                webhook_url=self.config.webhook_url,
                username=self.config.username,
                avatar_url=self.config.avatar_url
            ) as discord:
                return await discord.test_webhook()
        except Exception as e:
            logger.error(f"Notification system test failed: {e}")
            return False
    
    async def send_detailed_test(self):
        """Send a detailed test notification with sample data."""
        try:
            async with DiscordService(
                webhook_url=self.config.webhook_url,
                username=self.config.username,
                avatar_url=self.config.avatar_url
            ) as discord:
                # Send a comprehensive test message
                fields = [
                    {"name": "Test Type", "value": "Detailed System Test", "inline": True},
                    {"name": "Timestamp", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": True},
                    {"name": "Status", "value": "✅ All systems operational", "inline": False}
                ]
                
                return await discord.send_embed(
                    title="🧪 Detailed Test Notification",
                    description="This is a comprehensive test of the Discord notification system with sample formatting.",
                    color=EmbedColor.INFO,
                    fields=fields,
                    footer_text="Detailed test completed"
                )
        except Exception as e:
            logger.error(f"Detailed test failed: {e}")
            return False
    
    async def _send_character_discovered_notification(self, character_id: int):
        """Send notification for newly discovered character."""
        try:
            # Get character name and avatar
            character_name = await self._get_character_name(character_id)
            avatar_url = await self._get_character_avatar_url(character_id)
            
            async with DiscordService(
                webhook_url=self.config.webhook_url,
                username=self.config.username,
                avatar_url=self.config.avatar_url
            ) as discord:
                await discord.send_embed(
                    title="🆕 New Character Discovered",
                    description=f"Started monitoring **{character_name}** for changes.",
                    color=EmbedColor.SUCCESS,
                    footer_text="Character monitoring started",
                    thumbnail_url=avatar_url
                )
                logger.info(f"Character discovered notification sent for {character_name} ({character_id})")
        except Exception as e:
            logger.error(f"Failed to send character discovered notification: {e}")
    
    async def _send_multiple_character_notifications(
        self, 
        change_sets: List[CharacterChangeSet]
    ) -> bool:
        """Send Discord notifications for multiple characters."""
        try:
            async with DiscordService(
                webhook_url=self.config.webhook_url,
                username=self.config.username,
                avatar_url=self.config.avatar_url,
                rate_limit_requests_per_minute=self.config.rate_limit_requests_per_minute,
                rate_limit_burst=self.config.rate_limit_burst
            ) as discord:
                
                # Send summary if configured
                if self.config.send_summary_for_multiple and len(change_sets) > 1:
                    summary_message = self.formatter.create_summary_message(change_sets)
                    await discord.send_message(summary_message)
                    await asyncio.sleep(self.config.delay_between_messages)
                
                # Send individual character notifications
                for i, change_set in enumerate(change_sets):
                    avatar_url = await self._get_character_avatar_url(change_set.character_id)
                    
                    messages = self.formatter.format_character_changes(
                        change_set,
                        max_changes=self.config.max_changes_per_notification,
                        avatar_url=avatar_url
                    )
                    
                    # Send all messages for this character
                    for j, message in enumerate(messages):
                        success = await discord.send_message(message)
                        if not success:
                            logger.warning(f"Failed to send message {j+1}/{len(messages)} for character {change_set.character_id}")
                        
                        # Add delay between split messages
                        if j < len(messages) - 1:
                            await asyncio.sleep(self.config.delay_between_messages)
                    
                    if len(messages) > 1:
                        logger.info(f"Sent {len(messages)} split messages for character {change_set.character_id}")
                    
                    # Add delay between characters
                    if i < len(change_sets) - 1:
                        await asyncio.sleep(self.config.delay_between_messages)
                
                return True
                
        except Exception as e:
            logger.error(f"Error sending multiple character notifications: {e}")
            return False
    
    
    async def _get_character_name(self, character_id: int) -> str:
        """Get character name from storage."""
        try:
            # For file-based storage, get the latest snapshot file
            storage_dir = self.storage_dir
            pattern = f"character_{character_id}_*.json"
            
            import glob
            import json
            
            # Find the latest file
            character_files = glob.glob(str(storage_dir / pattern))
            if not character_files:
                return f"Character {character_id}"
            
            latest_file = max(character_files, key=lambda x: Path(x).stat().st_mtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                character_data = json.load(f)
                
                if 'character_info' in character_data:
                    character_info = character_data['character_info']
                    if isinstance(character_info, dict):
                        character_name = character_info.get('name', f'Character {character_id}')
                        return character_name
                
                return f"Character {character_id}"
                
        except Exception as e:
            logger.warning(f"Could not get character name for {character_id}: {e}")
            return f"Character {character_id}"

    async def _get_character_avatar_url(self, character_id: int) -> Optional[str]:
        """Get character avatar URL from storage."""
        try:
            # For file-based storage, get the latest snapshot file
            storage_dir = self.storage_dir
            pattern = f"character_{character_id}_*.json"
            
            # Find the most recent snapshot file
            snapshot_files = sorted(storage_dir.glob(pattern), key=lambda p: p.stat().st_mtime)
            
            if not snapshot_files:
                return None
                
            # Load the latest snapshot
            import json
            with open(snapshot_files[-1], 'r', encoding='utf-8') as f:
                character_data = json.load(f)
            
            # Try to get avatar URL from various possible locations
            if isinstance(character_data, dict):
                # Check character_info first (v6.0.0 format)
                if 'character_info' in character_data:
                    character_info = character_data['character_info']
                    if isinstance(character_info, dict):
                        # Check for avatarUrl (D&D Beyond format)
                        if 'avatarUrl' in character_info and character_info['avatarUrl']:
                            avatar_url = character_info['avatarUrl']
                            # Add size parameters for Discord thumbnail optimization
                            avatar_url = self._add_avatar_size_params(avatar_url)
                            return avatar_url
                        # Check for avatar_url (alternative format)
                        if 'avatar_url' in character_info and character_info['avatar_url']:
                            avatar_url = character_info['avatar_url']
                            avatar_url = self._add_avatar_size_params(avatar_url)
                            return avatar_url
                
                # Generate default D&D Beyond avatar if no custom avatar found
                if 'character_info' in character_data:
                    character_info = character_data['character_info']
                    if isinstance(character_info, dict):
                        character_name = character_info.get('name', 'Unknown')
                        character_id = character_info.get('character_id')
                        if character_id:
                            default_avatar = self._generate_default_avatar_url(character_id, character_name)
                            if default_avatar:
                                return default_avatar
                
                # Check decorations for avatar
                if 'decorations' in character_data:
                    decorations = character_data['decorations']
                    if isinstance(decorations, dict) and 'avatar' in decorations:
                        avatar = decorations['avatar']
                        if isinstance(avatar, dict) and 'avatarUrl' in avatar:
                            return avatar['avatarUrl']
                
                # Check direct avatar field
                if 'avatar' in character_data:
                    avatar = character_data['avatar']
                    if isinstance(avatar, str):
                        return avatar
                    elif isinstance(avatar, dict) and 'avatarUrl' in avatar:
                        return avatar['avatarUrl']
            
        except Exception as e:
            logger.debug(f"Could not get avatar for character {character_id}: {e}")
        
        return None
    
    def _add_avatar_size_params(self, avatar_url: str) -> str:
        """Add size parameters to D&D Beyond avatar URLs for Discord optimization."""
        if not avatar_url or not isinstance(avatar_url, str):
            return avatar_url
        
        # Check if it's a D&D Beyond avatar URL
        if 'dndbeyond.com' in avatar_url and 'avatars' in avatar_url:
            # Remove existing parameters if present
            if '?' in avatar_url:
                avatar_url = avatar_url.split('?')[0]
            
            # Add Discord-optimized parameters
            # 150x150 is good for Discord thumbnails, with crop and webp optimization
            avatar_url += "?width=150&height=150&fit=crop&quality=95&auto=webp"
        
        return avatar_url
    
    def _generate_default_avatar_url(self, character_id: int, character_name: str) -> Optional[str]:
        """Generate a default D&D Beyond avatar URL when no custom avatar is set."""
        try:
            # D&D Beyond sometimes uses predictable default avatar patterns
            # This is a fallback - we could also use a service like Gravatar with the character name
            
            # Option 1: Use D&D Beyond's default avatar (if we can determine the pattern)
            # For now, we'll use a placeholder approach
            
            # Option 2: Use a character initial-based avatar service
            if character_name and character_name != 'Unknown':
                # Use UI Avatars service to generate avatar from character name initials
                import urllib.parse
                name_encoded = urllib.parse.quote(character_name)
                # 150x150 matches our D&D Beyond sizing
                default_url = f"https://ui-avatars.com/api/?name={name_encoded}&size=150&background=7c4dff&color=fff&bold=true"
                return default_url
            
        except Exception as e:
            logger.debug(f"Error generating default avatar for character {character_id}: {e}")
        
        return None
    
    def _make_console_safe(self, text: str) -> str:
        """Make text safe for console output by replacing problematic Unicode characters."""
        if not text:
            return text
        
        # Emoji replacements for Windows console compatibility
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
            '📋': '[OTHER]'
        }
        
        safe_text = text
        for emoji, replacement in emoji_replacements.items():
            safe_text = safe_text.replace(emoji, replacement)
        
        return safe_text
    
    async def test_notification_system(self) -> bool:
        """
        Test the notification system by sending a test message.
        
        Returns:
            True if test successful, False otherwise
        """
        try:
            async with DiscordService(
                webhook_url=self.config.webhook_url,
                username=self.config.username,
                avatar_url=self.config.avatar_url
            ) as discord:
                return await discord.test_webhook()
                
        except Exception as e:
            logger.error(f"Notification system test failed: {e}")
            return False
    
    async def send_detailed_test(self) -> bool:
        """Send a detailed test notification showing the formatting."""
        try:
            from shared.models.change_detection import FieldChange, ChangeType, ChangePriority
            from discord.services.change_detection.models import CharacterChangeSet
            from datetime import datetime
            
            # Create realistic mock changes based on actual system descriptions
            mock_changes = [
                FieldChange(
                    field_path="basic_info.level",
                    old_value=4,
                    new_value=5,
                    change_type=ChangeType.INCREMENTED,
                    priority=ChangePriority.CRITICAL,
                    description="Level: 4 → 5"
                ),
                FieldChange(
                    field_path="spells.known",
                    old_value=["Magic Missile", "Shield"],
                    new_value=["Magic Missile", "Shield", "Fireball"],
                    change_type=ChangeType.ADDED,
                    priority=ChangePriority.HIGH,
                    description="Learned level 3 spell: Fireball"
                ),
                FieldChange(
                    field_path="spells.cantrips",
                    old_value=["Fire Bolt", "Mage Hand"],
                    new_value=["Fire Bolt", "Mage Hand", "Prestidigitation"],
                    change_type=ChangeType.ADDED,
                    priority=ChangePriority.HIGH,
                    description="Learned cantrip: Prestidigitation"
                ),
                FieldChange(
                    field_path="hit_points.maximum",
                    old_value=32,
                    new_value=38,
                    change_type=ChangeType.INCREMENTED,
                    priority=ChangePriority.HIGH,
                    description="Maximum HP: 32 → 38"
                ),
                FieldChange(
                    field_path="features",
                    old_value=["Action Surge"],
                    new_value=["Action Surge", "Second Wind"],
                    change_type=ChangeType.ADDED,
                    priority=ChangePriority.HIGH,
                    description="Gained feature: Second Wind"
                ),
                FieldChange(
                    field_path="inventory.items",
                    old_value=["Longsword", "Shield"],
                    new_value=["Longsword", "Shield", "Potion of Healing"],
                    change_type=ChangeType.ADDED,
                    priority=ChangePriority.MEDIUM,
                    description="Added 1x Potion of Healing"
                ),
                FieldChange(
                    field_path="equipment.armor",
                    old_value="Leather Armor",
                    new_value="Studded Leather Armor",
                    change_type=ChangeType.MODIFIED,
                    priority=ChangePriority.MEDIUM,
                    description="Equipped: Studded Leather Armor"
                ),
                FieldChange(
                    field_path="proficiencies.skills",
                    old_value=["Athletics", "Intimidation"],
                    new_value=["Athletics", "Intimidation", "Stealth"],
                    change_type=ChangeType.ADDED,
                    priority=ChangePriority.MEDIUM,
                    description="Gained proficiency: Stealth"
                ),
                FieldChange(
                    field_path="currency.gold",
                    old_value=150,
                    new_value=125,
                    change_type=ChangeType.DECREMENTED,
                    priority=ChangePriority.LOW,
                    description="GP: 150 → 125 (-25)"
                ),
                FieldChange(
                    field_path="spell_slots.level_1",
                    old_value=2,
                    new_value=3,
                    change_type=ChangeType.INCREMENTED,
                    priority=ChangePriority.MEDIUM,
                    description="Level 1 spell slots: 2 → 3"
                )
            ]
            
            # Create mock change set
            change_set = CharacterChangeSet(
                character_id=143359582,
                character_name="Test Character",
                from_version=4,
                to_version=5,
                timestamp=datetime.now(),
                changes=mock_changes,
                summary="Level up with new spells and equipment changes"
            )
            
            # Get test avatar
            avatar_url = "https://www.dndbeyond.com/avatars/17/196/636377838221407838.jpeg?width=150&height=150&fit=crop&quality=95&auto=webp"
            
            # Format and send detailed message
            messages = self.formatter.format_character_changes(
                change_set,
                max_changes=self.config.max_changes_per_notification,
                avatar_url=avatar_url
            )
            
            async with DiscordService(
                webhook_url=self.config.webhook_url,
                username=self.config.username,
                avatar_url=self.config.avatar_url
            ) as discord:
                for message in messages:
                    result = await discord.send_message(message)
                    if not result:
                        return False
                    if len(messages) > 1:
                        await asyncio.sleep(2.0)
                
                return True
                
        except Exception as e:
            logger.error(f"Detailed test failed: {e}")
            return False
    
    async def send_startup_notification(self) -> bool:
        """Send a notification that the monitoring system has started."""
        try:
            async with DiscordService(
                webhook_url=self.config.webhook_url,
                username=self.config.username,
                avatar_url=self.config.avatar_url
            ) as discord:
                return await discord.send_embed(
                    title="🎲 D&D Beyond Monitor Started",
                    description="Character monitoring system is now active and watching for changes.",
                    color=EmbedColor.SUCCESS,
                    footer_text=f"Min Priority: {self.config.min_priority.name}"
                )
                
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")
            return False
    
    async def send_shutdown_notification(self) -> bool:
        """Send a notification that the monitoring system is stopping."""
        try:
            async with DiscordService(
                webhook_url=self.config.webhook_url,
                username=self.config.username,
                avatar_url=self.config.avatar_url
            ) as discord:
                return await discord.send_embed(
                    title="🎲 D&D Beyond Monitor Stopped",
                    description="Character monitoring system has been stopped.",
                    color=EmbedColor.WARNING,
                    footer_text="Monitor will resume when restarted"
                )
                
        except Exception as e:
            logger.error(f"Failed to send shutdown notification: {e}")
            return False
    
    async def _send_character_discovered_notification(self, character_id: int) -> bool:
        """Send a notification when a character is discovered for the first time."""
        try:
            # Get character name and avatar
            character_name = await self._get_character_name(character_id)
            avatar_url = await self._get_character_avatar_url(character_id)
            
            async with DiscordService(
                webhook_url=self.config.webhook_url,
                username=self.config.username,
                avatar_url=self.config.avatar_url
            ) as discord:
                return await discord.send_embed(
                    title="🆕 New Character Discovered",
                    description=f"Now monitoring **{character_name}** for changes.\n\nFuture updates will be reported here.",
                    color=EmbedColor.INFO,
                    footer_text="Baseline snapshot saved",
                    thumbnail_url=avatar_url
                )
                
        except Exception as e:
            logger.error(f"Failed to send character discovered notification: {e}")
            return False
    
    def _track_delivery_success(self, character_id: int):
        """Track successful notification delivery for simple reliability monitoring."""
        if not hasattr(self, 'delivery_stats'):
            self.delivery_stats = {}
        
        if character_id not in self.delivery_stats:
            self.delivery_stats[character_id] = {'total': 0, 'last_success': None}
        
        self.delivery_stats[character_id]['total'] += 1
        self.delivery_stats[character_id]['last_success'] = datetime.now()
        
        logger.debug(f"Delivery success tracked for character {character_id}")
    
    def get_delivery_stats(self) -> Dict[int, Dict[str, Any]]:
        """Get simple delivery statistics."""
        return getattr(self, 'delivery_stats', {})

    async def check_and_notify_party_inventory_changes(self, character_data: Dict[str, Any]) -> bool:
        """
        Check for party inventory changes and send notifications if found.

        Args:
            character_data: Character data that may contain party inventory

        Returns:
            True if changes were detected and notification sent, False if no changes or error
        """
        try:
            # Process character data for party inventory changes
            party_changes = self.party_tracker.process_character_for_party_changes(character_data)

            if not party_changes:
                logger.debug("No party inventory changes detected")
                return False  # No changes detected

            # Extract campaign info for virtual character creation
            equipment = character_data.get('equipment', {})
            party_inventory = equipment.get('party_inventory', {})
            campaign_id = party_inventory.get('campaign_id')

            if not campaign_id:
                logger.warning("Party changes detected but no campaign ID found")
                return False

            # Get campaign name from character details
            character_details = character_data.get('character_details', {})
            campaign_name = character_details.get('campaign_name') if character_details else None

            # Create virtual character changeset
            virtual_character_id = self.party_tracker.get_virtual_character_id(str(campaign_id))
            virtual_character_name = f"Party Inventory ({campaign_name})" if campaign_name else f"Party Inventory (Campaign {campaign_id})"

            # Create changeset in format expected by notification system
            changeset = CharacterChangeSet(
                character_id=virtual_character_id,
                character_name=virtual_character_name,
                from_version=0,  # Version tracking for party inventory
                to_version=1,
                timestamp=datetime.now(),
                changes=party_changes,
                summary=f"Party inventory changes for {campaign_name}" if campaign_name else f"Party inventory changes for campaign {campaign_id}",
                metadata={
                    "is_party_inventory": True,
                    "campaign_id": campaign_id,
                    "campaign_name": campaign_name,
                    "change_count": len(party_changes)
                }
            )

            # Send notification using existing infrastructure
            return await self._send_character_notification(changeset)

        except Exception as e:
            logger.error(f"Error checking party inventory changes: {e}")
            return False


    async def _send_formatted_notification(self, changeset: CharacterChangeSet, is_party_inventory: bool = False) -> bool:
        """
        Format and send the Discord notification.

        Args:
            changeset: Filtered changeset to send
            is_party_inventory: Whether this is a party inventory notification

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Use existing formatter to create Discord message
            notification_data = self.formatter.format_character_changes(changeset)

            # Customize for party inventory
            if is_party_inventory:
                notification_data = self._customize_party_notification(notification_data, changeset)

            # Send via Discord service
            async with DiscordService(
                webhook_url=self.config.webhook_url,
                username=self.config.username,
                avatar_url=self.config.avatar_url
            ) as discord:
                # Send based on notification format
                if notification_data.get('embeds'):
                    success = await discord.send_embeds(notification_data['embeds'])
                else:
                    success = await discord.send_message(notification_data.get('content', 'Party inventory updated'))

                if success:
                    logger.info(f"Successfully sent {'party inventory' if is_party_inventory else 'character'} notification for {changeset.character_name}")
                    self._track_delivery_success(changeset.character_id)
                    return True
                else:
                    logger.error(f"Failed to send {'party inventory' if is_party_inventory else 'character'} notification for {changeset.character_name}")
                    return False

        except Exception as e:
            logger.error(f"Error formatting/sending notification: {e}")
            return False

    def _customize_party_notification(self, notification_data: Dict[str, Any], changeset: CharacterChangeSet) -> Dict[str, Any]:
        """
        Customize notification data for party inventory with improved formatting and icons.

        Args:
            notification_data: Base notification data from formatter
            changeset: Party inventory changeset

        Returns:
            Customized notification data with inventory-specific styling
        """
        try:
            # Customize embeds if present
            if 'embeds' in notification_data and notification_data['embeds']:
                for embed in notification_data['embeds']:
                    # Enhance title with party inventory icon
                    if 'title' in embed:
                        embed['title'] = f"🎒 {embed['title']}"

                    # Add campaign info to footer
                    campaign_id = changeset.metadata.get('campaign_id')
                    campaign_name = changeset.metadata.get('campaign_name')
                    if campaign_id and 'footer' in embed:
                        current_footer = embed['footer'].get('text', '')
                        campaign_display = campaign_name if campaign_name else f"Campaign {campaign_id}"
                        embed['footer']['text'] = f"{campaign_display} | {current_footer}".strip(' |')

                    # Use inventory-themed color (brown/leather)
                    embed['color'] = 0x8B4513  # Brown color for party inventory

                    # Enhance field formatting for inventory changes
                    if 'fields' in embed:
                        embed['fields'] = self._enhance_party_inventory_fields(embed['fields'], changeset.changes)

            # Customize content if no embeds
            elif 'content' in notification_data:
                notification_data['content'] = f"🎒 {notification_data['content']}"

            return notification_data

        except Exception as e:
            logger.error(f"Error customizing party notification: {e}")
            return notification_data

    def _enhance_party_inventory_fields(self, fields: List[Dict[str, Any]], changes: List) -> List[Dict[str, Any]]:
        """
        Enhance Discord embed fields for party inventory changes with better icons and categorization.

        Args:
            fields: List of Discord embed fields
            changes: List of FieldChange objects

        Returns:
            Enhanced fields with inventory-specific formatting
        """
        try:
            enhanced_fields = []

            for field in fields:
                field_name = field.get('name', '')
                field_value = field.get('value', '')

                # Replace generic "Other" category or equipment category with inventory-specific categories
                # This handles both "📋 Other (1)" and other generic categories for party inventory
                if ('Other' in field_name or 'equipment' in field_name.lower() or 'inventory' in field_name.lower()) and '(' in field_name:
                    # Analyze changes to categorize them properly
                    currency_changes = 0
                    item_changes = 0
                    container_changes = 0

                    # Analyze both field paths and descriptions to properly categorize
                    for change in changes:
                        change_text = ''

                        # Get text from field path
                        if hasattr(change, 'field_path'):
                            change_text += change.field_path.lower()

                        # Get text from description
                        if hasattr(change, 'description') and change.description:
                            change_text += ' ' + change.description.lower()

                        # Also check the field_value for additional context
                        change_text += ' ' + field_value.lower()

                        # Categorize based on combined text analysis
                        if any(word in change_text for word in ['currency', 'gp', 'gold', 'pp', 'platinum', 'cp', 'copper', 'sp', 'silver', 'ep', 'electrum']):
                            currency_changes += 1
                        elif any(word in change_text for word in ['container', 'bag of holding', 'handy haversack', 'bag', 'chest', 'pouch']):
                            container_changes += 1
                        elif any(word in change_text for word in ['added', 'removed', 'item', 'inventory', 'equipment']):
                            item_changes += 1
                        else:
                            # Default to items if we can't determine
                            item_changes += 1

                    # Create inventory-specific category fields with better separation
                    if currency_changes > 0:
                        enhanced_fields.append({
                            'name': f'💰 **Party Currency** • {currency_changes} change{"s" if currency_changes != 1 else ""}',
                            'value': self._format_category_section(
                                self._filter_field_value_by_type(field_value, ['gp', 'gold', 'currency']),
                                'currency'
                            ),
                            'inline': field.get('inline', False)
                        })

                    if item_changes > 0:
                        enhanced_fields.append({
                            'name': f'🎒 **Party Items** • {item_changes} change{"s" if item_changes != 1 else ""}',
                            'value': self._format_category_section(
                                self._filter_field_value_by_type(field_value, ['added', 'removed', 'item']),
                                'items'
                            ),
                            'inline': field.get('inline', False)
                        })

                    if container_changes > 0:
                        enhanced_fields.append({
                            'name': f'📦 **Containers** • {container_changes} change{"s" if container_changes != 1 else ""}',
                            'value': self._format_category_section(
                                self._filter_field_value_by_type(field_value, ['bag', 'container']),
                                'containers'
                            ),
                            'inline': field.get('inline', False)
                        })

                    # If we couldn't categorize, fall back to improved inventory field
                    if not (currency_changes or item_changes or container_changes):
                        change_count = field_name.split("(")[1].rstrip(")") if "(" in field_name else "?"
                        enhanced_fields.append({
                            'name': f'🎒 **Party Inventory** • {change_count} change{"s" if change_count != "1" else ""}',
                            'value': self._format_category_section(field_value, 'general'),
                            'inline': field.get('inline', False)
                        })
                else:
                    # Keep non-"Other" fields as-is but enhance icons for party inventory
                    enhanced_field_name = self._enhance_party_field_name(field_name)
                    enhanced_fields.append({
                        'name': enhanced_field_name,
                        'value': self._enhance_party_field_value(field_value),
                        'inline': field.get('inline', False)
                    })

            return enhanced_fields

        except Exception as e:
            logger.error(f"Error enhancing party inventory fields: {e}")
            return fields

    def _filter_field_value_by_type(self, field_value: str, keywords: List[str]) -> str:
        """Filter field value lines that contain specific keywords."""
        try:
            lines = field_value.split('\n')
            filtered_lines = []

            for line in lines:
                line_lower = line.lower()
                if any(keyword.lower() in line_lower for keyword in keywords):
                    filtered_lines.append(line)

            return '\n'.join(filtered_lines) if filtered_lines else field_value

        except Exception:
            return field_value

    def _enhance_party_field_name(self, field_name: str) -> str:
        """Enhance field names with party inventory appropriate icons."""
        try:
            if 'currency' in field_name.lower() or 'gp' in field_name.lower():
                return f"💰 {field_name}"
            elif 'item' in field_name.lower() or 'equipment' in field_name.lower():
                return f"🎒 {field_name}"
            elif 'container' in field_name.lower() or 'bag' in field_name.lower():
                return f"📦 {field_name}"
            else:
                return f"🎒 {field_name}"  # Default party inventory icon

        except Exception:
            return field_name

    def _enhance_party_field_value(self, field_value: str) -> str:
        """Enhance field values with better formatting for party inventory."""
        try:
            lines = field_value.split('\n')
            enhanced_lines = []

            for line in lines:
                # Enhance currency changes
                if 'gp' in line.lower() or 'gold' in line.lower():
                    enhanced_lines.append(f"💰 {line}")
                # Enhance item additions/removals
                elif 'added' in line.lower() and 'to party' in line.lower():
                    enhanced_lines.append(f"📥 {line}")
                elif 'removed' in line.lower() and 'from party' in line.lower():
                    enhanced_lines.append(f"📤 {line}")
                # Enhance container-related changes
                elif any(container in line.lower() for container in ['bag of holding', 'handy haversack', 'container']):
                    enhanced_lines.append(f"📦 {line}")
                else:
                    enhanced_lines.append(line)

            return '\n'.join(enhanced_lines)

        except Exception:
            return field_value

    def _format_category_section(self, field_value: str, category_type: str) -> str:
        """
        Format a category section with better visual separation and item differentiation.

        Args:
            field_value: The raw field value content
            category_type: Type of category (currency, items, containers, general)

        Returns:
            Formatted section with improved visual hierarchy
        """
        try:
            lines = field_value.split('\n')
            formatted_lines = []

            for i, line in enumerate(lines):
                if not line.strip():
                    continue

                # Remove existing icons and emoji from the beginning to avoid duplication
                # This handles cases like "🔄 🎒 New party inventory..." and "🔄 ➕ Added 1x..."
                clean_line = line
                # Remove all common change and category icons
                for icon in ['🔄', '➕', '➖', '💰', '🎒', '📦', '📥', '📤', '📋', '✨', '⚔️', '🛡️']:
                    clean_line = clean_line.replace(icon, '')
                clean_line = clean_line.strip()

                if category_type == 'currency':
                    # Currency items with clear hierarchy
                    if 'gp' in line.lower() or 'gold' in line.lower():
                        formatted_lines.append(f"   💸 {clean_line}")
                    else:
                        formatted_lines.append(f"   💰 {clean_line}")

                elif category_type == 'items':
                    # Item changes with action icons
                    if 'added' in line.lower():
                        formatted_lines.append(f"   📥 {clean_line}")
                    elif 'removed' in line.lower():
                        formatted_lines.append(f"   📤 {clean_line}")
                    else:
                        formatted_lines.append(f"   🔄 {clean_line}")

                elif category_type == 'containers':
                    # Container-related changes
                    if 'bag of holding' in line.lower():
                        formatted_lines.append(f"   🎒 {clean_line}")
                    elif 'handy haversack' in line.lower():
                        formatted_lines.append(f"   🎒 {clean_line}")
                    else:
                        formatted_lines.append(f"   📦 {clean_line}")

                else:  # general
                    # General party inventory items
                    formatted_lines.append(f"   • {clean_line}")

                # Add minimal spacing between items for better readability
                if i < len(lines) - 1 and line.strip():  # Add space after each item except the last
                    formatted_lines.append("")

            # Join with newlines and add section borders
            content = '\n'.join(formatted_lines)

            # Add visual formatting for better section separation
            if content.strip():
                # Use simple indentation and line breaks instead of code blocks
                return content
            else:
                return field_value

        except Exception as e:
            logger.error(f"Error formatting category section: {e}")
            return field_value

    def _customize_party_messages(self, messages: List, changeset: CharacterChangeSet) -> List:
        """
        Apply party inventory customizations to Discord messages.

        Args:
            messages: List of DiscordMessage objects
            changeset: Party inventory changeset

        Returns:
            List of customized DiscordMessage objects
        """
        try:
            customized_messages = []

            for message in messages:
                # Create a copy of the DiscordMessage
                customized_message = replace(message)

                # Customize embeds
                if message.embeds:
                    customized_embeds = []

                    for embed in message.embeds:
                        # Create a deep copy of the embed since it contains nested structures
                        customized_embed = deepcopy(embed)

                        # Add party inventory icon to title
                        if hasattr(customized_embed, 'title') and customized_embed.title:
                            customized_embed.title = f"🎒 {customized_embed.title}"

                        # Use inventory-themed color
                        customized_embed.color = 0x8B4513

                        # Add campaign info to footer
                        campaign_id = changeset.metadata.get('campaign_id')
                        campaign_name = changeset.metadata.get('campaign_name')
                        if campaign_id and hasattr(customized_embed, 'footer') and customized_embed.footer:
                            current_footer = customized_embed.footer.get('text', '') if isinstance(customized_embed.footer, dict) else ''
                            campaign_display = campaign_name if campaign_name else f"Campaign {campaign_id}"
                            customized_embed.footer['text'] = f"{campaign_display} | {current_footer}".strip(' |')

                        # Most importantly: enhance the description for party inventory formatting
                        if hasattr(customized_embed, 'description') and customized_embed.description:
                            customized_embed.description = self._enhance_party_inventory_description(
                                customized_embed.description, changeset.changes
                            )

                        customized_embeds.append(customized_embed)

                    customized_message = replace(customized_message, embeds=customized_embeds)

                # Customize content if no embeds
                elif message.content:
                    customized_message = replace(customized_message, content=f"🎒 {message.content}")

                customized_messages.append(customized_message)

            return customized_messages

        except Exception as e:
            logger.error(f"Error customizing party messages: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return messages

    def _enhance_party_inventory_description(self, description: str, changes: List) -> str:
        """
        Enhance the embed description for party inventory with better formatting.

        Args:
            description: Original embed description
            changes: List of FieldChange objects

        Returns:
            Enhanced description with better party inventory formatting
        """
        try:
            lines = description.split('\n')
            enhanced_lines = []

            # Keep the title line
            if lines and "total changes" in lines[0]:
                enhanced_lines.append(lines[0])
                lines = lines[1:]

            # Process each line to enhance party inventory formatting
            currency_changes = []
            item_changes = []
            container_changes = []
            discovery_changes = []
            other_changes = []

            # Group changes by type for better organization
            for change in changes:
                field_path = change.field_path.lower()
                description_text = change.description

                # Categorize based on field path and description
                if 'discovery' in field_path or 'new party inventory discovered' in description_text:
                    discovery_changes.append(change)
                elif 'items' in field_path or any(action in description_text.lower() for action in ['added', 'removed']):
                    item_changes.append(change)
                elif any(currency in field_path for currency in ['pp', 'gp', 'sp', 'cp', 'currency']):
                    currency_changes.append(change)
                elif 'container' in field_path or 'bag' in field_path:
                    container_changes.append(change)
                else:
                    other_changes.append(change)

            # Add discovery section first (for new party found)
            if discovery_changes:
                enhanced_lines.append("")
                enhanced_lines.append("🆕 **Party Discovery**")
                for change in discovery_changes:
                    enhanced_lines.append(f"   {change.description}")

            # Add currency section
            if currency_changes:
                enhanced_lines.append("")
                enhanced_lines.append(f"💰 **Currency Changes** ({len(currency_changes)})")
                for change in currency_changes:
                    emoji = "💎" if "PP" in change.description else "💰"
                    enhanced_lines.append(f"   {emoji} {change.description}")

            # Add items section
            if item_changes:
                enhanced_lines.append("")
                enhanced_lines.append(f"🎒 **Item Changes** ({len(item_changes)})")
                for change in item_changes:
                    if 'added' in change.description.lower():
                        emoji = "➕"
                    elif 'removed' in change.description.lower():
                        emoji = "➖"
                    else:
                        emoji = "🔄"
                    enhanced_lines.append(f"   {emoji} {change.description}")

            # Add container section
            if container_changes:
                enhanced_lines.append("")
                enhanced_lines.append(f"📦 **Container Changes** ({len(container_changes)})")
                for change in container_changes:
                    enhanced_lines.append(f"   📦 {change.description}")

            # Add other changes if any
            if other_changes:
                enhanced_lines.append("")
                enhanced_lines.append(f"📋 **Other Changes** ({len(other_changes)})")
                for change in other_changes:
                    enhanced_lines.append(f"   🔄 {change.description}")

            return '\n'.join(enhanced_lines)

        except Exception as e:
            logger.error(f"Error enhancing party inventory description: {e}")
            return description

    def _filter_changes_by_config(self, changes: List[Any]) -> List[Any]:
        """
        Filter changes based on configuration (priority, groups, etc.).

        Args:
            changes: List of changes to filter

        Returns:
            Filtered list of changes
        """
        try:
            filtered = []

            for change in changes:
                # Check minimum priority
                if hasattr(change, 'priority') and change.priority.value < self.config.min_priority.value:
                    continue

                # Check include/exclude groups (simplified version)
                if self.config.include_groups or self.config.exclude_groups:
                    # For party inventory, always include inventory category changes
                    if hasattr(change, 'category') and str(change.category).lower() == 'inventory':
                        filtered.append(change)
                        continue

                    # Apply group filtering logic here if needed
                    # (This would need more complex group mapping)

                filtered.append(change)

            return filtered

        except Exception as e:
            logger.error(f"Error filtering changes: {e}")
            return changes  # Return unfiltered on error