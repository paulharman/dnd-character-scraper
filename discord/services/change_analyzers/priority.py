"""
Priority Analysis for Change Detection

Provides priority assessment for character changes based on field importance,
change magnitude, and context-specific rules.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from enum import Enum
from dataclasses import dataclass
import re

from ..change_detection.models import FieldChange, ChangeType, ChangePriority, ChangeCategory

logger = logging.getLogger(__name__)


class PriorityRule(Enum):
    """Types of priority rules."""
    FIELD_BASED = "field_based"
    CHANGE_TYPE_BASED = "change_type_based"
    MAGNITUDE_BASED = "magnitude_based"
    CONTEXT_BASED = "context_based"


@dataclass
class PriorityRuleDefinition:
    """Definition of a priority rule."""
    rule_type: PriorityRule
    field_patterns: List[str]
    conditions: Dict[str, Any]
    priority: ChangePriority
    description: str
    weight: float = 1.0


class PriorityAnalyzer:
    """Analyzes and assigns priorities to character changes."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load priority rules
        self.priority_rules = self._load_priority_rules()
        
        # Field importance mappings
        self.field_importance = self._load_field_importance()
        
        # Context-specific multipliers
        self.context_multipliers = self._load_context_multipliers()
    
    def analyze_priority(self, change: FieldChange, context: Dict[str, Any] = None) -> ChangePriority:
        """Analyze and assign priority to a change."""
        context = context or {}
        
        # Start with the change's current priority
        base_priority = change.priority
        
        # Apply field-based rules
        field_priority = self._analyze_field_priority(change.field_path, change.old_value, change.new_value)
        
        # Apply change type rules
        type_priority = self._analyze_change_type_priority(change.change_type, change.old_value, change.new_value)
        
        # Apply magnitude-based rules
        magnitude_priority = self._analyze_magnitude_priority(change)
        
        # Apply context rules
        context_priority = self._analyze_context_priority(change, context)
        
        # Combine priorities using weighted average
        priorities = [
            (base_priority, 1.0),
            (field_priority, 2.0),
            (type_priority, 1.5),
            (magnitude_priority, 1.0),
            (context_priority, 1.5)
        ]
        
        final_priority = self._combine_priorities(priorities)
        
        self.logger.debug(f"Priority analysis for {change.field_path}: {base_priority} → {final_priority}")
        
        return final_priority
    
    def analyze_batch_priority(self, changes: List[FieldChange], context: Dict[str, Any] = None) -> List[FieldChange]:
        """Analyze priorities for a batch of changes."""
        context = context or {}
        
        # Analyze individual priorities
        for change in changes:
            change.priority = self.analyze_priority(change, context)
        
        # Apply batch-specific rules
        self._apply_batch_rules(changes, context)
        
        return changes
    
    def get_priority_distribution(self, changes: List[FieldChange]) -> Dict[ChangePriority, int]:
        """Get distribution of priorities in a list of changes."""
        distribution = {}
        for change in changes:
            distribution[change.priority] = distribution.get(change.priority, 0) + 1
        return distribution
    
    def _load_priority_rules(self) -> List[PriorityRuleDefinition]:
        """Load priority rules from configuration."""
        rules = []
        
        # Critical priority rules
        rules.extend([
            PriorityRuleDefinition(
                rule_type=PriorityRule.FIELD_BASED,
                field_patterns=['basic_info.level'],
                conditions={'change_type': [ChangeType.INCREMENTED, ChangeType.DECREMENTED]},
                priority=ChangePriority.CRITICAL,
                description="Character level changes are critical",
                weight=3.0
            ),
            PriorityRuleDefinition(
                rule_type=PriorityRule.FIELD_BASED,
                field_patterns=['basic_info.hit_points'],
                conditions={'magnitude_threshold': 10},
                priority=ChangePriority.CRITICAL,
                description="Major hit point changes are critical",
                weight=2.5
            ),
            PriorityRuleDefinition(
                rule_type=PriorityRule.CHANGE_TYPE_BASED,
                field_patterns=['spells.known_spells.*'],
                conditions={'change_type': [ChangeType.ADDED, ChangeType.REMOVED]},
                priority=ChangePriority.HIGH,
                description="Spell additions/removals are high priority",
                weight=2.0
            )
        ])
        
        # High priority rules
        rules.extend([
            PriorityRuleDefinition(
                rule_type=PriorityRule.FIELD_BASED,
                field_patterns=['basic_info.class', 'basic_info.race', 'basic_info.name'],
                conditions={},
                priority=ChangePriority.HIGH,
                description="Core character info changes are high priority",
                weight=2.0
            ),
            PriorityRuleDefinition(
                rule_type=PriorityRule.FIELD_BASED,
                field_patterns=['ability_scores.*'],
                conditions={'magnitude_threshold': 2},
                priority=ChangePriority.HIGH,
                description="Significant ability score changes are high priority",
                weight=1.8
            ),
            PriorityRuleDefinition(
                rule_type=PriorityRule.FIELD_BASED,
                field_patterns=['class_features.*', 'racial_traits.*', 'feats.*'],
                conditions={'change_type': [ChangeType.ADDED, ChangeType.REMOVED]},
                priority=ChangePriority.HIGH,
                description="Feature additions/removals are high priority",
                weight=1.8
            )
        ])
        
        # Medium priority rules
        rules.extend([
            PriorityRuleDefinition(
                rule_type=PriorityRule.FIELD_BASED,
                field_patterns=['skills.*.proficient'],
                conditions={'change_type': [ChangeType.ADDED, ChangeType.REMOVED]},
                priority=ChangePriority.MEDIUM,
                description="Skill proficiency changes are medium priority",
                weight=1.5
            ),
            PriorityRuleDefinition(
                rule_type=PriorityRule.FIELD_BASED,
                field_patterns=['equipment.*'],
                conditions={'change_type': [ChangeType.ADDED, ChangeType.REMOVED]},
                priority=ChangePriority.MEDIUM,
                description="Equipment changes are medium priority",
                weight=1.2
            ),
            PriorityRuleDefinition(
                rule_type=PriorityRule.FIELD_BASED,
                field_patterns=['basic_info.armor_class'],
                conditions={'magnitude_threshold': 1},
                priority=ChangePriority.MEDIUM,
                description="AC changes are medium priority",
                weight=1.5
            )
        ])
        
        # Low priority rules
        rules.extend([
            PriorityRuleDefinition(
                rule_type=PriorityRule.FIELD_BASED,
                field_patterns=['equipment.*.quantity'],
                conditions={'change_type': [ChangeType.INCREMENTED, ChangeType.DECREMENTED]},
                priority=ChangePriority.LOW,
                description="Equipment quantity changes are low priority",
                weight=1.0
            ),
            PriorityRuleDefinition(
                rule_type=PriorityRule.FIELD_BASED,
                field_patterns=['metadata.*'],
                conditions={},
                priority=ChangePriority.LOW,
                description="Metadata changes are low priority",
                weight=0.5
            )
        ])
        
        return rules
    
    def _load_field_importance(self) -> Dict[str, float]:
        """Load field importance mappings."""
        return {
            # Critical fields
            'basic_info.level': 1.0,
            'basic_info.hit_points': 0.9,
            'basic_info.name': 0.8,
            
            # High importance fields
            'basic_info.class': 0.8,
            'basic_info.race': 0.8,
            'basic_info.armor_class': 0.7,
            'ability_scores': 0.7,
            'spells.known_spells': 0.7,
            'class_features': 0.7,
            'racial_traits': 0.7,
            'feats': 0.7,
            
            # Medium importance fields
            'skills': 0.6,
            'equipment': 0.5,
            'basic_info.background': 0.5,
            'basic_info.alignment': 0.4,
            'basic_info.experience_points': 0.4,
            
            # Low importance fields
            'metadata': 0.2,
            'temporary': 0.1
        }
    
    def _load_context_multipliers(self) -> Dict[str, float]:
        """Load context-specific priority multipliers."""
        return {
            'combat_active': 1.5,
            'level_up': 2.0,
            'new_character': 0.8,
            'bulk_update': 0.7,
            'automated_update': 0.6
        }
    
    def _analyze_field_priority(self, field_path: str, old_value: Any, new_value: Any) -> ChangePriority:
        """Analyze priority based on field path."""
        # Check against priority rules
        for rule in self.priority_rules:
            if rule.rule_type == PriorityRule.FIELD_BASED:
                if self._matches_field_patterns(field_path, rule.field_patterns):
                    if self._meets_conditions(rule.conditions, old_value, new_value):
                        return rule.priority
        
        # Check field importance
        importance = self._get_field_importance(field_path)
        if importance >= 0.8:
            return ChangePriority.HIGH
        elif importance >= 0.6:
            return ChangePriority.MEDIUM
        elif importance >= 0.4:
            return ChangePriority.LOW
        else:
            return ChangePriority.LOW
    
    def _analyze_change_type_priority(self, change_type: ChangeType, old_value: Any, new_value: Any) -> ChangePriority:
        """Analyze priority based on change type."""
        # Check type-based rules
        for rule in self.priority_rules:
            if rule.rule_type == PriorityRule.CHANGE_TYPE_BASED:
                if self._meets_conditions(rule.conditions, old_value, new_value, change_type):
                    return rule.priority
        
        # Default type-based priorities
        if change_type in [ChangeType.ADDED, ChangeType.REMOVED]:
            return ChangePriority.MEDIUM
        elif change_type in [ChangeType.INCREMENTED, ChangeType.DECREMENTED]:
            return ChangePriority.LOW
        else:
            return ChangePriority.LOW
    
    def _analyze_magnitude_priority(self, change: FieldChange) -> ChangePriority:
        """Analyze priority based on change magnitude."""
        # Check magnitude-based rules
        for rule in self.priority_rules:
            if rule.rule_type == PriorityRule.MAGNITUDE_BASED:
                if self._matches_field_patterns(change.field_path, rule.field_patterns):
                    magnitude = self._get_change_magnitude(change.old_value, change.new_value)
                    if magnitude and 'magnitude_threshold' in rule.conditions:
                        if magnitude >= rule.conditions['magnitude_threshold']:
                            return rule.priority
        
        # Default magnitude-based logic
        magnitude = self._get_change_magnitude(change.old_value, change.new_value)
        if magnitude is None:
            return ChangePriority.MEDIUM
        
        if magnitude >= 10:
            return ChangePriority.HIGH
        elif magnitude >= 5:
            return ChangePriority.MEDIUM
        else:
            return ChangePriority.LOW
    
    def _analyze_context_priority(self, change: FieldChange, context: Dict[str, Any]) -> ChangePriority:
        """Analyze priority based on context."""
        base_priority = change.priority
        
        # Apply context multipliers
        multiplier = 1.0
        for context_key, context_multiplier in self.context_multipliers.items():
            if context.get(context_key, False):
                multiplier *= context_multiplier
        
        # Adjust priority based on multiplier
        if multiplier >= 1.5:
            return self._increase_priority(base_priority)
        elif multiplier <= 0.7:
            return self._decrease_priority(base_priority)
        else:
            return base_priority
    
    def _combine_priorities(self, priorities: List[tuple]) -> ChangePriority:
        """Combine multiple priorities using weighted average."""
        if not priorities:
            return ChangePriority.MEDIUM
        
        # Calculate weighted average
        total_weight = sum(weight for _, weight in priorities)
        weighted_sum = sum(priority.value * weight for priority, weight in priorities)
        
        if total_weight == 0:
            return ChangePriority.MEDIUM
        
        average_value = weighted_sum / total_weight
        
        # Map back to enum
        if average_value >= 3.5:
            return ChangePriority.CRITICAL
        elif average_value >= 2.5:
            return ChangePriority.HIGH
        elif average_value >= 1.5:
            return ChangePriority.MEDIUM
        else:
            return ChangePriority.LOW
    
    def _apply_batch_rules(self, changes: List[FieldChange], context: Dict[str, Any]):
        """Apply batch-specific priority rules."""
        if not changes:
            return
        
        # Rule: If there are many changes, reduce priority of individual changes
        if len(changes) > 20:
            for change in changes:
                if change.priority == ChangePriority.LOW:
                    # Don't reduce LOW priority further
                    continue
                change.priority = self._decrease_priority(change.priority)
        
        # Rule: If there's a critical change, boost related changes
        critical_changes = [c for c in changes if c.priority == ChangePriority.CRITICAL]
        if critical_changes:
            # Find changes related to critical changes
            for critical_change in critical_changes:
                related_changes = self._find_related_changes(critical_change, changes)
                for related_change in related_changes:
                    if related_change.priority == ChangePriority.LOW:
                        related_change.priority = ChangePriority.MEDIUM
    
    def _matches_field_patterns(self, field_path: str, patterns: List[str]) -> bool:
        """Check if field path matches any of the patterns."""
        import fnmatch
        return any(fnmatch.fnmatch(field_path, pattern) for pattern in patterns)
    
    def _meets_conditions(self, conditions: Dict[str, Any], old_value: Any, new_value: Any, 
                         change_type: ChangeType = None) -> bool:
        """Check if conditions are met."""
        if not conditions:
            return True
        
        # Check change type condition
        if 'change_type' in conditions:
            if change_type is None:
                change_type = self._get_change_type(old_value, new_value)
            if change_type not in conditions['change_type']:
                return False
        
        # Check magnitude threshold
        if 'magnitude_threshold' in conditions:
            magnitude = self._get_change_magnitude(old_value, new_value)
            if magnitude is None or magnitude < conditions['magnitude_threshold']:
                return False
        
        return True
    
    def _get_field_importance(self, field_path: str) -> float:
        """Get importance score for a field path."""
        # Check exact matches first
        if field_path in self.field_importance:
            return self.field_importance[field_path]
        
        # Check pattern matches
        for pattern, importance in self.field_importance.items():
            if self._matches_field_patterns(field_path, [pattern]):
                return importance
        
        # Check parent paths
        parts = field_path.split('.')
        for i in range(len(parts) - 1, 0, -1):
            parent_path = '.'.join(parts[:i])
            if parent_path in self.field_importance:
                return self.field_importance[parent_path] * 0.8  # Reduce importance for children
        
        return 0.3  # Default importance
    
    def _get_change_type(self, old_value: Any, new_value: Any) -> ChangeType:
        """Determine change type from values."""
        if old_value is None and new_value is not None:
            return ChangeType.ADDED
        elif old_value is not None and new_value is None:
            return ChangeType.REMOVED
        elif isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
            return ChangeType.INCREMENTED if new_value > old_value else ChangeType.DECREMENTED
        else:
            return ChangeType.MODIFIED
    
    def _get_change_magnitude(self, old_value: Any, new_value: Any) -> Optional[float]:
        """Get magnitude of change."""
        if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
            return abs(new_value - old_value)
        elif isinstance(old_value, str) and isinstance(new_value, str):
            return abs(len(new_value) - len(old_value))
        elif isinstance(old_value, (list, dict)) and isinstance(new_value, (list, dict)):
            try:
                return abs(len(new_value) - len(old_value))
            except TypeError:
                return None
        return None
    
    def _increase_priority(self, priority: ChangePriority) -> ChangePriority:
        """Increase priority by one level."""
        priority_order = [ChangePriority.LOW, ChangePriority.MEDIUM, ChangePriority.HIGH, ChangePriority.CRITICAL]
        current_index = priority_order.index(priority)
        if current_index < len(priority_order) - 1:
            return priority_order[current_index + 1]
        return priority
    
    def _decrease_priority(self, priority: ChangePriority) -> ChangePriority:
        """Decrease priority by one level."""
        priority_order = [ChangePriority.LOW, ChangePriority.MEDIUM, ChangePriority.HIGH, ChangePriority.CRITICAL]
        current_index = priority_order.index(priority)
        if current_index > 0:
            return priority_order[current_index - 1]
        return priority
    
    def _find_related_changes(self, target_change: FieldChange, all_changes: List[FieldChange]) -> List[FieldChange]:
        """Find changes related to a target change."""
        related = []
        target_parts = target_change.field_path.split('.')
        
        for change in all_changes:
            if change == target_change:
                continue
            
            change_parts = change.field_path.split('.')
            
            # Check if they share a common parent
            common_parts = 0
            for i in range(min(len(target_parts), len(change_parts))):
                if target_parts[i] == change_parts[i]:
                    common_parts += 1
                else:
                    break
            
            # Consider related if they share at least 2 path components
            if common_parts >= 2:
                related.append(change)
        
        return related


