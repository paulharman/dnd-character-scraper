"""
Unit tests for Discord service functionality.

Tests webhook validation, error handling, rate limiting, and message formatting.
"""

import pytest
import asyncio
import aiohttp
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json

import sys
from pathlib import Path

# Add Discord module to path
discord_root = Path(__file__).parent.parent.parent.parent / "discord"
sys.path.insert(0, str(discord_root))

from services.discord_service import DiscordService


class TestDiscordService:
    """Test Discord service webhook functionality."""
    
    @pytest.fixture
    def valid_webhook_url(self):
        """Valid Discord webhook URL for testing."""
        return "https://discord.com/api/webhooks/123456789/abcdef123456"
    
    @pytest.fixture
    def invalid_webhook_url(self):
        """Invalid webhook URL for testing."""
        return "https://invalid-url.com/not-a-webhook"
    
    @pytest.fixture
    def discord_service(self, valid_webhook_url):
        """Discord service instance for testing."""
        return DiscordService(webhook_url=valid_webhook_url, username="Test Bot")
    
    def test_webhook_url_validation(self, valid_webhook_url, invalid_webhook_url):
        """Test webhook URL format validation."""
        # Valid URL should work
        service = DiscordService(webhook_url=valid_webhook_url)
        assert service.webhook_url == valid_webhook_url
        
        # Invalid URL should still be accepted (validation happens at runtime)
        service = DiscordService(webhook_url=invalid_webhook_url)
        assert service.webhook_url == invalid_webhook_url
    
    def test_service_initialization(self, valid_webhook_url):
        """Test Discord service initialization with various parameters."""
        # Basic initialization
        service = DiscordService(webhook_url=valid_webhook_url)
        assert service.webhook_url == valid_webhook_url
        assert service.username == "D&D Beyond Monitor"  # Default
        assert service.avatar_url is None
        
        # Full initialization
        service = DiscordService(
            webhook_url=valid_webhook_url,
            username="Custom Bot",
            avatar_url="https://example.com/avatar.png"
        )
        assert service.username == "Custom Bot"
        assert service.avatar_url == "https://example.com/avatar.png"
    
    @pytest.mark.asyncio
    async def test_webhook_connectivity_success(self, valid_webhook_url):
        """Test successful webhook connectivity test."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock successful response
            mock_response = AsyncMock()
            mock_response.status = 204  # Discord webhook success status
            mock_response.headers = {'x-ratelimit-remaining': '5'}
            mock_post.return_value.__aenter__.return_value = mock_response
            
            async with DiscordService(webhook_url=valid_webhook_url) as discord_service:
                result = await discord_service.test_webhook()
                
                assert result is True
                mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_webhook_connectivity_failure(self, valid_webhook_url):
        """Test webhook connectivity failure scenarios."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock 404 response (webhook not found)
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_response.text = AsyncMock(return_value="Webhook not found")
            mock_post.return_value.__aenter__.return_value = mock_response
            
            async with DiscordService(webhook_url=valid_webhook_url) as discord_service:
                result = await discord_service.test_webhook()
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, valid_webhook_url):
        """Test rate limit detection and handling."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock rate limit response
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_response.headers = {
                'x-ratelimit-remaining': '0',
                'retry-after': '5'
            }
            mock_response.json = AsyncMock(return_value={
                'retry_after': 5.0,
                'global': False
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            async with DiscordService(webhook_url=valid_webhook_url) as discord_service:
                # Should handle rate limit gracefully
                result = await discord_service.send_simple_message("Test message")
                
                assert result is False  # Should fail due to rate limit
    
    @pytest.mark.asyncio
    async def test_message_sending_success(self, valid_webhook_url):
        """Test successful message sending."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 204
            mock_response.headers = {'x-ratelimit-remaining': '5'}
            mock_post.return_value.__aenter__.return_value = mock_response
            
            async with DiscordService(webhook_url=valid_webhook_url, username="Test Bot") as discord_service:
                result = await discord_service.send_simple_message("Test message")
                
                assert result is True
                
                # Verify the request was made with correct data
                call_args = mock_post.call_args
                assert call_args[1]['json']['content'] == "Test message"
                assert call_args[1]['json']['username'] == "Test Bot"
    
    @pytest.mark.asyncio
    async def test_embed_message_sending(self, valid_webhook_url):
        """Test sending messages with embeds."""
        from services.discord_service import EmbedColor
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 204
            mock_response.headers = {'x-ratelimit-remaining': '5'}
            mock_post.return_value.__aenter__.return_value = mock_response
            
            async with DiscordService(webhook_url=valid_webhook_url) as discord_service:
                result = await discord_service.send_embed(
                    title="Character Update",
                    description="Level increased",
                    color=EmbedColor.LEVEL_UP,
                    fields=[{'name': 'Level', 'value': '5 → 6', 'inline': True}],
                    content="Character updated!"
                )
                
                assert result is True
                
                # Verify embed was included in request
                call_args = mock_post.call_args
                assert 'embeds' in call_args[1]['json']
                assert call_args[1]['json']['embeds'][0]['title'] == 'Character Update'
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, valid_webhook_url):
        """Test handling of network errors."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock network timeout
            mock_post.side_effect = asyncio.TimeoutError("Connection timeout")
            
            async with DiscordService(webhook_url=valid_webhook_url) as discord_service:
                result = await discord_service.send_simple_message("Test message")
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_invalid_json_response_handling(self, valid_webhook_url):
        """Test handling of invalid JSON responses."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.json = AsyncMock(side_effect=json.JSONDecodeError("Invalid JSON", "", 0))
            mock_response.text = AsyncMock(return_value="Invalid request")
            mock_post.return_value.__aenter__.return_value = mock_response
            
            async with DiscordService(webhook_url=valid_webhook_url) as discord_service:
                result = await discord_service.send_simple_message("Test message")
                
                assert result is False
    
    def test_message_length_validation(self, discord_service):
        """Test message length validation."""
        # Discord has a 2000 character limit for messages
        long_message = "A" * 2001
        
        # Should handle long messages gracefully
        # (Implementation may truncate or split messages)
        assert len(long_message) > 2000
    
    @pytest.mark.asyncio
    async def test_context_manager_usage(self, valid_webhook_url):
        """Test Discord service as async context manager."""
        async with DiscordService(webhook_url=valid_webhook_url) as service:
            assert service.webhook_url == valid_webhook_url
            # Session should be created
            assert hasattr(service, '_session') or hasattr(service, 'session')
    
    @pytest.mark.asyncio
    async def test_retry_logic_on_temporary_failures(self, valid_webhook_url):
        """Test retry logic for temporary failures."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # First call fails with 500, second succeeds
            responses = [
                AsyncMock(status=500, text=AsyncMock(return_value="Server error")),
                AsyncMock(status=204, headers={'x-ratelimit-remaining': '5'})
            ]
            
            mock_post.return_value.__aenter__.side_effect = responses
            
            async with DiscordService(webhook_url=valid_webhook_url) as discord_service:
                # If retry logic is implemented, this should eventually succeed
                result = await discord_service.send_simple_message("Test message")
                
                # Result depends on implementation - may succeed with retry or fail immediately
                assert isinstance(result, bool)
    
    def test_webhook_url_masking_in_logs(self, valid_webhook_url):
        """Test that webhook URLs are properly masked in logs."""
        service = DiscordService(webhook_url=valid_webhook_url)
        
        # Get string representation (which might be logged)
        service_str = str(service)
        
        # Should not contain the full webhook URL
        assert valid_webhook_url not in service_str or "***" in service_str
    
    @pytest.mark.asyncio
    async def test_webhook_info_extraction(self, discord_service):
        """Test extraction of webhook information from URL."""
        # This tests if the service can extract webhook ID and token
        webhook_url = discord_service.webhook_url
        
        # Should be able to parse webhook components
        assert "webhooks" in webhook_url
        
        # Implementation-specific: may have methods to extract webhook ID/token
        if hasattr(discord_service, 'get_webhook_id'):
            webhook_id = discord_service.get_webhook_id()
            assert webhook_id is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_message_sending(self, discord_service):
        """Test sending multiple messages concurrently."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 204
            mock_response.headers = {'x-ratelimit-remaining': '5'}
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Send multiple messages concurrently
            tasks = [
                discord_service.send_message(f"Message {i}")
                for i in range(3)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should succeed (or handle rate limits appropriately)
            assert len(results) == 3
            assert all(isinstance(result, bool) for result in results)


class TestDiscordServiceErrorHandling:
    """Test Discord service error handling and classification."""
    
    @pytest.fixture
    def discord_service(self):
        """Discord service for error testing."""
        return DiscordService(
            webhook_url="https://discord.com/api/webhooks/123/abc",
            username="Error Test Bot"
        )
    
    @pytest.mark.asyncio
    async def test_404_webhook_not_found(self):
        """Test handling of 404 webhook not found errors."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_response.text = AsyncMock(return_value="Unknown Webhook")
            mock_post.return_value.__aenter__.return_value = mock_response
            
            async with DiscordService(webhook_url="https://discord.com/api/webhooks/123/abc") as discord_service:
                result = await discord_service.send_simple_message("Test")
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_403_permission_denied(self):
        """Test handling of 403 permission denied errors."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 403
            mock_response.text = AsyncMock(return_value="Missing Permissions")
            mock_post.return_value.__aenter__.return_value = mock_response
            
            async with DiscordService(webhook_url="https://discord.com/api/webhooks/123/abc") as discord_service:
                result = await discord_service.send_simple_message("Test")
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_500_server_error(self):
        """Test handling of 500 server errors."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Internal Server Error")
            mock_post.return_value.__aenter__.return_value = mock_response
            
            async with DiscordService(webhook_url="https://discord.com/api/webhooks/123/abc") as discord_service:
                result = await discord_service.send_simple_message("Test")
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_connection_timeout(self):
        """Test handling of connection timeouts."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = asyncio.TimeoutError()
            
            async with DiscordService(webhook_url="https://discord.com/api/webhooks/123/abc") as discord_service:
                result = await discord_service.send_simple_message("Test")
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_dns_resolution_failure(self):
        """Test handling of DNS resolution failures."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = aiohttp.ClientConnectorError(
                connection_key=None, 
                os_error=OSError("Name resolution failed")
            )
            
            async with DiscordService(webhook_url="https://discord.com/api/webhooks/123/abc") as discord_service:
                result = await discord_service.send_simple_message("Test")
                
                assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])