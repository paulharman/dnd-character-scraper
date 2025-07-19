"""
Significance Analysis for Change Detection

Provides significance assessment for character changes to determine
what changes are worth reporting to users.
"""

import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass
import math

from ..change_detection.models import FieldChange, ChangeType, ChangePriority, ChangeCategory

logger = logging.getLogger(__name__)


class SignificanceLevel(Enum):
    """Levels of significance for changes."""
    TRIVIAL = 0      # Not worth reporting
    MINOR = 1        # Minor changes
    MODERATE = 2     # Moderate changes
    MAJOR = 3        # Major changes
    CRITICAL = 4     # Critical changes


@dataclass
class SignificanceThreshold:
    """Threshold configuration for significance assessment."""
    category: ChangeCategory
    change_type: ChangeType
    min_priority: ChangePriority
    min_magnitude: float
    significance_level: SignificanceLevel


class SignificanceAnalyzer:
    """Analyzes the significance of character changes."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load significance thresholds
        self.thresholds = self._load_significance_thresholds()
        
        # Load field significance weights
        self.field_weights = self._load_field_weights()
        
        # Load context modifiers
        self.context_modifiers = self._load_context_modifiers()
    
    def analyze_significance(self, change: FieldChange, context: Dict[str, Any] = None) -> SignificanceLevel:
        """Analyze the significance of a single change."""
        context = context or {}
        
        # Get base significance from priority
        base_significance = self._priority_to_significance(change.priority)
        
        # Apply field-specific analysis
        field_significance = self._analyze_field_significance(change)
        
        # Apply magnitude analysis
        magnitude_significance = self._analyze_magnitude_significance(change)
        
        # Apply context modifiers
        context_significance = self._apply_context_modifiers(base_significance, context)
        
        # Combine significance levels
        final_significance = self._combine_significance_levels([
            base_significance,
            field_significance,
            magnitude_significance,
            context_significance
        ])
        
        self.logger.debug(f"Significance analysis for {change.field_path}: {final_significance}")
        
        return final_significance
    
    def analyze_batch_significance(self, changes: List[FieldChange], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze significance for a batch of changes."""
        context = context or {}
        
        if not changes:
            return {
                'overall_significance': SignificanceLevel.TRIVIAL,
                'significant_changes': [],
                'change_significance': {},
                'summary': {
                    'total_changes': 0,
                    'significant_count': 0,
                    'by_level': {}
                }
            }
        
        # Analyze individual changes
        change_significance = {}
        significant_changes = []
        
        for change in changes:
            significance = self.analyze_significance(change, context)
            change_significance[change.field_path] = significance
            
            if significance.value >= SignificanceLevel.MINOR.value:
                significant_changes.append(change)
        
        # Determine overall significance
        overall_significance = self._determine_overall_significance(changes, change_significance, context)
        
        # Generate summary
        summary = self._generate_significance_summary(changes, change_significance)
        
        return {
            'overall_significance': overall_significance,
            'significant_changes': significant_changes,
            'change_significance': change_significance,
            'summary': summary
        }
    
    def filter_significant_changes(self, changes: List[FieldChange], 
                                 min_significance: SignificanceLevel = SignificanceLevel.MINOR,
                                 context: Dict[str, Any] = None) -> List[FieldChange]:
        """Filter changes to only include significant ones."""
        context = context or {}
        significant_changes = []
        
        for change in changes:
            significance = self.analyze_significance(change, context)
            if significance.value >= min_significance.value:
                significant_changes.append(change)
        
        return significant_changes
    
    def rank_changes_by_significance(self, changes: List[FieldChange], 
                                   context: Dict[str, Any] = None) -> List[Tuple[FieldChange, SignificanceLevel]]:
        """Rank changes by their significance level."""
        context = context or {}
        ranked_changes = []
        
        for change in changes:
            significance = self.analyze_significance(change, context)
            ranked_changes.append((change, significance))
        
        # Sort by significance level (descending)
        ranked_changes.sort(key=lambda x: x[1].value, reverse=True)
        
        return ranked_changes
    
    def _load_significance_thresholds(self) -> List[SignificanceThreshold]:
        """Load significance thresholds configuration."""
        thresholds = []
        
        # Critical significance thresholds
        thresholds.extend([
            SignificanceThreshold(
                category=ChangeCategory.BASIC_INFO,
                change_type=ChangeType.MODIFIED,
                min_priority=ChangePriority.CRITICAL,
                min_magnitude=0.0,
                significance_level=SignificanceLevel.CRITICAL
            ),
            SignificanceThreshold(
                category=ChangeCategory.PROGRESSION,
                change_type=ChangeType.INCREMENTED,
                min_priority=ChangePriority.CRITICAL,
                min_magnitude=0.0,
                significance_level=SignificanceLevel.CRITICAL
            )
        ])
        
        # Major significance thresholds
        thresholds.extend([
            SignificanceThreshold(
                category=ChangeCategory.ABILITIES,
                change_type=ChangeType.INCREMENTED,
                min_priority=ChangePriority.HIGH,
                min_magnitude=2.0,
                significance_level=SignificanceLevel.MAJOR
            ),
            SignificanceThreshold(
                category=ChangeCategory.SPELLS,
                change_type=ChangeType.ADDED,
                min_priority=ChangePriority.HIGH,
                min_magnitude=0.0,
                significance_level=SignificanceLevel.MAJOR
            ),
            SignificanceThreshold(
                category=ChangeCategory.FEATURES,
                change_type=ChangeType.ADDED,
                min_priority=ChangePriority.HIGH,
                min_magnitude=0.0,
                significance_level=SignificanceLevel.MAJOR
            )
        ])
        
        # Moderate significance thresholds
        thresholds.extend([
            SignificanceThreshold(
                category=ChangeCategory.SKILLS,
                change_type=ChangeType.MODIFIED,
                min_priority=ChangePriority.MEDIUM,
                min_magnitude=1.0,
                significance_level=SignificanceLevel.MODERATE
            ),
            SignificanceThreshold(
                category=ChangeCategory.EQUIPMENT,
                change_type=ChangeType.ADDED,
                min_priority=ChangePriority.MEDIUM,
                min_magnitude=0.0,
                significance_level=SignificanceLevel.MODERATE
            ),
            SignificanceThreshold(
                category=ChangeCategory.COMBAT,
                change_type=ChangeType.MODIFIED,
                min_priority=ChangePriority.MEDIUM,
                min_magnitude=1.0,
                significance_level=SignificanceLevel.MODERATE
            )
        ])
        
        # Minor significance thresholds
        thresholds.extend([
            SignificanceThreshold(
                category=ChangeCategory.INVENTORY,
                change_type=ChangeType.INCREMENTED,
                min_priority=ChangePriority.LOW,
                min_magnitude=1.0,
                significance_level=SignificanceLevel.MINOR
            ),
            SignificanceThreshold(
                category=ChangeCategory.SOCIAL,
                change_type=ChangeType.MODIFIED,
                min_priority=ChangePriority.LOW,
                min_magnitude=0.0,
                significance_level=SignificanceLevel.MINOR
            )
        ])
        
        return thresholds
    
    def _load_field_weights(self) -> Dict[str, float]:
        """Load field-specific significance weights."""
        return {
            # Critical fields (high weight)
            'basic_info.level': 5.0,
            'basic_info.hit_points': 4.0,
            'basic_info.name': 3.5,
            'basic_info.class': 3.5,
            'basic_info.race': 3.5,
            
            # High importance fields
            'ability_scores.strength': 3.0,
            'ability_scores.dexterity': 3.0,
            'ability_scores.constitution': 3.0,
            'ability_scores.intelligence': 3.0,
            'ability_scores.wisdom': 3.0,
            'ability_scores.charisma': 3.0,
            'basic_info.armor_class': 3.0,
            'spells.known_spells': 2.8,
            'class_features': 2.8,
            'racial_traits': 2.8,
            'feats': 2.8,
            
            # Medium importance fields
            'skills': 2.0,
            'equipment': 1.8,
            'basic_info.background': 1.5,
            'basic_info.alignment': 1.2,
            'basic_info.experience_points': 1.5,
            'spells.spell_slots': 2.2,
            
            # Low importance fields
            'inventory': 1.0,
            'social': 0.8,
            'metadata': 0.3,
            'temporary': 0.2
        }
    
    def _load_context_modifiers(self) -> Dict[str, float]:
        """Load context-specific significance modifiers."""
        return {
            'combat_active': 1.5,
            'level_up_detected': 2.0,
            'new_character': 0.7,
            'bulk_update': 0.5,
            'automated_sync': 0.4,
            'user_initiated': 1.2,
            'session_active': 1.1,
            'first_time_user': 0.9
        }
    
    def _priority_to_significance(self, priority: ChangePriority) -> SignificanceLevel:
        """Convert priority to base significance level."""
        mapping = {
            ChangePriority.CRITICAL: SignificanceLevel.CRITICAL,
            ChangePriority.HIGH: SignificanceLevel.MAJOR,
            ChangePriority.MEDIUM: SignificanceLevel.MODERATE,
            ChangePriority.LOW: SignificanceLevel.MINOR
        }
        return mapping.get(priority, SignificanceLevel.MINOR)
    
    def _analyze_field_significance(self, change: FieldChange) -> SignificanceLevel:
        """Analyze significance based on field path."""
        # Get field weight
        field_weight = self._get_field_weight(change.field_path)
        
        # Check against thresholds
        for threshold in self.thresholds:
            if (change.category == threshold.category and
                change.change_type == threshold.change_type and
                change.priority.value >= threshold.min_priority.value):
                
                # Check magnitude if specified
                if threshold.min_magnitude > 0:
                    magnitude = self._get_change_magnitude(change)
                    if magnitude >= threshold.min_magnitude:
                        return threshold.significance_level
                else:
                    return threshold.significance_level
        
        # Use field weight to determine significance
        if field_weight >= 4.0:
            return SignificanceLevel.CRITICAL
        elif field_weight >= 3.0:
            return SignificanceLevel.MAJOR
        elif field_weight >= 2.0:
            return SignificanceLevel.MODERATE
        elif field_weight >= 1.0:
            return SignificanceLevel.MINOR
        else:
            return SignificanceLevel.TRIVIAL
    
    def _analyze_magnitude_significance(self, change: FieldChange) -> SignificanceLevel:
        """Analyze significance based on change magnitude."""
        magnitude = self._get_change_magnitude(change)
        
        if magnitude is None:
            return SignificanceLevel.MINOR
        
        # Scale magnitude by field importance
        field_weight = self._get_field_weight(change.field_path)
        weighted_magnitude = magnitude * field_weight
        
        # Determine significance based on weighted magnitude
        if weighted_magnitude >= 20:
            return SignificanceLevel.CRITICAL
        elif weighted_magnitude >= 10:
            return SignificanceLevel.MAJOR
        elif weighted_magnitude >= 5:
            return SignificanceLevel.MODERATE
        elif weighted_magnitude >= 1:
            return SignificanceLevel.MINOR
        else:
            return SignificanceLevel.TRIVIAL
    
    def _apply_context_modifiers(self, base_significance: SignificanceLevel, context: Dict[str, Any]) -> SignificanceLevel:
        """Apply context modifiers to significance."""
        modifier = 1.0
        
        for context_key, context_modifier in self.context_modifiers.items():
            if context.get(context_key, False):
                modifier *= context_modifier
        
        # Apply modifier to significance
        adjusted_value = base_significance.value * modifier
        
        # Map back to significance level
        if adjusted_value >= 4.0:
            return SignificanceLevel.CRITICAL
        elif adjusted_value >= 3.0:
            return SignificanceLevel.MAJOR
        elif adjusted_value >= 2.0:
            return SignificanceLevel.MODERATE
        elif adjusted_value >= 1.0:
            return SignificanceLevel.MINOR
        else:
            return SignificanceLevel.TRIVIAL
    
    def _combine_significance_levels(self, levels: List[SignificanceLevel]) -> SignificanceLevel:
        """Combine multiple significance levels."""
        if not levels:
            return SignificanceLevel.TRIVIAL
        
        # Use the highest significance level
        max_level = max(levels, key=lambda x: x.value)
        
        # But also consider the average to avoid outliers
        average_value = sum(level.value for level in levels) / len(levels)
        
        # If average is significantly lower than max, reduce the final level
        if max_level.value - average_value > 1.5:
            return SignificanceLevel(max(1, max_level.value - 1))
        
        return max_level
    
    def _determine_overall_significance(self, changes: List[FieldChange], 
                                      change_significance: Dict[str, SignificanceLevel],
                                      context: Dict[str, Any]) -> SignificanceLevel:
        """Determine overall significance of a batch of changes."""
        if not changes:
            return SignificanceLevel.TRIVIAL
        
        significance_values = list(change_significance.values())
        
        # Count changes by significance level
        significance_counts = {}
        for level in significance_values:
            significance_counts[level] = significance_counts.get(level, 0) + 1
        
        # Determine overall significance based on distribution
        total_changes = len(changes)
        
        # If any critical changes, overall is critical
        if significance_counts.get(SignificanceLevel.CRITICAL, 0) > 0:
            return SignificanceLevel.CRITICAL
        
        # If many major changes, overall is major
        major_count = significance_counts.get(SignificanceLevel.MAJOR, 0)
        if major_count > 0 and major_count >= total_changes * 0.2:
            return SignificanceLevel.MAJOR
        
        # If many moderate changes, overall is moderate
        moderate_count = significance_counts.get(SignificanceLevel.MODERATE, 0)
        if moderate_count > 0 and moderate_count >= total_changes * 0.3:
            return SignificanceLevel.MODERATE
        
        # If many minor changes, overall is minor
        minor_count = significance_counts.get(SignificanceLevel.MINOR, 0)
        if minor_count > 0 and minor_count >= total_changes * 0.4:
            return SignificanceLevel.MINOR
        
        # If few significant changes, overall is trivial
        significant_count = sum(significance_counts.get(level, 0) 
                              for level in [SignificanceLevel.MINOR, SignificanceLevel.MODERATE, 
                                          SignificanceLevel.MAJOR, SignificanceLevel.CRITICAL])
        
        if significant_count == 0:
            return SignificanceLevel.TRIVIAL
        elif significant_count < total_changes * 0.1:
            return SignificanceLevel.TRIVIAL
        else:
            return SignificanceLevel.MINOR
    
    def _generate_significance_summary(self, changes: List[FieldChange], 
                                     change_significance: Dict[str, SignificanceLevel]) -> Dict[str, Any]:
        """Generate summary of significance analysis."""
        total_changes = len(changes)
        
        # Count by significance level
        by_level = {}
        for level in SignificanceLevel:
            by_level[level.name] = sum(1 for sig in change_significance.values() if sig == level)
        
        # Count significant changes
        significant_count = sum(by_level[level.name] for level in SignificanceLevel 
                              if level.value >= SignificanceLevel.MINOR.value)
        
        # Calculate percentages
        percentages = {}
        for level_name, count in by_level.items():
            percentages[level_name] = (count / total_changes * 100) if total_changes > 0 else 0
        
        return {
            'total_changes': total_changes,
            'significant_count': significant_count,
            'significance_rate': (significant_count / total_changes * 100) if total_changes > 0 else 0,
            'by_level': by_level,
            'percentages': percentages
        }
    
    def _get_field_weight(self, field_path: str) -> float:
        """Get significance weight for a field path."""
        # Check exact matches first
        if field_path in self.field_weights:
            return self.field_weights[field_path]
        
        # Check pattern matches
        import fnmatch
        for pattern, weight in self.field_weights.items():
            if fnmatch.fnmatch(field_path, pattern):
                return weight
        
        # Check parent paths
        parts = field_path.split('.')
        for i in range(len(parts) - 1, 0, -1):
            parent_path = '.'.join(parts[:i])
            if parent_path in self.field_weights:
                return self.field_weights[parent_path] * 0.8  # Reduce weight for children
        
        return 1.0  # Default weight
    
    def _get_change_magnitude(self, change: FieldChange) -> Optional[float]:
        """Get magnitude of a change."""
        old_value = change.old_value
        new_value = change.new_value
        
        # Numeric values
        if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
            return abs(new_value - old_value)
        
        # String values (character length difference)
        if isinstance(old_value, str) and isinstance(new_value, str):
            return abs(len(new_value) - len(old_value))
        
        # Collection values (size difference)
        if isinstance(old_value, (list, dict)) and isinstance(new_value, (list, dict)):
            try:
                return abs(len(new_value) - len(old_value))
            except TypeError:
                return None
        
        # Boolean values
        if isinstance(old_value, bool) and isinstance(new_value, bool):
            return 1.0 if old_value != new_value else 0.0
        
        # None values
        if old_value is None or new_value is None:
            return 1.0
        
        # Default: changes have magnitude 1
        return 1.0


