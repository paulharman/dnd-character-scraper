#!/usr/bin/env python3
"""
Configuration Migration Tool

This script provides utilities for migrating configuration files to new naming standards
while maintaining backward compatibility and providing clear migration paths.
"""

import os
import yaml
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
import argparse

class ConfigMigrator:
    """Handles migration of configuration files to new naming standards."""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.migrations_applied = []
        self.warnings = []
        self.errors = []
        
        # Define migration mappings
        self.naming_migrations = {
            # High-impact migrations (breaking changes)
            'max_changes_per_notification': 'maximum_changes_per_notification',
            'min_priority': 'minimum_priority',
            'storage_dir': 'storage_directory',
            
            # Medium-impact migrations
            'check_interval': 'check_interval_seconds',
            'timeout': 'timeout_seconds',
            'retry_delay': 'retry_delay_seconds',
            
            # Low-impact migrations
            'config_dir': 'config_directory',
            'backup_dir': 'backup_directory',
        }
        
        # Define section-specific migrations
        self.section_migrations = {
            'discord': {
                'max_changes': 'maximum_changes_per_notification',
                'min_prio': 'minimum_priority'
            },
            'changelog': {
                'storage_dir': 'storage_directory',
                'max_entries': 'maximum_entries_per_batch'
            }
        }
    
    def migrate_config_file(self, config_path: Path) -> bool:
        """
        Migrate a single configuration file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            True if migration was successful, False otherwise
        """
        if not config_path.exists():
            self.errors.append(f"Configuration file not found: {config_path}")
            return False
        
        try:
            # Load current configuration
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
            
            # Create backup
            backup_path = self._create_backup(config_path)
            
            # Apply migrations
            migrated_data = self._apply_migrations(config_data, str(config_path))
            
            # Check if any changes were made
            if migrated_data == config_data:
                print(f"✅ No migration needed for {config_path}")
                return True
            
            # Save migrated configuration
            if not self.dry_run:
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(migrated_data, f, default_flow_style=False, indent=2)
                print(f"✅ Migrated {config_path} (backup: {backup_path})")
            else:
                print(f"🔍 Would migrate {config_path} (dry run)")
                self._show_migration_preview(config_data, migrated_data)
            
            return True
            
        except Exception as e:
            self.errors.append(f"Error migrating {config_path}: {e}")
            return False
    
    def _create_backup(self, config_path: Path) -> Path:
        """Create a backup of the configuration file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = config_path.with_suffix(f".backup_{timestamp}{config_path.suffix}")
        
        if not self.dry_run:
            shutil.copy2(config_path, backup_path)
        
        return backup_path
    
    def _apply_migrations(self, config_data: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        """Apply all applicable migrations to configuration data."""
        migrated = config_data.copy()
        
        # Apply global naming migrations
        migrated = self._apply_naming_migrations(migrated, file_path)
        
        # Apply section-specific migrations
        migrated = self._apply_section_migrations(migrated, file_path)
        
        # Apply value standardizations
        migrated = self._apply_value_standardizations(migrated, file_path)
        
        return migrated
    
    def _apply_naming_migrations(self, config_data: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        """Apply global naming migrations."""
        return self._migrate_keys_recursive(config_data, self.naming_migrations, file_path)
    
    def _apply_section_migrations(self, config_data: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        """Apply section-specific migrations."""
        migrated = config_data.copy()
        
        for section_name, section_migrations in self.section_migrations.items():
            if section_name in migrated and isinstance(migrated[section_name], dict):
                migrated[section_name] = self._migrate_keys_recursive(
                    migrated[section_name], 
                    section_migrations, 
                    f"{file_path}.{section_name}"
                )
        
        return migrated
    
    def _apply_value_standardizations(self, config_data: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        """Apply value standardizations (e.g., boolean normalization)."""
        migrated = config_data.copy()
        
        # Normalize boolean values
        migrated = self._normalize_booleans_recursive(migrated)
        
        # Standardize enum values to uppercase
        migrated = self._standardize_enums_recursive(migrated)
        
        return migrated
    
    def _migrate_keys_recursive(self, data: Dict[str, Any], migrations: Dict[str, str], path: str) -> Dict[str, Any]:
        """Recursively migrate keys in nested dictionaries."""
        if not isinstance(data, dict):
            return data
        
        migrated = {}
        
        for key, value in data.items():
            # Check if this key needs migration
            new_key = migrations.get(key, key)
            
            if new_key != key:
                self.migrations_applied.append(f"{path}.{key} → {path}.{new_key}")
                print(f"  📝 {key} → {new_key}")
            
            # Recursively migrate nested dictionaries
            if isinstance(value, dict):
                migrated[new_key] = self._migrate_keys_recursive(value, migrations, f"{path}.{new_key}")
            else:
                migrated[new_key] = value
        
        return migrated
    
    def _normalize_booleans_recursive(self, data: Any) -> Any:
        """Recursively normalize boolean values."""
        if isinstance(data, dict):
            return {key: self._normalize_booleans_recursive(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._normalize_booleans_recursive(item) for item in data]
        elif isinstance(data, str):
            # Convert string booleans to actual booleans
            if data.lower() in ('true', 'yes', '1'):
                return True
            elif data.lower() in ('false', 'no', '0'):
                return False
        
        return data
    
    def _standardize_enums_recursive(self, data: Any) -> Any:
        """Recursively standardize enum values."""
        if isinstance(data, dict):
            return {key: self._standardize_enums_recursive(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._standardize_enums_recursive(item) for item in data]
        elif isinstance(data, str):
            # Standardize priority levels
            if data.lower() in ('low', 'medium', 'high', 'critical'):
                return data.upper()
            # Standardize log levels
            elif data.lower() in ('debug', 'info', 'warning', 'error', 'critical'):
                return data.upper()
        
        return data
    
    def _show_migration_preview(self, original: Dict[str, Any], migrated: Dict[str, Any]):
        """Show a preview of what would be migrated."""
        print("  📋 Migration Preview:")
        
        # Show key changes
        original_keys = set(self._get_all_keys(original))
        migrated_keys = set(self._get_all_keys(migrated))
        
        removed_keys = original_keys - migrated_keys
        added_keys = migrated_keys - original_keys
        
        for key in removed_keys:
            print(f"    ❌ Remove: {key}")
        
        for key in added_keys:
            print(f"    ➕ Add: {key}")
    
    def _get_all_keys(self, data: Dict[str, Any], prefix: str = "") -> List[str]:
        """Get all keys from nested dictionary."""
        keys = []
        
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.append(full_key)
            
            if isinstance(value, dict):
                keys.extend(self._get_all_keys(value, full_key))
        
        return keys
    
    def migrate_all_configs(self, config_dir: Path = None) -> bool:
        """
        Migrate all configuration files in the project.
        
        Args:
            config_dir: Directory containing configuration files
            
        Returns:
            True if all migrations were successful
        """
        if config_dir is None:
            config_dir = Path("config")
        
        if not config_dir.exists():
            self.errors.append(f"Configuration directory not found: {config_dir}")
            return False
        
        # Find all YAML configuration files
        config_files = []
        config_files.extend(config_dir.glob("*.yaml"))
        config_files.extend(config_dir.glob("*.yml"))
        
        # Include environment-specific configs
        env_dir = config_dir / "environments"
        if env_dir.exists():
            config_files.extend(env_dir.glob("*.yaml"))
            config_files.extend(env_dir.glob("*.yml"))
        
        print(f"🔍 Found {len(config_files)} configuration files to migrate")
        
        success_count = 0
        for config_file in config_files:
            print(f"\n📁 Processing {config_file}")
            if self.migrate_config_file(config_file):
                success_count += 1
        
        # Print summary
        print(f"\n📊 Migration Summary:")
        print(f"  ✅ Successful: {success_count}/{len(config_files)}")
        print(f"  📝 Migrations applied: {len(self.migrations_applied)}")
        print(f"  ⚠️  Warnings: {len(self.warnings)}")
        print(f"  ❌ Errors: {len(self.errors)}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"    {warning}")
        
        if self.errors:
            print(f"\n❌ Errors:")
            for error in self.errors:
                print(f"    {error}")
        
        return len(self.errors) == 0
    
    def validate_migrated_configs(self, config_dir: Path = None) -> bool:
        """
        Validate that migrated configurations are still valid.
        
        Args:
            config_dir: Directory containing configuration files
            
        Returns:
            True if all configurations are valid
        """
        if config_dir is None:
            config_dir = Path("config")
        
        print("🔍 Validating migrated configurations...")
        
        validation_errors = []
        
        # Try to load each configuration file
        for config_file in config_dir.glob("*.yaml"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
                print(f"  ✅ {config_file} - Valid YAML")
            except Exception as e:
                validation_errors.append(f"{config_file}: {e}")
                print(f"  ❌ {config_file} - Invalid YAML: {e}")
        
        if validation_errors:
            print(f"\n❌ Validation failed with {len(validation_errors)} errors")
            return False
        else:
            print(f"\n✅ All configurations are valid")
            return True
    
    def generate_migration_report(self, output_path: Path = None) -> Path:
        """Generate a detailed migration report."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"config_migration_report_{timestamp}.json")
        
        report = {
            "migration_timestamp": datetime.now().isoformat(),
            "dry_run": self.dry_run,
            "migrations_applied": self.migrations_applied,
            "warnings": self.warnings,
            "errors": self.errors,
            "summary": {
                "total_migrations": len(self.migrations_applied),
                "warning_count": len(self.warnings),
                "error_count": len(self.errors),
                "success": len(self.errors) == 0
            }
        }
        
        if not self.dry_run:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            print(f"📄 Migration report saved to: {output_path}")
        
        return output_path

