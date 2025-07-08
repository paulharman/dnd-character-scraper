"""
Configuration settings for the D&D Beyond scraper.
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path

class Settings:
    """Configuration settings with environment variable support."""
    
    def __init__(self):
        """Initialize settings with defaults and environment overrides."""
        
        # API Configuration
        self.api_base_url = os.getenv('DNDBEYOND_API_BASE_URL', 'https://character-service.dndbeyond.com/character/v5/character')
        self.api_timeout = int(os.getenv('DNDBEYOND_API_TIMEOUT', '30'))
        self.api_retries = int(os.getenv('DNDBEYOND_API_RETRIES', '3'))
        self.api_retry_delay = float(os.getenv('DNDBEYOND_API_RETRY_DELAY', '30.0'))  # 30 second minimum
        self.user_agent = os.getenv('DNDBEYOND_USER_AGENT', 'DnDBeyond-Enhanced-Scraper/6.0.0')
        
        # Rate Limiting (respecting 30-second minimum)
        self.min_request_delay = float(os.getenv('DNDBEYOND_MIN_DELAY', '30.0'))  # 30 seconds minimum
        self.jitter_min = float(os.getenv('DNDBEYOND_JITTER_MIN', '0.5'))
        self.jitter_max = float(os.getenv('DNDBEYOND_JITTER_MAX', '2.0'))
        
        # Validation Settings
        self.enable_strict_validation = os.getenv('DNDBEYOND_STRICT_VALIDATION', 'true').lower() == 'true'
        self.validation_timeout = float(os.getenv('DNDBEYOND_VALIDATION_TIMEOUT', '5.0'))
        
        # Cache Settings
        self.enable_cache = os.getenv('DNDBEYOND_ENABLE_CACHE', 'true').lower() == 'true'
        self.cache_ttl = int(os.getenv('DNDBEYOND_CACHE_TTL', '3600'))  # 1 hour
        self.cache_size = int(os.getenv('DNDBEYOND_CACHE_SIZE', '100'))
        
        # Logging
        self.log_level = os.getenv('DNDBEYOND_LOG_LEVEL', 'INFO')
        self.enable_debug = os.getenv('DNDBEYOND_DEBUG', 'false').lower() == 'true'
        
        # Output Settings
        self.default_output_format = os.getenv('DNDBEYOND_OUTPUT_FORMAT', 'json')
        self.preserve_html = os.getenv('DNDBEYOND_PRESERVE_HTML', 'false').lower() == 'true'
        
        # Rule Version Settings
        self.default_rule_version = os.getenv('DNDBEYOND_DEFAULT_RULES', 'auto')  # auto, 2014, 2024
        self.conservative_detection = os.getenv('DNDBEYOND_CONSERVATIVE_DETECTION', 'true').lower() == 'true'
        
        # File Paths
        self.config_dir = Path(os.getenv('DNDBEYOND_CONFIG_DIR', './config'))
        self.spells_dir = Path(os.getenv('DNDBEYOND_SPELLS_DIR', './obsidian/spells'))
        self.data_dir = Path(os.getenv('DNDBEYOND_DATA_DIR', './data'))
        
    def get_api_config(self) -> Dict[str, Any]:
        """Get API-specific configuration."""
        return {
            'base_url': self.api_base_url,
            'timeout': self.api_timeout,
            'retries': self.api_retries,
            'retry_delay': self.api_retry_delay,
            'user_agent': self.user_agent,
            'min_delay': self.min_request_delay,
            'jitter_min': self.jitter_min,
            'jitter_max': self.jitter_max
        }
    
    def get_validation_config(self) -> Dict[str, Any]:
        """Get validation-specific configuration."""
        return {
            'strict_validation': self.enable_strict_validation,
            'timeout': self.validation_timeout
        }
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache-specific configuration."""
        return {
            'enabled': self.enable_cache,
            'ttl': self.cache_ttl,
            'size': self.cache_size
        }
    
    def get_rule_config(self) -> Dict[str, Any]:
        """Get rule version configuration."""
        return {
            'default_version': self.default_rule_version,
            'conservative_detection': self.conservative_detection
        }
    
    def update_from_dict(self, config_dict: Dict[str, Any]):
        """Update settings from a configuration dictionary."""
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            'api': self.get_api_config(),
            'validation': self.get_validation_config(),
            'cache': self.get_cache_config(),
            'rules': self.get_rule_config(),
            'logging': {
                'level': self.log_level,
                'debug': self.enable_debug
            },
            'output': {
                'format': self.default_output_format,
                'preserve_html': self.preserve_html
            },
            'paths': {
                'config_dir': str(self.config_dir),
                'spells_dir': str(self.spells_dir),
                'data_dir': str(self.data_dir)
            }
        }