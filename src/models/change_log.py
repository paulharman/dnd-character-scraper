"""
Change Log Models

Enhanced data models for persistent change logging with detailed attribution and causation tracking.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from pathlib import Path

# Import existing change detection models
from src.models.change_detection import FieldChange, ChangeType, ChangePriority, ChangeCategory


@dataclass
class ChangeCausation:
    """Information about what caused a change."""
    trigger: str  # level_progression, feat_selection, equipment_change, etc.
    trigger_details: Dict[str, Any] = field(default_factory=dict)
    related_changes: List[str] = field(default_factory=list)  # Field paths of related changes
    cascade_depth: int = 0  # How many steps removed from the root cause
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'trigger': self.trigger,
            'trigger_details': self.trigger_details,
            'related_changes': self.related_changes,
            'cascade_depth': self.cascade_depth
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChangeCausation':
        """Create from dictionary."""
        return cls(
            trigger=data.get('trigger', ''),
            trigger_details=data.get('trigger_details', {}),
            related_changes=data.get('related_changes', []),
            cascade_depth=data.get('cascade_depth', 0)
        )


@dataclass
class ChangeAttribution:
    """Attribution information for a change."""
    source: str  # feat_selection, ability_improvement, equipment, etc.
    source_name: str  # Specific feat name, item name, etc.
    source_type: str  # feat, equipment, class_feature, etc.
    impact_summary: str  # Human-readable impact description
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'source': self.source,
            'source_name': self.source_name,
            'source_type': self.source_type,
            'impact_summary': self.impact_summary
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChangeAttribution':
        """Create from dictionary."""
        return cls(
            source=data.get('source', ''),
            source_name=data.get('source_name', ''),
            source_type=data.get('source_type', ''),
            impact_summary=data.get('impact_summary', '')
        )


@dataclass
class ChangeLogEntry:
    """Single change log entry with detailed attribution."""
    character_id: int
    character_name: str
    timestamp: datetime
    change_type: str
    category: ChangeCategory
    field_path: str
    old_value: Any
    new_value: Any
    description: str  # Brief description for Discord
    detailed_description: str  # Comprehensive description for logs
    priority: ChangePriority
    causation: Optional[ChangeCausation] = None
    attribution: Optional[ChangeAttribution] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Ensure enums are properly set."""
        if not isinstance(self.category, ChangeCategory):
            self.category = ChangeCategory.METADATA
        if not isinstance(self.priority, ChangePriority):
            self.priority = ChangePriority.MEDIUM
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'character_id': self.character_id,
            'character_name': self.character_name,
            'timestamp': self.timestamp.isoformat(),
            'change_type': self.change_type,
            'category': self.category.value,
            'field_path': self.field_path,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'description': self.description,
            'detailed_description': self.detailed_description,
            'priority': self.priority.value,
            'causation': self.causation.to_dict() if self.causation else None,
            'attribution': self.attribution.to_dict() if self.attribution else None,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChangeLogEntry':
        """Create from dictionary."""
        return cls(
            character_id=data.get('character_id', 0),
            character_name=data.get('character_name', ''),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            change_type=data.get('change_type', ''),
            category=ChangeCategory(data.get('category', ChangeCategory.METADATA.value)),
            field_path=data.get('field_path', ''),
            old_value=data.get('old_value'),
            new_value=data.get('new_value'),
            description=data.get('description', ''),
            detailed_description=data.get('detailed_description', ''),
            priority=ChangePriority(data.get('priority', ChangePriority.MEDIUM.value)),
            causation=ChangeCausation.from_dict(data['causation']) if data.get('causation') else None,
            attribution=ChangeAttribution.from_dict(data['attribution']) if data.get('attribution') else None,
            metadata=data.get('metadata', {})
        )
    
    @classmethod
    def from_field_change(cls, field_change: FieldChange, character_id: int, character_name: str,
                         causation: Optional[ChangeCausation] = None,
                         attribution: Optional[ChangeAttribution] = None,
                         detailed_description: Optional[str] = None) -> 'ChangeLogEntry':
        """Create from a FieldChange object."""
        return cls(
            character_id=character_id,
            character_name=character_name,
            timestamp=field_change.timestamp,
            change_type=field_change.change_type.value,
            category=field_change.category,
            field_path=field_change.field_path,
            old_value=field_change.old_value,
            new_value=field_change.new_value,
            description=field_change.description or '',
            detailed_description=detailed_description or field_change.description or '',
            priority=field_change.priority,
            causation=causation,
            attribution=attribution,
            metadata=field_change.metadata.copy()
        )


