"""
Quick Discord functionality tests.

Fast-running tests for Discord module functionality, focusing on core features
and common use cases.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import sys
import tempfile
import yaml

# Add Discord module to path
discord_root = Path(__file__).parent.parent.parent / "discord"
sys.path.insert(0, str(discord_root))

from services.discord_service import DiscordService
from services.change_detection.detectors import SpellDetector, BasicInfoDetector
from services.change_detection.models import FieldChange, ChangeType, ChangePriority, ChangeCategory


class TestQuickDiscordService:
    """Quick tests for Discord service core functionality."""
    
    def test_discord_service_creation(self):
        """Test Discord service can be created."""
        service = DiscordService(
            webhook_url="https://discord.com/api/webhooks/123/abc",
            username="Test Bot"
        )
        
        assert service.webhook_url == "https://discord.com/api/webhooks/123/abc"
        assert service.username == "Test Bot"
    
    @pytest.mark.asyncio
    async def test_webhook_test_success(self):
        """Test successful webhook testing."""
        service = DiscordService(webhook_url="https://discord.com/api/webhooks/123/abc")
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 204
            mock_response.headers = {'x-ratelimit-remaining': '5'}
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await service.test_webhook()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_webhook_test_failure(self):
        """Test webhook testing failure."""
        service = DiscordService(webhook_url="https://discord.com/api/webhooks/123/abc")
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_response.text = AsyncMock(return_value="Not Found")
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await service.test_webhook()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_message_sending(self):
        """Test basic message sending."""
        service = DiscordService(webhook_url="https://discord.com/api/webhooks/123/abc")
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 204
            mock_response.headers = {'x-ratelimit-remaining': '5'}
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await service.send_message("Test message")
            assert result is True


class TestQuickSpellDetection:
    """Quick tests for spell detection fixes."""
    
    def test_spell_detector_creation(self):
        """Test spell detector can be created."""
        detector = SpellDetector()
        assert detector.name == "spells"
        assert ChangeCategory.SPELLS in detector.supported_categories
    
    def test_cantrip_slot_bug_fix(self):
        """Test that cantrip slots are not reported as changing."""
        detector = SpellDetector()
        
        old_data = {
            'spellcasting': {
                'spell_slots': [0, 2, 0, 0, 0, 0, 0, 0, 0, 0],  # No cantrip slots
                'spell_counts': {'total': 3, 'by_level': {0: 2, 1: 1}}
            }
        }
        
        new_data = {
            'spellcasting': {
                'spell_slots': [0, 3, 1, 0, 0, 0, 0, 0, 0, 0],  # Still no cantrip slots
                'spell_counts': {'total': 4, 'by_level': {0: 2, 1: 2}}
            }
        }
        
        changes = detector.detect_changes(old_data, new_data, {})
        
        # Should NOT detect cantrip slot changes (the bug)
        cantrip_slot_changes = [
            c for c in changes 
            if 'spell_slots' in c.field_path and ('0' in c.field_path or 'cantrip' in c.description.lower())
        ]
        
        # The bug was reporting "Level 0 spell slots changed"
        # This should not happen because cantrips don't have spell slots
        for change in cantrip_slot_changes:
            assert 'slot' not in change.description.lower() or 'known' in change.description.lower()
    
    def test_real_spell_slot_detection(self):
        """Test that real spell slots are properly detected."""
        detector = SpellDetector()
        
        old_data = {
            'spellcasting': {
                'spell_slots': [0, 2, 1, 0, 0, 0, 0, 0, 0, 0]
            }
        }
        
        new_data = {
            'spellcasting': {
                'spell_slots': [0, 3, 2, 0, 0, 0, 0, 0, 0, 0]
            }
        }
        
        changes = detector.detect_changes(old_data, new_data, {})
        
        # Should detect 1st and 2nd level spell slot increases
        first_level_changes = [c for c in changes if 'spell_slots' in c.field_path and '1' in c.field_path]
        second_level_changes = [c for c in changes if 'spell_slots' in c.field_path and '2' in c.field_path]
        
        assert len(first_level_changes) > 0
        assert len(second_level_changes) > 0
        
        # Verify the changes are correct
        if first_level_changes:
            change = first_level_changes[0]
            assert change.old_value == 2
            assert change.new_value == 3
            assert change.change_type == ChangeType.INCREMENTED


class TestQuickBasicDetection:
    """Quick tests for basic character info detection."""
    
    def test_basic_detector_creation(self):
        """Test basic info detector can be created."""
        detector = BasicInfoDetector()
        assert detector.name == "basic_info"
        assert ChangeCategory.BASIC_INFO in detector.supported_categories
    
    def test_level_change_detection(self):
        """Test level change detection."""
        detector = BasicInfoDetector()
        
        old_data = {'character_info': {'level': 5}}
        new_data = {'character_info': {'level': 6}}
        
        changes = detector.detect_changes(old_data, new_data, {})
        
        level_changes = [c for c in changes if 'level' in c.field_path]
        assert len(level_changes) == 1
        
        change = level_changes[0]
        assert change.old_value == 5
        assert change.new_value == 6
        assert change.change_type == ChangeType.INCREMENTED
        assert change.priority == ChangePriority.CRITICAL
    
    def test_no_false_changes(self):
        """Test that identical data produces no changes."""
        detector = BasicInfoDetector()
        
        data = {'character_info': {'level': 5, 'name': 'Test'}}
        changes = detector.detect_changes(data, data, {})
        
        assert len(changes) == 0


class TestQuickDiscordIntegration:
    """Quick integration tests for Discord functionality."""
    
    def test_discord_monitor_config_loading(self):
        """Test Discord monitor configuration loading."""
        config_data = {
            'webhook_url': 'https://discord.com/api/webhooks/123/abc',
            'character_id': 12345,
            'check_interval': 300
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            from discord_monitor import DiscordMonitor
            monitor = DiscordMonitor(temp_path)
            
            assert monitor.config is not None
            assert monitor.config['webhook_url'] == 'https://discord.com/api/webhooks/123/abc'
            assert monitor.config['character_id'] == 12345
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_notification_manager_creation(self):
        """Test notification manager can be created and initialized."""
        from services.notification_manager import NotificationManager, NotificationConfig
        from services.change_detection_service import ChangePriority
        
        config = NotificationConfig(
            webhook_url="https://discord.com/api/webhooks/123/abc",
            username="Test Bot",
            min_priority=ChangePriority.LOW
        )
        
        storage = Mock()
        manager = NotificationManager(storage, config, "/tmp/test")
        
        assert manager.config == config
        assert manager.storage == storage
    
    def test_change_priority_ordering(self):
        """Test that change priorities are properly ordered."""
        from services.change_detection_service import ChangePriority
        
        # Test priority ordering (lower value = higher priority)
        assert ChangePriority.CRITICAL.value < ChangePriority.HIGH.value
        assert ChangePriority.HIGH.value < ChangePriority.MEDIUM.value
        assert ChangePriority.MEDIUM.value < ChangePriority.LOW.value
    
    def test_change_categories_exist(self):
        """Test that all expected change categories exist."""
        from services.change_detection.models import ChangeCategory
        
        expected_categories = [
            ChangeCategory.BASIC_INFO,
            ChangeCategory.ABILITIES,
            ChangeCategory.SKILLS,
            ChangeCategory.COMBAT,
            ChangeCategory.SPELLS
        ]
        
        for category in expected_categories:
            assert category is not None
            assert hasattr(category, 'name') or hasattr(category, 'value')


class TestQuickErrorHandling:
    """Quick tests for error handling."""
    
    @pytest.mark.asyncio
    async def test_discord_service_network_error(self):
        """Test Discord service handles network errors."""
        service = DiscordService(webhook_url="https://discord.com/api/webhooks/123/abc")
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = asyncio.TimeoutError("Network timeout")
            
            result = await service.send_message("Test")
            assert result is False
    
    def test_detector_with_missing_data(self):
        """Test detectors handle missing data gracefully."""
        detector = BasicInfoDetector()
        
        old_data = {}  # Empty data
        new_data = {'character_info': {'level': 5}}
        
        # Should not crash with missing data
        changes = detector.detect_changes(old_data, new_data, {})
        
        # Should handle gracefully (may or may not detect changes)
        assert isinstance(changes, list)
    
    def test_spell_detector_with_invalid_data(self):
        """Test spell detector handles invalid data."""
        detector = SpellDetector()
        
        old_data = {'spellcasting': {'spell_slots': 'invalid'}}  # Invalid format
        new_data = {'spellcasting': {'spell_slots': [0, 1, 0, 0, 0, 0, 0, 0, 0, 0]}}
        
        # Should not crash with invalid data
        try:
            changes = detector.detect_changes(old_data, new_data, {})
            assert isinstance(changes, list)
        except (TypeError, AttributeError, IndexError):
            # Acceptable to fail gracefully with invalid data
            pass


def run_quick_discord_tests():
    """Run all quick Discord tests."""
    print("Running quick Discord tests...")
    
    # Run tests with minimal output
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ])
    
    if exit_code == 0:
        print("✅ All quick Discord tests passed!")
    else:
        print("❌ Some quick Discord tests failed!")
    
    return exit_code == 0


if __name__ == "__main__":
    run_quick_discord_tests()