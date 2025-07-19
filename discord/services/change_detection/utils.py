"""
Detection Utilities

Common utilities for change detection including field path handling,
value comparison, and data processing helpers.
"""

import logging
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from datetime import datetime
import fnmatch
import re
from dataclasses import dataclass

from .models import FieldChange, ChangeType, ChangePriority, ChangeCategory

logger = logging.getLogger(__name__)


class FieldPathUtils:
    """Utilities for handling field paths in change detection."""
    
    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalize a field path to a standard format."""
        # Remove leading/trailing dots and normalize separators
        path = path.strip().strip('.')
        # Replace multiple dots with single dots
        path = re.sub(r'\.+', '.', path)
        return path
    
    @staticmethod
    def split_path(path: str) -> List[str]:
        """Split a field path into components."""
        normalized = FieldPathUtils.normalize_path(path)
        return normalized.split('.') if normalized else []
    
    @staticmethod
    def join_path(*components: str) -> str:
        """Join path components into a field path."""
        # Filter out empty components and join with dots
        filtered = [str(c).strip() for c in components if c and str(c).strip()]
        return '.'.join(filtered)
    
    @staticmethod
    def get_parent_path(path: str) -> Optional[str]:
        """Get the parent path of a field path."""
        components = FieldPathUtils.split_path(path)
        if len(components) <= 1:
            return None
        return FieldPathUtils.join_path(*components[:-1])
    
    @staticmethod
    def get_field_name(path: str) -> str:
        """Get the field name from a field path."""
        components = FieldPathUtils.split_path(path)
        return components[-1] if components else path
    
    @staticmethod
    def matches_pattern(path: str, pattern: str) -> bool:
        """Check if a field path matches a pattern (supports wildcards)."""
        return fnmatch.fnmatch(path, pattern)
    
    @staticmethod
    def is_descendant(child_path: str, parent_path: str) -> bool:
        """Check if child_path is a descendant of parent_path."""
        normalized_child = FieldPathUtils.normalize_path(child_path)
        normalized_parent = FieldPathUtils.normalize_path(parent_path)
        
        if not normalized_parent:
            return True  # Empty parent matches everything
        
        return normalized_child.startswith(normalized_parent + '.')
    
    @staticmethod
    def get_common_prefix(paths: List[str]) -> str:
        """Get the common prefix of multiple field paths."""
        if not paths:
            return ""
        
        # Split all paths into components
        split_paths = [FieldPathUtils.split_path(path) for path in paths]
        
        # Find common prefix
        common_components = []
        if split_paths:
            min_length = min(len(components) for components in split_paths)
            
            for i in range(min_length):
                component = split_paths[0][i]
                if all(components[i] == component for components in split_paths):
                    common_components.append(component)
                else:
                    break
        
        return FieldPathUtils.join_path(*common_components)


class ValueComparator:
    """Utilities for comparing values in change detection."""
    
    @staticmethod
    def are_equal(value1: Any, value2: Any, tolerance: float = 0.001) -> bool:
        """Compare two values with support for different types and tolerance."""
        # Handle None values
        if value1 is None and value2 is None:
            return True
        if value1 is None or value2 is None:
            return False
        
        # Handle numeric values with tolerance
        if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
            return abs(value1 - value2) <= tolerance
        
        # Handle lists
        if isinstance(value1, list) and isinstance(value2, list):
            if len(value1) != len(value2):
                return False
            return all(ValueComparator.are_equal(v1, v2, tolerance) for v1, v2 in zip(value1, value2))
        
        # Handle dictionaries
        if isinstance(value1, dict) and isinstance(value2, dict):
            if set(value1.keys()) != set(value2.keys()):
                return False
            return all(ValueComparator.are_equal(value1[k], value2[k], tolerance) for k in value1.keys())
        
        # Handle strings (case-insensitive for certain fields)
        if isinstance(value1, str) and isinstance(value2, str):
            return value1.strip() == value2.strip()
        
        # Default comparison
        return value1 == value2
    
    @staticmethod
    def get_change_type(old_value: Any, new_value: Any) -> ChangeType:
        """Determine the type of change between two values."""
        if old_value is None and new_value is not None:
            return ChangeType.ADDED
        elif old_value is not None and new_value is None:
            return ChangeType.REMOVED
        elif isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
            if new_value > old_value:
                return ChangeType.INCREMENTED
            elif new_value < old_value:
                return ChangeType.DECREMENTED
            else:
                return ChangeType.MODIFIED
        else:
            return ChangeType.MODIFIED
    
    @staticmethod
    def get_change_magnitude(old_value: Any, new_value: Any) -> Optional[float]:
        """Get the magnitude of change between two values."""
        if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
            return abs(new_value - old_value)
        elif isinstance(old_value, str) and isinstance(new_value, str):
            # Use string edit distance as magnitude
            return ValueComparator._string_edit_distance(old_value, new_value)
        elif isinstance(old_value, (list, dict)) and isinstance(new_value, (list, dict)):
            # For collections, use size difference
            try:
                return abs(len(new_value) - len(old_value))
            except TypeError:
                return None
        return None
    
    @staticmethod
    def _string_edit_distance(s1: str, s2: str) -> float:
        """Calculate edit distance between two strings."""
        if len(s1) == 0:
            return len(s2)
        if len(s2) == 0:
            return len(s1)
        
        # Simple implementation - could be optimized
        if s1[0] == s2[0]:
            return ValueComparator._string_edit_distance(s1[1:], s2[1:])
        
        return 1 + min(
            ValueComparator._string_edit_distance(s1[1:], s2),    # deletion
            ValueComparator._string_edit_distance(s1, s2[1:]),    # insertion
            ValueComparator._string_edit_distance(s1[1:], s2[1:]) # substitution
        )


class DataExtractor:
    """Utilities for extracting data from character data structures."""
    
    @staticmethod
    def get_nested_value(data: Dict[str, Any], path: str, default: Any = None) -> Any:
        """Get a nested value from data using dot notation path."""
        try:
            current = data
            for component in FieldPathUtils.split_path(path):
                if isinstance(current, dict):
                    current = current.get(component, default)
                elif isinstance(current, list):
                    try:
                        index = int(component)
                        current = current[index] if 0 <= index < len(current) else default
                    except (ValueError, IndexError):
                        return default
                else:
                    return default
            return current
        except (AttributeError, KeyError, TypeError):
            return default
    
    @staticmethod
    def set_nested_value(data: Dict[str, Any], path: str, value: Any) -> bool:
        """Set a nested value in data using dot notation path."""
        try:
            current = data
            components = FieldPathUtils.split_path(path)
            
            # Navigate to the parent of the target
            for component in components[:-1]:
                if component not in current:
                    current[component] = {}
                current = current[component]
            
            # Set the final value
            if components:
                current[components[-1]] = value
                return True
            return False
        except (AttributeError, KeyError, TypeError):
            return False
    
    @staticmethod
    def has_nested_value(data: Dict[str, Any], path: str) -> bool:
        """Check if a nested value exists in data."""
        sentinel = object()
        return DataExtractor.get_nested_value(data, path, sentinel) is not sentinel
    
    @staticmethod
    def get_all_field_paths(data: Dict[str, Any], prefix: str = "") -> List[str]:
        """Get all field paths in a data structure."""
        paths = []
        
        def _extract_paths(obj: Any, current_path: str):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = FieldPathUtils.join_path(current_path, key)
                    paths.append(new_path)
                    _extract_paths(value, new_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_path = FieldPathUtils.join_path(current_path, str(i))
                    paths.append(new_path)
                    _extract_paths(item, new_path)
        
        _extract_paths(data, prefix)
        return paths
    
    @staticmethod
    def flatten_data(data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten nested data structure into dot-notation keys."""
        result = {}
        
        def _flatten(obj: Any, current_path: str):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = FieldPathUtils.join_path(current_path, key)
                    if isinstance(value, (dict, list)) and value:
                        _flatten(value, new_path)
                    else:
                        result[new_path] = value
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_path = FieldPathUtils.join_path(current_path, str(i))
                    if isinstance(item, (dict, list)) and item:
                        _flatten(item, new_path)
                    else:
                        result[new_path] = item
            else:
                result[current_path] = obj
        
        _flatten(data, prefix)
        return result