class SignificanceFilter:
    """Filter for changes based on significance levels."""
    
    def __init__(self, min_significance: SignificanceLevel = SignificanceLevel.MINOR):
        self.min_significance = min_significance
        self.analyzer = SignificanceAnalyzer()
    
    def filter_changes(self, changes: List[FieldChange], context: Dict[str, Any] = None) -> List[FieldChange]:
        """Filter changes based on significance threshold."""
        return self.analyzer.filter_significant_changes(changes, self.min_significance, context)
    
    def set_threshold(self, threshold: SignificanceLevel):
        """Set the significance threshold."""
        self.min_significance = threshold


class SignificanceReporter:
    """Reporter for generating significance reports."""
    
    def __init__(self, analyzer: SignificanceAnalyzer = None):
        self.analyzer = analyzer or SignificanceAnalyzer()
    
    def generate_report(self, changes: List[FieldChange], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a comprehensive significance report."""
        context = context or {}
        
        # Analyze significance
        analysis = self.analyzer.analyze_batch_significance(changes, context)
        
        # Rank changes
        ranked_changes = self.analyzer.rank_changes_by_significance(changes, context)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(analysis, ranked_changes, context)
        
        return {
            'analysis': analysis,
            'ranked_changes': [(change.field_path, significance.name) for change, significance in ranked_changes],
            'recommendations': recommendations,
            'context': context
        }
    
    def _generate_recommendations(self, analysis: Dict[str, Any], 
                                ranked_changes: List[Tuple[FieldChange, SignificanceLevel]],
                                context: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on significance analysis."""
        recommendations = []
        
        overall_significance = analysis['overall_significance']
        summary = analysis['summary']
        
        # Overall recommendations
        if overall_significance == SignificanceLevel.CRITICAL:
            recommendations.append("Immediate attention required - critical changes detected")
        elif overall_significance == SignificanceLevel.MAJOR:
            recommendations.append("High priority - major changes need review")
        elif overall_significance == SignificanceLevel.MODERATE:
            recommendations.append("Moderate priority - changes should be reviewed")
        elif overall_significance == SignificanceLevel.MINOR:
            recommendations.append("Low priority - minor changes for awareness")
        else:
            recommendations.append("No significant changes detected")
        
        # Specific recommendations
        if summary['by_level'].get('CRITICAL', 0) > 0:
            recommendations.append("Review critical changes immediately")
        
        if summary['by_level'].get('MAJOR', 0) > 3:
            recommendations.append("Multiple major changes detected - consider consolidating notifications")
        
        if summary['significance_rate'] > 80:
            recommendations.append("High rate of significant changes - may indicate bulk update")
        
        if context.get('session_active'):
            recommendations.append("Active session detected - provide real-time updates")
        
        return recommendations


# Factory functions
def create_significance_analyzer(config: Dict[str, Any] = None) -> SignificanceAnalyzer:
    """Create a significance analyzer with configuration."""
    return SignificanceAnalyzer(config)


def create_significance_filter(min_significance: SignificanceLevel = SignificanceLevel.MINOR) -> SignificanceFilter:
    """Create a significance filter with threshold."""
    return SignificanceFilter(min_significance)


def create_significance_reporter(analyzer: SignificanceAnalyzer = None) -> SignificanceReporter:
    """Create a significance reporter."""
    return SignificanceReporter(analyzer)


# Utility functions
def get_significance_level_name(level: SignificanceLevel) -> str:
    """Get human-readable name for significance level."""
    return level.name.title()


def is_significant(level: SignificanceLevel, threshold: SignificanceLevel = SignificanceLevel.MINOR) -> bool:
    """Check if significance level meets threshold."""
    return level.value >= threshold.value


def compare_significance(level1: SignificanceLevel, level2: SignificanceLevel) -> int:
    """Compare two significance levels. Returns -1, 0, or 1."""
    if level1.value < level2.value:
        return -1
    elif level1.value > level2.value:
        return 1
    else:
        return 0