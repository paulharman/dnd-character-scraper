#!/usr/bin/env python3
"""
Character Change Detection Service

Refactored service using modular architecture with consolidated detectors,
priority analysis, and significance assessment.
"""

import logging
import fnmatch
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass

# Import from new modular structure
from .change_detection.models import (
    FieldChange, ChangeType, ChangePriority, ChangeCategory,
    CharacterSnapshot, CharacterChangeSet, DetectionContext, DetectionResult
)
from .change_detection.detectors import CompositeDetector, create_detector
from .change_detection.utils import (
    DataExtractor, ValueComparator, ChangeDeduplicator, ChangeGrouper,
    compare_data_structures, filter_changes_by_patterns, get_change_summary
)
from .change_analyzers.priority import PriorityAnalyzer, create_priority_analyzer
from .change_analyzers.significance import SignificanceAnalyzer, SignificanceLevel, create_significance_analyzer

logger = logging.getLogger(__name__)


@dataclass
class ChangeDetectionConfig:
    """Configuration for change detection service."""
    excluded_fields: Set[str]
    high_priority_fields: Set[str]
    medium_priority_fields: Set[str]
    numeric_fields: Set[str]
    enable_priority_analysis: bool = True
    enable_significance_analysis: bool = True
    min_significance_level: SignificanceLevel = SignificanceLevel.MINOR
    detection_timeout: float = 30.0  # seconds