class ChangeGrouper:
    """Utilities for grouping related changes."""
    
    @staticmethod
    def group_by_parent_path(changes: List[FieldChange]) -> Dict[str, List[FieldChange]]:
        """Group changes by their parent path."""
        groups = {}
        
        for change in changes:
            parent_path = FieldPathUtils.get_parent_path(change.field_path)
            if parent_path is None:
                parent_path = "root"
            
            if parent_path not in groups:
                groups[parent_path] = []
            groups[parent_path].append(change)
        
        return groups
    
    @staticmethod
    def group_by_category(changes: List[FieldChange]) -> Dict[ChangeCategory, List[FieldChange]]:
        """Group changes by their category."""
        groups = {}
        
        for change in changes:
            if change.category not in groups:
                groups[change.category] = []
            groups[change.category].append(change)
        
        return groups
    
    @staticmethod
    def group_by_type(changes: List[FieldChange]) -> Dict[ChangeType, List[FieldChange]]:
        """Group changes by their type."""
        groups = {}
        
        for change in changes:
            if change.change_type not in groups:
                groups[change.change_type] = []
            groups[change.change_type].append(change)
        
        return groups
    
    @staticmethod
    def find_related_changes(changes: List[FieldChange], 
                           max_distance: int = 2) -> List[List[FieldChange]]:
        """Find groups of related changes based on field path proximity."""
        if not changes:
            return []
        
        # Sort changes by field path for easier grouping
        sorted_changes = sorted(changes, key=lambda c: c.field_path)
        
        groups = []
        current_group = [sorted_changes[0]]
        
        for i in range(1, len(sorted_changes)):
            current_change = sorted_changes[i]
            last_change = current_group[-1]
            
            # Check if changes are related
            if ChangeGrouper._are_changes_related(current_change, last_change, max_distance):
                current_group.append(current_change)
            else:
                # Start a new group
                groups.append(current_group)
                current_group = [current_change]
        
        # Add the last group
        if current_group:
            groups.append(current_group)
        
        return groups
    
    @staticmethod
    def _are_changes_related(change1: FieldChange, change2: FieldChange, 
                           max_distance: int) -> bool:
        """Check if two changes are related based on path distance."""
        path1_components = FieldPathUtils.split_path(change1.field_path)
        path2_components = FieldPathUtils.split_path(change2.field_path)
        
        # Check if they share a common prefix within the distance threshold
        common_prefix_len = 0
        min_len = min(len(path1_components), len(path2_components))
        
        for i in range(min_len):
            if path1_components[i] == path2_components[i]:
                common_prefix_len += 1
            else:
                break
        
        # Calculate distance as the number of different components
        distance = (len(path1_components) - common_prefix_len) + (len(path2_components) - common_prefix_len)
        
        return distance <= max_distance


