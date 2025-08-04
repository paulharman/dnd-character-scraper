# Change Log Compression Feature Plan

## Overview

The `changelog.enable_compression` configuration option is currently marked as a future feature. This document outlines the implementation plan, technical approach, and timeline for implementing change log compression.

## Current Status

- **Configuration**: ✅ Defined in `config/discord.yaml` 
- **Schema**: ✅ Defined in configuration models
- **Validation**: ✅ Configuration validation exists
- **Implementation**: ❌ Not implemented (marked as future feature)

## Business Justification

### Problem Statement
- Change logs can grow large over time, especially for active characters
- Large log files impact:
  - Storage space usage
  - File I/O performance
  - Backup/transfer times
  - Memory usage when loading logs

### Benefits of Compression
- **Storage Savings**: 60-80% reduction in file size (typical for JSON text)
- **Performance**: Faster file transfers and backups
- **Scalability**: Support for longer retention periods
- **Cost**: Reduced storage costs in cloud deployments

## Technical Design

### Compression Strategy

#### Option 1: File-Level Compression (Recommended)
```python
# Compress entire log files using gzip
import gzip
import json

def save_compressed_log(log_data: dict, file_path: Path):
    """Save log data with gzip compression."""
    with gzip.open(f"{file_path}.gz", 'wt', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)

def load_compressed_log(file_path: Path) -> dict:
    """Load compressed log data."""
    with gzip.open(f"{file_path}.gz", 'rt', encoding='utf-8') as f:
        return json.load(f)
```

#### Option 2: Entry-Level Compression
```python
# Compress individual log entries
import zlib
import base64

def compress_entry(entry: dict) -> str:
    """Compress a single log entry."""
    json_str = json.dumps(entry)
    compressed = zlib.compress(json_str.encode('utf-8'))
    return base64.b64encode(compressed).decode('ascii')
```

### Implementation Approach

#### Phase 1: Core Compression Infrastructure
1. **Compression Utilities**
   - Create `src/utils/compression.py` module
   - Support multiple compression algorithms (gzip, zlib, lz4)
   - Configurable compression levels

2. **Storage Layer Integration**
   - Modify `ChangeLogService` to support compressed storage
   - Transparent compression/decompression
   - Backward compatibility with uncompressed files

3. **Configuration Integration**
   - Respect `changelog.enable_compression` setting
   - Add compression algorithm selection
   - Add compression level configuration

#### Phase 2: Advanced Features
1. **Hybrid Compression**
   - Compress old log files, keep recent ones uncompressed
   - Configurable age threshold for compression

2. **Compression Migration**
   - Tool to compress existing uncompressed logs
   - Batch compression for historical data

3. **Performance Optimization**
   - Lazy decompression (only when needed)
   - Compression caching for frequently accessed files

### File Structure Changes

#### Current Structure
```
character_data/change_logs/
├── character_12345_changes.json
├── character_67890_changes.json
└── rotated/
    ├── character_12345_changes_2024-01.json
    └── character_12345_changes_2024-02.json
```

#### With Compression
```
character_data/change_logs/
├── character_12345_changes.json      # Current (uncompressed)
├── character_67890_changes.json      # Current (uncompressed)
└── rotated/
    ├── character_12345_changes_2024-01.json.gz  # Compressed
    ├── character_12345_changes_2024-02.json.gz  # Compressed
    └── metadata.json                             # Compression metadata
```

### Configuration Schema

#### Enhanced Configuration Options
```yaml
changelog:
  enable_compression: true
  compression:
    algorithm: "gzip"           # gzip, zlib, lz4
    level: 6                    # 1-9 (1=fast, 9=best compression)
    compress_after_days: 30     # Compress files older than X days
    compress_rotated_only: true # Only compress rotated files
    
  # Existing settings
  storage_dir: character_data/change_logs
  retention_days: 365
  rotation_size_mb: 10
```

### API Changes

#### ChangeLogService Modifications
```python
class ChangeLogService:
    def __init__(self, config: ChangeLogConfig):
        self.config = config
        self.compressor = CompressionManager(config.compression) if config.enable_compression else None
    
    async def _save_log_file(self, file_path: Path, log_file: ChangeLogFile):
        """Save log file with optional compression."""
        if self.compressor and self._should_compress(file_path):
            await self.compressor.save_compressed(file_path, log_file)
        else:
            # Existing uncompressed save logic
            await self._save_uncompressed(file_path, log_file)
    
    async def _load_log_file(self, file_path: Path) -> ChangeLogFile:
        """Load log file with automatic decompression."""
        if self.compressor and self._is_compressed(file_path):
            return await self.compressor.load_compressed(file_path)
        else:
            # Existing uncompressed load logic
            return await self._load_uncompressed(file_path)
```

