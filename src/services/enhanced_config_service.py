"""
Enhanced Configuration Service

Service for managing enhanced change tracking configuration,
integrating with existing Discord configuration, and providing
runtime configuration updates.
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from dataclasses import asdict

from src.models.enhanced_config import (
    EnhancedChangeTrackingConfig,
    ConfigurationManager,
    ConfigurationError,
    ChangeTypeConfig,
    DetailLevel
)
from discord.services.change_detection.models import ChangePriority


class EnhancedConfigService:
    """Service for managing enhanced change tracking configuration."""
    
    def __init__(self, config_dir: Path = None):
        """Initialize configuration service."""
        self.config_dir = config_dir or Path("config")
        self.logger = logging.getLogger(__name__)
        
        # Configuration managers
        self.enhanced_config_manager = ConfigurationManager(
            self.config_dir / "enhanced_change_tracking.yaml"
        )
        self.discord_config_path = self.config_dir / "discord.yaml"
        
        # Cached configurations
        self._enhanced_config: Optional[EnhancedChangeTrackingConfig] = None
        self._discord_config: Optional[Dict[str, Any]] = None
        
    def load_configurations(self) -> EnhancedChangeTrackingConfig:
        """Load and merge all configurations."""
        # Load enhanced configuration
        self._enhanced_config = self.enhanced_config_manager.load_config()
        
        # Load Discord configuration for integration
        self._load_discord_config()
        
        # Integrate configurations
        self._integrate_with_discord_config()
        
        return self._enhanced_config
    
    def get_enhanced_config(self) -> EnhancedChangeTrackingConfig:
        """Get current enhanced configuration."""
        if self._enhanced_config is None:
            return self.load_configurations()
        return self._enhanced_config
    
    def update_change_type_config(self, change_type: str, updates: Dict[str, Any]) -> bool:
        """Update configuration for a specific change type."""
        try:
            config = self.get_enhanced_config()
            
            if change_type not in config.change_types:
                # Create new change type configuration
                config.change_types[change_type] = ChangeTypeConfig()
            
            # Apply updates
            type_config = config.change_types[change_type]
            for key, value in updates.items():
                if hasattr(type_config, key):
                    # Handle priority conversion
                    if key == 'priority' and isinstance(value, str):
                        value = ChangePriority[value.upper()]
                    setattr(type_config, key, value)
                else:
                    self.logger.warning(f"Unknown configuration key: {key}")
            
            # Save updated configuration
            return self.enhanced_config_manager.save_config(config)
            
        except Exception as e:
            self.logger.error(f"Error updating change type config: {e}")
            return False
    
    def enable_change_type(self, change_type: str, discord: bool = True, logging: bool = True) -> bool:
        """Enable a specific change type."""
        return self.update_change_type_config(change_type, {
            'enabled': True,
            'discord_enabled': discord,
            'log_enabled': logging
        })
    
    def disable_change_type(self, change_type: str) -> bool:
        """Disable a specific change type."""
        return self.update_change_type_config(change_type, {
            'enabled': False,
            'discord_enabled': False,
            'log_enabled': False
        })
    
    def set_change_type_priority(self, change_type: str, priority: ChangePriority) -> bool:
        """Set priority for a specific change type."""
        return self.update_change_type_config(change_type, {'priority': priority})
    
    def get_enabled_change_types(self) -> Set[str]:
        """Get all enabled change types."""
        config = self.get_enhanced_config()
        return config.get_enabled_change_types()
    
    def get_discord_enabled_change_types(self) -> Set[str]:
        """Get change types enabled for Discord notifications."""
        config = self.get_enhanced_config()
        return {
            change_type for change_type, type_config in config.change_types.items()
            if type_config.enabled and type_config.discord_enabled
        }
    
    def get_logging_enabled_change_types(self) -> Set[str]:
        """Get change types enabled for logging."""
        config = self.get_enhanced_config()
        return {
            change_type for change_type, type_config in config.change_types.items()
            if type_config.enabled and type_config.log_enabled
        }
    
    def is_change_type_enabled(self, change_type: str) -> bool:
        """Check if a change type is enabled."""
        config = self.get_enhanced_config()
        return config.is_change_type_enabled(change_type)
    
    def should_notify_discord(self, change_type: str, priority: ChangePriority) -> bool:
        """Check if a change should trigger Discord notification."""
        config = self.get_enhanced_config()
        
        # Check if Discord notifications are enabled globally
        if not config.discord.enabled:
            return False
        
        # Check if change type is enabled for Discord
        if not config.is_discord_enabled_for_change_type(change_type):
            return False
        
        # Check priority threshold
        if priority.value < config.discord.min_priority.value:
            return False
        
        return True
    
    def should_log_change(self, change_type: str) -> bool:
        """Check if a change should be logged."""
        config = self.get_enhanced_config()
        
        # Check if logging is enabled globally
        if not config.change_log.enabled:
            return False
        
        # Check if change type is enabled for logging
        return config.is_logging_enabled_for_change_type(change_type)
    
    def get_discord_detail_level(self) -> DetailLevel:
        """Get Discord notification detail level."""
        config = self.get_enhanced_config()
        return config.discord.detail_level
    
    def get_log_detail_level(self) -> DetailLevel:
        """Get change log detail level."""
        config = self.get_enhanced_config()
        return config.change_log.detail_level
    
    def update_discord_config(self, updates: Dict[str, Any]) -> bool:
        """Update Discord notification configuration."""
        try:
            config = self.get_enhanced_config()
            
            # Apply updates to Discord configuration
            for key, value in updates.items():
                if hasattr(config.discord, key):
                    # Handle enum conversions
                    if key == 'detail_level' and isinstance(value, str):
                        value = DetailLevel(value.lower())
                    elif key == 'min_priority' and isinstance(value, str):
                        value = ChangePriority[value.upper()]
                    
                    setattr(config.discord, key, value)
                else:
                    self.logger.warning(f"Unknown Discord config key: {key}")
            
            return self.enhanced_config_manager.save_config(config)
            
        except Exception as e:
            self.logger.error(f"Error updating Discord config: {e}")
            return False
    
    def update_change_log_config(self, updates: Dict[str, Any]) -> bool:
        """Update change log configuration."""
        try:
            config = self.get_enhanced_config()
            
            # Apply updates to change log configuration
            for key, value in updates.items():
                if hasattr(config.change_log, key):
                    # Handle special conversions
                    if key == 'storage_dir' and isinstance(value, str):
                        value = Path(value)
                    elif key == 'detail_level' and isinstance(value, str):
                        value = DetailLevel(value.lower())
                    
                    setattr(config.change_log, key, value)
                else:
                    self.logger.warning(f"Unknown change log config key: {key}")
            
            return self.enhanced_config_manager.save_config(config)
            
        except Exception as e:
            self.logger.error(f"Error updating change log config: {e}")
            return False
    
    def validate_configuration(self) -> List[str]:
        """Validate current configuration."""
        config = self.get_enhanced_config()
        return config.validate()
    
    def create_default_config(self) -> bool:
        """Create default configuration file."""
        from src.models.enhanced_config import create_default_config_file
        return create_default_config_file(self.enhanced_config_manager.config_path)
    
    def backup_configuration(self) -> Optional[Path]:
        """Create a backup of current configuration."""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.enhanced_config_manager.config_path.with_suffix(f'.backup.{timestamp}.yaml')
            
            config = self.get_enhanced_config()
            config_dict = self.enhanced_config_manager._config_to_dict(config)
            
            with open(backup_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Created configuration backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Error creating configuration backup: {e}")
            return None
    
    def restore_configuration(self, backup_path: Path) -> bool:
        """Restore configuration from backup."""
        try:
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            with open(backup_path, 'r') as f:
                data = yaml.safe_load(f)
            
            config = self.enhanced_config_manager._parse_config_data(data)
            
            # Validate restored configuration
            errors = config.validate()
            if errors:
                raise ConfigurationError(f"Restored configuration is invalid: {errors}")
            
            # Save restored configuration
            self._enhanced_config = config
            return self.enhanced_config_manager.save_config(config)
            
        except Exception as e:
            self.logger.error(f"Error restoring configuration: {e}")
            return False
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration."""
        config = self.get_enhanced_config()
        
        enabled_types = config.get_enabled_change_types()
        discord_types = self.get_discord_enabled_change_types()
        logging_types = self.get_logging_enabled_change_types()
        
        return {
            'enabled': config.enabled,
            'config_version': config.config_version,
            'total_change_types': len(config.change_types),
            'enabled_change_types': len(enabled_types),
            'discord_enabled_types': len(discord_types),
            'logging_enabled_types': len(logging_types),
            'change_log_enabled': config.change_log.enabled,
            'discord_enabled': config.discord.enabled,
            'causation_analysis_enabled': config.causation_analysis.enabled,
            'storage_directory': str(config.change_log.storage_dir),
            'retention_days': config.change_log.retention_days,
            'discord_detail_level': config.discord.detail_level.value,
            'log_detail_level': config.change_log.detail_level.value
        }
    
    def _load_discord_config(self):
        """Load Discord configuration for integration."""
        try:
            if self.discord_config_path.exists():
                with open(self.discord_config_path, 'r') as f:
                    self._discord_config = yaml.safe_load(f)
            else:
                self._discord_config = {}
        except Exception as e:
            self.logger.warning(f"Could not load Discord config: {e}")
            self._discord_config = {}
    
    def _integrate_with_discord_config(self):
        """Integrate enhanced config with existing Discord configuration."""
        if not self._discord_config:
            return
        
        # Integrate Discord advanced settings
        advanced = self._discord_config.get('advanced', {})
        if 'max_changes_per_notification' in advanced:
            self._enhanced_config.discord.max_changes_per_notification = advanced['max_changes_per_notification']
        
        # Check for legacy change type settings in Discord config
        filtering = self._discord_config.get('filtering', {})
        legacy_change_types = filtering.get('change_types', [])
        
        if legacy_change_types:
            self.logger.info("Found legacy change types in Discord config, integrating...")
            
            # Map legacy change types to enhanced change types
            legacy_mapping = {
                'feats': 'feats',
                'class_features': 'multiclass',
                'spells_known': 'spells',
                'inventory_items': 'inventory',
                'equipment': 'inventory',
                'background': 'background',
                'ability_scores': 'ability_scores',
                'proficiencies': 'proficiencies'
            }
            
            # Enable change types that were enabled in Discord config
            for legacy_type in legacy_change_types:
                enhanced_type = legacy_mapping.get(legacy_type)
                if enhanced_type and enhanced_type in self._enhanced_config.change_types:
                    self._enhanced_config.change_types[enhanced_type].enabled = True
                    self._enhanced_config.change_types[enhanced_type].discord_enabled = True
    
    def migrate_from_legacy_config(self) -> bool:
        """Migrate from legacy Discord-only configuration."""
        try:
            if not self._discord_config:
                return True  # Nothing to migrate
            
            # Create backup of current enhanced config
            backup_path = self.backup_configuration()
            if backup_path:
                self.logger.info(f"Created backup before migration: {backup_path}")
            
            # Perform migration
            self._integrate_with_discord_config()
            
            # Save migrated configuration
            success = self.enhanced_config_manager.save_config(self._enhanced_config)
            
            if success:
                self.logger.info("Successfully migrated from legacy configuration")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error during configuration migration: {e}")
            return False


# Global configuration service instance
_config_service: Optional[EnhancedConfigService] = None


def get_config_service(config_dir: Path = None) -> EnhancedConfigService:
    """Get global configuration service instance."""
    global _config_service
    if _config_service is None:
        _config_service = EnhancedConfigService(config_dir)
    return _config_service


def initialize_configuration(config_dir: Path = None) -> EnhancedChangeTrackingConfig:
    """Initialize and load configuration."""
    service = get_config_service(config_dir)
    return service.load_configurations()