class ChangeDetectionService:
    """
    Main change detection service using modular architecture.
    
    This is the refactored version that consolidates the original 1673-line
    monolithic service into a focused coordinator using specialized modules.
    """
    
    def __init__(self, config: ChangeDetectionConfig = None):
        self.config = config or self._create_default_config()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize core components
        self.composite_detector = self._create_composite_detector()
        self.priority_analyzer = self._create_priority_analyzer()
        self.significance_analyzer = self._create_significance_analyzer()
        
        # Initialize utilities
        self.data_extractor = DataExtractor()
        self.value_comparator = ValueComparator()
        self.change_deduplicator = ChangeDeduplicator()
        self.change_grouper = ChangeGrouper()
        
        self.logger.info("Change detection service initialized with modular architecture")
    
    def detect_changes(self, old_snapshot: CharacterSnapshot, new_snapshot: CharacterSnapshot) -> CharacterChangeSet:
        """
        Detect changes between two character snapshots.
        
        This is the main entry point that coordinates all detection modules.
        """
        if old_snapshot.character_id != new_snapshot.character_id:
            raise ValueError("Cannot compare snapshots of different characters")
        
        self.logger.info(f"Detecting changes for character {old_snapshot.character_id} "
                        f"(v{old_snapshot.version} → v{new_snapshot.version})")
        
        # Create detection context
        context = self._create_detection_context(old_snapshot, new_snapshot)
        
        # Perform change detection
        changes = self._perform_detection(old_snapshot.character_data, new_snapshot.character_data, context)
        
        # Apply priority analysis if enabled
        if self.config.enable_priority_analysis:
            changes = self._apply_priority_analysis(changes, context)
        
        # Apply significance analysis if enabled
        if self.config.enable_significance_analysis:
            changes = self._apply_significance_analysis(changes, context)
        
        # Deduplicate and group changes
        changes = self._post_process_changes(changes)
        
        # Create change set
        change_set = self._create_change_set(old_snapshot, new_snapshot, changes)
        
        # Log debug info about pre-filtering count
        self.logger.debug(f"Change detection found {len(changes)} changes before external filtering")
        
        return change_set
    
    def detect_changes_legacy(self, old_snapshot: Any, new_snapshot: Any) -> CharacterChangeSet:
        """
        Legacy method for backward compatibility with old snapshot format.
        
        This method adapts the old format to the new modular structure.
        """
        # Convert legacy snapshots to new format
        old_char_snapshot = self._convert_legacy_snapshot(old_snapshot)
        new_char_snapshot = self._convert_legacy_snapshot(new_snapshot)
        
        return self.detect_changes(old_char_snapshot, new_char_snapshot)
    
    def get_supported_categories(self) -> List[ChangeCategory]:
        """Get all supported change categories."""
        return list(ChangeCategory)
    
    def configure_detection(self, config: Dict[str, Any]) -> None:
        """Configure detection settings."""
        if 'excluded_fields' in config:
            self.config.excluded_fields.update(config['excluded_fields'])
        
        if 'high_priority_fields' in config:
            self.config.high_priority_fields.update(config['high_priority_fields'])
        
        if 'enable_priority_analysis' in config:
            self.config.enable_priority_analysis = config['enable_priority_analysis']
        
        if 'enable_significance_analysis' in config:
            self.config.enable_significance_analysis = config['enable_significance_analysis']
        
        if 'min_significance_level' in config:
            self.config.min_significance_level = SignificanceLevel(config['min_significance_level'])
        
        self.logger.info("Detection configuration updated")
    
    def _create_default_config(self) -> ChangeDetectionConfig:
        """Create default configuration."""
        return ChangeDetectionConfig(
            excluded_fields={
                'updated_at', 'created_at', 'date_modified', 'timestamp',
                'last_modified', 'last_accessed', 'version',
                'character_info.avatarUrl', 'character_info.avatar_url',
                'meta.*', 'debug.*', 'generated_timestamp',
                'containers', 'containers.*',
                'inventory*', 'inventory_items*', 'encumbrance', 'encumbrance.*',
                'actions*', 
                # More specific spell exclusions - exclude metadata but allow spell content changes
                'spells.*.source_id', 'spells.*.sourceId', 'spells.*.source_page_number', 
                'spells.*.sourcePageNumber', 'spells.*.definition_key', 'spells.*.definitionKey',
                'spells.*.level_required', 'spells.*.levelRequired', 'spells.*.level_scales', 
                'spells.*.levelScales', 'spells.*.creature_rules', 'spells.*.creatureRules',
                'spells.*.display_order', 'spells.*.displayOrder', 'spells.*.hide_in_builder', 
                'spells.*.hideInBuilder', 'spells.*.hide_in_sheet', 'spells.*.hideInSheet',
                'spells.*.casting_time', 'spells.*.activationTime', 'spells.*.activation.activationTime',
                'spells.*.metadata.*', 'spells.*.last_updated',
                '*.level_required', '*.levelRequired', '*.level_scales', '*.levelScales',
                '*.creature_rules', '*.creatureRules', '*.display_order', '*.displayOrder',
                '*.hide_in_builder', '*.hideInBuilder', '*.hide_in_sheet', '*.hideInSheet',
                '*.source_id', '*.sourceId', '*.source_page_number', '*.sourcePageNumber',
                '*.definition_key', '*.definitionKey',
                # Additional commonly changing metadata fields
                'scraper_version', 'api_version', 'character_url',
                '*.casting_time', '*.activationTime', '*.activation.activationTime',
                '*.metadata.*', 'metadata.*', '*.last_updated'
            },
            high_priority_fields={
                'character_info.level', 'character_info.experience_points', 'combat.hit_points.current',
                'combat.hit_points.maximum', 'combat.armor_class.total',
                'character_info.classes.*', 'spellcasting.spell_slots.*', 'equipment.*', 'features.*'
            },
            medium_priority_fields={
                'ability_scores.*', 'proficiencies.*', 'skills.*',
                'saving_throws.*', 'equipment.*'
            },
            numeric_fields={
                'character_info.level', 'character_info.experience_points', 'combat.hit_points.*',
                'combat.armor_class.*', 'abilities.ability_scores.*', 'spellcasting.spell_slots.*', 'equipment.currency.*'
            }
        )
    
    def _create_composite_detector(self) -> CompositeDetector:
        """Create composite detector with all specialized detectors."""
        detector_config = {
            'character_info': create_detector('basic_info'),
            'abilities': create_detector('ability_scores'),
            'skills': create_detector('skills'),
            'spells': create_detector('spells'),
            'equipment': create_detector('equipment'),
            'features': create_detector('features')
        }
        
        return CompositeDetector(detector_config)
    
    def _create_priority_analyzer(self) -> PriorityAnalyzer:
        """Create priority analyzer with configuration."""
        priority_config = {
            'field_importance': self._get_field_importance_mapping(),
            'context_multipliers': self._get_context_multipliers()
        }
        
        return create_priority_analyzer(priority_config)
    
    def _create_significance_analyzer(self) -> SignificanceAnalyzer:
        """Create significance analyzer with configuration."""
        significance_config = {
            'min_significance_level': self.config.min_significance_level
        }
        
        return create_significance_analyzer(significance_config)
    
    def _create_detection_context(self, old_snapshot: CharacterSnapshot, new_snapshot: CharacterSnapshot) -> Dict[str, Any]:
        """Create detection context from snapshots."""
        # Extract character name safely
        character_name = self._extract_character_name(new_snapshot.character_data)
        
        # Determine rule version
        rule_version = self._determine_rule_version(new_snapshot.character_data)
        
        # Create detection context
        context = {
            'character_id': new_snapshot.character_id,
            'character_name': character_name,
            'rule_version': rule_version,
            'from_version': old_snapshot.version,
            'to_version': new_snapshot.version,
            'timestamp': new_snapshot.timestamp,
            'excluded_fields': self.config.excluded_fields,
            'high_priority_fields': self.config.high_priority_fields,
            'medium_priority_fields': self.config.medium_priority_fields,
            'numeric_fields': self.config.numeric_fields
        }
        
        return context
    
    def _perform_detection(self, old_data: Dict[str, Any], new_data: Dict[str, Any], context: Dict[str, Any]) -> List[FieldChange]:
        """Perform the actual change detection."""
        try:
            # Use composite detector for comprehensive detection
            changes = self.composite_detector.detect_changes(old_data, new_data, context)
            
            self.logger.debug(f"Composite detector found {len(changes)} changes")
            
            # Debug: Log all detected changes before exclusion
            if changes:
                self.logger.debug(f"Changes detected by composite detector:")
                for change in changes:
                    self.logger.debug(f"  - {change.field_path}: {change.old_value} → {change.new_value}")
            
            # If composite detector found no changes, use fallback detection as a backup
            # This handles cases where the composite detector doesn't recognize the data structure
            if not changes:
                self.logger.debug("No changes found by composite detector, trying fallback detection")
                fallback_changes = self._fallback_detection(old_data, new_data, context)
                if fallback_changes:
                    self.logger.debug(f"Fallback detection found {len(fallback_changes)} changes")
                    return fallback_changes
            
            # Apply field exclusion filters to composite detector results
            excluded_patterns = list(context.get('excluded_fields', set()))
            if excluded_patterns:
                unfiltered_count = len(changes)
                excluded_changes = []
                filtered_changes = []
                
                for change in changes:
                    excluded = False
                    for pattern in excluded_patterns:
                        if fnmatch.fnmatch(change.field_path, pattern):
                            excluded_changes.append(change)
                            excluded = True
                            break
                    if not excluded:
                        filtered_changes.append(change)
                
                changes = filtered_changes
                self.logger.debug(f"Field exclusion: {unfiltered_count} → {len(changes)} changes")
                
                # Debug: Log what fields were excluded
                if excluded_changes:
                    self.logger.debug(f"Excluded {len(excluded_changes)} changes:")
                    for change in excluded_changes:
                        self.logger.debug(f"  - {change.field_path}: {change.old_value} → {change.new_value}")
            
            return changes
            
        except Exception as e:
            self.logger.error(f"Error in change detection: {e}", exc_info=True)
            
            # Fallback to basic comparison
            self.logger.warning("Falling back to basic field comparison due to error")
            return self._fallback_detection(old_data, new_data, context)
    
    def _fallback_detection(self, old_data: Dict[str, Any], new_data: Dict[str, Any], context: Dict[str, Any]) -> List[FieldChange]:
        """Fallback detection using basic field comparison."""
        try:
            # Get excluded patterns
            excluded_patterns = list(context.get('excluded_fields', set()))
            
            # Perform basic comparison
            changes = compare_data_structures(old_data, new_data)
            
            self.logger.debug(f"Fallback detection found {len(changes)} changes before exclusion")
            
            # Debug: Log all changes before exclusion
            if changes:
                self.logger.debug(f"Changes detected by fallback detection:")
                for change in changes:
                    self.logger.debug(f"  - {change.field_path}: {change.old_value} → {change.new_value}")
            
            # Filter out excluded fields
            changes = filter_changes_by_patterns(changes, exclude_patterns=excluded_patterns)
            
            self.logger.debug(f"Fallback detection: {len(changes)} changes after exclusion")
            
            return changes
            
        except Exception as e:
            self.logger.error(f"Error in fallback detection: {e}", exc_info=True)
            return []
    
    def _apply_priority_analysis(self, changes: List[FieldChange], context: Dict[str, Any]) -> List[FieldChange]:
        """Apply priority analysis to changes."""
        try:
            return self.priority_analyzer.analyze_batch_priority(changes, context)
        except Exception as e:
            self.logger.error(f"Error in priority analysis: {e}", exc_info=True)
            return changes
    
    def _apply_significance_analysis(self, changes: List[FieldChange], context: Dict[str, Any]) -> List[FieldChange]:
        """Apply significance analysis to changes."""
        try:
            # Filter changes by significance level
            significant_changes = self.significance_analyzer.filter_significant_changes(
                changes, self.config.min_significance_level, context
            )
            
            self.logger.debug(f"Filtered {len(changes)} → {len(significant_changes)} significant changes")
            
            return significant_changes
            
        except Exception as e:
            self.logger.error(f"Error in significance analysis: {e}", exc_info=True)
            return changes
    
    def _post_process_changes(self, changes: List[FieldChange]) -> List[FieldChange]:
        """Post-process changes with deduplication and grouping."""
        try:
            # Deduplicate changes
            deduplicated = self.change_deduplicator.deduplicate_changes(changes)
            
            # Merge consecutive changes
            merged = self.change_deduplicator.merge_consecutive_changes(deduplicated)
            
            self.logger.debug(f"Post-processing: {len(changes)} → {len(merged)} changes")
            
            return merged
            
        except Exception as e:
            self.logger.error(f"Error in post-processing: {e}", exc_info=True)
            return changes
    
    def _create_change_set(self, old_snapshot: CharacterSnapshot, new_snapshot: CharacterSnapshot, 
                          changes: List[FieldChange]) -> CharacterChangeSet:
        """Create a CharacterChangeSet from detected changes."""
        character_name = self._extract_character_name(new_snapshot.character_data)
        
        # Generate summary
        summary = self._generate_change_summary(changes)
        
        return CharacterChangeSet(
            character_id=old_snapshot.character_id,
            character_name=character_name,
            from_version=old_snapshot.version,
            to_version=new_snapshot.version,
            timestamp=new_snapshot.timestamp,
            changes=changes,
            summary=summary
        )
    
    def _extract_character_name(self, character_data: Any) -> str:
        """Extract character name from character data."""
        try:
            # Try character_info field (v6.0.0 format)
            if isinstance(character_data, dict) and 'character_info' in character_data:
                character_info = character_data['character_info']
                if isinstance(character_info, dict):
                    return character_info.get('name', 'Unknown')
            
            # Try direct name field
            elif isinstance(character_data, dict) and 'name' in character_data:
                return character_data['name']
            
            return 'Unknown'
            
        except Exception as e:
            self.logger.warning(f"Error extracting character name: {e}")
            return 'Unknown'
    
    def _determine_rule_version(self, character_data: Any) -> str:
        """Determine rule version from character data."""
        try:
            # Try to extract rule version from character data
            if isinstance(character_data, dict):
                if 'rule_version' in character_data:
                    return character_data['rule_version']
                elif 'character_info' in character_data:
                    character_info = character_data['character_info']
                    if isinstance(character_info, dict) and 'rule_version' in character_info:
                        return character_info['rule_version']
            
            # Default to 2014 rules
            return "2014"
            
        except Exception as e:
            self.logger.warning(f"Error determining rule version: {e}")
            return "2014"
    
    def _generate_change_summary(self, changes: List[FieldChange]) -> str:
        """Generate a summary of changes."""
        if not changes:
            return "No changes detected"
        
        try:
            # Get change summary statistics
            summary_stats = get_change_summary(changes)
            
            # Generate human-readable summary
            total = summary_stats['total_changes']
            significant = summary_stats['significant_changes']
            
            if total == 1:
                return f"1 change detected"
            else:
                base_summary = f"{total} changes detected"
                if significant < total:
                    base_summary += f" ({significant} significant)"
                return base_summary
                
        except Exception as e:
            self.logger.warning(f"Error generating change summary: {e}")
            return f"{len(changes)} changes detected"
    
    def _get_field_importance_mapping(self) -> Dict[str, float]:
        """Get field importance mapping for priority analysis."""
        return {
            'character_info.level': 1.0,
            'combat.hit_points': 0.9,
            'character_info.name': 0.8,
            'character_info.classes': 0.8,
            'character_info.species': 0.8,
            'combat.armor_class': 0.7,
            'abilities': 0.7,
            'spells': 0.7,
            'features': 0.7,
            'skills': 0.6,
            'equipment': 0.5,
            'metadata': 0.2
        }
    
    def _get_context_multipliers(self) -> Dict[str, float]:
        """Get context multipliers for priority analysis."""
        return {
            'combat_active': 1.5,
            'level_up': 2.0,
            'new_character': 0.8,
            'bulk_update': 0.7,
            'automated_update': 0.6
        }
    
    def filter_changes_by_groups(
        self,
        changes: List[FieldChange],
        include_groups: Optional[Set[str]] = None,
        exclude_groups: Optional[Set[str]] = None,
        group_definitions: Optional[Dict[str, List[str]]] = None
    ) -> List[FieldChange]:
        """
        Filter changes based on data group membership.
        
        Args:
            changes: List of changes to filter
            include_groups: Groups to include (None = include all)
            exclude_groups: Groups to exclude
            group_definitions: Mapping of group names to field patterns
            
        Returns:
            Filtered list of changes
        """
        if not group_definitions:
            group_definitions = self._get_default_group_definitions()
        
        filtered_changes = []
        
        for change in changes:
            field_path = change.field_path
            
            # Check if field belongs to any excluded groups
            if exclude_groups:
                excluded = False
                for group_name in exclude_groups:
                    if group_name in group_definitions:
                        patterns = group_definitions[group_name]
                        if any(self._fnmatch_pattern(field_path, pattern) for pattern in patterns):
                            excluded = True
                            break
                if excluded:
                    continue
            
            # Check if field belongs to any included groups (if specified)
            if include_groups:
                included = False
                for group_name in include_groups:
                    if group_name in group_definitions:
                        patterns = group_definitions[group_name]
                        if any(self._fnmatch_pattern(field_path, pattern) for pattern in patterns):
                            included = True
                            break
                if not included:
                    continue
            
            filtered_changes.append(change)
        
        if len(changes) == len(filtered_changes):
            self.logger.info(f"All {len(changes)} changes passed filtering")
        else:
            self.logger.info(f"Filtered {len(changes)} changes to {len(filtered_changes)} changes")
            
        # Log filtering details
        if include_groups or exclude_groups:
            self.logger.info("Filtering settings:")
            if include_groups:
                self.logger.info(f"  Include groups: {sorted(include_groups)}")
            if exclude_groups:
                self.logger.info(f"  Exclude groups: {sorted(exclude_groups)}")
        else:
            self.logger.info("No filtering applied (debug preset = include all)")
        return filtered_changes
    
    def _fnmatch_pattern(self, field_path: str, pattern: str) -> bool:
        """Check if field path matches a pattern using fnmatch."""
        try:
            return fnmatch.fnmatch(field_path, pattern)
        except Exception as e:
            self.logger.warning(f"Error matching pattern '{pattern}' against '{field_path}': {e}")
            return False
    
    def _get_default_group_definitions(self) -> Dict[str, List[str]]:
        """Get default data group definitions."""
        return {
            'basic': [
                'character_info.name',
                'character_info.level',
                'character_info.experience_points',
                'character_info.classes.*',
                'features.*'
            ],
            'combat': [
                'combat.hit_points.*',
                'combat.armor_class.*',
                'combat.initiative.*',
                'combat.saving_throws.*'
            ],
            'abilities': [
                'abilities.ability_scores.*',
                'abilities.ability_modifiers.*'
            ],
            'spells': [
                'spells.*',
                'spellcasting.spell_slots.*',
                'spellcasting.*'
            ],
            'inventory': [
                'inventory.*',
                'equipment.*',
                'currency.*'
            ],
            'skills': [
                'skills.*',
                'proficiencies.*',
                'feats.*'
            ],
            'appearance': [
                'appearance.*',
                'character_info.avatar*',
                'decorations.*'
            ],
            'backstory': [
                'character_info.background.*',
                'backstory.*'
            ],
            'meta': [
                'meta.*',
                'processed_date',
                'scraper_version'
            ]
        }

    def _convert_legacy_snapshot(self, legacy_snapshot: Any) -> CharacterSnapshot:
        """Convert legacy snapshot format to new CharacterSnapshot."""
        # Handle different legacy formats
        if hasattr(legacy_snapshot, 'character_id'):
            # Already in new format
            return legacy_snapshot
        elif hasattr(legacy_snapshot, 'character_data'):
            # Legacy format with character_data
            return CharacterSnapshot(
                character_id=getattr(legacy_snapshot, 'character_id', 0),
                character_name=self._extract_character_name(legacy_snapshot.character_data),
                version=getattr(legacy_snapshot, 'version', 1),
                timestamp=getattr(legacy_snapshot, 'timestamp', datetime.now()),
                character_data=legacy_snapshot.character_data
            )
        else:
            # Assume it's raw character data
            return CharacterSnapshot(
                character_id=0,
                character_name=self._extract_character_name(legacy_snapshot),
                version=1,
                timestamp=datetime.now(),
                character_data=legacy_snapshot
            )


# Factory function for creating the service
def create_change_detection_service(config: ChangeDetectionConfig = None) -> ChangeDetectionService:
    """Create a change detection service with configuration."""
    return ChangeDetectionService(config)


# Utility functions for backward compatibility
def detect_changes(old_snapshot: Any, new_snapshot: Any) -> CharacterChangeSet:
    """
    Utility function for backward compatibility.
    
    Creates a service instance and detects changes.
    """
    service = create_change_detection_service()
    return service.detect_changes_legacy(old_snapshot, new_snapshot)


def create_field_change(field_path: str, old_value: Any, new_value: Any, 
                       change_type: ChangeType = None, priority: ChangePriority = None) -> FieldChange:
    """
    Utility function for creating FieldChange objects.
    
    Provides backward compatibility for legacy code.
    """
    from .change_detection.utils import create_change_from_comparison
    
    return create_change_from_comparison(field_path, old_value, new_value)


# Legacy classes for backward compatibility
class CharacterDiff:
    """Legacy class for backward compatibility."""
    
    def __init__(self, old_snapshot: Any, new_snapshot: Any, changes: Any):
        self.old_snapshot = old_snapshot
        self.new_snapshot = new_snapshot
        self.changes = changes