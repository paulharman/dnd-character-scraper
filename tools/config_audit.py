#!/usr/bin/env python3
"""
Configuration Audit Tool

This script performs a comprehensive audit of all configuration items across the project
to verify which items are actually used in the codebase vs. which are truly unused.
"""

import os
import re
import yaml
import json
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class ConfigItemStatus(Enum):
    ACTIVE = "active"           # Currently used in codebase
    DEPRECATED = "deprecated"   # Supported but will be removed
    UNUSED = "unused"          # Not used, safe to remove
    DUPLICATE = "duplicate"    # Duplicate of another setting
    PARTIAL = "partial"        # Partially implemented

@dataclass
class ConfigItem:
    path: str
    value: Any
    file: str
    status: ConfigItemStatus
    usage_count: int = 0
    usage_files: List[str] = None
    notes: str = ""
    
    def __post_init__(self):
        if self.usage_files is None:
            self.usage_files = []

class ConfigurationAuditor:
    """Comprehensive configuration auditor for the D&D Beyond Character Scraper project."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.config_items: Dict[str, ConfigItem] = {}
        self.search_patterns: Dict[str, List[str]] = {}
        
        # Files to search for configuration usage
        self.search_extensions = {'.py', '.yaml', '.yml', '.md'}
        self.exclude_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.kiro'}
        
    def run_audit(self) -> Dict[str, Any]:
        """Run complete configuration audit."""
        print("Starting Configuration Audit...")
        
        # Step 1: Load all configuration files
        print("\nStep 1: Loading configuration files...")
        self._load_all_configurations()
        
        # Step 2: Generate search patterns
        print("\nStep 2: Generating search patterns...")
        self._generate_search_patterns()
        
        # Step 3: Search codebase for usage
        print("\nStep 3: Searching codebase for configuration usage...")
        self._search_codebase_usage()
        
        # Step 4: Analyze and categorize items
        print("\nStep 4: Analyzing and categorizing configuration items...")
        self._analyze_configuration_items()
        
        # Step 5: Generate report
        print("\nStep 5: Generating audit report...")
        report = self._generate_report()
        
        print("Configuration audit complete!")
        return report
    
    def _load_all_configurations(self):
        """Load all configuration files in the project."""
        config_dir = self.project_root / "config"
        
        if not config_dir.exists():
            print(f"❌ Config directory not found: {config_dir}")
            return
            
        # Load main configuration files
        config_files = [
            "main.yaml",
            "discord.yaml", 
            "parser.yaml",
            "scraper.yaml"
        ]
        
        for config_file in config_files:
            config_path = config_dir / config_file
            if config_path.exists():
                self._load_yaml_config(config_path, config_file)
        
        # Load environment-specific configs
        env_dir = config_dir / "environments"
        if env_dir.exists():
            for env_file in env_dir.glob("*.yaml"):
                self._load_yaml_config(env_file, f"environments/{env_file.name}")
        
        # Load rules configs
        rules_dir = config_dir / "rules"
        if rules_dir.exists():
            for rules_file in rules_dir.glob("*.yaml"):
                self._load_yaml_config(rules_file, f"rules/{rules_file.name}")
        
        print(f"Loaded {len(self.config_items)} configuration items from {len(config_files) + 2} files")
    
    def _load_yaml_config(self, config_path: Path, config_name: str):
        """Load a YAML configuration file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
            
            self._extract_config_items(config_data, config_name, "")
            
        except Exception as e:
            print(f"Warning: Error loading {config_path}: {e}")
    
    def _extract_config_items(self, data: Any, file: str, prefix: str):
        """Recursively extract configuration items from nested data."""
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{prefix}.{key}" if prefix else key
                
                if isinstance(value, dict):
                    # Recurse into nested dictionaries
                    self._extract_config_items(value, file, current_path)
                else:
                    # This is a leaf configuration item
                    self.config_items[current_path] = ConfigItem(
                        path=current_path,
                        value=value,
                        file=file,
                        status=ConfigItemStatus.UNUSED  # Default to unused, will be updated
                    )
        elif isinstance(data, list):
            # Handle list configurations
            for i, item in enumerate(data):
                current_path = f"{prefix}[{i}]" if prefix else f"[{i}]"
                self._extract_config_items(item, file, current_path)
    
    def _generate_search_patterns(self):
        """Generate search patterns for each configuration item."""
        for config_path, config_item in self.config_items.items():
            patterns = []
            
            # Direct path patterns
            patterns.extend([
                # Dot notation: config.item.subitem
                re.escape(config_path),
                # Bracket notation: config['item']['subitem']
                self._path_to_bracket_notation(config_path),
                # get() method: config.get('item', {}).get('subitem')
                self._path_to_get_notation(config_path),
            ])
            
            # Individual key patterns (for partial matches)
            path_parts = config_path.split('.')
            if len(path_parts) > 1:
                # Last part of path (most specific)
                patterns.append(re.escape(path_parts[-1]))
                
                # Second to last part (for nested access)
                if len(path_parts) > 2:
                    patterns.append(f"{re.escape(path_parts[-2])}.*{re.escape(path_parts[-1])}")
            
            self.search_patterns[config_path] = patterns
    
    def _path_to_bracket_notation(self, path: str) -> str:
        """Convert dot notation to bracket notation pattern."""
        parts = path.split('.')
        pattern = parts[0]
        for part in parts[1:]:
            pattern += f"\\[[\'\"]?{re.escape(part)}[\'\"]?\\]"
        return pattern
    
    def _path_to_get_notation(self, path: str) -> str:
        """Convert dot notation to get() method pattern."""
        parts = path.split('.')
        pattern = parts[0]
        for part in parts[1:]:
            pattern += f"\\.get\\([\'\"]?{re.escape(part)}[\'\"]?"
        return pattern
    
    def _search_codebase_usage(self):
        """Search the entire codebase for configuration usage."""
        search_files = []
        
        # Collect all files to search
        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in self.search_extensions:
                    search_files.append(file_path)
        
        print(f"Searching {len(search_files)} files for configuration usage...")
        
        # Search each file for configuration patterns
        for file_path in search_files:
            self._search_file_for_patterns(file_path)
    
    def _search_file_for_patterns(self, file_path: Path):
        """Search a single file for configuration patterns."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            relative_path = str(file_path.relative_to(self.project_root))
            
            # Search for each configuration item
            for config_path, patterns in self.search_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        config_item = self.config_items[config_path]
                        config_item.usage_count += 1
                        if relative_path not in config_item.usage_files:
                            config_item.usage_files.append(relative_path)
                        break  # Found in this file, no need to check other patterns
                        
        except Exception as e:
            print(f"Warning: Error searching {file_path}: {e}")
    
    def _analyze_configuration_items(self):
        """Analyze configuration items and categorize their status."""
        
        # Known duplicates (from manual analysis)
        known_duplicates = {
            'features.caching': 'performance.enable_caching',
        }
        
        # Known partial implementations
        known_partial = {
            'discord.color_code_by_priority',
            'discord.group_related_changes', 
            'changelog.enable_compression'
        }
        
        # Items that are defined in schemas but not directly used
        schema_only_items = {
            'logging.include_timestamps',
            'logging.include_traceback',
            'performance.cleanup_temp_files'
        }
        
        for config_path, config_item in self.config_items.items():
            # Check for duplicates
            if config_path in known_duplicates:
                config_item.status = ConfigItemStatus.DUPLICATE
                config_item.notes = f"Duplicate of {known_duplicates[config_path]}"
            
            # Check for partial implementations
            elif config_path in known_partial:
                config_item.status = ConfigItemStatus.PARTIAL
                config_item.notes = "Partially implemented feature"
            
            # Check for schema-only items
            elif config_path in schema_only_items:
                config_item.status = ConfigItemStatus.UNUSED
                config_item.notes = "Defined in schema but not used"
            
            # Check usage count
            elif config_item.usage_count == 0:
                config_item.status = ConfigItemStatus.UNUSED
                config_item.notes = "No usage found in codebase"
            
            elif config_item.usage_count > 0:
                config_item.status = ConfigItemStatus.ACTIVE
                config_item.notes = f"Used in {config_item.usage_count} locations"
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive audit report."""
        
        # Categorize items by status
        categorized = {
            ConfigItemStatus.ACTIVE: [],
            ConfigItemStatus.UNUSED: [],
            ConfigItemStatus.DUPLICATE: [],
            ConfigItemStatus.PARTIAL: [],
            ConfigItemStatus.DEPRECATED: []
        }
        
        for config_item in self.config_items.values():
            categorized[config_item.status].append(config_item)
        
        # Generate summary statistics
        total_items = len(self.config_items)
        summary = {
            'total_items': total_items,
            'active_items': len(categorized[ConfigItemStatus.ACTIVE]),
            'unused_items': len(categorized[ConfigItemStatus.UNUSED]),
            'duplicate_items': len(categorized[ConfigItemStatus.DUPLICATE]),
            'partial_items': len(categorized[ConfigItemStatus.PARTIAL]),
            'deprecated_items': len(categorized[ConfigItemStatus.DEPRECATED])
        }
        
        # Calculate percentages
        summary['active_percentage'] = (summary['active_items'] / total_items) * 100
        summary['unused_percentage'] = (summary['unused_items'] / total_items) * 100
        
        # Create detailed report
        report = {
            'summary': summary,
            'categorized_items': {},
            'recommendations': self._generate_recommendations(categorized)
        }
        
        # Convert categorized items to serializable format
        for status, items in categorized.items():
            report['categorized_items'][status.value] = [
                {
                    'path': item.path,
                    'value': item.value,
                    'file': item.file,
                    'usage_count': item.usage_count,
                    'usage_files': item.usage_files,
                    'notes': item.notes
                }
                for item in items
            ]
        
        return report
    
    def _generate_recommendations(self, categorized: Dict[ConfigItemStatus, List[ConfigItem]]) -> List[str]:
        """Generate recommendations based on audit results."""
        recommendations = []
        
        unused_items = categorized[ConfigItemStatus.UNUSED]
        if unused_items:
            recommendations.append(
                f"Remove {len(unused_items)} unused configuration items to reduce confusion"
            )
        
        duplicate_items = categorized[ConfigItemStatus.DUPLICATE]
        if duplicate_items:
            recommendations.append(
                f"Consolidate {len(duplicate_items)} duplicate configuration items"
            )
        
        partial_items = categorized[ConfigItemStatus.PARTIAL]
        if partial_items:
            recommendations.append(
                f"Complete implementation of {len(partial_items)} partially implemented features"
            )
        
        active_items = categorized[ConfigItemStatus.ACTIVE]
        if active_items:
            recommendations.append(
                f"Document {len(active_items)} active configuration items comprehensively"
            )
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], output_path: Path = None):
        """Save audit report to file."""
        if output_path is None:
            output_path = self.project_root / "config_audit_report.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Audit report saved to: {output_path}")
    
    def print_summary(self, report: Dict[str, Any]):
        """Print audit summary to console."""
        summary = report['summary']
        
        print("\n" + "="*60)
        print("CONFIGURATION AUDIT SUMMARY")
        print("="*60)
        
        print(f"Total Configuration Items: {summary['total_items']}")
        print(f"Active Items: {summary['active_items']} ({summary['active_percentage']:.1f}%)")
        print(f"Unused Items: {summary['unused_items']} ({summary['unused_percentage']:.1f}%)")
        print(f"Duplicate Items: {summary['duplicate_items']}")
        print(f"Partial Items: {summary['partial_items']}")
        
        print("\nRECOMMENDATIONS:")
        for i, recommendation in enumerate(report['recommendations'], 1):
            print(f"{i}. {recommendation}")
        
        print("\nUNUSED ITEMS TO REMOVE:")
        unused_items = report['categorized_items']['unused']
        for item in unused_items:
            print(f"  - {item['path']} (in {item['file']}) - {item['notes']}")
        
        print("\nDUPLICATE ITEMS TO CONSOLIDATE:")
        duplicate_items = report['categorized_items']['duplicate']
        for item in duplicate_items:
            print(f"  - {item['path']} (in {item['file']}) - {item['notes']}")
        
        print("\nPARTIAL IMPLEMENTATIONS TO COMPLETE:")
        partial_items = report['categorized_items']['partial']
        for item in partial_items:
            print(f"  - {item['path']} (in {item['file']}) - {item['notes']}")

def main():
    """Main entry point for configuration audit."""
    auditor = ConfigurationAuditor()
    report = auditor.run_audit()
    
    # Save report
    auditor.save_report(report)
    
    # Print summary
    auditor.print_summary(report)

if __name__ == "__main__":
    main()