#!/usr/bin/env python3
"""
Discord Notifier Data Group System - Implementation Example

This module demonstrates how the data group system would be implemented
for filtering character change notifications.
"""

import fnmatch
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass
from enum import Enum


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class FieldChange:
    """Represents a single field change"""
    field_path: str
    old_value: Any
    new_value: Any
    change_type: str  # 'added', 'removed', 'modified'
    priority: Priority = Priority.MEDIUM


@dataclass
class GroupDefinition:
    """Defines a data group with its fields and metadata"""
    name: str
    fields: List[str]
    description: str
    priority: Priority = Priority.MEDIUM
    subgroups: Optional[List[str]] = None


# Core data group definitions based on v6.0.0 JSON structure
DATA_GROUPS = {
    "basic": GroupDefinition(
        name="basic",
        fields=[
            "basic_info.name",
            "basic_info.level", 
            "basic_info.experience",
            "basic_info.inspiration",
            "basic_info.classes.*",
            "meta.character_id",
            "meta.is_2024_rules",
            "meta.proficiency_bonus"
        ],
        description="Essential character identity and progression data",
        priority=Priority.HIGH
    ),
    
    "stats": GroupDefinition(
        name="stats",
        fields=[
            "ability_scores.*",
            "skills.*", 
            "saving_throws.*",
            "proficiencies.*",
            "proficiency_sources.*"
        ],
        description="Core ability scores, saves, and skills",
        priority=Priority.HIGH,
        subgroups=["abilities", "skills", "saves", "proficiencies"]
    ),
    
    "combat": GroupDefinition(
        name="combat",
        fields=[
            "basic_info.armor_class.*",
            "basic_info.hit_points.*",
            "basic_info.initiative.*",
            "basic_info.speed.*",
            "meta.passive_senses.*"
        ],
        description="Combat-relevant statistics",
        priority=Priority.HIGH,
        subgroups=["ac", "hp", "initiative", "speed"]
    ),
    
    "spells": GroupDefinition(
        name="spells",
        fields=[
            "spells.*",
            "spell_slots.*",
            "meta.primary_spellcasting_ability",
            "meta.total_caster_level"
        ],
        description="All spellcasting related data",
        priority=Priority.HIGH,
        subgroups=["known", "slots"]
    ),
    
    "inventory": GroupDefinition(
        name="inventory",
        fields=[
            "inventory.*",
            "meta.total_wealth_gp",
            "meta.individual_currencies.*",
            "meta.carrying_capacity"
        ],
        description="Equipment, money, and carrying capacity",
        priority=Priority.MEDIUM,
        subgroups=["equipment", "wealth"]
    ),
    
    "features": GroupDefinition(
        name="features",
        fields=[
            "species.traits.*",
            "feats.*",
            "actions.*",
            "background.description"
        ],
        description="Class features, racial traits, feats, and actions",
        priority=Priority.MEDIUM,
        subgroups=["racial", "feats", "actions"]
    ),
    
    "appearance": GroupDefinition(
        name="appearance",
        fields=[
            "appearance.*",
            "basic_info.avatarUrl"
        ],
        description="Physical description and avatar",
        priority=Priority.LOW
    ),
    
    "background": GroupDefinition(
        name="background",
        fields=[
            "background.personal_possessions",
            "background.other_holdings",
            "background.organizations",
            "background.enemies",
            "background.ideals",
            "background.bonds", 
            "background.flaws",
            "background.personality_traits",
            "notes.*"
        ],
        description="Backstory, personality, and relationships",
        priority=Priority.LOW
    ),
    
    "meta": GroupDefinition(
        name="meta",
        fields=[
            "meta.processed_timestamp",
            "meta.scraper_version",
            "meta.diagnostics.*",
            "basic_info.lifestyleId"
        ],
        description="System metadata and diagnostics",
        priority=Priority.LOW
    )
}

