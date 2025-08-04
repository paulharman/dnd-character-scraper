"""
Change Log Query Interface

Provides comprehensive querying, filtering, and analysis capabilities for change logs
with causation details, pagination, and maintenance functions.
"""

import logging
from typing import Dict, Any, List, Optional, Set, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from src.models.change_log import (
    ChangeLogEntry, ChangeLogConfig, ChangeLogMetadata, ChangeLogFile,
    ChangeCausation, ChangeAttribution
)
from src.services.change_log_service import ChangeLogService
from discord.services.change_detection.models import ChangeCategory, ChangePriority

logger = logging.getLogger(__name__)


class SortOrder(Enum):
    """Sort order for query results."""
    ASC = "asc"
    DESC = "desc"


class QueryOperator(Enum):
    """Query operators for filtering."""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IN = "in"
    NOT_IN = "not_in"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_EQUAL = "gte"
    LESS_EQUAL = "lte"


@dataclass
class QueryFilter:
    """Filter criteria for change log queries."""
    field: str
    operator: QueryOperator
    value: Any
    
    def matches(self, entry: ChangeLogEntry) -> bool:
        """Check if an entry matches this filter."""
        try:
            # Get field value from entry
            field_value = self._get_field_value(entry, self.field)
            
            if field_value is None:
                return self.operator == QueryOperator.NOT_EQUALS
            
            # Apply operator
            if self.operator == QueryOperator.EQUALS:
                return field_value == self.value
            elif self.operator == QueryOperator.NOT_EQUALS:
                return field_value != self.value
            elif self.operator == QueryOperator.CONTAINS:
                return str(self.value).lower() in str(field_value).lower()
            elif self.operator == QueryOperator.STARTS_WITH:
                return str(field_value).lower().startswith(str(self.value).lower())
            elif self.operator == QueryOperator.ENDS_WITH:
                return str(field_value).lower().endswith(str(self.value).lower())
            elif self.operator == QueryOperator.IN:
                return field_value in self.value
            elif self.operator == QueryOperator.NOT_IN:
                return field_value not in self.value
            elif self.operator == QueryOperator.GREATER_THAN:
                return field_value > self.value
            elif self.operator == QueryOperator.LESS_THAN:
                return field_value < self.value
            elif self.operator == QueryOperator.GREATER_EQUAL:
                return field_value >= self.value
            elif self.operator == QueryOperator.LESS_EQUAL:
                return field_value <= self.value
            
            return False
            
        except Exception as e:
            logger.warning(f"Error applying filter {self.field} {self.operator.value} {self.value}: {e}")
            return False
    
    def _get_field_value(self, entry: ChangeLogEntry, field_path: str) -> Any:
        """Get field value from entry using dot notation."""
        try:
            value = entry
            for part in field_path.split('.'):
                if hasattr(value, part):
                    value = getattr(value, part)
                elif isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            return value
        except Exception:
            return None


@dataclass
class QueryOptions:
    """Options for change log queries."""
    limit: Optional[int] = None
    offset: int = 0
    sort_by: str = "timestamp"
    sort_order: SortOrder = SortOrder.DESC
    include_causation: bool = True
    include_attribution: bool = True
    filters: List[QueryFilter] = field(default_factory=list)
    
    # Date range filtering
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Category and priority filtering
    categories: Optional[Set[ChangeCategory]] = None
    priorities: Optional[Set[ChangePriority]] = None
    change_types: Optional[Set[str]] = None
    
    # Causation filtering
    cause_types: Optional[Set[str]] = None
    cause_names: Optional[Set[str]] = None
    source_types: Optional[Set[str]] = None


@dataclass
class QueryResult:
    """Result of a change log query."""
    entries: List[ChangeLogEntry]
    total_count: int
    filtered_count: int
    has_more: bool
    query_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'entries': [entry.to_dict() for entry in self.entries],
            'total_count': self.total_count,
            'filtered_count': self.filtered_count,
            'has_more': self.has_more,
            'query_time_ms': self.query_time_ms
        }


@dataclass
class CausationReport:
    """Report of causation analysis for a character."""
    character_id: int
    character_name: str
    total_changes: int
    causation_breakdown: Dict[str, int]  # trigger type -> count
    attribution_breakdown: Dict[str, int]  # source type -> count
    top_causes: List[Tuple[str, str, int]]  # (cause_type, cause_name, count)
    cascade_analysis: Dict[str, List[str]]  # trigger -> affected fields
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'character_id': self.character_id,
            'character_name': self.character_name,
            'total_changes': self.total_changes,
            'causation_breakdown': self.causation_breakdown,
            'attribution_breakdown': self.attribution_breakdown,
            'top_causes': self.top_causes,
            'cascade_analysis': self.cascade_analysis,
            'generated_at': self.generated_at.isoformat()
        }


