"""
File-based JSON storage implementation.

This provides a simple, portable storage solution suitable for:
- Single-user applications
- Small deployments
- Development/testing
- Backup/export functionality
"""

import json
import os
import gzip
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import hashlib
import asyncio
from asyncio import Lock
import aiofiles
import aiofiles.os

from src.interfaces.storage import (
    ICharacterStorage, CharacterSnapshot, CharacterDiff,
    QueryFilter, StorageBackend
)
from src.models.character import Character
from src.models.storage import (
    CharacterIndex, VersionMetadata, StorageMetadata,
    CompressionType, StorageStatistics
)


class FileJsonStorage(ICharacterStorage):
    """
    File-based JSON storage implementation.
    
    Directory structure:
    storage_root/
        index.json              # Character index
        metadata.json          # Storage metadata
        characters/
            {character_id}/
                latest.json    # Latest version for quick access
                versions/
                    v{version}.json         # Full snapshots
                    v{version}.json.gz      # Compressed snapshots
                    v{version}.delta.json   # Delta files (optional)
                metadata.json           # Version metadata
        archive/               # Archived old versions
        temp/                  # Temporary files
    """
    
    def __init__(
        self,
        storage_root: str,
        compression: CompressionType = CompressionType.GZIP,
        enable_delta_storage: bool = True,
        delta_threshold_kb: int = 100
    ):
        self.storage_root = Path(storage_root)
        self.compression = compression
        self.enable_delta_storage = enable_delta_storage
        self.delta_threshold_kb = delta_threshold_kb
        
        # Create directory structure
        self._init_directories()
        
        # Locks for concurrent access
        self._locks: Dict[int, Lock] = {}
        self._index_lock = Lock()
        
        # Cache for frequently accessed data
        self._index_cache: Optional[Dict[int, CharacterIndex]] = None
        self._metadata_cache: Optional[StorageMetadata] = None
    
    def _init_directories(self):
        """Initialize storage directory structure."""
        directories = [
            self.storage_root,
            self.storage_root / "characters",
            self.storage_root / "archive",
            self.storage_root / "temp"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _get_character_dir(self, character_id: int) -> Path:
        """Get character directory path."""
        return self.storage_root / "characters" / str(character_id)
    
    def _get_version_path(
        self,
        character_id: int,
        version: int,
        compressed: bool = False,
        is_delta: bool = False
    ) -> Path:
        """Get path for a specific version file."""
        char_dir = self._get_character_dir(character_id)
        versions_dir = char_dir / "versions"
        
        filename = f"v{version}"
        if is_delta:
            filename += ".delta"
        filename += ".json"
        if compressed:
            filename += ".gz"
            
        return versions_dir / filename
    
    async def _get_character_lock(self, character_id: int) -> Lock:
        """Get or create lock for character."""
        if character_id not in self._locks:
            self._locks[character_id] = Lock()
        return self._locks[character_id]
    
    async def _load_index(self) -> Dict[int, CharacterIndex]:
        """Load character index from disk."""
        if self._index_cache is not None:
            return self._index_cache
            
        index_path = self.storage_root / "index.json"
        
        if not index_path.exists():
            self._index_cache = {}
            return self._index_cache
        
        async with aiofiles.open(index_path, 'r') as f:
            data = await f.read()
            index_data = json.loads(data)
            
        self._index_cache = {
            int(char_id): CharacterIndex(**entry)
            for char_id, entry in index_data.items()
        }
        
        return self._index_cache
    
    async def _save_index(self, index: Dict[int, CharacterIndex]):
        """Save character index to disk."""
        async with self._index_lock:
            index_path = self.storage_root / "index.json"
            temp_path = self.storage_root / "temp" / "index.json.tmp"
            
            # Serialize index
            index_data = {
                str(char_id): entry.dict()
                for char_id, entry in index.items()
            }
            
            # Write to temp file first
            async with aiofiles.open(temp_path, 'w') as f:
                await f.write(json.dumps(index_data, indent=2, default=str))
            
            # Atomic rename
            await aiofiles.os.rename(temp_path, index_path)
            
            # Update cache
            self._index_cache = index
    
    async def _load_character_data(
        self,
        path: Path,
        compressed: bool = False
    ) -> Dict[str, Any]:
        """Load character data from file."""
        if compressed:
            # Read compressed data
            async with aiofiles.open(path, 'rb') as f:
                compressed_data = await f.read()
            
            # Decompress in thread pool
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None,
                lambda: gzip.decompress(compressed_data).decode('utf-8')
            )
            
            return json.loads(data)
        else:
            async with aiofiles.open(path, 'r') as f:
                data = await f.read()
                return json.loads(data)
    
    async def _save_character_data(
        self,
        path: Path,
        data: Dict[str, Any],
        compress: bool = False
    ):
        """Save character data to file."""
        json_str = json.dumps(data, indent=2, default=str)
        
        if compress:
            # Compress in thread pool
            loop = asyncio.get_event_loop()
            compressed_data = await loop.run_in_executor(
                None,
                lambda: gzip.compress(json_str.encode('utf-8'))
            )
            
            async with aiofiles.open(path, 'wb') as f:
                await f.write(compressed_data)
        else:
            async with aiofiles.open(path, 'w') as f:
                await f.write(json_str)
    
    async def _calculate_diff(
        self,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any]
    ) -> Dict[str, Tuple[Any, Any]]:
        """Calculate differences between two character versions."""
        changes = {}
        
        # Helper function to recursively compare dictionaries
        def compare_dicts(old: Dict, new: Dict, path: str = ""):
            for key in set(old.keys()) | set(new.keys()):
                current_path = f"{path}.{key}" if path else key
                
                if key not in old:
                    changes[current_path] = (None, new[key])
                elif key not in new:
                    changes[current_path] = (old[key], None)
                elif old[key] != new[key]:
                    if isinstance(old[key], dict) and isinstance(new[key], dict):
                        compare_dicts(old[key], new[key], current_path)
                    else:
                        changes[current_path] = (old[key], new[key])
        
        compare_dicts(old_data, new_data)
        return changes
    
    async def save_character(
        self,
        character: Character,
        user_id: Optional[str] = None,
        change_summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CharacterSnapshot:
        """Save a character, creating a new version snapshot."""
        character_id = character.id
        
        # Get character lock
        lock = await self._get_character_lock(character_id)
        async with lock:
            # Load index
            index = await self._load_index()
            
            # Determine version number
            if character_id in index:
                index_entry = index[character_id]
                new_version = index_entry.latest_version + 1
            else:
                # New character
                new_version = 1
                index_entry = CharacterIndex(
                    character_id=character_id,
                    character_name=character.name,
                    latest_version=1,
                    total_versions=1,
                    created_at=datetime.utcnow(),
                    last_modified=datetime.utcnow(),
                    classes=[c.name for c in character.classes],
                    level=character.level,
                    primary_class=character.get_primary_class().name,
                    species=character.species.name,
                    rule_version=character.rule_version.value,
                    user_id=user_id
                )
            
            # Create character directory structure
            char_dir = self._get_character_dir(character_id)
            versions_dir = char_dir / "versions"
            versions_dir.mkdir(parents=True, exist_ok=True)
            
            # Serialize character data
            character_data = character.dict()
            
            # Calculate changes if not first version
            changes = {}
            if new_version > 1:
                # Load previous version for diff
                prev_path = self._get_version_path(
                    character_id,
                    index_entry.latest_version,
                    compressed=self.compression != CompressionType.NONE
                )
                
                if prev_path.exists():
                    prev_data = await self._load_character_data(
                        prev_path,
                        compressed=self.compression != CompressionType.NONE
                    )
                    changes = await self._calculate_diff(prev_data, character_data)
            
            # Save version file
            version_path = self._get_version_path(
                character_id,
                new_version,
                compressed=self.compression != CompressionType.NONE
            )
            
            await self._save_character_data(
                version_path,
                character_data,
                compress=self.compression != CompressionType.NONE
            )
            
            # Save latest.json for quick access
            latest_path = char_dir / "latest.json"
            await self._save_character_data(latest_path, character_data)
            
            # Update version metadata
            version_meta = VersionMetadata(
                character_id=character_id,
                version=new_version,
                timestamp=datetime.utcnow(),
                change_summary=change_summary,
                change_count=len(changes),
                changed_fields=list(changes.keys()),
                data_size=len(json.dumps(character_data)),
                compression=self.compression,
                user_id=user_id
            )
            
            # Save version metadata
            meta_path = char_dir / "metadata.json"
            if meta_path.exists():
                async with aiofiles.open(meta_path, 'r') as f:
                    meta_data = json.loads(await f.read())
            else:
                meta_data = {"versions": {}}
            
            meta_data["versions"][str(new_version)] = version_meta.dict()
            
            async with aiofiles.open(meta_path, 'w') as f:
                await f.write(json.dumps(meta_data, indent=2, default=str))
            
            # Update index
            index_entry.latest_version = new_version
            index_entry.total_versions = new_version
            index_entry.last_modified = datetime.utcnow()
            index_entry.character_name = character.name
            index_entry.classes = [c.name for c in character.classes]
            index_entry.level = character.level
            index_entry.primary_class = character.get_primary_class().name
            index_entry.species = character.species.name
            
            index[character_id] = index_entry
            await self._save_index(index)
            
            # Create and return snapshot
            return CharacterSnapshot(
                character_id=character_id,
                version=new_version,
                character_data=character,
                timestamp=datetime.utcnow(),
                change_summary=change_summary,
                metadata=metadata or {}
            )
    
    async def get_character(
        self,
        character_id: int,
        version: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> Optional[CharacterSnapshot]:
        """Retrieve a character snapshot."""
        # Load index
        index = await self._load_index()
        
        if character_id not in index:
            return None
        
        index_entry = index[character_id]
        
        # Access control check
        if user_id and index_entry.user_id and index_entry.user_id != user_id:
            return None
        
        # Update access statistics
        index_entry.last_accessed = datetime.utcnow()
        index_entry.access_count += 1
        await self._save_index(index)
        
        # Determine version to load
        if version is None:
            version = index_entry.latest_version
        
        # Load character data
        if version == index_entry.latest_version:
            # Use latest.json for current version
            latest_path = self._get_character_dir(character_id) / "latest.json"
            if latest_path.exists():
                data = await self._load_character_data(latest_path)
            else:
                # Fall back to version file
                version_path = self._get_version_path(
                    character_id,
                    version,
                    compressed=self.compression != CompressionType.NONE
                )
                data = await self._load_character_data(
                    version_path,
                    compressed=self.compression != CompressionType.NONE
                )
        else:
            # Load specific version
            version_path = self._get_version_path(
                character_id,
                version,
                compressed=self.compression != CompressionType.NONE
            )
            
            if not version_path.exists():
                return None
            
            data = await self._load_character_data(
                version_path,
                compressed=self.compression != CompressionType.NONE
            )
        
        # Load version metadata
        meta_path = self._get_character_dir(character_id) / "metadata.json"
        change_summary = None
        
        if meta_path.exists():
            async with aiofiles.open(meta_path, 'r') as f:
                meta_data = json.loads(await f.read())
                if str(version) in meta_data.get("versions", {}):
                    version_meta = meta_data["versions"][str(version)]
                    change_summary = version_meta.get("change_summary")
        
        # Create character instance
        character = Character(**data)
        
        # Create and return snapshot
        return CharacterSnapshot(
            character_id=character_id,
            version=version,
            character_data=character,
            timestamp=index_entry.last_modified,
            change_summary=change_summary
        )
    
    async def get_character_history(
        self,
        character_id: int,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[CharacterSnapshot]:
        """Get version history for a character."""
        # Load index
        index = await self._load_index()
        
        if character_id not in index:
            return []
        
        index_entry = index[character_id]
        
        # Access control check
        if user_id and index_entry.user_id and index_entry.user_id != user_id:
            return []
        
        # Load metadata
        meta_path = self._get_character_dir(character_id) / "metadata.json"
        if not meta_path.exists():
            return []
        
        async with aiofiles.open(meta_path, 'r') as f:
            meta_data = json.loads(await f.read())
        
        versions = meta_data.get("versions", {})
        
        # Sort versions by number (newest first)
        sorted_versions = sorted(versions.keys(), key=int, reverse=True)
        
        # Apply pagination
        if offset:
            sorted_versions = sorted_versions[offset:]
        if limit:
            sorted_versions = sorted_versions[:limit]
        
        # Load snapshots
        snapshots = []
        for version_str in sorted_versions:
            version = int(version_str)
            snapshot = await self.get_character(character_id, version, user_id)
            if snapshot:
                snapshots.append(snapshot)
        
        return snapshots
    
    async def get_character_diff(
        self,
        character_id: int,
        from_version: int,
        to_version: int,
        user_id: Optional[str] = None
    ) -> Optional[CharacterDiff]:
        """Get differences between two character versions."""
        # Load both versions
        from_snapshot = await self.get_character(character_id, from_version, user_id)
        to_snapshot = await self.get_character(character_id, to_version, user_id)
        
        if not from_snapshot or not to_snapshot:
            return None
        
        # Calculate differences
        from_data = from_snapshot.character_data.dict()
        to_data = to_snapshot.character_data.dict()
        
        changes = await self._calculate_diff(from_data, to_data)
        
        return CharacterDiff(
            character_id=character_id,
            from_version=from_version,
            to_version=to_version,
            changes=changes,
            timestamp=to_snapshot.timestamp
        )
    
    async def query_characters(self, filter: QueryFilter) -> List[CharacterSnapshot]:
        """Query characters based on filter criteria."""
        # Load index
        index = await self._load_index()
        
        results = []
        
        for char_id, entry in index.items():
            # Apply filters
            if filter.character_ids and char_id not in filter.character_ids:
                continue
            
            if filter.user_id and entry.user_id != filter.user_id:
                continue
            
            if filter.campaign_id and entry.campaign_id != filter.campaign_id:
                continue
            
            if filter.character_names:
                if not any(name.lower() in entry.character_name.lower() 
                          for name in filter.character_names):
                    continue
            
            if filter.class_names:
                if not any(cls in entry.classes for cls in filter.class_names):
                    continue
            
            if filter.min_level and entry.level < filter.min_level:
                continue
            
            if filter.max_level and entry.level > filter.max_level:
                continue
            
            if filter.modified_after and entry.last_modified < filter.modified_after:
                continue
            
            if filter.modified_before and entry.last_modified > filter.modified_before:
                continue
            
            if not filter.include_deleted and entry.is_deleted:
                continue
            
            # Load character snapshot
            snapshot = await self.get_character(char_id, user_id=filter.user_id)
            if snapshot:
                results.append(snapshot)
        
        # Sort by last modified (newest first)
        results.sort(key=lambda s: s.timestamp, reverse=True)
        
        # Apply pagination
        if filter.offset:
            results = results[filter.offset:]
        if filter.limit:
            results = results[:filter.limit]
        
        return results
    
    async def delete_character(
        self,
        character_id: int,
        user_id: Optional[str] = None,
        hard_delete: bool = False
    ) -> bool:
        """Delete a character."""
        # Load index
        index = await self._load_index()
        
        if character_id not in index:
            return False
        
        index_entry = index[character_id]
        
        # Access control check
        if user_id and index_entry.user_id and index_entry.user_id != user_id:
            return False
        
        if hard_delete:
            # Remove character directory
            char_dir = self._get_character_dir(character_id)
            if char_dir.exists():
                shutil.rmtree(char_dir)
            
            # Remove from index
            del index[character_id]
        else:
            # Soft delete - mark as deleted in index
            index_entry.is_deleted = True
        
        await self._save_index(index)
        return True
    
    async def archive_old_versions(
        self,
        before_date: datetime,
        keep_every_nth: int = 1
    ) -> int:
        """Archive old character versions based on retention policy."""
        # Load index
        index = await self._load_index()
        
        archived_count = 0
        archive_dir = self.storage_root / "archive"
        
        for char_id, entry in index.items():
            # Load version metadata
            meta_path = self._get_character_dir(char_id) / "metadata.json"
            if not meta_path.exists():
                continue
            
            async with aiofiles.open(meta_path, 'r') as f:
                meta_data = json.loads(await f.read())
            
            versions = meta_data.get("versions", {})
            versions_to_archive = []
            
            # Determine which versions to archive
            sorted_versions = sorted(versions.keys(), key=int)
            
            for i, version_str in enumerate(sorted_versions[:-1]):  # Keep latest
                version_meta = versions[version_str]
                timestamp = datetime.fromisoformat(version_meta["timestamp"])
                
                if timestamp < before_date:
                    # Check if we should keep this version
                    if i % keep_every_nth != 0:
                        versions_to_archive.append(int(version_str))
            
            # Archive selected versions
            if versions_to_archive:
                # Create archive directory for character
                char_archive_dir = archive_dir / str(char_id)
                char_archive_dir.mkdir(parents=True, exist_ok=True)
                
                for version in versions_to_archive:
                    # Move version file to archive
                    version_path = self._get_version_path(
                        char_id,
                        version,
                        compressed=self.compression != CompressionType.NONE
                    )
                    
                    if version_path.exists():
                        archive_path = char_archive_dir / version_path.name
                        await aiofiles.os.rename(version_path, archive_path)
                        archived_count += 1
                        
                        # Remove from metadata
                        del versions[str(version)]
                
                # Update metadata
                meta_data["versions"] = versions
                async with aiofiles.open(meta_path, 'w') as f:
                    await f.write(json.dumps(meta_data, indent=2, default=str))
        
        return archived_count
    
    async def export_character(
        self,
        character_id: int,
        format: str = "json",
        include_history: bool = False,
        user_id: Optional[str] = None
    ) -> bytes:
        """Export character data in specified format."""
        if format != "json":
            raise ValueError(f"Unsupported export format: {format}")
        
        # Get latest character data
        snapshot = await self.get_character(character_id, user_id=user_id)
        if not snapshot:
            raise ValueError(f"Character {character_id} not found")
        
        export_data = {
            "character": snapshot.character_data.dict(),
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "version": snapshot.version,
                "character_id": character_id
            }
        }
        
        if include_history:
            # Get all versions
            history = await self.get_character_history(character_id, user_id=user_id)
            export_data["history"] = [
                {
                    "version": snap.version,
                    "timestamp": snap.timestamp.isoformat(),
                    "change_summary": snap.change_summary,
                    "data": snap.character_data.dict()
                }
                for snap in history
            ]
        
        return json.dumps(export_data, indent=2, default=str).encode('utf-8')
    
    async def import_character(
        self,
        data: bytes,
        format: str = "json",
        user_id: Optional[str] = None
    ) -> CharacterSnapshot:
        """Import character data from external format."""
        if format != "json":
            raise ValueError(f"Unsupported import format: {format}")
        
        import_data = json.loads(data.decode('utf-8'))
        
        if "character" not in import_data:
            raise ValueError("Invalid import data: missing 'character' field")
        
        # Create character instance
        character = Character(**import_data["character"])
        
        # Save as new character (will get new ID if ID exists)
        return await self.save_character(
            character,
            user_id=user_id,
            change_summary="Imported from external source",
            metadata=import_data.get("metadata", {})
        )
    
    async def get_statistics(self) -> StorageStatistics:
        """Get storage statistics."""
        index = await self._load_index()
        
        stats = StorageStatistics()
        stats.total_characters = len(index)
        
        # Calculate statistics from index
        for entry in index.values():
            stats.total_versions += entry.total_versions
            
            # Class distribution
            for class_name in entry.classes:
                stats.characters_by_class[class_name] = \
                    stats.characters_by_class.get(class_name, 0) + 1
            
            # Level distribution
            stats.characters_by_level[entry.level] = \
                stats.characters_by_level.get(entry.level, 0) + 1
            
            # Rule version distribution
            if entry.rule_version:
                stats.characters_by_rule_version[entry.rule_version] = \
                    stats.characters_by_rule_version.get(entry.rule_version, 0) + 1
            
            # Time-based metrics
            if entry.created_at.date() == datetime.utcnow().date():
                stats.characters_created_today += 1
            
            if entry.last_modified.date() == datetime.utcnow().date():
                stats.characters_modified_today += 1
        
        # Calculate averages
        if stats.total_characters > 0:
            stats.average_versions_per_character = \
                stats.total_versions / stats.total_characters
        
        return stats