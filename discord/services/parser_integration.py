#!/usr/bin/env python3
"""
Parser Integration for Discord Notifications

Provides utilities for the parser to trigger Discord notifications for both
character changes and party inventory changes.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Add project paths for imports
project_root = Path(__file__).absolute().parent.parent.parent
discord_root = Path(__file__).absolute().parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(discord_root) not in sys.path:
    sys.path.insert(0, str(discord_root))

from .notification_manager import NotificationManager, NotificationConfig
from shared.models.change_detection import ChangePriority

logger = logging.getLogger(__name__)


class DiscordParserIntegration:
    """
    Integration layer between the parser and Discord notification system.

    Handles both character change notifications and party inventory change notifications.
    """

    def __init__(self, discord_config_path: str = "config/discord.yaml"):
        """
        Initialize the Discord parser integration.

        Args:
            discord_config_path: Path to Discord configuration file
        """
        self.discord_config_path = Path(discord_config_path)
        self.notification_manager = None
        self.config = None

        logger.info(f"Discord parser integration initialized with config: {discord_config_path}")

    def _load_discord_config(self) -> Dict[str, Any]:
        """Load Discord configuration from file."""
        try:
            import yaml

            if not self.discord_config_path.exists():
                logger.warning(f"Discord config not found at {self.discord_config_path}, notifications disabled")
                return {}

            with open(self.discord_config_path, 'r') as f:
                config = yaml.safe_load(f)

            # Process environment variables (similar to discord_monitor.py)
            config = self._process_config_with_env_vars(config)

            return config

        except Exception as e:
            logger.error(f"Error loading Discord config: {e}")
            return {}

    def _process_config_with_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process configuration with environment variable substitution."""
        processed_config = config.copy()

        # Environment variable mappings
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
                    logger.debug(f"Using environment variable {env_var} for {config_key}")
                    break

        return processed_config

    def _create_notification_config(self, config: Dict[str, Any]) -> NotificationConfig:
        """Create NotificationConfig from loaded configuration."""
        # Parse minimum priority
        min_priority_name = config.get('discord', {}).get('min_priority', 'MEDIUM')
        try:
            min_priority = ChangePriority[min_priority_name.upper()]
        except KeyError:
            logger.warning(f"Invalid priority '{min_priority_name}', using MEDIUM")
            min_priority = ChangePriority.MEDIUM

        # Parse Discord settings
        discord_config = config.get('discord', {})
        rate_limit = discord_config.get('rate_limit', {})

        return NotificationConfig(
            webhook_url=config.get('webhook_url', ''),
            username=discord_config.get('username', 'D&D Beyond Parser'),
            avatar_url=discord_config.get('avatar_url'),
            max_changes_per_notification=discord_config.get('maximum_changes_per_notification', 20),
            min_priority=min_priority,
            include_groups=None,  # Could be configured if needed
            exclude_groups=None,
            rate_limit_requests_per_minute=rate_limit.get('requests_per_minute', 3),
            rate_limit_burst=rate_limit.get('maximum_burst_requests', 1),
            timezone=discord_config.get('timezone', 'UTC'),
            send_summary_for_multiple=False,  # Parser sends individual notifications
            delay_between_messages=discord_config.get('delay_between_messages', 2.0)
        )

    async def initialize(self) -> bool:
        """
        Initialize the notification manager.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Load configuration
            self.config = self._load_discord_config()

            if not self.config.get('webhook_url'):
                logger.info("No Discord webhook URL configured, notifications disabled")
                return False

            # Create notification config
            notification_config = self._create_notification_config(self.config)

            # Initialize notification manager
            # Use default storage directory structure
            project_root = Path(__file__).absolute().parent.parent.parent
            storage_dir = project_root / "character_data" / "discord"

            self.notification_manager = NotificationManager(
                storage=None,  # File-based storage
                config=notification_config,
                storage_dir=str(storage_dir)
            )

            logger.info("Discord parser integration initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Error initializing Discord parser integration: {e}")
            return False

    async def notify_character_changes(self, character_data: Dict[str, Any]) -> bool:
        """
        Notify about character changes using the notification manager's change detection.

        Args:
            character_data: Complete character data dictionary

        Returns:
            True if notification handled successfully, False otherwise
        """
        try:
            if not self.notification_manager:
                logger.debug("Notification manager not initialized, skipping character notification")
                return False

            character_info = character_data.get('character_info', {})
            character_id = character_info.get('character_id')
            character_name = character_info.get('name', 'Unknown Character')

            if not character_id:
                logger.warning("No character ID found in character data, cannot detect changes")
                return False

            logger.info(f"Character change notification requested for {character_name} (ID: {character_id})")

            # Use the notification manager's existing change detection logic
            # This will compare with previous snapshots in the discord directory
            result = await self.notification_manager.check_and_notify_character_changes(character_id)

            if result:
                logger.info(f"Character change notification sent for {character_name}")
            else:
                logger.debug(f"No significant character changes detected for {character_name}")

            return result

        except Exception as e:
            logger.error(f"Error notifying character changes: {e}")
            return False

    async def notify_party_inventory_changes(self, character_data: Dict[str, Any]) -> bool:
        """
        Notify about party inventory changes.

        Args:
            character_data: Character data that may contain party inventory

        Returns:
            True if notification handled successfully, False otherwise
        """
        try:
            if not self.notification_manager:
                logger.debug("Notification manager not initialized, skipping party inventory notification")
                return False

            # Use the party inventory notification method we added
            success = await self.notification_manager.check_and_notify_party_inventory_changes(character_data)

            if success:
                logger.info("Party inventory notification processed successfully")
            else:
                logger.warning("Party inventory notification failed")

            return success

        except Exception as e:
            logger.error(f"Error notifying party inventory changes: {e}")
            return False

    async def notify_all_changes(self, character_data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Notify about both character and party inventory changes.

        Args:
            character_data: Complete character data dictionary

        Returns:
            Dictionary with notification results: {'character': bool, 'party_inventory': bool}
        """
        results = {
            'character': False,
            'party_inventory': False
        }

        try:
            # Initialize if not already done
            if not self.notification_manager:
                if not await self.initialize():
                    logger.warning("Failed to initialize Discord notifications")
                    return results

            # Double-check after initialization
            if not self.notification_manager:
                logger.info("Discord notifications not configured, skipping all notifications")
                return results

            # Notify character changes
            results['character'] = await self.notify_character_changes(character_data)

            # Notify party inventory changes
            results['party_inventory'] = await self.notify_party_inventory_changes(character_data)

            # Log summary
            success_count = sum(1 for success in results.values() if success)
            logger.info(f"Discord notifications completed: {success_count}/2 successful")

            return results

        except Exception as e:
            logger.error(f"Error in notify_all_changes: {e}")
            return results

    def is_party_inventory_enabled(self) -> bool:
        """
        Check if party inventory notifications are enabled in configuration.

        Returns:
            True if party inventory notifications should be sent
        """
        try:
            if not self.config:
                return False

            # Check if party inventory is specifically enabled
            # This could be a configuration option in discord.yaml
            discord_config = self.config.get('discord', {})
            return discord_config.get('party_inventory_enabled', True)  # Default to enabled

        except Exception as e:
            logger.error(f"Error checking party inventory configuration: {e}")
            return False

    def is_character_notifications_enabled(self) -> bool:
        """
        Check if character notifications are enabled in configuration.

        Returns:
            True if character notifications should be sent
        """
        try:
            if not self.config:
                return False

            # Check if character notifications are enabled
            discord_config = self.config.get('discord', {})
            return discord_config.get('character_notifications_enabled', True)  # Default to enabled

        except Exception as e:
            logger.error(f"Error checking character notification configuration: {e}")
            return False


