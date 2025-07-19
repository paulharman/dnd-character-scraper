#!/usr/bin/env python3
"""
Webhook Manager for Discord integration.

Provides comprehensive webhook validation, testing, and management
capabilities with detailed error handling and troubleshooting guidance.
"""

import asyncio
import aiohttp
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse
import json

logger = logging.getLogger(__name__)


class WebhookErrorType(Enum):
    """Types of webhook errors for classification."""
    INVALID_URL = "invalid_url"
    WEBHOOK_NOT_FOUND = "webhook_not_found"
    PERMISSION_ERROR = "permission_error"
    RATE_LIMITED = "rate_limited"
    NETWORK_ERROR = "network_error"
    SERVER_ERROR = "server_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class WebhookInfo:
    """Information about a Discord webhook."""
    id: str
    name: str
    channel_id: str
    guild_id: str
    avatar: Optional[str] = None
    token: Optional[str] = None
    url: Optional[str] = None
    
    def __post_init__(self):
        """Mask sensitive information for logging."""
        if self.token and len(self.token) > 8:
            self.token_masked = f"{self.token[:4]}...{self.token[-4:]}"
        else:
            self.token_masked = "***"


@dataclass
class WebhookValidationResult:
    """Result of webhook validation."""
    is_valid: bool
    webhook_info: Optional[WebhookInfo] = None
    error_type: Optional[WebhookErrorType] = None
    error_message: Optional[str] = None
    troubleshooting_steps: List[str] = None
    
    def __post_init__(self):
        if self.troubleshooting_steps is None:
            self.troubleshooting_steps = []


