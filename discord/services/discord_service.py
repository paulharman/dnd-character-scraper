#!/usr/bin/env python3
"""
Discord notification service for D&D character updates.

Provides webhook-based Discord notifications with rate limiting,
retry logic, and rich formatting capabilities.
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from .discord_error_handler import DiscordErrorHandler, ErrorHandlingResult
from .webhook_manager import WebhookManager, WebhookValidationResult
from .discord_logger import DiscordLogger, OperationType, LogLevel, timed_operation

logger = logging.getLogger(__name__)

# Discord message limits (from official API docs)
DISCORD_MESSAGE_LIMIT = 2000        # Characters in message content
DISCORD_TOTAL_EMBED_LIMIT = 6000    # Total characters across ALL embeds in message
DISCORD_EMBED_TITLE_LIMIT = 256     # Characters in embed title
DISCORD_EMBED_DESC_LIMIT = 4096     # Characters in embed description
DISCORD_EMBED_FIELD_LIMIT = 1024    # Characters per field value
DISCORD_EMBED_FIELD_NAME_LIMIT = 256 # Characters per field name
DISCORD_EMBED_FIELD_COUNT_LIMIT = 25 # Maximum fields per embed
DISCORD_EMBED_FOOTER_LIMIT = 2048   # Characters in footer text
DISCORD_EMBED_AUTHOR_LIMIT = 256    # Characters in author name
DISCORD_EMBEDS_PER_MESSAGE = 10     # Maximum embeds per webhook message


class EmbedColor(Enum):
    """Discord embed colors for different notification types."""
    LEVEL_UP = 0x00FF00      # Green
    INVENTORY = 0x0099FF     # Blue  
    COMBAT = 0xFF6600        # Orange
    SPELLS = 0x9966FF        # Purple
    ERROR = 0xFF0000         # Red
    INFO = 0x808080          # Gray
    SUCCESS = 0x00FF00       # Green
    WARNING = 0xFFFF00       # Yellow
    
    # Priority-based colors
    PRIORITY_LOW = 0x36393F      # Dark gray (Discord's default embed color)
    PRIORITY_MEDIUM = 0xFFA500   # Orange
    PRIORITY_HIGH = 0xFF4500     # Red-orange  
    PRIORITY_CRITICAL = 0xFF0000 # Red


@dataclass
class DiscordEmbed:
    """Discord embed structure."""
    title: str
    description: Optional[str] = None
    color: Optional[int] = None
    timestamp: Optional[str] = None
    author: Optional[Dict[str, str]] = None
    fields: Optional[List[Dict[str, Any]]] = None
    footer: Optional[Dict[str, str]] = None
    thumbnail: Optional[Dict[str, str]] = None
    image: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class DiscordMessage:
    """Discord webhook message structure."""
    content: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    embeds: Optional[List[DiscordEmbed]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {}
        if self.content:
            data['content'] = self.content
        if self.username:
            data['username'] = self.username
        if self.avatar_url:
            data['avatar_url'] = self.avatar_url
        if self.embeds:
            data['embeds'] = [embed.to_dict() for embed in self.embeds]
        return data


class RateLimiter:
    """Simple rate limiter for Discord webhooks."""
    
    def __init__(self, requests_per_minute: int = 3, burst_limit: int = 1):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.requests = []
        self.last_request = None
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = datetime.now()
        
        # Remove requests older than 1 minute
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < timedelta(minutes=1)]
        
        # Check if we need to wait
        if len(self.requests) >= self.requests_per_minute:
            oldest_request = min(self.requests)
            wait_time = (oldest_request + timedelta(minutes=1) - now).total_seconds()
            if wait_time > 0:
                logger.info(f"Rate limiting: waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
        
        # Check burst limit
        if (self.last_request and 
            now - self.last_request < timedelta(seconds=60 / self.requests_per_minute)):
            wait_time = (60 / self.requests_per_minute) - (now - self.last_request).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        # Record this request
        self.requests.append(now)
        self.last_request = now


class DiscordService:
    """
    Discord notification service with webhook support.
    
    Features:
    - Webhook message sending
    - Rate limiting
    - Retry logic with exponential backoff
    - Rich embed formatting
    - Error handling and logging
    """
    
    def __init__(
        self,
        webhook_url: str,
        username: str = "D&D Beyond Monitor",
        avatar_url: Optional[str] = None,
        rate_limit_requests_per_minute: int = 3,
        rate_limit_burst: int = 1,
        max_retries: int = 3,
        retry_backoff_factor: float = 2.0,
        retry_max_delay: float = 60.0,
        timeout: float = 30.0
    ):
        self.webhook_url = webhook_url
        self.username = username
        self.avatar_url = avatar_url
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor
        self.retry_max_delay = retry_max_delay
        self.timeout = timeout
        
        self.rate_limiter = RateLimiter(rate_limit_requests_per_minute, rate_limit_burst)
        self.session = None
        
        # Initialize enhanced error handling and logging
        self.error_handler = DiscordErrorHandler(
            max_retries=max_retries,
            base_delay=1.0,
            max_delay=retry_max_delay,
            backoff_factor=retry_backoff_factor
        )
        self.discord_logger = DiscordLogger('discord.service')
        
        # Log with masked webhook URL for security
        masked_url = self._mask_webhook_url(webhook_url)
        logger.info(f"Discord service initialized for webhook: {masked_url}")
    
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
    
    async def send_message(self, message: DiscordMessage) -> bool:
        """
        Send a message to Discord webhook.
        
        Args:
            message: Discord message to send
            
        Returns:
            True if successful, False otherwise
        """
        if not self.session:
            raise RuntimeError("Discord service not initialized. Use async context manager.")
        
        # Apply default username and avatar
        if not message.username:
            message.username = self.username
        if not message.avatar_url and self.avatar_url:
            message.avatar_url = self.avatar_url
        
        payload = message.to_dict()
        
        for attempt in range(self.max_retries + 1):
            try:
                # Apply rate limiting
                await self.rate_limiter.wait_if_needed()
                
                async with self.session.post(self.webhook_url, json=payload) as response:
                    if response.status == 204:
                        logger.info(f"Discord message sent successfully (attempt {attempt + 1})")
                        print(f"DEBUG: Successfully sent Discord message (attempt {attempt + 1}, content hash: {hash(str(payload))})")
                        
                        # Record success for error handler and enhanced logging
                        self.error_handler.record_success()
                        self.discord_logger.log_webhook_operation(
                            "send_message",
                            self.webhook_url,
                            True,
                            duration_ms=None
                        )
                        return True
                    else:
                        # Handle error using enhanced error handler
                        error = Exception(f"HTTP {response.status}")
                        error_result = self.error_handler.handle_webhook_error(error, response)
                        
                        logger.error(f"Discord API error: {error_result.user_message}")
                        logger.debug(f"Technical details: {error_result.technical_details}")
                        
                        # Enhanced logging for webhook errors
                        self.discord_logger.log_webhook_operation(
                            "send_message",
                            self.webhook_url,
                            False,
                            error_details={
                                'status_code': response.status,
                                'error_type': error_result.error_type.value,
                                'user_message': error_result.user_message,
                                'attempt': attempt + 1
                            }
                        )
                        
                        # Log rate limiting specifically
                        if response.status == 429:
                            retry_after = float(response.headers.get('Retry-After', 1))
                            self.discord_logger.log_rate_limit_event(
                                retry_after,
                                "send_message"
                            )
                        
                        # Check if we should retry
                        if not error_result.should_retry or attempt >= self.max_retries:
                            if error_result.is_permanent:
                                logger.error("Permanent error - not retrying")
                                logger.info("Troubleshooting steps:")
                                for step in error_result.troubleshooting_steps:
                                    logger.info(f"  - {step}")
                            return False
                        
                        # Wait for retry delay
                        if error_result.retry_delay > 0:
                            logger.info(f"Waiting {error_result.retry_delay} seconds before retry")
                            await asyncio.sleep(error_result.retry_delay)
                        continue
                            
            except Exception as e:
                # Handle exception using enhanced error handler
                error_result = self.error_handler.handle_webhook_error(e)
                
                logger.error(f"Discord request error: {error_result.user_message}")
                logger.debug(f"Technical details: {error_result.technical_details}")
                
                # Enhanced logging for exceptions
                self.discord_logger.log_error_with_context(
                    e,
                    OperationType.MESSAGE_SEND,
                    context={
                        'attempt': attempt + 1,
                        'webhook_masked': self._mask_webhook_url(self.webhook_url),
                        'error_classification': error_result.error_type.value
                    }
                )
                
                # Check if we should retry
                if not error_result.should_retry or attempt >= self.max_retries:
                    if error_result.is_permanent:
                        logger.error("Permanent error - not retrying")
                        logger.info("Troubleshooting steps:")
                        for step in error_result.troubleshooting_steps:
                            logger.info(f"  - {step}")
                    return False
                
                # Calculate backoff delay if not specified
                if error_result.retry_delay == 0:
                    delay = self.error_handler.get_retry_delay(attempt)
                else:
                    delay = error_result.retry_delay
                
                logger.info(f"Retrying Discord request in {delay:.1f} seconds")
                await asyncio.sleep(delay)
        
        logger.error("Failed to send Discord message after all retries")
        return False
    
    async def send_embed(
        self,
        title: str,
        description: Optional[str] = None,
        color: Optional[EmbedColor] = None,
        fields: Optional[List[Dict[str, Any]]] = None,
        footer_text: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        content: Optional[str] = None
    ) -> bool:
        """
        Send a Discord embed message.
        
        Args:
            title: Embed title
            description: Embed description
            color: Embed color
            fields: List of embed fields
            footer_text: Footer text
            thumbnail_url: Thumbnail image URL
            content: Message content (outside embed)
            
        Returns:
            True if successful, False otherwise
        """
        embed = DiscordEmbed(
            title=title,
            description=description,
            color=color.value if color else None,
            timestamp=datetime.utcnow().isoformat(),
            fields=fields,
            footer={'text': footer_text} if footer_text else None,
            thumbnail={'url': thumbnail_url} if thumbnail_url else None
        )
        
        message = DiscordMessage(
            content=content,
            embeds=[embed]
        )
        
        return await self.send_message(message)
    
    async def send_simple_message(self, content: str) -> bool:
        """
        Send a simple text message.
        
        Args:
            content: Message content
            
        Returns:
            True if successful, False otherwise
        """
        message = DiscordMessage(content=content)
        return await self.send_message(message)
    
    async def test_webhook(self) -> bool:
        """
        Test the webhook connection.
        
        Returns:
            True if webhook is working, False otherwise
        """
        return await self.send_embed(
            title="🧙‍♂️ D&D Beyond Monitor",
            description="Discord webhook connection test successful!",
            color=EmbedColor.SUCCESS,
            footer_text="Test message"
        )
    
    async def validate_webhook(self) -> WebhookValidationResult:
        """
        Validate the webhook configuration and connectivity.
        
        Returns:
            WebhookValidationResult with validation details
        """
        async with WebhookManager() as manager:
            return await manager.test_webhook_connectivity(self.webhook_url, send_test_message=False)
    
    async def validate_webhook_with_test(self) -> WebhookValidationResult:
        """
        Validate the webhook and send a test message.
        
        Returns:
            WebhookValidationResult with validation details
        """
        async with WebhookManager() as manager:
            return await manager.test_webhook_connectivity(self.webhook_url, send_test_message=True)
    
    def get_error_handler_status(self) -> Dict[str, Any]:
        """
        Get current error handler status for monitoring.
        
        Returns:
            Dictionary with error handler status information
        """
        return self.error_handler.get_circuit_breaker_status()
    
    def _mask_webhook_url(self, url: str) -> str:
        """
        Mask sensitive parts of webhook URL for logging.
        
        Args:
            url: Full webhook URL
            
        Returns:
            Masked URL safe for logging
        """
        if not url or len(url) < 20:
            return "***"
        
        # Extract parts for masking
        if 'webhooks' in url:
            # Format: https://discord.com/api/webhooks/ID/TOKEN
            parts = url.split('/')
            if len(parts) >= 6:
                # Show domain and first few chars of ID, mask token completely
                webhook_id = parts[-2]
                masked_id = f"{webhook_id[:4]}...{webhook_id[-4:]}" if len(webhook_id) > 8 else "***"
                return f"https://discord.com/api/webhooks/{masked_id}/***"
        
        # Fallback: show first and last few characters
        return f"{url[:15]}...{url[-4:]}"
    
    def get_logging_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive logging and error statistics.
        
        Returns:
            Dictionary with logging statistics and error handler status
        """
        return {
            'logging_stats': self.discord_logger.get_operation_stats(),
            'error_handler_status': self.error_handler.get_circuit_breaker_status()
        }


# Convenience function for quick Discord notifications
async def send_discord_notification(
    webhook_url: str,
    title: str,
    description: str,
    color: EmbedColor = EmbedColor.INFO,
    **kwargs
) -> bool:
    """
    Quick function to send a Discord notification.
    
    Args:
        webhook_url: Discord webhook URL
        title: Notification title
        description: Notification description
        color: Embed color
        **kwargs: Additional arguments for DiscordService
    
    Returns:
        True if successful, False otherwise
    """
    async with DiscordService(webhook_url, **kwargs) as discord:
        return await discord.send_embed(title, description, color)