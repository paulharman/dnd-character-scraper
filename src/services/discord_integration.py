#!/usr/bin/env python3
"""
Discord integration service for the enhanced D&D scraper.

Provides lightweight Discord notification functionality that can be integrated
into the scraper workflow without re-scraping data.
"""

import asyncio
import logging
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add discord module to path for imports
discord_path = Path(__file__).parent.parent.parent / "discord"
if str(discord_path) not in sys.path:
    sys.path.insert(0, str(discord_path))

try:
    from src.services.enhanced_change_detection_service import (
        EnhancedChangeDetectionService as ChangeDetectionService
    )
    from src.models.change_detection import ChangePriority
    from discord.services.change_detection.models import CharacterSnapshot
    from services.notification_manager import NotificationManager, NotificationConfig
except ImportError as e:
    logging.warning(f"Discord services not available: {e}")
    ChangeDetectionService = None
    NotificationManager = None
    CharacterSnapshot = None
    ChangePriority = None
    NotificationConfig = None

logger = logging.getLogger(__name__)


class DiscordIntegrationService:
    """
    Lightweight Discord integration service for the enhanced scraper.
    
    Features:
    - Uses already-scraped character data (no re-scraping)
    - Integrates with existing Discord notification system
    - Handles snapshot creation and change detection
    - Supports configuration from main scraper config
    """
    
    def __init__(self, config: Dict[str, Any], storage_dir: Optional[str] = None):
        """
        Initialize Discord integration service.
        
        Args:
            config: Discord configuration dictionary
            storage_dir: Directory for storing character snapshots
        """
        self.config = config
        self.storage_dir = Path(storage_dir) if storage_dir else Path("character_data")
        self.storage_dir.mkdir(exist_ok=True)
        
        # Initialize services if available
        self.change_detector = None
        self.notification_manager = None
        
        if ChangeDetectionService and NotificationManager:
            self.change_detector = ChangeDetectionService()
            logger.info("Discord integration service initialized")
        else:
            logger.warning("Discord services not available - notifications disabled")
    
    def is_available(self) -> bool:
        """Check if Discord services are available."""
        return self.change_detector is not None and self.notification_manager is not None
    
    async def notify_character_saved(
        self,
        character_id: int,
        character_data: Dict[str, Any],
        output_path: str
    ) -> bool:
        """
        Send Discord notification for a saved character.
        
        Args:
            character_id: Character ID
            character_data: Complete character data dictionary
            output_path: Path where character data was saved
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        if not self.is_available():
            logger.debug("Discord services not available, skipping notification")
            return False
        
        if not self.config.get('enabled', False):
            logger.debug("Discord notifications disabled in config")
            return False
        
        if not self.config.get('notify_on_save', True):
            logger.debug("Discord notifications on save disabled")
            return False
        
        try:
            # Create current snapshot
            current_snapshot = self._create_snapshot(character_id, character_data)
            
            # Find previous snapshot
            previous_snapshot = self._load_previous_snapshot(character_id)
            
            if not previous_snapshot:
                logger.info(f"No previous snapshot found for character {character_id} - first save")
                await self._send_first_save_notification(character_id, character_data)
                return True
            
            # Create notification config from main config
            notification_config = self._create_notification_config()
            
            # Initialize notification manager
            self.notification_manager = NotificationManager(
                storage=None,  # Using file-based storage
                config=notification_config,
                storage_dir=str(self.storage_dir)
            )
            
            # Detect changes
            change_set = self.change_detector.detect_changes(previous_snapshot, current_snapshot)
            
            if not change_set.changes:
                logger.info(f"No changes detected for character {character_id}")
                return True
            
            # Apply filtering based on config
            filtered_changes = self._filter_changes(change_set.changes)
            change_set.changes = filtered_changes
            
            if not filtered_changes:
                logger.info(f"All changes filtered out for character {character_id}")
                return True
            
            # Send notification
            success = await self.notification_manager._send_character_notification(change_set)
            
            if success:
                logger.info(f"Discord notification sent for character {character_id} ({len(filtered_changes)} changes)")
            else:
                logger.warning(f"Failed to send Discord notification for character {character_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending Discord notification for character {character_id}: {e}")
            return False
    
    def _create_snapshot(self, character_id: int, character_data: Dict[str, Any]) -> CharacterSnapshot:
        """Create a character snapshot from scraped data."""
        # Use current timestamp as version
        version = int(datetime.now().timestamp())
        
        return CharacterSnapshot(
            character_id=character_id,
            version=version,
            timestamp=datetime.now(),
            character_data=character_data
        )
    
    def _load_previous_snapshot(self, character_id: int) -> Optional[CharacterSnapshot]:
        """Load the most recent previous snapshot for a character."""
        try:
            # Find all snapshot files for this character
            pattern = f"character_{character_id}_*.json"
            snapshot_files = list(self.storage_dir.glob(pattern))
            
            if len(snapshot_files) < 2:
                return None
            
            # Sort by modification time and get the second most recent
            snapshot_files.sort(key=lambda p: p.stat().st_mtime)
            previous_file = snapshot_files[-2]
            
            # Load previous snapshot data
            with open(previous_file, 'r') as f:
                previous_data = json.load(f)
            
            # Create snapshot object
            version = len(snapshot_files) - 1
            return CharacterSnapshot(
                character_id=character_id,
                version=version,
                timestamp=datetime.fromtimestamp(previous_file.stat().st_mtime),
                character_data=previous_data
            )
            
        except Exception as e:
            logger.error(f"Error loading previous snapshot for character {character_id}: {e}")
            return None
    
    def _create_notification_config(self) -> NotificationConfig:
        """Create notification config from Discord config."""
        # Parse minimum priority
        min_priority_str = self.config.get('min_priority', 'LOW')
        min_priority = ChangePriority[min_priority_str.upper()]
        
        # Convert change types to include/exclude groups
        change_types = self.config.get('change_types', [])
        include_groups = self._convert_change_types_to_groups(change_types)
        
        return NotificationConfig(
            webhook_url=self.config.get('webhook_url', ''),
            username=self.config.get('username', 'D&D Beyond Scraper'),
            avatar_url=self.config.get('avatar_url'),
            max_changes_per_notification=200,  # High limit, will split if needed
            min_priority=min_priority,
            include_groups=include_groups,
            exclude_groups=None,
            rate_limit_requests_per_minute=3,
            rate_limit_burst=1,
            timezone='UTC',
            send_summary_for_multiple=False,  # Single character
            delay_between_messages=2.0
        )
    
    def _convert_change_types_to_groups(self, change_types: List[str]) -> Optional[set]:
        """Convert change types to Discord notification groups."""
        # Mapping from config change types to notification groups
        # These map to the group definitions in change_detection_service.py
        type_to_group_map = {
            'level': 'basic',
            'experience': 'basic',
            'hit_points': 'combat',
            'armor_class': 'combat',
            'ability_scores': 'abilities',
            'spells_known': 'spells',
            'spell_slots': 'spells',
            'inventory_items': 'inventory',
            'equipment': 'inventory',
            'currency': 'inventory',
            'skills': 'skills',
            'proficiencies': 'skills',
            'feats': 'skills',
            'class_features': 'basic',
            'appearance': 'appearance',
            'background': 'backstory'
        }
        
        if not change_types:
            logger.info("No change types specified in config - all changes will be included")
            return None  # None means include all groups
        
        groups = set()
        for change_type in change_types:
            if change_type in type_to_group_map:
                groups.add(type_to_group_map[change_type])
                logger.debug(f"Mapped change type '{change_type}' to group '{type_to_group_map[change_type]}'")
            else:
                logger.warning(f"Unknown change type in config: '{change_type}'")
        
        if groups:
            logger.info(f"Discord notifications will include change groups: {sorted(groups)}")
            return groups
        else:
            logger.warning("No valid change types found in config - all changes will be included")
            return None
    
    def _filter_changes(self, changes):
        """Apply additional filtering based on config."""
        if not changes:
            return changes
        
        # Apply minimum priority filter
        min_priority_str = self.config.get('min_priority', 'LOW')
        min_priority = ChangePriority[min_priority_str.upper()]
        
        filtered = [
            change for change in changes 
            if change.priority.value >= min_priority.value
        ]
        
        return filtered
    
    async def _send_first_save_notification(self, character_id: int, character_data: Dict[str, Any]):
        """Send notification for first-time character save."""
        try:
            # Create notification config
            notification_config = self._create_notification_config()
            
            # Initialize notification manager
            self.notification_manager = NotificationManager(
                storage=None,
                config=notification_config,
                storage_dir=str(self.storage_dir)
            )
            
            # Send character discovered notification
            await self.notification_manager._send_character_discovered_notification(character_id)
            
        except Exception as e:
            logger.error(f"Error sending first save notification: {e}")