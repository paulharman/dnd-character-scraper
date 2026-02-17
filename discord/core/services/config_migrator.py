"""
Configuration Migration Service

Handles migration of configuration files from older versions
to the current enhanced change tracking configuration format.
Provides backup and rollback capabilities.
"""

import logging
import yaml
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

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


class ConfigurationMigrator:
    """Handles configuration migration between versions."""
    
    def __init__(self, config_dir: Path = None):
        """Initialize configuration migrator."""
        self.config_dir = config_dir or Path("config")
        self.logger = logging.getLogger(__name__)
        
        # Migration history
        self.migration_log: List[Dict[str, Any]] = []
    
    def migrate_configuration(self, config_path: Path, backup: bool = True) -> Tuple[bool, Optional[EnhancedChangeTrackingConfig]]:
        """Migrate configuration file to current version."""
        try:
            # Load existing configuration
            if not config_path.exists():
                self.logger.info("No existing configuration found, creating default")
                return self._create_default_configuration(config_path)
            
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            if not config_data:
                self.logger.warning("Empty configuration file, creating default")
                return self._create_default_configuration(config_path)
            
            # Determine current version
            current_version = config_data.get('config_version', '0.0')
            target_version = '1.0'
            
            if current_version == target_version:
                self.logger.info("Configuration is already at target version")
                from discord.core.services.config_service import EnhancedConfigService
                service = EnhancedConfigService(self.config_dir)
                config = service.enhanced_config_manager._parse_config_data(config_data)
                return True, config
            
            # Create backup if requested
            backup_path = None
            if backup:
                backup_path = self._create_backup(config_path, current_version)
                if not backup_path:
                    self.logger.error("Failed to create backup, aborting migration")
                    return False, None
            
            # Perform migration
            migrated_data = self._perform_migration(config_data, current_version, target_version)
            
            # Validate migrated configuration
            from discord.core.services.config_service import EnhancedConfigService
            service = EnhancedConfigService(self.config_dir)
            migrated_config = service.enhanced_config_manager._parse_config_data(migrated_data)
            
            errors = migrated_config.validate()
            if errors:
                self.logger.error(f"Migrated configuration is invalid: {errors}")
                return False, None
            
            # Save migrated configuration
            with open(config_path, 'w') as f:
                yaml.dump(migrated_data, f, default_flow_style=False, indent=2)
            
            # Log migration
            self._log_migration(current_version, target_version, backup_path, config_path)
            
            self.logger.info(f"Successfully migrated configuration from {current_version} to {target_version}")
            return True, migrated_config
            
        except Exception as e:
            self.logger.error(f"Configuration migration failed: {e}")
            return False, None
    
    def migrate_from_discord_config(self, discord_config_path: Path, enhanced_config_path: Path) -> bool:
        """Migrate from legacy Discord-only configuration."""
        try:
            if not discord_config_path.exists():
                self.logger.info("No Discord configuration found to migrate")
                return True
            
            # Load Discord configuration
            with open(discord_config_path, 'r') as f:
                discord_config = yaml.safe_load(f)
            
            if not discord_config:
                return True
            
            # Extract relevant settings
            enhanced_config_data = self._extract_from_discord_config(discord_config)
            
            # Create enhanced configuration
            with open(enhanced_config_path, 'w') as f:
                yaml.dump(enhanced_config_data, f, default_flow_style=False, indent=2)
            
            self.logger.info("Successfully migrated from Discord configuration")
            return True
            
        except Exception as e:
            self.logger.error(f"Discord configuration migration failed: {e}")
            return False
    
    def rollback_migration(self, config_path: Path, backup_path: Path) -> bool:
        """Rollback configuration to previous version."""
        try:
            if not backup_path.exists():
                self.logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Create backup of current (failed) configuration
            failed_backup = config_path.with_suffix(f'.failed.{datetime.now().strftime("%Y%m%d_%H%M%S")}.yaml')
            shutil.copy2(config_path, failed_backup)
            
            # Restore from backup
            shutil.copy2(backup_path, config_path)
            
            self.logger.info(f"Rolled back configuration from {backup_path}")
            self.logger.info(f"Failed configuration saved as {failed_backup}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration rollback failed: {e}")
            return False
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get migration history."""
        return self.migration_log.copy()
    
    def _create_default_configuration(self, config_path: Path) -> Tuple[bool, EnhancedChangeTrackingConfig]:
        """Create default configuration."""
        try:
            from discord.core.models.config_models import create_default_config_file
            success = create_default_config_file(config_path)
            
            if success:
                # Load the created configuration
                from discord.core.services.config_service import EnhancedConfigService
                service = EnhancedConfigService(self.config_dir)
                config = service.load_configurations()
                return True, config
            else:
                return False, None
                
        except Exception as e:
            self.logger.error(f"Failed to create default configuration: {e}")
            return False, None
    
    def _create_backup(self, config_path: Path, version: str) -> Optional[Path]:
        """Create backup of configuration file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = config_path.with_suffix(f'.backup.v{version}.{timestamp}.yaml')
            
            shutil.copy2(config_path, backup_path)
            self.logger.info(f"Created configuration backup: {backup_path}")
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None
    
    def _perform_migration(self, config_data: Dict[str, Any], from_version: str, to_version: str) -> Dict[str, Any]:
        """Perform migration between versions."""
        if from_version == '0.0' and to_version == '1.0':
            return self._migrate_v0_to_v1(config_data)
        else:
            raise ConfigurationError(f"Unsupported migration path: {from_version} -> {to_version}")
    
    def _migrate_v0_to_v1(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from version 0.0 (legacy) to version 1.0."""
        migrated = {
            'enabled': config_data.get('enabled', True),
            'config_version': '1.0',
            'migration_backup': True,
            'detect_minor_changes': config_data.get('detect_minor_changes', False),
            'detect_metadata_changes': config_data.get('detect_metadata_changes', False),
            'detect_cosmetic_changes': config_data.get('detect_cosmetic_changes', False),
            'change_types': {},
            'change_log': {
                'enabled': config_data.get('enable_change_logging', True),
                'storage_dir': config_data.get('change_log_storage_dir', 'character_data/change_logs'),
                'retention_days': config_data.get('change_log_retention_days', 365),
                'rotation_size_mb': config_data.get('change_log_rotation_size_mb', 10),
                'backup_old_logs': config_data.get('backup_old_logs', True),
                'detail_level': 'comprehensive',
                'max_entries_per_batch': config_data.get('max_entries_per_batch', 100),
                'enable_compression': False,
                'enable_causation_analysis': config_data.get('enable_causation_analysis', True),
                'enable_detailed_descriptions': config_data.get('enable_detailed_descriptions', True)
            },
            'discord': {
                'enabled': True,
                'detail_level': config_data.get('discord_detail_level', 'summary'),
                'include_attribution': config_data.get('include_attribution_in_discord', True),
                'include_causation': config_data.get('notify_on_causation_detected', True),
                'min_priority': config_data.get('min_priority_for_discord', 'LOW'),
                'max_changes_per_notification': config_data.get('max_changes_per_notification', 200),
                'notify_on_causation_detected': config_data.get('notify_on_causation_detected', True),
                'group_related_changes': True
            },
            'causation_analysis': {
                'enabled': config_data.get('enable_causation_analysis', True),
                'confidence_threshold': config_data.get('causation_confidence_threshold', 0.7),
                'max_cascade_depth': config_data.get('max_cascade_depth', 3),
                'detect_feat_causation': True,
                'detect_level_progression': True,
                'detect_equipment_causation': True,
                'detect_ability_score_cascades': True,
                'analysis_timeout_seconds': 30,
                'cache_analysis_results': True
            }
        }
        
        # Migrate enabled change types
        enabled_types = config_data.get('enabled_change_types', set())
        if isinstance(enabled_types, list):
            enabled_types = set(enabled_types)
        
        # Default change type configurations
        default_change_types = {
            'feats': {'enabled': True, 'priority': 'HIGH', 'discord_enabled': True, 'log_enabled': True, 'causation_analysis': True},
            'subclass': {'enabled': True, 'priority': 'HIGH', 'discord_enabled': True, 'log_enabled': True, 'causation_analysis': True},
            'spells': {'enabled': True, 'priority': 'MEDIUM', 'discord_enabled': True, 'log_enabled': True, 'causation_analysis': True},
            'inventory': {'enabled': True, 'priority': 'MEDIUM', 'discord_enabled': True, 'log_enabled': True, 'causation_analysis': True},
            'background': {'enabled': True, 'priority': 'HIGH', 'discord_enabled': True, 'log_enabled': True, 'causation_analysis': True},
            'max_hp': {'enabled': True, 'priority': 'MEDIUM', 'discord_enabled': True, 'log_enabled': True, 'causation_analysis': True},
            'proficiencies': {'enabled': True, 'priority': 'MEDIUM', 'discord_enabled': True, 'log_enabled': True, 'causation_analysis': True},
            'ability_scores': {'enabled': True, 'priority': 'HIGH', 'discord_enabled': True, 'log_enabled': True, 'causation_analysis': True},
            'race_species': {'enabled': True, 'priority': 'HIGH', 'discord_enabled': True, 'log_enabled': True, 'causation_analysis': True},
            'multiclass': {'enabled': True, 'priority': 'HIGH', 'discord_enabled': True, 'log_enabled': True, 'causation_analysis': True},
            'personality': {'enabled': False, 'priority': 'LOW', 'discord_enabled': False, 'log_enabled': True, 'causation_analysis': False},
            'spellcasting_stats': {'enabled': True, 'priority': 'MEDIUM', 'discord_enabled': True, 'log_enabled': True, 'causation_analysis': True},
            'initiative': {'enabled': True, 'priority': 'MEDIUM', 'discord_enabled': True, 'log_enabled': True, 'causation_analysis': True},
            'passive_skills': {'enabled': False, 'priority': 'LOW', 'discord_enabled': False, 'log_enabled': True, 'causation_analysis': True},
            'alignment': {'enabled': True, 'priority': 'MEDIUM', 'discord_enabled': True, 'log_enabled': True, 'causation_analysis': False},
            'size': {'enabled': True, 'priority': 'MEDIUM', 'discord_enabled': True, 'log_enabled': True, 'causation_analysis': True},
            'movement_speed': {'enabled': False, 'priority': 'LOW', 'discord_enabled': False, 'log_enabled': True, 'causation_analysis': True}
        }
        
        # Apply enabled types from legacy configuration
        for change_type, default_config in default_change_types.items():
            config = default_config.copy()
            
            # Override enabled status based on legacy configuration
            if enabled_types:
                # Map legacy change types to new change types
                legacy_mapping = {
                    'feats': 'feats',
                    'class_features': 'multiclass',
                    'spells_known': 'spells',
                    'spell_slots': 'spells',
                    'inventory_items': 'inventory',
                    'equipment': 'inventory',
                    'background': 'background',
                    'ability_scores': 'ability_scores',
                    'proficiencies': 'proficiencies',
                    'skills': 'proficiencies'
                }
                
                # Check if this change type was enabled in legacy config
                legacy_enabled = any(
                    legacy_type in enabled_types 
                    for legacy_type, mapped_type in legacy_mapping.items()
                    if mapped_type == change_type
                )
                
                if legacy_enabled:
                    config['enabled'] = True
                    config['discord_enabled'] = True
            
            migrated['change_types'][change_type] = config
        
        return migrated
    
    def _extract_from_discord_config(self, discord_config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract enhanced configuration from Discord configuration."""
        enhanced_config = {
            'enabled': True,
            'config_version': '1.0',
            'migration_backup': True,
            'detect_minor_changes': False,
            'detect_metadata_changes': False,
            'detect_cosmetic_changes': False,
            'change_types': {},
            'change_log': {
                'enabled': True,
                'storage_dir': 'character_data/change_logs',
                'retention_days': 365,
                'rotation_size_mb': 10,
                'backup_old_logs': True,
                'detail_level': 'comprehensive',
                'max_entries_per_batch': 100,
                'enable_compression': False,
                'enable_causation_analysis': True,
                'enable_detailed_descriptions': True
            },
            'discord': {
                'enabled': True,
                'detail_level': 'summary',
                'include_attribution': True,
                'include_causation': True,
                'min_priority': 'LOW',
                'max_changes_per_notification': discord_config.get('advanced', {}).get('max_changes_per_notification', 200),
                'notify_on_causation_detected': True,
                'group_related_changes': True
            },
            'causation_analysis': {
                'enabled': True,
                'confidence_threshold': 0.7,
                'max_cascade_depth': 3,
                'detect_feat_causation': True,
                'detect_level_progression': True,
                'detect_equipment_causation': True,
                'detect_ability_score_cascades': True,
                'analysis_timeout_seconds': 30,
                'cache_analysis_results': True
            }
        }
        
        # Extract enabled change types from Discord filtering
        filtering = discord_config.get('filtering', {})
        discord_change_types = filtering.get('change_types', [])
        
        # Map Discord change types to enhanced change types
        discord_mapping = {
            'level': 'multiclass',
            'experience': 'multiclass',
            'hit_points': 'max_hp',
            'armor_class': 'ability_scores',
            'ability_scores': 'ability_scores',
            'spells_known': 'spells',
            'spell_slots': 'spells',
            'inventory_items': 'inventory',
            'equipment': 'inventory',
            'currency': 'inventory',
            'skills': 'proficiencies',
            'proficiencies': 'proficiencies',
            'feats': 'feats',
            'class_features': 'multiclass',
            'appearance': 'personality',
            'background': 'background'
        }
        
        # Initialize all change types as disabled
        all_change_types = {
            'feats', 'subclass', 'spells', 'inventory', 'background', 
            'max_hp', 'proficiencies', 'ability_scores', 'race_species',
            'multiclass', 'personality', 'spellcasting_stats', 'initiative',
            'passive_skills', 'alignment', 'size', 'movement_speed'
        }
        
        for change_type in all_change_types:
            enhanced_config['change_types'][change_type] = {
                'enabled': False,
                'priority': 'MEDIUM',
                'discord_enabled': False,
                'log_enabled': True,
                'causation_analysis': True
            }
        
        # Enable change types that were enabled in Discord config
        enabled_enhanced_types = set()
        for discord_type in discord_change_types:
            enhanced_type = discord_mapping.get(discord_type)
            if enhanced_type:
                enabled_enhanced_types.add(enhanced_type)
        
        # Apply enabled types
        for change_type in enabled_enhanced_types:
            if change_type in enhanced_config['change_types']:
                enhanced_config['change_types'][change_type]['enabled'] = True
                enhanced_config['change_types'][change_type]['discord_enabled'] = True
        
        return enhanced_config
    
    def _log_migration(self, from_version: str, to_version: str, backup_path: Optional[Path], config_path: Path):
        """Log migration details."""
        migration_entry = {
            'timestamp': datetime.now().isoformat(),
            'from_version': from_version,
            'to_version': to_version,
            'backup_path': str(backup_path) if backup_path else None,
            'config_path': str(config_path),
            'success': True
        }
        
        self.migration_log.append(migration_entry)
        
        # Save migration log
        try:
            log_path = self.config_dir / 'migration_log.yaml'
            with open(log_path, 'w') as f:
                yaml.dump(self.migration_log, f, default_flow_style=False, indent=2)
        except Exception as e:
            self.logger.warning(f"Could not save migration log: {e}")


def migrate_configuration(config_path: Path, backup: bool = True) -> Tuple[bool, Optional[EnhancedChangeTrackingConfig]]:
    """Migrate configuration file to current version."""
    migrator = ConfigurationMigrator(config_path.parent)
    return migrator.migrate_configuration(config_path, backup)


def migrate_from_discord_config(discord_config_path: Path, enhanced_config_path: Path) -> bool:
    """Migrate from Discord configuration to enhanced configuration."""
    migrator = ConfigurationMigrator(enhanced_config_path.parent)
    return migrator.migrate_from_discord_config(discord_config_path, enhanced_config_path)