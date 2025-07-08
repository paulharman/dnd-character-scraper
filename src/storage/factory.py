"""
Storage factory for creating storage instances based on configuration.

This factory provides a unified interface for creating character storage backends
with different capabilities and deployment requirements.

Available Storage Backends:
- file_json: File-based JSON storage (development, single-user)
- file_sqlite: SQLite database storage (small to medium deployments)
- database_postgres: PostgreSQL storage (production, scalable)
- memory: In-memory storage (testing, ephemeral)

Planned Storage Backends (not implemented):
- database_mysql: MySQL database storage
- cloud_s3: Amazon S3 cloud storage
- cloud_azure: Azure Blob cloud storage

Use get_available_backends() to get the list of actually implemented backends.
"""

from typing import Dict, Any, Optional, List, Tuple
import logging

from src.interfaces.storage import (
    ICharacterStorage, ICacheStorage, IStorageFactory,
    StorageBackend
)
from src.models.storage import CompressionType

# Import storage implementations
from .file_json import FileJsonStorage
from .file_sqlite import FileSQLiteStorage
from .database_postgres import PostgresStorage
from .memory import MemoryStorage
from .cache import MemoryCache, RedisCache, TieredCache, CacheManager


logger = logging.getLogger(__name__)


class StorageFactory(IStorageFactory):
    """
    Factory for creating storage instances based on configuration.
    """
    
    def create_character_storage(
        self,
        backend: StorageBackend,
        config: Dict[str, Any]
    ) -> ICharacterStorage:
        """Create character storage instance based on backend type."""
        
        if backend == StorageBackend.FILE_JSON:
            return self._create_file_json_storage(config)
        
        elif backend == StorageBackend.FILE_SQLITE:
            return self._create_file_sqlite_storage(config)
        
        elif backend == StorageBackend.DATABASE_POSTGRES:
            return self._create_postgres_storage(config)
        
        elif backend == StorageBackend.DATABASE_MYSQL:
            return self._create_mysql_storage(config)
        
        elif backend == StorageBackend.CLOUD_S3:
            return self._create_s3_storage(config)
        
        elif backend == StorageBackend.CLOUD_AZURE:
            return self._create_azure_storage(config)
        
        elif backend == StorageBackend.MEMORY:
            return self._create_memory_storage(config)
        
        else:
            raise ValueError(f"Unsupported storage backend: {backend}")
    
    def create_cache_storage(
        self,
        backend: str,
        config: Dict[str, Any]
    ) -> ICacheStorage:
        """Create cache storage instance."""
        
        if backend == "memory":
            return self._create_memory_cache(config)
        
        elif backend == "redis":
            return self._create_redis_cache(config)
        
        elif backend == "tiered":
            return self._create_tiered_cache(config)
        
        else:
            raise ValueError(f"Unsupported cache backend: {backend}")
    
    def supports_transactions(self, backend: StorageBackend) -> bool:
        """Check if backend supports transactions."""
        return backend in [
            StorageBackend.FILE_SQLITE,
            StorageBackend.DATABASE_POSTGRES,
            StorageBackend.DATABASE_MYSQL
        ]
    
    def get_available_backends(self) -> List[StorageBackend]:
        """Get list of actually implemented storage backends."""
        return [
            StorageBackend.FILE_JSON,
            StorageBackend.FILE_SQLITE,
            StorageBackend.DATABASE_POSTGRES,
            StorageBackend.MEMORY
        ]
    
    def get_unavailable_backends(self) -> List[StorageBackend]:
        """Get list of planned but not implemented storage backends."""
        return [
            StorageBackend.DATABASE_MYSQL,
            StorageBackend.CLOUD_S3,
            StorageBackend.CLOUD_AZURE
        ]
    
    def _create_file_json_storage(self, config: Dict[str, Any]) -> FileJsonStorage:
        """Create file-based JSON storage."""
        storage_root = config.get("storage_root", "./data/characters")
        compression = CompressionType(config.get("compression", "gzip"))
        enable_delta_storage = config.get("enable_delta_storage", True)
        delta_threshold_kb = config.get("delta_threshold_kb", 100)
        
        return FileJsonStorage(
            storage_root=storage_root,
            compression=compression,
            enable_delta_storage=enable_delta_storage,
            delta_threshold_kb=delta_threshold_kb
        )
    
    def _create_file_sqlite_storage(self, config: Dict[str, Any]) -> FileSQLiteStorage:
        """Create SQLite storage."""
        db_path = config.get("db_path", "./data/characters.db")
        compression = CompressionType(config.get("compression", "gzip"))
        enable_wal = config.get("enable_wal", True)
        cache_size_mb = config.get("cache_size_mb", 50)
        
        return FileSQLiteStorage(
            db_path=db_path,
            compression=compression,
            enable_wal=enable_wal,
            cache_size_mb=cache_size_mb
        )
    
    def _create_postgres_storage(self, config: Dict[str, Any]) -> PostgresStorage:
        """Create PostgreSQL storage."""
        dsn = config.get("dsn")
        if not dsn:
            # Build DSN from components
            host = config.get("host", "localhost")
            port = config.get("port", 5432)
            database = config.get("database", "dnd_characters")
            user = config.get("user", "postgres")
            password = config.get("password", "")
            
            dsn = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        pool_size = config.get("pool_size", 10)
        max_pool_size = config.get("max_pool_size", 20)
        compression = CompressionType(config.get("compression", "zstd"))
        enable_partitioning = config.get("enable_partitioning", False)
        partition_by = config.get("partition_by", "month")
        
        return PostgresStorage(
            dsn=dsn,
            pool_size=pool_size,
            max_pool_size=max_pool_size,
            compression=compression,
            enable_partitioning=enable_partitioning,
            partition_by=partition_by
        )
    
    def _create_mysql_storage(self, config: Dict[str, Any]) -> ICharacterStorage:
        """Create MySQL storage (not implemented).
        
        This backend is planned for future development but not yet available.
        Consider using PostgreSQL storage instead, which provides similar functionality.
        """
        raise NotImplementedError(
            "MySQL storage backend is not implemented. "
            "Available backends: file_json, file_sqlite, database_postgres, memory"
        )
    
    def _create_s3_storage(self, config: Dict[str, Any]) -> ICharacterStorage:
        """Create S3 storage (not implemented).
        
        This backend is planned for future development for cloud deployments.
        Consider using file_json storage with network-mounted directories as a workaround.
        """
        raise NotImplementedError(
            "S3 storage backend is not implemented. "
            "Available backends: file_json, file_sqlite, database_postgres, memory"
        )
    
    def _create_azure_storage(self, config: Dict[str, Any]) -> ICharacterStorage:
        """Create Azure Blob storage (not implemented).
        
        This backend is planned for future development for cloud deployments.
        Consider using file_json storage with network-mounted directories as a workaround.
        """
        raise NotImplementedError(
            "Azure storage backend is not implemented. "
            "Available backends: file_json, file_sqlite, database_postgres, memory"
        )
    
    def _create_memory_storage(self, config: Dict[str, Any]) -> MemoryStorage:
        """Create in-memory storage (for testing)."""
        return MemoryStorage()
    
    def _create_memory_cache(self, config: Dict[str, Any]) -> MemoryCache:
        """Create memory cache."""
        max_size = config.get("max_size", 1000)
        default_ttl_seconds = config.get("default_ttl_seconds", 3600)
        cleanup_interval_seconds = config.get("cleanup_interval_seconds", 300)
        max_memory_mb = config.get("max_memory_mb", 100)
        
        return MemoryCache(
            max_size=max_size,
            default_ttl_seconds=default_ttl_seconds,
            cleanup_interval_seconds=cleanup_interval_seconds,
            max_memory_mb=max_memory_mb
        )
    
    def _create_redis_cache(self, config: Dict[str, Any]) -> RedisCache:
        """Create Redis cache."""
        redis_url = config.get("redis_url", "redis://localhost:6379")
        key_prefix = config.get("key_prefix", "dnd_scraper:")
        default_ttl_seconds = config.get("default_ttl_seconds", 3600)
        max_connections = config.get("max_connections", 10)
        
        return RedisCache(
            redis_url=redis_url,
            key_prefix=key_prefix,
            default_ttl_seconds=default_ttl_seconds,
            max_connections=max_connections
        )
    
    def _create_tiered_cache(self, config: Dict[str, Any]) -> TieredCache:
        """Create tiered cache with multiple levels."""
        tiers = config.get("tiers", [])
        if not tiers:
            raise ValueError("Tiered cache requires at least one tier configuration")
        
        caches = []
        for tier_config in tiers:
            backend = tier_config.get("backend")
            if not backend:
                raise ValueError("Each tier must specify a backend")
            
            cache = self.create_cache_storage(backend, tier_config)
            caches.append(cache)
        
        return TieredCache(caches)


