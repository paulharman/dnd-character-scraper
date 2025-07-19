"""
Change Detection Models

Data structures for change detection with clean, simple models.
Uses dataclasses and enums for clear data representation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from datetime import datetime


class ChangeType(Enum):
    """Types of changes that can be detected."""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    INCREMENTED = "incremented"
    DECREMENTED = "decremented"
    REORDERED = "reordered"
    RENAMED = "renamed"
    MOVED = "moved"


class ChangePriority(Enum):
    """Priority levels for changes."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ChangeCategory(Enum):
    """Categories of changes for organization."""
    BASIC_INFO = "basic_info"
    ABILITIES = "abilities"
    SKILLS = "skills"
    COMBAT = "combat"
    SPELLS = "spells"
    FEATURES = "features"
    EQUIPMENT = "equipment"
    INVENTORY = "inventory"
    PROGRESSION = "progression"
    SOCIAL = "social"
    METADATA = "metadata"


@dataclass
class FieldChange:
    """Represents a single field change with metadata."""
    field_path: str
    old_value: Any
    new_value: Any
    change_type: ChangeType
    priority: ChangePriority = ChangePriority.MEDIUM
    category: ChangeCategory = ChangeCategory.METADATA
    description: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    detection_timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate field_path is always a string and priority is an enum."""
        self.field_path = str(self.field_path)
        
        # Ensure priority is always a ChangePriority enum
        if not isinstance(self.priority, ChangePriority):
            self.priority = ChangePriority.MEDIUM
        
        # Ensure category is always a ChangeCategory enum
        if not isinstance(self.category, ChangeCategory):
            self.category = ChangeCategory.METADATA
    
    def get_change_delta(self) -> Optional[int]:
        """Get numeric delta for incremental changes."""
        if self.change_type in [ChangeType.INCREMENTED, ChangeType.DECREMENTED]:
            try:
                old_val = int(self.old_value) if self.old_value is not None else 0
                new_val = int(self.new_value) if self.new_value is not None else 0
                return new_val - old_val
            except (ValueError, TypeError):
                return None
        return None
    
    def is_significant(self) -> bool:
        """Check if this change is significant enough to report."""
        return self.priority.value >= ChangePriority.MEDIUM.value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'field_path': self.field_path,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'change_type': self.change_type.value,
            'priority': self.priority.value,
            'category': self.category.value,
            'description': self.description,
            'confidence': self.confidence,
            'metadata': self.metadata,
            'detection_timestamp': self.detection_timestamp.isoformat()
        }


@dataclass
class ChangeGroup:
    """Represents a group of related changes."""
    group_id: str
    changes: List[FieldChange] = field(default_factory=list)
    group_type: str = "generic"
    priority: ChangePriority = ChangePriority.MEDIUM
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Ensure priority is always a ChangePriority enum."""
        if not isinstance(self.priority, ChangePriority):
            self.priority = ChangePriority.MEDIUM
    
    def add_change(self, change: FieldChange):
        """Add a change to this group."""
        self.changes.append(change)
        # Update group priority to highest change priority
        if change.priority.value > self.priority.value:
            self.priority = change.priority
    
    def get_highest_priority(self) -> ChangePriority:
        """Get the highest priority among all changes in this group."""
        if not self.changes:
            return self.priority
        return max(change.priority for change in self.changes)
    
    def get_changes_by_category(self, category: ChangeCategory) -> List[FieldChange]:
        """Get changes in this group by category."""
        return [change for change in self.changes if change.category == category]
    
    def is_significant(self) -> bool:
        """Check if this group contains significant changes."""
        return any(change.is_significant() for change in self.changes)


