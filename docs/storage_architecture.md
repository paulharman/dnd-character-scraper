# D&D Character Scraper - Storage Architecture

## Overview

The D&D Character Scraper uses a flexible, multi-backend storage architecture designed to scale from single-user file storage to enterprise-grade multi-user database deployments. The system supports version history, change tracking, data compression, caching, and GDPR compliance.

## Architecture Components

### 1. Storage Interface Layer (`src/interfaces/storage.py`)

The storage system is built around abstract interfaces that define contracts for:

- **`ICharacterStorage`**: Core character data operations (CRUD, versioning, querying)
- **`ICacheStorage`**: Caching operations with TTL support
- **`IStorageTransaction`**: Transaction management for ACID compliance
- **`IStorageFactory`**: Factory pattern for creating storage instances

### 2. Storage Implementations

#### File-based Storage

**JSON Storage (`FileJsonStorage`)**
- **Use Case**: Development, single-user, portable deployments
- **Features**: Human-readable format, compression, delta storage
- **Directory Structure**:
  ```
  storage_root/
  ├── index.json              # Character index
  ├── metadata.json          # Storage metadata
  ├── characters/
  │   └── {character_id}/
  │       ├── latest.json    # Current version
  │       ├── versions/      # Version history
  │       └── metadata.json  # Version metadata
  ├── archive/               # Archived versions
  └── temp/                  # Temporary files
  ```

**SQLite Storage (`FileSQLiteStorage`)**
- **Use Case**: Single-user with better performance than JSON
- **Features**: ACID compliance, SQL queries, WAL mode, compression
- **Benefits**: Single file deployment, concurrent reads, built-in indexing

#### Database Storage

**PostgreSQL Storage (`PostgresStorage`)**
- **Use Case**: Production, multi-user, high concurrency
- **Features**: JSONB queries, connection pooling, partitioning, replication
- **Advanced Features**:
  - Row-level security for multi-tenancy
  - JSONB indexing for flexible queries
  - Table partitioning for large datasets
  - Prepared statements for performance

### 3. Caching Layer

**Memory Cache (`MemoryCache`)**
- LRU eviction policy
- TTL support with background cleanup
- Memory usage tracking
- Configurable size limits

**Redis Cache (`RedisCache`)**
- Distributed caching across instances
- Persistence options
- Advanced data structures
- Connection pooling

**Tiered Cache (`TieredCache`)**
- Multiple cache levels (e.g., Memory → Redis)
- Automatic backfill to faster caches
- Fault tolerance

### 4. Storage Factory

The `StorageFactory` creates storage instances based on configuration:

```python
from src.storage import create_storage_from_config

config = {
    "storage": {
        "backend": "database_postgres",
        "config": {"dsn": "postgresql://..."}
    },
    "cache": {
        "backend": "tiered",
        "config": {"tiers": [...]}
    }
}

storage, cache_manager = create_storage_from_config(config)
```

## Data Models

### Character Storage Models

**`CharacterSnapshot`**: Point-in-time character state
- Character ID and version
- Full character data
- Timestamp and change summary
- Metadata

**`CharacterDiff`**: Differences between versions
- Source and target versions
- Field-level changes (old_value, new_value)
- Change timestamp

**`CharacterIndex`**: Fast lookup metadata
- Basic character info (name, level, classes)
- Version counts and timestamps
- Access statistics
- User/campaign associations

### Query and Filtering

**`QueryFilter`**: Flexible character search
- Character IDs, names, classes
- Level ranges, date ranges
- User/campaign filtering
- Pagination support

## Storage Backend Comparison

| Feature | JSON | SQLite | PostgreSQL | Future: S3 |
|---------|------|--------|------------|------------|
| **Deployment** | Single file/dir | Single file | Server | Cloud |
| **Concurrency** | File locking | Read concurrent | High concurrent | Eventually consistent |
| **Query Performance** | Linear scan | Indexed | Advanced indexing | Limited |
| **ACID Compliance** | No | Yes | Yes | No |
| **Scalability** | Limited | Medium | High | Very High |
| **Backup** | File copy | File copy | Standard tools | Built-in |
| **Multi-user** | No | Limited | Yes | Yes |

## Performance Optimizations

### 1. Caching Strategy

```python
# Cache hierarchy for optimal performance
cache_config = {
    "backend": "tiered",
    "tiers": [
        {"backend": "memory", "max_size": 1000},    # L1: Hot data
        {"backend": "redis", "ttl": 3600}           # L2: Shared cache
    ]
}
```

### 2. Data Compression

- **GZIP**: Balanced compression/speed (default for file storage)
- **ZSTD**: Better compression ratios (recommended for database)
- **LZ4**: Fastest compression/decompression

### 3. Database Optimizations

**PostgreSQL**:
- JSONB with GIN indexes for flexible queries
- Connection pooling (20-50 connections)
- Table partitioning by time period
- Prepared statements for common operations

**SQLite**:
- WAL mode for concurrent reads
- Increased cache size (50-100MB)
- Optimized PRAGMA settings

### 4. Efficient Querying

```python
# Optimized character queries
filter = QueryFilter(
    class_names=["Fighter", "Wizard"],
    min_level=5,
    max_level=10,
    limit=20,
    user_id="user123"
)

characters = await storage.query_characters(filter)
```