class PriorityRuleEngine:
    """Engine for managing and applying priority rules."""
    
    def __init__(self, rules: List[PriorityRuleDefinition] = None):
        self.rules = rules or []
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def add_rule(self, rule: PriorityRuleDefinition):
        """Add a priority rule."""
        self.rules.append(rule)
        self.logger.info(f"Added priority rule: {rule.description}")
    
    def remove_rule(self, rule_description: str):
        """Remove a priority rule by description."""
        self.rules = [rule for rule in self.rules if rule.description != rule_description]
        self.logger.info(f"Removed priority rule: {rule_description}")
    
    def apply_rules(self, change: FieldChange) -> List[ChangePriority]:
        """Apply all matching rules to a change."""
        matching_priorities = []
        
        for rule in self.rules:
            if self._rule_matches_change(rule, change):
                matching_priorities.append(rule.priority)
        
        return matching_priorities
    
    def _rule_matches_change(self, rule: PriorityRuleDefinition, change: FieldChange) -> bool:
        """Check if a rule matches a change."""
        # Check field patterns
        if rule.field_patterns:
            import fnmatch
            if not any(fnmatch.fnmatch(change.field_path, pattern) for pattern in rule.field_patterns):
                return False
        
        # Check conditions
        if rule.conditions:
            if 'change_type' in rule.conditions:
                if change.change_type not in rule.conditions['change_type']:
                    return False
            
            if 'magnitude_threshold' in rule.conditions:
                magnitude = self._get_change_magnitude(change.old_value, change.new_value)
                if magnitude is None or magnitude < rule.conditions['magnitude_threshold']:
                    return False
        
        return True
    
    def _get_change_magnitude(self, old_value: Any, new_value: Any) -> Optional[float]:
        """Get magnitude of change."""
        if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
            return abs(new_value - old_value)
        return None


# Factory function for creating priority analyzer
def create_priority_analyzer(config: Dict[str, Any] = None) -> PriorityAnalyzer:
    """Create a priority analyzer with default configuration."""
    return PriorityAnalyzer(config)


# Utility functions for priority management
def get_priority_level_name(priority: ChangePriority) -> str:
    """Get human-readable name for priority level."""
    return priority.name.title()


def is_high_priority(priority: ChangePriority) -> bool:
    """Check if priority is high or critical."""
    return priority.value >= ChangePriority.HIGH.value


def compare_priorities(priority1: ChangePriority, priority2: ChangePriority) -> int:
    """Compare two priorities. Returns -1, 0, or 1."""
    if priority1.value < priority2.value:
        return -1
    elif priority1.value > priority2.value:
        return 1
    else:
        return 0


def sort_changes_by_priority(changes: List[FieldChange], descending: bool = True) -> List[FieldChange]:
    """Sort changes by priority."""
    return sorted(changes, key=lambda c: c.priority.value, reverse=descending)


def filter_by_min_priority(changes: List[FieldChange], min_priority: ChangePriority) -> List[FieldChange]:
    """Filter changes by minimum priority."""
    return [change for change in changes if change.priority.value >= min_priority.value]