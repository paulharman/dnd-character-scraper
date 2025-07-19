#!/usr/bin/env python3
"""
Discord Error Handler for comprehensive error handling and recovery.

Provides error classification, retry logic, and user-friendly error messages
for Discord API interactions and webhook operations.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Classification of Discord API errors."""
    WEBHOOK_NOT_FOUND = "webhook_not_found"      # 404 errors
    PERMISSION_ERROR = "permission_error"        # 403 errors
    RATE_LIMITED = "rate_limited"               # 429 errors
    NETWORK_ERROR = "network_error"             # Connection issues
    SERVER_ERROR = "server_error"               # 5xx errors
    CLIENT_ERROR = "client_error"               # 4xx errors (except 403, 404, 429)
    TIMEOUT_ERROR = "timeout_error"             # Request timeouts
    CONFIGURATION_ERROR = "configuration_error"  # Invalid config
    UNKNOWN_ERROR = "unknown_error"             # Unclassified errors


@dataclass
class ErrorHandlingResult:
    """Result of error handling analysis."""
    should_retry: bool
    retry_delay: float
    error_type: ErrorType
    user_message: str
    technical_details: str
    troubleshooting_steps: List[str]
    is_permanent: bool = False
    
    def __post_init__(self):
        if not self.troubleshooting_steps:
            self.troubleshooting_steps = []


