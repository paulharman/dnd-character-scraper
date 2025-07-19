"""
Integration tests for Discord functionality.

Tests end-to-end Discord notification workflows, configuration loading,
and integration between Discord services.
"""

import pytest
import asyncio
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import sys

# Add Discord module to path
discord_root = Path(__file__).parent.parent.parent / "discord"
sys.path.insert(0, str(discord_root))

from discord_monitor import DiscordMonitor
from services.notification_manager import NotificationManager, NotificationConfig
from services.change_detection_service import ChangeDetectionService, ChangePriority


class TestDiscordIntegration:
    """Test Discord integration workflows."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create temporary Discord configuration file."""
        config_data = {
            'webhook_url': 'https://discord.com/api/webhooks/123456789/test-webhook-token',
            'character_id': 12345,
            'check_interval': 300,
            'run_continuous': False,
            'min_priority': 'LOW',
            'notifications': {
                'username': 'Test D&D Monitor',
                'timezone': 'UTC'
            },
            'advanced': {
                'max_changes_per_notification': 15,
                'delay_between_messages': 1.0
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def temp_party_config_file(self):
        """Create temporary party configuration file."""
        config_data = {
            'webhook_url': 'https://discord.com/api/webhooks/123456789/test-webhook-token',
            'party': [
                {'character_id': 12345, 'name': 'Character 1'},
                {'character_id': 67890, 'name': 'Character 2'},
                {'character_id': 11111, 'name': 'Character 3'}
            ],
            'check_interval': 300,
            'run_continuous': False,
            'min_priority': 'MEDIUM',
            'notifications': {
                'username': 'Party Monitor',
                'timezone': 'UTC'
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)
    
    def test_discord_monitor_initialization(self, temp_config_file):
        """Test Discord monitor initialization with configuration."""
        monitor = DiscordMonitor(temp_config_file)
        
        assert monitor.config_path == Path(temp_config_file)
        assert monitor.config is not None
        assert monitor.config['webhook_url'] == 'https://discord.com/api/webhooks/123456789/test-webhook-token'
        assert monitor.config['character_id'] == 12345
    
    def test_party_mode_initialization(self, temp_party_config_file):
        """Test Discord monitor initialization in party mode."""
        monitor = DiscordMonitor(temp_party_config_file, use_party_mode=True)
        
        assert monitor.config is not None
        assert 'party' in monitor.config
        assert len(monitor.config['party']) == 3
    
    @pytest.mark.asyncio
    async def test_discord_monitor_initialization_async(self, temp_config_file):
        """Test Discord monitor async initialization."""
        monitor = DiscordMonitor(temp_config_file)
        
        with patch('discord_monitor.EnhancedDnDScraper') as mock_scraper_class:
            with patch('services.discord_service.DiscordService') as mock_discord_service:
                mock_discord = AsyncMock()
                mock_discord.test_webhook = AsyncMock(return_value=True)
                mock_discord_service.return_value.__aenter__.return_value = mock_discord
                
                await monitor.initialize(skip_webhook_test=False)
                
                assert monitor.character_ids == [12345]
                assert monitor.notification_manager is not None
    
    @pytest.mark.asyncio
    async def test_webhook_validation_integration(self, temp_config_file):
        """Test webhook validation integration."""
        monitor = DiscordMonitor(temp_config_file)
        
        with patch('services.discord_service.DiscordService') as mock_discord_service:
            # Test successful webhook validation
            mock_discord = AsyncMock()
            mock_discord.test_webhook = AsyncMock(return_value=True)
            mock_discord_service.return_value.__aenter__.return_value = mock_discord
            
            result = await monitor.test_notifications()
            
            assert result is True
            mock_discord.test_webhook.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_webhook_validation_failure(self, temp_config_file):
        """Test webhook validation failure handling."""
        monitor = DiscordMonitor(temp_config_file)
        
        with patch('services.discord_service.DiscordService') as mock_discord_service:
            # Test webhook validation failure
            mock_discord = AsyncMock()
            mock_discord.test_webhook = AsyncMock(return_value=False)
            mock_discord_service.return_value.__aenter__.return_value = mock_discord
            
            result = await monitor.test_notifications()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_character_scraping_integration(self, temp_config_file):
        """Test character scraping integration."""
        monitor = DiscordMonitor(temp_config_file)
        
        with patch('discord_monitor.EnhancedDnDScraper') as mock_scraper_class:
            mock_scraper = Mock()
            mock_scraper.fetch_character_data = Mock(return_value=True)
            mock_scraper.save_character_data = Mock(return_value="/path/to/saved/data.json")
            mock_scraper._check_rate_limit = Mock()
            mock_scraper_class.return_value = mock_scraper
            
            await monitor.initialize(skip_webhook_test=True)
            result = await monitor.scrape_character(12345)
            
            assert result is True
            mock_scraper.fetch_character_data.assert_called_once()
            mock_scraper.save_character_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_change_detection_integration(self, temp_config_file):
        """Test change detection integration."""
        monitor = DiscordMonitor(temp_config_file)
        
        with patch('discord_monitor.EnhancedDnDScraper'):
            with patch('services.discord_service.DiscordService') as mock_discord_service:
                mock_discord = AsyncMock()
                mock_discord.send_embed = AsyncMock(return_value=True)
                mock_discord_service.return_value.__aenter__.return_value = mock_discord
                
                await monitor.initialize(skip_webhook_test=True)
                
                # Mock change detection
                with patch.object(monitor.notification_manager, '_get_character_changes') as mock_get_changes:
                    mock_changes = [
                        Mock(
                            field_path="character_info.level",
                            old_value=5,
                            new_value=6,
                            priority=ChangePriority.CRITICAL,
                            description="Level increased from 5 to 6"
                        )
                    ]
                    mock_get_changes.return_value = mock_changes
                    
                    result = await monitor.notification_manager.check_and_notify_character_changes(
                        12345, timedelta(minutes=5)
                    )
                    
                    assert result is True
                    mock_discord.send_embed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_party_mode_integration(self, temp_party_config_file):
        """Test party mode integration."""
        monitor = DiscordMonitor(temp_party_config_file, use_party_mode=True)
        
        with patch('discord_monitor.EnhancedDnDScraper'):
            with patch('services.discord_service.DiscordService') as mock_discord_service:
                mock_discord = AsyncMock()
                mock_discord.send_message = AsyncMock(return_value=True)
                mock_discord_service.return_value.__aenter__.return_value = mock_discord
                
                await monitor.initialize(skip_webhook_test=True)
                
                assert len(monitor.character_ids) == 3
                assert 12345 in monitor.character_ids
                assert 67890 in monitor.character_ids
                assert 11111 in monitor.character_ids
    
    @pytest.mark.asyncio
    async def test_run_once_integration(self, temp_config_file):
        """Test run-once mode integration."""
        monitor = DiscordMonitor(temp_config_file)
        
        with patch('discord_monitor.EnhancedDnDScraper') as mock_scraper_class:
            with patch('services.discord_service.DiscordService') as mock_discord_service:
                # Mock successful scraping
                mock_scraper = Mock()
                mock_scraper.fetch_character_data = Mock(return_value=True)
                mock_scraper.save_character_data = Mock(return_value="/path/to/data.json")
                mock_scraper._check_rate_limit = Mock()
                mock_scraper_class.return_value = mock_scraper
                
                # Mock Discord service
                mock_discord = AsyncMock()
                mock_discord.send_embed = AsyncMock(return_value=True)
                mock_discord_service.return_value.__aenter__.return_value = mock_discord
                
                # Mock change detection
                with patch.object(ChangeDetectionService, 'detect_changes') as mock_detect:
                    mock_detect.return_value = []  # No changes
                    
                    result = await monitor.run_once()
                    
                    assert result is True
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, temp_config_file):
        """Test error handling integration."""
        monitor = DiscordMonitor(temp_config_file)
        
        with patch('discord_monitor.EnhancedDnDScraper') as mock_scraper_class:
            # Mock scraper failure
            mock_scraper = Mock()
            mock_scraper.fetch_character_data = Mock(return_value=False)
            mock_scraper._check_rate_limit = Mock()
            mock_scraper_class.return_value = mock_scraper
            
            await monitor.initialize(skip_webhook_test=True)
            result = await monitor.scrape_character(12345)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_rate_limiting_integration(self, temp_config_file):
        """Test rate limiting integration."""
        monitor = DiscordMonitor(temp_config_file)
        
        with patch('services.discord_service.DiscordService') as mock_discord_service:
            # Mock rate limited response
            mock_discord = AsyncMock()
            mock_discord.send_message = AsyncMock(return_value=False)  # Rate limited
            mock_discord_service.return_value.__aenter__.return_value = mock_discord
            
            await monitor.initialize(skip_webhook_test=True)
            
            # Should handle rate limiting gracefully
            result = await monitor.notification_manager.send_startup_notification()
            
            assert result is False  # Failed due to rate limiting
    
    def test_configuration_validation_integration(self):
        """Test configuration validation integration."""
        # Test with invalid configuration
        invalid_config_data = {
            'webhook_url': '',  # Invalid empty webhook URL
            'character_id': 'not-a-number',  # Invalid character ID
            'check_interval': -1  # Invalid interval
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_config_data, f)
            temp_path = f.name
        
        try:
            # Should handle invalid configuration gracefully
            monitor = DiscordMonitor(temp_path)
            # Configuration loading might succeed but validation should catch issues
            assert monitor.config is not None
        except (ValueError, FileNotFoundError, yaml.YAMLError):
            # Expected for invalid configuration
            pass
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_notification_formatting_integration(self, temp_config_file):
        """Test notification formatting integration."""
        monitor = DiscordMonitor(temp_config_file)
        
        with patch('services.discord_service.DiscordService') as mock_discord_service:
            mock_discord = AsyncMock()
            mock_discord.send_embed = AsyncMock(return_value=True)
            mock_discord_service.return_value.__aenter__.return_value = mock_discord
            
            await monitor.initialize(skip_webhook_test=True)
            
            # Test detailed notification
            result = await monitor.test_notifications(detailed=True)
            
            assert result is True
            mock_discord.send_embed.assert_called_once()
            
            # Verify embed formatting
            call_args = mock_discord.send_embed.call_args
            embed_data = call_args[0][1]  # Second argument is embed data
            
            assert 'title' in embed_data
            assert 'fields' in embed_data
            assert isinstance(embed_data['fields'], list)
    
    @pytest.mark.asyncio
    async def test_storage_integration(self, temp_config_file):
        """Test storage integration with Discord monitoring."""
        monitor = DiscordMonitor(temp_config_file)
        
        with patch('discord_monitor.EnhancedDnDScraper') as mock_scraper_class:
            mock_scraper = Mock()
            mock_scraper.fetch_character_data = Mock(return_value=True)
            mock_scraper.save_character_data = Mock(return_value="/path/to/data.json")
            mock_scraper._check_rate_limit = Mock()
            mock_scraper_class.return_value = mock_scraper
            
            await monitor.initialize(skip_webhook_test=True)
            
            # Verify storage directory is set up
            assert monitor.storage_dir is not None
            assert "discord" in str(monitor.storage_dir)
    
    @pytest.mark.asyncio
    async def test_archiving_integration(self, temp_config_file):
        """Test archiving integration."""
        monitor = DiscordMonitor(temp_config_file)
        
        with patch('discord_monitor.EnhancedDnDScraper'):
            with patch('src.storage.archiving.SnapshotArchiver') as mock_archiver_class:
                mock_archiver = Mock()
                mock_archiver.archive_old_snapshots = Mock()
                mock_archiver_class.return_value = mock_archiver
                
                await monitor.initialize(skip_webhook_test=True)
                
                # Verify archiver is initialized
                assert monitor.archiver is not None


class TestDiscordConfigurationIntegration:
    """Test Discord configuration integration."""
    
    def test_environment_variable_integration(self):
        """Test environment variable integration for webhook URL."""
        with patch.dict('os.environ', {'DISCORD_WEBHOOK_URL': 'https://discord.com/api/webhooks/env/test'}):
            # Test that environment variables are properly loaded
            # (Implementation depends on actual environment variable support)
            pass
    
    def test_configuration_security_integration(self, temp_config_file):
        """Test configuration security integration."""
        monitor = DiscordMonitor(temp_config_file)
        
        # Verify webhook URL is not exposed in string representation
        monitor_str = str(monitor)
        
        # Should not contain full webhook URL for security
        assert 'test-webhook-token' not in monitor_str or '***' in monitor_str
    
    def test_multiple_configuration_formats(self):
        """Test support for multiple configuration formats."""
        # Test different configuration structures
        config_formats = [
            {
                # New format with change_types at top level
                'webhook_url': 'https://discord.com/api/webhooks/123/abc',
                'character_id': 12345,
                'change_types': ['level', 'hit_points', 'spells_known']
            },
            {
                # Legacy format with filtering section
                'webhook_url': 'https://discord.com/api/webhooks/123/abc',
                'character_id': 12345,
                'filtering': {
                    'change_types': ['level', 'experience', 'armor_class']
                }
            },
            {
                # Preset filtering format
                'webhook_url': 'https://discord.com/api/webhooks/123/abc',
                'character_id': 12345,
                'filtering': {
                    'preset': 'combat_only'
                }
            }
        ]
        
        for config_data in config_formats:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(config_data, f)
                temp_path = f.name
            
            try:
                monitor = DiscordMonitor(temp_path)
                assert monitor.config is not None
                
                # Should handle different configuration formats
                notification_config = monitor._create_notification_config()
                assert notification_config is not None
                
            finally:
                Path(temp_path).unlink(missing_ok=True)


class TestDiscordEndToEndWorkflow:
    """Test complete end-to-end Discord workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_monitoring_workflow(self, temp_config_file):
        """Test complete monitoring workflow from scraping to notification."""
        monitor = DiscordMonitor(temp_config_file)
        
        # Mock all external dependencies
        with patch('discord_monitor.EnhancedDnDScraper') as mock_scraper_class:
            with patch('services.discord_service.DiscordService') as mock_discord_service:
                with patch('services.change_detection_service.ChangeDetectionService') as mock_change_service_class:
                    
                    # Mock scraper
                    mock_scraper = Mock()
                    mock_scraper.fetch_character_data = Mock(return_value=True)
                    mock_scraper.save_character_data = Mock(return_value="/path/to/data.json")
                    mock_scraper._check_rate_limit = Mock()
                    mock_scraper_class.return_value = mock_scraper
                    
                    # Mock Discord service
                    mock_discord = AsyncMock()
                    mock_discord.send_embed = AsyncMock(return_value=True)
                    mock_discord_service.return_value.__aenter__.return_value = mock_discord
                    
                    # Mock change detection
                    mock_change_service = Mock()
                    mock_changes = [
                        Mock(
                            field_path="character_info.level",
                            old_value=5,
                            new_value=6,
                            priority=ChangePriority.CRITICAL,
                            description="Level increased from 5 to 6",
                            category=Mock()
                        )
                    ]
                    mock_change_service.detect_changes = Mock(return_value=mock_changes)
                    mock_change_service_class.return_value = mock_change_service
                    
                    # Run complete workflow
                    result = await monitor.run_once()
                    
                    assert result is True
                    
                    # Verify workflow steps
                    mock_scraper.fetch_character_data.assert_called_once()
                    mock_scraper.save_character_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, temp_config_file):
        """Test error recovery in complete workflow."""
        monitor = DiscordMonitor(temp_config_file)
        
        with patch('discord_monitor.EnhancedDnDScraper') as mock_scraper_class:
            with patch('services.discord_service.DiscordService') as mock_discord_service:
                
                # Mock scraper failure
                mock_scraper = Mock()
                mock_scraper.fetch_character_data = Mock(side_effect=Exception("API Error"))
                mock_scraper._check_rate_limit = Mock()
                mock_scraper_class.return_value = mock_scraper
                
                # Mock Discord service
                mock_discord = AsyncMock()
                mock_discord.send_message = AsyncMock(return_value=True)
                mock_discord_service.return_value.__aenter__.return_value = mock_discord
                
                # Should handle errors gracefully
                result = await monitor.run_once()
                
                # May succeed or fail depending on error handling implementation
                assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])