class ChangeDeduplicator:
    """Utilities for deduplicating changes."""
    
    @staticmethod
    def deduplicate_changes(changes: List[FieldChange]) -> List[FieldChange]:
        """Remove duplicate changes keeping the most recent/significant ones."""
        if not changes:
            return []
        
        # Group changes by field path
        field_groups = {}
        for change in changes:
            if change.field_path not in field_groups:
                field_groups[change.field_path] = []
            field_groups[change.field_path].append(change)
        
        # Keep the best change for each field path
        deduplicated = []
        for field_path, field_changes in field_groups.items():
            if len(field_changes) == 1:
                deduplicated.append(field_changes[0])
            else:
                # Choose the most significant change
                best_change = ChangeDeduplicator._choose_best_change(field_changes)
                deduplicated.append(best_change)
        
        return deduplicated
    
    @staticmethod
    def _choose_best_change(changes: List[FieldChange]) -> FieldChange:
        """Choose the best change from a list of changes for the same field."""
        if not changes:
            raise ValueError("Cannot choose best change from empty list")
        
        # Sort by priority (highest first), then by timestamp (most recent first)
        sorted_changes = sorted(changes, 
                              key=lambda c: (c.priority.value, c.detection_timestamp), 
                              reverse=True)
        
        return sorted_changes[0]
    
    @staticmethod
    def merge_consecutive_changes(changes: List[FieldChange]) -> List[FieldChange]:
        """Merge consecutive changes of the same type for the same field."""
        if not changes:
            return []
        
        # Group by field path
        field_groups = ChangeGrouper.group_by_parent_path(changes)
        
        merged = []
        for field_path, field_changes in field_groups.items():
            if len(field_changes) <= 1:
                merged.extend(field_changes)
            else:
                # Sort by timestamp and merge consecutive changes
                sorted_changes = sorted(field_changes, key=lambda c: c.detection_timestamp)
                merged.extend(ChangeDeduplicator._merge_field_changes(sorted_changes))
        
        return merged
    
    @staticmethod
    def _merge_field_changes(changes: List[FieldChange]) -> List[FieldChange]:
        """Merge consecutive changes for a single field."""
        if not changes:
            return []
        
        merged = [changes[0]]
        
        for i in range(1, len(changes)):
            current = changes[i]
            last_merged = merged[-1]
            
            # Check if changes can be merged
            if (current.field_path == last_merged.field_path and 
                current.change_type == last_merged.change_type and
                current.change_type in [ChangeType.INCREMENTED, ChangeType.DECREMENTED]):
                
                # Merge the changes
                merged_change = FieldChange(
                    field_path=current.field_path,
                    old_value=last_merged.old_value,
                    new_value=current.new_value,
                    change_type=current.change_type,
                    priority=max(current.priority, last_merged.priority, key=lambda p: p.value),
                    category=current.category,
                    description=f"Merged change: {last_merged.description} → {current.description}",
                    detection_timestamp=current.detection_timestamp
                )
                merged[-1] = merged_change
            else:
                merged.append(current)
        
        return merged


