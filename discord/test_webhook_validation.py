#!/usr/bin/env python3
"""
Test script for webhook validation functionality.

This script tests the new webhook validation and error handling features
without requiring a full Discord monitor setup.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from services.webhook_manager import WebhookManager, validate_webhook
from services.discord_error_handler import DiscordErrorHandler
from services.configuration_validator import ConfigurationValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_webhook_validation():
    """Test webhook validation with various URL formats."""
    logger.info("Testing webhook URL validation...")
    
    test_urls = [
        # Valid formats
        "https://discord.com/api/webhooks/123456789/abcdef123456",
        "https://discordapp.com/api/webhooks/987654321/xyz789abc",
        
        # Invalid formats
        "",
        "not-a-url",
        "http://discord.com/api/webhooks/123/abc",  # HTTP instead of HTTPS
        "https://discord.com/api/webhooks/invalid",  # Missing token
        "https://example.com/webhook",  # Wrong domain
        
        # Environment variable (should be valid)
        "${DISCORD_WEBHOOK_URL}",
        "%DISCORD_WEBHOOK_URL%"
    ]
    
    async with WebhookManager() as manager:
        for url in test_urls:
            is_valid, error = manager.validate_webhook_url_format(url)
            status = "✅ VALID" if is_valid else "❌ INVALID"
            logger.info(f"{status}: {url[:50]}{'...' if len(url) > 50 else ''}")
            if error:
                logger.info(f"  Error: {error}")


def test_configuration_validation():
    """Test configuration validation."""
    logger.info("Testing configuration validation...")
    
    # Test valid configuration
    valid_config = {
        "webhook_url": "${DISCORD_WEBHOOK_URL}",
        "character_id": 12345,
        "username": "Test Bot",
        "min_priority": "LOW",
        "notifications": {
            "username": "D&D Monitor"
        }
    }
    
    # Test invalid configuration
    invalid_config = {
        "webhook_url": "https://discord.com/api/webhooks/123456789/hardcoded-token-bad",
        "character_id": "not-a-number",
        "session_cookie": "hardcoded-cookie-also-bad",
        "min_priority": "INVALID_PRIORITY"
    }
    
    validator = ConfigurationValidator()
    
    # Test valid config
    logger.info("Testing valid configuration...")
    result = validator.validate_discord_config(valid_config)
    logger.info(f"Valid config result: {'✅ PASS' if result.is_valid else '❌ FAIL'}")
    
    # Test invalid config
    logger.info("Testing invalid configuration...")
    result = validator.validate_discord_config(invalid_config)
    logger.info(f"Invalid config result: {'✅ PASS' if result.is_valid else '❌ FAIL'} (should fail)")
    
    if result.errors:
        logger.info("Errors found:")
        for error in result.errors:
            logger.info(f"  - {error}")
    
    if result.security_warnings:
        logger.info("Security warnings:")
        for warning in result.security_warnings:
            logger.info(f"  - [{warning.severity.value}] {warning.message}")


def test_error_classification():
    """Test error classification and handling."""
    logger.info("Testing error classification...")
    
    handler = DiscordErrorHandler()
    
    # Test different error types
    test_errors = [
        (Exception("Connection timeout"), "Should be classified as network error"),
        (ValueError("Invalid webhook URL"), "Should be classified as configuration error"),
        (Exception("HTTP 404"), "Should be classified as webhook not found"),
        (Exception("HTTP 429"), "Should be classified as rate limited"),
        (Exception("HTTP 500"), "Should be classified as server error")
    ]
    
    for error, description in test_errors:
        error_type = handler.classify_error(error)
        logger.info(f"Error: {str(error)[:50]} -> {error_type.value}")
        
        # Test error handling
        result = handler.handle_webhook_error(error)
        logger.info(f"  Should retry: {result.should_retry}")
        logger.info(f"  User message: {result.user_message}")


async def main():
    """Run all tests."""
    logger.info("Starting webhook validation tests...")
    
    try:
        # Test webhook validation
        await test_webhook_validation()
        
        # Test configuration validation
        test_configuration_validation()
        
        # Test error classification
        test_error_classification()
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)