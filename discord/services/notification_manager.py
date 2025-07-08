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
from dataclasses import dataclass
from pathlib import Path

from .discord_service import DiscordService, EmbedColor
from .change_detection_service import ChangeDetectionService, CharacterChangeSet, ChangePriority, CharacterSnapshot

# Handle both relative and absolute imports
try:
    from ..formatters.discord_formatter import DiscordFormatter, FormatType
except (ImportError, ValueError):
    # Fallback for when running as main module or beyond top-level package
    import sys
    import os
    discord_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if discord_dir not in sys.path:
        sys.path.insert(0, discord_dir)
    from formatters.discord_formatter import DiscordFormatter, FormatType

logger = logging.getLogger(__name__)


@dataclass
class NotificationConfig:
    """Configuration for Discord notifications."""
    webhook_url: str
    username: str = "D&D Beyond Monitor"
    avatar_url: Optional[str] = None
    format_type: FormatType = FormatType.DETAILED
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
        # Use unified character_data directory (one level up from discord folder)
        self.storage_dir = Path(storage_dir) if storage_dir else Path("../character_data")
        
        # Initialize services
        self.change_detector = ChangeDetectionService()
        self.formatter = DiscordFormatter(config.format_type)
        
        # Track last notification times to avoid spam
        self.last_notification_times: Dict[int, datetime] = {}
        
        logger.info("Notification manager initialized")
    
    async def check_and_notify_character_changes(
        self,
        character_id: int,
        min_change_interval: timedelta = timedelta(minutes=5),
        return_message_content: bool = False
    ) -> Union[bool, Tuple[bool, Optional[str]]]:
        """
        Check for changes to a single character and send notifications if needed.
        
        Args:
            character_id: ID of character to check
            min_change_interval: Minimum time between notifications for same character
            
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
            
            if len(snapshot_files) < 2:
                logger.info(f"Character {character_id} is new or has no previous snapshot - sending welcome notification")
                # Send a "character discovered" notification instead
                await self._send_character_discovered_notification(character_id)
                return True
            
            # Load the two most recent snapshots
            try:
                import json
                with open(snapshot_files[-2], 'r') as f:
                    old_data = json.load(f)
                with open(snapshot_files[-1], 'r') as f:
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
                return False
            
            # Use the loaded snapshots
            current_snapshot = new_snapshot
            previous_snapshot = old_snapshot
            
            # Detect changes
            change_set = self.change_detector.detect_changes(previous_snapshot, current_snapshot)
            
            if not change_set.changes:
                logger.debug(f"No changes detected for character {character_id}")
                if return_message_content:
                    return False, ""
                return False
            
            # Apply filtering
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
            
            # Check minimum priority
            qualifying_changes = [change for change in filtered_changes 
                                 if change.priority.value >= self.config.min_priority.value]
            
            if not qualifying_changes:
                logger.info(f"No changes meet minimum priority {self.config.min_priority.name}")
                logger.info(f"Change priorities: {[f'{change.field_path}:{change.priority.name}' for change in filtered_changes]}")
                if return_message_content:
                    return False, ""
                return False
            
            logger.info(f"Sending notification for {len(qualifying_changes)} qualifying changes (min priority: {self.config.min_priority.name})")
            
            # Output change summaries for parser integration
            print(f"PARSER_CHANGES:{len(qualifying_changes)}")
            print("PARSER_NOTIFICATION:true")
            for change in qualifying_changes:  # Show all changes
                # Get change description and make it Windows-compatible
                desc = str(change.description)
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
                return success, message_content
            else:
                success = result
                if success:
                    self.last_notification_times[character_id] = datetime.now()
                    logger.info(f"Successfully sent notification for character {character_id}")
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
                    with open(snapshot_files[-2], 'r') as f:
                        old_data = json.load(f)
                    with open(snapshot_files[-1], 'r') as f:
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
                            if hasattr(field, 'name') and hasattr(field, 'value'):
                                console_output.append(f"**{self._make_console_safe(field.name)}:** {self._make_console_safe(field.value)}")
            
            if len(messages) > 1 and i < len(messages) - 1:
                console_output.append("")  # Empty line between messages
        
        return "\n".join(console_output)
    
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
            with open(snapshot_files[-1], 'r') as f:
                character_data = json.load(f)
            
            # Try to get avatar URL from various possible locations
            if isinstance(character_data, dict):
                # Check basic_info first (most common location)
                if 'basic_info' in character_data:
                    basic_info = character_data['basic_info']
                    if isinstance(basic_info, dict):
                        # Check for avatarUrl (D&D Beyond format)
                        if 'avatarUrl' in basic_info and basic_info['avatarUrl']:
                            avatar_url = basic_info['avatarUrl']
                            # Add size parameters for Discord thumbnail optimization
                            avatar_url = self._add_avatar_size_params(avatar_url)
                            return avatar_url
                        # Check for avatar_url (alternative format)
                        if 'avatar_url' in basic_info and basic_info['avatar_url']:
                            avatar_url = basic_info['avatar_url']
                            avatar_url = self._add_avatar_size_params(avatar_url)
                            return avatar_url
                        
                        # Generate default D&D Beyond avatar if no custom avatar
                        character_name = basic_info.get('name', 'Unknown')
                        character_id = basic_info.get('character_id')
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
            from .change_detection_service import FieldChange, ChangeType, ChangePriority, CharacterChangeSet
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
                    footer_text=f"Format: {self.config.format_type.value} | "
                               f"Min Priority: {self.config.min_priority.name}"
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
            async with DiscordService(
                webhook_url=self.config.webhook_url,
                username=self.config.username,
                avatar_url=self.config.avatar_url
            ) as discord:
                return await discord.send_embed(
                    title="🆕 New Character Discovered",
                    description=f"Now monitoring character {character_id} for changes.\n\nFuture updates will be reported here.",
                    color=EmbedColor.INFO,
                    footer_text="Baseline snapshot saved"
                )
                
        except Exception as e:
            logger.error(f"Failed to send character discovered notification: {e}")
            return False