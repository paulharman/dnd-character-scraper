#!/usr/bin/env python3
"""
Shared snapshot archiving utility for the D&D Beyond scraper system.

Provides centralized archiving functionality that can be used by both
the parser and Discord monitor to manage character snapshot retention.
"""

import logging
from pathlib import Path
from typing import Optional
import yaml

logger = logging.getLogger(__name__)


class SnapshotArchiver:
    """
    Manages archiving of character snapshot files to maintain storage limits.
    
    Features:
    - Configurable snapshot retention limits
    - Automatic archive directory creation
    - Safe file moving with error handling
    - Supports multiple configuration sources
    """
    
    def __init__(self, max_snapshots: Optional[int] = None):
        """
        Initialize the snapshot archiver.

        Args:
            max_snapshots: Maximum snapshots to keep per character.
                          If None, will try to load from config files.
        """
        self._retention_config = self._load_retention_config()
        self.max_snapshots = max_snapshots if max_snapshots is not None else self._retention_config.get('max_per_character', 10)
        self.max_scraper_files = self._retention_config.get('max_scraper_files_per_character', 10)
        self.max_raw_files = self._retention_config.get('max_raw_files_per_character', 5)

    def _load_retention_config(self) -> dict:
        """
        Load snapshot retention settings from config/discord.yaml snapshots section.

        Returns:
            Dictionary with retention settings, using defaults if not found.
        """
        defaults = {
            'max_per_character': 10,
            'max_scraper_files_per_character': 10,
            'max_raw_files_per_character': 5,
        }

        project_root = Path(__file__).parent.parent.parent
        discord_yaml = project_root / "config" / "discord.yaml"

        if discord_yaml.exists():
            try:
                with open(discord_yaml, 'r') as f:
                    config = yaml.safe_load(f) or {}
                snapshots_config = config.get('snapshots', {})
                if snapshots_config:
                    result = {**defaults, **snapshots_config}
                    logger.debug(f"Loaded retention config from discord.yaml: {result}")
                    return result
            except Exception as e:
                logger.debug(f"Could not read discord.yaml: {e}")

        logger.debug(f"Using default retention config: {defaults}")
        return defaults
    
    def archive_old_snapshots(self, character_id: int, storage_dir: Path) -> int:
        """
        Archive old snapshots for a character, keeping only the most recent ones.
        
        Args:
            character_id: Character ID to archive snapshots for
            storage_dir: Directory containing character snapshots
            
        Returns:
            Number of snapshots archived
        """
        if self.max_snapshots <= 0:
            logger.debug(f"Archiving disabled (max_snapshots={self.max_snapshots})")
            return 0
        
        storage_dir = Path(storage_dir)
        if not storage_dir.exists():
            logger.warning(f"Storage directory does not exist: {storage_dir}")
            return 0
        
        try:
            # Find all snapshot files for this character
            pattern = f"character_{character_id}_*.json"
            snapshot_files = list(storage_dir.glob(pattern))
            
            if len(snapshot_files) <= self.max_snapshots:
                logger.debug(f"Character {character_id} has {len(snapshot_files)} snapshots, "
                           f"no archiving needed (max: {self.max_snapshots})")
                return 0
            
            # Sort by modification time (oldest first)
            snapshot_files.sort(key=lambda p: p.stat().st_mtime)
            
            # Determine which files to archive
            files_to_archive = snapshot_files[:-self.max_snapshots]
            
            if not files_to_archive:
                return 0
            
            # Create archive directory
            archive_dir = storage_dir / "archive"
            archive_dir.mkdir(exist_ok=True)
            
            # Move old files to archive
            archived_count = 0
            for file_path in files_to_archive:
                try:
                    archive_path = archive_dir / file_path.name
                    
                    # Handle duplicate names in archive
                    counter = 1
                    original_archive_path = archive_path
                    while archive_path.exists():
                        stem = original_archive_path.stem
                        suffix = original_archive_path.suffix
                        archive_path = archive_dir / f"{stem}_duplicate_{counter}{suffix}"
                        counter += 1
                    
                    file_path.rename(archive_path)
                    archived_count += 1
                    logger.debug(f"Archived {file_path.name} to {archive_path.name}")
                    
                except Exception as e:
                    logger.warning(f"Failed to archive {file_path.name}: {e}")
            
            if archived_count > 0:
                logger.info(f"Archived {archived_count} old snapshots for character {character_id} "
                           f"(keeping {self.max_snapshots} most recent)")
            
            return archived_count
            
        except Exception as e:
            logger.error(f"Error during snapshot archiving for character {character_id}: {e}")
            return 0
    
    def cleanup_scraper_files(self, character_id: int, project_root: Path) -> int:
        """
        Delete old scraper output files for a character, keeping only the most recent.

        Args:
            character_id: Character ID to clean up files for
            project_root: Project root directory

        Returns:
            Number of files deleted
        """
        deleted = 0
        scraper_dir = project_root / "character_data" / "scraper"
        raw_dir = scraper_dir / "raw"

        # Clean processed scraper files
        if self.max_scraper_files > 0 and scraper_dir.exists():
            deleted += self._delete_oldest_files(
                scraper_dir, f"character_{character_id}_*.json", self.max_scraper_files, "scraper"
            )

        # Clean raw API response files
        if self.max_raw_files > 0 and raw_dir.exists():
            deleted += self._delete_oldest_files(
                raw_dir, f"character_{character_id}_*_raw.json", self.max_raw_files, "raw"
            )

        return deleted

    def _delete_oldest_files(self, directory: Path, pattern: str, max_files: int, label: str) -> int:
        """Delete oldest files matching pattern, keeping max_files most recent."""
        files = list(directory.glob(pattern))
        if len(files) <= max_files:
            return 0

        files.sort(key=lambda p: p.stat().st_mtime)
        files_to_delete = files[:-max_files]
        deleted = 0

        for file_path in files_to_delete:
            try:
                file_path.unlink()
                deleted += 1
                logger.debug(f"Deleted old {label} file: {file_path.name}")
            except Exception as e:
                logger.warning(f"Failed to delete {file_path.name}: {e}")

        if deleted > 0:
            logger.info(f"Deleted {deleted} old {label} files (keeping {max_files} most recent)")

        return deleted

    def get_archive_stats(self, storage_dir: Path) -> dict:
        """
        Get statistics about archived and active snapshots.
        
        Args:
            storage_dir: Directory containing character snapshots
            
        Returns:
            Dictionary with archive statistics
        """
        storage_dir = Path(storage_dir)
        archive_dir = storage_dir / "archive"
        
        stats = {
            'active_snapshots': len(list(storage_dir.glob("character_*.json"))),
            'archived_snapshots': len(list(archive_dir.glob("character_*.json"))) if archive_dir.exists() else 0,
            'total_snapshots': 0,
            'max_snapshots_per_character': self.max_snapshots
        }
        
        stats['total_snapshots'] = stats['active_snapshots'] + stats['archived_snapshots']
        
        return stats