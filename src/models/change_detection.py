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
    """Represents a single field change with enhanced metadata."""
    field_path: str
    old_value: Any
    new_value: Any
    change_type: ChangeType
    description: str
    priority: ChangePriority
    category: ChangeCategory
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'field_path': self.field_path,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'change_type': self.change_type.value,
            'description': self.description,
            'priority': self.priority.value,
            'category': self.category.value,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class DetectionContext:
    """Context information for change detection."""
    character_id: str
    character_name: str = ""
    detection_timestamp: datetime = field(default_factory=datetime.now)
    comparison_files: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChangeDetectionResult:
    """Result of change detection operation."""
    character_id: str
    changes: List[FieldChange]
    context: DetectionContext
    detection_timestamp: datetime = field(default_factory=datetime.now)
    total_changes: int = field(init=False)
    changes_by_category: Dict[str, int] = field(init=False)
    changes_by_priority: Dict[str, int] = field(init=False)
    
    def __post_init__(self):
        """Calculate summary statistics."""
        self.total_changes = len(self.changes)
        
        # Count by category
        self.changes_by_category = {}
        for change in self.changes:
            category = change.category.value
            self.changes_by_category[category] = self.changes_by_category.get(category, 0) + 1
        
        # Count by priority
        self.changes_by_priority = {}
        for change in self.changes:
            priority = change.priority.value
            self.changes_by_priority[priority] = self.changes_by_priority.get(priority, 0) + 1
    
    def get_changes_by_category(self, category: ChangeCategory) -> List[FieldChange]:
        """Get all changes for a specific category."""
        return [change for change in self.changes if change.category == category]
    
    def get_changes_by_priority(self, priority: ChangePriority) -> List[FieldChange]:
        """Get all changes for a specific priority level."""
        return [change for change in self.changes if change.priority == priority]
    
    def has_high_priority_changes(self) -> bool:
        """Check if there are any high or critical priority changes."""
        return any(change.priority in [ChangePriority.HIGH, ChangePriority.CRITICAL] 
                  for change in self.changes)