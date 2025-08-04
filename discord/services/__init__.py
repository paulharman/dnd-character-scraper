"""
Discord services for character monitoring and notifications.
"""

from .discord_service import DiscordService, EmbedColor
from src.services.enhanced_change_detection_service import EnhancedChangeDetectionService as ChangeDetectionService
from src.models.change_detection import ChangePriority
from .notification_manager import NotificationManager, NotificationConfig

__all__ = [
    'DiscordService',
    'EmbedColor',
    'ChangeDetectionService', 
    'ChangePriority',
    'NotificationManager',
    'NotificationConfig'
]