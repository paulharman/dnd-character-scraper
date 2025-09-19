"""
Storage subsystem for D&D character data persistence.

This module provides comprehensive storage solutions for character data with:
- Multiple backend support (JSON, SQLite, PostgreSQL, cloud)
- Version history and change tracking
- Efficient caching strategies
- Data compression and archival
- GDPR compliance features
- Migration between storage backends
"""

from typing import List

from .factory import (
    StorageFactory,
    StorageConfig,
    create_storage_from_config,
    validate_storage_config
)

from .cache import (
    MemoryCache,
    RedisCache,
    TieredCache,
    CacheManager,
    make_character_key,
    make_history_key,
    make_query_key
)

from .file_json import FileJsonStorage
from .file_sqlite import FileSQLiteStorage
from .database_postgres import PostgresStorage

# Re-export interface types
from shared.interfaces.storage import (
    ICharacterStorage,
    ICacheStorage,
    IStorageFactory,
    IStorageTransaction,
    StorageBackend,
    QueryFilter,
    CharacterSnapshot,
    CharacterDiff
)

from shared.models.storage import (
    CompressionType,
    StorageMetadata,
    CharacterIndex,
    VersionMetadata,
    CharacterRelationship,
    Campaign,
    User,
    RetentionPolicy,
    StorageStatistics
)


__all__ = [
    # Factory and configuration
    "StorageFactory",
    "StorageConfig", 
    "create_storage_from_config",
    "validate_storage_config",
    
    # Cache implementations
    "MemoryCache",
    "RedisCache", 
    "TieredCache",
    "CacheManager",
    "make_character_key",
    "make_history_key",
    "make_query_key",
    
    # Storage implementations
    "FileJsonStorage",
    "FileSQLiteStorage",
    "PostgresStorage",
    
    # Interface types
    "ICharacterStorage",
    "ICacheStorage",
    "IStorageFactory",
    "IStorageTransaction",
    "StorageBackend",
    "QueryFilter",
    "CharacterSnapshot",
    "CharacterDiff",
    
    # Model types
    "CompressionType",
    "StorageMetadata",
    "CharacterIndex",
    "VersionMetadata",
    "CharacterRelationship",
    "Campaign",
    "User",
    "RetentionPolicy",
    "StorageStatistics"
]


# Version information
__version__ = "1.0.0"
__author__ = "D&D Character Scraper Team"


def get_available_backends() -> List[StorageBackend]:
    """Get list of available storage backends."""
    return [
        StorageBackend.FILE_JSON,
        StorageBackend.FILE_SQLITE,
        StorageBackend.DATABASE_POSTGRES,
        # StorageBackend.DATABASE_MYSQL,  # Not yet implemented
        # StorageBackend.CLOUD_S3,        # Not yet implemented  
        # StorageBackend.CLOUD_AZURE,     # Not yet implemented
        StorageBackend.MEMORY,           # For testing only
    ]


def get_recommended_backend(use_case: str) -> StorageBackend:
    """
    Get recommended storage backend for different use cases.
    
    Args:
        use_case: One of 'development', 'testing', 'production', 'high_performance'
        
    Returns:
        Recommended storage backend
    """
    recommendations = {
        "development": StorageBackend.FILE_JSON,
        "testing": StorageBackend.MEMORY,
        "production": StorageBackend.DATABASE_POSTGRES,
        "high_performance": StorageBackend.DATABASE_POSTGRES,
        "single_user": StorageBackend.FILE_SQLITE,
        "multi_user": StorageBackend.DATABASE_POSTGRES,
        "portable": StorageBackend.FILE_JSON,
        "cloud": StorageBackend.DATABASE_POSTGRES  # Could be S3 when implemented
    }
    
    return recommendations.get(use_case, StorageBackend.FILE_JSON)


# Quick setup functions for common scenarios

async def create_development_storage():
    """Create storage setup optimized for development."""
    config = StorageConfig.get_development_config()
    return create_storage_from_config(config)


async def create_production_storage():
    """Create storage setup optimized for production."""
    config = StorageConfig.get_production_config()
    return create_storage_from_config(config)


async def create_testing_storage():
    """Create storage setup optimized for testing."""
    config = StorageConfig.get_testing_config()
    return create_storage_from_config(config)