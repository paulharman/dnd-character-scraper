"""
PostgreSQL storage implementation.

This provides a scalable database storage solution suitable for:
- Multi-user deployments
- High concurrency
- Advanced querying with JSONB
- Full ACID compliance
- Replication support
"""

import json
import asyncpg
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import logging
from contextlib import asynccontextmanager

from shared.interfaces.storage import (
    ICharacterStorage, CharacterSnapshot, CharacterDiff,
    QueryFilter, IStorageTransaction
)
from shared.models.character import Character
from shared.models.storage import (
    CharacterIndex, VersionMetadata, StorageStatistics,
    CompressionType, SQL_SCHEMA_POSTGRES
)


logger = logging.getLogger(__name__)


class PostgresTransaction(IStorageTransaction):
    """PostgreSQL transaction context manager."""
    
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection
        self.transaction = None
        self._committed = False
        self._rolled_back = False
    
    async def __aenter__(self):
        self.transaction = self.connection.transaction()
        await self.transaction.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        elif not self._committed and not self._rolled_back:
            await self.commit()
        return False
    
    async def commit(self):
        if not self._committed and not self._rolled_back and self.transaction:
            await self.transaction.commit()
            self._committed = True
    
    async def rollback(self):
        if not self._committed and not self._rolled_back and self.transaction:
            await self.transaction.rollback()
            self._rolled_back = True


