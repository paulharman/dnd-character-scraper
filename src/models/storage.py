"""
Storage-specific data models and schemas.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import hashlib
import json


class CompressionType(str, Enum):
    """Supported compression types for storage."""
    NONE = "none"
    GZIP = "gzip"
    ZSTD = "zstd"
    LZ4 = "lz4"


class StorageMetadata(BaseModel):
    """Metadata for stored character data."""
    storage_version: str = Field(default="1.0.0")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    compression: CompressionType = CompressionType.NONE
    content_hash: Optional[str] = None
    content_size: int = 0
    user_id: Optional[str] = None
    campaign_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def calculate_hash(self, content: bytes) -> str:
        """Calculate SHA256 hash of content."""
        return hashlib.sha256(content).hexdigest()


class CharacterIndex(BaseModel):
    """Index entry for fast character lookups."""
    character_id: int
    character_name: str
    latest_version: int
    total_versions: int
    created_at: datetime
    last_modified: datetime
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    user_id: Optional[str] = None
    campaign_id: Optional[str] = None
    classes: List[str] = Field(default_factory=list)
    level: int
    is_deleted: bool = False
    
    # Denormalized fields for fast queries
    primary_class: Optional[str] = None
    species: Optional[str] = None
    rule_version: Optional[str] = None
    
    class Config:
        indexes = [
            "character_id",
            "character_name",
            "user_id",
            "campaign_id",
            "primary_class",
            "level",
            "last_modified"
        ]


class VersionMetadata(BaseModel):
    """Metadata for a specific character version."""
    character_id: int
    version: int
    timestamp: datetime
    change_summary: Optional[str] = None
    change_count: int = 0
    changed_fields: List[str] = Field(default_factory=list)
    data_size: int = 0
    compressed_size: Optional[int] = None
    compression: CompressionType = CompressionType.NONE
    checksum: Optional[str] = None
    user_id: Optional[str] = None
    
    # Delta storage optimization
    is_full_snapshot: bool = True
    base_version: Optional[int] = None  # For delta storage
    
    class Config:
        indexes = [
            "character_id",
            "version",
            "timestamp"
        ]


class CharacterRelationship(BaseModel):
    """Relationships between characters (party members, etc)."""
    source_character_id: int
    target_character_id: int
    relationship_type: str  # "party_member", "rival", "mentor", etc.
    campaign_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Campaign(BaseModel):
    """Campaign information for grouping characters."""
    campaign_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    owner_user_id: str
    member_user_ids: List[str] = Field(default_factory=list)
    character_ids: List[int] = Field(default_factory=list)
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class User(BaseModel):
    """User information for multi-user deployments."""
    user_id: str
    username: str
    email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_active: bool = True
    permissions: List[str] = Field(default_factory=list)
    character_ids: List[int] = Field(default_factory=list)
    campaign_ids: List[str] = Field(default_factory=list)
    storage_quota_mb: Optional[int] = None
    storage_used_mb: int = 0
    
    @field_validator('storage_used_mb')
    @classmethod
    def validate_storage_usage(cls, v, info):
        """Ensure storage usage doesn't exceed quota."""
        if hasattr(info, 'data') and 'storage_quota_mb' in info.data and info.data['storage_quota_mb']:
            if v > info.data['storage_quota_mb']:
                raise ValueError(f"Storage usage ({v}MB) exceeds quota ({info.data['storage_quota_mb']}MB)")
        return v


