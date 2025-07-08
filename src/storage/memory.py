"""
In-memory storage implementation for testing and development.

This provides a fast, ephemeral storage solution suitable for:
- Unit testing
- Development/debugging
- Temporary operations
- Performance benchmarking

Note: All data is lost when the application stops.
"""

import json
import copy
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from collections import defaultdict
import logging
from dataclasses import asdict

from src.interfaces.storage import (
    ICharacterStorage, CharacterSnapshot, CharacterDiff,
    QueryFilter, StorageBackend
)
from src.models.character import Character


logger = logging.getLogger(__name__)


class MemoryStorage(ICharacterStorage):
    """
    In-memory storage implementation.
    
    Data Structure:
    - _characters: Dict[character_id, Dict[version, CharacterSnapshot]]
    - _latest_versions: Dict[character_id, int]
    - _deleted_characters: Set[character_id] (for soft deletes)
    - _metadata: Dict[character_id, Dict[str, Any]]
    
    All operations are synchronous but wrapped in async for interface compliance.
    """
    
    def __init__(self):
        # Main storage: character_id -> version -> CharacterSnapshot
        self._characters: Dict[int, Dict[int, CharacterSnapshot]] = defaultdict(dict)
        
        # Track latest version for each character
        self._latest_versions: Dict[int, int] = {}
        
        # Soft delete tracking
        self._deleted_characters: set = set()
        
        # Additional metadata per character
        self._metadata: Dict[int, Dict[str, Any]] = defaultdict(dict)
        
        # Statistics
        self._stats = {
            "total_characters": 0,
            "total_versions": 0,
            "total_queries": 0,
            "created_at": datetime.utcnow()
        }
        
        logger.info("Initialized MemoryStorage")
    
    async def save_character(
        self,
        character: Character,
        user_id: Optional[str] = None,
        change_summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CharacterSnapshot:
        """Save a character, creating a new version snapshot."""
        character_id = character.id
        
        if character_id is None:
            raise ValueError("Character must have an ID")
        
        # Determine next version number
        if character_id in self._latest_versions:
            next_version = self._latest_versions[character_id] + 1
        else:
            next_version = 1
            self._stats["total_characters"] += 1
        
        # Remove from deleted set if it was soft-deleted
        self._deleted_characters.discard(character_id)
        
        # Create snapshot
        snapshot = CharacterSnapshot(
            character_id=character_id,
            version=next_version,
            character_data=copy.deepcopy(character),
            timestamp=datetime.utcnow(),
            change_summary=change_summary,
            metadata=metadata or {}
        )
        
        # Store snapshot
        self._characters[character_id][next_version] = snapshot
        self._latest_versions[character_id] = next_version
        
        # Store metadata
        if user_id:
            self._metadata[character_id]["user_id"] = user_id
        if metadata:
            self._metadata[character_id].update(metadata)
        
        self._stats["total_versions"] += 1
        
        logger.debug(f"Saved character {character_id} version {next_version}")
        return copy.deepcopy(snapshot)
    
    async def get_character(
        self,
        character_id: int,
        version: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> Optional[CharacterSnapshot]:
        """Retrieve a character snapshot."""
        
        # Check if character exists
        if character_id not in self._characters:
            return None
        
        # Check if soft deleted (unless requesting specific version)
        if character_id in self._deleted_characters and version is None:
            return None
        
        # Check user access (basic implementation)
        if user_id and self._metadata[character_id].get("user_id") != user_id:
            return None
        
        # Get specific version or latest
        if version is None:
            version = self._latest_versions.get(character_id)
            if version is None:
                return None
        
        snapshot = self._characters[character_id].get(version)
        if snapshot is None:
            return None
        
        logger.debug(f"Retrieved character {character_id} version {version}")
        return copy.deepcopy(snapshot)
    
    async def get_character_history(
        self,
        character_id: int,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[CharacterSnapshot]:
        """Get version history for a character."""
        
        # Check if character exists
        if character_id not in self._characters:
            return []
        
        # Check user access
        if user_id and self._metadata[character_id].get("user_id") != user_id:
            return []
        
        # Get all versions, sorted by version number (newest first)
        versions = sorted(self._characters[character_id].keys(), reverse=True)
        
        # Apply offset and limit
        if offset:
            versions = versions[offset:]
        if limit:
            versions = versions[:limit]
        
        # Return snapshots
        snapshots = [
            copy.deepcopy(self._characters[character_id][version])
            for version in versions
        ]
        
        logger.debug(f"Retrieved {len(snapshots)} versions for character {character_id}")
        return snapshots
    
    async def get_character_diff(
        self,
        character_id: int,
        from_version: int,
        to_version: int,
        user_id: Optional[str] = None
    ) -> Optional[CharacterDiff]:
        """Get differences between two character versions."""
        
        # Check if character exists
        if character_id not in self._characters:
            return None
        
        # Check user access
        if user_id and self._metadata[character_id].get("user_id") != user_id:
            return None
        
        # Get both versions
        from_snapshot = self._characters[character_id].get(from_version)
        to_snapshot = self._characters[character_id].get(to_version)
        
        if not from_snapshot or not to_snapshot:
            return None
        
        # Calculate differences (basic implementation)
        changes = self._calculate_character_diff(
            from_snapshot.character_data,
            to_snapshot.character_data
        )
        
        diff = CharacterDiff(
            character_id=character_id,
            from_version=from_version,
            to_version=to_version,
            changes=changes,
            timestamp=to_snapshot.timestamp
        )
        
        logger.debug(f"Generated diff for character {character_id} v{from_version} -> v{to_version}")
        return diff
    
    def _calculate_character_diff(self, from_char: Character, to_char: Character) -> Dict[str, Tuple[Any, Any]]:
        """Calculate differences between two character objects."""
        changes = {}
        
        # Convert to dicts for comparison
        try:
            from_dict = from_char.model_dump() if hasattr(from_char, 'model_dump') else asdict(from_char)
            to_dict = to_char.model_dump() if hasattr(to_char, 'model_dump') else asdict(to_char)
        except:
            # Fallback to basic attribute comparison
            from_dict = vars(from_char) if hasattr(from_char, '__dict__') else {}
            to_dict = vars(to_char) if hasattr(to_char, '__dict__') else {}
        
        # Find changed fields
        all_keys = set(from_dict.keys()) | set(to_dict.keys())
        
        for key in all_keys:
            from_val = from_dict.get(key)
            to_val = to_dict.get(key)
            
            if from_val != to_val:
                changes[key] = (from_val, to_val)
        
        return changes
    
    async def query_characters(
        self,
        filter: QueryFilter
    ) -> List[CharacterSnapshot]:
        """Query characters based on filter criteria."""
        self._stats["total_queries"] += 1
        
        results = []
        
        # Get character IDs to check
        character_ids = filter.character_ids or list(self._characters.keys())
        
        for character_id in character_ids:
            # Skip if doesn't exist
            if character_id not in self._characters:
                continue
            
            # Skip if soft deleted (unless explicitly including deleted)
            if character_id in self._deleted_characters and not filter.include_deleted:
                continue
            
            # Get latest version for filtering
            latest_version = self._latest_versions.get(character_id)
            if latest_version is None:
                continue
            
            snapshot = self._characters[character_id][latest_version]
            character = snapshot.character_data
            
            # Apply filters
            if not self._matches_filter(character, snapshot, filter):
                continue
            
            # Check user access
            if filter.user_id and self._metadata[character_id].get("user_id") != filter.user_id:
                continue
            
            results.append(copy.deepcopy(snapshot))
        
        # Sort by timestamp (newest first)
        results.sort(key=lambda s: s.timestamp, reverse=True)
        
        # Apply offset and limit
        if filter.offset:
            results = results[filter.offset:]
        if filter.limit:
            results = results[:filter.limit]
        
        logger.debug(f"Query returned {len(results)} characters")
        return results
    
    def _matches_filter(self, character: Character, snapshot: CharacterSnapshot, filter: QueryFilter) -> bool:
        """Check if character matches query filter."""
        
        # Character name filter
        if filter.character_names:
            char_name = getattr(character, 'name', None)
            if not char_name or char_name not in filter.character_names:
                return False
        
        # Class name filter
        if filter.class_names:
            char_classes = getattr(character, 'classes', [])
            class_names = [cls.name for cls in char_classes] if char_classes else []
            if not any(name in filter.class_names for name in class_names):
                return False
        
        # Level filters
        if filter.min_level is not None or filter.max_level is not None:
            char_level = getattr(character, 'level', 0)
            if filter.min_level is not None and char_level < filter.min_level:
                return False
            if filter.max_level is not None and char_level > filter.max_level:
                return False
        
        # Timestamp filters
        if filter.modified_after and snapshot.timestamp < filter.modified_after:
            return False
        if filter.modified_before and snapshot.timestamp > filter.modified_before:
            return False
        
        # Campaign filter
        if filter.campaign_id:
            char_campaign = getattr(character, 'campaign_id', None)
            if char_campaign != filter.campaign_id:
                return False
        
        return True
    
    async def delete_character(
        self,
        character_id: int,
        user_id: Optional[str] = None,
        hard_delete: bool = False
    ) -> bool:
        """Delete a character."""
        
        # Check if character exists
        if character_id not in self._characters:
            return False
        
        # Check user access
        if user_id and self._metadata[character_id].get("user_id") != user_id:
            return False
        
        if hard_delete:
            # Permanently remove all data
            del self._characters[character_id]
            self._latest_versions.pop(character_id, None)
            self._deleted_characters.discard(character_id)
            self._metadata.pop(character_id, None)
            self._stats["total_characters"] -= 1
            logger.info(f"Hard deleted character {character_id}")
        else:
            # Soft delete - mark as deleted
            self._deleted_characters.add(character_id)
            logger.info(f"Soft deleted character {character_id}")
        
        return True
    
    async def archive_old_versions(
        self,
        before_date: datetime,
        keep_every_nth: int = 1
    ) -> int:
        """Archive old character versions based on retention policy."""
        archived_count = 0
        
        for character_id, versions_dict in self._characters.items():
            versions_to_archive = []
            
            # Get versions before the date, sorted
            old_versions = [
                v for v, snapshot in versions_dict.items()
                if snapshot.timestamp < before_date
            ]
            old_versions.sort()
            
            # Keep every nth version
            for i, version in enumerate(old_versions):
                if i % keep_every_nth != 0:
                    versions_to_archive.append(version)
            
            # Remove archived versions
            for version in versions_to_archive:
                del self._characters[character_id][version]
                archived_count += 1
        
        logger.info(f"Archived {archived_count} old versions")
        return archived_count
    
    async def export_character(
        self,
        character_id: int,
        format: str = "json",
        include_history: bool = False,
        user_id: Optional[str] = None
    ) -> bytes:
        """Export character data in specified format."""
        
        # Check if character exists
        if character_id not in self._characters:
            raise ValueError(f"Character {character_id} not found")
        
        # Check user access
        if user_id and self._metadata[character_id].get("user_id") != user_id:
            raise PermissionError("Access denied")
        
        if format.lower() != "json":
            raise ValueError(f"Unsupported export format: {format}")
        
        export_data = {}
        
        if include_history:
            # Export all versions
            versions = {}
            for version, snapshot in self._characters[character_id].items():
                versions[str(version)] = {
                    "character_data": snapshot.character_data.model_dump() if hasattr(snapshot.character_data, 'model_dump') else vars(snapshot.character_data),
                    "timestamp": snapshot.timestamp.isoformat(),
                    "change_summary": snapshot.change_summary,
                    "metadata": snapshot.metadata
                }
            export_data["versions"] = versions
        else:
            # Export latest version only
            latest_version = self._latest_versions[character_id]
            snapshot = self._characters[character_id][latest_version]
            export_data = {
                "character_data": snapshot.character_data.model_dump() if hasattr(snapshot.character_data, 'model_dump') else vars(snapshot.character_data),
                "timestamp": snapshot.timestamp.isoformat(),
                "change_summary": snapshot.change_summary,
                "metadata": snapshot.metadata
            }
        
        # Add metadata
        export_data["character_metadata"] = self._metadata[character_id]
        
        return json.dumps(export_data, indent=2, default=str).encode('utf-8')
    
    async def import_character(
        self,
        data: bytes,
        format: str = "json",
        user_id: Optional[str] = None
    ) -> CharacterSnapshot:
        """Import character data from external format."""
        
        if format.lower() != "json":
            raise ValueError(f"Unsupported import format: {format}")
        
        try:
            import_data = json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid JSON data: {e}")
        
        # Extract character data
        if "character_data" in import_data:
            # Single character import
            char_data = import_data["character_data"]
            change_summary = import_data.get("change_summary", "Imported character")
            metadata = import_data.get("metadata", {})
        else:
            raise ValueError("No character data found in import")
        
        # Create Character object
        try:
            # This is a simplified approach - in reality you'd need proper deserialization
            character = Character(**char_data) if hasattr(Character, '__init__') else Character()
            for key, value in char_data.items():
                if hasattr(character, key):
                    setattr(character, key, value)
        except Exception as e:
            raise ValueError(f"Failed to create character from import data: {e}")
        
        # Save the character
        snapshot = await self.save_character(
            character=character,
            user_id=user_id,
            change_summary=change_summary,
            metadata=metadata
        )
        
        logger.info(f"Imported character {character.id}")
        return snapshot
    
    # Additional utility methods for testing/debugging
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return {
            **self._stats,
            "deleted_characters": len(self._deleted_characters),
            "memory_usage_estimate": self._estimate_memory_usage()
        }
    
    def _estimate_memory_usage(self) -> str:
        """Rough estimate of memory usage."""
        import sys
        
        total_size = 0
        total_size += sys.getsizeof(self._characters)
        total_size += sys.getsizeof(self._latest_versions)
        total_size += sys.getsizeof(self._deleted_characters)  
        total_size += sys.getsizeof(self._metadata)
        
        # Rough estimate of nested data
        total_size += len(self._characters) * 1000  # Rough estimate per character
        
        if total_size < 1024:
            return f"{total_size} bytes"
        elif total_size < 1024 * 1024:
            return f"{total_size / 1024:.1f} KB"
        else:
            return f"{total_size / (1024 * 1024):.1f} MB"
    
    def clear_all_data(self):
        """Clear all stored data (for testing)."""
        self._characters.clear()
        self._latest_versions.clear()
        self._deleted_characters.clear()
        self._metadata.clear()
        self._stats = {
            "total_characters": 0,
            "total_versions": 0,
            "total_queries": 0,
            "created_at": datetime.utcnow()
        }
        logger.info("Cleared all memory storage data")
    
    def __str__(self) -> str:
        return f"MemoryStorage(characters={len(self._characters)}, versions={self._stats['total_versions']})"
    
    def __repr__(self) -> str:
        return self.__str__()