## Data Retention and Archival

### Retention Policies

**Configurable retention rules**:
```yaml
retention:
  keep_all_for_days: 30        # Keep every version for 30 days
  keep_daily_for_days: 90      # Keep daily snapshots for 90 days  
  keep_weekly_for_days: 365    # Keep weekly snapshots for 1 year
  keep_monthly_forever: true   # Keep monthly snapshots forever
  max_versions_per_character: 100
```

### Archival Process

1. **Identification**: Find versions older than retention policy
2. **Compression**: Create compressed archives of old versions
3. **Storage**: Move to archive table/storage (PostgreSQL) or archive directory (file)
4. **Cleanup**: Remove archived versions from main tables
5. **Verification**: Ensure archive integrity

### GDPR Compliance

**Data Subject Rights**:
- Right to be forgotten (hard delete)
- Data portability (export all data)
- Data minimization (automatic cleanup)
- Consent management

**Privacy Features**:
- Encryption at rest for sensitive fields
- Audit logging for all access
- Anonymization instead of deletion
- Configurable data retention limits

## Migration Between Backends

### Migration Process

```python
from src.storage.migration import StorageMigrator

migrator = StorageMigrator(
    source_storage=old_storage,
    target_storage=new_storage,
    batch_size=100,
    verify_integrity=True
)

await migrator.migrate_all_characters()
```

### Migration Strategies

1. **Full Migration**: Move all data to new backend
2. **Gradual Migration**: Migrate characters on access
3. **Hybrid Approach**: Keep old data, new data on new backend
4. **Backup Migration**: Create backup in different format

## Configuration Examples

### Development Setup
```yaml
storage:
  backend: file_json
  config:
    storage_root: "./data/dev"
    compression: gzip
```

### Production Setup
```yaml
storage:
  backend: database_postgres
  config:
    dsn: "${DATABASE_URL}"
    pool_size: 20
    compression: zstd
    enable_partitioning: true

cache:
  backend: tiered
  config:
    tiers:
      - backend: memory
        max_size: 1000
        max_memory_mb: 200
      - backend: redis
        redis_url: "${REDIS_URL}"
        default_ttl_seconds: 3600
```

## Monitoring and Observability

### Storage Metrics

**Performance Metrics**:
- Query response times
- Cache hit rates
- Storage utilization
- Connection pool stats

**Business Metrics**:
- Characters created/modified per day
- Most popular character classes
- User activity patterns
- Version history growth

### Health Checks

```python
# Storage health monitoring
async def check_storage_health(storage):
    try:
        # Test basic operations
        await storage.get_character(test_id)
        
        # Check connection pool
        if hasattr(storage, 'get_pool_stats'):
            pool_stats = await storage.get_pool_stats()
            assert pool_stats['available'] > 0
            
        # Verify recent operations
        stats = await storage.get_statistics()
        assert stats.characters_modified_today >= 0
        
        return {"status": "healthy", "stats": stats}
        
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### Alerting

**Critical Alerts**:
- Storage unavailable
- High error rates (>5%)
- Connection pool exhaustion
- Disk space low (<10%)

**Warning Alerts**:
- Slow queries (>1s)
- Cache hit rate low (<80%)
- High memory usage (>80%)
- Unusual access patterns

## Security Considerations

### Access Control

**User-based Access**:
- Character ownership validation
- Campaign-based sharing
- Role-based permissions

**API Security**:
- Input validation and sanitization
- SQL injection prevention
- Rate limiting

### Data Protection

**Encryption**:
- At-rest encryption for sensitive data
- In-transit encryption (TLS)
- Key rotation policies

**Audit Logging**:
- All data access logged
- User action tracking
- Compliance reporting

## Best Practices

### Development

1. **Use appropriate backend for environment**:
   - Development: `file_json`
   - Testing: `memory`
   - Production: `database_postgres`

2. **Configure caching appropriately**:
   - Development: Small memory cache
   - Production: Tiered cache with Redis

3. **Set up proper retention policies**:
   - Development: Short retention
   - Production: Business-appropriate retention

### Production

1. **Monitor storage performance**
2. **Regular backup verification**
3. **Capacity planning and scaling**
4. **Security audit and compliance**
5. **Disaster recovery testing**

### Performance

1. **Use connection pooling for databases**
2. **Implement appropriate caching**
3. **Monitor and optimize slow queries**
4. **Consider read replicas for scaling**
5. **Use compression for large datasets**

## Future Enhancements

### Planned Features

1. **Cloud Storage Backends**:
   - Amazon S3 with lifecycle policies
   - Azure Blob Storage
   - Google Cloud Storage

2. **Advanced Analytics**:
   - Character progression analysis
   - Usage pattern insights
   - Predictive caching

3. **Real-time Features**:
   - WebSocket support for live updates
   - Event-driven architecture
   - Change notifications

4. **Enhanced Security**:
   - Field-level encryption
   - Zero-trust architecture
   - Advanced audit trails

### Research Areas

1. **Advanced Compression**:
   - Character-specific compression algorithms
   - Delta compression for similar characters
   - Schema evolution handling

2. **Machine Learning**:
   - Automatic character classification
   - Anomaly detection in character data
   - Predictive character builds

3. **Distributed Storage**:
   - Sharding strategies
   - Geographic distribution
   - Edge caching