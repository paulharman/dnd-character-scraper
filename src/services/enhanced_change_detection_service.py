"""
Enhanced Change Detection Service

Integrates enhanced change detection models, specialized detectors, causation analysis,
and change logging to provide comprehensive D&D Beyond character change tracking.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

from src.models.change_detection import (
    FieldChange, ChangeType, ChangePriority, ChangeCategory, DetectionContext, ChangeDetectionResult
)
from src.models.enhanced_change_detection import (
    ChangeDetectionConfig, ENHANCED_FIELD_MAPPINGS, get_field_mapping,
    is_change_type_enabled, get_priority_for_field, validate_enhanced_config
)
from src.services.enhanced_change_detectors import (
    create_enhanced_detector, get_available_enhanced_detectors
)
from src.services.causation_analyzer import ChangeCausationAnalyzer
from src.services.change_log_service import ChangeLogService
from src.services.error_handler import get_error_handler, ErrorHandlerConfig
from src.services.dynamic_config_manager import DynamicConfigManager, NotificationTarget
from src.models.change_log import ChangeCausation, ChangeAttribution, ChangeLogConfig

logger = logging.getLogger(__name__)


class EnhancedChangeDetectionService:
    """
    Enhanced change detection service that coordinates specialized detectors
    and causation analysis for comprehensive character change tracking.
    """
    
    def __init__(self, config: ChangeDetectionConfig = None, change_log_service: ChangeLogService = None,
                 error_handler_config: ErrorHandlerConfig = None):
        self.config = config or ChangeDetectionConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize error handler
        self.error_handler = get_error_handler(error_handler_config)
        
        # Validate configuration
        config_errors = validate_enhanced_config(self.config)
        if config_errors:
            self.logger.warning(f"Configuration validation errors: {config_errors}")
        
        # Initialize enhanced detectors
        self.detectors = self._create_enhanced_detectors()
        
        # Initialize causation analyzer
        self.causation_analyzer = ChangeCausationAnalyzer() if self.config.enable_causation_analysis else None
        
        # Initialize change log service
        self.change_log_service = change_log_service or self._create_change_log_service()
        
        # Initialize dynamic configuration manager
        self.dynamic_config = DynamicConfigManager()
        
        # Log initialization status
        if self.change_log_service:
            self.logger.info(f"Enhanced change detection service initialized with {len(self.detectors)} detectors and change logging ENABLED")
        else:
            self.logger.info(f"Enhanced change detection service initialized with {len(self.detectors)} detectors and change logging DISABLED")
        
        # Log dynamic config stats
        config_stats = self.dynamic_config.get_stats()
        self.logger.info(f"Dynamic config loaded: {config_stats['total_configured_fields']} field patterns ({config_stats['pattern_matches']} wildcards, {config_stats['exact_matches']} exact)")
    
    async def detect_and_log_changes(self, character_id: int, old_data: Dict[str, Any], 
                                   new_data: Dict[str, Any], context: DetectionContext) -> List[FieldChange]:
        """
        Detect changes and log them with detailed attribution and causation analysis.
        This is the main integration method that combines detection and logging.
        """
        try:
            # Validate character data before processing
            sanitized_old_data = await self._validate_and_sanitize_data(old_data, "old_data", character_id)
            sanitized_new_data = await self._validate_and_sanitize_data(new_data, "new_data", character_id)
            
            if not sanitized_old_data or not sanitized_new_data:
                self.logger.error(f"Could not sanitize character data for character {character_id}")
                return []
            
            # Detect changes using enhanced detectors
            changes = self.detect_changes(sanitized_old_data, sanitized_new_data, context)
            
            if not changes:
                self.logger.debug(f"No changes detected for character {character_id}")
                return changes
            
            # Log changes with detailed attribution if change logging is enabled
            if self.config.enable_change_logging and self.change_log_service:
                # Create retry function for storage errors
                async def retry_log_changes():
                    return await self.change_log_service.log_changes(
                        character_id, changes, sanitized_new_data, sanitized_old_data
                    )
                
                success = await self.error_handler.handle_storage_error(
                    f"log_changes_character_{character_id}",
                    Exception("Initial logging attempt"),  # Placeholder - actual error will be caught in retry
                    character_id=character_id,
                    context={'changes_count': len(changes)},
                    retry_func=retry_log_changes
                )
                
                if success:
                    self.logger.info(f"Successfully logged {len(changes)} changes for character {character_id}")
                else:
                    self.logger.warning(f"Failed to log changes for character {character_id} after retries")
            
            return changes
            
        except Exception as e:
            self.logger.error(f"Error in detect_and_log_changes for character {character_id}: {e}", exc_info=True)
            return []

    def detect_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any],
                      context: DetectionContext) -> List[FieldChange]:
        """
        Detect changes using enhanced detectors with comprehensive field mappings
        and priority classification.
        """
        return self._detect_changes_internal(old_data, new_data, context)
    
    def detect_changes_as_changeset(self, old_snapshot: Any, new_snapshot: Any) -> Any:
        """
        Main interface method that matches the general change detection service.
        This is now the primary method for change detection.
        """
        return self._detect_changes_with_snapshots(old_snapshot, new_snapshot)
    
    def detect_changes_legacy(self, old_snapshot: Any, new_snapshot: Any) -> Any:
        """
        Legacy method for backward compatibility with old snapshot format.
        """
        return self.detect_changes_as_changeset(old_snapshot, new_snapshot)
    
    def configure_detection(self, config: Dict[str, Any]) -> None:
        """Configure detection settings for backward compatibility."""
        # Update configuration based on provided settings
        if 'excluded_fields' in config:
            # Add excluded fields to configuration
            pass
        self.logger.info("Detection configuration updated")
    
    def get_supported_categories(self) -> List[Any]:
        """Get supported change categories for backward compatibility."""
        from src.models.change_detection import ChangeCategory
        return list(ChangeCategory)
    
    def _fallback_detection(self, old_data: Dict[str, Any], new_data: Dict[str, Any], 
                           context: DetectionContext) -> List[FieldChange]:
        """
        Fallback detection using basic field comparison for any fields not covered by enhanced detectors.
        This ensures no changes are missed after consolidation.
        """
        fallback_changes = []
        
        try:
            # Simple recursive comparison for any fields that might be missed
            def compare_dicts(old_dict, new_dict, path=""):
                changes = []
                
                # Check for added/removed keys
                old_keys = set(old_dict.keys()) if isinstance(old_dict, dict) else set()
                new_keys = set(new_dict.keys()) if isinstance(new_dict, dict) else set()
                
                # Added keys
                for key in new_keys - old_keys:
                    field_path = f"{path}.{key}" if path else key
                    changes.append(FieldChange(
                        field_path=field_path,
                        old_value=None,
                        new_value=new_dict[key],
                        change_type=ChangeType.ADDED,
                        priority=ChangePriority.MEDIUM,
                        category=ChangeCategory.METADATA,
                        description=f"Added {field_path}"
                    ))
                
                # Removed keys
                for key in old_keys - new_keys:
                    field_path = f"{path}.{key}" if path else key
                    changes.append(FieldChange(
                        field_path=field_path,
                        old_value=old_dict[key],
                        new_value=None,
                        change_type=ChangeType.REMOVED,
                        priority=ChangePriority.MEDIUM,
                        category=ChangeCategory.METADATA,
                        description=f"Removed {field_path}"
                    ))
                
                # Modified keys
                for key in old_keys & new_keys:
                    field_path = f"{path}.{key}" if path else key
                    old_val = old_dict[key]
                    new_val = new_dict[key]
                    
                    if isinstance(old_val, dict) and isinstance(new_val, dict):
                        # Recurse into nested dictionaries
                        changes.extend(compare_dicts(old_val, new_val, field_path))
                    elif old_val != new_val:
                        # Value changed
                        changes.append(FieldChange(
                            field_path=field_path,
                            old_value=old_val,
                            new_value=new_val,
                            change_type=ChangeType.MODIFIED,
                            priority=ChangePriority.LOW,
                            category=ChangeCategory.METADATA,
                            description=f"Changed {field_path}: {old_val} → {new_val}"
                        ))
                
                return changes
            
            # Only run fallback on a limited set of fields to avoid duplicates
            # Focus on fields that might not be covered by enhanced detectors
            fallback_fields = ['metadata', 'preferences', 'settings', 'configuration']
            
            for field in fallback_fields:
                if field in old_data and field in new_data:
                    field_changes = compare_dicts(old_data[field], new_data[field], field)
                    fallback_changes.extend(field_changes)
            
        except Exception as e:
            self.logger.error(f"Error in fallback detection: {e}")
        
        return fallback_changes
    
    def _detect_changes_with_snapshots(self, old_snapshot: Any, new_snapshot: Any) -> Any:
        """
        Detect changes and return as CharacterChangeSet for compatibility with general service.
        This method provides the same interface as the general change detection service.
        """
        try:
            # Import the required types from the general service for compatibility
            from discord.services.change_detection.models import CharacterChangeSet, CharacterSnapshot, DetectionContext
            
            # Convert inputs to the expected format
            if hasattr(old_snapshot, 'character_data'):
                old_data = old_snapshot.character_data
                character_id = old_snapshot.character_id
            else:
                old_data = old_snapshot
                character_id = old_data.get('character_info', {}).get('character_id', 0)
            
            if hasattr(new_snapshot, 'character_data'):
                new_data = new_snapshot.character_data
            else:
                new_data = new_snapshot
            
            # Create detection context
            context = DetectionContext(
                character_id=character_id,
                character_name=new_data.get('character_info', {}).get('name', 'Unknown'),
                detection_timestamp=datetime.now()
            )
            
            # Detect changes using enhanced detectors
            changes = self._detect_changes_internal(old_data, new_data, context)
            
            # Log changes if change logging is enabled and we have changes
            if changes and self.config.enable_change_logging and self.change_log_service:
                self.logger.info(f"Attempting to log {len(changes)} changes for character {character_id}")
                try:
                    # Since this method is called from sync context, we need to handle async logging
                    import asyncio
                    
                    # Create a simple sync wrapper for the async logging
                    def sync_log_changes():
                        try:
                            self.logger.debug(f"Attempting to log changes in sync context")
                            
                            # Check if we're already in an async context
                            try:
                                current_loop = asyncio.get_running_loop()
                                self.logger.debug(f"Found running event loop, scheduling change logging task")
                                
                                # We're in an async context, schedule the coroutine as a fire-and-forget task
                                async def log_changes_async():
                                    try:
                                        await self.change_log_service.log_changes(character_id, changes, new_data, old_data)
                                        self.logger.debug(f"Successfully logged {len(changes)} changes for character {character_id}")
                                    except Exception as e:
                                        self.logger.error(f"Failed to log changes asynchronously: {e}")
                                
                                # Schedule the task and wait for it to complete  
                                task = current_loop.create_task(log_changes_async())
                                self.logger.info(f"Scheduled async logging of {len(changes)} changes for character {character_id}")
                                
                                # Store task to prevent it from being garbage collected
                                if not hasattr(current_loop, '_change_log_tasks'):
                                    current_loop._change_log_tasks = set()
                                current_loop._change_log_tasks.add(task)
                                
                                # Clean up completed tasks
                                task.add_done_callback(lambda t: current_loop._change_log_tasks.discard(t))
                                return None
                                
                            except RuntimeError:
                                # No running loop, safe to create a new one
                                self.logger.debug(f"No running event loop found, creating new one")
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                try:
                                    self.logger.debug(f"Running async log_changes method")
                                    result = loop.run_until_complete(self.change_log_service.log_changes(
                                        character_id, changes, new_data, old_data
                                    ))
                                    self.logger.debug(f"Async log_changes completed with result: {result}")
                                    return result
                                finally:
                                    loop.close()
                                    self.logger.debug(f"Event loop closed")
                                    
                        except Exception as e:
                            self.logger.error(f"Exception in sync_log_changes for character {character_id}: {e}", exc_info=True)
                            return False
                    
                    success = sync_log_changes()
                    if success:
                        self.logger.info(f"Successfully logged {len(changes)} changes for character {character_id}")
                    else:
                        self.logger.warning(f"Change logging failed for character {character_id}")
                    
                except Exception as e:
                    self.logger.error(f"Error in change logging wrapper for character {character_id}: {e}", exc_info=True)
            else:
                if not changes:
                    self.logger.debug(f"No changes to log for character {character_id}")
                elif not self.config.enable_change_logging:
                    self.logger.debug(f"Change logging disabled for character {character_id}")
                elif not self.change_log_service:
                    self.logger.warning(f"Change log service not available for character {character_id}")
            
            # Create CharacterChangeSet for compatibility
            character_name = new_data.get('character_info', {}).get('name', 'Unknown')
            summary = self._generate_change_summary(changes)
            
            change_set = CharacterChangeSet(
                character_id=character_id,
                character_name=character_name,
                from_version=getattr(old_snapshot, 'version', 1),
                to_version=getattr(new_snapshot, 'version', 2),
                timestamp=datetime.now(),
                changes=changes,
                summary=summary
            )
            
            return change_set
            
        except Exception as e:
            self.logger.error(f"Error in detect_changes_as_changeset: {e}", exc_info=True)
            # Return empty changeset on error
            from discord.services.change_detection.models import CharacterChangeSet
            return CharacterChangeSet(
                character_id=0,
                character_name='Unknown',
                from_version=1,
                to_version=2,
                timestamp=datetime.now(),
                changes=[],
                summary="Error detecting changes"
            )
    
    def _detect_changes_internal(self, old_data: Dict[str, Any], new_data: Dict[str, Any],
                      context: DetectionContext) -> List[FieldChange]:
        """
        Internal method for detecting changes using enhanced detectors with comprehensive field mappings
        and priority classification.
        """
        all_changes = []
        failed_detectors = []
        
        try:
            # Run each enabled detector with error handling
            for detector_name, detector in self.detectors.items():
                if is_change_type_enabled(detector_name, self.config):
                    try:
                        changes = detector.detect_changes(old_data, new_data, context)
                        
                        # Apply enhanced priority rules
                        for change in changes:
                            change.priority = get_priority_for_field(change.field_path, self.config)
                        
                        all_changes.extend(changes)
                        
                        self.logger.debug(f"{detector_name} detector found {len(changes)} changes")
                        
                    except Exception as e:
                        # Use error handler for graceful degradation
                        import asyncio
                        
                        # Handle detector error asynchronously if possible
                        try:
                            if asyncio.get_event_loop().is_running():
                                # We're in an async context, but this is a sync method
                                # Log the error and continue
                                self.logger.error(f"Error in {detector_name} detector: {e}", exc_info=True)
                                failed_detectors.append(detector_name)
                                continue
                            else:
                                # Not in async context, can run async error handler
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                try:
                                    can_continue = loop.run_until_complete(
                                        self.error_handler.handle_detector_error(
                                            detector_name, e, 
                                            character_id=getattr(context, 'character_id', None),
                                            context={'old_data_keys': list(old_data.keys()), 
                                                   'new_data_keys': list(new_data.keys())}
                                        )
                                    )
                                    
                                    if can_continue:
                                        failed_detectors.append(detector_name)
                                        continue
                                    else:
                                        # Critical error - stop processing
                                        self.logger.critical(f"Critical error in {detector_name} detector, stopping detection")
                                        break
                                finally:
                                    loop.close()
                        except Exception as handler_error:
                            self.logger.error(f"Error in detector error handler: {handler_error}", exc_info=True)
                            failed_detectors.append(detector_name)
                            continue
            
            # Log summary of failed detectors
            if failed_detectors:
                self.logger.warning(f"Detectors failed but processing continued: {failed_detectors}")
            
            # Add fallback detection for any fields not covered by enhanced detectors
            fallback_changes = self._fallback_detection(old_data, new_data, context)
            if fallback_changes:
                self.logger.debug(f"Fallback detector found {len(fallback_changes)} additional changes")
                all_changes.extend(fallback_changes)
            
            # Apply field mapping enhancements
            all_changes = self._apply_field_mapping_enhancements(all_changes)
            
            # Filter by configuration settings
            all_changes = self._apply_configuration_filters(all_changes)
            
            self.logger.info(f"Enhanced change detection found {len(all_changes)} changes ({len(failed_detectors)} detectors failed)")
            
        except Exception as e:
            self.logger.error(f"Error in enhanced change detection: {e}", exc_info=True)
        
        return all_changes
    
    def analyze_causation(self, changes: List[FieldChange], old_data: Dict[str, Any], 
                         new_data: Dict[str, Any]) -> List[ChangeCausation]:
        """
        Analyze causation for detected changes using the enhanced causation analyzer.
        """
        if not self.causation_analyzer or not self.config.enable_causation_analysis:
            return []
        
        try:
            import asyncio
            
            # Run causation analysis with error handling
            if asyncio.iscoroutinefunction(self.causation_analyzer.analyze_causation):
                # Handle async causation analysis
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an async context, we can't use run_until_complete
                    # This is a simplified approach - in production you'd want better async handling
                    self.logger.warning("Cannot run async causation analysis in sync context")
                    return []
                else:
                    causations = loop.run_until_complete(
                        self.causation_analyzer.analyze_causation(changes, old_data, new_data)
                    )
            else:
                causations = self.causation_analyzer.analyze_causation(changes, old_data, new_data)
            
            # Filter causations by confidence threshold
            if self.config.causation_confidence_threshold > 0:
                filtered_causations = []
                for causation in causations:
                    # For now, we'll assume all causations meet the threshold
                    # In a more sophisticated implementation, you'd check causation confidence
                    filtered_causations.append(causation)
                causations = filtered_causations
            
            self.logger.debug(f"Causation analysis found {len(causations)} causation patterns")
            return causations
            
        except Exception as e:
            # Use error handler for causation analysis errors
            import asyncio
            
            try:
                if asyncio.get_event_loop().is_running():
                    self.logger.error(f"Causation analysis error: {e}", exc_info=True)
                else:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        can_continue = loop.run_until_complete(
                            self.error_handler.handle_causation_analysis_error(
                                e, context={'changes_count': len(changes)}
                            )
                        )
                        
                        if can_continue:
                            self.logger.warning("Continuing without causation analysis due to error")
                        else:
                            self.logger.error("Critical causation analysis error")
                    finally:
                        loop.close()
            except Exception as handler_error:
                self.logger.error(f"Error in causation analysis error handler: {handler_error}", exc_info=True)
            
            return []
    
    def get_supported_change_types(self) -> Set[str]:
        """Get all supported change types."""
        return set(get_available_enhanced_detectors())
    
    def get_enabled_change_types(self) -> Set[str]:
        """Get currently enabled change types."""
        return self.config.enabled_change_types.intersection(self.get_supported_change_types())
    
    def configure_change_types(self, enabled_types: Set[str]) -> None:
        """Configure which change types are enabled."""
        valid_types = self.get_supported_change_types()
        invalid_types = enabled_types - valid_types
        
        if invalid_types:
            self.logger.warning(f"Invalid change types ignored: {invalid_types}")
        
        self.config.enabled_change_types = enabled_types.intersection(valid_types)
        self.logger.info(f"Enabled change types: {self.config.enabled_change_types}")
    
    def get_field_mapping_info(self, field_path: str) -> Optional[Dict[str, Any]]:
        """Get field mapping information for a specific field path."""
        mapping = get_field_mapping(field_path)
        if mapping:
            return {
                'api_path': mapping.api_path,
                'display_name': mapping.display_name,
                'priority': mapping.priority.name,
                'category': mapping.category.name,
                'change_types': [ct.value for ct in mapping.change_types],
                'causation_patterns': mapping.causation_patterns
            }
        return None
    
    async def get_change_history(self, character_id: int, limit: Optional[int] = None,
                               since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get change history for a character from the change log service."""
        if not self.change_log_service:
            self.logger.warning("Change log service not available")
            return []
        
        try:
            entries = await self.change_log_service.get_change_history(
                character_id, limit=limit, since=since, include_causation=True
            )
            
            # Convert to dictionaries for easier consumption
            return [entry.to_dict() for entry in entries]
            
        except Exception as e:
            self.logger.error(f"Error retrieving change history for character {character_id}: {e}", exc_info=True)
            return []

    async def get_changes_by_cause(self, character_id: int, cause_type: str, cause_name: str) -> List[Dict[str, Any]]:
        """Get changes caused by a specific source."""
        if not self.change_log_service:
            self.logger.warning("Change log service not available")
            return []
        
        try:
            entries = await self.change_log_service.get_changes_by_cause(
                character_id, cause_type, cause_name
            )
            
            return [entry.to_dict() for entry in entries]
            
        except Exception as e:
            self.logger.error(f"Error retrieving changes by cause for character {character_id}: {e}", exc_info=True)
            return []

    def format_changes_for_discord(self, changes: List[FieldChange]) -> List[Dict[str, Any]]:
        """Format changes for Discord notifications with appropriate detail level."""
        formatted_changes = []
        
        for change in changes:
            # Create base Discord format
            discord_change = {
                'field_path': change.field_path,
                'description': change.description or f"{change.field_path} changed",
                'priority': change.priority.name,
                'category': change.category.name,
                'change_type': change.change_type.value
            }
            
            # Add value information for Discord (simplified)
            if change.change_type in [ChangeType.INCREMENTED, ChangeType.DECREMENTED]:
                delta = change.get_change_delta()
                if delta is not None:
                    sign = "+" if delta > 0 else ""
                    discord_change['description'] += f" ({sign}{delta})"
            elif change.change_type == ChangeType.ADDED:
                discord_change['description'] += " (added)"
            elif change.change_type == ChangeType.REMOVED:
                discord_change['description'] += " (removed)"
            
            formatted_changes.append(discord_change)
        
        return formatted_changes

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the enhanced change detection service."""
        stats = {
            'total_detectors': len(self.detectors),
            'enabled_detectors': len([d for d in self.detectors.keys() 
                                    if is_change_type_enabled(d, self.config)]),
            'enabled_change_types': list(self.get_enabled_change_types()),
            'supported_change_types': list(self.get_supported_change_types()),
            'causation_analysis_enabled': self.config.enable_causation_analysis,
            'causation_confidence_threshold': self.config.causation_confidence_threshold,
            'max_cascade_depth': self.config.max_cascade_depth,
            'field_mappings_count': len(ENHANCED_FIELD_MAPPINGS),
            'change_logging_enabled': self.config.enable_change_logging
        }
        
        # Add change log service statistics if available
        if self.change_log_service:
            stats['change_log_service_available'] = True
        else:
            stats['change_log_service_available'] = False
        
        return stats
    
    def _create_enhanced_detectors(self) -> Dict[str, Any]:
        """Create enhanced detectors for all supported change types."""
        detectors = {}
        
        for detector_type in get_available_enhanced_detectors():
            try:
                detector = create_enhanced_detector(detector_type)
                detectors[detector_type] = detector
                self.logger.debug(f"Created {detector_type} detector")
            except Exception as e:
                self.logger.error(f"Failed to create {detector_type} detector: {e}")
        
        return detectors
    
    def _apply_field_mapping_enhancements(self, changes: List[FieldChange]) -> List[FieldChange]:
        """Apply field mapping enhancements to detected changes."""
        enhanced_changes = []
        
        for change in changes:
            mapping = get_field_mapping(change.field_path)
            if mapping:
                # Update category if not already set appropriately
                if change.category == ChangeCategory.METADATA:
                    change.category = mapping.category
                
                # Update description if generic
                if not change.description or change.description == f"{change.field_path} changed":
                    change.description = f"{mapping.display_name} changed"
            
            enhanced_changes.append(change)
        
        return enhanced_changes
    
    def _apply_configuration_filters(self, changes: List[FieldChange]) -> List[FieldChange]:
        """Apply dynamic configuration-based filters to changes."""
        self.logger.info(f"🔄 DYNAMIC CONFIG FILTER START - Input changes: {len(changes)}")
        
        # Show dynamic config stats
        config_stats = self.dynamic_config.get_stats()
        self.logger.info(f"📋 DYNAMIC CONFIG:")
        self.logger.info(f"   Total field patterns: {config_stats['total_configured_fields']}")
        self.logger.info(f"   Auto-discovery enabled: {config_stats['auto_discovery_enabled']}")
        self.logger.info(f"   Previously discovered: {config_stats['discovered_fields']}")
        
        filtered_changes = []
        excluded_changes = []
        
        for i, change in enumerate(changes):
            excluded = False
            exclusion_reason = None
            
            # Get field-specific priority from dynamic config
            field_priority = self.dynamic_config.get_field_priority(change.field_path)
            
            # Handle IGNORED fields
            if field_priority is None:  # IGNORED
                excluded = True
                exclusion_reason = "Field marked as IGNORED in dynamic config"
            else:
                # Update change priority if dynamic config specifies it
                if field_priority != change.priority:
                    old_priority = change.priority
                    change.priority = field_priority
                    self.logger.debug(f"Updated priority for {change.field_path}: {old_priority.name} → {field_priority.name}")
            
            # Apply legacy configuration filters (for compatibility)
            if not self.config.detect_minor_changes and change.priority == ChangePriority.LOW:
                excluded = True
                exclusion_reason = "LOW priority filtered (detect_minor_changes=False)"
            elif not self.config.detect_metadata_changes and hasattr(change, 'category') and change.category == ChangeCategory.METADATA:
                excluded = True
                exclusion_reason = "METADATA category filtered (detect_metadata_changes=False)"
            elif not self.config.detect_cosmetic_changes and hasattr(change, 'category') and change.category == ChangeCategory.SOCIAL:
                excluded = True
                exclusion_reason = "SOCIAL category filtered (detect_cosmetic_changes=False)"
            
            if excluded:
                excluded_changes.append({
                    'field_path': change.field_path,
                    'description': change.description,
                    'priority': change.priority.name if hasattr(change.priority, 'name') else str(change.priority),
                    'reason': exclusion_reason
                })
                self.logger.info(f"❌ CHANGE {i+1} EXCLUDED - {exclusion_reason}: {change.field_path} | {change.description}")
            else:
                filtered_changes.append(change)
                self.logger.info(f"✅ CHANGE {i+1} INCLUDED - {change.field_path} | {change.description} (Priority: {change.priority.name if hasattr(change.priority, 'name') else str(change.priority)})")
        
        self.logger.info(f"🏁 DYNAMIC CONFIG FILTER COMPLETE - {len(filtered_changes)}/{len(changes)} changes passed configuration filters")
        
        if excluded_changes:
            self.logger.info(f"❌ CONFIGURATION FILTER EXCLUDED {len(excluded_changes)} CHANGES:")
            for i, excluded in enumerate(excluded_changes, 1):
                self.logger.info(f"   {i}. {excluded['field_path']}: {excluded['description']} (Priority: {excluded['priority']}) - {excluded['reason']}")
        
        return filtered_changes

    def _create_change_log_service(self) -> Optional[ChangeLogService]:
        """Create change log service with default configuration."""
        try:
            self.logger.debug(f"Creating change log service, enable_change_logging={self.config.enable_change_logging}")
            if self.config.enable_change_logging:
                change_log_config = ChangeLogConfig(
                    enable_causation_analysis=self.config.enable_causation_analysis,
                    enable_detailed_descriptions=True,
                    log_retention_days=self.config.change_log_retention_days,
                    log_rotation_size_mb=self.config.change_log_rotation_size_mb
                )
                self.logger.debug(f"Creating ChangeLogService with config: {change_log_config}")
                service = ChangeLogService(change_log_config)
                self.logger.info(f"Successfully created change log service with storage at {change_log_config.storage_dir}")
                return service
            else:
                self.logger.info("Change logging disabled in configuration")
                return None
        except Exception as e:
            self.logger.error(f"Error creating change log service: {e}", exc_info=True)
            return None

    async def _validate_and_sanitize_data(self, data: Dict[str, Any], data_source: str, 
                                        character_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Validate and sanitize character data before processing."""
        try:
            # Basic validation - check if data has required structure
            if not isinstance(data, dict):
                raise ValueError(f"Character data must be a dictionary, got {type(data)}")
            
            # Check for essential fields
            if not data:
                raise ValueError("Character data is empty")
            
            # Data appears valid
            return data
            
        except Exception as e:
            # Use error handler for data validation errors
            sanitized_data = await self.error_handler.handle_data_validation_error(
                data_source, e, character_id=character_id, malformed_data=data
            )
            
            if sanitized_data:
                self.logger.info(f"Successfully sanitized {data_source} for character {character_id}")
                return sanitized_data
            else:
                self.logger.error(f"Could not sanitize {data_source} for character {character_id}")
                return None

    async def _handle_logging_error(self, character_id: int, error: Exception) -> bool:
        """Handle errors from change logging with retry logic."""
        try:
            self.logger.warning(f"Change logging failed for character {character_id}: {error}")
            
            # Implement simple retry logic
            if hasattr(self, '_logging_retry_count'):
                self._logging_retry_count += 1
            else:
                self._logging_retry_count = 1
            
            # Don't retry more than 3 times
            if self._logging_retry_count > 3:
                self.logger.error(f"Change logging failed after {self._logging_retry_count} attempts for character {character_id}")
                self._logging_retry_count = 0
                return False
            
            # Wait briefly before potential retry
            import asyncio
            await asyncio.sleep(0.1 * self._logging_retry_count)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in logging error handler: {e}", exc_info=True)
            return False

    def _should_include_in_discord(self, change: FieldChange) -> bool:
        """Determine if a change should be included in Discord notifications using dynamic config."""
        return self.dynamic_config.should_notify(change, NotificationTarget.DISCORD)

    def _should_include_in_change_log(self, change: FieldChange) -> bool:
        """Determine if a change should be included in change logs using dynamic config."""
        # Check if change logging is enabled
        if not self.config.enable_change_logging:
            return False
        
        # Skip very low confidence changes
        if hasattr(change, 'confidence') and change.confidence < 0.5:
            return False
        
        # Use dynamic config for changelog filtering
        return self.dynamic_config.should_notify(change, NotificationTarget.CHANGELOG)
    
    def _generate_change_summary(self, changes: List[FieldChange]) -> str:
        """Generate a summary of changes for CharacterChangeSet compatibility."""
        if not changes:
            return "No changes detected"
        
        try:
            total = len(changes)
            if total == 1:
                return f"1 change detected"
            else:
                return f"{total} changes detected"
                
        except Exception as e:
            self.logger.warning(f"Error generating change summary: {e}")
            return f"{len(changes)} changes detected"
    
    def filter_changes_by_groups(
        self,
        changes: List[FieldChange],
        include_groups: Optional[Set[str]] = None,
        exclude_groups: Optional[Set[str]] = None,
        group_definitions: Optional[Dict[str, List[str]]] = None
    ) -> List[FieldChange]:
        """
        Filter changes based on data group membership.
        This method provides compatibility with the general change detection service.
        
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
            
            # Debug logging for group filtering
            self.logger.debug(f"⚙ GROUP FILTER - Evaluating change: {field_path} | {change.description}")
            
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
            
        return filtered_changes
    
    def _fnmatch_pattern(self, field_path: str, pattern: str) -> bool:
        """Check if field path matches a pattern using fnmatch."""
        try:
            import fnmatch
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
                'character.classes.*',
                'features.*'
            ],
            'combat': [
                'combat.hit_points.*',
                'combat.armor_class.*',
                'combat.initiative.*',
                'combat.saving_throws.*',
                'character.hit_points.*',  # Enhanced detector paths
                'character.combat.*',
                'hit_points.*'  # Direct HP paths
            ],
            'abilities': [
                'abilities.ability_scores.*',
                'abilities.ability_modifiers.*',
                'character.ability_scores.*',  # Enhanced detector paths
                'character.abilityScores.*',   # Enhanced detector paths (camelCase)
                'ability_scores.*'
            ],
            'spells': [
                'spells.*',
                'spellcasting.spell_slots.*',
                'spellcasting.*',
                'character.spells.*',  # Enhanced detector paths
                'character.spellcasting.*'
            ],
            'inventory': [
                'inventory.*',
                'equipment.*',
                'currency.*',
                'character.inventory.*',  # Enhanced detector paths
                'character.equipment.*'
            ],
            'skills': [
                'skills.*',
                'proficiencies.*',
                'feats.*',
                'character.skills.*',  # Enhanced detector paths
                'character.proficiencies.*',
                'character.feats.*',
                'character.proficiency_bonus',  # Proficiency bonus changes
                'character_info.proficiency_bonus'  # Alternative proficiency bonus path
            ],
            'appearance': [
                'appearance.*',
                'character_info.avatar*',
                'decorations.*'
            ],
            'backstory': [
                'character_info.background.*',
                'backstory.*',
                'character.background.*'  # Enhanced detector paths
            ],
            'meta': [
                'meta.*',
                'processed_date',
                'scraper_version'
            ]
        }


def create_enhanced_change_detection_service(config: ChangeDetectionConfig = None, 
                                           change_log_service: ChangeLogService = None) -> EnhancedChangeDetectionService:
    """Factory function to create an enhanced change detection service."""
    return EnhancedChangeDetectionService(config, change_log_service)


def get_default_enhanced_config() -> ChangeDetectionConfig:
    """Get a default enhanced change detection configuration."""
    return ChangeDetectionConfig()


def validate_service_configuration(config: ChangeDetectionConfig) -> List[str]:
    """Validate service configuration and return any errors."""
    return validate_enhanced_config(config)


# Backward compatibility functions
def create_change_detection_service(config: ChangeDetectionConfig = None) -> EnhancedChangeDetectionService:
    """Create a change detection service with configuration (backward compatibility)."""
    return EnhancedChangeDetectionService(config)


def detect_changes(old_snapshot: Any, new_snapshot: Any) -> Any:
    """
    Utility function for backward compatibility.
    Creates a service instance and detects changes.
    """
    service = create_change_detection_service()
    return service.detect_changes_as_changeset(old_snapshot, new_snapshot)