class StorageConfig:
    """
    Configuration helper for storage settings.
    """
    
    @staticmethod
    def get_development_config() -> Dict[str, Any]:
        """Get configuration suitable for development."""
        return {
            "storage": {
                "backend": "file_json",
                "config": {
                    "storage_root": "./data/dev/characters",
                    "compression": "gzip",
                    "enable_delta_storage": True
                }
            },
            "cache": {
                "backend": "memory",
                "config": {
                    "max_size": 100,
                    "default_ttl_seconds": 1800,  # 30 minutes
                    "max_memory_mb": 50
                }
            }
        }
    
    @staticmethod
    def get_production_config() -> Dict[str, Any]:
        """Get configuration suitable for production."""
        return {
            "storage": {
                "backend": "database_postgres",
                "config": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "dnd_characters",
                    "user": "dnd_app",
                    "password": "${DB_PASSWORD}",  # Environment variable
                    "pool_size": 20,
                    "max_pool_size": 50,
                    "compression": "zstd",
                    "enable_partitioning": True
                }
            },
            "cache": {
                "backend": "tiered",
                "config": {
                    "tiers": [
                        {
                            "backend": "memory",
                            "max_size": 500,
                            "default_ttl_seconds": 900,  # 15 minutes
                            "max_memory_mb": 200
                        },
                        {
                            "backend": "redis",
                            "redis_url": "redis://redis-cluster:6379",
                            "default_ttl_seconds": 3600,  # 1 hour
                            "max_connections": 20
                        }
                    ]
                }
            }
        }
    
    @staticmethod
    def get_testing_config() -> Dict[str, Any]:
        """Get configuration suitable for testing."""
        return {
            "storage": {
                "backend": "memory",  # Fast, ephemeral
                "config": {}
            },
            "cache": {
                "backend": "memory",
                "config": {
                    "max_size": 50,
                    "default_ttl_seconds": 60,  # 1 minute
                    "max_memory_mb": 10
                }
            }
        }
    
    @staticmethod
    def get_high_performance_config() -> Dict[str, Any]:
        """Get configuration optimized for high performance."""
        return {
            "storage": {
                "backend": "database_postgres",
                "config": {
                    "dsn": "${DATABASE_URL}",
                    "pool_size": 50,
                    "max_pool_size": 100,
                    "compression": "zstd",
                    "enable_partitioning": True,
                    "partition_by": "month"
                }
            },
            "cache": {
                "backend": "tiered",
                "config": {
                    "tiers": [
                        {
                            "backend": "memory",
                            "max_size": 2000,
                            "default_ttl_seconds": 300,  # 5 minutes
                            "max_memory_mb": 500
                        },
                        {
                            "backend": "redis",
                            "redis_url": "${REDIS_URL}",
                            "default_ttl_seconds": 1800,  # 30 minutes
                            "max_connections": 50
                        }
                    ]
                }
            }
        }