class WebhookManager:
    """
    Comprehensive webhook management and validation.
    
    Features:
    - URL format validation
    - Connectivity testing without sending notifications
    - Webhook information retrieval
    - Error classification and troubleshooting
    - Rate limit handling
    """
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.session = None
        
        # Discord webhook URL pattern
        self.webhook_url_pattern = re.compile(
            r'https://discord(?:app)?\.com/api/webhooks/(\d+)/([a-zA-Z0-9_-]+)'
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                'User-Agent': 'D&D-Character-Scraper/6.0.0'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def validate_webhook_url_format(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Discord webhook URL format.
        
        Args:
            url: Webhook URL to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url or not isinstance(url, str):
            return False, "Webhook URL is empty or not a string"
        
        url = url.strip()
        
        # Check for environment variable patterns (these are valid)
        env_var_pattern = re.compile(r'\$\{([^}]+)\}|%([^%]+)%')
        if env_var_pattern.search(url):
            return True, None  # Environment variables are valid
        
        if not url.startswith('https://'):
            return False, "Webhook URL must use HTTPS"
        
        if not self.webhook_url_pattern.match(url):
            return False, "Invalid Discord webhook URL format. Expected: https://discord.com/api/webhooks/ID/TOKEN"
        
        # Check for common mistakes
        if 'discordapp.com' in url and 'discord.com' not in url:
            return False, "Use discord.com instead of discordapp.com for webhook URLs"
        
        return True, None
    
    def extract_webhook_components(self, url: str) -> Optional[Tuple[str, str]]:
        """
        Extract webhook ID and token from URL.
        
        Args:
            url: Discord webhook URL
            
        Returns:
            Tuple of (webhook_id, token) or None if invalid
        """
        match = self.webhook_url_pattern.match(url.strip())
        if match:
            return match.group(1), match.group(2)
        return None
    
    async def get_webhook_info(self, url: str) -> WebhookValidationResult:
        """
        Get detailed information about a webhook.
        
        Args:
            url: Discord webhook URL
            
        Returns:
            WebhookValidationResult with webhook information
        """
        if not self.session:
            raise RuntimeError("WebhookManager not initialized. Use async context manager.")
        
        # Validate URL format first
        is_valid_format, format_error = self.validate_webhook_url_format(url)
        if not is_valid_format:
            return WebhookValidationResult(
                is_valid=False,
                error_type=WebhookErrorType.INVALID_URL,
                error_message=format_error,
                troubleshooting_steps=self._get_url_format_troubleshooting()
            )
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    webhook_data = await response.json()
                    
                    webhook_info = WebhookInfo(
                        id=webhook_data.get('id', ''),
                        name=webhook_data.get('name', 'Unknown'),
                        channel_id=webhook_data.get('channel_id', ''),
                        guild_id=webhook_data.get('guild_id', ''),
                        avatar=webhook_data.get('avatar'),
                        url=url
                    )
                    
                    return WebhookValidationResult(
                        is_valid=True,
                        webhook_info=webhook_info
                    )
                
                elif response.status == 404:
                    return WebhookValidationResult(
                        is_valid=False,
                        error_type=WebhookErrorType.WEBHOOK_NOT_FOUND,
                        error_message="Webhook not found (404). The webhook may have been deleted or the URL is incorrect.",
                        troubleshooting_steps=self._get_not_found_troubleshooting()
                    )
                
                elif response.status == 403:
                    return WebhookValidationResult(
                        is_valid=False,
                        error_type=WebhookErrorType.PERMISSION_ERROR,
                        error_message="Permission denied (403). The webhook token may be invalid.",
                        troubleshooting_steps=self._get_permission_troubleshooting()
                    )
                
                elif response.status == 429:
                    retry_after = response.headers.get('Retry-After', 'unknown')
                    return WebhookValidationResult(
                        is_valid=False,
                        error_type=WebhookErrorType.RATE_LIMITED,
                        error_message=f"Rate limited (429). Retry after {retry_after} seconds.",
                        troubleshooting_steps=self._get_rate_limit_troubleshooting()
                    )
                
                elif 500 <= response.status < 600:
                    return WebhookValidationResult(
                        is_valid=False,
                        error_type=WebhookErrorType.SERVER_ERROR,
                        error_message=f"Discord server error ({response.status}). This is usually temporary.",
                        troubleshooting_steps=self._get_server_error_troubleshooting()
                    )
                
                else:
                    error_text = await response.text()
                    return WebhookValidationResult(
                        is_valid=False,
                        error_type=WebhookErrorType.UNKNOWN_ERROR,
                        error_message=f"Unexpected response ({response.status}): {error_text}",
                        troubleshooting_steps=self._get_generic_troubleshooting()
                    )
        
        except asyncio.TimeoutError:
            return WebhookValidationResult(
                is_valid=False,
                error_type=WebhookErrorType.NETWORK_ERROR,
                error_message="Request timed out. Check your internet connection.",
                troubleshooting_steps=self._get_network_troubleshooting()
            )
        
        except aiohttp.ClientError as e:
            return WebhookValidationResult(
                is_valid=False,
                error_type=WebhookErrorType.NETWORK_ERROR,
                error_message=f"Network error: {str(e)}",
                troubleshooting_steps=self._get_network_troubleshooting()
            )
        
        except Exception as e:
            return WebhookValidationResult(
                is_valid=False,
                error_type=WebhookErrorType.UNKNOWN_ERROR,
                error_message=f"Unexpected error: {str(e)}",
                troubleshooting_steps=self._get_generic_troubleshooting()
            )
    
    async def test_webhook_connectivity(self, url: str, send_test_message: bool = False) -> WebhookValidationResult:
        """
        Test webhook connectivity without sending a notification.
        
        Args:
            url: Discord webhook URL
            send_test_message: If True, sends a test message. If False, only validates.
            
        Returns:
            WebhookValidationResult with test results
        """
        # First get webhook info (this tests connectivity)
        validation_result = await self.get_webhook_info(url)
        
        if not validation_result.is_valid:
            return validation_result
        
        # If requested, send a test message
        if send_test_message:
            test_message = self.create_test_message()
            
            try:
                async with self.session.post(url, json=test_message) as response:
                    if response.status == 204:
                        logger.info("Test message sent successfully")
                        return WebhookValidationResult(
                            is_valid=True,
                            webhook_info=validation_result.webhook_info
                        )
                    else:
                        error_text = await response.text()
                        return WebhookValidationResult(
                            is_valid=False,
                            error_type=WebhookErrorType.UNKNOWN_ERROR,
                            error_message=f"Failed to send test message ({response.status}): {error_text}",
                            troubleshooting_steps=self._get_message_send_troubleshooting()
                        )
            
            except Exception as e:
                return WebhookValidationResult(
                    is_valid=False,
                    error_type=WebhookErrorType.NETWORK_ERROR,
                    error_message=f"Error sending test message: {str(e)}",
                    troubleshooting_steps=self._get_network_troubleshooting()
                )
        
        return validation_result
    
    def create_test_message(self) -> Dict[str, Any]:
        """
        Create a test message for webhook validation.
        
        Returns:
            Dictionary representing a Discord message
        """
        return {
            "username": "D&D Beyond Monitor",
            "embeds": [{
                "title": "🧙‍♂️ Webhook Test",
                "description": "This is a test message to verify webhook connectivity.",
                "color": 0x00FF00,  # Green
                "footer": {
                    "text": "Test completed successfully"
                },
                "timestamp": "2025-01-01T00:00:00.000Z"
            }]
        }
    
    def _get_url_format_troubleshooting(self) -> List[str]:
        """Get troubleshooting steps for URL format issues."""
        return [
            "1. Ensure the URL starts with 'https://'",
            "2. Use the format: https://discord.com/api/webhooks/ID/TOKEN",
            "3. Copy the webhook URL directly from Discord server settings",
            "4. Make sure there are no extra spaces or characters",
            "5. Use discord.com, not discordapp.com"
        ]
    
    def _get_not_found_troubleshooting(self) -> List[str]:
        """Get troubleshooting steps for webhook not found."""
        return [
            "1. Check if the webhook still exists in Discord server settings",
            "2. Verify the webhook URL is copied correctly",
            "3. The webhook may have been deleted by a server administrator",
            "4. Create a new webhook if the old one was deleted",
            "5. Ensure you have the complete URL including the token"
        ]
    
    def _get_permission_troubleshooting(self) -> List[str]:
        """Get troubleshooting steps for permission errors."""
        return [
            "1. Verify the webhook token in the URL is correct",
            "2. Check if the webhook was regenerated (old token invalid)",
            "3. Ensure the bot/webhook has permission to send messages",
            "4. Try creating a new webhook with fresh permissions",
            "5. Contact server administrator if permissions were changed"
        ]
    
    def _get_rate_limit_troubleshooting(self) -> List[str]:
        """Get troubleshooting steps for rate limiting."""
        return [
            "1. Wait for the specified retry period before testing again",
            "2. Reduce the frequency of webhook calls",
            "3. Implement proper rate limiting in your application",
            "4. Consider using multiple webhooks for high-volume applications",
            "5. Check Discord's rate limit documentation for current limits"
        ]
    
    def _get_server_error_troubleshooting(self) -> List[str]:
        """Get troubleshooting steps for server errors."""
        return [
            "1. Wait a few minutes and try again (Discord server issues are usually temporary)",
            "2. Check Discord's status page: https://discordstatus.com/",
            "3. Try testing with a different webhook if available",
            "4. Monitor Discord's official channels for service announcements",
            "5. Implement retry logic with exponential backoff"
        ]
    
    def _get_network_troubleshooting(self) -> List[str]:
        """Get troubleshooting steps for network errors."""
        return [
            "1. Check your internet connection",
            "2. Verify DNS resolution is working",
            "3. Try accessing Discord in a web browser",
            "4. Check if a firewall is blocking the connection",
            "5. Try from a different network if possible"
        ]
    
    def _get_message_send_troubleshooting(self) -> List[str]:
        """Get troubleshooting steps for message sending issues."""
        return [
            "1. Check if the message content violates Discord's guidelines",
            "2. Ensure the message is not too long (2000 character limit)",
            "3. Verify embed structure is valid",
            "4. Check if the channel still exists",
            "5. Try sending a simpler message format"
        ]
    
    def _get_generic_troubleshooting(self) -> List[str]:
        """Get generic troubleshooting steps."""
        return [
            "1. Double-check the webhook URL is correct",
            "2. Try creating a new webhook",
            "3. Test with a simple Discord bot or webhook tester",
            "4. Check Discord's developer documentation",
            "5. Contact support if the issue persists"
        ]


# Convenience function for quick webhook validation
async def validate_webhook(url: str, test_message: bool = False) -> WebhookValidationResult:
    """
    Quick function to validate a Discord webhook.
    
    Args:
        url: Discord webhook URL
        test_message: Whether to send a test message
        
    Returns:
        WebhookValidationResult with validation results
    """
    async with WebhookManager() as manager:
        return await manager.test_webhook_connectivity(url, test_message)