@dataclass
class ChangeLogConfig:
    """Configuration for change log service."""
    storage_dir: Path = field(default_factory=lambda: Path("character_data/change_logs"))
    log_rotation_size_mb: int = 10
    log_retention_days: int = 365
    enable_causation_analysis: bool = True
    enable_detailed_descriptions: bool = True
    backup_old_logs: bool = True
    
    def __post_init__(self):
        """Ensure storage_dir is a Path object."""
        if not isinstance(self.storage_dir, Path):
            self.storage_dir = Path(self.storage_dir)


@dataclass
class ChangeLogMetadata:
    """Metadata for a change log file."""
    character_id: int
    character_name: str
    log_version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    total_entries: int = 0
    log_file_size: int = 0
    rotation_count: int = 0
    retention_policy_days: int = 365
    discord_notifications_sent: int = 0
    change_categories: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'character_id': self.character_id,
            'character_name': self.character_name,
            'log_version': self.log_version,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'total_entries': self.total_entries,
            'log_file_size': self.log_file_size,
            'rotation_count': self.rotation_count,
            'retention_policy_days': self.retention_policy_days,
            'discord_notifications_sent': self.discord_notifications_sent,
            'change_categories': self.change_categories
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChangeLogMetadata':
        """Create from dictionary."""
        return cls(
            character_id=data.get('character_id', 0),
            character_name=data.get('character_name', ''),
            log_version=data.get('log_version', '1.0'),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            last_updated=datetime.fromisoformat(data.get('last_updated', datetime.now().isoformat())),
            total_entries=data.get('total_entries', 0),
            log_file_size=data.get('log_file_size', 0),
            rotation_count=data.get('rotation_count', 0),
            retention_policy_days=data.get('retention_policy_days', 365),
            discord_notifications_sent=data.get('discord_notifications_sent', 0),
            change_categories=data.get('change_categories', {})
        )


@dataclass
class ChangeLogFile:
    """Represents a complete change log file."""
    metadata: ChangeLogMetadata
    entries: List[ChangeLogEntry] = field(default_factory=list)
    
    def add_entry(self, entry: ChangeLogEntry):
        """Add an entry to the log file."""
        self.entries.append(entry)
        self.metadata.total_entries = len(self.entries)
        self.metadata.last_updated = datetime.now()
        
        # Update category counts
        category_key = entry.category.value
        if category_key not in self.metadata.change_categories:
            self.metadata.change_categories[category_key] = 0
        self.metadata.change_categories[category_key] += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            **self.metadata.to_dict(),
            'entries': [entry.to_dict() for entry in self.entries]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChangeLogFile':
        """Create from dictionary."""
        # Extract metadata (all fields except 'entries')
        metadata_data = {k: v for k, v in data.items() if k != 'entries'}
        metadata = ChangeLogMetadata.from_dict(metadata_data)
        
        # Extract entries
        entries = [ChangeLogEntry.from_dict(entry_data) for entry_data in data.get('entries', [])]
        
        return cls(metadata=metadata, entries=entries)
    
    def get_entries_by_date_range(self, start_date: datetime, end_date: datetime) -> List[ChangeLogEntry]:
        """Get entries within a date range."""
        return [entry for entry in self.entries 
                if start_date <= entry.timestamp <= end_date]
    
    def get_entries_by_category(self, category: ChangeCategory) -> List[ChangeLogEntry]:
        """Get entries by category."""
        return [entry for entry in self.entries if entry.category == category]
    
    def get_entries_by_cause(self, cause_type: str, cause_name: str) -> List[ChangeLogEntry]:
        """Get entries caused by a specific source."""
        return [entry for entry in self.entries 
                if entry.attribution and 
                entry.attribution.source == cause_type and 
                entry.attribution.source_name == cause_name]