@dataclass
class CharacterSnapshot:
    """Represents a character data snapshot for comparison."""
    character_id: int
    character_name: str
    version: int
    timestamp: datetime
    character_data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_field_value(self, field_path: str) -> Any:
        """Get value of a specific field using dot notation."""
        try:
            current = self.character_data
            for key in field_path.split('.'):
                if isinstance(current, dict):
                    current = current.get(key)
                else:
                    return None
            return current
        except (AttributeError, KeyError, TypeError):
            return None
    
    def has_field(self, field_path: str) -> bool:
        """Check if a field exists in the character data."""
        return self.get_field_value(field_path) is not None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of this snapshot."""
        return {
            'character_id': self.character_id,
            'character_name': self.character_name,
            'version': self.version,
            'timestamp': self.timestamp.isoformat(),
            'data_size': len(str(self.character_data)),
            'metadata': self.metadata
        }


@dataclass
class CharacterChangeSet:
    """Collection of changes for a character with metadata."""
    character_id: int
    character_name: str
    from_version: int
    to_version: int
    timestamp: datetime
    changes: List[FieldChange] = field(default_factory=list)
    change_groups: List[ChangeGroup] = field(default_factory=list)
    summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_change(self, change: FieldChange):
        """Add a change to this changeset."""
        self.changes.append(change)
    
    def add_change_group(self, group: ChangeGroup):
        """Add a change group to this changeset."""
        self.change_groups.append(group)
    
    def get_changes_by_priority(self, min_priority: ChangePriority = ChangePriority.LOW) -> List[FieldChange]:
        """Get changes filtered by minimum priority."""
        return [change for change in self.changes if change.priority.value >= min_priority.value]
    
    def get_changes_by_type(self, change_type: ChangeType) -> List[FieldChange]:
        """Get changes filtered by type."""
        return [change for change in self.changes if change.change_type == change_type]
    
    def get_changes_by_category(self, category: ChangeCategory) -> List[FieldChange]:
        """Get changes filtered by category."""
        return [change for change in self.changes if change.category == category]
    
    def has_high_priority_changes(self) -> bool:
        """Check if any high priority changes exist."""
        return any(change.priority.value >= ChangePriority.HIGH.value for change in self.changes)
    
    def has_critical_changes(self) -> bool:
        """Check if any critical changes exist."""
        return any(change.priority.value >= ChangePriority.CRITICAL.value for change in self.changes)
    
    def get_change_count_by_category(self) -> Dict[ChangeCategory, int]:
        """Get count of changes by category."""
        counts = {}
        for change in self.changes:
            counts[change.category] = counts.get(change.category, 0) + 1
        return counts
    
    def get_priority_distribution(self) -> Dict[ChangePriority, int]:
        """Get distribution of changes by priority."""
        distribution = {}
        for change in self.changes:
            distribution[change.priority] = distribution.get(change.priority, 0) + 1
        return distribution
    
    def is_significant(self) -> bool:
        """Check if this changeset contains significant changes."""
        return any(change.is_significant() for change in self.changes)
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for this changeset."""
        return {
            'total_changes': len(self.changes),
            'total_groups': len(self.change_groups),
            'has_high_priority': self.has_high_priority_changes(),
            'has_critical': self.has_critical_changes(),
            'is_significant': self.is_significant(),
            'category_counts': self.get_change_count_by_category(),
            'priority_distribution': self.get_priority_distribution(),
            'from_version': self.from_version,
            'to_version': self.to_version,
            'timestamp': self.timestamp.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'character_id': self.character_id,
            'character_name': self.character_name,
            'from_version': self.from_version,
            'to_version': self.to_version,
            'timestamp': self.timestamp.isoformat(),
            'changes': [change.to_dict() for change in self.changes],
            'change_groups': [
                {
                    'group_id': group.group_id,
                    'group_type': group.group_type,
                    'priority': group.priority.value,
                    'description': group.description,
                    'change_count': len(group.changes),
                    'metadata': group.metadata
                }
                for group in self.change_groups
            ],
            'summary': self.summary,
            'metadata': self.metadata,
            'stats': self.get_summary_stats()
        }


@dataclass
class DetectionContext:
    """Context for change detection operations."""
    character_id: int
    character_name: str
    rule_version: str = "2014"
    detection_timestamp: datetime = field(default_factory=datetime.now)
    excluded_fields: Set[str] = field(default_factory=set)
    included_fields: Set[str] = field(default_factory=set)
    detection_settings: Dict[str, Any] = field(default_factory=dict)
    validation_enabled: bool = True
    significance_threshold: ChangePriority = ChangePriority.MEDIUM
    
    def should_detect_field(self, field_path: str) -> bool:
        """Check if a field should be detected based on inclusion/exclusion rules."""
        # If included_fields is specified, only detect those fields
        if self.included_fields:
            return field_path in self.included_fields
        
        # Otherwise, detect all fields except excluded ones
        return field_path not in self.excluded_fields
    
    def is_significant_priority(self, priority: ChangePriority) -> bool:
        """Check if a priority meets the significance threshold."""
        return priority.value >= self.significance_threshold.value


