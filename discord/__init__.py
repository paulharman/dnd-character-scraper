"""
Discord notification system for D&D character monitoring.

This package provides comprehensive Discord integration for character change notifications:
- Real-time character monitoring
- Rich Discord embeds with emojis and formatting  
- Configurable filtering and priority levels
- Multi-character campaign support
- Rate limiting and error handling
"""

from .services.discord_service import DiscordService, EmbedColor
from .services.change_detection_service import ChangeDetectionService, ChangePriority
from .services.notification_manager import NotificationManager, NotificationConfig
from .formatters.discord_formatter import DiscordFormatter

__all__ = [
    'DiscordService',
    'EmbedColor', 
    'ChangeDetectionService',
    'ChangePriority',
    'NotificationManager',
    'NotificationConfig',
    'DiscordFormatter'
]

__version__ = "1.0.0"
__author__ = "D&D Character Scraper Team"