def create_storage_from_config(config: Dict[str, Any]) -> Tuple[ICharacterStorage, Optional[CacheManager]]:
    """
    Create storage and cache instances from configuration.
    
    Returns:
        Tuple of (storage, cache_manager)
    """
    factory = StorageFactory()
    
    # Create storage
    storage_config = config.get("storage", {})
    backend = StorageBackend(storage_config.get("backend", "file_json"))
    storage_params = storage_config.get("config", {})
    
    storage = factory.create_character_storage(backend, storage_params)
    
    # Create cache if configured
    cache_manager = None
    cache_config = config.get("cache")
    
    if cache_config:
        cache_backend = cache_config.get("backend")
        cache_params = cache_config.get("config", {})
        
        if cache_backend:
            cache = factory.create_cache_storage(cache_backend, cache_params)
            default_ttl = cache_params.get("default_ttl_seconds", 3600)
            cache_manager = CacheManager(cache, default_ttl)
    
    return storage, cache_manager


# Example usage and configuration validation

def validate_storage_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate storage configuration and return list of errors.
    """
    errors = []
    
    # Check storage config
    storage_config = config.get("storage")
    if not storage_config:
        errors.append("Missing 'storage' configuration")
        return errors
    
    backend = storage_config.get("backend")
    if not backend:
        errors.append("Missing storage backend")
    else:
        try:
            backend_enum = StorageBackend(backend)
            # Check if backend is actually implemented
            factory = StorageFactory()
            if backend_enum not in factory.get_available_backends():
                available = [b.value for b in factory.get_available_backends()]
                errors.append(f"Storage backend '{backend}' is not implemented. Available backends: {', '.join(available)}")
        except ValueError:
            errors.append(f"Invalid storage backend: {backend}")
    
    storage_params = storage_config.get("config", {})
    
    # Backend-specific validation
    if backend == "file_json":
        if not storage_params.get("storage_root"):
            errors.append("file_json backend requires 'storage_root'")
    
    elif backend == "file_sqlite":
        if not storage_params.get("db_path"):
            errors.append("file_sqlite backend requires 'db_path'")
    
    elif backend == "database_postgres":
        if not storage_params.get("dsn") and not all([
            storage_params.get("host"),
            storage_params.get("database"),
            storage_params.get("user")
        ]):
            errors.append("postgres backend requires 'dsn' or host/database/user")
    
    # Check cache config (optional)
    cache_config = config.get("cache")
    if cache_config:
        cache_backend = cache_config.get("backend")
        if cache_backend == "tiered":
            tiers = cache_config.get("config", {}).get("tiers", [])
            if not tiers:
                errors.append("tiered cache requires at least one tier")
    
    return errors


if __name__ == "__main__":
    # Example usage
    import asyncio
    
    async def main():
        # Test development configuration
        dev_config = StorageConfig.get_development_config()
        
        # Validate configuration
        errors = validate_storage_config(dev_config)
        if errors:
            print("Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return
        
        # Show available backends
        factory = StorageFactory()
        available = factory.get_available_backends()
        unavailable = factory.get_unavailable_backends()
        
        print("Available storage backends:")
        for backend in available:
            print(f"  ✓ {backend.value}")
        
        print("Planned storage backends (not implemented):")
        for backend in unavailable:
            print(f"  ✗ {backend.value}")
        
        # Create storage and cache
        storage, cache_manager = create_storage_from_config(dev_config)
        
        print(f"\nCreated storage: {type(storage).__name__}")
        if cache_manager:
            print(f"Created cache: {type(cache_manager.cache).__name__}")
        
        # Test memory storage specifically
        print("\nTesting memory storage:")
        memory_config = StorageConfig.get_testing_config()
        memory_storage, _ = create_storage_from_config(memory_config)
        print(f"Memory storage: {type(memory_storage).__name__}")
        
        # Clean up
        if hasattr(storage, 'close'):
            await storage.close()
        
        if cache_manager and hasattr(cache_manager.cache, 'close'):
            await cache_manager.cache.close()
    
    asyncio.run(main())