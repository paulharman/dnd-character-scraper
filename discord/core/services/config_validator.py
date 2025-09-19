"""
Configuration Validation Service

Validates enhanced change tracking configuration settings,
provides detailed error messages, and ensures configuration
integrity before activation.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import os
import stat

from discord.core.models.config_models import (
    EnhancedChangeTrackingConfig,
    ChangeTypeConfig,
    ChangeLogConfig,
    DiscordNotificationConfig,
    CausationAnalysisConfig,
    DetailLevel,
    ConfigurationError
)
from discord.services.change_detection.models import ChangePriority


class ConfigurationValidator:
    """Validates enhanced change tracking configuration."""
    
    def __init__(self):
        """Initialize configuration validator."""
        self.logger = logging.getLogger(__name__)
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_full_configuration(self, config: EnhancedChangeTrackingConfig) -> Tuple[List[str], List[str]]:
        """Validate entire configuration and return errors and warnings."""
        self.errors = []
        self.warnings = []
        
        # Validate main configuration
        self._validate_main_config(config)
        
        # Validate change type configurations
        self._validate_change_types(config.change_types)
        
        # Validate sub-configurations
        self._validate_change_log_config(config.change_log)
        self._validate_discord_config(config.discord)
        self._validate_causation_config(config.causation_analysis)
        
        # Validate integration and consistency
        self._validate_configuration_consistency(config)
        
        return self.errors.copy(), self.warnings.copy()
    
    def validate_change_type_config(self, change_type: str, config: ChangeTypeConfig) -> List[str]:
        """Validate individual change type configuration."""
        errors = []
        
        # Validate change type name
        valid_change_types = {
            'feats', 'subclass', 'spells', 'inventory', 'background', 
            'max_hp', 'proficiencies', 'ability_scores', 'race_species',
            'multiclass', 'personality', 'spellcasting_stats', 'initiative',
            'passive_skills', 'alignment', 'size', 'movement_speed'
        }
        
        if change_type not in valid_change_types:
            errors.append(f"Invalid change type: {change_type}")
        
        # Validate priority
        if config.priority is not None and not isinstance(config.priority, ChangePriority):
            errors.append(f"Invalid priority for {change_type}: {config.priority}")
        
        # Validate boolean fields
        if not isinstance(config.enabled, bool):
            errors.append(f"enabled must be boolean for {change_type}")
        
        if not isinstance(config.discord_enabled, bool):
            errors.append(f"discord_enabled must be boolean for {change_type}")
        
        if not isinstance(config.log_enabled, bool):
            errors.append(f"log_enabled must be boolean for {change_type}")
        
        if not isinstance(config.causation_analysis, bool):
            errors.append(f"causation_analysis must be boolean for {change_type}")
        
        return errors
    
    def validate_storage_permissions(self, storage_dir: Path) -> List[str]:
        """Validate storage directory permissions."""
        errors = []
        
        try:
            # Create directory if it doesn't exist
            storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if it's actually a directory
            if not storage_dir.is_dir():
                errors.append(f"Storage path is not a directory: {storage_dir}")
                return errors
            
            # Check read permission
            if not os.access(storage_dir, os.R_OK):
                errors.append(f"No read permission for storage directory: {storage_dir}")
            
            # Check write permission
            if not os.access(storage_dir, os.W_OK):
                errors.append(f"No write permission for storage directory: {storage_dir}")
            
            # Test actual file creation
            test_file = storage_dir / ".config_test"
            try:
                test_file.write_text("test")
                test_file.unlink()
            except Exception as e:
                errors.append(f"Cannot create files in storage directory: {e}")
            
        except Exception as e:
            errors.append(f"Cannot access storage directory {storage_dir}: {e}")
        
        return errors
    
    def validate_configuration_migration(self, old_config: Dict[str, Any], new_config: EnhancedChangeTrackingConfig) -> List[str]:
        """Validate configuration migration."""
        errors = []
        warnings = []
        
        # Check for data loss during migration
        old_enabled_types = set(old_config.get('enabled_change_types', []))
        new_enabled_types = new_config.get_enabled_change_types()
        
        lost_types = old_enabled_types - new_enabled_types
        if lost_types:
            warnings.append(f"Change types disabled during migration: {lost_types}")
        
        # Check for configuration version compatibility
        old_version = old_config.get('config_version', '0.0')
        if old_version > new_config.config_version:
            errors.append(f"Cannot downgrade configuration from {old_version} to {new_config.config_version}")
        
        return errors
    
    def _validate_main_config(self, config: EnhancedChangeTrackingConfig):
        """Validate main configuration settings."""
        # Validate boolean fields
        if not isinstance(config.enabled, bool):
            self.errors.append("enabled must be boolean")
        
        if not isinstance(config.detect_minor_changes, bool):
            self.errors.append("detect_minor_changes must be boolean")
        
        if not isinstance(config.detect_metadata_changes, bool):
            self.errors.append("detect_metadata_changes must be boolean")
        
        if not isinstance(config.detect_cosmetic_changes, bool):
            self.errors.append("detect_cosmetic_changes must be boolean")
        
        if not isinstance(config.migration_backup, bool):
            self.errors.append("migration_backup must be boolean")
        
        # Validate version string
        if not isinstance(config.config_version, str):
            self.errors.append("config_version must be string")
        elif not config.config_version:
            self.errors.append("config_version cannot be empty")
    
    def _validate_change_types(self, change_types: Dict[str, ChangeTypeConfig]):
        """Validate change type configurations."""
        if not isinstance(change_types, dict):
            self.errors.append("change_types must be dictionary")
            return
        
        for change_type, config in change_types.items():
            errors = self.validate_change_type_config(change_type, config)
            self.errors.extend(errors)
        
        # Check for missing essential change types
        essential_types = {'feats', 'ability_scores', 'spells', 'inventory'}
        missing_essential = essential_types - set(change_types.keys())
        if missing_essential:
            self.warnings.append(f"Missing essential change types: {missing_essential}")
    
    def _validate_change_log_config(self, config: ChangeLogConfig):
        """Validate change log configuration."""
        # Validate boolean fields
        if not isinstance(config.enabled, bool):
            self.errors.append("change_log.enabled must be boolean")
        
        if not isinstance(config.backup_old_logs, bool):
            self.errors.append("change_log.backup_old_logs must be boolean")
        
        if not isinstance(config.enable_compression, bool):
            self.errors.append("change_log.enable_compression must be boolean")
        
        if not isinstance(config.enable_causation_analysis, bool):
            self.errors.append("change_log.enable_causation_analysis must be boolean")
        
        if not isinstance(config.enable_detailed_descriptions, bool):
            self.errors.append("change_log.enable_detailed_descriptions must be boolean")
        
        # Validate numeric fields
        if not isinstance(config.retention_days, int) or config.retention_days <= 0:
            self.errors.append("change_log.retention_days must be positive integer")
        
        if not isinstance(config.rotation_size_mb, int) or config.rotation_size_mb <= 0:
            self.errors.append("change_log.rotation_size_mb must be positive integer")
        
        if not isinstance(config.max_entries_per_batch, int) or config.max_entries_per_batch <= 0:
            self.errors.append("change_log.max_entries_per_batch must be positive integer")
        
        # Validate detail level
        if not isinstance(config.detail_level, DetailLevel):
            self.errors.append("change_log.detail_level must be valid DetailLevel")
        
        # Validate storage directory
        if not isinstance(config.storage_dir, Path):
            self.errors.append("change_log.storage_dir must be Path object")
        else:
            storage_errors = self.validate_storage_permissions(config.storage_dir)
            self.errors.extend(storage_errors)
        
        # Performance warnings
        if config.retention_days > 1095:  # 3 years
            self.warnings.append("change_log.retention_days is very high (>3 years), may impact performance")
        
        if config.max_entries_per_batch > 1000:
            self.warnings.append("change_log.max_entries_per_batch is very high, may impact performance")
    
    def _validate_discord_config(self, config: DiscordNotificationConfig):
        """Validate Discord notification configuration."""
        # Validate boolean fields
        if not isinstance(config.enabled, bool):
            self.errors.append("discord.enabled must be boolean")
        
        if not isinstance(config.include_attribution, bool):
            self.errors.append("discord.include_attribution must be boolean")
        
        if not isinstance(config.include_causation, bool):
            self.errors.append("discord.include_causation must be boolean")
        
        if not isinstance(config.notify_on_causation_detected, bool):
            self.errors.append("discord.notify_on_causation_detected must be boolean")
        
        if not isinstance(config.group_related_changes, bool):
            self.errors.append("discord.group_related_changes must be boolean")
        
        # Validate enum fields
        if not isinstance(config.detail_level, DetailLevel):
            self.errors.append("discord.detail_level must be valid DetailLevel")
        
        if not isinstance(config.min_priority, ChangePriority):
            self.errors.append("discord.min_priority must be valid ChangePriority")
        
        # Validate numeric fields
        if not isinstance(config.max_changes_per_notification, int) or config.max_changes_per_notification <= 0:
            self.errors.append("discord.max_changes_per_notification must be positive integer")
        
        # Performance warnings
        if config.max_changes_per_notification > 500:
            self.warnings.append("discord.max_changes_per_notification is very high, may cause message truncation")
    
    def _validate_causation_config(self, config: CausationAnalysisConfig):
        """Validate causation analysis configuration."""
        # Validate boolean fields
        boolean_fields = [
            'enabled', 'detect_feat_causation', 'detect_level_progression',
            'detect_equipment_causation', 'detect_ability_score_cascades',
            'cache_analysis_results'
        ]
        
        for field in boolean_fields:
            if not isinstance(getattr(config, field), bool):
                self.errors.append(f"causation_analysis.{field} must be boolean")
        
        # Validate numeric fields
        if not isinstance(config.confidence_threshold, (int, float)):
            self.errors.append("causation_analysis.confidence_threshold must be numeric")
        elif not 0.0 <= config.confidence_threshold <= 1.0:
            self.errors.append("causation_analysis.confidence_threshold must be between 0.0 and 1.0")
        
        if not isinstance(config.max_cascade_depth, int) or config.max_cascade_depth < 0:
            self.errors.append("causation_analysis.max_cascade_depth must be non-negative integer")
        
        if not isinstance(config.analysis_timeout_seconds, int) or config.analysis_timeout_seconds <= 0:
            self.errors.append("causation_analysis.analysis_timeout_seconds must be positive integer")
        
        # Performance warnings
        if config.max_cascade_depth > 5:
            self.warnings.append("causation_analysis.max_cascade_depth is very high, may impact performance")
        
        if config.analysis_timeout_seconds > 60:
            self.warnings.append("causation_analysis.analysis_timeout_seconds is very high")
        
        if config.confidence_threshold < 0.5:
            self.warnings.append("causation_analysis.confidence_threshold is low, may produce false positives")
    
    def _validate_configuration_consistency(self, config: EnhancedChangeTrackingConfig):
        """Validate consistency between different configuration sections."""
        # Check if causation analysis is enabled but no change types use it
        if config.causation_analysis.enabled:
            causation_enabled_types = [
                change_type for change_type, type_config in config.change_types.items()
                if type_config.causation_analysis
            ]
            
            if not causation_enabled_types:
                self.warnings.append("Causation analysis is enabled but no change types use it")
        
        # Check if Discord notifications are enabled but no change types use them
        if config.discord.enabled:
            discord_enabled_types = [
                change_type for change_type, type_config in config.change_types.items()
                if type_config.discord_enabled
            ]
            
            if not discord_enabled_types:
                self.warnings.append("Discord notifications are enabled but no change types use them")
        
        # Check if change logging is enabled but no change types use it
        if config.change_log.enabled:
            log_enabled_types = [
                change_type for change_type, type_config in config.change_types.items()
                if type_config.log_enabled
            ]
            
            if not log_enabled_types:
                self.warnings.append("Change logging is enabled but no change types use it")
        
        # Check for conflicting settings
        if config.change_log.enable_causation_analysis and not config.causation_analysis.enabled:
            self.errors.append("Change log causation analysis enabled but global causation analysis disabled")
        
        # Check detail level consistency
        if config.discord.detail_level == DetailLevel.COMPREHENSIVE and config.discord.max_changes_per_notification < 50:
            self.warnings.append("Comprehensive Discord detail level with low max changes may truncate information")


def validate_configuration(config: EnhancedChangeTrackingConfig) -> Tuple[List[str], List[str]]:
    """Validate configuration and return errors and warnings."""
    validator = ConfigurationValidator()
    return validator.validate_full_configuration(config)


def validate_change_type(change_type: str, config: ChangeTypeConfig) -> List[str]:
    """Validate individual change type configuration."""
    validator = ConfigurationValidator()
    return validator.validate_change_type_config(change_type, config)


def validate_storage_directory(storage_dir: Path) -> List[str]:
    """Validate storage directory permissions."""
    validator = ConfigurationValidator()
    return validator.validate_storage_permissions(storage_dir)