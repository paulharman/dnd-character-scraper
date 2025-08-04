"""
Enhanced Configuration Management

Comprehensive configuration system for enhanced Discord change tracking.
Supports enabling/disabling specific change types, change log settings,
validation, and configuration migration.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Set, Union
from pathlib import Path
import yaml
import logging
from datetime import datetime

from discord.services.change_detection.models import ChangePriority


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass


class DetailLevel(Enum):
    """Detail levels for notifications and logging."""
    BRIEF = "brief"
    SUMMARY = "summary"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


@dataclass
class ChangeTypeConfig:
    """Configuration for individual change types."""
    enabled: bool = True
    priority: Optional[ChangePriority] = None
    discord_enabled: bool = True
    log_enabled: bool = True
    causation_analysis: bool = True
    
    def __post_init__(self):
        """Validate configuration values."""
        if self.priority is not None and not isinstance(self.priority, ChangePriority):
            if isinstance(self.priority, str):
                try:
                    self.priority = ChangePriority[self.priority.upper()]
                except KeyError:
                    raise ConfigurationError(f"Invalid priority: {self.priority}")


@dataclass
class ChangeLogConfig:
    """Configuration for change logging system."""
    enabled: bool = True
    storage_dir: Union[str, Path] = "character_data/change_logs"
    retention_days: int = 365
    rotation_size_mb: int = 10
    backup_old_logs: bool = True
    detail_level: DetailLevel = DetailLevel.COMPREHENSIVE
    
    # Performance settings
    max_entries_per_batch: int = 100
    enable_compression: bool = False  # FUTURE FEATURE: Planned for implementation (see compression_feature_plan.md)
    
    # Feature toggles
    enable_causation_analysis: bool = True
    enable_detailed_descriptions: bool = True
    
    def __post_init__(self):
        """Validate and normalize configuration."""
        if isinstance(self.storage_dir, str):
            self.storage_dir = Path(self.storage_dir)
        
        if isinstance(self.detail_level, str):
            try:
                self.detail_level = DetailLevel(self.detail_level.lower())
            except ValueError:
                raise ConfigurationError(f"Invalid detail level: {self.detail_level}")
        
        if self.retention_days <= 0:
            raise ConfigurationError("retention_days must be positive")
        
        if self.rotation_size_mb <= 0:
            raise ConfigurationError("rotation_size_mb must be positive")
        
        if self.max_entries_per_batch <= 0:
            raise ConfigurationError("max_entries_per_batch must be positive")


@dataclass
class DiscordNotificationConfig:
    """Configuration for Discord notifications."""
    enabled: bool = True
    detail_level: DetailLevel = DetailLevel.SUMMARY
    include_attribution: bool = True
    include_causation: bool = True
    
    # Priority filtering
    min_priority: ChangePriority = ChangePriority.LOW
    max_changes_per_notification: int = 200
    
    # Notification behavior
    notify_on_causation_detected: bool = True
    group_related_changes: bool = True
    
    def __post_init__(self):
        """Validate configuration values."""
        if isinstance(self.detail_level, str):
            try:
                self.detail_level = DetailLevel(self.detail_level.lower())
            except ValueError:
                raise ConfigurationError(f"Invalid detail level: {self.detail_level}")
        
        if isinstance(self.min_priority, str):
            try:
                self.min_priority = ChangePriority[self.min_priority.upper()]
            except KeyError:
                raise ConfigurationError(f"Invalid priority: {self.min_priority}")
        
        if self.max_changes_per_notification <= 0:
            raise ConfigurationError("max_changes_per_notification must be positive")


@dataclass
class CausationAnalysisConfig:
    """Configuration for causation analysis system."""
    enabled: bool = True
    confidence_threshold: float = 0.7
    max_cascade_depth: int = 3
    
    # Analysis features
    detect_feat_causation: bool = True
    detect_level_progression: bool = True
    detect_equipment_causation: bool = True
    detect_ability_score_cascades: bool = True
    
    # Performance settings
    analysis_timeout_seconds: int = 30
    cache_analysis_results: bool = True
    
    def __post_init__(self):
        """Validate configuration values."""
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ConfigurationError("confidence_threshold must be between 0.0 and 1.0")
        
        if self.max_cascade_depth < 0:
            raise ConfigurationError("max_cascade_depth must be non-negative")
        
        if self.analysis_timeout_seconds <= 0:
            raise ConfigurationError("analysis_timeout_seconds must be positive")


@dataclass
class EnhancedChangeTrackingConfig:
    """Main configuration for enhanced change tracking system."""
    # Change type configurations
    change_types: Dict[str, ChangeTypeConfig] = field(default_factory=dict)
    
    # Sub-configurations
    change_log: ChangeLogConfig = field(default_factory=ChangeLogConfig)
    discord: DiscordNotificationConfig = field(default_factory=DiscordNotificationConfig)
    causation_analysis: CausationAnalysisConfig = field(default_factory=CausationAnalysisConfig)
    
    # Global settings
    enabled: bool = True
    detect_minor_changes: bool = False
    detect_metadata_changes: bool = False
    detect_cosmetic_changes: bool = False
    
    # Migration settings
    config_version: str = "1.0"
    migration_backup: bool = True
    
    def __post_init__(self):
        """Initialize default change type configurations."""
        if not self.change_types:
            self._initialize_default_change_types()
    
    def _initialize_default_change_types(self):
        """Initialize default configurations for all change types."""
        default_change_types = {
            'feats': ChangeTypeConfig(enabled=True, priority=ChangePriority.HIGH),
            'subclass': ChangeTypeConfig(enabled=True, priority=ChangePriority.HIGH),
            'spells': ChangeTypeConfig(enabled=True, priority=ChangePriority.MEDIUM),
            'inventory': ChangeTypeConfig(enabled=True, priority=ChangePriority.MEDIUM),
            'background': ChangeTypeConfig(enabled=True, priority=ChangePriority.HIGH),
            'max_hp': ChangeTypeConfig(enabled=True, priority=ChangePriority.MEDIUM),
            'proficiencies': ChangeTypeConfig(enabled=True, priority=ChangePriority.MEDIUM),
            'ability_scores': ChangeTypeConfig(enabled=True, priority=ChangePriority.HIGH),
            'race_species': ChangeTypeConfig(enabled=True, priority=ChangePriority.HIGH),
            'multiclass': ChangeTypeConfig(enabled=True, priority=ChangePriority.HIGH),
            'personality': ChangeTypeConfig(enabled=False, priority=ChangePriority.LOW),
            'spellcasting_stats': ChangeTypeConfig(enabled=True, priority=ChangePriority.MEDIUM),
            'initiative': ChangeTypeConfig(enabled=True, priority=ChangePriority.MEDIUM),
            'passive_skills': ChangeTypeConfig(enabled=False, priority=ChangePriority.LOW),
            'alignment': ChangeTypeConfig(enabled=True, priority=ChangePriority.MEDIUM),
            'size': ChangeTypeConfig(enabled=True, priority=ChangePriority.MEDIUM),
            'movement_speed': ChangeTypeConfig(enabled=False, priority=ChangePriority.LOW)
        }
        
        for change_type, config in default_change_types.items():
            if change_type not in self.change_types:
                self.change_types[change_type] = config
    
    def is_change_type_enabled(self, change_type: str) -> bool:
        """Check if a specific change type is enabled."""
        if not self.enabled:
            return False
        
        config = self.change_types.get(change_type)
        return config.enabled if config else False
    
    def is_discord_enabled_for_change_type(self, change_type: str) -> bool:
        """Check if Discord notifications are enabled for a change type."""
        if not self.discord.enabled:
            return False
        
        config = self.change_types.get(change_type)
        return config.discord_enabled if config else False
    
    def is_logging_enabled_for_change_type(self, change_type: str) -> bool:
        """Check if logging is enabled for a change type."""
        if not self.change_log.enabled:
            return False
        
        config = self.change_types.get(change_type)
        return config.log_enabled if config else False
    
    def get_priority_for_change_type(self, change_type: str) -> ChangePriority:
        """Get the priority for a specific change type."""
        config = self.change_types.get(change_type)
        return config.priority if config and config.priority else ChangePriority.MEDIUM
    
    def get_enabled_change_types(self) -> Set[str]:
        """Get all enabled change types."""
        return {
            change_type for change_type, config in self.change_types.items()
            if config.enabled
        }
    
    def validate(self) -> List[str]:
        """Validate the entire configuration."""
        errors = []
        
        # Validate change log storage directory
        try:
            self.change_log.storage_dir.mkdir(parents=True, exist_ok=True)
            if not self.change_log.storage_dir.is_dir():
                errors.append(f"Storage directory is not a directory: {self.change_log.storage_dir}")
        except Exception as e:
            errors.append(f"Cannot create storage directory: {e}")
        
        # Validate change type configurations
        valid_change_types = {
            'feats', 'subclass', 'spells', 'inventory', 'background', 
            'max_hp', 'proficiencies', 'ability_scores', 'race_species',
            'multiclass', 'personality', 'spellcasting_stats', 'initiative',
            'passive_skills', 'alignment', 'size', 'movement_speed'
        }
        
        invalid_types = set(self.change_types.keys()) - valid_change_types
        if invalid_types:
            errors.append(f"Invalid change types: {invalid_types}")
        
        # Validate individual change type configs
        for change_type, config in self.change_types.items():
            try:
                # This will trigger validation in __post_init__
                ChangeTypeConfig(**config.__dict__)
            except ConfigurationError as e:
                errors.append(f"Invalid config for {change_type}: {e}")
        
        return errors


class ConfigurationManager:
    """Manages loading, saving, and migration of enhanced change tracking configuration."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager."""
        self.config_path = config_path or Path("config/enhanced_change_tracking.yaml")
        self.logger = logging.getLogger(__name__)
        self._config: Optional[EnhancedChangeTrackingConfig] = None
    
    def load_config(self) -> EnhancedChangeTrackingConfig:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = yaml.safe_load(f)
                
                # Check if migration is needed
                if self._needs_migration(data):
                    data = self._migrate_config(data)
                
                self._config = self._parse_config_data(data)
                self.logger.info(f"Loaded configuration from {self.config_path}")
                
            except Exception as e:
                self.logger.error(f"Error loading configuration: {e}")
                self.logger.info("Using default configuration")
                self._config = EnhancedChangeTrackingConfig()
        else:
            self.logger.info("Configuration file not found, creating default")
            self._config = EnhancedChangeTrackingConfig()
            self.save_config()
        
        # Validate configuration
        errors = self._config.validate()
        if errors:
            error_msg = f"Configuration validation failed: {errors}"
            self.logger.error(error_msg)
            raise ConfigurationError(error_msg)
        
        return self._config
    
    def save_config(self, config: Optional[EnhancedChangeTrackingConfig] = None) -> bool:
        """Save configuration to file."""
        if config is None:
            config = self._config
        
        if config is None:
            raise ValueError("No configuration to save")
        
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to dictionary for YAML serialization
            config_dict = self._config_to_dict(config)
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Saved configuration to {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False
    
    def get_config(self) -> EnhancedChangeTrackingConfig:
        """Get current configuration, loading if necessary."""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values."""
        if self._config is None:
            self.load_config()
        
        try:
            # Apply updates to configuration
            self._apply_config_updates(self._config, updates)
            
            # Validate updated configuration
            errors = self._config.validate()
            if errors:
                raise ConfigurationError(f"Updated configuration is invalid: {errors}")
            
            # Save updated configuration
            return self.save_config()
            
        except Exception as e:
            self.logger.error(f"Error updating configuration: {e}")
            return False
    
    def _needs_migration(self, data: Dict[str, Any]) -> bool:
        """Check if configuration needs migration."""
        current_version = data.get('config_version', '0.0')
        return current_version != "1.0"
    
    def _migrate_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate configuration from older versions."""
        current_version = data.get('config_version', '0.0')
        
        # Backup original configuration if requested
        if data.get('migration_backup', True):
            backup_path = self.config_path.with_suffix(f'.backup.{current_version}.yaml')
            try:
                with open(backup_path, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False, indent=2)
                self.logger.info(f"Created configuration backup: {backup_path}")
            except Exception as e:
                self.logger.warning(f"Could not create backup: {e}")
        
        # Perform migration based on version
        if current_version == '0.0':
            data = self._migrate_from_v0_to_v1(data)
        
        data['config_version'] = '1.0'
        self.logger.info(f"Migrated configuration from {current_version} to 1.0")
        
        return data
    
    def _migrate_from_v0_to_v1(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from legacy configuration format to v1.0."""
        migrated = {
            'enabled': data.get('enabled', True),
            'config_version': '1.0',
            'migration_backup': True,
            'change_types': {},
            'change_log': {
                'enabled': data.get('enable_change_logging', True),
                'storage_dir': data.get('change_log_storage_dir', 'character_data/change_logs'),
                'retention_days': data.get('change_log_retention_days', 365),
                'rotation_size_mb': data.get('change_log_rotation_size_mb', 10),
                'detail_level': 'comprehensive'
            },
            'discord': {
                'enabled': True,
                'detail_level': 'summary',
                'include_attribution': True,
                'min_priority': 'LOW'
            },
            'causation_analysis': {
                'enabled': data.get('enable_causation_analysis', True),
                'confidence_threshold': data.get('causation_confidence_threshold', 0.7),
                'max_cascade_depth': data.get('max_cascade_depth', 3)
            }
        }
        
        # Migrate enabled change types
        enabled_types = data.get('enabled_change_types', set())
        for change_type in enabled_types:
            migrated['change_types'][change_type] = {
                'enabled': True,
                'discord_enabled': True,
                'log_enabled': True
            }
        
        return migrated
    
    def _parse_config_data(self, data: Dict[str, Any]) -> EnhancedChangeTrackingConfig:
        """Parse configuration data into configuration object."""
        # Parse change type configurations
        change_types = {}
        for change_type, config_data in data.get('change_types', {}).items():
            change_types[change_type] = ChangeTypeConfig(**config_data)
        
        # Parse sub-configurations
        change_log_config = ChangeLogConfig(**data.get('change_log', {}))
        discord_config = DiscordNotificationConfig(**data.get('discord', {}))
        causation_config = CausationAnalysisConfig(**data.get('causation_analysis', {}))
        
        # Create main configuration
        config = EnhancedChangeTrackingConfig(
            change_types=change_types,
            change_log=change_log_config,
            discord=discord_config,
            causation_analysis=causation_config,
            enabled=data.get('enabled', True),
            detect_minor_changes=data.get('detect_minor_changes', False),
            detect_metadata_changes=data.get('detect_metadata_changes', False),
            detect_cosmetic_changes=data.get('detect_cosmetic_changes', False),
            config_version=data.get('config_version', '1.0'),
            migration_backup=data.get('migration_backup', True)
        )
        
        return config
    
    def _config_to_dict(self, config: EnhancedChangeTrackingConfig) -> Dict[str, Any]:
        """Convert configuration object to dictionary for serialization."""
        return {
            'enabled': config.enabled,
            'config_version': config.config_version,
            'migration_backup': config.migration_backup,
            'detect_minor_changes': config.detect_minor_changes,
            'detect_metadata_changes': config.detect_metadata_changes,
            'detect_cosmetic_changes': config.detect_cosmetic_changes,
            'change_types': {
                change_type: {
                    'enabled': cfg.enabled,
                    'priority': cfg.priority.name if cfg.priority else None,
                    'discord_enabled': cfg.discord_enabled,
                    'log_enabled': cfg.log_enabled,
                    'causation_analysis': cfg.causation_analysis
                }
                for change_type, cfg in config.change_types.items()
            },
            'change_log': {
                'enabled': config.change_log.enabled,
                'storage_dir': str(config.change_log.storage_dir),
                'retention_days': config.change_log.retention_days,
                'rotation_size_mb': config.change_log.rotation_size_mb,
                'backup_old_logs': config.change_log.backup_old_logs,
                'detail_level': config.change_log.detail_level.value,
                'max_entries_per_batch': config.change_log.max_entries_per_batch,
                'enable_compression': config.change_log.enable_compression,
                'enable_causation_analysis': config.change_log.enable_causation_analysis,
                'enable_detailed_descriptions': config.change_log.enable_detailed_descriptions
            },
            'discord': {
                'enabled': config.discord.enabled,
                'detail_level': config.discord.detail_level.value,
                'include_attribution': config.discord.include_attribution,
                'include_causation': config.discord.include_causation,
                'min_priority': config.discord.min_priority.name,
                'max_changes_per_notification': config.discord.max_changes_per_notification,
                'notify_on_causation_detected': config.discord.notify_on_causation_detected,
                'group_related_changes': config.discord.group_related_changes
            },
            'causation_analysis': {
                'enabled': config.causation_analysis.enabled,
                'confidence_threshold': config.causation_analysis.confidence_threshold,
                'max_cascade_depth': config.causation_analysis.max_cascade_depth,
                'detect_feat_causation': config.causation_analysis.detect_feat_causation,
                'detect_level_progression': config.causation_analysis.detect_level_progression,
                'detect_equipment_causation': config.causation_analysis.detect_equipment_causation,
                'detect_ability_score_cascades': config.causation_analysis.detect_ability_score_cascades,
                'analysis_timeout_seconds': config.causation_analysis.analysis_timeout_seconds,
                'cache_analysis_results': config.causation_analysis.cache_analysis_results
            }
        }
    
    def _apply_config_updates(self, config: EnhancedChangeTrackingConfig, updates: Dict[str, Any]):
        """Apply updates to configuration object."""
        for key, value in updates.items():
            if key == 'change_types' and isinstance(value, dict):
                for change_type, type_config in value.items():
                    if change_type in config.change_types:
                        # Update existing change type config
                        for attr, attr_value in type_config.items():
                            setattr(config.change_types[change_type], attr, attr_value)
                    else:
                        # Add new change type config
                        config.change_types[change_type] = ChangeTypeConfig(**type_config)
            elif key in ['change_log', 'discord', 'causation_analysis'] and isinstance(value, dict):
                # Update sub-configuration
                sub_config = getattr(config, key)
                for attr, attr_value in value.items():
                    setattr(sub_config, attr, attr_value)
            elif hasattr(config, key):
                # Update main configuration attribute
                setattr(config, key, value)


def create_default_config_file(config_path: Path) -> bool:
    """Create a default configuration file with documentation."""
    config_content = """# Enhanced Change Tracking Configuration
# Configuration for comprehensive D&D Beyond character change tracking

# Global settings
enabled: true                    # Enable/disable entire enhanced change tracking system
config_version: "1.0"           # Configuration version for migration
migration_backup: true          # Create backup during configuration migration

# Detection sensitivity
detect_minor_changes: false     # Detect minor cosmetic changes
detect_metadata_changes: false  # Detect metadata-only changes
detect_cosmetic_changes: false  # Detect appearance/avatar changes

# Change type configurations
# Each change type can be individually configured
change_types:
  feats:
    enabled: true               # Enable feat change detection
    priority: HIGH              # Priority level (LOW, MEDIUM, HIGH)
    discord_enabled: true       # Send Discord notifications for this type
    log_enabled: true          # Log changes of this type
    causation_analysis: true   # Analyze causation for this type
  
  subclass:
    enabled: true
    priority: HIGH
    discord_enabled: true
    log_enabled: true
    causation_analysis: true
  
  spells:
    enabled: true
    priority: MEDIUM
    discord_enabled: true
    log_enabled: true
    causation_analysis: true
  
  inventory:
    enabled: true
    priority: MEDIUM
    discord_enabled: true
    log_enabled: true
    causation_analysis: true
  
  background:
    enabled: true
    priority: HIGH
    discord_enabled: true
    log_enabled: true
    causation_analysis: true
  
  max_hp:
    enabled: true
    priority: MEDIUM
    discord_enabled: true
    log_enabled: true
    causation_analysis: true
  
  proficiencies:
    enabled: true
    priority: MEDIUM
    discord_enabled: true
    log_enabled: true
    causation_analysis: true
  
  ability_scores:
    enabled: true
    priority: HIGH
    discord_enabled: true
    log_enabled: true
    causation_analysis: true
  
  race_species:
    enabled: true
    priority: HIGH
    discord_enabled: true
    log_enabled: true
    causation_analysis: true
  
  multiclass:
    enabled: true
    priority: HIGH
    discord_enabled: true
    log_enabled: true
    causation_analysis: true
  
  personality:
    enabled: false              # Personality changes are often minor
    priority: LOW
    discord_enabled: false
    log_enabled: true
    causation_analysis: false
  
  spellcasting_stats:
    enabled: true
    priority: MEDIUM
    discord_enabled: true
    log_enabled: true
    causation_analysis: true
  
  initiative:
    enabled: true
    priority: MEDIUM
    discord_enabled: true
    log_enabled: true
    causation_analysis: true
  
  passive_skills:
    enabled: false              # Passive skills change frequently
    priority: LOW
    discord_enabled: false
    log_enabled: true
    causation_analysis: true
  
  alignment:
    enabled: true
    priority: MEDIUM
    discord_enabled: true
    log_enabled: true
    causation_analysis: false
  
  size:
    enabled: true
    priority: MEDIUM
    discord_enabled: true
    log_enabled: true
    causation_analysis: true
  
  movement_speed:
    enabled: false              # Speed changes are often temporary
    priority: LOW
    discord_enabled: false
    log_enabled: true
    causation_analysis: true

# Change log configuration
change_log:
  enabled: true                           # Enable change logging
  storage_dir: "character_data/change_logs"  # Directory for change logs
  retention_days: 365                     # Keep logs for 1 year
  rotation_size_mb: 10                    # Rotate when file exceeds this size
  backup_old_logs: true                   # Archive old logs instead of deleting
  detail_level: comprehensive             # Detail level (brief, summary, detailed, comprehensive)
  
  # Performance settings
  max_entries_per_batch: 100              # Maximum entries to process at once
  enable_compression: false               # Compress log files (future feature)
  
  # Feature toggles
  enable_causation_analysis: true         # Analyze what caused changes
  enable_detailed_descriptions: true      # Generate comprehensive descriptions

# Discord notification configuration
discord:
  enabled: true                           # Enable Discord notifications
  detail_level: summary                   # Detail level (brief, summary, detailed)
  include_attribution: true               # Include what caused the change
  include_causation: true                 # Include causation analysis
  
  # Priority filtering
  min_priority: LOW                       # Minimum priority to notify (LOW, MEDIUM, HIGH)
  max_changes_per_notification: 200       # Maximum changes per notification
  
  # Notification behavior
  notify_on_causation_detected: true      # Send notification when causation is found
  group_related_changes: true             # Group related changes together

# Causation analysis configuration
causation_analysis:
  enabled: true                           # Enable causation analysis
  confidence_threshold: 0.7               # Minimum confidence for causation (0.0-1.0)
  max_cascade_depth: 3                    # Maximum depth for cascade detection
  
  # Analysis features
  detect_feat_causation: true             # Detect changes caused by feats
  detect_level_progression: true          # Detect changes from level progression
  detect_equipment_causation: true        # Detect changes from equipment
  detect_ability_score_cascades: true     # Detect cascading ability score effects
  
  # Performance settings
  analysis_timeout_seconds: 30            # Timeout for causation analysis
  cache_analysis_results: true            # Cache analysis results for performance
"""
    
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            f.write(config_content)
        return True
    except Exception:
        return False