### Performance Impact

#### Compression Performance
- **CPU Usage**: +10-20% during compression/decompression
- **Memory Usage**: +5-10% for compression buffers
- **I/O Performance**: 
  - Write: -20% (compression overhead)
  - Read: +30% (smaller files, faster I/O)

#### Storage Savings
- **JSON Text**: 70-80% size reduction
- **Typical Log File**: 10MB → 2-3MB
- **Annual Savings**: 500MB → 100-150MB per character

### Migration Strategy

#### Backward Compatibility
1. **Dual Support**: Support both compressed and uncompressed files
2. **Automatic Detection**: Detect file format automatically
3. **Gradual Migration**: Compress files as they're rotated
4. **Configuration Flag**: Allow disabling compression if needed

#### Migration Tools
```python
# Migration utility
async def migrate_to_compression(storage_dir: Path, dry_run: bool = True):
    """Migrate existing logs to compressed format."""
    for log_file in storage_dir.glob("*.json"):
        if not log_file.name.endswith('.gz'):
            compressed_size = await compress_file(log_file, dry_run)
            print(f"Compressed {log_file.name}: {log_file.stat().st_size} → {compressed_size} bytes")
```

## Implementation Timeline

### Phase 1: Foundation (2-3 weeks)
- [ ] Week 1: Compression utilities and core infrastructure
- [ ] Week 2: ChangeLogService integration
- [ ] Week 3: Configuration integration and testing

### Phase 2: Advanced Features (2-3 weeks)
- [ ] Week 4: Hybrid compression and migration tools
- [ ] Week 5: Performance optimization and caching
- [ ] Week 6: Documentation and user guides

### Phase 3: Production Readiness (1 week)
- [ ] Week 7: Production testing, monitoring, and deployment

**Total Estimated Timeline: 6-7 weeks**

## Testing Strategy

### Unit Tests
- Compression/decompression accuracy
- Performance benchmarks
- Error handling (corrupted files, etc.)
- Configuration validation

### Integration Tests
- End-to-end log storage and retrieval
- Migration from uncompressed to compressed
- Mixed compressed/uncompressed environments

### Performance Tests
- Compression ratio measurements
- CPU and memory usage profiling
- I/O performance comparison

## Risks and Mitigation

### Technical Risks
1. **Data Corruption**: Compressed files more susceptible to corruption
   - **Mitigation**: Checksums, backup strategies, validation
2. **Performance Impact**: Compression overhead
   - **Mitigation**: Configurable compression levels, selective compression
3. **Compatibility**: Breaking changes to log format
   - **Mitigation**: Backward compatibility, gradual migration

### Operational Risks
1. **Storage Migration**: Risk during migration process
   - **Mitigation**: Backup before migration, dry-run mode
2. **Debugging Difficulty**: Compressed logs harder to inspect
   - **Mitigation**: Decompression tools, debug modes

## Success Metrics

### Technical Metrics
- **Storage Reduction**: Target 70%+ reduction in log file sizes
- **Performance Impact**: <20% CPU overhead, <10% memory overhead
- **Reliability**: 99.9%+ compression/decompression success rate

### User Experience Metrics
- **Transparency**: Users shouldn't notice compression (except storage savings)
- **Configuration**: Simple on/off toggle with sensible defaults
- **Migration**: Seamless upgrade path from uncompressed logs

## Documentation Requirements

### User Documentation
- Configuration guide for compression settings
- Migration guide for existing installations
- Troubleshooting guide for compression issues

### Developer Documentation
- API documentation for compression utilities
- Architecture documentation for storage changes
- Performance tuning guide

## Future Enhancements

### Advanced Compression
- **Columnar Compression**: Compress similar fields together
- **Delta Compression**: Store only differences between log entries
- **Streaming Compression**: Compress logs as they're written

### Cloud Integration
- **Cloud Storage**: Direct compression for S3/Azure storage
- **CDN Integration**: Serve compressed logs via CDN
- **Backup Optimization**: Compressed backups for disaster recovery

## Conclusion

The change log compression feature represents a significant enhancement to the system's scalability and efficiency. The phased implementation approach ensures minimal risk while delivering substantial benefits.

**Recommendation**: Proceed with Phase 1 implementation, focusing on core compression infrastructure with backward compatibility as the top priority.

**Next Steps**:
1. Review and approve this implementation plan
2. Create detailed technical specifications for Phase 1
3. Begin implementation of compression utilities
4. Set up performance testing infrastructure

This feature will position the system for long-term scalability while maintaining the reliability and performance users expect.