# Utility functions for common operations
def create_change_from_comparison(field_path: str, old_value: Any, new_value: Any,
                                category: ChangeCategory = ChangeCategory.METADATA,
                                description: str = None) -> Optional[FieldChange]:
    """Create a FieldChange from a value comparison."""
    if ValueComparator.are_equal(old_value, new_value):
        return None
    
    change_type = ValueComparator.get_change_type(old_value, new_value)
    
    # Auto-determine priority based on change type and field path
    priority = ChangePriority.MEDIUM
    if change_type in [ChangeType.ADDED, ChangeType.REMOVED]:
        priority = ChangePriority.HIGH
    elif field_path.startswith(('basic_info.level', 'basic_info.hit_points')):
        priority = ChangePriority.CRITICAL
    
    # Generate description if not provided
    if description is None:
        field_name = FieldPathUtils.get_field_name(field_path)
        description = f"{field_name} changed from {old_value} to {new_value}"
    
    return FieldChange(
        field_path=field_path,
        old_value=old_value,
        new_value=new_value,
        change_type=change_type,
        priority=priority,
        category=category,
        description=description
    )


def compare_data_structures(old_data: Dict[str, Any], new_data: Dict[str, Any],
                          field_patterns: List[str] = None) -> List[FieldChange]:
    """Compare two data structures and return changes."""
    changes = []
    
    # Flatten both data structures
    old_flat = DataExtractor.flatten_data(old_data)
    new_flat = DataExtractor.flatten_data(new_data)
    
    # Get all field paths
    all_paths = set(old_flat.keys()) | set(new_flat.keys())
    
    # Filter paths if patterns are provided
    if field_patterns:
        filtered_paths = set()
        for path in all_paths:
            for pattern in field_patterns:
                if FieldPathUtils.matches_pattern(path, pattern):
                    filtered_paths.add(path)
                    break
        all_paths = filtered_paths
    
    # Compare values for each path
    for path in all_paths:
        old_value = old_flat.get(path)
        new_value = new_flat.get(path)
        
        change = create_change_from_comparison(path, old_value, new_value)
        if change:
            changes.append(change)
    
    return changes


def filter_changes_by_patterns(changes: List[FieldChange], 
                             include_patterns: List[str] = None,
                             exclude_patterns: List[str] = None) -> List[FieldChange]:
    """Filter changes based on field path patterns."""
    filtered = changes
    
    # Apply include patterns
    if include_patterns:
        filtered = [
            change for change in filtered
            if any(FieldPathUtils.matches_pattern(change.field_path, pattern) 
                  for pattern in include_patterns)
        ]
    
    # Apply exclude patterns
    if exclude_patterns:
        filtered = [
            change for change in filtered
            if not any(FieldPathUtils.matches_pattern(change.field_path, pattern) 
                      for pattern in exclude_patterns)
        ]
    
    return filtered


def get_change_summary(changes: List[FieldChange]) -> Dict[str, Any]:
    """Get a summary of changes."""
    if not changes:
        return {
            'total_changes': 0,
            'by_type': {},
            'by_priority': {},
            'by_category': {},
            'significant_changes': 0
        }
    
    by_type = {}
    by_priority = {}
    by_category = {}
    significant_count = 0
    
    for change in changes:
        # Count by type
        type_key = change.change_type.value
        by_type[type_key] = by_type.get(type_key, 0) + 1
        
        # Count by priority
        priority_key = change.priority.name
        by_priority[priority_key] = by_priority.get(priority_key, 0) + 1
        
        # Count by category
        category_key = change.category.value
        by_category[category_key] = by_category.get(category_key, 0) + 1
        
        # Count significant changes
        if change.is_significant():
            significant_count += 1
    
    return {
        'total_changes': len(changes),
        'by_type': by_type,
        'by_priority': by_priority,
        'by_category': by_category,
        'significant_changes': significant_count,
        'has_high_priority': any(c.priority.value >= ChangePriority.HIGH.value for c in changes),
        'has_critical': any(c.priority.value >= ChangePriority.CRITICAL.value for c in changes)
    }