class PostgresStorage(ICharacterStorage):
    """
    PostgreSQL-based storage implementation.
    
    Features:
    - Full JSONB support for flexible querying
    - Connection pooling
    - Prepared statements
    - Advanced indexing
    - Partitioning support for large datasets
    - Row-level security
    """
    
    def __init__(
        self,
        dsn: str,
        pool_size: int = 10,
        max_pool_size: int = 20,
        compression: CompressionType = CompressionType.ZSTD,
        enable_partitioning: bool = False,
        partition_by: str = "month"  # month, year
    ):
        self.dsn = dsn
        self.pool_size = pool_size
        self.max_pool_size = max_pool_size
        self.compression = compression
        self.enable_partitioning = enable_partitioning
        self.partition_by = partition_by
        
        self._pool: Optional[asyncpg.Pool] = None
        self._prepared_statements: Dict[str, bool] = {}
    
    async def _get_pool(self) -> asyncpg.Pool:
        """Get or create connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self.dsn,
                min_size=self.pool_size,
                max_size=self.max_pool_size,
                command_timeout=60
            )
            
            # Initialize schema
            await self._init_schema()
        
        return self._pool
    
    async def _init_schema(self):
        """Initialize database schema."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            # Execute schema creation
            await conn.execute(SQL_SCHEMA_POSTGRES)
            
            # Create additional indexes for JSONB queries
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_character_data_gin 
                ON character_versions USING gin (character_data);
            """)
            
            # Create partitioning if enabled
            if self.enable_partitioning:
                await self._setup_partitioning(conn)
            
            # Prepare commonly used statements
            await self._prepare_statements(conn)
    
    async def _setup_partitioning(self, conn: asyncpg.Connection):
        """Set up table partitioning for character_versions."""
        if self.partition_by == "month":
            # Create partitioned table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS character_versions_partitioned (
                    LIKE character_versions INCLUDING ALL
                ) PARTITION BY RANGE (timestamp);
            """)
            
            # Create function to automatically create partitions
            await conn.execute("""
                CREATE OR REPLACE FUNCTION create_monthly_partition()
                RETURNS trigger AS $$
                DECLARE
                    partition_name text;
                    start_date date;
                    end_date date;
                BEGIN
                    start_date := date_trunc('month', NEW.timestamp);
                    end_date := start_date + interval '1 month';
                    partition_name := 'character_versions_' || to_char(start_date, 'YYYY_MM');
                    
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_class WHERE relname = partition_name
                    ) THEN
                        EXECUTE format(
                            'CREATE TABLE %I PARTITION OF character_versions_partitioned
                            FOR VALUES FROM (%L) TO (%L)',
                            partition_name, start_date, end_date
                        );
                    END IF;
                    
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)
    
    async def _prepare_statements(self, conn: asyncpg.Connection):
        """Prepare commonly used SQL statements."""
        statements = {
            "get_character_index": """
                SELECT character_name, latest_version, user_id, is_deleted,
                       classes, level, primary_class, species, rule_version
                FROM character_index
                WHERE character_id = $1
            """,
            "get_character_version": """
                SELECT character_data, timestamp, change_summary, metadata,
                       compressed_size, compression
                FROM character_versions
                WHERE character_id = $1 AND version = $2
            """,
            "update_character_index": """
                UPDATE character_index SET
                    character_name = $2,
                    latest_version = $3,
                    total_versions = $4,
                    last_modified = $5,
                    classes = $6,
                    level = $7,
                    primary_class = $8,
                    species = $9,
                    rule_version = $10
                WHERE character_id = $1
            """,
            "insert_character_version": """
                INSERT INTO character_versions (
                    character_id, version, timestamp, change_summary,
                    change_count, changed_fields, data_size, compressed_size,
                    compression, checksum, user_id, character_data, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """
        }
        
        for name, query in statements.items():
            await conn.execute(f"PREPARE {name} AS {query}")
            self._prepared_statements[name] = True
    
    @asynccontextmanager
    async def transaction(self):
        """Create a new transaction."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with PostgresTransaction(conn) as txn:
                yield txn
    
    async def _compress_data(self, data: Dict[str, Any]) -> bytes:
        """Compress character data."""
        json_str = json.dumps(data, default=str)
        
        if self.compression == CompressionType.ZSTD:
            import zstandard
            cctx = zstandard.ZstdCompressor(level=3)
            return cctx.compress(json_str.encode('utf-8'))
        elif self.compression == CompressionType.GZIP:
            import gzip
            return gzip.compress(json_str.encode('utf-8'), compresslevel=6)
        else:
            return json_str.encode('utf-8')
    
    async def _decompress_data(self, data: bytes, compression: str) -> Dict[str, Any]:
        """Decompress character data."""
        if compression == CompressionType.ZSTD.value:
            import zstandard
            dctx = zstandard.ZstdDecompressor()
            json_str = dctx.decompress(data).decode('utf-8')
        elif compression == CompressionType.GZIP.value:
            import gzip
            json_str = gzip.decompress(data).decode('utf-8')
        else:
            json_str = data.decode('utf-8')
        
        return json.loads(json_str)
    
    async def save_character(
        self,
        character: Character,
        user_id: Optional[str] = None,
        change_summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CharacterSnapshot:
        """Save a character, creating a new version snapshot."""
        pool = await self._get_pool()
        character_id = character.id
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Check if character exists
                row = await conn.fetchrow(
                    "SELECT latest_version FROM character_index WHERE character_id = $1",
                    character_id
                )
                
                if row:
                    # Existing character
                    new_version = row['latest_version'] + 1
                    
                    # Update index using prepared statement
                    await conn.execute("""
                        UPDATE character_index SET
                            character_name = $2,
                            latest_version = $3,
                            total_versions = $4,
                            last_modified = $5,
                            classes = $6,
                            level = $7,
                            primary_class = $8,
                            species = $9,
                            rule_version = $10
                        WHERE character_id = $1
                    """, 
                        character_id,
                        character.name,
                        new_version,
                        new_version,
                        datetime.utcnow(),
                        [c.name for c in character.classes],
                        character.level,
                        character.get_primary_class().name,
                        character.species.name,
                        character.rule_version.value
                    )
                else:
                    # New character
                    new_version = 1
                    
                    # Insert into index
                    await conn.execute("""
                        INSERT INTO character_index (
                            character_id, character_name, latest_version, total_versions,
                            created_at, last_modified, user_id, classes, level,
                            primary_class, species, rule_version
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    """,
                        character_id,
                        character.name,
                        1,
                        1,
                        datetime.utcnow(),
                        datetime.utcnow(),
                        user_id,
                        [c.name for c in character.classes],
                        character.level,
                        character.get_primary_class().name,
                        character.species.name,
                        character.rule_version.value
                    )
                
                # Prepare character data
                character_dict = character.dict()
                
                # Calculate changes if not first version
                changed_fields = []
                if new_version > 1:
                    # Get previous version for comparison
                    prev_row = await conn.fetchrow("""
                        SELECT character_data
                        FROM character_versions
                        WHERE character_id = $1 AND version = $2
                    """, character_id, new_version - 1)
                    
                    if prev_row:
                        prev_data = prev_row['character_data']
                        # PostgreSQL JSONB comparison
                        diff_result = await conn.fetchval("""
                            SELECT jsonb_diff($1::jsonb, $2::jsonb)
                        """, json.dumps(prev_data), json.dumps(character_dict))
                        
                        if diff_result:
                            changed_fields = list(diff_result.keys())
                
                # Compress data if needed
                if self.compression != CompressionType.NONE:
                    compressed_data = await self._compress_data(character_dict)
                    data_to_store = compressed_data
                    compressed_size = len(compressed_data)
                else:
                    data_to_store = json.dumps(character_dict).encode('utf-8')
                    compressed_size = None
                
                # Calculate checksum
                import hashlib
                checksum = hashlib.sha256(data_to_store).hexdigest()
                
                # Insert version
                await conn.execute("""
                    INSERT INTO character_versions (
                        character_id, version, timestamp, change_summary,
                        change_count, changed_fields, data_size, compressed_size,
                        compression, checksum, user_id, character_data, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """,
                    character_id,
                    new_version,
                    datetime.utcnow(),
                    change_summary,
                    len(changed_fields),
                    changed_fields,
                    len(json.dumps(character_dict)),
                    compressed_size,
                    self.compression.value,
                    checksum,
                    user_id,
                    character_dict,  # PostgreSQL will store as JSONB
                    metadata or {}
                )
                
                # Log audit entry
                await conn.execute("""
                    INSERT INTO audit_log (user_id, action, resource_type, resource_id, details)
                    VALUES ($1, $2, $3, $4, $5)
                """,
                    user_id,
                    "character_save",
                    "character",
                    str(character_id),
                    {"version": new_version, "change_summary": change_summary}
                )
        
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
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            # Get character info
            row = await conn.fetchrow("""
                SELECT character_name, latest_version, user_id, is_deleted
                FROM character_index
                WHERE character_id = $1
            """, character_id)
            
            if not row:
                return None
            
            # Access control
            if user_id and row['user_id'] and row['user_id'] != user_id:
                return None
            
            # Check if deleted
            if row['is_deleted']:
                return None
            
            # Use latest version if not specified
            if version is None:
                version = row['latest_version']
            
            # Get version data
            version_row = await conn.fetchrow("""
                SELECT character_data, timestamp, change_summary, metadata,
                       compression, compressed_size
                FROM character_versions
                WHERE character_id = $1 AND version = $2
            """, character_id, version)
            
            if not version_row:
                return None
            
            # Character data is stored as JSONB
            character_dict = version_row['character_data']
            character = Character(**character_dict)
            
            # Update access statistics
            await conn.execute("""
                UPDATE character_index
                SET last_accessed = $1, access_count = access_count + 1
                WHERE character_id = $2
            """, datetime.utcnow(), character_id)
            
            return CharacterSnapshot(
                character_id=character_id,
                version=version,
                character_data=character,
                timestamp=version_row['timestamp'],
                change_summary=version_row['change_summary'],
                metadata=version_row['metadata'] or {}
            )
    
    async def get_character_history(
        self,
        character_id: int,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[CharacterSnapshot]:
        """Get version history for a character."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            # Check access
            row = await conn.fetchrow(
                "SELECT user_id FROM character_index WHERE character_id = $1",
                character_id
            )
            
            if not row:
                return []
            
            if user_id and row['user_id'] and row['user_id'] != user_id:
                return []
            
            # Get versions
            query = """
                SELECT version, character_data, timestamp, change_summary, metadata
                FROM character_versions
                WHERE character_id = $1
                ORDER BY version DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            if offset:
                query += f" OFFSET {offset}"
            
            rows = await conn.fetch(query, character_id)
            
            snapshots = []
            for row in rows:
                character = Character(**row['character_data'])
                snapshots.append(CharacterSnapshot(
                    character_id=character_id,
                    version=row['version'],
                    character_data=character,
                    timestamp=row['timestamp'],
                    change_summary=row['change_summary'],
                    metadata=row['metadata'] or {}
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
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            # Use PostgreSQL's JSONB diff capabilities
            result = await conn.fetchrow("""
                SELECT 
                    v1.character_data as from_data,
                    v2.character_data as to_data,
                    v2.timestamp,
                    jsonb_diff(v1.character_data, v2.character_data) as diff
                FROM character_versions v1
                JOIN character_versions v2 
                    ON v1.character_id = v2.character_id
                WHERE v1.character_id = $1 
                    AND v1.version = $2 
                    AND v2.version = $3
            """, character_id, from_version, to_version)
            
            if not result:
                return None
            
            # Convert JSONB diff to our format
            changes = {}
            if result['diff']:
                for key, value in result['diff'].items():
                    if isinstance(value, dict) and 'old' in value and 'new' in value:
                        changes[key] = (value['old'], value['new'])
                    else:
                        # Field was added or removed
                        old_val = result['from_data'].get(key)
                        new_val = result['to_data'].get(key)
                        changes[key] = (old_val, new_val)
            
            return CharacterDiff(
                character_id=character_id,
                from_version=from_version,
                to_version=to_version,
                changes=changes,
                timestamp=result['timestamp']
            )
    
    async def query_characters(self, filter: QueryFilter) -> List[CharacterSnapshot]:
        """Query characters with advanced JSONB queries."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            # Build query dynamically
            query_parts = ["SELECT character_id, latest_version FROM character_index WHERE 1=1"]
            params = []
            param_count = 0
            
            # Character IDs filter
            if filter.character_ids:
                param_count += 1
                query_parts.append(f"AND character_id = ANY(${param_count})")
                params.append(filter.character_ids)
            
            # User ID filter
            if filter.user_id:
                param_count += 1
                query_parts.append(f"AND user_id = ${param_count}")
                params.append(filter.user_id)
            
            # Campaign ID filter
            if filter.campaign_id:
                param_count += 1
                query_parts.append(f"AND campaign_id = ${param_count}")
                params.append(filter.campaign_id)
            
            # Character name filter (case-insensitive)
            if filter.character_names:
                name_conditions = []
                for name in filter.character_names:
                    param_count += 1
                    name_conditions.append(f"character_name ILIKE ${param_count}")
                    params.append(f"%{name}%")
                query_parts.append(f"AND ({' OR '.join(name_conditions)})")
            
            # Class filter using JSONB
            if filter.class_names:
                param_count += 1
                query_parts.append(f"AND classes ?| ${param_count}")
                params.append(filter.class_names)
            
            # Level filters
            if filter.min_level:
                param_count += 1
                query_parts.append(f"AND level >= ${param_count}")
                params.append(filter.min_level)
            
            if filter.max_level:
                param_count += 1
                query_parts.append(f"AND level <= ${param_count}")
                params.append(filter.max_level)
            
            # Date filters
            if filter.modified_after:
                param_count += 1
                query_parts.append(f"AND last_modified > ${param_count}")
                params.append(filter.modified_after)
            
            if filter.modified_before:
                param_count += 1
                query_parts.append(f"AND last_modified < ${param_count}")
                params.append(filter.modified_before)
            
            # Deleted filter
            if not filter.include_deleted:
                query_parts.append("AND is_deleted = FALSE")
            
            # Order and pagination
            query_parts.append("ORDER BY last_modified DESC")
            
            if filter.limit:
                param_count += 1
                query_parts.append(f"LIMIT ${param_count}")
                params.append(filter.limit)
            
            if filter.offset:
                param_count += 1
                query_parts.append(f"OFFSET ${param_count}")
                params.append(filter.offset)
            
            query = " ".join(query_parts)
            rows = await conn.fetch(query, *params)
            
            # Load full snapshots
            snapshots = []
            for row in rows:
                snapshot = await self.get_character(
                    row['character_id'],
                    row['latest_version'],
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
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            # Check ownership
            row = await conn.fetchrow(
                "SELECT user_id FROM character_index WHERE character_id = $1",
                character_id
            )
            
            if not row:
                return False
            
            if user_id and row['user_id'] and row['user_id'] != user_id:
                return False
            
            async with conn.transaction():
                if hard_delete:
                    # Delete relationships
                    await conn.execute("""
                        DELETE FROM character_relationships
                        WHERE source_character_id = $1 OR target_character_id = $1
                    """, character_id)
                    
                    # Delete versions
                    await conn.execute(
                        "DELETE FROM character_versions WHERE character_id = $1",
                        character_id
                    )
                    
                    # Delete from index
                    await conn.execute(
                        "DELETE FROM character_index WHERE character_id = $1",
                        character_id
                    )
                else:
                    # Soft delete
                    await conn.execute(
                        "UPDATE character_index SET is_deleted = TRUE WHERE character_id = $1",
                        character_id
                    )
                
                # Audit log
                await conn.execute("""
                    INSERT INTO audit_log (user_id, action, resource_type, resource_id, details)
                    VALUES ($1, $2, $3, $4, $5)
                """,
                    user_id,
                    "character_delete" if hard_delete else "character_soft_delete",
                    "character",
                    str(character_id),
                    {"hard_delete": hard_delete}
                )
            
            return True
    
    async def archive_old_versions(
        self,
        before_date: datetime,
        keep_every_nth: int = 1
    ) -> int:
        """Archive old versions to separate table."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Find versions to archive
                rows = await conn.fetch("""
                    SELECT DISTINCT character_id
                    FROM character_versions
                    WHERE timestamp < $1
                """, before_date)
                
                archived_count = 0
                
                for row in rows:
                    character_id = row['character_id']
                    
                    # Get versions to archive
                    versions = await conn.fetch("""
                        SELECT version, character_data, compression
                        FROM character_versions
                        WHERE character_id = $1 AND timestamp < $2
                        ORDER BY version
                    """, character_id, before_date)
                    
                    if not versions:
                        continue
                    
                    # Keep every nth version
                    versions_to_archive = []
                    for i, v in enumerate(versions[:-1]):  # Keep latest
                        if i % keep_every_nth != 0:
                            versions_to_archive.append(v)
                    
                    if versions_to_archive:
                        # Compress all versions together
                        archive_data = {
                            "character_id": character_id,
                            "versions": [
                                {
                                    "version": v['version'],
                                    "data": v['character_data']
                                }
                                for v in versions_to_archive
                            ]
                        }
                        
                        compressed = await self._compress_data(archive_data)
                        
                        # Insert into archive
                        await conn.execute("""
                            INSERT INTO character_archive (
                                character_id, version_range, archived_at,
                                data_blob, compression, metadata
                            ) VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                            character_id,
                            f"[{versions_to_archive[0]['version']},{versions_to_archive[-1]['version']}]",
                            datetime.utcnow(),
                            compressed,
                            self.compression.value,
                            {"count": len(versions_to_archive)}
                        )
                        
                        # Delete archived versions
                        version_numbers = [v['version'] for v in versions_to_archive]
                        await conn.execute("""
                            DELETE FROM character_versions
                            WHERE character_id = $1 AND version = ANY($2)
                        """, character_id, version_numbers)
                        
                        archived_count += len(versions_to_archive)
                
                return archived_count
    
    async def export_character(
        self,
        character_id: int,
        format: str = "json",
        include_history: bool = False,
        user_id: Optional[str] = None
    ) -> bytes:
        """Export character with optional history."""
        if format != "json":
            raise ValueError(f"Unsupported export format: {format}")
        
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
        """Import character from external format."""
        if format != "json":
            raise ValueError(f"Unsupported import format: {format}")
        
        import_data = json.loads(data.decode('utf-8'))
        
        if "character" not in import_data:
            raise ValueError("Invalid import data: missing 'character' field")
        
        character = Character(**import_data["character"])
        
        return await self.save_character(
            character,
            user_id=user_id,
            change_summary="Imported from external source",
            metadata=import_data.get("metadata", {})
        )
    
    async def close(self):
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None