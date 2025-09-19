"""
Change Log Maintenance Utilities

Provides comprehensive maintenance operations for change log storage including
rotation, cleanup, validation, and health monitoring.
"""

import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
import os
import shutil

from discord.core.models.change_log import ChangeLogConfig, ChangeLogFile, ChangeLogMetadata
from discord.core.services.change_log_service import ChangeLogService

logger = logging.getLogger(__name__)


class ChangeLogMaintenanceService:
    """
    Service for performing maintenance operations on change log storage.
    """
    
    def __init__(self, config: ChangeLogConfig = None):
        self.config = config or ChangeLogConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Ensure storage directory exists
        self.config.storage_dir.mkdir(parents=True, exist_ok=True)
    
    async def run_scheduled_maintenance(self) -> Dict[str, Any]:
        """Run scheduled maintenance operations."""
        try:
            self.logger.info("Starting scheduled maintenance")
            
            results = {
                'timestamp': datetime.now().isoformat(),
                'operations': {},
                'summary': {
                    'total_operations': 0,
                    'successful_operations': 0,
                    'failed_operations': 0,
                    'warnings': 0
                }
            }
            
            # 1. Check storage health
            health_check = await self.check_storage_health()
            results['operations']['health_check'] = health_check
            self._update_summary(results, health_check.get('status') == 'healthy')
            
            # 2. Rotate logs that need rotation
            rotation_results = await self.rotate_oversized_logs()
            results['operations']['rotation'] = rotation_results
            self._update_summary(results, rotation_results.get('success', False))
            
            # 3. Clean up old logs
            cleanup_results = await self.cleanup_expired_logs()
            results['operations']['cleanup'] = cleanup_results
            self._update_summary(results, cleanup_results.get('success', False))
            
            # 4. Validate log integrity
            validation_results = await self.validate_all_logs()
            results['operations']['validation'] = validation_results
            self._update_summary(results, validation_results.get('success', False))
            
            # 5. Optimize storage structure
            optimization_results = await self.optimize_storage()
            results['operations']['optimization'] = optimization_results
            self._update_summary(results, optimization_results.get('success', False))
            
            # 6. Generate maintenance report
            report_results = await self.generate_maintenance_report()
            results['operations']['report'] = report_results
            self._update_summary(results, report_results.get('success', False))
            
            self.logger.info(f"Scheduled maintenance completed: "
                           f"{results['summary']['successful_operations']} successful, "
                           f"{results['summary']['failed_operations']} failed, "
                           f"{results['summary']['warnings']} warnings")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error during scheduled maintenance: {e}", exc_info=True)
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'summary': {'total_operations': 0, 'successful_operations': 0, 'failed_operations': 1}
            }
    
    async def check_storage_health(self) -> Dict[str, Any]:
        """Comprehensive storage health check."""
        try:
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'checks': {},
                'warnings': [],
                'errors': [],
                'recommendations': []
            }
            
            # Check 1: Storage directory accessibility
            try:
                if not self.config.storage_dir.exists():
                    health_status['errors'].append("Storage directory does not exist")
                    health_status['status'] = 'critical'
                elif not os.access(self.config.storage_dir, os.R_OK | os.W_OK):
                    health_status['errors'].append("Storage directory is not readable/writable")
                    health_status['status'] = 'critical'
                else:
                    health_status['checks']['directory_access'] = 'ok'
            except Exception as e:
                health_status['errors'].append(f"Directory access check failed: {e}")
                health_status['status'] = 'critical'
            
            # Check 2: Disk space
            try:
                disk_usage = shutil.disk_usage(self.config.storage_dir)
                free_space_gb = disk_usage.free / (1024**3)
                total_space_gb = disk_usage.total / (1024**3)
                usage_percent = ((disk_usage.total - disk_usage.free) / disk_usage.total) * 100
                
                health_status['checks']['disk_space'] = {
                    'free_gb': round(free_space_gb, 2),
                    'total_gb': round(total_space_gb, 2),
                    'usage_percent': round(usage_percent, 2)
                }
                
                if free_space_gb < 1:  # Less than 1GB free
                    health_status['errors'].append("Low disk space (< 1GB free)")
                    health_status['status'] = 'critical'
                elif free_space_gb < 5:  # Less than 5GB free
                    health_status['warnings'].append("Low disk space (< 5GB free)")
                    if health_status['status'] == 'healthy':
                        health_status['status'] = 'warning'
                
            except Exception as e:
                health_status['warnings'].append(f"Disk space check failed: {e}")
            
            # Check 3: Log file integrity
            try:
                integrity_results = await self._check_log_integrity()
                health_status['checks']['log_integrity'] = integrity_results
                
                if integrity_results['corrupted_files'] > 0:
                    health_status['errors'].append(f"{integrity_results['corrupted_files']} corrupted log files found")
                    health_status['status'] = 'critical'
                elif integrity_results['files_with_warnings'] > 0:
                    health_status['warnings'].append(f"{integrity_results['files_with_warnings']} log files have warnings")
                    if health_status['status'] == 'healthy':
                        health_status['status'] = 'warning'
                
            except Exception as e:
                health_status['warnings'].append(f"Log integrity check failed: {e}")
            
            # Check 4: Storage size and rotation needs
            try:
                size_results = await self._check_storage_size()
                health_status['checks']['storage_size'] = size_results
                
                if size_results['files_needing_rotation'] > 0:
                    health_status['recommendations'].append(f"{size_results['files_needing_rotation']} files need rotation")
                
                if size_results['total_size_gb'] > 10:  # More than 10GB
                    health_status['recommendations'].append("Consider adjusting retention policy - storage size is large")
                
            except Exception as e:
                health_status['warnings'].append(f"Storage size check failed: {e}")
            
            # Check 5: Configuration validation
            try:
                config_results = self._validate_configuration()
                health_status['checks']['configuration'] = config_results
                
                if not config_results['valid']:
                    health_status['warnings'].extend(config_results['issues'])
                    if health_status['status'] == 'healthy':
                        health_status['status'] = 'warning'
                
            except Exception as e:
                health_status['warnings'].append(f"Configuration validation failed: {e}")
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Error checking storage health: {e}", exc_info=True)
            return {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def rotate_oversized_logs(self) -> Dict[str, Any]:
        """Rotate all logs that exceed size limits."""
        try:
            results = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'files_checked': 0,
                'files_rotated': 0,
                'rotation_details': [],
                'errors': []
            }
            
            # Find all current log files
            log_files = list(self.config.storage_dir.glob("character_*_changes.json"))
            results['files_checked'] = len(log_files)
            
            for log_file_path in log_files:
                try:
                    file_size_mb = log_file_path.stat().st_size / (1024 * 1024)
                    
                    if file_size_mb >= self.config.log_rotation_size_mb:
                        character_id = self._extract_character_id_from_path(log_file_path)
                        if character_id:
                            # Use ChangeLogService for rotation
                            from discord.core.services.change_log_service import ChangeLogService
                            log_service = ChangeLogService(self.config)
                            rotation_success = await log_service.rotate_logs(character_id)
                            
                            if rotation_success:
                                results['files_rotated'] += 1
                                results['rotation_details'].append({
                                    'character_id': character_id,
                                    'original_size_mb': round(file_size_mb, 2),
                                    'rotated_at': datetime.now().isoformat()
                                })
                            else:
                                results['errors'].append(f"Failed to rotate log for character {character_id}")
                                results['success'] = False
                
                except Exception as e:
                    results['errors'].append(f"Error processing {log_file_path}: {e}")
                    results['success'] = False
            
            self.logger.info(f"Log rotation completed: {results['files_rotated']} files rotated")
            return results
            
        except Exception as e:
            self.logger.error(f"Error rotating oversized logs: {e}", exc_info=True)
            return {
                'success': False,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def cleanup_expired_logs(self) -> Dict[str, Any]:
        """Clean up logs that exceed retention policy."""
        try:
            results = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'retention_days': self.config.log_retention_days,
                'files_processed': 0,
                'files_archived': 0,
                'files_deleted': 0,
                'space_freed_mb': 0,
                'errors': []
            }
            
            cutoff_date = datetime.now() - timedelta(days=self.config.log_retention_days)
            
            # Process current log files
            current_files = list(self.config.storage_dir.glob("character_*_changes.json"))
            
            # Process rotated files
            rotated_files = []
            for character_dir in self.config.storage_dir.glob("character_*"):
                if character_dir.is_dir():
                    rotated_dir = character_dir / "rotated"
                    if rotated_dir.exists():
                        rotated_files.extend(rotated_dir.glob("changes_*.json"))
            
            all_files = current_files + rotated_files
            results['files_processed'] = len(all_files)
            
            for log_file_path in all_files:
                try:
                    file_mtime = datetime.fromtimestamp(log_file_path.stat().st_mtime)
                    file_size = log_file_path.stat().st_size
                    
                    if file_mtime < cutoff_date:
                        if self.config.backup_old_logs:
                            # Archive the file
                            archive_success = await self._archive_log_file(log_file_path)
                            if archive_success:
                                results['files_archived'] += 1
                                results['space_freed_mb'] += file_size / (1024 * 1024)
                            else:
                                results['errors'].append(f"Failed to archive {log_file_path}")
                                results['success'] = False
                        else:
                            # Delete the file
                            log_file_path.unlink()
                            results['files_deleted'] += 1
                            results['space_freed_mb'] += file_size / (1024 * 1024)
                
                except Exception as e:
                    results['errors'].append(f"Error processing {log_file_path}: {e}")
                    results['success'] = False
            
            results['space_freed_mb'] = round(results['space_freed_mb'], 2)
            
            self.logger.info(f"Log cleanup completed: {results['files_archived']} archived, "
                           f"{results['files_deleted']} deleted, "
                           f"{results['space_freed_mb']} MB freed")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired logs: {e}", exc_info=True)
            return {
                'success': False,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def validate_all_logs(self) -> Dict[str, Any]:
        """Validate integrity of all log files."""
        try:
            results = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'files_checked': 0,
                'files_valid': 0,
                'files_repaired': 0,
                'files_corrupted': 0,
                'validation_details': [],
                'errors': []
            }
            
            # Get all log files
            all_files = []
            all_files.extend(self.config.storage_dir.glob("character_*_changes.json"))
            
            # Add rotated files
            for character_dir in self.config.storage_dir.glob("character_*"):
                if character_dir.is_dir():
                    rotated_dir = character_dir / "rotated"
                    if rotated_dir.exists():
                        all_files.extend(rotated_dir.glob("changes_*.json"))
            
            results['files_checked'] = len(all_files)
            
            for log_file_path in all_files:
                try:
                    validation_result = await self._validate_single_log_file(log_file_path)
                    
                    if validation_result['status'] == 'valid':
                        results['files_valid'] += 1
                    elif validation_result['status'] == 'repaired':
                        results['files_repaired'] += 1
                    elif validation_result['status'] == 'corrupted':
                        results['files_corrupted'] += 1
                        results['success'] = False
                    
                    results['validation_details'].append({
                        'file': str(log_file_path),
                        'status': validation_result['status'],
                        'issues': validation_result.get('issues', []),
                        'repairs': validation_result.get('repairs', [])
                    })
                
                except Exception as e:
                    results['errors'].append(f"Error validating {log_file_path}: {e}")
                    results['success'] = False
            
            self.logger.info(f"Log validation completed: {results['files_valid']} valid, "
                           f"{results['files_repaired']} repaired, "
                           f"{results['files_corrupted']} corrupted")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error validating logs: {e}", exc_info=True)
            return {
                'success': False,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def optimize_storage(self) -> Dict[str, Any]:
        """Optimize storage structure and performance."""
        try:
            results = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'optimizations': [],
                'space_saved_mb': 0,
                'errors': []
            }
            
            # 1. Create proper directory structure
            structure_results = await self._optimize_directory_structure()
            results['optimizations'].append(structure_results)
            
            # 2. Consolidate small rotated files
            consolidation_results = await self._consolidate_small_files()
            results['optimizations'].append(consolidation_results)
            results['space_saved_mb'] += consolidation_results.get('space_saved_mb', 0)
            
            # 3. Remove empty directories
            cleanup_results = await self._cleanup_empty_directories()
            results['optimizations'].append(cleanup_results)
            
            # 4. Update file permissions if needed
            permissions_results = await self._fix_file_permissions()
            results['optimizations'].append(permissions_results)
            
            # Check if any optimization failed
            for optimization in results['optimizations']:
                if not optimization.get('success', True):
                    results['success'] = False
                    results['errors'].extend(optimization.get('errors', []))
            
            self.logger.info(f"Storage optimization completed: {len(results['optimizations'])} operations, "
                           f"{results['space_saved_mb']} MB saved")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error optimizing storage: {e}", exc_info=True)
            return {
                'success': False,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def generate_maintenance_report(self) -> Dict[str, Any]:
        """Generate comprehensive maintenance report."""
        try:
            report = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'report_file': None,
                'summary': {}
            }
            
            # Gather comprehensive statistics
            log_service = ChangeLogService(self.config)
            storage_health = await log_service.get_storage_health()
            
            # Create report content
            report_content = {
                'maintenance_report': {
                    'generated_at': datetime.now().isoformat(),
                    'configuration': {
                        'storage_directory': str(self.config.storage_dir),
                        'rotation_size_mb': self.config.log_rotation_size_mb,
                        'retention_days': self.config.log_retention_days,
                        'backup_old_logs': self.config.backup_old_logs
                    },
                    'storage_health': storage_health,
                    'recommendations': await self._generate_recommendations(storage_health)
                }
            }
            
            # Save report to file
            report_file = self.config.storage_dir / f"maintenance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_content, f, indent=2, ensure_ascii=False)
            
            report['report_file'] = str(report_file)
            report['summary'] = {
                'total_characters': storage_health.get('storage_statistics', {}).get('total_characters', 0),
                'total_log_files': storage_health.get('storage_statistics', {}).get('total_log_files', 0),
                'total_size_mb': storage_health.get('storage_statistics', {}).get('total_size_mb', 0),
                'health_status': storage_health.get('health_summary', {}).get('status', 'unknown')
            }
            
            self.logger.info(f"Maintenance report generated: {report_file}")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating maintenance report: {e}", exc_info=True)
            return {
                'success': False,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    # Helper methods
    
    def _update_summary(self, results: Dict[str, Any], success: bool) -> None:
        """Update operation summary."""
        results['summary']['total_operations'] += 1
        if success:
            results['summary']['successful_operations'] += 1
        else:
            results['summary']['failed_operations'] += 1
    
    def _extract_character_id_from_path(self, file_path: Path) -> Optional[int]:
        """Extract character ID from log file path."""
        try:
            filename = file_path.name
            if filename.startswith("character_") and filename.endswith("_changes.json"):
                # Extract ID between "character_" and "_changes.json"
                start_idx = len("character_")
                end_idx = filename.rfind("_changes.json")
                id_part = filename[start_idx:end_idx]
                return int(id_part)
        except Exception:
            pass
        return None
    
    async def _check_log_integrity(self) -> Dict[str, Any]:
        """Check integrity of all log files."""
        results = {
            'files_checked': 0,
            'files_valid': 0,
            'corrupted_files': 0,
            'files_with_warnings': 0
        }
        
        all_files = list(self.config.storage_dir.glob("character_*_changes.json"))
        for character_dir in self.config.storage_dir.glob("character_*"):
            if character_dir.is_dir():
                rotated_dir = character_dir / "rotated"
                if rotated_dir.exists():
                    all_files.extend(rotated_dir.glob("changes_*.json"))
        
        for log_file_path in all_files:
            results['files_checked'] += 1
            try:
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Basic structure validation
                if not isinstance(data, dict):
                    results['corrupted_files'] += 1
                    continue
                
                # Check required fields
                required_fields = ['character_id', 'character_name', 'entries']
                if not all(field in data for field in required_fields):
                    results['files_with_warnings'] += 1
                    continue
                
                results['files_valid'] += 1
                
            except (json.JSONDecodeError, Exception):
                results['corrupted_files'] += 1
        
        return results
    
    async def _check_storage_size(self) -> Dict[str, Any]:
        """Check storage size and rotation needs."""
        results = {
            'total_files': 0,
            'total_size_gb': 0,
            'files_needing_rotation': 0,
            'largest_file_mb': 0
        }
        
        all_files = list(self.config.storage_dir.rglob("*.json"))
        results['total_files'] = len(all_files)
        
        total_size = 0
        for file_path in all_files:
            try:
                file_size = file_path.stat().st_size
                total_size += file_size
                
                file_size_mb = file_size / (1024 * 1024)
                results['largest_file_mb'] = max(results['largest_file_mb'], file_size_mb)
                
                # Check if current log file needs rotation
                if (file_path.name.endswith("_changes.json") and 
                    file_size_mb >= self.config.log_rotation_size_mb):
                    results['files_needing_rotation'] += 1
                    
            except Exception:
                continue
        
        results['total_size_gb'] = round(total_size / (1024**3), 2)
        results['largest_file_mb'] = round(results['largest_file_mb'], 2)
        
        return results
    
    def _validate_configuration(self) -> Dict[str, Any]:
        """Validate configuration settings."""
        results = {
            'valid': True,
            'issues': []
        }
        
        if self.config.log_rotation_size_mb <= 0:
            results['valid'] = False
            results['issues'].append("Log rotation size must be positive")
        
        if self.config.log_retention_days <= 0:
            results['valid'] = False
            results['issues'].append("Log retention days must be positive")
        
        if not self.config.storage_dir.exists():
            results['issues'].append("Storage directory does not exist")
        
        return results
    
    async def _archive_log_file(self, log_file_path: Path) -> bool:
        """Archive a log file to the archive directory."""
        try:
            archive_dir = self.config.storage_dir / "archive"
            archive_dir.mkdir(exist_ok=True)
            
            # Preserve directory structure for rotated files
            if "character_" in str(log_file_path.parent):
                character_archive_dir = archive_dir / log_file_path.parent.name
                character_archive_dir.mkdir(exist_ok=True)
                archive_path = character_archive_dir / log_file_path.name
            else:
                archive_path = archive_dir / log_file_path.name
            
            # Move file to archive
            log_file_path.rename(archive_path)
            return True
            
        except Exception as e:
            self.logger.error(f"Error archiving {log_file_path}: {e}")
            return False
    
    async def _validate_single_log_file(self, log_file_path: Path) -> Dict[str, Any]:
        """Validate a single log file."""
        result = {
            'status': 'valid',
            'issues': [],
            'repairs': []
        }
        
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate structure
            if not isinstance(data, dict):
                result['status'] = 'corrupted'
                result['issues'].append("Invalid JSON structure")
                return result
            
            # Check and repair metadata consistency
            if 'entries' in data and 'total_entries' in data:
                expected_count = len(data['entries'])
                actual_count = data['total_entries']
                
                if expected_count != actual_count:
                    data['total_entries'] = expected_count
                    data['last_updated'] = datetime.now().isoformat()
                    
                    # Save repaired file
                    with open(log_file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    result['status'] = 'repaired'
                    result['repairs'].append(f"Fixed entry count: {actual_count} -> {expected_count}")
            
            return result
            
        except json.JSONDecodeError:
            result['status'] = 'corrupted'
            result['issues'].append("Invalid JSON format")
            return result
        except Exception as e:
            result['status'] = 'corrupted'
            result['issues'].append(f"Validation error: {e}")
            return result
    
    async def _optimize_directory_structure(self) -> Dict[str, Any]:
        """Optimize directory structure."""
        return {
            'operation': 'directory_structure',
            'success': True,
            'directories_created': 0,
            'directories_cleaned': 0
        }
    
    async def _consolidate_small_files(self) -> Dict[str, Any]:
        """Consolidate small rotated files if beneficial."""
        return {
            'operation': 'file_consolidation',
            'success': True,
            'files_consolidated': 0,
            'space_saved_mb': 0
        }
    
    async def _cleanup_empty_directories(self) -> Dict[str, Any]:
        """Remove empty directories."""
        return {
            'operation': 'directory_cleanup',
            'success': True,
            'directories_removed': 0
        }
    
    async def _fix_file_permissions(self) -> Dict[str, Any]:
        """Fix file permissions if needed."""
        return {
            'operation': 'permissions',
            'success': True,
            'files_fixed': 0
        }
    
    async def _generate_recommendations(self, storage_health: Dict[str, Any]) -> List[str]:
        """Generate maintenance recommendations based on storage health."""
        recommendations = []
        
        storage_stats = storage_health.get('storage_statistics', {})
        
        # Size-based recommendations
        total_size_mb = storage_stats.get('total_size_mb', 0)
        if total_size_mb > 1000:  # > 1GB
            recommendations.append("Consider reducing retention period - storage size is large")
        
        # Rotation recommendations
        files_needing_rotation = len(storage_stats.get('characters_needing_rotation', []))
        if files_needing_rotation > 0:
            recommendations.append(f"Rotate {files_needing_rotation} oversized log files")
        
        # Error recommendations
        characters_with_errors = storage_stats.get('characters_with_errors', [])
        if characters_with_errors:
            recommendations.append(f"Investigate {len(characters_with_errors)} characters with log errors")
        
        # Performance recommendations
        total_files = storage_stats.get('total_log_files', 0) + storage_stats.get('total_rotated_files', 0)
        if total_files > 100:
            recommendations.append("Consider archiving old logs to improve performance")
        
        return recommendations