"""
Error Handler Service

Provides comprehensive error handling and recovery mechanisms for the enhanced
Discord change tracking system, including graceful degradation, retry logic,
and monitoring capabilities.
"""

import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import json
import traceback

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for monitoring and alerting."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors for classification and handling."""
    DETECTOR_FAILURE = "detector_failure"
    STORAGE_FAILURE = "storage_failure"
    DATA_VALIDATION = "data_validation"
    CAUSATION_ANALYSIS = "causation_analysis"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    SYSTEM = "system"


@dataclass
class ErrorRecord:
    """Record of an error occurrence with context and metadata."""
    timestamp: datetime
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    component: str
    message: str
    exception_type: str
    traceback_info: str
    context: Dict[str, Any] = field(default_factory=dict)
    character_id: Optional[int] = None
    retry_count: int = 0
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error record to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'error_id': self.error_id,
            'category': self.category.value,
            'severity': self.severity.value,
            'component': self.component,
            'message': self.message,
            'exception_type': self.exception_type,
            'traceback_info': self.traceback_info,
            'context': self.context,
            'character_id': self.character_id,
            'retry_count': self.retry_count,
            'resolved': self.resolved,
            'resolution_timestamp': self.resolution_timestamp.isoformat() if self.resolution_timestamp else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorRecord':
        """Create error record from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            error_id=data['error_id'],
            category=ErrorCategory(data['category']),
            severity=ErrorSeverity(data['severity']),
            component=data['component'],
            message=data['message'],
            exception_type=data['exception_type'],
            traceback_info=data['traceback_info'],
            context=data.get('context', {}),
            character_id=data.get('character_id'),
            retry_count=data.get('retry_count', 0),
            resolved=data.get('resolved', False),
            resolution_timestamp=datetime.fromisoformat(data['resolution_timestamp']) if data.get('resolution_timestamp') else None
        )


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number."""
        delay = min(self.base_delay * (self.exponential_base ** attempt), self.max_delay)
        
        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
        
        return delay


@dataclass
class ErrorHandlerConfig:
    """Configuration for error handler service."""
    error_log_path: Path = Path("custom_logs/error_log.json")
    max_error_records: int = 10000
    error_retention_days: int = 30
    enable_monitoring: bool = True
    enable_alerting: bool = False
    alert_threshold_per_hour: int = 10
    critical_error_immediate_alert: bool = True
    
    # Retry configurations for different error categories
    detector_retry_config: RetryConfig = field(default_factory=RetryConfig)
    storage_retry_config: RetryConfig = field(default_factory=lambda: RetryConfig(max_attempts=5, base_delay=2.0))
    network_retry_config: RetryConfig = field(default_factory=lambda: RetryConfig(max_attempts=3, base_delay=0.5))


