"""
Dynamic Configuration Manager for Change Detection

Manages field-specific priorities with pattern matching and auto-discovery.
Supports separate thresholds for Discord notifications vs changelog.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
import yaml
from enum import Enum

from src.models.change_detection import FieldChange, ChangePriority

logger = logging.getLogger(__name__)


class NotificationTarget(Enum):
    """Target systems for notifications."""
    DISCORD = "discord"
    CHANGELOG = "changelog"


class DynamicConfigManager:
    """
    Manages dynamic configuration for change detection priorities.
    
    Features:
    - Pattern matching for field paths (e.g., spells.*)
    - Auto-discovery of new field types
    - Hierarchical priority overrides
    - Separate thresholds for Discord vs changelog
    """
    
    def __init__(self, config_path: str = "config/discord.yaml"):
        self.config_path = Path(config_path)
        self.config = {}
        self.discovered_fields: Set[str] = set()
        self.pattern_cache: Dict[str, List[re.Pattern]] = {}
        
        self._load_config()
        self._compile_patterns()
    
    def _load_config(self):
        """Load configuration from file, creating default if missing."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
                logger.info(f"Loaded dynamic config from {self.config_path}")
            else:
                logger.info(f"Config file not found, creating default: {self.config_path}")
                self._create_default_config()
                
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration with sensible priorities integrated into Discord config."""
        # Don't overwrite existing config - just add our section if missing
        if 'detection' not in self.config:
            self.config['detection'] = {
                # Auto-discovery settings
                'auto_add_new_fields': True,
                'default_priority_for_new_fields': 'MEDIUM',
                
                # Field-specific priorities with pattern support
                'field_patterns': {
                    # Character progression (HIGH priority)
                    'character_info.level': 'HIGH',
                    'character.abilityScores.*': 'HIGH',
                    
                    # Combat/spellcasting (MEDIUM priority)
                    'character.hit_points.maximum': 'MEDIUM',
                    'character.spellcasting.spell_save_dc': 'MEDIUM',
                    'character.spellcasting.spell_attack_bonus': 'MEDIUM',
                    'equipment.*.location': 'MEDIUM',  # Container moves
                    
                    # Spells (configurable by type)
                    'spells.*': 'MEDIUM',
                    
                    # Equipment
                    'equipment.enhanced_equipment.*': 'MEDIUM',
                    
                    # Low priority
                    'character.hit_points.current': 'LOW',
                    'character.proficiency_bonus': 'LOW',
                    'character.spellcasting.spell_slots.*': 'LOW',
                    
                    # Ignored by default
                    'character.metadata.*': 'IGNORED',
                    'character.timestamps.*': 'IGNORED'
                }
            }
            self._save_config()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for efficient matching."""
        self.pattern_cache.clear()
        # Get field patterns (includes both manual and auto-discovered)
        field_priorities = self.config.get('detection', {}).get('field_patterns', {})
        
        for pattern_str in field_priorities.keys():
            if '*' in pattern_str:
                # Convert wildcard pattern to regex
                # First escape literal dots, then replace * with pattern that matches anything
                regex_pattern = pattern_str.replace('.', r'\.').replace('*', r'.*')
                regex_pattern = f'^{regex_pattern}$'
                
                try:
                    compiled_pattern = re.compile(regex_pattern)
                    if pattern_str not in self.pattern_cache:
                        self.pattern_cache[pattern_str] = []
                    self.pattern_cache[pattern_str].append(compiled_pattern)
                except re.error as e:
                    logger.warning(f"Invalid pattern '{pattern_str}': {e}")
    
    def get_field_priority(self, field_path: str, auto_discover: bool = True) -> ChangePriority:
        """
        Get priority for a specific field path with pattern matching.
        
        Args:
            field_path: The field path (e.g., 'spells.Wizard.fireball')
            auto_discover: Whether to auto-add unknown fields
            
        Returns:
            ChangePriority enum value
        """
        # Get field patterns (includes both manual and auto-discovered)
        field_priorities = self.config.get('detection', {}).get('field_patterns', {})
        
        # 1. Check for exact match first
        if field_path in field_priorities:
            priority_str = field_priorities[field_path]
            if priority_str.upper() == 'IGNORED':
                return None  # Special case for IGNORED
            return self._str_to_priority(priority_str)
        
        # 2. Check pattern matches (most specific first)
        matched_patterns = []
        for pattern_str, compiled_patterns in self.pattern_cache.items():
            for compiled_pattern in compiled_patterns:
                if compiled_pattern.match(field_path):
                    matched_patterns.append((pattern_str, field_priorities[pattern_str]))
        
        # Sort by specificity (fewer wildcards = more specific)
        if matched_patterns:
            matched_patterns.sort(key=lambda x: x[0].count('*'))
            most_specific_priority = matched_patterns[0][1]
            if most_specific_priority.upper() == 'IGNORED':
                return None  # Special case for IGNORED
            return self._str_to_priority(most_specific_priority)
        
        # 3. Auto-discover new field if enabled (only if not already covered by wildcard)
        if auto_discover and self.config.get('detection', {}).get('auto_add_new_fields', True):
            # Don't auto-add if we found a matching pattern (wildcard already covers it)
            if not matched_patterns:
                default_priority = self.config.get('detection', {}).get('default_priority_for_new_fields', 'MEDIUM')
                self._add_discovered_field(field_path, default_priority)
                return self._str_to_priority(default_priority)
        
        # 4. Default fallback
        return ChangePriority.MEDIUM
    
    def should_notify(self, field_change: FieldChange, target: NotificationTarget) -> bool:
        """
        Determine if a change should trigger notification for the target system.
        
        Args:
            field_change: The field change to evaluate
            target: Discord or changelog
            
        Returns:
            True if should notify, False otherwise
        """
        # First check for field-specific priority overrides
        field_specific_priority = self._get_field_specific_priority(field_change.field_path, target)
        
        if field_specific_priority is not None:
            # Use field-specific priority if available
            if field_specific_priority.upper() == 'IGNORED':
                return False
            field_priority = self._str_to_priority(field_specific_priority)
        else:
            # Fall back to general field priority
            field_priority = self.get_field_priority(field_change.field_path)
            
            # Handle IGNORED fields
            if field_priority is None:  # IGNORED
                return False
        
        # Get minimum threshold for target using new Discord config structure
        if target == NotificationTarget.DISCORD:
            min_priority_str = self.config.get('discord', {}).get('min_priority', 'MEDIUM')
        elif target == NotificationTarget.CHANGELOG:
            min_priority_str = self.config.get('changelog', {}).get('min_priority', 'LOW')
        else:
            min_priority_str = 'MEDIUM'
        
        min_priority = self._str_to_priority(min_priority_str)
        
        # Check if field priority meets threshold
        return self._priority_meets_threshold(field_priority, min_priority)
    
    def _get_field_specific_priority(self, field_path: str, target: NotificationTarget) -> Optional[str]:
        """
        Get field-specific priority for Discord or Changelog if configured.
        
        Args:
            field_path: The field path to check
            target: Discord or changelog
            
        Returns:
            Priority string if configured, None otherwise
        """
        field_specific_config = self.config.get('detection', {}).get('field_specific_priorities', {})
        
        # Check for exact match first
        if field_path in field_specific_config:
            field_config = field_specific_config[field_path]
            if isinstance(field_config, dict):
                return field_config.get(target.value)
        
        # Check for wildcard matches
        for pattern_str, field_config in field_specific_config.items():
            if '*' in pattern_str and isinstance(field_config, dict):
                # Use compiled patterns if available
                if pattern_str in self.pattern_cache:
                    for compiled_pattern in self.pattern_cache[pattern_str]:
                        if compiled_pattern.match(field_path):
                            return field_config.get(target.value)
                else:
                    # Fallback pattern matching
                    regex_pattern = pattern_str.replace('.', r'\.').replace('*', r'.*')
                    regex_pattern = f'^{regex_pattern}$'
                    try:
                        if re.match(regex_pattern, field_path):
                            return field_config.get(target.value)
                    except re.error:
                        pass
        
        return None
    
    def _add_discovered_field(self, field_path: str, priority: str):
        """Add a newly discovered field to config."""
        if field_path not in self.discovered_fields:
            self.discovered_fields.add(field_path)
            
            # Add to field_patterns section (will be saved with comment)
            field_patterns = self.config.setdefault('detection', {}).setdefault('field_patterns', {})
            field_patterns[field_path] = priority
            
            logger.info(f"Auto-discovered new field: {field_path} (priority: {priority})")
            
            # Save updated config
            self._save_config()
    
    def _save_config(self):
        """Save current configuration to file with auto-discovered patterns properly commented."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # If we have discovered fields, we need to add them with proper commenting
            if self.discovered_fields:
                self._save_config_with_autodiscovered_section()
            else:
                # Standard YAML save
                with open(self.config_path, 'w') as f:
                    yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
            
            logger.debug(f"Saved config to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def _save_config_with_autodiscovered_section(self):
        """Save config with auto-discovered patterns appended at the end of field_patterns."""
        # Read the existing config file content
        with open(self.config_path, 'r') as f:
            content = f.read()
        
        # Find auto-discovered fields
        field_patterns = self.config.get('detection', {}).get('field_patterns', {})
        auto_discovered = {k: v for k, v in field_patterns.items() if k in self.discovered_fields}
        
        if auto_discovered:
            # Check if auto-discovered section already exists
            if '# === AUTO-DISCOVERED PATTERNS ===' not in content:
                # Add auto-discovered section at the end of the file
                if not content.endswith('\n'):
                    content += '\n'
                content += '\n    # === AUTO-DISCOVERED PATTERNS ===\n'
                for field_path, priority in sorted(auto_discovered.items()):
                    content += f"    {field_path}: {priority}\n"
            else:
                # Update existing auto-discovered section
                lines = content.split('\n')
                updated_lines = []
                in_auto_section = False
                
                for line in lines:
                    if '# === AUTO-DISCOVERED PATTERNS ===' in line:
                        in_auto_section = True
                        updated_lines.append(line)
                        # Add all auto-discovered patterns
                        for field_path, priority in sorted(auto_discovered.items()):
                            updated_lines.append(f"    {field_path}: {priority}")
                    elif in_auto_section and line.strip() and not line.startswith('    '):
                        # End of auto-discovered section
                        in_auto_section = False
                        updated_lines.append(line)
                    elif not in_auto_section:
                        updated_lines.append(line)
                
                content = '\n'.join(updated_lines)
            
            # Write the updated content
            with open(self.config_path, 'w') as f:
                f.write(content)
    
    def _str_to_priority(self, priority_str: str) -> ChangePriority:
        """Convert string priority to enum."""
        try:
            if priority_str.upper() == 'IGNORED':
                # Return a special marker that we can check for
                return None  # We'll handle this specially
            return ChangePriority[priority_str.upper()]
        except (KeyError, AttributeError):
            logger.warning(f"Unknown priority '{priority_str}', defaulting to MEDIUM")
            return ChangePriority.MEDIUM
    
    def _priority_meets_threshold(self, field_priority: ChangePriority, min_threshold: ChangePriority) -> bool:
        """Check if field priority meets minimum threshold."""
        priority_values = {
            ChangePriority.LOW: 1,
            ChangePriority.MEDIUM: 2,
            ChangePriority.HIGH: 3
        }
        
        field_value = priority_values.get(field_priority, 2)
        threshold_value = priority_values.get(min_threshold, 2)
        
        return field_value >= threshold_value
    
    def get_all_field_patterns(self) -> Dict[str, str]:
        """Get all configured field patterns and their priorities."""
        return self.config.get('detection', {}).get('field_patterns', {})
    
    def update_field_priority(self, field_path: str, priority: str):
        """Update priority for a specific field path."""
        field_priorities = self.config.setdefault('detection', {}).setdefault('field_patterns', {})
        field_priorities[field_path] = priority.upper()
        self._save_config()
        self._compile_patterns()  # Recompile patterns after update
        logger.info(f"Updated field priority: {field_path} -> {priority}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about discovered fields and patterns."""
        # Get field patterns (includes both manual and auto-discovered)
        field_priorities = self.config.get('detection', {}).get('field_patterns', {})
        
        pattern_count = sum(1 for pattern in field_priorities.keys() if '*' in pattern)
        exact_count = len(field_priorities) - pattern_count
        
        return {
            'total_configured_fields': len(field_priorities),
            'exact_matches': exact_count,
            'pattern_matches': pattern_count,
            'discovered_fields': len(self.discovered_fields),
            'auto_discovery_enabled': self.config.get('detection', {}).get('auto_add_new_fields', True)
        }