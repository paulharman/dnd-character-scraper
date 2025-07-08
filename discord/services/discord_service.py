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

logger = logging.getLogger(__name__)

# Discord message limits
DISCORD_MESSAGE_LIMIT = 2000        # Characters in message content
DISCORD_EMBED_LIMIT = 6000          # Total characters per embed
DISCORD_EMBED_DESC_LIMIT = 4096     # Characters in embed description
DISCORD_EMBED_FIELD_LIMIT = 1024    # Characters per field value
DISCORD_EMBED_FIELD_COUNT_LIMIT = 25 # Maximum fields per embed


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
        
        logger.info(f"Discord service initialized for webhook: {webhook_url[:50]}...")
    
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
                        return True
                    elif response.status == 429:
                        # Rate limited by Discord
                        retry_after = int(response.headers.get('Retry-After', 1))
                        logger.warning(f"Discord rate limited, waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        error_text = await response.text()
                        logger.error(f"Discord API error {response.status}: {error_text}")
                        
                        # Don't retry client errors (4xx except 429)
                        if 400 <= response.status < 500 and response.status != 429:
                            return False
                            
            except asyncio.TimeoutError:
                logger.error(f"Discord request timeout (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"Discord request failed (attempt {attempt + 1}): {e}")
            
            # Calculate backoff delay
            if attempt < self.max_retries:
                delay = min(
                    self.retry_backoff_factor ** attempt,
                    self.retry_max_delay
                )
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