class RetentionPolicy(BaseModel):
    """Data retention policy configuration."""
    policy_id: str
    name: str
    description: Optional[str] = None
    
    # Version retention
    keep_all_for_days: int = Field(default=30, ge=1)
    keep_daily_for_days: int = Field(default=90, ge=1)
    keep_weekly_for_days: int = Field(default=365, ge=1)
    keep_monthly_forever: bool = True
    
    # Size-based retention
    max_versions_per_character: Optional[int] = Field(default=None, ge=1)
    max_total_size_mb: Optional[int] = Field(default=None, ge=1)
    
    # Archival settings
    archive_after_days: Optional[int] = Field(default=None, ge=1)
    archive_compression: CompressionType = CompressionType.ZSTD
    
    # GDPR compliance
    auto_delete_after_days: Optional[int] = Field(default=None, ge=1)
    anonymize_instead_of_delete: bool = False
    
    def should_keep_version(self, version_age_days: int, version_number: int) -> bool:
        """Determine if a version should be kept based on policy."""
        if version_age_days <= self.keep_all_for_days:
            return True
        
        if version_age_days <= self.keep_daily_for_days:
            # Keep one per day
            return version_number % 1 == 0  # Simplified; real implementation would check timestamps
            
        if version_age_days <= self.keep_weekly_for_days:
            # Keep one per week
            return version_number % 7 == 0  # Simplified
            
        if self.keep_monthly_forever:
            # Keep one per month
            return version_number % 30 == 0  # Simplified
            
        return False


class StorageStatistics(BaseModel):
    """Storage usage statistics."""
    total_characters: int = 0
    total_versions: int = 0
    total_size_bytes: int = 0
    compressed_size_bytes: int = 0
    
    # Breakdown by type
    characters_by_class: Dict[str, int] = Field(default_factory=dict)
    characters_by_level: Dict[int, int] = Field(default_factory=dict)
    characters_by_rule_version: Dict[str, int] = Field(default_factory=dict)
    
    # Performance metrics
    average_character_size_bytes: int = 0
    average_versions_per_character: float = 0.0
    compression_ratio: float = 1.0
    
    # Time-based metrics
    characters_created_today: int = 0
    characters_modified_today: int = 0
    most_active_hours: List[int] = Field(default_factory=list)  # 0-23
    
    # User metrics (for multi-user)
    total_users: int = 0
    active_users_today: int = 0
    
    def calculate_compression_ratio(self):
        """Calculate compression ratio."""
        if self.total_size_bytes > 0:
            self.compression_ratio = self.total_size_bytes / max(self.compressed_size_bytes, 1)


# Database Schema Definitions (for SQL backends)

SQL_SCHEMA_POSTGRES = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    permissions JSONB DEFAULT '[]'::jsonb,
    storage_quota_mb INTEGER,
    storage_used_mb INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    owner_user_id VARCHAR(255) REFERENCES users(user_id),
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Campaign members junction table
CREATE TABLE IF NOT EXISTS campaign_members (
    campaign_id VARCHAR(255) REFERENCES campaigns(campaign_id),
    user_id VARCHAR(255) REFERENCES users(user_id),
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    role VARCHAR(50) DEFAULT 'member',
    PRIMARY KEY (campaign_id, user_id)
);