# Nested group definitions for granular control
NESTED_GROUPS = {
    "stats.abilities": ["ability_scores.*"],
    "stats.skills": ["skills.*"],
    "stats.saves": ["saving_throws.*"],
    "stats.proficiencies": ["proficiencies.*", "proficiency_sources.*"],
    
    "combat.ac": ["basic_info.armor_class.*"],
    "combat.hp": ["basic_info.hit_points.*"],
    "combat.initiative": ["basic_info.initiative.*"],
    "combat.speed": ["basic_info.speed.*"],
    
    "spells.known": ["spells.*"],
    "spells.slots": ["spell_slots.*"],
    
    "inventory.equipment": ["inventory.*"],
    "inventory.wealth": ["meta.total_wealth_gp", "meta.individual_currencies.*"],
    
    "features.racial": ["species.traits.*"],
    "features.feats": ["feats.*"],
    "features.actions": ["actions.*"]
}

# Composite group definitions for convenience
COMPOSITE_GROUPS = {
    "progression": ["basic", "stats.abilities", "features.feats", "spells.known", "spells.slots"],
    "mechanics": ["basic", "stats", "combat", "spells", "features"],
    "roleplay": ["appearance", "background"],
    "resources": ["combat.hp", "spells.slots", "inventory.wealth"]
}


class DataGroupFilter:
    """Handles filtering of character changes based on data groups"""
    
    def __init__(self, include_groups: Optional[List[str]] = None, 
                 exclude_groups: Optional[List[str]] = None):
        """
        Initialize the filter with include/exclude group lists
        
        Args:
            include_groups: List of groups to include (None = all)
            exclude_groups: List of groups to exclude (None = none)
        """
        self.include_groups = include_groups or ["*"]
        self.exclude_groups = exclude_groups or []
        
        # Resolve groups to actual field patterns
        self.include_patterns = self._resolve_groups(self.include_groups)
        self.exclude_patterns = self._resolve_groups(self.exclude_groups)
    
    def _resolve_groups(self, group_list: List[str]) -> Set[str]:
        """Resolve group names to actual JSON field patterns"""
        resolved_patterns = set()
        
        for group in group_list:
            if group == "*":
                # Include all groups
                for group_def in DATA_GROUPS.values():
                    resolved_patterns.update(group_def.fields)
                continue
                
            if group in COMPOSITE_GROUPS:
                # Resolve composite group
                for subgroup in COMPOSITE_GROUPS[group]:
                    resolved_patterns.update(self._resolve_single_group(subgroup))
            else:
                # Resolve single group
                resolved_patterns.update(self._resolve_single_group(group))
        
        return resolved_patterns
    
    def _resolve_single_group(self, group_name: str) -> Set[str]:
        """Resolve a single group name to field patterns"""
        # Check nested groups first
        if group_name in NESTED_GROUPS:
            return set(NESTED_GROUPS[group_name])
        
        # Check main groups
        if group_name in DATA_GROUPS:
            return set(DATA_GROUPS[group_name].fields)
        
        # Unknown group - log warning in real implementation
        print(f"Warning: Unknown group '{group_name}'")
        return set()
    
    def should_track_field(self, field_path: str) -> bool:
        """Determine if a field should be tracked based on include/exclude rules"""
        # Check exclude patterns first (they take precedence)
        if self.exclude_patterns and self._field_matches_any_pattern(field_path, self.exclude_patterns):
            return False
        
        # Check include patterns
        if self.include_patterns and not self._field_matches_any_pattern(field_path, self.include_patterns):
            return False
        
        return True
    
    def _field_matches_any_pattern(self, field_path: str, patterns: Set[str]) -> bool:
        """Check if field matches any of the given patterns"""
        for pattern in patterns:
            if self._field_matches_pattern(field_path, pattern):
                return True
        return False
    
    def _field_matches_pattern(self, field_path: str, pattern: str) -> bool:
        """Check if a field path matches a pattern (supports wildcards)"""
        # Handle nested object notation (.*) 
        if pattern.endswith(".*"):
            base_pattern = pattern[:-2]  # Remove .*
            return field_path.startswith(base_pattern + ".")
        
        # Handle exact matches and wildcards
        return fnmatch.fnmatch(field_path, pattern)
    
    def filter_changes(self, changes: List[FieldChange]) -> List[FieldChange]:
        """Filter detected changes based on group settings"""
        return [change for change in changes if self.should_track_field(change.field_path)]
    
    def get_group_info(self, group_name: str) -> Optional[GroupDefinition]:
        """Get information about a specific group"""
        return DATA_GROUPS.get(group_name)
    
    def list_available_groups(self) -> Dict[str, str]:
        """List all available groups with descriptions"""
        groups = {}
        
        # Main groups
        for name, group_def in DATA_GROUPS.items():
            groups[name] = group_def.description
        
        # Nested groups
        for name in NESTED_GROUPS.keys():
            groups[name] = f"Nested group: {name.split('.')[1]}"
        
        # Composite groups
        for name, included_groups in COMPOSITE_GROUPS.items():
            groups[name] = f"Composite group including: {', '.join(included_groups)}"
        
        return groups