class ErrorHandler:
    """
    Comprehensive error handler for the enhanced Discord change tracking system.
    Provides graceful degradation, retry logic, monitoring, and recovery mechanisms.
    """
    
    def __init__(self, config: ErrorHandlerConfig = None):
        self.config = config or ErrorHandlerConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Error tracking
        self.error_records: List[ErrorRecord] = []
        self.error_counts: Dict[str, int] = {}
        self.last_alert_time: Dict[str, datetime] = {}
        
        # Component health tracking
        self.component_health: Dict[str, Dict[str, Any]] = {}
        
        # Ensure error log directory exists
        self.config.error_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing error records
        self._load_error_records()
        
        self.logger.info("Error handler initialized")
    
    async def handle_detector_error(self, detector_name: str, error: Exception, 
                                  character_id: Optional[int] = None,
                                  context: Dict[str, Any] = None) -> bool:
        """
        Handle errors from individual change detectors with graceful degradation.
        
        Returns:
            bool: True if the error was handled gracefully, False if critical failure
        """
        try:
            error_record = self._create_error_record(
                category=ErrorCategory.DETECTOR_FAILURE,
                severity=self._determine_error_severity(error, ErrorCategory.DETECTOR_FAILURE),
                component=f"detector_{detector_name}",
                error=error,
                character_id=character_id,
                context=context or {}
            )
            
            await self._record_error(error_record)
            
            # Update component health
            self._update_component_health(f"detector_{detector_name}", False, str(error))
            
            # Determine if this is a critical failure or can be handled gracefully
            if self._is_critical_detector_error(error):
                self.logger.critical(f"Critical detector error in {detector_name}: {error}")
                return False
            
            # Log warning and continue with other detectors
            self.logger.warning(f"Detector {detector_name} failed, continuing with other detectors: {error}")
            
            # Check if detector is consistently failing
            recent_failures = self._get_recent_error_count(f"detector_{detector_name}", hours=1)
            if recent_failures >= 5:
                self.logger.error(f"Detector {detector_name} has failed {recent_failures} times in the last hour")
                await self._trigger_alert(error_record)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in detector error handler: {e}", exc_info=True)
            return False
    
    async def handle_storage_error(self, operation: str, error: Exception,
                                 character_id: Optional[int] = None,
                                 context: Dict[str, Any] = None,
                                 retry_func: Optional[Callable] = None) -> bool:
        """
        Handle change log storage errors with retry logic.
        
        Args:
            operation: Description of the storage operation that failed
            error: The exception that occurred
            character_id: Character ID if applicable
            context: Additional context information
            retry_func: Function to retry if provided
            
        Returns:
            bool: True if operation succeeded (possibly after retry), False if failed
        """
        try:
            error_record = self._create_error_record(
                category=ErrorCategory.STORAGE_FAILURE,
                severity=self._determine_error_severity(error, ErrorCategory.STORAGE_FAILURE),
                component="change_log_storage",
                error=error,
                character_id=character_id,
                context={**(context or {}), 'operation': operation}
            )
            
            await self._record_error(error_record)
            
            # If no retry function provided, just log and return False
            if not retry_func:
                self.logger.error(f"Storage operation '{operation}' failed with no retry available: {error}")
                return False
            
            # Attempt retry with exponential backoff
            retry_config = self.config.storage_retry_config
            
            for attempt in range(1, retry_config.max_attempts + 1):
                try:
                    delay = retry_config.get_delay(attempt - 1)
                    self.logger.info(f"Retrying storage operation '{operation}' (attempt {attempt}/{retry_config.max_attempts}) after {delay:.2f}s delay")
                    
                    await asyncio.sleep(delay)
                    
                    # Attempt the retry
                    if asyncio.iscoroutinefunction(retry_func):
                        result = await retry_func()
                    else:
                        result = retry_func()
                    
                    # Success - mark error as resolved
                    error_record.resolved = True
                    error_record.resolution_timestamp = datetime.now()
                    error_record.retry_count = attempt
                    
                    self.logger.info(f"Storage operation '{operation}' succeeded on attempt {attempt}")
                    self._update_component_health("change_log_storage", True, "Operation successful after retry")
                    
                    return True
                    
                except Exception as retry_error:
                    error_record.retry_count = attempt
                    self.logger.warning(f"Storage retry attempt {attempt} failed: {retry_error}")
                    
                    if attempt == retry_config.max_attempts:
                        # Final attempt failed
                        self.logger.error(f"Storage operation '{operation}' failed after {retry_config.max_attempts} attempts")
                        self._update_component_health("change_log_storage", False, f"Failed after {retry_config.max_attempts} attempts")
                        await self._trigger_alert(error_record)
                        return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in storage error handler: {e}", exc_info=True)
            return False
    
    async def handle_data_validation_error(self, data_source: str, error: Exception,
                                         character_id: Optional[int] = None,
                                         malformed_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Handle malformed character data gracefully with data sanitization.
        
        Args:
            data_source: Source of the malformed data
            error: The validation error
            character_id: Character ID if available
            malformed_data: The malformed data that caused the error
            
        Returns:
            Optional[Dict[str, Any]]: Sanitized data if possible, None if unrecoverable
        """
        try:
            error_record = self._create_error_record(
                category=ErrorCategory.DATA_VALIDATION,
                severity=self._determine_error_severity(error, ErrorCategory.DATA_VALIDATION),
                component=f"data_validation_{data_source}",
                error=error,
                character_id=character_id,
                context={'data_source': data_source, 'has_malformed_data': malformed_data is not None}
            )
            
            await self._record_error(error_record)
            
            # Attempt data sanitization
            if malformed_data:
                sanitized_data = self._sanitize_character_data(malformed_data, data_source)
                
                if sanitized_data:
                    self.logger.warning(f"Successfully sanitized malformed data from {data_source} for character {character_id}")
                    error_record.resolved = True
                    error_record.resolution_timestamp = datetime.now()
                    return sanitized_data
                else:
                    self.logger.error(f"Could not sanitize malformed data from {data_source} for character {character_id}")
            
            # Check if this is a recurring data validation issue
            recent_failures = self._get_recent_error_count(f"data_validation_{data_source}", hours=24)
            if recent_failures >= 3:
                await self._trigger_alert(error_record)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in data validation error handler: {e}", exc_info=True)
            return None
    
    async def handle_causation_analysis_error(self, error: Exception,
                                            character_id: Optional[int] = None,
                                            context: Dict[str, Any] = None) -> bool:
        """
        Handle errors in causation analysis with graceful degradation.
        
        Returns:
            bool: True if system can continue without causation analysis, False if critical
        """
        try:
            error_record = self._create_error_record(
                category=ErrorCategory.CAUSATION_ANALYSIS,
                severity=ErrorSeverity.MEDIUM,  # Causation analysis is not critical for basic functionality
                component="causation_analyzer",
                error=error,
                character_id=character_id,
                context=context or {}
            )
            
            await self._record_error(error_record)
            
            self.logger.warning(f"Causation analysis failed, continuing without detailed attribution: {error}")
            
            # Update component health
            self._update_component_health("causation_analyzer", False, str(error))
            
            # Causation analysis failure is not critical - system can continue
            return True
            
        except Exception as e:
            self.logger.error(f"Error in causation analysis error handler: {e}", exc_info=True)
            return False
    
    def get_component_health_status(self) -> Dict[str, Dict[str, Any]]:
        """Get health status of all monitored components."""
        return self.component_health.copy()
    
    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for the specified time period."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_errors = [e for e in self.error_records if e.timestamp >= cutoff_time]
            
            # Count by category
            category_counts = {}
            for error in recent_errors:
                category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
            
            # Count by severity
            severity_counts = {}
            for error in recent_errors:
                severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
            
            # Count by component
            component_counts = {}
            for error in recent_errors:
                component_counts[error.component] = component_counts.get(error.component, 0) + 1
            
            # Resolution rate
            resolved_count = len([e for e in recent_errors if e.resolved])
            resolution_rate = (resolved_count / len(recent_errors)) * 100 if recent_errors else 100
            
            return {
                'time_period_hours': hours,
                'total_errors': len(recent_errors),
                'resolved_errors': resolved_count,
                'resolution_rate_percent': round(resolution_rate, 2),
                'errors_by_category': category_counts,
                'errors_by_severity': severity_counts,
                'errors_by_component': component_counts,
                'most_problematic_component': max(component_counts.items(), key=lambda x: x[1])[0] if component_counts else None
            }
            
        except Exception as e:
            self.logger.error(f"Error generating error statistics: {e}", exc_info=True)
            return {}
    
    async def cleanup_old_errors(self, retention_days: Optional[int] = None) -> int:
        """Clean up old error records based on retention policy."""
        try:
            retention_days = retention_days or self.config.error_retention_days
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            initial_count = len(self.error_records)
            self.error_records = [e for e in self.error_records if e.timestamp >= cutoff_date]
            cleaned_count = initial_count - len(self.error_records)
            
            if cleaned_count > 0:
                await self._save_error_records()
                self.logger.info(f"Cleaned up {cleaned_count} old error records (retention: {retention_days} days)")
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old error records: {e}", exc_info=True)
            return 0
    
    def _create_error_record(self, category: ErrorCategory, severity: ErrorSeverity,
                           component: str, error: Exception, character_id: Optional[int] = None,
                           context: Dict[str, Any] = None) -> ErrorRecord:
        """Create an error record from an exception."""
        import uuid
        
        return ErrorRecord(
            timestamp=datetime.now(),
            error_id=str(uuid.uuid4())[:8],
            category=category,
            severity=severity,
            component=component,
            message=str(error),
            exception_type=type(error).__name__,
            traceback_info=traceback.format_exc(),
            context=context or {},
            character_id=character_id
        )
    
    def _determine_error_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity based on exception type and category."""
        # Critical errors that should stop processing
        if isinstance(error, (MemoryError, SystemExit, KeyboardInterrupt)):
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if isinstance(error, (FileNotFoundError, PermissionError, OSError)) and category == ErrorCategory.STORAGE_FAILURE:
            return ErrorSeverity.HIGH
        
        if isinstance(error, (ConnectionError, TimeoutError)) and category == ErrorCategory.NETWORK:
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if isinstance(error, (ValueError, TypeError, KeyError)) and category == ErrorCategory.DATA_VALIDATION:
            return ErrorSeverity.MEDIUM
        
        if category == ErrorCategory.DETECTOR_FAILURE:
            return ErrorSeverity.MEDIUM
        
        # Default to low severity
        return ErrorSeverity.LOW
    
    def _is_critical_detector_error(self, error: Exception) -> bool:
        """Determine if a detector error is critical enough to stop processing."""
        # Only stop for truly critical system errors
        return isinstance(error, (MemoryError, SystemExit, KeyboardInterrupt))
    
    def _sanitize_character_data(self, data: Dict[str, Any], source: str) -> Optional[Dict[str, Any]]:
        """Attempt to sanitize malformed character data."""
        try:
            sanitized = {}
            
            # Basic character info sanitization
            if 'character_info' in data:
                char_info = data['character_info']
                if isinstance(char_info, dict):
                    sanitized['character_info'] = {
                        'name': str(char_info.get('name', 'Unknown')),
                        'level': max(1, int(char_info.get('level', 1))) if char_info.get('level') else 1,
                        'class': str(char_info.get('class', 'Unknown'))
                    }
            
            # Ability scores sanitization
            if 'ability_scores' in data:
                ability_scores = data['ability_scores']
                if isinstance(ability_scores, dict):
                    sanitized_abilities = {}
                    for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
                        value = ability_scores.get(ability)
                        if isinstance(value, (int, float)):
                            sanitized_abilities[ability] = max(1, min(30, int(value)))
                        else:
                            sanitized_abilities[ability] = 10  # Default value
                    sanitized['ability_scores'] = sanitized_abilities
            
            # Only return sanitized data if we have essential information
            if 'character_info' in sanitized and 'ability_scores' in sanitized:
                self.logger.info(f"Successfully sanitized character data from {source}")
                return sanitized
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error sanitizing character data: {e}", exc_info=True)
            return None
    
    def _update_component_health(self, component: str, healthy: bool, message: str):
        """Update health status for a component."""
        self.component_health[component] = {
            'healthy': healthy,
            'last_check': datetime.now().isoformat(),
            'message': message,
            'consecutive_failures': self.component_health.get(component, {}).get('consecutive_failures', 0) + (0 if healthy else 1)
        }
        
        if healthy:
            self.component_health[component]['consecutive_failures'] = 0
    
    def _get_recent_error_count(self, component: str, hours: int) -> int:
        """Get count of recent errors for a specific component."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return len([e for e in self.error_records 
                   if e.component == component and e.timestamp >= cutoff_time])
    
    async def _record_error(self, error_record: ErrorRecord):
        """Record an error and manage error log size."""
        self.error_records.append(error_record)
        
        # Maintain maximum error records
        if len(self.error_records) > self.config.max_error_records:
            # Remove oldest records
            self.error_records = self.error_records[-self.config.max_error_records:]
        
        # Save to disk
        await self._save_error_records()
        
        # Update error counts for monitoring
        self.error_counts[error_record.component] = self.error_counts.get(error_record.component, 0) + 1
    
    async def _trigger_alert(self, error_record: ErrorRecord):
        """Trigger alert for critical or recurring errors."""
        if not self.config.enable_alerting:
            return
        
        try:
            # Check if we should alert based on frequency
            now = datetime.now()
            last_alert = self.last_alert_time.get(error_record.component)
            
            if last_alert and (now - last_alert).total_seconds() < 3600:  # Don't alert more than once per hour
                return
            
            # Log alert (in a real system, this would send notifications)
            self.logger.critical(f"ALERT: {error_record.severity.value.upper()} error in {error_record.component}: {error_record.message}")
            
            self.last_alert_time[error_record.component] = now
            
        except Exception as e:
            self.logger.error(f"Error triggering alert: {e}", exc_info=True)
    
    def _load_error_records(self):
        """Load existing error records from disk."""
        try:
            if self.config.error_log_path.exists():
                with open(self.config.error_log_path, 'r') as f:
                    data = json.load(f)
                
                self.error_records = [ErrorRecord.from_dict(record) for record in data.get('error_records', [])]
                self.logger.info(f"Loaded {len(self.error_records)} existing error records")
            
        except Exception as e:
            self.logger.warning(f"Could not load existing error records: {e}")
            self.error_records = []
    
    async def _save_error_records(self):
        """Save error records to disk."""
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'total_records': len(self.error_records),
                'error_records': [record.to_dict() for record in self.error_records]
            }
            
            # Write to temporary file first, then rename for atomic operation
            temp_path = self.config.error_log_path.with_suffix('.tmp')
            
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            temp_path.replace(self.config.error_log_path)
            
        except Exception as e:
            self.logger.error(f"Error saving error records: {e}", exc_info=True)


# Global error handler instance
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler(config: ErrorHandlerConfig = None) -> ErrorHandler:
    """Get or create global error handler instance."""
    global _global_error_handler
    
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler(config)
    
    return _global_error_handler


def reset_error_handler():
    """Reset global error handler (mainly for testing)."""
    global _global_error_handler
    _global_error_handler = None