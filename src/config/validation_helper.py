"""
Configuration validation helper with user-friendly error messages.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml
from pydantic import ValidationError


class ConfigurationValidationError(Exception):
    """Custom exception for configuration validation errors."""
    
    def __init__(self, message: str, suggestions: List[str] = None):
        self.message = message
        self.suggestions = suggestions or []
        super().__init__(message)


class ConfigurationValidator:
    """Provides user-friendly configuration validation with helpful error messages."""
    
    def __init__(self):
        self.common_fixes = {
            'webhook_url': [
                "Set the DISCORD_WEBHOOK_URL environment variable",
                "Get webhook URL from Discord: Server Settings > Integrations > Webhooks",
                "Example: export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/..."
            ],
            'character_id': [
                "Find your character ID in the D&D Beyond URL",
                "Example: dndbeyond.com/characters/145081718 → character_id: 145081718",
                "Make sure it's a number, not a string"
            ],
            'logging.level': [
                "Use one of: DEBUG, INFO, WARNING, ERROR, CRITICAL",
                "DEBUG = verbose (development), INFO = standard (production)",
                "Case sensitive - use uppercase"
            ],
            'min_priority': [
                "Use one of: LOW, MEDIUM, HIGH, CRITICAL",
                "LOW = all changes, MEDIUM = important changes, HIGH = critical only",
                "Case sensitive - use uppercase"
            ],
            'storage_directory': [
                "Ensure the directory exists and is writable",
                "Use forward slashes even on Windows: character_data/logs",
                "Relative paths are relative to the project root"
            ]
        }
    
    def validate_config_file(self, config_path: Path) -> List[str]:
        """
        Validate a configuration file and return user-friendly error messages.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            List of validation error messages with suggestions
        """
        errors = []
        
        try:
            # Check if file exists
            if not config_path.exists():
                errors.append(f"Configuration file not found: {config_path}")
                return errors
            
            # Try to parse YAML
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                errors.append(f"Invalid YAML syntax in {config_path}: {e}")
                errors.append("Check for proper indentation and syntax")
                return errors
            
            # Validate specific configuration files
            if config_path.name == 'discord.yaml':
                errors.extend(self._validate_discord_config(config_data))
            elif config_path.name == 'main.yaml':
                errors.extend(self._validate_main_config(config_data))
            
        except Exception as e:
            errors.append(f"Unexpected error validating {config_path}: {e}")
        
        return errors
    
    def _validate_discord_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate Discord configuration with helpful error messages."""
        errors = []
        
        # Check required fields
        if 'webhook_url' not in config:
            errors.append("Missing required field: webhook_url")
            errors.extend([f"  → {fix}" for fix in self.common_fixes['webhook_url']])
        elif config['webhook_url'] == '${DISCORD_WEBHOOK_URL}':
            # Check if environment variable is set
            if not os.getenv('DISCORD_WEBHOOK_URL'):
                errors.append("DISCORD_WEBHOOK_URL environment variable not set")
                errors.extend([f"  → {fix}" for fix in self.common_fixes['webhook_url']])
        
        if 'character_id' not in config:
            errors.append("Missing required field: character_id")
            errors.extend([f"  → {fix}" for fix in self.common_fixes['character_id']])
        elif not isinstance(config['character_id'], int):
            errors.append(f"character_id must be a number, got: {type(config['character_id']).__name__}")
            errors.extend([f"  → {fix}" for fix in self.common_fixes['character_id']])
        
        # Check Discord section
        discord_config = config.get('discord', {})
        if 'min_priority' in discord_config:
            priority = discord_config['min_priority']
            valid_priorities = {'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'}
            if priority not in valid_priorities:
                errors.append(f"Invalid min_priority: {priority}")
                errors.extend([f"  → {fix}" for fix in self.common_fixes['min_priority']])
        
        # Check storage directory
        if 'storage_directory' in config:
            storage_dir = Path(config['storage_directory'])
            if not storage_dir.exists():
                errors.append(f"Storage directory does not exist: {storage_dir}")
                errors.extend([f"  → {fix}" for fix in self.common_fixes['storage_directory']])
        
        # Check time values
        if 'check_interval_seconds' in config:
            interval = config['check_interval_seconds']
            if not isinstance(interval, (int, float)) or interval <= 0:
                errors.append(f"check_interval_seconds must be a positive number, got: {interval}")
                errors.append("  → Recommended: 300-1800 seconds (5-30 minutes)")
            elif interval < 60:
                errors.append(f"check_interval_seconds is very low ({interval}s), may cause rate limiting")
                errors.append("  → Recommended minimum: 300 seconds (5 minutes)")
        
        return errors
    
    def _validate_main_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate main configuration with helpful error messages."""
        errors = []
        
        # Check environment
        if 'environment' in config:
            env = config['environment']
            valid_envs = {'development', 'testing', 'production'}
            if env not in valid_envs:
                errors.append(f"Invalid environment: {env}")
                errors.append(f"  → Valid options: {', '.join(sorted(valid_envs))}")
        
        # Check logging level
        logging_config = config.get('logging', {})
        if 'level' in logging_config:
            level = logging_config['level']
            valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
            if level not in valid_levels:
                errors.append(f"Invalid logging level: {level}")
                errors.extend([f"  → {fix}" for fix in self.common_fixes['logging.level']])
        
        # Check paths
        paths_config = config.get('paths', {})
        for path_name, path_value in paths_config.items():
            if not isinstance(path_value, str):
                errors.append(f"Path {path_name} must be a string, got: {type(path_value).__name__}")
                continue
            
            path = Path(path_value)
            if path.is_absolute():
                errors.append(f"Path {path_name} should be relative to project root: {path_value}")
                errors.append("  → Use relative paths like 'character_data' instead of absolute paths")
        
        return errors
    
    def format_validation_errors(self, errors: List[str], config_file: str) -> str:
        """Format validation errors into a user-friendly message."""
        if not errors:
            return f"✅ {config_file} configuration is valid"
        
        message = f"❌ Configuration errors in {config_file}:\n\n"
        for i, error in enumerate(errors, 1):
            if error.startswith('  →'):
                message += f"{error}\n"
            else:
                message += f"{i}. {error}\n"
        
        message += "\n💡 For more help, see docs/configuration_guide.md"
        return message
    
    def validate_all_configs(self, config_dir: Path = None) -> Dict[str, List[str]]:
        """
        Validate all configuration files and return results.
        
        Args:
            config_dir: Directory containing configuration files
            
        Returns:
            Dictionary mapping config file names to lists of error messages
        """
        if config_dir is None:
            config_dir = Path('config')
        
        results = {}
        config_files = ['main.yaml', 'discord.yaml', 'parser.yaml', 'scraper.yaml']
        
        for config_file in config_files:
            config_path = config_dir / config_file
            if config_path.exists():
                results[config_file] = self.validate_config_file(config_path)
            else:
                results[config_file] = [f"Configuration file not found: {config_path}"]
        
        return results
    
    def print_validation_summary(self, results: Dict[str, List[str]]):
        """Print a summary of validation results."""
        print("Configuration Validation Summary")
        print("=" * 40)
        
        total_errors = 0
        for config_file, errors in results.items():
            total_errors += len(errors)
            if errors:
                print(f"\n{self.format_validation_errors(errors, config_file)}")
            else:
                print(f"✅ {config_file}: No errors")
        
        print("\n" + "=" * 40)
        if total_errors == 0:
            print("🎉 All configurations are valid!")
        else:
            print(f"❌ Found {total_errors} configuration errors")
            print("📖 See docs/configuration_guide.md for help")


def main():
    """Command-line interface for configuration validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate configuration files')
    parser.add_argument('--config-dir', type=Path, default=Path('config'),
                       help='Directory containing configuration files')
    parser.add_argument('--file', type=str, help='Validate specific configuration file')
    
    args = parser.parse_args()
    
    validator = ConfigurationValidator()
    
    if args.file:
        # Validate specific file
        config_path = args.config_dir / args.file
        errors = validator.validate_config_file(config_path)
        print(validator.format_validation_errors(errors, args.file))
    else:
        # Validate all files
        results = validator.validate_all_configs(args.config_dir)
        validator.print_validation_summary(results)


if __name__ == '__main__':
    main()