def get_all_field_paths(data: Dict[str, Any], prefix: str = "") -> List[str]:
    """Recursively get all field paths from a JSON structure"""
    paths = []
    
    for key, value in data.items():
        current_path = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, dict):
            paths.extend(get_all_field_paths(value, current_path))
        elif isinstance(value, list):
            # For arrays, we'll track the array itself
            paths.append(current_path)
            # Optionally track individual elements
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    paths.extend(get_all_field_paths(item, f"{current_path}.{i}"))
        else:
            paths.append(current_path)
    
    return paths


# Example usage and testing
def main():
    """Demonstrate the data group system"""
    
    # Example 1: Combat session tracking
    print("=== Example 1: Combat Session Tracking ===")
    combat_filter = DataGroupFilter(include_groups=["combat", "spells.slots"])
    
    # Simulate some changes
    changes = [
        FieldChange("basic_info.hit_points.current", 25, 20, "modified"),
        FieldChange("basic_info.armor_class.total", 15, 17, "modified"),
        FieldChange("spell_slots.level_1", 3, 2, "modified"),
        FieldChange("inventory.0.name", "Sword", "Magic Sword", "modified"),  # Should be filtered out
        FieldChange("notes.character_notes", "Old note", "New note", "modified"),  # Should be filtered out
    ]
    
    filtered_changes = combat_filter.filter_changes(changes)
    print(f"Original changes: {len(changes)}")
    print(f"Filtered changes: {len(filtered_changes)}")
    for change in filtered_changes:
        print(f"  - {change.field_path}: {change.old_value} -> {change.new_value}")
    
    # Example 2: Everything except meta
    print("\n=== Example 2: Everything Except Meta ===")
    no_meta_filter = DataGroupFilter(exclude_groups=["meta"])
    
    meta_changes = [
        FieldChange("basic_info.level", 1, 2, "modified"),
        FieldChange("meta.processed_timestamp", 123456, 123457, "modified"),  # Should be filtered out
        FieldChange("appearance.hair", "brown", "black", "modified"),
        FieldChange("meta.diagnostics.errors", [], ["some error"], "modified"),  # Should be filtered out
    ]
    
    filtered_meta = no_meta_filter.filter_changes(meta_changes)
    print(f"Original changes: {len(meta_changes)}")
    print(f"Filtered changes: {len(filtered_meta)}")
    for change in filtered_meta:
        print(f"  - {change.field_path}: {change.old_value} -> {change.new_value}")
    
    # Example 3: List available groups
    print("\n=== Available Groups ===")
    filter_obj = DataGroupFilter()
    groups = filter_obj.list_available_groups()
    for name, description in sorted(groups.items()):
        priority = ""
        if name in DATA_GROUPS:
            priority = f" ({DATA_GROUPS[name].priority.name})"
        print(f"  {name}{priority}: {description}")


if __name__ == "__main__":
    main()