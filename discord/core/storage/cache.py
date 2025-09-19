"""
Cache implementations for improved storage performance.
"""

import json
import time
import pickle
from typing import Any, Optional, Dict, Set, List
from datetime import datetime, timedelta
import asyncio
from asyncio import Lock
import logging

from shared.interfaces.storage import ICacheStorage


logger = logging.getLogger(__name__)


class MemoryCache(ICacheStorage):
    """
    In-memory cache implementation.
    
    Features:
    - LRU eviction
    - TTL support
    - Automatic cleanup
    - Memory usage tracking
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl_seconds: int = 3600,
        cleanup_interval_seconds: int = 300,
        max_memory_mb: int = 100
    ):
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
        self._expiry_times: Dict[str, float] = {}
        self._lock = Lock()
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._memory_usage = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            current_time = time.time()
            
            # Check if key exists and not expired
            if key in self._cache:
                if key in self._expiry_times and current_time > self._expiry_times[key]:
                    # Expired
                    await self._remove_key(key)
                    self._misses += 1
                    return None
                
                # Update access time for LRU
                self._access_times[key] = current_time
                self._hits += 1
                
                return self._cache[key]['value']
            
            self._misses += 1
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL."""
        async with self._lock:
            current_time = time.time()
            
            # Calculate expiry time
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
            expiry_time = current_time + ttl if ttl > 0 else None
            
            # Serialize value to calculate size
            try:
                serialized = pickle.dumps(value)
                value_size = len(serialized)
            except Exception as e:
                logger.error(f"Failed to serialize cache value for key {key}: {e}")
                return False
            
            # Check if we need to evict entries
            while (len(self._cache) >= self.max_size or 
                   self._memory_usage + value_size > self.max_memory_bytes):
                
                if not await self._evict_lru():
                    # Can't evict anymore, reject the new value
                    logger.warning(f"Cache full, cannot store key: {key}")
                    return False
            
            # Store the value
            self._cache[key] = {
                'value': value,
                'size': value_size,
                'created_at': current_time
            }
            self._access_times[key] = current_time
            
            if expiry_time:
                self._expiry_times[key] = expiry_time
            
            self._memory_usage += value_size
            
            return True
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        async with self._lock:
            if key in self._cache:
                await self._remove_key(key)
                return True
            return False
    
    async def clear(self) -> int:
        """Clear all cached values."""
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._access_times.clear()
            self._expiry_times.clear()
            self._memory_usage = 0
            return count
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        async with self._lock:
            current_time = time.time()
            
            if key not in self._cache:
                return False
            
            # Check if expired
            if key in self._expiry_times and current_time > self._expiry_times[key]:
                await self._remove_key(key)
                return False
            
            return True
    
    async def _remove_key(self, key: str):
        """Remove a key from cache and update statistics."""
        if key in self._cache:
            self._memory_usage -= self._cache[key]['size']
            del self._cache[key]
        
        if key in self._access_times:
            del self._access_times[key]
        
        if key in self._expiry_times:
            del self._expiry_times[key]
    
    async def _evict_lru(self) -> bool:
        """Evict least recently used item."""
        if not self._access_times:
            return False
        
        # Find LRU item
        lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        
        await self._remove_key(lru_key)
        self._evictions += 1
        
        return True
    
    async def _cleanup_loop(self):
        """Background task to clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval_seconds)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
    
    async def _cleanup_expired(self):
        """Remove expired entries."""
        async with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, expiry in self._expiry_times.items()
                if current_time > expiry
            ]
            
            for key in expired_keys:
                await self._remove_key(key)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        hit_rate = self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0
        
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "memory_usage_mb": self._memory_usage / (1024 * 1024),
            "max_memory_mb": self.max_memory_bytes / (1024 * 1024),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "evictions": self._evictions
        }
    
    async def close(self):
        """Clean up resources."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