# Convenience functions for parser to use
_integration_instance = None

async def send_discord_notifications(character_data: Dict[str, Any],
                                   config_path: str = "config/discord.yaml") -> Dict[str, bool]:
    """
    Convenience function for parser to send Discord notifications.

    Args:
        character_data: Complete character data dictionary
        config_path: Path to Discord configuration file

    Returns:
        Dictionary with notification results: {'character': bool, 'party_inventory': bool}
    """
    global _integration_instance

    try:
        # Create or reuse integration instance
        if _integration_instance is None:
            _integration_instance = DiscordParserIntegration(config_path)

        # Send all notifications
        return await _integration_instance.notify_all_changes(character_data)

    except Exception as e:
        logger.error(f"Error in send_discord_notifications: {e}")
        return {'character': False, 'party_inventory': False}


async def send_party_inventory_notification(character_data: Dict[str, Any],
                                          config_path: str = "config/discord.yaml") -> bool:
    """
    Convenience function for parser to send only party inventory notifications.

    Args:
        character_data: Character data that may contain party inventory
        config_path: Path to Discord configuration file

    Returns:
        True if notification sent successfully
    """
    global _integration_instance

    try:
        # Create or reuse integration instance
        if _integration_instance is None:
            _integration_instance = DiscordParserIntegration(config_path)

        # Initialize if needed
        if not await _integration_instance.initialize():
            return False

        # Send party inventory notification only
        return await _integration_instance.notify_party_inventory_changes(character_data)

    except Exception as e:
        logger.error(f"Error in send_party_inventory_notification: {e}")
        return False


def reset_integration():
    """Reset the global integration instance (useful for testing)."""
    global _integration_instance
    _integration_instance = None


# Example usage for parser integration
def example_parser_integration():
    """
    Example of how the parser would integrate Discord notifications.
    """
    example_code = '''
    # In the parser (e.g., dnd_json_to_markdown.py):

    async def generate_character_sheet_with_discord(character_data, output_path, config):
        """Generate character sheet and send Discord notifications if configured."""

        # Generate the character sheet (existing functionality)
        output_path = generate_character_sheet(character_data, output_path, config)

        # Check if Discord notifications are enabled
        discord_config = config.get('discord', {})
        discord_enabled = discord_config.get('enabled', False)

        if discord_enabled:
            try:
                # Import Discord integration
                from discord.services.parser_integration import send_discord_notifications

                # Send notifications for both character and party inventory changes
                results = await send_discord_notifications(character_data)

                # Log results
                if results['character']:
                    print("✅ Character Discord notification sent")
                if results['party_inventory']:
                    print("✅ Party inventory Discord notification sent")

            except Exception as e:
                print(f"❌ Discord notification error: {e}")

        return output_path

    # Or for party inventory only:

    async def handle_party_inventory_discord(character_data, config):
        """Send Discord notification only for party inventory changes."""

        discord_config = config.get('discord', {})
        party_notifications_enabled = discord_config.get('party_inventory_enabled', False)

        if party_notifications_enabled:
            try:
                from discord.services.parser_integration import send_party_inventory_notification

                success = await send_party_inventory_notification(character_data)
                if success:
                    print("✅ Party inventory Discord notification sent")

            except Exception as e:
                print(f"❌ Party inventory Discord notification error: {e}")
    '''

    return example_code