class ChangeLogQueryInterface:
    """
    Enhanced query interface for change logs with filtering, pagination,
    causation analysis, and maintenance functions.
    """
    
    def __init__(self, change_log_service: ChangeLogService):
        self.change_log_service = change_log_service
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def query_changes(self, character_id: int, options: QueryOptions) -> QueryResult:
        """
        Query changes with comprehensive filtering and pagination.
        
        Args:
            character_id: Character to query changes for
            options: Query options including filters, sorting, and pagination
            
        Returns:
            QueryResult with matching entries and metadata
        """
        start_time = datetime.now()
        
        try:
            # Get all entries for the character
            all_entries = await self.change_log_service.get_change_history(
                character_id, 
                include_causation=options.include_causation
            )
            
            total_count = len(all_entries)
            
            # Apply filters
            filtered_entries = self._apply_filters(all_entries, options)
            filtered_count = len(filtered_entries)
            
            # Apply sorting
            sorted_entries = self._apply_sorting(filtered_entries, options)
            
            # Apply pagination
            paginated_entries = self._apply_pagination(sorted_entries, options)
            
            # Remove causation/attribution if not requested
            if not options.include_causation:
                for entry in paginated_entries:
                    entry.causation = None
            
            if not options.include_attribution:
                for entry in paginated_entries:
                    entry.attribution = None
            
            # Calculate query time
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Determine if there are more results
            has_more = (options.offset + len(paginated_entries)) < filtered_count
            
            return QueryResult(
                entries=paginated_entries,
                total_count=total_count,
                filtered_count=filtered_count,
                has_more=has_more,
                query_time_ms=query_time
            )
            
        except Exception as e:
            self.logger.error(f"Error querying changes for character {character_id}: {e}", exc_info=True)
            return QueryResult(
                entries=[],
                total_count=0,
                filtered_count=0,
                has_more=False,
                query_time_ms=0.0
            )
    
    async def get_changes_by_cause(self, character_id: int, cause_type: str, 
                                 cause_name: str, limit: Optional[int] = None) -> List[ChangeLogEntry]:
        """
        Get all changes caused by a specific source with enhanced filtering.
        
        Args:
            character_id: Character to query
            cause_type: Type of cause (feat_selection, level_progression, etc.)
            cause_name: Specific name of the cause
            limit: Optional limit on results
            
        Returns:
            List of matching change log entries
        """
        try:
            options = QueryOptions(
                limit=limit,
                filters=[
                    QueryFilter("attribution.source", QueryOperator.EQUALS, cause_type),
                    QueryFilter("attribution.source_name", QueryOperator.EQUALS, cause_name)
                ]
            )
            
            result = await self.query_changes(character_id, options)
            return result.entries
            
        except Exception as e:
            self.logger.error(f"Error getting changes by cause for character {character_id}: {e}", exc_info=True)
            return []
    
    async def get_changes_by_date_range(self, character_id: int, start_date: datetime, 
                                      end_date: datetime, limit: Optional[int] = None) -> List[ChangeLogEntry]:
        """
        Get changes within a specific date range.
        
        Args:
            character_id: Character to query
            start_date: Start of date range
            end_date: End of date range
            limit: Optional limit on results
            
        Returns:
            List of matching change log entries
        """
        try:
            options = QueryOptions(
                limit=limit,
                start_date=start_date,
                end_date=end_date
            )
            
            result = await self.query_changes(character_id, options)
            return result.entries
            
        except Exception as e:
            self.logger.error(f"Error getting changes by date range for character {character_id}: {e}", exc_info=True)
            return []
    
    async def get_changes_by_type(self, character_id: int, change_types: List[str], 
                                limit: Optional[int] = None) -> List[ChangeLogEntry]:
        """
        Get changes by specific change types.
        
        Args:
            character_id: Character to query
            change_types: List of change types to filter by
            limit: Optional limit on results
            
        Returns:
            List of matching change log entries
        """
        try:
            options = QueryOptions(
                limit=limit,
                change_types=set(change_types)
            )
            
            result = await self.query_changes(character_id, options)
            return result.entries
            
        except Exception as e:
            self.logger.error(f"Error getting changes by type for character {character_id}: {e}", exc_info=True)
            return []
    
    async def search_changes(self, character_id: int, search_term: str, 
                           search_fields: Optional[List[str]] = None,
                           limit: Optional[int] = None) -> List[ChangeLogEntry]:
        """
        Search changes by text content in descriptions and other fields.
        
        Args:
            character_id: Character to query
            search_term: Text to search for
            search_fields: Fields to search in (default: description, detailed_description)
            limit: Optional limit on results
            
        Returns:
            List of matching change log entries
        """
        try:
            if search_fields is None:
                search_fields = ["description", "detailed_description", "field_path"]
            
            # Create filters for each search field
            filters = []
            for field in search_fields:
                filters.append(QueryFilter(field, QueryOperator.CONTAINS, search_term))
            
            # Get all entries and apply text search
            all_entries = await self.change_log_service.get_change_history(character_id)
            
            matching_entries = []
            for entry in all_entries:
                # Check if any filter matches (OR logic)
                if any(filter_obj.matches(entry) for filter_obj in filters):
                    matching_entries.append(entry)
            
            # Apply limit
            if limit:
                matching_entries = matching_entries[:limit]
            
            return matching_entries
            
        except Exception as e:
            self.logger.error(f"Error searching changes for character {character_id}: {e}", exc_info=True)
            return []
    
    async def generate_causation_report(self, character_id: int, 
                                      days_back: Optional[int] = None) -> CausationReport:
        """
        Generate a comprehensive causation analysis report.
        
        Args:
            character_id: Character to analyze
            days_back: Optional number of days to look back (default: all time)
            
        Returns:
            CausationReport with detailed analysis
        """
        try:
            # Get entries for analysis
            start_date = None
            if days_back:
                start_date = datetime.now() - timedelta(days=days_back)
            
            entries = await self.change_log_service.get_change_history(
                character_id, 
                since=start_date,
                include_causation=True
            )
            
            if not entries:
                return CausationReport(
                    character_id=character_id,
                    character_name="Unknown",
                    total_changes=0,
                    causation_breakdown={},
                    attribution_breakdown={},
                    top_causes=[],
                    cascade_analysis={}
                )
            
            character_name = entries[0].character_name
            total_changes = len(entries)
            
            # Analyze causation breakdown
            causation_breakdown = {}
            attribution_breakdown = {}
            cause_counts = {}  # (cause_type, cause_name) -> count
            cascade_analysis = {}  # trigger -> affected fields
            
            for entry in entries:
                # Causation analysis
                if entry.causation:
                    trigger = entry.causation.trigger
                    causation_breakdown[trigger] = causation_breakdown.get(trigger, 0) + 1
                    
                    # Track cascade effects
                    if trigger not in cascade_analysis:
                        cascade_analysis[trigger] = set()
                    cascade_analysis[trigger].add(entry.field_path)
                
                # Attribution analysis
                if entry.attribution:
                    source_type = entry.attribution.source_type
                    attribution_breakdown[source_type] = attribution_breakdown.get(source_type, 0) + 1
                    
                    # Track specific causes
                    cause_key = (entry.attribution.source, entry.attribution.source_name)
                    cause_counts[cause_key] = cause_counts.get(cause_key, 0) + 1
            
            # Convert cascade analysis sets to lists
            cascade_analysis = {k: list(v) for k, v in cascade_analysis.items()}
            
            # Get top causes
            top_causes = sorted(
                [(cause_type, cause_name, count) for (cause_type, cause_name), count in cause_counts.items()],
                key=lambda x: x[2],
                reverse=True
            )[:10]  # Top 10 causes
            
            return CausationReport(
                character_id=character_id,
                character_name=character_name,
                total_changes=total_changes,
                causation_breakdown=causation_breakdown,
                attribution_breakdown=attribution_breakdown,
                top_causes=top_causes,
                cascade_analysis=cascade_analysis
            )
            
        except Exception as e:
            self.logger.error(f"Error generating causation report for character {character_id}: {e}", exc_info=True)
            return CausationReport(
                character_id=character_id,
                character_name="Unknown",
                total_changes=0,
                causation_breakdown={},
                attribution_breakdown={},
                top_causes=[],
                cascade_analysis={}
            )
    
    async def get_related_changes(self, character_id: int, field_path: str, 
                                time_window_hours: int = 24) -> List[ChangeLogEntry]:
        """
        Get changes related to a specific field within a time window.
        
        Args:
            character_id: Character to query
            field_path: Field path to find related changes for
            time_window_hours: Time window to search within
            
        Returns:
            List of related change log entries
        """
        try:
            # Get all entries
            all_entries = await self.change_log_service.get_change_history(
                character_id, 
                include_causation=True
            )
            
            # Find the reference entry
            reference_entry = None
            for entry in all_entries:
                if entry.field_path == field_path:
                    reference_entry = entry
                    break
            
            if not reference_entry:
                return []
            
            # Define time window
            time_window = timedelta(hours=time_window_hours)
            start_time = reference_entry.timestamp - time_window
            end_time = reference_entry.timestamp + time_window
            
            # Find related entries
            related_entries = []
            for entry in all_entries:
                if (entry != reference_entry and 
                    start_time <= entry.timestamp <= end_time):
                    
                    # Check if entries are causally related
                    if self._are_entries_related(reference_entry, entry):
                        related_entries.append(entry)
            
            # Sort by timestamp
            related_entries.sort(key=lambda x: x.timestamp)
            
            return related_entries
            
        except Exception as e:
            self.logger.error(f"Error getting related changes for character {character_id}: {e}", exc_info=True)
            return []
    
    async def cleanup_logs_by_criteria(self, character_id: int, 
                                     cleanup_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean up logs based on specific criteria.
        
        Args:
            character_id: Character to clean up logs for
            cleanup_criteria: Criteria for cleanup (age, count, categories, etc.)
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            cleanup_results = {
                'character_id': character_id,
                'entries_before': 0,
                'entries_after': 0,
                'entries_removed': 0,
                'categories_cleaned': [],
                'cleanup_time': datetime.now().isoformat()
            }
            
            # Get current log file
            log_file_path = self.change_log_service._get_current_log_file_path(character_id)
            
            if not log_file_path.exists():
                return cleanup_results
            
            # Load log file
            log_file = await self.change_log_service._load_log_file(log_file_path)
            original_count = len(log_file.entries)
            cleanup_results['entries_before'] = original_count
            
            # Apply cleanup criteria
            filtered_entries = []
            
            for entry in log_file.entries:
                should_keep = True
                
                # Age-based cleanup
                if 'max_age_days' in cleanup_criteria:
                    max_age = timedelta(days=cleanup_criteria['max_age_days'])
                    if datetime.now() - entry.timestamp > max_age:
                        should_keep = False
                
                # Category-based cleanup
                if 'exclude_categories' in cleanup_criteria:
                    if entry.category.value in cleanup_criteria['exclude_categories']:
                        should_keep = False
                        if entry.category.value not in cleanup_results['categories_cleaned']:
                            cleanup_results['categories_cleaned'].append(entry.category.value)
                
                # Priority-based cleanup
                if 'min_priority' in cleanup_criteria:
                    min_priority = cleanup_criteria['min_priority']
                    if entry.priority.value < min_priority:
                        should_keep = False
                
                # Change type cleanup
                if 'exclude_change_types' in cleanup_criteria:
                    if entry.change_type in cleanup_criteria['exclude_change_types']:
                        should_keep = False
                
                if should_keep:
                    filtered_entries.append(entry)
            
            # Update log file
            log_file.entries = filtered_entries
            log_file.metadata.total_entries = len(filtered_entries)
            
            # Recalculate category counts
            log_file.metadata.change_categories = {}
            for entry in filtered_entries:
                category_key = entry.category.value
                log_file.metadata.change_categories[category_key] = \
                    log_file.metadata.change_categories.get(category_key, 0) + 1
            
            # Save updated log file
            await self.change_log_service._save_log_file(log_file_path, log_file)
            
            cleanup_results['entries_after'] = len(filtered_entries)
            cleanup_results['entries_removed'] = original_count - len(filtered_entries)
            
            self.logger.info(f"Cleaned up {cleanup_results['entries_removed']} entries for character {character_id}")
            
            return cleanup_results
            
        except Exception as e:
            self.logger.error(f"Error cleaning up logs for character {character_id}: {e}", exc_info=True)
            return {'error': str(e)}
    
    async def get_log_maintenance_info(self, character_id: int) -> Dict[str, Any]:
        """
        Get maintenance information for character logs.
        
        Args:
            character_id: Character to get maintenance info for
            
        Returns:
            Dictionary with maintenance information
        """
        try:
            # Get log statistics
            stats = await self.change_log_service.get_log_statistics(character_id)
            
            # Add maintenance recommendations
            maintenance_info = stats.copy()
            maintenance_info['recommendations'] = []
            
            # Check file size
            if stats.get('total_size_mb', 0) > 50:
                maintenance_info['recommendations'].append({
                    'type': 'file_size',
                    'message': 'Log files are large, consider cleanup or archiving',
                    'severity': 'warning'
                })
            
            # Check entry count
            if stats.get('total_entries', 0) > 10000:
                maintenance_info['recommendations'].append({
                    'type': 'entry_count',
                    'message': 'High number of entries, consider cleanup',
                    'severity': 'info'
                })
            
            # Check age of oldest entry
            if stats.get('oldest_entry'):
                oldest_date = datetime.fromisoformat(stats['oldest_entry'])
                age_days = (datetime.now() - oldest_date).days
                
                if age_days > 365:
                    maintenance_info['recommendations'].append({
                        'type': 'old_entries',
                        'message': f'Entries older than {age_days} days found, consider archiving',
                        'severity': 'info'
                    })
            
            return maintenance_info
            
        except Exception as e:
            self.logger.error(f"Error getting maintenance info for character {character_id}: {e}", exc_info=True)
            return {'error': str(e)}
    
    def _apply_filters(self, entries: List[ChangeLogEntry], options: QueryOptions) -> List[ChangeLogEntry]:
        """Apply filters to entries."""
        filtered_entries = entries
        
        # Date range filtering
        if options.start_date:
            filtered_entries = [e for e in filtered_entries if e.timestamp >= options.start_date]
        
        if options.end_date:
            filtered_entries = [e for e in filtered_entries if e.timestamp <= options.end_date]
        
        # Category filtering
        if options.categories:
            filtered_entries = [e for e in filtered_entries if e.category in options.categories]
        
        # Priority filtering
        if options.priorities:
            filtered_entries = [e for e in filtered_entries if e.priority in options.priorities]
        
        # Change type filtering
        if options.change_types:
            filtered_entries = [e for e in filtered_entries if e.change_type in options.change_types]
        
        # Causation filtering
        if options.cause_types:
            filtered_entries = [e for e in filtered_entries 
                              if e.causation and e.causation.trigger in options.cause_types]
        
        if options.cause_names:
            filtered_entries = [e for e in filtered_entries 
                              if e.attribution and e.attribution.source_name in options.cause_names]
        
        if options.source_types:
            filtered_entries = [e for e in filtered_entries 
                              if e.attribution and e.attribution.source_type in options.source_types]
        
        # Custom filters
        for filter_obj in options.filters:
            filtered_entries = [e for e in filtered_entries if filter_obj.matches(e)]
        
        return filtered_entries
    
    def _apply_sorting(self, entries: List[ChangeLogEntry], options: QueryOptions) -> List[ChangeLogEntry]:
        """Apply sorting to entries."""
        try:
            reverse = options.sort_order == SortOrder.DESC
            
            if options.sort_by == "timestamp":
                return sorted(entries, key=lambda x: x.timestamp, reverse=reverse)
            elif options.sort_by == "priority":
                return sorted(entries, key=lambda x: x.priority.value, reverse=reverse)
            elif options.sort_by == "category":
                return sorted(entries, key=lambda x: x.category.value, reverse=reverse)
            elif options.sort_by == "change_type":
                return sorted(entries, key=lambda x: x.change_type, reverse=reverse)
            elif options.sort_by == "field_path":
                return sorted(entries, key=lambda x: x.field_path, reverse=reverse)
            else:
                # Default to timestamp
                return sorted(entries, key=lambda x: x.timestamp, reverse=reverse)
                
        except Exception as e:
            self.logger.warning(f"Error sorting entries: {e}")
            return entries
    
    def _apply_pagination(self, entries: List[ChangeLogEntry], options: QueryOptions) -> List[ChangeLogEntry]:
        """Apply pagination to entries."""
        start_idx = options.offset
        end_idx = start_idx + options.limit if options.limit else len(entries)
        
        return entries[start_idx:end_idx]
    
    def _are_entries_related(self, entry1: ChangeLogEntry, entry2: ChangeLogEntry) -> bool:
        """Check if two entries are causally related."""
        # Check if they share the same causation trigger
        if (entry1.causation and entry2.causation and 
            entry1.causation.trigger == entry2.causation.trigger):
            return True
        
        # Check if one entry's field is in the other's related changes
        if entry1.causation and entry1.field_path in entry1.causation.related_changes:
            if entry2.field_path in entry1.causation.related_changes:
                return True
        
        if entry2.causation and entry2.field_path in entry2.causation.related_changes:
            if entry1.field_path in entry2.causation.related_changes:
                return True
        
        # Check if they have the same attribution source
        if (entry1.attribution and entry2.attribution and 
            entry1.attribution.source == entry2.attribution.source and
            entry1.attribution.source_name == entry2.attribution.source_name):
            return True
        
        return False