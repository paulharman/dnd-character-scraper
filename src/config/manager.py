"""
Configuration Manager for D&D Beyond Character Scraper.

Handles loading, merging, and managing configuration from multiple sources:
- YAML configuration files
- Environment variables  
- Command line arguments
- Default values
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field

from .schemas import (
    AppConfig, 
    GameConstantsConfig, 
    RuleSpecificConfig,
    EnvironmentConfig
)


@dataclass
class ConfigPaths:
    """Configuration file paths for organized structure."""
    config_dir: Path = field(default_factory=lambda: Path("config"))
    main_config: Path = field(default_factory=lambda: Path("config/main.yaml"))
    scraper_config: Path = field(default_factory=lambda: Path("config/scraper.yaml"))
    discord_config: Path = field(default_factory=lambda: Path("config/discord.yaml"))
    parser_config: Path = field(default_factory=lambda: Path("config/parser.yaml"))
    constants_config: Path = field(default_factory=lambda: Path("config/rules/constants.yaml"))
    rules_2014: Path = field(default_factory=lambda: Path("config/rules/2014.yaml"))
    rules_2024: Path = field(default_factory=lambda: Path("config/rules/2024.yaml"))
    
    def __post_init__(self):
        """Resolve paths relative to project root."""
        # Find project root (where config/ directory is located)
        current = Path.cwd()
        while not (current / "config").exists() and current != current.parent:
            current = current.parent
            
        if (current / "config").exists():
            self.config_dir = current / "config"
        else:
            # Fallback to current directory
            self.config_dir = Path("config")
            
        # Update all paths relative to config directory
        self.main_config = self.config_dir / "main.yaml"
        self.scraper_config = self.config_dir / "scraper.yaml"
        self.discord_config = self.config_dir / "discord.yaml"
        self.parser_config = self.config_dir / "parser.yaml"
        self.constants_config = self.config_dir / "rules" / "constants.yaml"
        self.rules_2014 = self.config_dir / "rules" / "2014.yaml"
        self.rules_2024 = self.config_dir / "rules" / "2024.yaml"


class ConfigManager:
    """
    Configuration manager with support for:
    - YAML file loading
    - Environment variable overrides
    - Configuration validation
    - Environment-specific configurations
    """
    
    def __init__(self, environment: Optional[str] = None, config_dir: Optional[str] = None):
        self.environment = environment or os.getenv("DNDBS_ENVIRONMENT", "production")
        self.paths = ConfigPaths()
        
        if config_dir:
            self.paths.config_dir = Path(config_dir)
            
        self._app_config: Optional[AppConfig] = None
        self._constants_config: Optional[GameConstantsConfig] = None
        self._rules_2014_config: Optional[RuleSpecificConfig] = None
        self._rules_2024_config: Optional[RuleSpecificConfig] = None
        
    def load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse a YAML configuration file."""
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {file_path}")
                
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            if data is None:
                return {}
                
            return data
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {file_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading {file_path}: {e}")
    
    def apply_environment_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration."""
        # Environment variable prefix
        prefix = "DNDBS_"
        
        # Common environment variable mappings
        env_mappings = {
            f"{prefix}API_TIMEOUT": ("api", "timeout"),
            f"{prefix}API_MAX_RETRIES": ("api", "max_retries"),
            f"{prefix}API_USER_AGENT": ("api", "user_agent"),
            f"{prefix}API_BASE_URL": ("api", "base_url"),
            f"{prefix}OUTPUT_VERBOSE": ("output", "verbose"),  
            f"{prefix}OUTPUT_INCLUDE_RAW": ("output", "include_raw_data"),
            f"{prefix}OUTPUT_FORMAT": ("output", "format"),
            f"{prefix}LOG_LEVEL": ("logging", "level"),
            f"{prefix}LOG_TO_FILE": ("logging", "log_to_file"),
            f"{prefix}LOG_FILE_PATH": ("logging", "log_file_path"),
        }
        
        # Apply environment overrides
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                elif value.replace('.', '').isdigit():
                    value = float(value)
                
                # Set the value in config
                if section not in config_data:
                    config_data[section] = {}
                config_data[section][key] = value
        
        return config_data
    
    def merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries."""
        merged = base.copy()
        
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self.merge_configs(merged[key], value)
            else:
                merged[key] = value
                
        return merged
    
    def load_environment_config(self, environment: str) -> Dict[str, Any]:
        """Load environment-specific configuration."""
        env_config_path = self.paths.config_dir / "environments" / f"{environment}.yaml"
        
        if env_config_path.exists():
            return self.load_yaml_file(env_config_path)
        else:
            # Return empty config if environment file doesn't exist
            return {}
    
    def get_app_config(self) -> AppConfig:
        """Get the main application configuration from organized structure."""
        if self._app_config is None:
            # Load configuration from organized structure
            config_data = self._load_organized_config()
            
            # Load environment-specific overrides
            env_config = self.load_environment_config(self.environment)
            if env_config:
                config_data = self.merge_configs(config_data, env_config)
            
            # Apply environment variable overrides
            config_data = self.apply_environment_overrides(config_data)
            
            # Validate and create configuration object
            self._app_config = AppConfig(**config_data)
            
        return self._app_config
    
    def _load_organized_config(self) -> Dict[str, Any]:
        """Load configuration from organized structure (main.yaml, scraper.yaml, discord.yaml, parser.yaml)."""
        # Start with main config as base
        config_data = self.load_yaml_file(self.paths.main_config)
        
        # Load and merge scraper config
        if self.paths.scraper_config.exists():
            scraper_config = self.load_yaml_file(self.paths.scraper_config)
            # Merge scraper config under 'api' section and other relevant sections
            if 'api' in scraper_config:
                if 'api' not in config_data:
                    config_data['api'] = {}
                config_data['api'].update(scraper_config['api'])
            
            # Merge calculations, output, error_handling, testing, batch_processing, rate_limit
            for section in ['calculations', 'output', 'error_handling', 'testing', 'batch_processing', 'rate_limit']:
                if section in scraper_config:
                    config_data[section] = scraper_config[section]
        
        # Load and merge Discord config
        if self.paths.discord_config.exists():
            discord_config = self.load_yaml_file(self.paths.discord_config)
            # Extract main Discord settings and merge under 'discord' section
            discord_data = {}
            
            # Map top-level Discord settings to discord section
            discord_settings = ['enabled', 'webhook_url', 'username', 'avatar_url', 'create_snapshots', 
                              'notify_on_save', 'config_file', 'format_type', 'min_priority', 'change_types']
            for setting in discord_settings:
                if setting in discord_config:
                    discord_data[setting] = discord_config[setting]
            
            # Handle nested structures
            if 'rate_limit' in discord_config:
                discord_data['rate_limit'] = discord_config['rate_limit']
            if 'messages' in discord_config:
                discord_data['messages'] = discord_config['messages']
            if 'legacy' in discord_config:
                discord_data['legacy'] = discord_config['legacy']
            
            config_data['discord'] = discord_data
        
        # Load and merge parser config (for future parser integration)
        if self.paths.parser_config.exists():
            parser_config = self.load_yaml_file(self.paths.parser_config)
            # Parser config can be stored under a 'parser' section for future use
            config_data['parser'] = parser_config.get('parser', {})
        
        # Apply project-wide settings from main config
        if 'project' in config_data:
            # Project config is already loaded from main.yaml
            pass
        
        # Apply global settings from main config
        if 'paths' in config_data:
            config_data['paths'] = config_data['paths']
        
        if 'logging' in config_data:
            config_data['logging'] = config_data['logging']
        
        if 'features' in config_data:
            config_data['features'] = config_data['features']
        
        if 'performance' in config_data:
            config_data['performance'] = config_data['performance']
        
        if 'environments' in config_data:
            config_data['environments'] = config_data['environments']
        
        return config_data
    
    def get_constants_config(self) -> GameConstantsConfig:
        """Get the game constants configuration."""
        if self._constants_config is None:
            config_data = self.load_yaml_file(self.paths.constants_config)
            self._constants_config = GameConstantsConfig(**config_data)
            
        return self._constants_config
    
    def get_rules_config(self, rule_version: str) -> RuleSpecificConfig:
        """Get rule-specific configuration (2014 or 2024)."""
        if rule_version == "2014":
            if self._rules_2014_config is None:
                config_data = self.load_yaml_file(self.paths.rules_2014)
                self._rules_2014_config = RuleSpecificConfig(**config_data)
            return self._rules_2014_config
            
        elif rule_version == "2024":
            if self._rules_2024_config is None:
                config_data = self.load_yaml_file(self.paths.rules_2024)
                self._rules_2024_config = RuleSpecificConfig(**config_data)
            return self._rules_2024_config
            
        else:
            raise ValueError(f"Unknown rule version: {rule_version}. Use '2014' or '2024'")
    
    def get_config_value(self, *keys: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation."""
        config = self.get_app_config()
        
        current = config.dict()
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
                
        return current
    
    def set_setting(self, setting_path: str, value: Any) -> None:
        """
        Set a configuration setting at runtime.
        
        Args:
            setting_path: Dot-separated path to setting (e.g., 'output.clean_html')
            value: Value to set
        """
        # Split the path and set the value in the app config
        keys = setting_path.split('.')
        config = self.get_app_config()
        config_dict = config.dict()
        
        # Navigate to the parent dictionary
        current = config_dict
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
        
        # Recreate the config object with updated values
        self._app_config = AppConfig(**config_dict)
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate all configuration and return validation results."""
        results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Validate main config
            app_config = self.get_app_config()
            
            # Validate constants config
            constants_config = self.get_constants_config()
            
            # Validate rule configs
            rules_2014 = self.get_rules_config("2014")
            rules_2024 = self.get_rules_config("2024")
            
            # Check for required files in organized structure
            required_files = [
                self.paths.main_config,
                self.paths.scraper_config,
                self.paths.discord_config,
                self.paths.constants_config,
                self.paths.rules_2014,
                self.paths.rules_2024
            ]
            
            for file_path in required_files:
                if not file_path.exists():
                    results["errors"].append(f"Required config file missing: {file_path}")
                    results["valid"] = False
            
            # Check environment-specific config
            env_config_path = self.paths.config_dir / "environments" / f"{self.environment}.yaml"
            if not env_config_path.exists():
                results["warnings"].append(f"Environment config not found: {env_config_path}")
                
        except Exception as e:
            results["valid"] = False
            results["errors"].append(f"Configuration validation error: {str(e)}")
            
        return results
    
    def reload_config(self):
        """Reload all configuration from files."""
        self._app_config = None
        self._constants_config = None
        self._rules_2014_config = None
        self._rules_2024_config = None
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration."""
        config = self.get_app_config()
        
        return {
            "environment": self.environment,
            "project": {
                "name": config.project.name,
                "version": config.project.version
            },
            "api": {
                "base_url": config.api.base_url,
                "timeout": config.api.timeout,
                "max_retries": config.api.max_retries
            },
            "output": {
                "verbose": config.output.verbose,
                "format": config.output.format
            },
            "config_files": {
                "main": str(self.paths.main_config),
                "scraper": str(self.paths.scraper_config),
                "discord": str(self.paths.discord_config),
                "parser": str(self.paths.parser_config),
                "constants": str(self.paths.constants_config),
                "environment": str(self.paths.config_dir / "environments" / f"{self.environment}.yaml")
            }
        }


# Singleton instance for global access
_config_manager: Optional[ConfigManager] = None


def get_config_manager(environment: Optional[str] = None, config_dir: Optional[str] = None) -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager(environment=environment, config_dir=config_dir)
    
    return _config_manager


def reset_config_manager():
    """Reset the global configuration manager (useful for testing)."""
    global _config_manager
    _config_manager = None