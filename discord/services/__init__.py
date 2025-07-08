"""
Discord services for character monitoring and notifications.
"""

from .discord_service import DiscordService, EmbedColor
from .change_detection_service import ChangeDetectionService, ChangePriority
from .notification_manager import NotificationManager, NotificationConfig

__all__ = [
    'DiscordService',
    'EmbedColor',
    'ChangeDetectionService', 
    'ChangePriority',
    'NotificationManager',
    'NotificationConfig'
]