@dataclass
class DetectionResult:
    """Result of a change detection operation."""
    detector_name: str
    changes: List[FieldChange] = field(default_factory=list)
    execution_time: float = 0.0
    success: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_change(self, change: FieldChange):
        """Add a change to the detection result."""
        self.changes.append(change)
    
    def add_error(self, error: str):
        """Add an error to the detection result."""
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str):
        """Add a warning to the detection result."""
        self.warnings.append(warning)
    
    def get_significant_changes(self) -> List[FieldChange]:
        """Get only significant changes from the result."""
        return [change for change in self.changes if change.is_significant()]
    
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for this detection result."""
        return {
            'detector_name': self.detector_name,
            'total_changes': len(self.changes),
            'significant_changes': len(self.get_significant_changes()),
            'execution_time': self.execution_time,
            'success': self.success,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }


# Utility functions for working with models
def create_field_change(field_path: str, old_value: Any, new_value: Any,
                       change_type: ChangeType = None, priority: ChangePriority = None,
                       category: ChangeCategory = None, description: str = None) -> FieldChange:
    """
    Utility function to create a FieldChange with automatic type detection.
    """
    # Auto-detect change type if not provided
    if change_type is None:
        if old_value is None and new_value is not None:
            change_type = ChangeType.ADDED
        elif old_value is not None and new_value is None:
            change_type = ChangeType.REMOVED
        elif isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
            change_type = ChangeType.INCREMENTED if new_value > old_value else ChangeType.DECREMENTED
        else:
            change_type = ChangeType.MODIFIED
    
    # Auto-detect priority if not provided
    if priority is None:
        if change_type in [ChangeType.ADDED, ChangeType.REMOVED]:
            priority = ChangePriority.HIGH
        elif change_type in [ChangeType.INCREMENTED, ChangeType.DECREMENTED]:
            priority = ChangePriority.MEDIUM
        else:
            priority = ChangePriority.LOW
    
    # Auto-detect category if not provided
    if category is None:
        if field_path.startswith('basic_info'):
            category = ChangeCategory.BASIC_INFO
        elif field_path.startswith('ability_scores'):
            category = ChangeCategory.ABILITIES
        elif field_path.startswith('skills'):
            category = ChangeCategory.SKILLS
        elif field_path.startswith('spells'):
            category = ChangeCategory.SPELLS
        elif field_path.startswith('equipment'):
            category = ChangeCategory.EQUIPMENT
        elif field_path.startswith('class_features') or field_path.startswith('racial_traits'):
            category = ChangeCategory.FEATURES
        else:
            category = ChangeCategory.METADATA
    
    return FieldChange(
        field_path=field_path,
        old_value=old_value,
        new_value=new_value,
        change_type=change_type,
        priority=priority,
        category=category,
        description=description
    )


def group_changes_by_category(changes: List[FieldChange]) -> Dict[ChangeCategory, List[FieldChange]]:
    """Group changes by their category."""
    groups = {}
    for change in changes:
        if change.category not in groups:
            groups[change.category] = []
        groups[change.category].append(change)
    return groups


def filter_changes_by_priority(changes: List[FieldChange], 
                              min_priority: ChangePriority) -> List[FieldChange]:
    """Filter changes by minimum priority level."""
    return [change for change in changes if change.priority.value >= min_priority.value]


def merge_changesets(changesets: List[CharacterChangeSet]) -> CharacterChangeSet:
    """Merge multiple changesets into a single changeset."""
    if not changesets:
        raise ValueError("Cannot merge empty list of changesets")
    
    # Use the first changeset as the base
    base = changesets[0]
    merged = CharacterChangeSet(
        character_id=base.character_id,
        character_name=base.character_name,
        from_version=base.from_version,
        to_version=base.to_version,
        timestamp=base.timestamp,
        summary=base.summary,
        metadata=base.metadata.copy()
    )
    
    # Merge all changes
    for changeset in changesets:
        merged.changes.extend(changeset.changes)
        merged.change_groups.extend(changeset.change_groups)
    
    return merged