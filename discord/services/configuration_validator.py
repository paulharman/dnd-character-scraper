#!/usr/bin/env python3
"""
Configuration Validator for Discord integration.

Validates Discord configuration, checks for security issues,
and provides guidance for secure configuration practices.
"""

import os
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security warning levels."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class SecurityWarning:
    """Security warning information."""
    severity: SecurityLevel
    message: str
    recommendation: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    security_warnings: List[SecurityWarning]
    suggestions: List[str]
    
    def __post_init__(self):
        if not self.errors:
            self.errors = []
        if not self.warnings:
            self.warnings = []
        if not self.security_warnings:
            self.security_warnings = []
        if not self.suggestions:
            self.suggestions = []


class ConfigurationValidator:
    """
    Comprehensive configuration validation for Discord integration.
    
    Features:
    - Configuration field validation
    - Security risk detection
    - Environment variable recommendations
    - Webhook URL validation
    - File-based security scanning
    """
    
    def __init__(self):
        # Discord webhook URL patterns
        self.webhook_patterns = [
            re.compile(r'https://discord(?:app)?\.com/api/webhooks/\d+/[a-zA-Z0-9_-]+'),
            re.compile(r'discord\.com/api/webhooks'),
            re.compile(r'discordapp\.com/api/webhooks')
        ]
        
        # Environment variable patterns
        self.env_var_pattern = re.compile(r'\$\{([^}]+)\}|%([^%]+)%')
        
        # Required configuration fields
        self.required_fields = {
            'webhook_url': str,
            'character_id': (int, str),  # Can be int or string
        }
        
        # Optional fields with types
        self.optional_fields = {
            'username': str,
            'avatar_url': str,
            'min_priority': str,
            'change_types': list,
            'check_interval': int,
            'log_level': str,
            'run_continuous': bool,
            'session_cookie': str,
            'storage_dir': str,
            'notifications': dict,
            'advanced': dict,
            'filtering': dict,
            'party': list
        }
    
    def validate_discord_config(self, config: Dict[str, Any], config_file_path: Optional[str] = None) -> ValidationResult:
        """
        Validate complete Discord configuration.
        
        Args:
            config: Configuration dictionary
            config_file_path: Path to config file for security scanning
            
        Returns:
            ValidationResult with validation details
        """
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            security_warnings=[],
            suggestions=[]
        )
        
        # Validate required fields
        self._validate_required_fields(config, result)
        
        # Validate field types
        self._validate_field_types(config, result)
        
        # Validate webhook URL
        self._validate_webhook_url(config.get('webhook_url'), result)
        
        # Check for security risks
        self._check_security_risks(config, result, config_file_path)
        
        # Validate specific configurations
        self._validate_notifications_config(config.get('notifications', {}), result)
        self._validate_filtering_config(config.get('filtering', {}), result)
        self._validate_advanced_config(config.get('advanced', {}), result)
        
        # Generate suggestions
        self._generate_suggestions(config, result)
        
        # Set overall validity
        result.is_valid = len(result.errors) == 0
        
        return result
    
    def validate_webhook_url(self, url: str) -> Tuple[bool, Optional[str]]:
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
        
        # Check for environment variable
        if self.env_var_pattern.search(url):
            return True, None  # Environment variables are valid
        
        if not url.startswith('https://'):
            return False, "Webhook URL must use HTTPS"
        
        # Check Discord webhook pattern
        if not any(pattern.search(url) for pattern in self.webhook_patterns):
            return False, "Invalid Discord webhook URL format"
        
        # Check for common mistakes
        if 'discordapp.com' in url and 'discord.com' not in url:
            return False, "Use discord.com instead of discordapp.com for webhook URLs"
        
        return True, None
    
    def check_security_risks(self, config: Dict[str, Any], config_file_path: Optional[str] = None) -> List[SecurityWarning]:
        """
        Check configuration for security risks.
        
        Args:
            config: Configuration dictionary
            config_file_path: Path to config file
            
        Returns:
            List of security warnings
        """
        warnings = []
        
        # Check for hardcoded webhook URLs
        webhook_url = config.get('webhook_url', '')
        if webhook_url and isinstance(webhook_url, str):
            if not self.env_var_pattern.search(webhook_url) and webhook_url.startswith('https://'):
                warnings.append(SecurityWarning(
                    severity=SecurityLevel.HIGH,
                    message="Hardcoded webhook URL found in configuration",
                    recommendation="Use environment variables to store sensitive webhook URLs",
                    file_path=config_file_path
                ))
        
        # Check for session cookies
        session_cookie = config.get('session_cookie', '')
        if session_cookie and isinstance(session_cookie, str):
            if not self.env_var_pattern.search(session_cookie):
                warnings.append(SecurityWarning(
                    severity=SecurityLevel.HIGH,
                    message="Hardcoded session cookie found in configuration",
                    recommendation="Use environment variables to store session cookies",
                    file_path=config_file_path
                ))
        
        # Check for other sensitive data
        sensitive_fields = ['api_key', 'token', 'password', 'secret']
        for field in sensitive_fields:
            if field in config and config[field]:
                if not self.env_var_pattern.search(str(config[field])):
                    warnings.append(SecurityWarning(
                        severity=SecurityLevel.MEDIUM,
                        message=f"Potentially sensitive field '{field}' found in configuration",
                        recommendation=f"Consider using environment variables for '{field}'",
                        file_path=config_file_path
                    ))
        
        # Check file permissions if file path provided
        if config_file_path and os.path.exists(config_file_path):
            try:
                stat_info = os.stat(config_file_path)
                permissions = oct(stat_info.st_mode)[-3:]
                
                # Check if file is world-readable
                if int(permissions[2]) >= 4:
                    warnings.append(SecurityWarning(
                        severity=SecurityLevel.MEDIUM,
                        message="Configuration file is world-readable",
                        recommendation="Restrict file permissions to owner only (chmod 600)",
                        file_path=config_file_path
                    ))
            except Exception as e:
                logger.debug(f"Could not check file permissions: {e}")
        
        return warnings
    
    def suggest_environment_variables(self, config: Dict[str, Any]) -> List[str]:
        """
        Suggest environment variables for sensitive configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            List of environment variable suggestions
        """
        suggestions = []
        
        # Webhook URL
        webhook_url = config.get('webhook_url', '')
        if webhook_url and not self.env_var_pattern.search(webhook_url):
            suggestions.append("DISCORD_WEBHOOK_URL - for webhook URL")
        
        # Session cookie
        session_cookie = config.get('session_cookie', '')
        if session_cookie and not self.env_var_pattern.search(session_cookie):
            suggestions.append("DND_SESSION_COOKIE - for D&D Beyond session cookie")
        
        return suggestions
    
    def scan_files_for_webhooks(self, directory: str, extensions: List[str] = None) -> List[SecurityWarning]:
        """
        Scan files for hardcoded webhook URLs.
        
        Args:
            directory: Directory to scan
            extensions: File extensions to scan (default: common config files)
            
        Returns:
            List of security warnings for found webhooks
        """
        if extensions is None:
            extensions = ['.yml', '.yaml', '.json', '.txt', '.md', '.py', '.sh', '.bat']
        
        warnings = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            return warnings
        
        for file_path in directory_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            for pattern in self.webhook_patterns:
                                if pattern.search(line):
                                    warnings.append(SecurityWarning(
                                        severity=SecurityLevel.HIGH,
                                        message=f"Webhook URL found in file: {file_path.name}",
                                        recommendation="Remove webhook URL from version control and use environment variables",
                                        file_path=str(file_path),
                                        line_number=line_num
                                    ))
                except Exception as e:
                    logger.debug(f"Could not scan file {file_path}: {e}")
        
        return warnings
    
    def _validate_required_fields(self, config: Dict[str, Any], result: ValidationResult):
        """Validate required configuration fields."""
        for field, expected_type in self.required_fields.items():
            if field not in config:
                result.errors.append(f"Required field '{field}' is missing")
            elif config[field] is None:
                result.errors.append(f"Required field '{field}' cannot be None")
            elif isinstance(expected_type, tuple):
                # Multiple allowed types
                if not any(isinstance(config[field], t) for t in expected_type):
                    type_names = [t.__name__ for t in expected_type]
                    result.errors.append(f"Field '{field}' must be one of: {', '.join(type_names)}")
            elif not isinstance(config[field], expected_type):
                result.errors.append(f"Field '{field}' must be of type {expected_type.__name__}")
    
    def _validate_field_types(self, config: Dict[str, Any], result: ValidationResult):
        """Validate optional field types."""
        for field, expected_type in self.optional_fields.items():
            if field in config and config[field] is not None:
                if not isinstance(config[field], expected_type):
                    result.warnings.append(f"Field '{field}' should be of type {expected_type.__name__}")
    
    def _validate_webhook_url(self, webhook_url: Any, result: ValidationResult):
        """Validate webhook URL specifically."""
        if webhook_url:
            is_valid, error_msg = self.validate_webhook_url(webhook_url)
            if not is_valid:
                result.errors.append(f"Invalid webhook URL: {error_msg}")
    
    def _check_security_risks(self, config: Dict[str, Any], result: ValidationResult, config_file_path: Optional[str]):
        """Check for security risks in configuration."""
        security_warnings = self.check_security_risks(config, config_file_path)
        result.security_warnings.extend(security_warnings)
    
    def _validate_notifications_config(self, notifications: Dict[str, Any], result: ValidationResult):
        """Validate notifications configuration section."""
        if not isinstance(notifications, dict):
            result.warnings.append("'notifications' should be a dictionary")
            return
        
        # Validate username
        username = notifications.get('username')
        if username and not isinstance(username, str):
            result.warnings.append("notifications.username should be a string")
        
        # Validate avatar_url
        avatar_url = notifications.get('avatar_url')
        if avatar_url and not isinstance(avatar_url, str):
            result.warnings.append("notifications.avatar_url should be a string")
        elif avatar_url and not avatar_url.startswith('http'):
            result.warnings.append("notifications.avatar_url should be a valid URL")
    
    def _validate_filtering_config(self, filtering: Dict[str, Any], result: ValidationResult):
        """Validate filtering configuration section."""
        if not isinstance(filtering, dict):
            result.warnings.append("'filtering' should be a dictionary")
            return
        
        # Validate change_types
        change_types = filtering.get('change_types')
        if change_types and not isinstance(change_types, list):
            result.warnings.append("filtering.change_types should be a list")
        
        # Validate preset
        preset = filtering.get('preset')
        if preset and not isinstance(preset, str):
            result.warnings.append("filtering.preset should be a string")
        
        valid_presets = ['combat_only', 'level_up', 'roleplay_session', 'shopping_trip', 'minimal', 'debug']
        if preset and preset not in valid_presets:
            result.warnings.append(f"filtering.preset should be one of: {', '.join(valid_presets)}")
    
    def _validate_advanced_config(self, advanced: Dict[str, Any], result: ValidationResult):
        """Validate advanced configuration section."""
        if not isinstance(advanced, dict):
            result.warnings.append("'advanced' should be a dictionary")
            return
        
        # Validate numeric fields
        numeric_fields = {
            'max_changes_per_notification': (1, 100),
            'delay_between_messages': (0.1, 60.0),
            'error_retry_delay': (1, 300),
            'shutdown_check_interval': (1, 300)
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            value = advanced.get(field)
            if value is not None:
                if not isinstance(value, (int, float)):
                    result.warnings.append(f"advanced.{field} should be a number")
                elif value < min_val or value > max_val:
                    result.warnings.append(f"advanced.{field} should be between {min_val} and {max_val}")
    
    def _generate_suggestions(self, config: Dict[str, Any], result: ValidationResult):
        """Generate helpful suggestions for configuration improvement."""
        # Environment variable suggestions
        env_suggestions = self.suggest_environment_variables(config)
        if env_suggestions:
            result.suggestions.append("Consider using environment variables for:")
            result.suggestions.extend([f"  - {suggestion}" for suggestion in env_suggestions])
        
        # Performance suggestions
        check_interval = config.get('check_interval', 600)
        if check_interval < 300:
            result.suggestions.append("Consider increasing check_interval to reduce API calls (minimum recommended: 300 seconds)")
        
        # Security suggestions
        if not config.get('log_level'):
            result.suggestions.append("Set log_level to control logging verbosity (DEBUG, INFO, WARNING, ERROR)")
        
        # Configuration completeness
        if not config.get('notifications'):
            result.suggestions.append("Add 'notifications' section to customize Discord message appearance")
        
        if not config.get('filtering'):
            result.suggestions.append("Add 'filtering' section to control which changes trigger notifications")