def main():
    """Main entry point for configuration migration."""
    parser = argparse.ArgumentParser(description="Migrate configuration files to new naming standards")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Preview changes without applying them (default)")
    parser.add_argument("--apply", action="store_true",
                       help="Actually apply the migrations")
    parser.add_argument("--config-dir", type=Path, default=Path("config"),
                       help="Directory containing configuration files")
    parser.add_argument("--validate", action="store_true",
                       help="Validate configurations after migration")
    parser.add_argument("--report", type=Path,
                       help="Path to save migration report")
    
    args = parser.parse_args()
    
    # Determine if this is a dry run
    dry_run = not args.apply
    
    print("🔧 Configuration Migration Tool")
    print("=" * 40)
    
    if dry_run:
        print("🔍 Running in DRY RUN mode (no changes will be made)")
        print("    Use --apply to actually perform migrations")
    else:
        print("⚠️  Running in APPLY mode (changes will be made)")
        print("    Backups will be created automatically")
    
    print(f"📁 Configuration directory: {args.config_dir}")
    print()
    
    # Create migrator
    migrator = ConfigMigrator(dry_run=dry_run)
    
    # Perform migration
    success = migrator.migrate_all_configs(args.config_dir)
    
    # Validate if requested
    if args.validate and not dry_run:
        migrator.validate_migrated_configs(args.config_dir)
    
    # Generate report
    if args.report or not dry_run:
        migrator.generate_migration_report(args.report)
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    main()