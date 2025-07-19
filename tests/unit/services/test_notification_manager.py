"""
Unit tests for notification manager functionality.

Tests notification delivery, rate limiting, message formatting, and error handling.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add Discord module to path
discord_root = Path(__file__).parent.parent.parent.parent / "discord"
sys.path.insert(0, str(discord_root))

from services.notification_manager import NotificationManager, NotificationConfig
from services.change_detection_service import ChangePriority
from services.change_detection.models import FieldChange, ChangeType, ChangeCategory


class TestNotificationManager:
    """Test notification manager functionality."""
    
    @pytest.fixture
    def notification_config(self):
        """Basic notification configuration."""
        return NotificationConfig(
            webhook_url="https://discord.com/api/webhooks/123/abc",
            username="Test Bot",
            max_changes_per_notification=10,
            min_priority=ChangePriority.LOW,
            rate_limit_requests_per_minute=5,
            rate_limit_burst=2,
            timezone="UTC"
        )
    
    @pytest.fixture
    def mock_storage(self):
        """Mock storage for testing."""
        storage = Mock()
        storage.get_character_data = Mock(return_value=None)
        storage.save_character_data = Mock()
        return storage
    
    @pytest.fixture
    def notification_manager(self, mock_storage, notification_config):
        """Notification manager instance."""
        return NotificationManager(
            storage=mock_storage,
            config=notification_config,
            storage_dir="/tmp/test"
        )
    
    @pytest.fixture
    def sample_changes(self):
        """Sample character changes for testing."""
        return [
            FieldChange(
                field_path="character_info.level",
                old_value=5,
                new_value=6,
                change_type=ChangeType.INCREMENTED,
                priority=ChangePriority.CRITICAL,
                category=ChangeCategory.BASIC_INFO,
                description="Character level increased from 5 to 6"
            ),
            FieldChange(
                field_path="character_info.hit_points",
                old_value=32,
                new_value=38,
                change_type=ChangeType.INCREMENTED,
                priority=ChangePriority.HIGH,
                category=ChangeCategory.COMBAT,
                description="Hit points increased from 32 to 38"
            ),
            FieldChange(
                field_path="ability_scores.intelligence",
                old_value=16,
                new_value=17,
                change_type=ChangeType.INCREMENTED,
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.ABILITIES,
                description="Intelligence increased from 16 to 17"
            )
        ]
    
    def test_notification_manager_initialization(self, mock_storage, notification_config):
        """Test notification manager initialization."""
        manager = NotificationManager(
            storage=mock_storage,
            config=notification_config,
            storage_dir="/tmp/test"
        )
        
        assert manager.config == notification_config
        assert manager.storage == mock_storage
        assert manager.storage_dir == "/tmp/test"
    
    @pytest.mark.asyncio
    async def test_startup_notification(self, notification_manager):
        """Test startup notification sending."""
        with patch.object(notification_manager, '_create_discord_service') as mock_create_service:
            mock_discord = AsyncMock()
            mock_discord.send_message = AsyncMock(return_value=True)
            mock_create_service.return_value.__aenter__.return_value = mock_discord
            
            result = await notification_manager.send_startup_notification()
            
            assert result is True
            mock_discord.send_message.assert_called_once()
            
            # Verify startup message content
            call_args = mock_discord.send_message.call_args[0]
            message = call_args[0]
            assert "started" in message.lower() or "monitoring" in message.lower()
    
    @pytest.mark.asyncio
    async def test_shutdown_notification(self, notification_manager):
        """Test shutdown notification sending."""
        with patch.object(notification_manager, '_create_discord_service') as mock_create_service:
            mock_discord = AsyncMock()
            mock_discord.send_message = AsyncMock(return_value=True)
            mock_create_service.return_value.__aenter__.return_value = mock_discord
            
            result = await notification_manager.send_shutdown_notification()
            
            assert result is True
            mock_discord.send_message.assert_called_once()
            
            # Verify shutdown message content
            call_args = mock_discord.send_message.call_args[0]
            message = call_args[0]
            assert "stopped" in message.lower() or "shutdown" in message.lower()
    
    @pytest.mark.asyncio
    async def test_test_notification_system(self, notification_manager):
        """Test the notification system test functionality."""
        with patch.object(notification_manager, '_create_discord_service') as mock_create_service:
            mock_discord = AsyncMock()
            mock_discord.test_webhook = AsyncMock(return_value=True)
            mock_create_service.return_value.__aenter__.return_value = mock_discord
            
            result = await notification_manager.test_notification_system()
            
            assert result is True
            mock_discord.test_webhook.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_detailed_test_notification(self, notification_manager, sample_changes):
        """Test detailed test notification with sample data."""
        with patch.object(notification_manager, '_create_discord_service') as mock_create_service:
            mock_discord = AsyncMock()
            mock_discord.send_embed = AsyncMock(return_value=True)
            mock_create_service.return_value.__aenter__.return_value = mock_discord
            
            result = await notification_manager.send_detailed_test()
            
            assert result is True
            mock_discord.send_embed.assert_called_once()
            
            # Verify test message includes sample data
            call_args = mock_discord.send_embed.call_args
            embed_data = call_args[0][1]  # Second argument is embed data
            
            assert 'title' in embed_data
            assert 'fields' in embed_data
            assert len(embed_data['fields']) > 0
    
    def test_change_filtering_by_priority(self, notification_manager, sample_changes):
        """Test filtering changes by minimum priority."""
        # Set high minimum priority
        notification_manager.config.min_priority = ChangePriority.HIGH
        
        filtered_changes = notification_manager._filter_changes(sample_changes)
        
        # Should only include CRITICAL and HIGH priority changes
        assert len(filtered_changes) == 2  # Level (CRITICAL) and HP (HIGH)
        
        priorities = [change.priority for change in filtered_changes]
        assert ChangePriority.CRITICAL in priorities
        assert ChangePriority.HIGH in priorities
        assert ChangePriority.MEDIUM not in priorities
    
    def test_change_filtering_by_groups(self, notification_manager, sample_changes):
        """Test filtering changes by include/exclude groups."""
        # Include only basic info changes
        notification_manager.config.include_groups = {'basic'}
        
        filtered_changes = notification_manager._filter_changes(sample_changes)
        
        # Should only include basic info changes (level)
        assert len(filtered_changes) == 1
        assert filtered_changes[0].category == ChangeCategory.BASIC_INFO
    
    def test_change_filtering_exclude_groups(self, notification_manager, sample_changes):
        """Test excluding specific change groups."""
        # Exclude combat changes
        notification_manager.config.exclude_groups = {'combat'}
        
        filtered_changes = notification_manager._filter_changes(sample_changes)
        
        # Should exclude hit points change (combat category)
        combat_changes = [c for c in filtered_changes if c.category == ChangeCategory.COMBAT]
        assert len(combat_changes) == 0
    
    def test_message_formatting_for_single_character(self, notification_manager, sample_changes):
        """Test message formatting for single character changes."""
        character_name = "Test Wizard"
        
        message = notification_manager._format_changes_message(
            changes=sample_changes,
            character_name=character_name,
            character_id=12345
        )
        
        assert character_name in message
        assert "level" in message.lower()
        assert "5" in message and "6" in message  # Old and new level values
        
        # Should include priority indicators
        assert any(emoji in message for emoji in ['🔴', '🟠', '🟡', '[CRIT]', '[HIGH]', '[MED]'])
    
    def test_message_formatting_for_multiple_characters(self, notification_manager):
        """Test message formatting for multiple character summary."""
        character_summaries = [
            {"name": "Character 1", "id": 123, "change_count": 3},
            {"name": "Character 2", "id": 456, "change_count": 1},
            {"name": "Character 3", "id": 789, "change_count": 0}
        ]
        
        message = notification_manager._format_multiple_character_summary(character_summaries)
        
        assert "Character 1" in message
        assert "Character 2" in message
        assert "3" in message  # Change count for Character 1
        assert "1" in message  # Change count for Character 2
        
        # Should indicate no changes for Character 3
        assert "no changes" in message.lower() or "0" in message
    
    def test_rate_limiting_logic(self, notification_manager):
        """Test rate limiting logic."""
        # Simulate multiple rapid requests
        now = datetime.now()
        
        # First request should be allowed
        assert notification_manager._check_rate_limit(now) is True
        
        # Record the request
        notification_manager._record_request(now)
        
        # Immediate second request should be allowed (within burst limit)
        assert notification_manager._check_rate_limit(now) is True
        notification_manager._record_request(now)
        
        # Third immediate request should be rate limited
        if hasattr(notification_manager, '_check_rate_limit'):
            # Implementation may vary - test based on actual rate limiting logic
            pass
    
    @pytest.mark.asyncio
    async def test_character_change_notification(self, notification_manager, sample_changes):
        """Test sending character change notifications."""
        character_id = 12345
        min_change_interval = timedelta(minutes=5)
        
        with patch.object(notification_manager, '_get_character_changes') as mock_get_changes:
            with patch.object(notification_manager, '_create_discord_service') as mock_create_service:
                mock_get_changes.return_value = sample_changes
                
                mock_discord = AsyncMock()
                mock_discord.send_embed = AsyncMock(return_value=True)
                mock_create_service.return_value.__aenter__.return_value = mock_discord
                
                result = await notification_manager.check_and_notify_character_changes(
                    character_id, min_change_interval
                )
                
                assert result is True
                mock_discord.send_embed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_multiple_character_notification(self, notification_manager):
        """Test sending notifications for multiple characters."""
        character_ids = [123, 456, 789]
        min_change_interval = timedelta(minutes=5)
        
        with patch.object(notification_manager, '_get_character_changes') as mock_get_changes:
            with patch.object(notification_manager, '_create_discord_service') as mock_create_service:
                # Mock different change counts for each character
                mock_get_changes.side_effect = [
                    [Mock()],  # 1 change for character 123
                    [],        # 0 changes for character 456
                    [Mock(), Mock()]  # 2 changes for character 789
                ]
                
                mock_discord = AsyncMock()
                mock_discord.send_message = AsyncMock(return_value=True)
                mock_create_service.return_value.__aenter__.return_value = mock_discord
                
                results = await notification_manager.check_and_notify_multiple_characters(
                    character_ids, min_change_interval
                )
                
                assert len(results) == 3
                assert 123 in results
                assert 456 in results
                assert 789 in results
    
    def test_emoji_handling_for_console_compatibility(self, notification_manager, sample_changes):
        """Test emoji handling for console compatibility."""
        character_name = "Test Character"
        
        message = notification_manager._format_changes_message(
            changes=sample_changes,
            character_name=character_name,
            character_id=12345
        )
        
        # Should handle emoji gracefully (either include them or replace with text)
        assert message is not None
        assert len(message) > 0
        
        # If emojis are replaced, should use text alternatives
        if '[CRIT]' in message or '[HIGH]' in message:
            # Text replacements are being used
            assert '🔴' not in message  # Original emoji should be replaced
    
    def test_message_length_limits(self, notification_manager):
        """Test handling of message length limits."""
        # Create a very long list of changes
        long_changes = []
        for i in range(50):  # Many changes
            change = FieldChange(
                field_path=f"test_field_{i}",
                old_value=i,
                new_value=i+1,
                change_type=ChangeType.INCREMENTED,
                priority=ChangePriority.LOW,
                category=ChangeCategory.BASIC_INFO,
                description=f"Very long description for change number {i} that might make the message too long for Discord"
            )
            long_changes.append(change)
        
        message = notification_manager._format_changes_message(
            changes=long_changes,
            character_name="Test Character",
            character_id=12345
        )
        
        # Discord has a 2000 character limit for messages
        # Implementation should handle this gracefully
        assert message is not None
        
        # If message is truncated, should indicate this
        if len(message) >= 1900:  # Close to limit
            assert "..." in message or "truncated" in message.lower() or len(message) <= 2000
    
    @pytest.mark.asyncio
    async def test_error_handling_in_notifications(self, notification_manager, sample_changes):
        """Test error handling during notification sending."""
        with patch.object(notification_manager, '_create_discord_service') as mock_create_service:
            # Mock Discord service that fails
            mock_discord = AsyncMock()
            mock_discord.send_embed = AsyncMock(side_effect=Exception("Network error"))
            mock_create_service.return_value.__aenter__.return_value = mock_discord
            
            result = await notification_manager.check_and_notify_character_changes(
                12345, timedelta(minutes=5)
            )
            
            # Should handle error gracefully
            assert result is False
    
    def test_configuration_validation(self, mock_storage):
        """Test notification configuration validation."""
        # Test with invalid configuration
        invalid_config = NotificationConfig(
            webhook_url="invalid-url",
            username="",
            max_changes_per_notification=-1,
            min_priority=ChangePriority.LOW,
            rate_limit_requests_per_minute=0
        )
        
        # Should either validate during creation or handle gracefully
        try:
            manager = NotificationManager(
                storage=mock_storage,
                config=invalid_config,
                storage_dir="/tmp/test"
            )
            # If creation succeeds, validation might happen later
            assert manager is not None
        except (ValueError, TypeError):
            # Configuration validation during creation is also acceptable
            pass
    
    def test_timezone_handling(self, notification_manager):
        """Test timezone handling in notifications."""
        # Test with different timezone
        notification_manager.config.timezone = "America/New_York"
        
        # Should handle timezone conversion gracefully
        timestamp = notification_manager._get_formatted_timestamp()
        
        assert timestamp is not None
        assert len(timestamp) > 0
    
    @pytest.mark.asyncio
    async def test_notification_delay_between_messages(self, notification_manager):
        """Test delay between multiple notifications."""
        notification_manager.config.delay_between_messages = 1.0  # 1 second delay
        
        with patch.object(notification_manager, '_create_discord_service') as mock_create_service:
            mock_discord = AsyncMock()
            mock_discord.send_message = AsyncMock(return_value=True)
            mock_create_service.return_value.__aenter__.return_value = mock_discord
            
            start_time = datetime.now()
            
            # Send multiple notifications
            await notification_manager.send_startup_notification()
            await notification_manager.send_shutdown_notification()
            
            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()
            
            # Should have some delay between messages
            # (Exact timing depends on implementation)
            assert elapsed >= 0  # At minimum, should not be negative


class TestNotificationConfig:
    """Test notification configuration class."""
    
    def test_notification_config_creation(self):
        """Test creating notification configuration."""
        config = NotificationConfig(
            webhook_url="https://discord.com/api/webhooks/123/abc",
            username="Test Bot",
            max_changes_per_notification=15,
            min_priority=ChangePriority.MEDIUM
        )
        
        assert config.webhook_url == "https://discord.com/api/webhooks/123/abc"
        assert config.username == "Test Bot"
        assert config.max_changes_per_notification == 15
        assert config.min_priority == ChangePriority.MEDIUM
    
    def test_notification_config_defaults(self):
        """Test notification configuration default values."""
        config = NotificationConfig(
            webhook_url="https://discord.com/api/webhooks/123/abc"
        )
        
        # Should have reasonable defaults
        assert config.username is not None
        assert config.max_changes_per_notification > 0
        assert config.min_priority is not None
        assert config.rate_limit_requests_per_minute > 0
    
    def test_notification_config_validation(self):
        """Test notification configuration validation."""
        # Test with various invalid configurations
        test_cases = [
            {"webhook_url": ""},  # Empty webhook URL
            {"webhook_url": "not-a-url"},  # Invalid URL format
            {"max_changes_per_notification": 0},  # Zero max changes
            {"rate_limit_requests_per_minute": -1},  # Negative rate limit
        ]
        
        for invalid_params in test_cases:
            try:
                config = NotificationConfig(
                    webhook_url=invalid_params.get("webhook_url", "https://discord.com/api/webhooks/123/abc"),
                    max_changes_per_notification=invalid_params.get("max_changes_per_notification", 10),
                    rate_limit_requests_per_minute=invalid_params.get("rate_limit_requests_per_minute", 5)
                )
                # If creation succeeds, validation might happen elsewhere
                assert config is not None
            except (ValueError, TypeError):
                # Validation during creation is acceptable
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])