-- Character index table
CREATE TABLE IF NOT EXISTS character_index (
    character_id BIGINT PRIMARY KEY,
    character_name VARCHAR(255) NOT NULL,
    latest_version INTEGER NOT NULL DEFAULT 1,
    total_versions INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    user_id VARCHAR(255) REFERENCES users(user_id),
    campaign_id VARCHAR(255) REFERENCES campaigns(campaign_id),
    classes JSONB DEFAULT '[]'::jsonb,
    level INTEGER NOT NULL,
    primary_class VARCHAR(100),
    species VARCHAR(100),
    rule_version VARCHAR(20),
    is_deleted BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for character_index
CREATE INDEX idx_character_name ON character_index(character_name);
CREATE INDEX idx_character_user ON character_index(user_id);
CREATE INDEX idx_character_campaign ON character_index(campaign_id);
CREATE INDEX idx_character_class ON character_index(primary_class);
CREATE INDEX idx_character_level ON character_index(level);
CREATE INDEX idx_character_modified ON character_index(last_modified DESC);

-- Character versions table
CREATE TABLE IF NOT EXISTS character_versions (
    character_id BIGINT,
    version INTEGER,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    change_summary TEXT,
    change_count INTEGER DEFAULT 0,
    changed_fields JSONB DEFAULT '[]'::jsonb,
    data_size INTEGER NOT NULL,
    compressed_size INTEGER,
    compression VARCHAR(20) DEFAULT 'none',
    checksum VARCHAR(64),
    user_id VARCHAR(255) REFERENCES users(user_id),
    is_full_snapshot BOOLEAN DEFAULT TRUE,
    base_version INTEGER,
    character_data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    PRIMARY KEY (character_id, version),
    FOREIGN KEY (character_id) REFERENCES character_index(character_id)
);

-- Indexes for character_versions
CREATE INDEX idx_version_timestamp ON character_versions(timestamp DESC);
CREATE INDEX idx_version_user ON character_versions(user_id);

-- Character relationships table
CREATE TABLE IF NOT EXISTS character_relationships (
    source_character_id BIGINT REFERENCES character_index(character_id),
    target_character_id BIGINT REFERENCES character_index(character_id),
    relationship_type VARCHAR(50) NOT NULL,
    campaign_id VARCHAR(255) REFERENCES campaigns(campaign_id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    PRIMARY KEY (source_character_id, target_character_id, relationship_type)
);

-- Archive table for old versions
CREATE TABLE IF NOT EXISTS character_archive (
    archive_id BIGSERIAL PRIMARY KEY,
    character_id BIGINT,
    version_range INT4RANGE,
    archived_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_blob BYTEA NOT NULL,
    compression VARCHAR(20) NOT NULL,
    checksum VARCHAR(64),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    log_id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(255),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255) NOT NULL,
    details JSONB DEFAULT '{}'::jsonb
);

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_modified_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for timestamp updates
CREATE TRIGGER update_campaign_timestamp BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_modified_timestamp();

CREATE TRIGGER update_character_timestamp BEFORE UPDATE ON character_index
    FOR EACH ROW EXECUTE FUNCTION update_modified_timestamp();
"""


SQL_SCHEMA_SQLITE = """
-- SQLite schema (simplified version for file-based storage)
CREATE TABLE IF NOT EXISTS character_index (
    character_id INTEGER PRIMARY KEY,
    character_name TEXT NOT NULL,
    latest_version INTEGER NOT NULL DEFAULT 1,
    total_versions INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    last_modified TEXT NOT NULL,
    last_accessed TEXT,
    access_count INTEGER DEFAULT 0,
    user_id TEXT,
    campaign_id TEXT,
    classes TEXT,  -- JSON string
    level INTEGER NOT NULL,
    primary_class TEXT,
    species TEXT,
    rule_version TEXT,
    is_deleted INTEGER DEFAULT 0,
    metadata TEXT  -- JSON string
);

CREATE TABLE IF NOT EXISTS character_versions (
    character_id INTEGER,
    version INTEGER,
    timestamp TEXT NOT NULL,
    change_summary TEXT,
    change_count INTEGER DEFAULT 0,
    changed_fields TEXT,  -- JSON string
    data_size INTEGER NOT NULL,
    compressed_size INTEGER,
    compression TEXT DEFAULT 'none',
    checksum TEXT,
    user_id TEXT,
    is_full_snapshot INTEGER DEFAULT 1,
    base_version INTEGER,
    character_data TEXT NOT NULL,  -- JSON string
    metadata TEXT,  -- JSON string
    PRIMARY KEY (character_id, version),
    FOREIGN KEY (character_id) REFERENCES character_index(character_id)
);

-- Create indexes
CREATE INDEX idx_character_name ON character_index(character_name);
CREATE INDEX idx_character_user ON character_index(user_id);
CREATE INDEX idx_character_modified ON character_index(last_modified DESC);
CREATE INDEX idx_version_timestamp ON character_versions(timestamp DESC);
"""