#!/usr/bin/env python3
"""
Enhanced logging utilities for Discord integration.

Provides structured logging, error tracking, and performance monitoring
for Discord operations with security-conscious log formatting.
"""

import logging
import time
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import functools

# Create a dedicated logger for Discord operations
discord_logger = logging.getLogger('discord')


class LogLevel(Enum):
    """Log levels for Discord operations."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class OperationType(Enum):
    """Types of Discord operations for logging."""
    WEBHOOK_VALIDATION = "webhook_validation"
    MESSAGE_SEND = "message_send"
    CONFIGURATION_LOAD = "configuration_load"
    ERROR_HANDLING = "error_handling"
    RATE_LIMITING = "rate_limiting"
    SECURITY_CHECK = "security_check"


@dataclass
class LogEntry:
    """Structured log entry for Discord operations."""
    timestamp: str
    operation: OperationType
    level: LogLevel
    message: str
    details: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None
    character_id: Optional[int] = None
    error_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class DiscordLogger:
    """
    Enhanced logging for Discord operations.
    
    Features:
    - Structured logging with operation tracking
    - Performance monitoring
    - Security-conscious log formatting
    - Error aggregation and reporting
    - Rate limit tracking
    """
    
    def __init__(self, logger_name: str = 'discord'):
        self.logger = logging.getLogger(logger_name)
        self.operation_stats = {}
        self.error_counts = {}
        self.rate_limit_events = []
        
    def log_operation(
        self,
        operation: OperationType,
        level: LogLevel,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        character_id: Optional[int] = None,
        error_type: Optional[str] = None
    ):
        """
        Log a Discord operation with structured data.
        
        Args:
            operation: Type of operation being logged
            level: Log level
            message: Human-readable message
            details: Additional structured data
            character_id: Character ID if applicable
            error_type: Error type if this is an error log
        """
        # Create structured log entry
        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat(),
            operation=operation,
            level=level,
            message=message,
            details=self._sanitize_details(details) if details else None,
            character_id=character_id,
            error_type=error_type
        )
        
        # Log using standard logger
        log_method = getattr(self.logger, level.value.lower())
        log_method(f"[{operation.value}] {message}")
        
        # Log details if present and debug level
        if details and self.logger.isEnabledFor(logging.DEBUG):
            sanitized_details = self._sanitize_details(details)
            self.logger.debug(f"Details: {json.dumps(sanitized_details, indent=2)}")
        
        # Track operation statistics
        self._track_operation_stats(operation, level, error_type)
    
    def log_webhook_operation(
        self,
        operation_name: str,
        webhook_url: str,
        success: bool,
        duration_ms: Optional[float] = None,
        error_details: Optional[Dict[str, Any]] = None
    ):
        """
        Log webhook-specific operations with URL masking.
        
        Args:
            operation_name: Name of the webhook operation
            webhook_url: Webhook URL (will be masked)
            success: Whether operation succeeded
            duration_ms: Operation duration in milliseconds
            error_details: Error details if operation failed
        """
        masked_url = self._mask_webhook_url(webhook_url)
        
        level = LogLevel.INFO if success else LogLevel.ERROR
        message = f"{operation_name} {'succeeded' if success else 'failed'} for webhook {masked_url}"
        
        details = {
            'webhook_masked': masked_url,
            'success': success,
            'duration_ms': duration_ms
        }
        
        if error_details:
            details['error'] = self._sanitize_details(error_details)
        
        self.log_operation(
            OperationType.MESSAGE_SEND,
            level,
            message,
            details,
            error_type='webhook_error' if not success else None
        )
    
    def log_rate_limit_event(
        self,
        retry_after: float,
        operation: str,
        character_id: Optional[int] = None
    ):
        """
        Log rate limiting events for monitoring.
        
        Args:
            retry_after: Seconds to wait before retry
            operation: Operation that was rate limited
            character_id: Character ID if applicable
        """
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'retry_after': retry_after,
            'operation': operation,
            'character_id': character_id
        }
        
        self.rate_limit_events.append(event)
        
        # Keep only recent events (last 24 hours)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self.rate_limit_events = [
            e for e in self.rate_limit_events
            if datetime.fromisoformat(e['timestamp']) > cutoff
        ]
        
        self.log_operation(
            OperationType.RATE_LIMITING,
            LogLevel.WARNING,
            f"Rate limited for {retry_after}s during {operation}",
            event,
            character_id=character_id
        )
    
    def log_configuration_event(
        self,
        event_type: str,
        message: str,
        config_details: Optional[Dict[str, Any]] = None,
        security_level: Optional[str] = None
    ):
        """
        Log configuration-related events.
        
        Args:
            event_type: Type of configuration event
            message: Human-readable message
            config_details: Configuration details (will be sanitized)
            security_level: Security level if this is a security event
        """
        level = LogLevel.WARNING if security_level in ['HIGH', 'MEDIUM'] else LogLevel.INFO
        
        details = {
            'event_type': event_type,
            'security_level': security_level
        }
        
        if config_details:
            details['config'] = self._sanitize_details(config_details)
        
        self.log_operation(
            OperationType.CONFIGURATION_LOAD,
            level,
            message,
            details
        )
    
    def log_error_with_context(
        self,
        error: Exception,
        operation: OperationType,
        context: Optional[Dict[str, Any]] = None,
        character_id: Optional[int] = None
    ):
        """
        Log errors with full context for debugging.
        
        Args:
            error: Exception that occurred
            operation: Operation during which error occurred
            context: Additional context information
            character_id: Character ID if applicable
        """
        error_type = type(error).__name__
        
        details = {
            'error_type': error_type,
            'error_message': str(error),
            'context': self._sanitize_details(context) if context else None
        }
        
        self.log_operation(
            operation,
            LogLevel.ERROR,
            f"{error_type}: {str(error)}",
            details,
            character_id=character_id,
            error_type=error_type
        )
    
    def get_operation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about logged operations.
        
        Returns:
            Dictionary with operation statistics
        """
        return {
            'operation_counts': dict(self.operation_stats),
            'error_counts': dict(self.error_counts),
            'recent_rate_limits': len(self.rate_limit_events),
            'rate_limit_events': self.rate_limit_events[-10:]  # Last 10 events
        }
    
    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize log details to remove sensitive information.
        
        Args:
            details: Raw details dictionary
            
        Returns:
            Sanitized details safe for logging
        """
        if not isinstance(details, dict):
            return details
        
        sanitized = {}
        sensitive_keys = {
            'webhook_url', 'token', 'password', 'secret', 'cookie',
            'authorization', 'auth', 'key', 'session'
        }
        
        for key, value in details.items():
            key_lower = key.lower()
            
            # Check if key contains sensitive information
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                if isinstance(value, str) and len(value) > 8:
                    sanitized[key] = f"{value[:4]}...{value[-4:]}"
                else:
                    sanitized[key] = "***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_details(value)
            elif isinstance(value, str) and 'webhook' in value.lower():
                sanitized[key] = self._mask_webhook_url(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _mask_webhook_url(self, url: str) -> str:
        """
        Mask webhook URL for safe logging.
        
        Args:
            url: Webhook URL to mask
            
        Returns:
            Masked URL safe for logging
        """
        if not url or len(url) < 20:
            return "***"
        
        if 'webhooks' in url:
            parts = url.split('/')
            if len(parts) >= 6:
                webhook_id = parts[-2]
                masked_id = f"{webhook_id[:4]}...{webhook_id[-4:]}" if len(webhook_id) > 8 else "***"
                return f"https://discord.com/api/webhooks/{masked_id}/***"
        
        return f"{url[:15]}...{url[-4:]}"
    
    def _track_operation_stats(
        self,
        operation: OperationType,
        level: LogLevel,
        error_type: Optional[str]
    ):
        """Track statistics for operations and errors."""
        # Track operation counts
        op_key = operation.value
        if op_key not in self.operation_stats:
            self.operation_stats[op_key] = {'total': 0, 'errors': 0}
        
        self.operation_stats[op_key]['total'] += 1
        
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            self.operation_stats[op_key]['errors'] += 1
        
        # Track error types
        if error_type:
            if error_type not in self.error_counts:
                self.error_counts[error_type] = 0
            self.error_counts[error_type] += 1


def timed_operation(operation: OperationType, logger: DiscordLogger):
    """
    Decorator to time and log Discord operations.
    
    Args:
        operation: Type of operation being timed
        logger: Logger instance to use
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_operation(
                    operation,
                    LogLevel.INFO,
                    f"{func.__name__} completed in {duration_ms:.1f}ms",
                    {'duration_ms': duration_ms, 'success': True}
                )
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_error_with_context(
                    e,
                    operation,
                    {'duration_ms': duration_ms, 'function': func.__name__}
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_operation(
                    operation,
                    LogLevel.INFO,
                    f"{func.__name__} completed in {duration_ms:.1f}ms",
                    {'duration_ms': duration_ms, 'success': True}
                )
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_error_with_context(
                    e,
                    operation,
                    {'duration_ms': duration_ms, 'function': func.__name__}
                )
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global logger instance
discord_logger_instance = DiscordLogger()


# Convenience functions
def log_webhook_operation(operation_name: str, webhook_url: str, success: bool, **kwargs):
    """Convenience function for logging webhook operations."""
    discord_logger_instance.log_webhook_operation(operation_name, webhook_url, success, **kwargs)


def log_rate_limit(retry_after: float, operation: str, character_id: Optional[int] = None):
    """Convenience function for logging rate limit events."""
    discord_logger_instance.log_rate_limit_event(retry_after, operation, character_id)


def log_configuration_event(event_type: str, message: str, **kwargs):
    """Convenience function for logging configuration events."""
    discord_logger_instance.log_configuration_event(event_type, message, **kwargs)


def log_error(error: Exception, operation: OperationType, **kwargs):
    """Convenience function for logging errors with context."""
    discord_logger_instance.log_error_with_context(error, operation, **kwargs)