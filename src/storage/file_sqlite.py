"""
SQLite storage implementation.

This provides a file-based database storage solution suitable for:
- Medium-sized deployments
- Better query performance than JSON
- ACID compliance
- Concurrent access with proper locking
"""

import json
import sqlite3
import aiosqlite
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

from src.interfaces.storage import (
    ICharacterStorage, CharacterSnapshot, CharacterDiff,
    QueryFilter, IStorageTransaction
)
from src.models.character import Character
from src.models.storage import (
    CharacterIndex, VersionMetadata, StorageStatistics,
    CompressionType, SQL_SCHEMA_SQLITE
)


class SQLiteTransaction(IStorageTransaction):
    """SQLite transaction context manager."""
    
    def __init__(self, connection: aiosqlite.Connection):
        self.connection = connection
        self._committed = False
        self._rolled_back = False
    
    async def __aenter__(self):
        await self.connection.execute("BEGIN")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        elif not self._committed and not self._rolled_back:
            await self.commit()
        return False
    
    async def commit(self):
        if not self._committed and not self._rolled_back:
            await self.connection.commit()
            self._committed = True
    
    async def rollback(self):
        if not self._committed and not self._rolled_back:
            await self.connection.rollback()
            self._rolled_back = True


class FileSQLiteStorage(ICharacterStorage):
    """
    SQLite-based storage implementation.
    
    Features:
    - Single file database
    - ACID compliance
    - Better query performance than JSON
    - Built-in indexing
    - Transaction support
    - Concurrent read access
    """
    
    def __init__(
        self,
        db_path: str,
        compression: CompressionType = CompressionType.GZIP,
        enable_wal: bool = True,
        cache_size_mb: int = 50
    ):
        self.db_path = Path(db_path)
        self.compression = compression
        self.enable_wal = enable_wal
        self.cache_size_mb = cache_size_mb
        
        # Connection pool
        self._connection: Optional[aiosqlite.Connection] = None
        self._connection_lock = asyncio.Lock()
        
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def _get_connection(self) -> aiosqlite.Connection:
        """Get or create database connection."""
        if self._connection is None:
            async with self._connection_lock:
                if self._connection is None:
                    self._connection = await aiosqlite.connect(
                        self.db_path,
                        isolation_level=None  # Autocommit mode
                    )
                    
                    # Configure SQLite for better performance
                    if self.enable_wal:
                        await self._connection.execute("PRAGMA journal_mode=WAL")
                    
                    await self._connection.execute(
                        f"PRAGMA cache_size=-{self.cache_size_mb * 1024}"
                    )
                    await self._connection.execute("PRAGMA synchronous=NORMAL")
                    await self._connection.execute("PRAGMA temp_store=MEMORY")
                    
                    # Initialize schema
                    await self._init_schema()
        
        return self._connection
    
    async def _init_schema(self):
        """Initialize database schema."""
        conn = await self._get_connection()
        
        # Execute schema creation
        for statement in SQL_SCHEMA_SQLITE.split(';'):
            statement = statement.strip()
            if statement:
                await conn.execute(statement)
        
        await conn.commit()
    
    @asynccontextmanager
    async def transaction(self):
        """Create a new transaction."""
        conn = await self._get_connection()
        async with SQLiteTransaction(conn) as txn:
            yield txn
    
    async def _compress_data(self, data: str) -> bytes:
        """Compress JSON data."""
        if self.compression == CompressionType.GZIP:
            import gzip
            return gzip.compress(data.encode('utf-8'))
        elif self.compression == CompressionType.ZSTD:
            import zstandard
            cctx = zstandard.ZstdCompressor()
            return cctx.compress(data.encode('utf-8'))
        else:
            return data.encode('utf-8')
    
    async def _decompress_data(self, data: bytes) -> str:
        """Decompress JSON data."""
        if self.compression == CompressionType.GZIP:
            import gzip
            return gzip.decompress(data).decode('utf-8')
        elif self.compression == CompressionType.ZSTD:
            import zstandard
            dctx = zstandard.ZstdDecompressor()
            return dctx.decompress(data).decode('utf-8')
        else:
            return data.decode('utf-8')
    
    async def save_character(
        self,
        character: Character,
        user_id: Optional[str] = None,
        change_summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CharacterSnapshot:
        """Save a character, creating a new version snapshot."""
        conn = await self._get_connection()
        character_id = character.id
        
        async with self.transaction() as txn:
            # Check if character exists
            cursor = await conn.execute(
                "SELECT latest_version, total_versions FROM character_index WHERE character_id = ?",
                (character_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                # Existing character
                latest_version, total_versions = row
                new_version = latest_version + 1
                
                # Update index
                await conn.execute("""
                    UPDATE character_index SET
                        character_name = ?,
                        latest_version = ?,
                        total_versions = ?,
                        last_modified = ?,
                        classes = ?,
                        level = ?,
                        primary_class = ?,
                        species = ?,
                        rule_version = ?
                    WHERE character_id = ?
                """, (
                    character.name,
                    new_version,
                    new_version,
                    datetime.utcnow().isoformat(),
                    json.dumps([c.name for c in character.classes]),
                    character.level,
                    character.get_primary_class().name,
                    character.species.name,
                    character.rule_version.value,
                    character_id
                ))
            else:
                # New character
                new_version = 1
                
                # Insert into index
                await conn.execute("""
                    INSERT INTO character_index (
                        character_id, character_name, latest_version, total_versions,
                        created_at, last_modified, user_id, classes, level,
                        primary_class, species, rule_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    character_id,
                    character.name,
                    1,
                    1,
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                    user_id,
                    json.dumps([c.name for c in character.classes]),
                    character.level,
                    character.get_primary_class().name,
                    character.species.name,
                    character.rule_version.value
                ))
            
            # Serialize and compress character data
            character_json = json.dumps(character.dict(), default=str)
            compressed_data = await self._compress_data(character_json)
            
            # Calculate changes if not first version
            changed_fields = []
            if new_version > 1:
                # Get previous version
                cursor = await conn.execute("""
                    SELECT character_data FROM character_versions
                    WHERE character_id = ? AND version = ?
                """, (character_id, latest_version))
                
                row = await cursor.fetchone()
                if row:
                    prev_data = json.loads(await self._decompress_data(row[0]))
                    # Simple field comparison (could be enhanced)
                    changed_fields = self._get_changed_fields(prev_data, character.dict())
            
            # Insert version
            await conn.execute("""
                INSERT INTO character_versions (
                    character_id, version, timestamp, change_summary,
                    change_count, changed_fields, data_size, compressed_size,
                    compression, user_id, character_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                character_id,
                new_version,
                datetime.utcnow().isoformat(),
                change_summary,
                len(changed_fields),
                json.dumps(changed_fields),
                len(character_json),
                len(compressed_data),
                self.compression.value,
                user_id,
                compressed_data
            ))
            
            await txn.commit()
        
        # Create and return snapshot
        return CharacterSnapshot(
            character_id=character_id,
            version=new_version,
            character_data=character,
            timestamp=datetime.utcnow(),
            change_summary=change_summary,
            metadata=metadata or {}
        )
    
    def _get_changed_fields(self, old_data: Dict, new_data: Dict) -> List[str]:
        """Get list of changed fields between two data dictionaries."""
        changed = []
        
        def compare_dicts(old: Dict, new: Dict, path: str = ""):
            for key in set(old.keys()) | set(new.keys()):
                current_path = f"{path}.{key}" if path else key
                
                if key not in old or key not in new:
                    changed.append(current_path)
                elif old[key] != new[key]:
                    if isinstance(old[key], dict) and isinstance(new[key], dict):
                        compare_dicts(old[key], new[key], current_path)
                    else:
                        changed.append(current_path)
        
        compare_dicts(old_data, new_data)
        return changed
    
    async def get_character(
        self,
        character_id: int,
        version: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> Optional[CharacterSnapshot]:
        """Retrieve a character snapshot."""
        conn = await self._get_connection()
        
        # Get character info from index
        cursor = await conn.execute("""
            SELECT character_name, latest_version, user_id, is_deleted
            FROM character_index
            WHERE character_id = ?
        """, (character_id,))
        
        row = await cursor.fetchone()
        if not row:
            return None
        
        char_name, latest_version, owner_id, is_deleted = row
        
        # Access control
        if user_id and owner_id and owner_id != user_id:
            return None
        
        # Don't return deleted characters unless specifically requested
        if is_deleted:
            return None
        
        # Use latest version if not specified
        if version is None:
            version = latest_version
        
        # Get version data
        cursor = await conn.execute("""
            SELECT character_data, timestamp, change_summary, metadata
            FROM character_versions
            WHERE character_id = ? AND version = ?
        """, (character_id, version))
        
        row = await cursor.fetchone()
        if not row:
            return None
        
        compressed_data, timestamp, change_summary, metadata_json = row
        
        # Decompress and deserialize
        character_json = await self._decompress_data(compressed_data)
        character_data = json.loads(character_json)
        character = Character(**character_data)
        
        # Update access statistics
        await conn.execute("""
            UPDATE character_index
            SET last_accessed = ?, access_count = access_count + 1
            WHERE character_id = ?
        """, (datetime.utcnow().isoformat(), character_id))
        
        # Parse metadata
        metadata = json.loads(metadata_json) if metadata_json else {}
        
        return CharacterSnapshot(
            character_id=character_id,
            version=version,
            character_data=character,
            timestamp=datetime.fromisoformat(timestamp),
            change_summary=change_summary,
            metadata=metadata
        )
    
    async def get_character_history(
        self,
        character_id: int,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[CharacterSnapshot]:
        """Get version history for a character."""
        conn = await self._get_connection()
        
        # Check access
        cursor = await conn.execute(
            "SELECT user_id FROM character_index WHERE character_id = ?",
            (character_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            return []
        
        owner_id = row[0]
        if user_id and owner_id and owner_id != user_id:
            return []
        
        # Build query
        query = """
            SELECT version, character_data, timestamp, change_summary, metadata
            FROM character_versions
            WHERE character_id = ?
            ORDER BY version DESC
        """
        
        params = [character_id]
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        if offset:
            query += " OFFSET ?"
            params.append(offset)
        
        cursor = await conn.execute(query, params)
        
        snapshots = []
        async for row in cursor:
            version, compressed_data, timestamp, change_summary, metadata_json = row
            
            # Decompress and deserialize
            character_json = await self._decompress_data(compressed_data)
            character_data = json.loads(character_json)
            character = Character(**character_data)
            
            metadata = json.loads(metadata_json) if metadata_json else {}
            
            snapshots.append(CharacterSnapshot(
                character_id=character_id,
                version=version,
                character_data=character,
                timestamp=datetime.fromisoformat(timestamp),
                change_summary=change_summary,
                metadata=metadata
            ))
        
        return snapshots
    
    async def get_character_diff(
        self,
        character_id: int,
        from_version: int,
        to_version: int,
        user_id: Optional[str] = None
    ) -> Optional[CharacterDiff]:
        """Get differences between two character versions."""
        # Get both versions
        from_snapshot = await self.get_character(character_id, from_version, user_id)
        to_snapshot = await self.get_character(character_id, to_version, user_id)
        
        if not from_snapshot or not to_snapshot:
            return None
        
        # Calculate differences
        from_data = from_snapshot.character_data.dict()
        to_data = to_snapshot.character_data.dict()
        
        changes = {}
        
        def compare_values(old_val, new_val, path: str):
            if old_val != new_val:
                changes[path] = (old_val, new_val)
        
        def compare_dicts(old: Dict, new: Dict, path: str = ""):
            for key in set(old.keys()) | set(new.keys()):
                current_path = f"{path}.{key}" if path else key
                
                if key not in old:
                    changes[current_path] = (None, new[key])
                elif key not in new:
                    changes[current_path] = (old[key], None)
                elif isinstance(old[key], dict) and isinstance(new[key], dict):
                    compare_dicts(old[key], new[key], current_path)
                else:
                    compare_values(old[key], new[key], current_path)
        
        compare_dicts(from_data, to_data)
        
        return CharacterDiff(
            character_id=character_id,
            from_version=from_version,
            to_version=to_version,
            changes=changes,
            timestamp=to_snapshot.timestamp
        )
    
    async def query_characters(self, filter: QueryFilter) -> List[CharacterSnapshot]:
        """Query characters based on filter criteria."""
        conn = await self._get_connection()
        
        # Build query
        query = """
            SELECT character_id, latest_version
            FROM character_index
            WHERE 1=1
        """
        params = []
        
        # Apply filters
        if filter.character_ids:
            placeholders = ",".join("?" for _ in filter.character_ids)
            query += f" AND character_id IN ({placeholders})"
            params.extend(filter.character_ids)
        
        if filter.user_id:
            query += " AND user_id = ?"
            params.append(filter.user_id)
        
        if filter.campaign_id:
            query += " AND campaign_id = ?"
            params.append(filter.campaign_id)
        
        if filter.character_names:
            name_conditions = " OR ".join("character_name LIKE ?" for _ in filter.character_names)
            query += f" AND ({name_conditions})"
            params.extend(f"%{name}%" for name in filter.character_names)
        
        if filter.class_names:
            # JSON search in SQLite
            class_conditions = " OR ".join("classes LIKE ?" for _ in filter.class_names)
            query += f" AND ({class_conditions})"
            params.extend(f'%"{cls}"%' for cls in filter.class_names)
        
        if filter.min_level:
            query += " AND level >= ?"
            params.append(filter.min_level)
        
        if filter.max_level:
            query += " AND level <= ?"
            params.append(filter.max_level)
        
        if filter.modified_after:
            query += " AND last_modified > ?"
            params.append(filter.modified_after.isoformat())
        
        if filter.modified_before:
            query += " AND last_modified < ?"
            params.append(filter.modified_before.isoformat())
        
        if not filter.include_deleted:
            query += " AND is_deleted = 0"
        
        # Add ordering
        query += " ORDER BY last_modified DESC"
        
        # Add pagination
        if filter.limit:
            query += " LIMIT ?"
            params.append(filter.limit)
        
        if filter.offset:
            query += " OFFSET ?"
            params.append(filter.offset)
        
        cursor = await conn.execute(query, params)
        
        # Load full character snapshots
        snapshots = []
        async for row in cursor:
            character_id, latest_version = row
            snapshot = await self.get_character(
                character_id,
                latest_version,
                filter.user_id
            )
            if snapshot:
                snapshots.append(snapshot)
        
        return snapshots
    
    async def delete_character(
        self,
        character_id: int,
        user_id: Optional[str] = None,
        hard_delete: bool = False
    ) -> bool:
        """Delete a character."""
        conn = await self._get_connection()
        
        # Check ownership
        cursor = await conn.execute(
            "SELECT user_id FROM character_index WHERE character_id = ?",
            (character_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            return False
        
        owner_id = row[0]
        if user_id and owner_id and owner_id != user_id:
            return False
        
        async with self.transaction() as txn:
            if hard_delete:
                # Delete all versions
                await conn.execute(
                    "DELETE FROM character_versions WHERE character_id = ?",
                    (character_id,)
                )
                
                # Delete from index
                await conn.execute(
                    "DELETE FROM character_index WHERE character_id = ?",
                    (character_id,)
                )
            else:
                # Soft delete
                await conn.execute(
                    "UPDATE character_index SET is_deleted = 1 WHERE character_id = ?",
                    (character_id,)
                )
            
            await txn.commit()
        
        return True
    
    async def archive_old_versions(
        self,
        before_date: datetime,
        keep_every_nth: int = 1
    ) -> int:
        """Archive old character versions based on retention policy."""
        conn = await self._get_connection()
        
        # For SQLite, we'll just delete old versions
        # In a real implementation, we might move to a separate archive table
        
        deleted_count = 0
        
        # Get all characters
        cursor = await conn.execute(
            "SELECT DISTINCT character_id FROM character_versions"
        )
        character_ids = [row[0] for row in await cursor.fetchall()]
        
        async with self.transaction() as txn:
            for character_id in character_ids:
                # Get versions to potentially delete
                cursor = await conn.execute("""
                    SELECT version, timestamp
                    FROM character_versions
                    WHERE character_id = ?
                    ORDER BY version
                """, (character_id,))
                
                versions = []
                async for row in cursor:
                    version, timestamp = row
                    if datetime.fromisoformat(timestamp) < before_date:
                        versions.append(version)
                
                # Keep every nth version and the latest
                versions_to_delete = []
                for i, version in enumerate(versions[:-1]):  # Keep latest
                    if i % keep_every_nth != 0:
                        versions_to_delete.append(version)
                
                # Delete selected versions
                if versions_to_delete:
                    placeholders = ",".join("?" for _ in versions_to_delete)
                    await conn.execute(f"""
                        DELETE FROM character_versions
                        WHERE character_id = ? AND version IN ({placeholders})
                    """, [character_id] + versions_to_delete)
                    
                    deleted_count += len(versions_to_delete)
            
            await txn.commit()
        
        return deleted_count
    
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
        
        # Get latest character
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
        
        # Save as new version
        return await self.save_character(
            character,
            user_id=user_id,
            change_summary="Imported from external source",
            metadata=import_data.get("metadata", {})
        )
    
    async def close(self):
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None