class DiscordErrorHandler:
    """
    Comprehensive error handling for Discord operations.
    
    Features:
    - Error classification and analysis
    - Retry logic with exponential backoff
    - User-friendly error messages
    - Troubleshooting guidance
    - Rate limit handling
    """
    
    def __init__(
        self,
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        
        # Track consecutive errors for circuit breaker
        self.consecutive_errors = 0
        self.last_error_time = 0
        self.circuit_breaker_threshold = 10
        self.circuit_breaker_reset_time = 300  # 5 minutes
    
    def classify_error(self, error: Exception, response: Optional[aiohttp.ClientResponse] = None) -> ErrorType:
        """
        Classify an error for appropriate handling.
        
        Args:
            error: The exception that occurred
            response: HTTP response if available
            
        Returns:
            ErrorType classification
        """
        # HTTP response errors
        if response:
            status = response.status
            
            if status == 404:
                return ErrorType.WEBHOOK_NOT_FOUND
            elif status == 403:
                return ErrorType.PERMISSION_ERROR
            elif status == 429:
                return ErrorType.RATE_LIMITED
            elif 400 <= status < 500:
                return ErrorType.CLIENT_ERROR
            elif 500 <= status < 600:
                return ErrorType.SERVER_ERROR
        
        # Exception-based classification
        if isinstance(error, asyncio.TimeoutError):
            return ErrorType.TIMEOUT_ERROR
        elif isinstance(error, aiohttp.ClientConnectorError):
            return ErrorType.NETWORK_ERROR
        elif isinstance(error, aiohttp.ClientError):
            return ErrorType.NETWORK_ERROR
        elif isinstance(error, ValueError) and "webhook" in str(error).lower():
            return ErrorType.CONFIGURATION_ERROR
        
        return ErrorType.UNKNOWN_ERROR
    
    def should_retry(self, error: Exception, attempt: int, response: Optional[aiohttp.ClientResponse] = None) -> bool:
        """
        Determine if an error should be retried.
        
        Args:
            error: The exception that occurred
            attempt: Current attempt number (0-based)
            response: HTTP response if available
            
        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.max_retries:
            return False
        
        # Check circuit breaker
        if self._is_circuit_breaker_open():
            logger.warning("Circuit breaker is open, not retrying")
            return False
        
        error_type = self.classify_error(error, response)
        
        # Never retry these errors
        permanent_errors = {
            ErrorType.WEBHOOK_NOT_FOUND,
            ErrorType.PERMISSION_ERROR,
            ErrorType.CLIENT_ERROR,
            ErrorType.CONFIGURATION_ERROR
        }
        
        if error_type in permanent_errors:
            return False
        
        # Always retry these errors (with limits)
        retryable_errors = {
            ErrorType.RATE_LIMITED,
            ErrorType.SERVER_ERROR,
            ErrorType.NETWORK_ERROR,
            ErrorType.TIMEOUT_ERROR,
            ErrorType.UNKNOWN_ERROR
        }
        
        return error_type in retryable_errors
    
    def get_retry_delay(self, attempt: int, response: Optional[aiohttp.ClientResponse] = None) -> float:
        """
        Calculate retry delay with exponential backoff.
        
        Args:
            attempt: Current attempt number (0-based)
            response: HTTP response if available (for rate limit headers)
            
        Returns:
            Delay in seconds
        """
        # Check for Discord rate limit headers
        if response and response.status == 429:
            retry_after = response.headers.get('Retry-After')
            if retry_after:
                try:
                    return float(retry_after)
                except ValueError:
                    pass
        
        # Exponential backoff
        delay = self.base_delay * (self.backoff_factor ** attempt)
        return min(delay, self.max_delay)
    
    def handle_webhook_error(self, error: Exception, response: Optional[aiohttp.ClientResponse] = None) -> ErrorHandlingResult:
        """
        Handle a webhook-related error and provide guidance.
        
        Args:
            error: The exception that occurred
            response: HTTP response if available
            
        Returns:
            ErrorHandlingResult with handling recommendations
        """
        error_type = self.classify_error(error, response)
        
        # Update circuit breaker state
        self._record_error()
        
        # Generate appropriate response based on error type
        if error_type == ErrorType.WEBHOOK_NOT_FOUND:
            return self._handle_webhook_not_found(error, response)
        elif error_type == ErrorType.PERMISSION_ERROR:
            return self._handle_permission_error(error, response)
        elif error_type == ErrorType.RATE_LIMITED:
            return self._handle_rate_limited(error, response)
        elif error_type == ErrorType.NETWORK_ERROR:
            return self._handle_network_error(error, response)
        elif error_type == ErrorType.SERVER_ERROR:
            return self._handle_server_error(error, response)
        elif error_type == ErrorType.TIMEOUT_ERROR:
            return self._handle_timeout_error(error, response)
        elif error_type == ErrorType.CLIENT_ERROR:
            return self._handle_client_error(error, response)
        elif error_type == ErrorType.CONFIGURATION_ERROR:
            return self._handle_configuration_error(error, response)
        else:
            return self._handle_unknown_error(error, response)
    
    def generate_troubleshooting_info(self, error: Exception, response: Optional[aiohttp.ClientResponse] = None) -> str:
        """
        Generate comprehensive troubleshooting information.
        
        Args:
            error: The exception that occurred
            response: HTTP response if available
            
        Returns:
            Formatted troubleshooting information
        """
        result = self.handle_webhook_error(error, response)
        
        info = [
            f"Error Type: {result.error_type.value}",
            f"User Message: {result.user_message}",
            f"Technical Details: {result.technical_details}",
            f"Should Retry: {result.should_retry}",
            f"Is Permanent: {result.is_permanent}"
        ]
        
        if result.troubleshooting_steps:
            info.append("Troubleshooting Steps:")
            for i, step in enumerate(result.troubleshooting_steps, 1):
                info.append(f"  {i}. {step}")
        
        return "\n".join(info)
    
    def _handle_webhook_not_found(self, error: Exception, response: Optional[aiohttp.ClientResponse]) -> ErrorHandlingResult:
        """Handle webhook not found errors (404)."""
        return ErrorHandlingResult(
            should_retry=False,
            retry_delay=0,
            error_type=ErrorType.WEBHOOK_NOT_FOUND,
            user_message="Discord webhook not found. The webhook may have been deleted or the URL is incorrect.",
            technical_details=f"HTTP 404: {str(error)}",
            is_permanent=True,
            troubleshooting_steps=[
                "Check if the webhook still exists in Discord server settings",
                "Verify the webhook URL is copied correctly",
                "Create a new webhook if the old one was deleted",
                "Ensure you have the complete URL including the token",
                "Contact server administrator if webhook was removed"
            ]
        )
    
    def _handle_permission_error(self, error: Exception, response: Optional[aiohttp.ClientResponse]) -> ErrorHandlingResult:
        """Handle permission errors (403)."""
        return ErrorHandlingResult(
            should_retry=False,
            retry_delay=0,
            error_type=ErrorType.PERMISSION_ERROR,
            user_message="Permission denied. The webhook token may be invalid or permissions changed.",
            technical_details=f"HTTP 403: {str(error)}",
            is_permanent=True,
            troubleshooting_steps=[
                "Verify the webhook token in the URL is correct",
                "Check if the webhook was regenerated (old token invalid)",
                "Ensure the webhook has permission to send messages",
                "Try creating a new webhook with fresh permissions",
                "Contact server administrator about channel permissions"
            ]
        )
    
    def _handle_rate_limited(self, error: Exception, response: Optional[aiohttp.ClientResponse]) -> ErrorHandlingResult:
        """Handle rate limiting errors (429)."""
        retry_after = 60  # Default
        if response:
            retry_after = int(response.headers.get('Retry-After', 60))
        
        return ErrorHandlingResult(
            should_retry=True,
            retry_delay=retry_after,
            error_type=ErrorType.RATE_LIMITED,
            user_message=f"Rate limited by Discord. Will retry in {retry_after} seconds.",
            technical_details=f"HTTP 429: Rate limit exceeded. Retry after {retry_after}s",
            troubleshooting_steps=[
                "Wait for the specified retry period",
                "Reduce the frequency of Discord notifications",
                "Implement proper rate limiting in configuration",
                "Consider using multiple webhooks for high volume",
                "Check Discord's rate limit documentation"
            ]
        )
    
    def _handle_network_error(self, error: Exception, response: Optional[aiohttp.ClientResponse]) -> ErrorHandlingResult:
        """Handle network connectivity errors."""
        return ErrorHandlingResult(
            should_retry=True,
            retry_delay=self.base_delay,
            error_type=ErrorType.NETWORK_ERROR,
            user_message="Network connection error. Will retry automatically.",
            technical_details=f"Network error: {str(error)}",
            troubleshooting_steps=[
                "Check your internet connection",
                "Verify DNS resolution is working",
                "Try accessing Discord in a web browser",
                "Check if a firewall is blocking the connection",
                "Try from a different network if possible"
            ]
        )
    
    def _handle_server_error(self, error: Exception, response: Optional[aiohttp.ClientResponse]) -> ErrorHandlingResult:
        """Handle Discord server errors (5xx)."""
        status = response.status if response else "unknown"
        
        return ErrorHandlingResult(
            should_retry=True,
            retry_delay=self.base_delay * 2,  # Longer delay for server errors
            error_type=ErrorType.SERVER_ERROR,
            user_message="Discord server error. This is usually temporary and will be retried.",
            technical_details=f"HTTP {status}: Discord server error - {str(error)}",
            troubleshooting_steps=[
                "Wait a few minutes - Discord server issues are usually temporary",
                "Check Discord's status page: https://discordstatus.com/",
                "Try testing with a different webhook if available",
                "Monitor Discord's official channels for service announcements",
                "The system will automatically retry with exponential backoff"
            ]
        )
    
    def _handle_timeout_error(self, error: Exception, response: Optional[aiohttp.ClientResponse]) -> ErrorHandlingResult:
        """Handle request timeout errors."""
        return ErrorHandlingResult(
            should_retry=True,
            retry_delay=self.base_delay,
            error_type=ErrorType.TIMEOUT_ERROR,
            user_message="Request timed out. Will retry with longer timeout.",
            technical_details=f"Timeout error: {str(error)}",
            troubleshooting_steps=[
                "Check your internet connection speed",
                "Verify network stability",
                "Try from a different network if possible",
                "The system will automatically retry",
                "Consider increasing timeout settings if this persists"
            ]
        )
    
    def _handle_client_error(self, error: Exception, response: Optional[aiohttp.ClientResponse]) -> ErrorHandlingResult:
        """Handle other client errors (4xx)."""
        status = response.status if response else "unknown"
        
        return ErrorHandlingResult(
            should_retry=False,
            retry_delay=0,
            error_type=ErrorType.CLIENT_ERROR,
            user_message="Client error in Discord request. Check configuration and message format.",
            technical_details=f"HTTP {status}: Client error - {str(error)}",
            is_permanent=True,
            troubleshooting_steps=[
                "Check if the message content is valid",
                "Verify message is not too long (2000 character limit)",
                "Ensure embed structure is correct",
                "Check webhook URL format",
                "Review Discord API documentation for requirements"
            ]
        )
    
    def _handle_configuration_error(self, error: Exception, response: Optional[aiohttp.ClientResponse]) -> ErrorHandlingResult:
        """Handle configuration-related errors."""
        return ErrorHandlingResult(
            should_retry=False,
            retry_delay=0,
            error_type=ErrorType.CONFIGURATION_ERROR,
            user_message="Configuration error. Please check your Discord settings.",
            technical_details=f"Configuration error: {str(error)}",
            is_permanent=True,
            troubleshooting_steps=[
                "Check webhook URL format and validity",
                "Verify all required configuration fields are present",
                "Ensure webhook URL is not empty or malformed",
                "Review configuration file syntax",
                "Check environment variables if using them"
            ]
        )
    
    def _handle_unknown_error(self, error: Exception, response: Optional[aiohttp.ClientResponse]) -> ErrorHandlingResult:
        """Handle unclassified errors."""
        return ErrorHandlingResult(
            should_retry=True,
            retry_delay=self.base_delay,
            error_type=ErrorType.UNKNOWN_ERROR,
            user_message="Unknown error occurred. Will attempt to retry.",
            technical_details=f"Unknown error: {str(error)}",
            troubleshooting_steps=[
                "Check Discord webhook configuration",
                "Verify internet connectivity",
                "Try creating a new webhook",
                "Check system logs for more details",
                "Contact support if the issue persists"
            ]
        )
    
    def _record_error(self):
        """Record an error for circuit breaker tracking."""
        self.consecutive_errors += 1
        self.last_error_time = time.time()
        
        if self.consecutive_errors >= self.circuit_breaker_threshold:
            logger.warning(f"Circuit breaker threshold reached: {self.consecutive_errors} consecutive errors")
    
    def record_success(self):
        """Record a successful operation (resets circuit breaker)."""
        self.consecutive_errors = 0
        self.last_error_time = 0
    
    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open (preventing retries)."""
        if self.consecutive_errors < self.circuit_breaker_threshold:
            return False
        
        # Check if enough time has passed to reset
        if time.time() - self.last_error_time > self.circuit_breaker_reset_time:
            logger.info("Circuit breaker reset time reached, allowing retry")
            self.consecutive_errors = 0
            return False
        
        return True
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status for monitoring."""
        return {
            "consecutive_errors": self.consecutive_errors,
            "is_open": self._is_circuit_breaker_open(),
            "last_error_time": self.last_error_time,
            "threshold": self.circuit_breaker_threshold,
            "reset_time": self.circuit_breaker_reset_time
        }