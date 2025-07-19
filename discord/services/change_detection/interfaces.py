"""
Change detection interfaces for the DnD character tracking system.

This module defines the core interfaces for detecting changes in character
data, including field-level changes, snapshots, and change aggregation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Set
from dataclasses import dataclass
from enum import Enum
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
class ChangeContext:
    """Context information for change detection."""
    character_id: int
    character_name: str
    rule_version: str
    detection_timestamp: datetime
    detection_settings: Dict[str, Any]
    validation_rules: Dict[str, Any]
    snapshot_metadata: Dict[str, Any]
    
    def __post_init__(self):
        if self.detection_settings is None:
            self.detection_settings = {}
        if self.validation_rules is None:
            self.validation_rules = {}
        if self.snapshot_metadata is None:
            self.snapshot_metadata = {}


@dataclass
class FieldChange:
    """Represents a single field change with full context."""
    field_path: str
    old_value: Any
    new_value: Any
    change_type: ChangeType
    priority: ChangePriority
    category: ChangeCategory
    description: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = None
    detection_timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.detection_timestamp is None:
            self.detection_timestamp = datetime.now()


@dataclass
class ChangeGroup:
    """Represents a group of related changes."""
    group_id: str
    changes: List[FieldChange]
    group_type: str
    priority: ChangePriority
    description: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DetectionResult:
    """Result of a change detection operation."""
    detector_name: str
    changes: List[FieldChange]
    execution_time: float
    success: bool
    errors: List[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ValidationResult:
    """Result of change validation."""
    is_valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    corrected_changes: List[FieldChange] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.corrected_changes is None:
            self.corrected_changes = []


class IChangeDetector(ABC):
    """
    Base interface for all change detectors.
    
    Change detectors are responsible for identifying specific types of
    changes between character snapshots.
    """
    
    @property
    @abstractmethod
    def detector_name(self) -> str:
        """Get the unique detector name."""
        pass
    
    @property
    @abstractmethod
    def supported_categories(self) -> List[ChangeCategory]:
        """Get the change categories this detector supports."""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """Get the detector priority (lower = higher priority)."""
        pass
    
    @abstractmethod
    def detect_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any], 
                      context: ChangeContext) -> DetectionResult:
        """
        Detect changes between old and new data.
        
        Args:
            old_data: Previous character data
            new_data: Current character data
            context: Change detection context
            
        Returns:
            DetectionResult with found changes
        """
        pass
    
    @abstractmethod
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """
        Validate that the input data is suitable for this detector.
        
        Args:
            data: Character data to validate
            
        Returns:
            True if data is valid for this detector
        """
        pass
    
    @abstractmethod
    def get_supported_fields(self) -> List[str]:
        """
        Get list of field paths this detector supports.
        
        Returns:
            List of field paths (supports wildcards)
        """
        pass
    
    @abstractmethod
    def can_detect(self, field_path: str) -> bool:
        """
        Check if this detector can detect changes for a specific field.
        
        Args:
            field_path: The field path to check
            
        Returns:
            True if detector can handle this field
        """
        pass


class ISnapshotDetector(ABC):
    """
    Interface for snapshot-level change detection.
    
    Handles comparison of complete character snapshots and coordinates
    multiple field-level detectors.
    """
    
    @abstractmethod
    def compare_snapshots(self, old_snapshot: 'CharacterSnapshot', 
                         new_snapshot: 'CharacterSnapshot') -> 'CharacterChangeSet':
        """
        Compare two character snapshots and detect all changes.
        
        Args:
            old_snapshot: Previous character snapshot
            new_snapshot: Current character snapshot
            
        Returns:
            Complete set of detected changes
        """
        pass
    
    @abstractmethod
    def validate_snapshots(self, old_snapshot: 'CharacterSnapshot', 
                          new_snapshot: 'CharacterSnapshot') -> ValidationResult:
        """
        Validate that snapshots are compatible for comparison.
        
        Args:
            old_snapshot: Previous character snapshot
            new_snapshot: Current character snapshot
            
        Returns:
            Validation result
        """
        pass
    
    @abstractmethod
    def get_snapshot_summary(self, snapshot: 'CharacterSnapshot') -> Dict[str, Any]:
        """
        Get a summary of a character snapshot.
        
        Args:
            snapshot: Character snapshot to summarize
            
        Returns:
            Summary information
        """
        pass


class IChangeAggregator(ABC):
    """
    Interface for aggregating and grouping related changes.
    
    Responsible for organizing individual field changes into logical
    groups and reducing noise in change detection.
    """
    
    @abstractmethod
    def aggregate_changes(self, changes: List[FieldChange], 
                         context: ChangeContext) -> List[ChangeGroup]:
        """
        Aggregate individual changes into logical groups.
        
        Args:
            changes: List of individual field changes
            context: Change detection context
            
        Returns:
            List of change groups
        """
        pass
    
    @abstractmethod
    def deduplicate_changes(self, changes: List[FieldChange]) -> List[FieldChange]:
        """
        Remove duplicate or redundant changes.
        
        Args:
            changes: List of changes to deduplicate
            
        Returns:
            Deduplicated list of changes
        """
        pass
    
    @abstractmethod
    def merge_related_changes(self, changes: List[FieldChange]) -> List[FieldChange]:
        """
        Merge related changes into single changes where appropriate.
        
        Args:
            changes: List of changes to merge
            
        Returns:
            List of merged changes
        """
        pass
    
    @abstractmethod
    def prioritize_changes(self, changes: List[FieldChange], 
                          context: ChangeContext) -> List[FieldChange]:
        """
        Assign priorities to changes based on context.
        
        Args:
            changes: List of changes to prioritize
            context: Change detection context
            
        Returns:
            List of changes with updated priorities
        """
        pass


class IChangeValidator(ABC):
    """
    Interface for validating detected changes.
    
    Ensures that detected changes are accurate and consistent with
    the character data and game rules.
    """
    
    @abstractmethod
    def validate_change(self, change: FieldChange, context: ChangeContext) -> ValidationResult:
        """
        Validate a single change.
        
        Args:
            change: The change to validate
            context: Change detection context
            
        Returns:
            Validation result
        """
        pass
    
    @abstractmethod
    def validate_changes(self, changes: List[FieldChange], 
                        context: ChangeContext) -> ValidationResult:
        """
        Validate a list of changes for consistency.
        
        Args:
            changes: List of changes to validate
            context: Change detection context
            
        Returns:
            Validation result
        """
        pass
    
    @abstractmethod
    def validate_change_logic(self, change: FieldChange, 
                             old_data: Dict[str, Any], 
                             new_data: Dict[str, Any]) -> bool:
        """
        Validate that a change makes logical sense.
        
        Args:
            change: The change to validate
            old_data: Previous character data
            new_data: Current character data
            
        Returns:
            True if change is logically valid
        """
        pass
    
    @abstractmethod
    def get_validation_rules(self) -> Dict[str, Any]:
        """
        Get the validation rules used by this validator.
        
        Returns:
            Dictionary of validation rules
        """
        pass


class IChangeFilter(ABC):
    """
    Interface for filtering detected changes.
    
    Provides filtering capabilities to focus on specific types of
    changes or exclude noise.
    """
    
    @abstractmethod
    def filter_changes(self, changes: List[FieldChange], 
                      filter_criteria: Dict[str, Any]) -> List[FieldChange]:
        """
        Filter changes based on criteria.
        
        Args:
            changes: List of changes to filter
            filter_criteria: Filtering criteria
            
        Returns:
            Filtered list of changes
        """
        pass
    
    @abstractmethod
    def filter_by_category(self, changes: List[FieldChange], 
                          categories: List[ChangeCategory]) -> List[FieldChange]:
        """
        Filter changes by category.
        
        Args:
            changes: List of changes to filter
            categories: Categories to include
            
        Returns:
            Filtered list of changes
        """
        pass
    
    @abstractmethod
    def filter_by_priority(self, changes: List[FieldChange], 
                          min_priority: ChangePriority) -> List[FieldChange]:
        """
        Filter changes by minimum priority.
        
        Args:
            changes: List of changes to filter
            min_priority: Minimum priority to include
            
        Returns:
            Filtered list of changes
        """
        pass
    
    @abstractmethod
    def filter_by_field_pattern(self, changes: List[FieldChange], 
                               patterns: List[str]) -> List[FieldChange]:
        """
        Filter changes by field path patterns.
        
        Args:
            changes: List of changes to filter
            patterns: Field path patterns to include
            
        Returns:
            Filtered list of changes
        """
        pass


class IChangeDetectionFactory(ABC):
    """
    Interface for creating change detection components.
    
    Provides factory methods for creating and configuring
    change detectors with proper dependencies.
    """
    
    @abstractmethod
    def create_detector(self, detector_type: str, config: Dict[str, Any]) -> IChangeDetector:
        """
        Create a change detector of the specified type.
        
        Args:
            detector_type: Type of detector to create
            config: Configuration for the detector
            
        Returns:
            Configured change detector
        """
        pass
    
    @abstractmethod
    def create_snapshot_detector(self, detectors: List[IChangeDetector], 
                                config: Dict[str, Any]) -> ISnapshotDetector:
        """
        Create a snapshot detector with the given field detectors.
        
        Args:
            detectors: List of field-level detectors
            config: Configuration for the snapshot detector
            
        Returns:
            Configured snapshot detector
        """
        pass
    
    @abstractmethod
    def create_aggregator(self, config: Dict[str, Any]) -> IChangeAggregator:
        """
        Create a change aggregator.
        
        Args:
            config: Configuration for the aggregator
            
        Returns:
            Configured change aggregator
        """
        pass
    
    @abstractmethod
    def create_validator(self, config: Dict[str, Any]) -> IChangeValidator:
        """
        Create a change validator.
        
        Args:
            config: Configuration for the validator
            
        Returns:
            Configured change validator
        """
        pass
    
    @abstractmethod
    def get_available_detectors(self) -> List[str]:
        """
        Get list of available detector types.
        
        Returns:
            List of detector type names
        """
        pass


class IChangeDetectionService(ABC):
    """
    Interface for the main change detection service.
    
    Coordinates all change detection components to provide
    a complete change detection pipeline.
    """
    
    @abstractmethod
    def detect_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any], 
                      context: ChangeContext) -> 'CharacterChangeSet':
        """
        Detect all changes between old and new character data.
        
        Args:
            old_data: Previous character data
            new_data: Current character data
            context: Change detection context
            
        Returns:
            Complete set of detected changes
        """
        pass
    
    @abstractmethod
    def register_detector(self, detector: IChangeDetector) -> None:
        """
        Register a change detector with the service.
        
        Args:
            detector: The change detector to register
        """
        pass
    
    @abstractmethod
    def unregister_detector(self, detector_name: str) -> None:
        """
        Unregister a change detector.
        
        Args:
            detector_name: Name of the detector to unregister
        """
        pass
    
    @abstractmethod
    def get_supported_categories(self) -> List[ChangeCategory]:
        """
        Get all supported change categories.
        
        Returns:
            List of supported categories
        """
        pass
    
    @abstractmethod
    def configure_detection(self, config: Dict[str, Any]) -> None:
        """
        Configure detection settings.
        
        Args:
            config: Detection configuration
        """
        pass