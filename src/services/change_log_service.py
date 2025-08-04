"""
Change Log Service

Provides persistent logging of all character changes with structured storage,
detailed attribution, and causation analysis.
"""

import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
import os

from src.models.change_detection import FieldChange
from src.models.change_log import (
    ChangeLogEntry, ChangeLogConfig, ChangeLogMetadata, ChangeLogFile,
    ChangeCausation, ChangeAttribution
)
from src.services.causation_analyzer import ChangeCausationAnalyzer
from src.services.error_handler import get_error_handler, ErrorHandlerConfig

logger = logging.getLogger(__name__)


class ChangeLogService:
    """
    Service for persistent logging of character changes with comprehensive attribution
    and causation analysis.
    """
    
    def __init__(self, config: ChangeLogConfig = None, error_handler_config: ErrorHandlerConfig = None):
        self.config = config or ChangeLogConfig()
        self.log_files: Dict[int, Path] = {}
        self.causation_analyzer = ChangeCausationAnalyzer()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize error handler
        self.error_handler = get_error_handler(error_handler_config)
        
        # Ensure storage directory exists
        try:
            self.config.storage_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"Failed to create storage directory {self.config.storage_dir}: {e}")
            raise
        
        self.logger.info(f"Change log service initialized with storage at {self.config.storage_dir}")
    
    async def log_changes(self, character_id: int, changes: List[FieldChange], 
                         character_data: Dict[str, Any], old_character_data: Optional[Dict[str, Any]] = None) -> bool:
        """Log multiple changes with comprehensive attribution and causation analysis."""
        self.logger.info(f"ChangeLogService.log_changes called for character {character_id} with {len(changes)} changes")
        try:
            if not changes:
                self.logger.debug(f"No changes to log for character {character_id}")
                return True
            
            # Extract character name
            character_name = self._extract_character_name(character_data)
            
            # Analyze causation if enabled
            causations = []
            if self.config.enable_causation_analysis and old_character_data:
                causations = await self.causation_analyzer.analyze_causation(
                    changes, old_character_data, character_data
                )
            
            # Create change log entries
            log_entries = []
            for change in changes:
                # Find causation and attribution for this change
                causation, attribution = self._find_change_causation_and_attribution(
                    change, causations, character_data
                )
                
                # Generate detailed description
                detailed_description = self._generate_detailed_description(
                    change, causation, attribution
                ) if self.config.enable_detailed_descriptions else change.description
                
                # Create log entry
                log_entry = ChangeLogEntry.from_field_change(
                    change, character_id, character_name,
                    causation=causation,
                    attribution=attribution,
                    detailed_description=detailed_description
                )
                
                log_entries.append(log_entry)
            
            # Write entries to log file
            success = await self._write_log_entries(character_id, log_entries)
            
            if success:
                self.logger.info(f"Successfully logged {len(log_entries)} changes for character {character_id}")
            else:
                self.logger.error(f"Failed to log changes for character {character_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error logging changes for character {character_id}: {e}", exc_info=True)
            return False
    
    async def get_change_history(self, character_id: int, 
                               limit: Optional[int] = None,
                               since: Optional[datetime] = None,
                               include_causation: bool = True) -> List[ChangeLogEntry]:
        """Retrieve change history with optional causation details."""
        try:
            entries = []
            
            # Get all log files for this character
            log_files = self._get_character_log_files(character_id)
            
            for log_file_path in log_files:
                try:
                    log_file = await self._load_log_file(log_file_path)
                    
                    # Filter by date if specified
                    file_entries = log_file.entries
                    if since:
                        file_entries = [entry for entry in file_entries if entry.timestamp >= since]
                    
                    entries.extend(file_entries)
                    
                except Exception as e:
                    self.logger.warning(f"Error loading log file {log_file_path}: {e}")
                    continue
            
            # Sort by timestamp (most recent first)
            entries.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply limit if specified
            if limit:
                entries = entries[:limit]
            
            # Remove causation data if not requested
            if not include_causation:
                for entry in entries:
                    entry.causation = None
                    entry.attribution = None
            
            self.logger.debug(f"Retrieved {len(entries)} change history entries for character {character_id}")
            return entries
            
        except Exception as e:
            self.logger.error(f"Error retrieving change history for character {character_id}: {e}", exc_info=True)
            return []
    
    async def get_changes_by_cause(self, character_id: int, 
                                 cause_type: str, cause_name: str) -> List[ChangeLogEntry]:
        """Get all changes caused by a specific source (e.g., specific feat)."""
        try:
            all_entries = await self.get_change_history(character_id, include_causation=True)
            
            # Filter by cause
            matching_entries = []
            for entry in all_entries:
                if (entry.attribution and 
                    entry.attribution.source == cause_type and 
                    entry.attribution.source_name == cause_name):
                    matching_entries.append(entry)
            
            self.logger.debug(f"Found {len(matching_entries)} changes caused by {cause_type}:{cause_name} for character {character_id}")
            return matching_entries
            
        except Exception as e:
            self.logger.error(f"Error getting changes by cause for character {character_id}: {e}", exc_info=True)
            return []
    
    async def rotate_logs(self, character_id: int, character_name: str = None) -> bool:
        """Rotate log files when they become too large."""
        try:
            # Find the current log file (could be old or new naming pattern)
            log_files = self._get_character_log_files(character_id)
            if not log_files:
                return True
            
            current_log_path = log_files[0]  # Should be only one current file
            
            # Check file size
            file_size_mb = current_log_path.stat().st_size / (1024 * 1024)
            
            if file_size_mb >= self.config.log_rotation_size_mb:
                # Load current log file to update rotation count and get character name
                try:
                    log_file = await self._load_log_file(current_log_path)
                    log_file.metadata.rotation_count += 1
                    character_name = log_file.metadata.character_name or character_name or "Unknown"
                except Exception as e:
                    self.logger.warning(f"Could not load log file for rotation count update: {e}")
                    # Create minimal metadata for rotation
                    character_name = character_name or "Unknown"
                    metadata = ChangeLogMetadata(
                        character_id=character_id,
                        character_name=character_name,
                        rotation_count=1
                    )
                    log_file = ChangeLogFile(metadata=metadata)
                
                # Create rotated directory structure with character name
                sanitized_name = self._sanitize_filename(character_name, character_id)
                rotated_dir = self.config.storage_dir / f"{sanitized_name}_{character_id}" / "rotated"
                rotated_dir.mkdir(parents=True, exist_ok=True)
                
                # Create backup filename with timestamp and rotation count
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                rotation_count = log_file.metadata.rotation_count
                backup_filename = f"changes_{timestamp}_r{rotation_count:03d}.json"
                backup_path = rotated_dir / backup_filename
                
                # Save the rotated log with updated metadata
                await self._save_log_file(backup_path, log_file)
                
                # Remove original file
                current_log_path.unlink()
                
                self.logger.info(f"Rotated log file for character {character_id}: {backup_path}")
                
                # Update storage health metrics
                await self._update_storage_health_metrics(character_id, "rotation", {
                    "rotated_file": str(backup_path),
                    "file_size_mb": file_size_mb,
                    "rotation_count": rotation_count
                })
                
                return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error rotating logs for character {character_id}: {e}", exc_info=True)
            await self._update_storage_health_metrics(character_id, "rotation_error", {
                "error": str(e)
            })
            return False
    
    async def cleanup_old_logs(self, retention_days: Optional[int] = None) -> int:
        """Clean up old log entries based on retention policy."""
        try:
            retention_days = retention_days or self.config.log_retention_days
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            cleaned_count = 0
            archived_count = 0
            deleted_count = 0
            total_size_cleaned = 0
            
            # Process current log files - handle all naming patterns
            log_file_patterns = [
                "*_changes.json",  # New pattern: {name}_{id}_changes.json and old patterns
            ]
            
            for pattern in log_file_patterns:
                for log_file_path in self.config.storage_dir.glob(pattern):
                    # Skip if it's not actually a character log file
                    if not self._extract_character_id_from_path(log_file_path):
                        continue
                        
                    try:
                        file_size = log_file_path.stat().st_size
                        file_mtime = datetime.fromtimestamp(log_file_path.stat().st_mtime)
                        
                        if file_mtime < cutoff_date:
                            if self.config.backup_old_logs:
                                # Move to archive instead of deleting
                                archive_dir = self.config.storage_dir / "archive"
                                archive_dir.mkdir(exist_ok=True)
                                archive_path = archive_dir / log_file_path.name
                                log_file_path.rename(archive_path)
                                self.logger.debug(f"Archived old log file: {archive_path}")
                                archived_count += 1
                            else:
                                # Delete the file
                                log_file_path.unlink()
                                self.logger.debug(f"Deleted old log file: {log_file_path}")
                                deleted_count += 1
                            
                            cleaned_count += 1
                            total_size_cleaned += file_size
                            
                    except Exception as e:
                        self.logger.warning(f"Error processing log file {log_file_path}: {e}")
                        continue
            
            # Process rotated log files in character subdirectories
            for character_dir in self.config.storage_dir.glob("character_*"):
                if not character_dir.is_dir():
                    continue
                    
                rotated_dir = character_dir / "rotated"
                if not rotated_dir.exists():
                    continue
                
                for rotated_file in rotated_dir.glob("changes_*.json"):
                    try:
                        file_size = rotated_file.stat().st_size
                        file_mtime = datetime.fromtimestamp(rotated_file.stat().st_mtime)
                        
                        if file_mtime < cutoff_date:
                            if self.config.backup_old_logs:
                                # Move to archive
                                archive_dir = self.config.storage_dir / "archive" / character_dir.name
                                archive_dir.mkdir(parents=True, exist_ok=True)
                                archive_path = archive_dir / rotated_file.name
                                rotated_file.rename(archive_path)
                                self.logger.debug(f"Archived old rotated log: {archive_path}")
                                archived_count += 1
                            else:
                                # Delete the file
                                rotated_file.unlink()
                                self.logger.debug(f"Deleted old rotated log: {rotated_file}")
                                deleted_count += 1
                            
                            cleaned_count += 1
                            total_size_cleaned += file_size
                            
                    except Exception as e:
                        self.logger.warning(f"Error processing rotated log file {rotated_file}: {e}")
                        continue
                
                # Remove empty rotated directories
                try:
                    if rotated_dir.exists() and not any(rotated_dir.iterdir()):
                        rotated_dir.rmdir()
                        self.logger.debug(f"Removed empty rotated directory: {rotated_dir}")
                except Exception as e:
                    self.logger.warning(f"Error removing empty directory {rotated_dir}: {e}")
            
            # Update storage health metrics
            await self._update_storage_health_metrics(None, "cleanup", {
                "retention_days": retention_days,
                "total_cleaned": cleaned_count,
                "archived": archived_count,
                "deleted": deleted_count,
                "size_cleaned_mb": round(total_size_cleaned / (1024 * 1024), 2),
                "cutoff_date": cutoff_date.isoformat()
            })
            
            self.logger.info(f"Cleaned up {cleaned_count} old log files (retention: {retention_days} days) - "
                           f"Archived: {archived_count}, Deleted: {deleted_count}, "
                           f"Size freed: {round(total_size_cleaned / (1024 * 1024), 2)} MB")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old logs: {e}", exc_info=True)
            await self._update_storage_health_metrics(None, "cleanup_error", {
                "error": str(e)
            })
            return 0
    
    async def get_log_statistics(self, character_id: int) -> Dict[str, Any]:
        """Get statistics about change logs for a character."""
        try:
            log_files = self._get_character_log_files(character_id)
            
            total_entries = 0
            total_size = 0
            oldest_entry = None
            newest_entry = None
            category_counts = {}
            
            for log_file_path in log_files:
                try:
                    log_file = await self._load_log_file(log_file_path)
                    
                    total_entries += len(log_file.entries)
                    total_size += log_file_path.stat().st_size
                    
                    # Update category counts
                    for category, count in log_file.metadata.change_categories.items():
                        category_counts[category] = category_counts.get(category, 0) + count
                    
                    # Track oldest and newest entries
                    if log_file.entries:
                        file_oldest = min(log_file.entries, key=lambda x: x.timestamp)
                        file_newest = max(log_file.entries, key=lambda x: x.timestamp)
                        
                        if oldest_entry is None or file_oldest.timestamp < oldest_entry:
                            oldest_entry = file_oldest.timestamp
                        
                        if newest_entry is None or file_newest.timestamp > newest_entry:
                            newest_entry = file_newest.timestamp
                    
                except Exception as e:
                    self.logger.warning(f"Error processing log file {log_file_path} for statistics: {e}")
                    continue
            
            return {
                'character_id': character_id,
                'total_entries': total_entries,
                'total_files': len(log_files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'oldest_entry': oldest_entry.isoformat() if oldest_entry else None,
                'newest_entry': newest_entry.isoformat() if newest_entry else None,
                'category_counts': category_counts,
                'storage_file': str(self._get_current_log_file_path(character_id))
            }
            
        except Exception as e:
            self.logger.error(f"Error getting log statistics for character {character_id}: {e}", exc_info=True)
            return {}
    
    def _extract_character_name(self, character_data: Dict[str, Any]) -> str:
        """Extract character name from character data."""
        try:
            # Try character_info field first (v6.0.0 format)
            if 'character_info' in character_data:
                character_info = character_data['character_info']
                if isinstance(character_info, dict) and 'name' in character_info:
                    return character_info['name']
            
            # Try direct name field
            if 'name' in character_data:
                return character_data['name']
            
            return 'Unknown'
            
        except Exception as e:
            self.logger.warning(f"Error extracting character name: {e}")
            return 'Unknown'
    
    def _sanitize_filename(self, name: str, character_id: int = None, max_total_length: int = 200) -> str:
        """
        Sanitize character name for use in filename.
        
        Args:
            name: Character name to sanitize
            character_id: Character ID (used to calculate available space for name)
            max_total_length: Maximum total filename length (default 200 to stay well under 255 limit)
        
        Returns:
            Sanitized character name, truncated if necessary to preserve character ID
        """
        try:
            # Remove or replace invalid filename characters
            invalid_chars = '<>:"/\\|?*'
            sanitized = name
            
            for char in invalid_chars:
                sanitized = sanitized.replace(char, '_')
            
            # Replace multiple spaces/underscores with single underscore
            import re
            sanitized = re.sub(r'[_\s]+', '_', sanitized)
            
            # Remove leading/trailing underscores and spaces
            sanitized = sanitized.strip('_ ')
            
            # Calculate available space for character name
            # Format: {name}_{character_id}_changes.json
            if character_id is not None:
                # Reserve space for: _{character_id}_changes.json
                reserved_space = len(f"_{character_id}_changes.json")
                max_name_length = max_total_length - reserved_space
                
                # Ensure we have at least some space for the name
                if max_name_length < 10:
                    max_name_length = 10
                
                # Truncate if too long, but preserve readability
                if len(sanitized) > max_name_length:
                    sanitized = sanitized[:max_name_length].rstrip('_')
            else:
                # Fallback to original behavior if no character_id provided
                if len(sanitized) > 50:
                    sanitized = sanitized[:50].rstrip('_')
            
            # Ensure we have something valid
            if not sanitized or sanitized.isspace():
                sanitized = 'Unknown'
            
            return sanitized
            
        except Exception as e:
            self.logger.warning(f"Error sanitizing filename '{name}': {e}")
            return 'Unknown'
    
    def _find_change_causation_and_attribution(self, change: FieldChange, 
                                             causations: List[ChangeCausation],
                                             character_data: Dict[str, Any]) -> tuple[Optional[ChangeCausation], Optional[ChangeAttribution]]:
        """Find causation and attribution for a specific change."""
        # Find matching causation
        matching_causation = None
        for causation in causations:
            if change.field_path in causation.related_changes:
                matching_causation = causation
                break
        
        # Generate attribution based on causation
        attribution = None
        if matching_causation:
            attribution = self._generate_attribution(change, matching_causation, character_data)
        
        return matching_causation, attribution
    
    def _generate_attribution(self, change: FieldChange, causation: ChangeCausation,
                            character_data: Dict[str, Any]) -> ChangeAttribution:
        """Generate attribution information for a change."""
        try:
            if causation.trigger == "feat_selection":
                feat_name = causation.trigger_details.get("feat_name", "Unknown Feat")
                return ChangeAttribution(
                    source="feat_selection",
                    source_name=feat_name,
                    source_type="feat",
                    impact_summary=f"Effect of {feat_name} feat"
                )
            
            elif causation.trigger == "level_progression":
                level = causation.trigger_details.get("level_gained", "Unknown")
                class_name = causation.trigger_details.get("class")
                if class_name is None:
                    class_name = "character"  # Default when class is not specified
                return ChangeAttribution(
                    source="level_progression",
                    source_name=f"Level {level}" + (f" {class_name}" if class_name != "character" else ""),
                    source_type="class_feature",
                    impact_summary=f"Level progression to level {level}"
                )
            
            elif causation.trigger == "equipment_change":
                item_name = causation.trigger_details.get("item_name", "Unknown Item")
                return ChangeAttribution(
                    source="equipment_change",
                    source_name=item_name,
                    source_type="equipment",
                    impact_summary=f"Effect of {item_name}"
                )
            
            elif causation.trigger == "ability_score_change":
                ability = causation.trigger_details.get("ability", "Unknown")
                modifier_change = causation.trigger_details.get("modifier_change", 0)
                sign = "+" if modifier_change > 0 else ""
                return ChangeAttribution(
                    source="ability_score_change",
                    source_name=f"{ability} modifier {sign}{modifier_change}",
                    source_type="ability_score",
                    impact_summary=f"Effect of {ability} modifier change"
                )
            
            else:
                return ChangeAttribution(
                    source=causation.trigger,
                    source_name="Unknown",
                    source_type="unknown",
                    impact_summary="Unknown cause"
                )
                
        except Exception as e:
            self.logger.warning(f"Error generating attribution: {e}")
            return ChangeAttribution(
                source="unknown",
                source_name="Unknown",
                source_type="unknown",
                impact_summary="Attribution generation failed"
            )
    
    def _generate_detailed_description(self, change: FieldChange, 
                                     causation: Optional[ChangeCausation],
                                     attribution: Optional[ChangeAttribution]) -> str:
        """Generate detailed description for change log entry."""
        try:
            base_description = change.description or f"{change.field_path} changed"
            
            if attribution:
                detailed = f"{base_description}. {attribution.impact_summary}"
                
                if causation and causation.trigger_details:
                    # Add specific details based on trigger type
                    if causation.trigger == "feat_selection":
                        feat_name = causation.trigger_details.get("feat_name")
                        if feat_name:
                            detailed += f". This change was caused by selecting the {feat_name} feat"
                    
                    elif causation.trigger == "level_progression":
                        level = causation.trigger_details.get("level_gained")
                        class_name = causation.trigger_details.get("class")
                        if level and class_name:
                            detailed += f". This change occurred when advancing to {class_name} level {level}"
                    
                    elif causation.trigger == "ability_score_change":
                        ability = causation.trigger_details.get("ability")
                        old_score = causation.trigger_details.get("old_score")
                        new_score = causation.trigger_details.get("new_score")
                        if ability and old_score is not None and new_score is not None:
                            detailed += f". This change resulted from {ability} increasing from {old_score} to {new_score}"
                
                return detailed
            
            return base_description
            
        except Exception as e:
            self.logger.warning(f"Error generating detailed description: {e}")
            return change.description or f"{change.field_path} changed"
    
    def _get_current_log_file_path(self, character_id: int, character_name: str = None) -> Path:
        """Get the current log file path for a character."""
        if character_name is not None:
            sanitized_name = self._sanitize_filename(character_name, character_id)
            return self.config.storage_dir / f"{sanitized_name}_{character_id}_changes.json"
        else:
            # Fallback to old naming pattern for backward compatibility
            return self.config.storage_dir / f"character_{character_id}_changes.json"
    
    def _get_character_log_files(self, character_id: int) -> List[Path]:
        """Get all log files for a character (supports both old and new naming patterns)."""
        log_files = []
        
        # Check for files with all naming patterns:
        # Pattern 1: {name}_{id}_changes.json (new format)
        # Pattern 2: character_{id}_{name}_changes.json (old new format)
        # Pattern 3: character_{id}_changes.json (original format)
        
        # New pattern: {name}_{id}_changes.json
        for log_file_path in self.config.storage_dir.glob(f"*_{character_id}_changes.json"):
            # Verify it's not the old pattern (character_{id}_{name}_changes.json)
            if not log_file_path.name.startswith("character_"):
                log_files.append(log_file_path)
        
        # Old patterns: character_{id}_*.json
        for log_file_path in self.config.storage_dir.glob(f"character_{character_id}_*.json"):
            if log_file_path.name.endswith("_changes.json"):
                log_files.append(log_file_path)
        
        return log_files
    
    async def _write_log_entries(self, character_id: int, entries: List[ChangeLogEntry]) -> bool:
        """Write log entries to the appropriate log file with error handling and retry."""
        async def write_operation():
            # Ensure storage directory exists
            self.config.storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract character name for filename
            character_name = entries[0].character_name if entries else "Unknown"
            
            # Get current log file path with character name
            log_file_path = self._get_current_log_file_path(character_id, character_name)
            
            # Check if we need to migrate from old naming patterns
            if not log_file_path.exists():
                # Look for existing files to migrate from
                existing_files = self._get_character_log_files(character_id)
                
                # Find the most recent file to migrate from
                if existing_files:
                    # Sort by modification time, most recent first
                    existing_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                    old_log_file_path = existing_files[0]
                    
                    if old_log_file_path != log_file_path:
                        # Migrate from old naming pattern to new one
                        self.logger.info(f"Migrating log file from {old_log_file_path.name} to {log_file_path.name}")
                        old_log_file_path.rename(log_file_path)
            
            # Load existing log file or create new one
            if log_file_path.exists():
                log_file = await self._load_log_file(log_file_path)
                # Update character name in metadata if it has changed
                if log_file.metadata.character_name != character_name:
                    log_file.metadata.character_name = character_name
            else:
                # Create new log file
                metadata = ChangeLogMetadata(
                    character_id=character_id,
                    character_name=character_name,
                    retention_policy_days=self.config.log_retention_days
                )
                log_file = ChangeLogFile(metadata=metadata)
            
            # Add new entries
            for entry in entries:
                log_file.add_entry(entry)
            
            # Check if rotation is needed
            await self.rotate_logs(character_id, character_name)
            
            # Write log file
            await self._save_log_file(log_file_path, log_file)
            
            return True
        
        # Use error handler for storage operations with retry logic
        try:
            return await self.error_handler.handle_storage_error(
                f"write_log_entries_character_{character_id}",
                Exception("Log entry write operation"),  # Placeholder - actual errors caught in retry
                character_id=character_id,
                context={'entries_count': len(entries)},
                retry_func=write_operation
            )
        except Exception as e:
            self.logger.error(f"Error writing log entries for character {character_id}: {e}", exc_info=True)
            return False
    
    async def _load_log_file(self, file_path: Path) -> ChangeLogFile:
        """Load a log file from disk with error handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate loaded data structure
            if not isinstance(data, dict):
                raise ValueError(f"Log file {file_path} contains invalid data structure")
            
            return ChangeLogFile.from_dict(data)
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # Handle corrupted log file data
            sanitized_data = await self.error_handler.handle_data_validation_error(
                f"log_file_{file_path.name}", e, malformed_data=None
            )
            
            if sanitized_data:
                self.logger.warning(f"Using sanitized data for corrupted log file {file_path}")
                return ChangeLogFile.from_dict(sanitized_data)
            else:
                self.logger.error(f"Could not recover corrupted log file {file_path}")
                raise
        except Exception as e:
            self.logger.error(f"Error loading log file {file_path}: {e}", exc_info=True)
            raise
    
    async def _save_log_file(self, file_path: Path, log_file: ChangeLogFile) -> None:
        """Save a log file to disk with error handling."""
        async def save_operation():
            # Update metadata
            log_file.metadata.last_updated = datetime.now()
            
            # Write to temporary file first, then rename for atomic operation
            temp_path = file_path.with_suffix('.tmp')
            
            try:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(log_file.to_dict(), f, indent=2, ensure_ascii=False)
                
                # Atomic rename
                temp_path.replace(file_path)
                
                # Update file size in metadata
                log_file.metadata.log_file_size = file_path.stat().st_size
                
                return True
                
            except Exception as e:
                # Clean up temp file if it exists
                if temp_path.exists():
                    temp_path.unlink()
                raise e
        
        # Use error handler for file save operations
        try:
            success = await self.error_handler.handle_storage_error(
                f"save_log_file_{file_path.name}",
                Exception("Log file save operation"),  # Placeholder
                context={'file_path': str(file_path)},
                retry_func=save_operation
            )
            
            if not success:
                raise Exception(f"Failed to save log file {file_path} after retries")
                
        except Exception as e:
            self.logger.error(f"Error saving log file {file_path}: {e}", exc_info=True)
            raise
    
    async def _update_storage_health_metrics(self, character_id: Optional[int], 
                                           operation: str, metrics: Dict[str, Any]) -> None:
        """Update storage health metrics for monitoring."""
        try:
            health_file = self.config.storage_dir / "storage_health.json"
            
            # Load existing health data
            health_data = {}
            if health_file.exists():
                try:
                    with open(health_file, 'r', encoding='utf-8') as f:
                        health_data = json.load(f)
                except Exception as e:
                    self.logger.warning(f"Error loading health data: {e}")
            
            # Initialize structure if needed
            if 'operations' not in health_data:
                health_data['operations'] = []
            if 'summary' not in health_data:
                health_data['summary'] = {
                    'total_operations': 0,
                    'last_updated': None,
                    'error_count': 0,
                    'rotation_count': 0,
                    'cleanup_count': 0
                }
            
            # Add new operation record
            operation_record = {
                'timestamp': datetime.now().isoformat(),
                'character_id': character_id,
                'operation': operation,
                'metrics': metrics
            }
            health_data['operations'].append(operation_record)
            
            # Update summary
            health_data['summary']['total_operations'] += 1
            health_data['summary']['last_updated'] = datetime.now().isoformat()
            
            if 'error' in operation:
                health_data['summary']['error_count'] += 1
            elif operation == 'rotation':
                health_data['summary']['rotation_count'] += 1
            elif operation == 'cleanup':
                health_data['summary']['cleanup_count'] += 1
            
            # Keep only last 1000 operations to prevent unbounded growth
            if len(health_data['operations']) > 1000:
                health_data['operations'] = health_data['operations'][-1000:]
            
            # Save health data
            with open(health_file, 'w', encoding='utf-8') as f:
                json.dump(health_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.warning(f"Error updating storage health metrics: {e}")
    
    async def get_storage_health(self) -> Dict[str, Any]:
        """Get storage health information for monitoring."""
        try:
            health_file = self.config.storage_dir / "storage_health.json"
            
            # Load health data
            health_data = {}
            if health_file.exists():
                try:
                    with open(health_file, 'r', encoding='utf-8') as f:
                        health_data = json.load(f)
                except Exception as e:
                    self.logger.warning(f"Error loading health data: {e}")
            
            # Calculate current storage statistics
            storage_stats = await self._calculate_storage_statistics()
            
            # Combine health data with current stats
            return {
                'storage_directory': str(self.config.storage_dir),
                'health_summary': health_data.get('summary', {}),
                'recent_operations': health_data.get('operations', [])[-10:],  # Last 10 operations
                'storage_statistics': storage_stats,
                'configuration': {
                    'rotation_size_mb': self.config.log_rotation_size_mb,
                    'retention_days': self.config.log_retention_days,
                    'backup_old_logs': self.config.backup_old_logs
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting storage health: {e}", exc_info=True)
            return {
                'error': str(e),
                'storage_directory': str(self.config.storage_dir)
            }
    
    async def _calculate_storage_statistics(self) -> Dict[str, Any]:
        """Calculate current storage statistics."""
        try:
            stats = {
                'total_characters': 0,
                'total_log_files': 0,
                'total_rotated_files': 0,
                'total_archived_files': 0,
                'total_size_mb': 0,
                'largest_file_mb': 0,
                'oldest_entry': None,
                'newest_entry': None,
                'characters_needing_rotation': [],
                'characters_with_errors': []
            }
            
            # Process current log files - handle all naming patterns
            for log_file_path in self.config.storage_dir.glob("*_changes.json"):
                # Skip if it's not actually a character log file
                character_id = self._extract_character_id_from_path(log_file_path)
                if not character_id:
                    continue
                    
                try:
                    file_size = log_file_path.stat().st_size
                    file_size_mb = file_size / (1024 * 1024)
                    
                    stats['total_log_files'] += 1
                    stats['total_size_mb'] += file_size_mb
                    stats['largest_file_mb'] = max(stats['largest_file_mb'], file_size_mb)
                    
                    # Check if rotation is needed
                    if file_size_mb >= self.config.log_rotation_size_mb:
                        stats['characters_needing_rotation'].append(character_id)
                    
                    # Try to get entry timestamps
                    try:
                        log_file = await self._load_log_file(log_file_path)
                        if log_file.entries:
                            file_oldest = min(log_file.entries, key=lambda x: x.timestamp).timestamp
                            file_newest = max(log_file.entries, key=lambda x: x.timestamp).timestamp
                            
                            if stats['oldest_entry'] is None or file_oldest < stats['oldest_entry']:
                                stats['oldest_entry'] = file_oldest
                            if stats['newest_entry'] is None or file_newest > stats['newest_entry']:
                                stats['newest_entry'] = file_newest
                    except Exception as e:
                        stats['characters_with_errors'].append({
                            'character_id': character_id,
                            'error': str(e)
                        })
                    
                except Exception as e:
                    self.logger.warning(f"Error processing log file {log_file_path}: {e}")
                    continue
            
            # Count character directories
            character_dirs = list(self.config.storage_dir.glob("character_*"))
            stats['total_characters'] = len([d for d in character_dirs if d.is_dir()])
            
            # Count rotated files
            for character_dir in character_dirs:
                if character_dir.is_dir():
                    rotated_dir = character_dir / "rotated"
                    if rotated_dir.exists():
                        rotated_files = list(rotated_dir.glob("changes_*.json"))
                        stats['total_rotated_files'] += len(rotated_files)
                        
                        # Add rotated file sizes
                        for rotated_file in rotated_files:
                            try:
                                file_size_mb = rotated_file.stat().st_size / (1024 * 1024)
                                stats['total_size_mb'] += file_size_mb
                            except Exception:
                                continue
            
            # Count archived files
            archive_dir = self.config.storage_dir / "archive"
            if archive_dir.exists():
                archived_files = list(archive_dir.rglob("*.json"))
                stats['total_archived_files'] = len(archived_files)
                
                # Add archived file sizes
                for archived_file in archived_files:
                    try:
                        file_size_mb = archived_file.stat().st_size / (1024 * 1024)
                        stats['total_size_mb'] += file_size_mb
                    except Exception:
                        continue
            
            # Format timestamps
            if stats['oldest_entry']:
                stats['oldest_entry'] = stats['oldest_entry'].isoformat()
            if stats['newest_entry']:
                stats['newest_entry'] = stats['newest_entry'].isoformat()
            
            # Round size
            stats['total_size_mb'] = round(stats['total_size_mb'], 2)
            stats['largest_file_mb'] = round(stats['largest_file_mb'], 2)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error calculating storage statistics: {e}", exc_info=True)
            return {'error': str(e)}
    
    def _extract_character_id_from_path(self, file_path: Path) -> Optional[int]:
        """Extract character ID from log file path (supports all naming patterns)."""
        try:
            filename = file_path.name
            
            if filename.endswith("_changes.json"):
                # Remove "_changes.json" suffix
                base_name = filename[:-12]
                
                if filename.startswith("character_"):
                    # Old patterns: character_{id}_changes.json or character_{id}_{name}_changes.json
                    # Remove "character_" prefix
                    middle_part = base_name[10:]
                    
                    # Split by underscore and take the first part as ID
                    id_part = middle_part.split('_')[0]
                    return int(id_part)
                else:
                    # New pattern: {name}_{id}_changes.json
                    # Split by underscore and take the last part as ID
                    parts = base_name.split('_')
                    if len(parts) >= 2:
                        # Last part should be the character ID - try from right to left
                        for i in range(len(parts)):
                            try:
                                id_part = parts[-(i+1)]
                                # Check if this part is numeric (character ID)
                                return int(id_part)
                            except ValueError:
                                continue
        except Exception:
            pass
        return None
    
    async def perform_maintenance(self, character_id: Optional[int] = None) -> Dict[str, Any]:
        """Perform comprehensive maintenance operations."""
        try:
            maintenance_results = {
                'timestamp': datetime.now().isoformat(),
                'character_id': character_id,
                'operations': {},
                'summary': {
                    'total_operations': 0,
                    'successful_operations': 0,
                    'failed_operations': 0
                }
            }
            
            # Operation 1: Check and rotate logs if needed
            if character_id:
                rotation_result = await self.rotate_logs(character_id)
                maintenance_results['operations']['rotation'] = {
                    'success': rotation_result,
                    'character_id': character_id
                }
            else:
                # Rotate logs for all characters that need it
                rotation_results = {}
                storage_stats = await self._calculate_storage_statistics()
                
                for char_id in storage_stats.get('characters_needing_rotation', []):
                    rotation_result = await self.rotate_logs(char_id)
                    rotation_results[char_id] = rotation_result
                
                maintenance_results['operations']['rotation'] = rotation_results
            
            # Operation 2: Clean up old logs
            cleanup_count = await self.cleanup_old_logs()
            maintenance_results['operations']['cleanup'] = {
                'success': cleanup_count >= 0,
                'files_cleaned': cleanup_count
            }
            
            # Operation 3: Validate log file integrity
            validation_results = await self._validate_log_files(character_id)
            maintenance_results['operations']['validation'] = validation_results
            
            # Operation 4: Optimize storage structure
            optimization_results = await self._optimize_storage_structure(character_id)
            maintenance_results['operations']['optimization'] = optimization_results
            
            # Calculate summary
            for operation, result in maintenance_results['operations'].items():
                maintenance_results['summary']['total_operations'] += 1
                
                if isinstance(result, dict):
                    if result.get('success', False):
                        maintenance_results['summary']['successful_operations'] += 1
                    else:
                        maintenance_results['summary']['failed_operations'] += 1
                elif isinstance(result, bool) and result:
                    maintenance_results['summary']['successful_operations'] += 1
                else:
                    maintenance_results['summary']['failed_operations'] += 1
            
            self.logger.info(f"Maintenance completed for character {character_id or 'all'}: "
                           f"{maintenance_results['summary']['successful_operations']} successful, "
                           f"{maintenance_results['summary']['failed_operations']} failed")
            
            return maintenance_results
            
        except Exception as e:
            self.logger.error(f"Error performing maintenance: {e}", exc_info=True)
            return {
                'timestamp': datetime.now().isoformat(),
                'character_id': character_id,
                'error': str(e)
            }
    
    async def _validate_log_files(self, character_id: Optional[int] = None) -> Dict[str, Any]:
        """Validate log file integrity."""
        try:
            validation_results = {
                'files_checked': 0,
                'files_valid': 0,
                'files_corrupted': 0,
                'files_repaired': 0,
                'errors': []
            }
            
            # Get files to validate
            if character_id:
                log_files = self._get_character_log_files(character_id)
            else:
                log_files = []
                # Get all character log files regardless of naming pattern
                for log_file in self.config.storage_dir.glob("*_changes.json"):
                    if self._extract_character_id_from_path(log_file):
                        log_files.append(log_file)
                
                # Also check rotated files
                for character_dir in self.config.storage_dir.glob("character_*"):
                    if character_dir.is_dir():
                        rotated_dir = character_dir / "rotated"
                        if rotated_dir.exists():
                            log_files.extend(rotated_dir.glob("changes_*.json"))
            
            for log_file_path in log_files:
                validation_results['files_checked'] += 1
                
                try:
                    # Try to load the log file
                    log_file = await self._load_log_file(log_file_path)
                    
                    # Validate structure
                    if not log_file.entries:
                        validation_results['files_valid'] += 1
                        continue
                    
                    # Check for data consistency
                    expected_count = len(log_file.entries)
                    actual_count = log_file.metadata.total_entries
                    
                    if expected_count != actual_count:
                        # Repair metadata
                        log_file.metadata.total_entries = expected_count
                        await self._save_log_file(log_file_path, log_file)
                        validation_results['files_repaired'] += 1
                        self.logger.info(f"Repaired entry count for {log_file_path}: {actual_count} -> {expected_count}")
                    
                    validation_results['files_valid'] += 1
                    
                except Exception as e:
                    validation_results['files_corrupted'] += 1
                    validation_results['errors'].append({
                        'file': str(log_file_path),
                        'error': str(e)
                    })
                    self.logger.warning(f"Corrupted log file {log_file_path}: {e}")
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating log files: {e}", exc_info=True)
            return {'error': str(e)}
    
    async def _optimize_storage_structure(self, character_id: Optional[int] = None) -> Dict[str, Any]:
        """Optimize storage structure for better performance."""
        try:
            optimization_results = {
                'directories_created': 0,
                'directories_cleaned': 0,
                'files_moved': 0,
                'space_saved_mb': 0
            }
            
            # Create proper directory structure for characters
            if character_id:
                character_dirs = [self.config.storage_dir / f"character_{character_id}"]
            else:
                # Find all characters with log files
                character_ids = set()
                for log_file in self.config.storage_dir.glob("*_changes.json"):
                    char_id = self._extract_character_id_from_path(log_file)
                    if char_id:
                        character_ids.add(char_id)
                
                character_dirs = [self.config.storage_dir / f"character_{char_id}" 
                                for char_id in character_ids]
            
            for character_dir in character_dirs:
                char_id = self._extract_character_id_from_path(character_dir / "dummy")
                if not char_id:
                    continue
                
                # Ensure character directory exists
                if not character_dir.exists():
                    character_dir.mkdir(parents=True, exist_ok=True)
                    optimization_results['directories_created'] += 1
                
                # Ensure rotated subdirectory exists if needed
                current_logs = self._get_character_log_files(char_id)
                
                if current_logs:
                    current_log = current_logs[0]  # Should be only one current file
                    file_size_mb = current_log.stat().st_size / (1024 * 1024)
                    if file_size_mb >= self.config.log_rotation_size_mb * 0.8:  # 80% threshold
                        # Create rotated directory based on current log filename
                        log_filename = current_log.stem  # Remove .json extension
                        if "_changes" in log_filename:
                            base_name = log_filename.replace("_changes", "")
                            rotated_dir = self.config.storage_dir / base_name / "rotated"
                        else:
                            rotated_dir = character_dir / "rotated"
                        
                        if not rotated_dir.exists():
                            rotated_dir.mkdir(parents=True, exist_ok=True)
                            optimization_results['directories_created'] += 1
            
            # Clean up empty directories
            for character_dir in self.config.storage_dir.glob("character_*"):
                if character_dir.is_dir():
                    rotated_dir = character_dir / "rotated"
                    if rotated_dir.exists() and not any(rotated_dir.iterdir()):
                        rotated_dir.rmdir()
                        optimization_results['directories_cleaned'] += 1
                    
                    if not any(character_dir.iterdir()):
                        character_dir.rmdir()
                        optimization_results['directories_cleaned'] += 1
            
            return optimization_results
            
        except Exception as e:
            self.logger.error(f"Error optimizing storage structure: {e}", exc_info=True)
            return {'error': str(e)}