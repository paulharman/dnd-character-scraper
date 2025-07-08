"""
Storage interface definitions for character data persistence.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple, Iterator
from datetime import datetime
from enum import Enum

from src.models.character import Character


class StorageBackend(Enum):
    """Available storage backend types."""
    FILE_JSON = "file_json"
    FILE_SQLITE = "file_sqlite"
    DATABASE_POSTGRES = "database_postgres"
    DATABASE_MYSQL = "database_mysql"
    CLOUD_S3 = "cloud_s3"
    CLOUD_AZURE = "cloud_azure"
    MEMORY = "memory"


class QueryFilter:
    """Query filter for searching characters."""
    
    def __init__(self):
        self.character_ids: Optional[List[int]] = None
        self.character_names: Optional[List[str]] = None
        self.class_names: Optional[List[str]] = None
        self.min_level: Optional[int] = None
        self.max_level: Optional[int] = None
        self.modified_after: Optional[datetime] = None
        self.modified_before: Optional[datetime] = None
        self.user_id: Optional[str] = None
        self.campaign_id: Optional[str] = None
        self.limit: Optional[int] = None
        self.offset: Optional[int] = None
        self.include_deleted: bool = False


class CharacterSnapshot:
    """A point-in-time snapshot of a character."""
    
    def __init__(
        self,
        character_id: int,
        version: int,
        character_data: Character,
        timestamp: datetime,
        change_summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.character_id = character_id
        self.version = version
        self.character_data = character_data
        self.timestamp = timestamp
        self.change_summary = change_summary
        self.metadata = metadata or {}


class CharacterDiff:
    """Represents differences between two character snapshots."""
    
    def __init__(
        self,
        character_id: int,
        from_version: int,
        to_version: int,
        changes: Dict[str, Tuple[Any, Any]],  # field -> (old_value, new_value)
        timestamp: datetime
    ):
        self.character_id = character_id
        self.from_version = from_version
        self.to_version = to_version
        self.changes = changes
        self.timestamp = timestamp
        
    def get_changed_fields(self) -> List[str]:
        """Get list of fields that changed."""
        return list(self.changes.keys())
    
    def has_field_changed(self, field: str) -> bool:
        """Check if a specific field changed."""
        return field in self.changes


class ICharacterStorage(ABC):
    """
    Abstract interface for character data storage.
    
    Implementations should handle:
    - CRUD operations for characters
    - Version history tracking
    - Efficient querying
    - Data compression
    - Transaction support where applicable
    """
    
    @abstractmethod
    async def save_character(
        self,
        character: Character,
        user_id: Optional[str] = None,
        change_summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CharacterSnapshot:
        """
        Save a character, creating a new version snapshot.
        
        Args:
            character: The character data to save
            user_id: Optional user identifier
            change_summary: Optional description of changes
            metadata: Optional metadata to store with snapshot
            
        Returns:
            The created character snapshot
        """
        pass
    
    @abstractmethod
    async def get_character(
        self,
        character_id: int,
        version: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> Optional[CharacterSnapshot]:
        """
        Retrieve a character snapshot.
        
        Args:
            character_id: The character's ID
            version: Specific version to retrieve (None for latest)
            user_id: Optional user ID for access control
            
        Returns:
            Character snapshot if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_character_history(
        self,
        character_id: int,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[CharacterSnapshot]:
        """
        Get version history for a character.
        
        Args:
            character_id: The character's ID
            user_id: Optional user ID for access control
            limit: Maximum number of versions to return
            offset: Number of versions to skip
            
        Returns:
            List of character snapshots, newest first
        """
        pass
    
    @abstractmethod
    async def get_character_diff(
        self,
        character_id: int,
        from_version: int,
        to_version: int,
        user_id: Optional[str] = None
    ) -> Optional[CharacterDiff]:
        """
        Get differences between two character versions.
        
        Args:
            character_id: The character's ID
            from_version: Starting version
            to_version: Ending version
            user_id: Optional user ID for access control
            
        Returns:
            Character diff if versions exist, None otherwise
        """
        pass
    
    @abstractmethod
    async def query_characters(
        self,
        filter: QueryFilter
    ) -> List[CharacterSnapshot]:
        """
        Query characters based on filter criteria.
        
        Args:
            filter: Query filter with search criteria
            
        Returns:
            List of matching character snapshots
        """
        pass
    
    @abstractmethod
    async def delete_character(
        self,
        character_id: int,
        user_id: Optional[str] = None,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete a character.
        
        Args:
            character_id: The character's ID
            user_id: Optional user ID for access control
            hard_delete: If True, permanently delete. If False, soft delete.
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def archive_old_versions(
        self,
        before_date: datetime,
        keep_every_nth: int = 1
    ) -> int:
        """
        Archive old character versions based on retention policy.
        
        Args:
            before_date: Archive versions before this date
            keep_every_nth: Keep every Nth version (1 = keep all)
            
        Returns:
            Number of versions archived
        """
        pass
    
    @abstractmethod
    async def export_character(
        self,
        character_id: int,
        format: str = "json",
        include_history: bool = False,
        user_id: Optional[str] = None
    ) -> bytes:
        """
        Export character data in specified format.
        
        Args:
            character_id: The character's ID
            format: Export format (json, xml, etc.)
            include_history: Whether to include version history
            user_id: Optional user ID for access control
            
        Returns:
            Exported data as bytes
        """
        pass
    
    @abstractmethod
    async def import_character(
        self,
        data: bytes,
        format: str = "json",
        user_id: Optional[str] = None
    ) -> CharacterSnapshot:
        """
        Import character data from external format.
        
        Args:
            data: Character data to import
            format: Import format (json, xml, etc.)
            user_id: Optional user ID
            
        Returns:
            Created character snapshot
        """
        pass


class ICacheStorage(ABC):
    """
    Abstract interface for caching frequently accessed data.
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> int:
        """Clear all cached values. Returns number cleared."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass


class IStorageTransaction(ABC):
    """
    Transaction context for storage operations.
    """
    
    @abstractmethod
    async def __aenter__(self):
        """Begin transaction."""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Commit or rollback transaction."""
        pass
    
    @abstractmethod
    async def commit(self):
        """Explicitly commit transaction."""
        pass
    
    @abstractmethod
    async def rollback(self):
        """Explicitly rollback transaction."""
        pass


class IStorageFactory(ABC):
    """
    Factory for creating storage instances based on configuration.
    """
    
    @abstractmethod
    def create_character_storage(
        self,
        backend: StorageBackend,
        config: Dict[str, Any]
    ) -> ICharacterStorage:
        """Create character storage instance."""
        pass
    
    @abstractmethod
    def create_cache_storage(
        self,
        backend: str,
        config: Dict[str, Any]
    ) -> ICacheStorage:
        """Create cache storage instance."""
        pass
    
    @abstractmethod
    def supports_transactions(self, backend: StorageBackend) -> bool:
        """Check if backend supports transactions."""
        pass