class RedisCache(ICacheStorage):
    """
    Redis-based cache implementation.
    
    Features:
    - Distributed caching
    - Persistence options
    - Advanced data structures
    - High performance
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        key_prefix: str = "dnd_scraper:",
        default_ttl_seconds: int = 3600,
        max_connections: int = 10
    ):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.default_ttl_seconds = default_ttl_seconds
        self.max_connections = max_connections
        
        self._redis = None
        self._connection_pool = None
    
    async def _get_redis(self):
        """Get or create Redis connection."""
        if self._redis is None:
            try:
                import aioredis
                
                self._connection_pool = aioredis.ConnectionPool.from_url(
                    self.redis_url,
                    max_connections=self.max_connections,
                    decode_responses=False  # We handle encoding ourselves
                )
                
                self._redis = aioredis.Redis(connection_pool=self._connection_pool)
                
                # Test connection
                await self._redis.ping()
                
            except ImportError:
                raise ImportError("aioredis is required for Redis cache")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        
        return self._redis
    
    def _make_key(self, key: str) -> str:
        """Create prefixed key."""
        return f"{self.key_prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        redis = await self._get_redis()
        
        try:
            data = await redis.get(self._make_key(key))
            if data is None:
                return None
            
            # Deserialize
            return pickle.loads(data)
            
        except Exception as e:
            logger.error(f"Error getting key {key} from Redis: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Set value in Redis cache."""
        redis = await self._get_redis()
        
        try:
            # Serialize value
            data = pickle.dumps(value)
            
            # Set TTL
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
            
            if ttl > 0:
                await redis.setex(self._make_key(key), ttl, data)
            else:
                await redis.set(self._make_key(key), data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting key {key} in Redis: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from Redis cache."""
        redis = await self._get_redis()
        
        try:
            result = await redis.delete(self._make_key(key))
            return result > 0
            
        except Exception as e:
            logger.error(f"Error deleting key {key} from Redis: {e}")
            return False
    
    async def clear(self) -> int:
        """Clear all cached values with our prefix."""
        redis = await self._get_redis()
        
        try:
            # Find all keys with our prefix
            keys = []
            async for key in redis.scan_iter(match=f"{self.key_prefix}*"):
                keys.append(key)
            
            if keys:
                return await redis.delete(*keys)
            
            return 0
            
        except Exception as e:
            logger.error(f"Error clearing Redis cache: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        redis = await self._get_redis()
        
        try:
            result = await redis.exists(self._make_key(key))
            return result > 0
            
        except Exception as e:
            logger.error(f"Error checking key {key} in Redis: {e}")
            return False
    
    async def close(self):
        """Close Redis connections."""
        if self._connection_pool:
            await self._connection_pool.disconnect()
            self._connection_pool = None
            self._redis = None


class TieredCache(ICacheStorage):
    """
    Multi-tiered cache implementation.
    
    Uses multiple cache levels (e.g., memory + Redis) for optimal performance.
    """
    
    def __init__(self, caches: List[ICacheStorage]):
        """
        Initialize with list of caches, ordered by speed (fastest first).
        """
        if not caches:
            raise ValueError("At least one cache is required")
        
        self.caches = caches
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from the first cache that has it."""
        for i, cache in enumerate(self.caches):
            try:
                value = await cache.get(key)
                if value is not None:
                    # Backfill to faster caches
                    for j in range(i):
                        try:
                            await self.caches[j].set(key, value)
                        except Exception as e:
                            logger.warning(f"Failed to backfill cache {j}: {e}")
                    
                    return value
            except Exception as e:
                logger.warning(f"Error getting from cache {i}: {e}")
                continue
        
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Set value in all caches."""
        success = False
        
        for i, cache in enumerate(self.caches):
            try:
                if await cache.set(key, value, ttl_seconds):
                    success = True
            except Exception as e:
                logger.warning(f"Failed to set in cache {i}: {e}")
        
        return success
    
    async def delete(self, key: str) -> bool:
        """Delete from all caches."""
        success = False
        
        for cache in self.caches:
            try:
                if await cache.delete(key):
                    success = True
            except Exception as e:
                logger.warning(f"Failed to delete from cache: {e}")
        
        return success
    
    async def clear(self) -> int:
        """Clear all caches."""
        total_cleared = 0
        
        for cache in self.caches:
            try:
                cleared = await cache.clear()
                total_cleared += cleared
            except Exception as e:
                logger.warning(f"Failed to clear cache: {e}")
        
        return total_cleared
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in any cache."""
        for cache in self.caches:
            try:
                if await cache.exists(key):
                    return True
            except Exception as e:
                logger.warning(f"Failed to check cache: {e}")
        
        return False
    
    async def close(self):
        """Close all caches."""
        for cache in self.caches:
            try:
                if hasattr(cache, 'close'):
                    await cache.close()
            except Exception as e:
                logger.warning(f"Failed to close cache: {e}")


# Cache key generation utilities

def make_character_key(character_id: int, version: Optional[int] = None) -> str:
    """Generate cache key for character data."""
    if version:
        return f"character:{character_id}:v{version}"
    return f"character:{character_id}:latest"


def make_history_key(character_id: int, limit: Optional[int] = None, offset: Optional[int] = None) -> str:
    """Generate cache key for character history."""
    key = f"history:{character_id}"
    if limit:
        key += f":limit{limit}"
    if offset:
        key += f":offset{offset}"
    return key


def make_query_key(filter: 'QueryFilter') -> str:
    """Generate cache key for character queries."""
    # Create a deterministic key from filter parameters
    key_parts = ["query"]
    
    if filter.character_ids:
        key_parts.append(f"ids:{','.join(map(str, sorted(filter.character_ids)))}")
    
    if filter.user_id:
        key_parts.append(f"user:{filter.user_id}")
    
    if filter.campaign_id:
        key_parts.append(f"campaign:{filter.campaign_id}")
    
    if filter.character_names:
        key_parts.append(f"names:{','.join(sorted(filter.character_names))}")
    
    if filter.class_names:
        key_parts.append(f"classes:{','.join(sorted(filter.class_names))}")
    
    if filter.min_level:
        key_parts.append(f"minlvl:{filter.min_level}")
    
    if filter.max_level:
        key_parts.append(f"maxlvl:{filter.max_level}")
    
    if filter.limit:
        key_parts.append(f"limit:{filter.limit}")
    
    if filter.offset:
        key_parts.append(f"offset:{filter.offset}")
    
    return ":".join(key_parts)


class CacheManager:
    """
    High-level cache management with automatic key generation and invalidation.
    """
    
    def __init__(self, cache: ICacheStorage, default_ttl: int = 3600):
        self.cache = cache
        self.default_ttl = default_ttl
        self._invalidation_patterns: Dict[str, Set[str]] = {}
    
    async def get_character(self, character_id: int, version: Optional[int] = None):
        """Get cached character data."""
        key = make_character_key(character_id, version)
        return await self.cache.get(key)
    
    async def set_character(
        self,
        character_id: int,
        data: Any,
        version: Optional[int] = None,
        ttl: Optional[int] = None
    ):
        """Cache character data."""
        key = make_character_key(character_id, version)
        ttl = ttl or self.default_ttl
        
        # Set up invalidation tracking
        pattern = f"character:{character_id}:*"
        if pattern not in self._invalidation_patterns:
            self._invalidation_patterns[pattern] = set()
        self._invalidation_patterns[pattern].add(key)
        
        return await self.cache.set(key, data, ttl)
    
    async def invalidate_character(self, character_id: int):
        """Invalidate all cached data for a character."""
        pattern = f"character:{character_id}:*"
        
        if pattern in self._invalidation_patterns:
            for key in self._invalidation_patterns[pattern]:
                await self.cache.delete(key)
            
            del self._invalidation_patterns[pattern]
    
    async def get_query_result(self, filter: 'QueryFilter'):
        """Get cached query result."""
        key = make_query_key(filter)
        return await self.cache.get(key)
    
    async def set_query_result(
        self,
        filter: 'QueryFilter',
        result: Any,
        ttl: Optional[int] = None
    ):
        """Cache query result."""
        key = make_query_key(filter)
        ttl = ttl or (self.default_ttl // 4)  # Shorter TTL for queries
        
        return await self.cache.set(key, result, ttl)
    
    async def invalidate_queries(self):
        """Invalidate all cached query results."""
        # In a real implementation, we'd track query keys
        # For now, we'll use a pattern-based approach
        keys_to_delete = []
        
        # This would need to be implemented based on the cache backend
        # For Redis, we could use SCAN with pattern matching
        # For memory cache, we'd need to track query keys
        
        # Placeholder implementation
        pass