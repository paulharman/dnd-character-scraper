#!/usr/bin/env python3
"""
Change Log Maintenance Example

Demonstrates how to use the change log maintenance functionality for
log rotation, cleanup, validation, and health monitoring.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta

from src.models.change_log import ChangeLogConfig
from src.services.change_log_maintenance import ChangeLogMaintenanceService
from src.services.change_log_service import ChangeLogService


async def main():
    """Demonstrate change log maintenance operations."""
    
    # Configuration
    config = ChangeLogConfig(
        storage_dir=Path("character_data/change_logs"),
        log_rotation_size_mb=10,
        log_retention_days=365,
        backup_old_logs=True,
        enable_causation_analysis=True,
        enable_detailed_descriptions=True
    )
    
    # Create services
    log_service = ChangeLogService(config)
    maintenance_service = ChangeLogMaintenanceService(config)
    
    print("=== Change Log Maintenance Example ===\n")
    
    # 1. Check Storage Health
    print("1. Checking storage health...")
    health_result = await maintenance_service.check_storage_health()
    
    print(f"   Status: {health_result['status'].upper()}")
    print(f"   Timestamp: {health_result['timestamp']}")
    
    if health_result.get('warnings'):
        print("   Warnings:")
        for warning in health_result['warnings']:
            print(f"     - {warning}")
    
    if health_result.get('errors'):
        print("   Errors:")
        for error in health_result['errors']:
            print(f"     - {error}")
    
    if health_result.get('recommendations'):
        print("   Recommendations:")
        for rec in health_result['recommendations']:
            print(f"     - {rec}")
    
    print()
    
    # 2. Get Storage Statistics
    print("2. Getting storage statistics...")
    storage_health = await log_service.get_storage_health()
    storage_stats = storage_health.get('storage_statistics', {})
    
    print(f"   Total characters: {storage_stats.get('total_characters', 0)}")
    print(f"   Total log files: {storage_stats.get('total_log_files', 0)}")
    print(f"   Total rotated files: {storage_stats.get('total_rotated_files', 0)}")
    print(f"   Total size: {storage_stats.get('total_size_mb', 0)} MB")
    print(f"   Largest file: {storage_stats.get('largest_file_mb', 0)} MB")
    
    if storage_stats.get('characters_needing_rotation'):
        print(f"   Characters needing rotation: {len(storage_stats['characters_needing_rotation'])}")
    
    print()
    
    # 3. Character-specific Statistics
    print("3. Getting character-specific statistics...")
    
    # Find a character with log data
    log_files = list(config.storage_dir.glob("character_*_changes.json"))
    if log_files:
        # Extract character ID from first log file
        filename = log_files[0].name
        if filename.startswith("character_") and filename.endswith("_changes.json"):
            character_id_str = filename[10:-12]  # Remove prefix and suffix
            try:
                character_id = int(character_id_str)
                
                char_stats = await log_service.get_log_statistics(character_id)
                print(f"   Character {character_id}:")
                print(f"     Total entries: {char_stats.get('total_entries', 0)}")
                print(f"     Total files: {char_stats.get('total_files', 0)}")
                print(f"     Size: {char_stats.get('total_size_mb', 0)} MB")
                
                if char_stats.get('oldest_entry'):
                    print(f"     Oldest entry: {char_stats['oldest_entry']}")
                if char_stats.get('newest_entry'):
                    print(f"     Newest entry: {char_stats['newest_entry']}")
                
                if char_stats.get('category_counts'):
                    print("     Change categories:")
                    for category, count in char_stats['category_counts'].items():
                        print(f"       {category}: {count}")
                
            except ValueError:
                print("   No valid character IDs found in log files")
    else:
        print("   No log files found")
    
    print()
    
    # 4. Log Rotation
    print("4. Checking for logs that need rotation...")
    rotation_result = await maintenance_service.rotate_oversized_logs()
    
    print(f"   Files checked: {rotation_result.get('files_checked', 0)}")
    print(f"   Files rotated: {rotation_result.get('files_rotated', 0)}")
    print(f"   Success: {rotation_result.get('success', False)}")
    
    if rotation_result.get('rotation_details'):
        print("   Rotation details:")
        for detail in rotation_result['rotation_details']:
            print(f"     Character {detail['character_id']}: {detail['original_size_mb']} MB -> rotated")
    
    if rotation_result.get('errors'):
        print("   Errors:")
        for error in rotation_result['errors']:
            print(f"     - {error}")
    
    print()
    
    # 5. Log Validation
    print("5. Validating log file integrity...")
    validation_result = await maintenance_service.validate_all_logs()
    
    print(f"   Files checked: {validation_result.get('files_checked', 0)}")
    print(f"   Files valid: {validation_result.get('files_valid', 0)}")
    print(f"   Files repaired: {validation_result.get('files_repaired', 0)}")
    print(f"   Files corrupted: {validation_result.get('files_corrupted', 0)}")
    print(f"   Success: {validation_result.get('success', False)}")
    
    if validation_result.get('validation_details'):
        print("   Validation details:")
        for detail in validation_result['validation_details']:
            if detail['status'] != 'valid':
                print(f"     {Path(detail['file']).name}: {detail['status']}")
                if detail.get('issues'):
                    for issue in detail['issues']:
                        print(f"       Issue: {issue}")
                if detail.get('repairs'):
                    for repair in detail['repairs']:
                        print(f"       Repair: {repair}")
    
    print()
    
    # 6. Log Cleanup
    print("6. Cleaning up expired logs...")
    cleanup_result = await maintenance_service.cleanup_expired_logs()
    
    print(f"   Files processed: {cleanup_result.get('files_processed', 0)}")
    print(f"   Files archived: {cleanup_result.get('files_archived', 0)}")
    print(f"   Files deleted: {cleanup_result.get('files_deleted', 0)}")
    print(f"   Space freed: {cleanup_result.get('space_freed_mb', 0)} MB")
    print(f"   Retention period: {cleanup_result.get('retention_days', 0)} days")
    print(f"   Success: {cleanup_result.get('success', False)}")
    
    print()
    
    # 7. Storage Optimization
    print("7. Optimizing storage structure...")
    optimization_result = await maintenance_service.optimize_storage()
    
    print(f"   Success: {optimization_result.get('success', False)}")
    print(f"   Space saved: {optimization_result.get('space_saved_mb', 0)} MB")
    
    if optimization_result.get('optimizations'):
        print("   Optimizations performed:")
        for optimization in optimization_result['optimizations']:
            op_name = optimization.get('operation', 'unknown')
            op_success = optimization.get('success', False)
            print(f"     {op_name}: {'✓' if op_success else '✗'}")
    
    print()
    
    # 8. Generate Maintenance Report
    print("8. Generating maintenance report...")
    report_result = await maintenance_service.generate_maintenance_report()
    
    print(f"   Success: {report_result.get('success', False)}")
    
    if report_result.get('report_file'):
        print(f"   Report saved to: {report_result['report_file']}")
        
        # Display report summary
        summary = report_result.get('summary', {})
        print(f"   Total characters: {summary.get('total_characters', 0)}")
        print(f"   Total log files: {summary.get('total_log_files', 0)}")
        print(f"   Total size: {summary.get('total_size_mb', 0)} MB")
        print(f"   Health status: {summary.get('health_status', 'unknown')}")
    
    print()
    
    # 9. Full Maintenance Cycle
    print("9. Running full maintenance cycle...")
    full_maintenance_result = await maintenance_service.run_scheduled_maintenance()
    
    summary = full_maintenance_result.get('summary', {})
    print(f"   Total operations: {summary.get('total_operations', 0)}")
    print(f"   Successful: {summary.get('successful_operations', 0)}")
    print(f"   Failed: {summary.get('failed_operations', 0)}")
    print(f"   Warnings: {summary.get('warnings', 0)}")
    
    if full_maintenance_result.get('operations'):
        print("   Operation results:")
        for op_name, op_result in full_maintenance_result['operations'].items():
            if isinstance(op_result, dict):
                status = "✓" if op_result.get('success', False) else "✗"
                print(f"     {op_name}: {status}")
            else:
                print(f"     {op_name}: {op_result}")
    
    print()
    
    # 10. Demonstrate Query Functionality
    print("10. Demonstrating change log queries...")
    
    if log_files:
        try:
            character_id = int(log_files[0].name[10:-12])
            
            # Get recent changes
            recent_changes = await log_service.get_change_history(
                character_id, 
                limit=5, 
                include_causation=True
            )
            
            print(f"   Recent changes for character {character_id}:")
            for change in recent_changes:
                print(f"     {change.timestamp.strftime('%Y-%m-%d %H:%M')} - {change.description}")
                if change.attribution:
                    print(f"       Caused by: {change.attribution.source_name} ({change.attribution.source_type})")
            
            # Get changes by cause (example)
            if recent_changes:
                sample_change = recent_changes[0]
                if sample_change.attribution:
                    cause_changes = await log_service.get_changes_by_cause(
                        character_id,
                        sample_change.attribution.source,
                        sample_change.attribution.source_name
                    )
                    
                    if cause_changes:
                        print(f"   Changes caused by {sample_change.attribution.source_name}:")
                        for change in cause_changes:
                            print(f"     - {change.description}")
        
        except (ValueError, IndexError):
            print("   Could not demonstrate queries - no valid character data found")
    
    print("\n=== Maintenance Example Complete ===")


if __name__ == "__main__":
    asyncio.run(main())