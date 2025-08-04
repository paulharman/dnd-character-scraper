#!/usr/bin/env python3
"""
Change Log Maintenance Tool

Command-line utility for performing maintenance operations on change log storage.
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.change_log import ChangeLogConfig
from src.services.change_log_maintenance import ChangeLogMaintenanceService
from src.services.change_log_service import ChangeLogService


async def main():
    parser = argparse.ArgumentParser(description="Change Log Maintenance Tool")
    parser.add_argument("--storage-dir", type=str, default="character_data/change_logs",
                       help="Change log storage directory")
    parser.add_argument("--rotation-size", type=int, default=10,
                       help="Log rotation size in MB")
    parser.add_argument("--retention-days", type=int, default=365,
                       help="Log retention period in days")
    parser.add_argument("--backup-old-logs", action="store_true", default=True,
                       help="Archive old logs instead of deleting")
    
    # Operation selection
    operations = parser.add_mutually_exclusive_group(required=True)
    operations.add_argument("--health-check", action="store_true",
                           help="Check storage health")
    operations.add_argument("--rotate", action="store_true",
                           help="Rotate oversized logs")
    operations.add_argument("--cleanup", action="store_true",
                           help="Clean up expired logs")
    operations.add_argument("--validate", action="store_true",
                           help="Validate log file integrity")
    operations.add_argument("--optimize", action="store_true",
                           help="Optimize storage structure")
    operations.add_argument("--full-maintenance", action="store_true",
                           help="Run complete maintenance cycle")
    operations.add_argument("--report", action="store_true",
                           help="Generate maintenance report")
    operations.add_argument("--character-stats", type=int, metavar="CHARACTER_ID",
                           help="Get statistics for specific character")
    
    # Output options
    parser.add_argument("--output", type=str, choices=["json", "text"], default="text",
                       help="Output format")
    parser.add_argument("--output-file", type=str,
                       help="Save output to file")
    parser.add_argument("--verbose", action="store_true",
                       help="Verbose output")
    
    args = parser.parse_args()
    
    # Create configuration
    config = ChangeLogConfig(
        storage_dir=Path(args.storage_dir),
        log_rotation_size_mb=args.rotation_size,
        log_retention_days=args.retention_days,
        backup_old_logs=args.backup_old_logs
    )
    
    # Create maintenance service
    maintenance_service = ChangeLogMaintenanceService(config)
    log_service = ChangeLogService(config)
    
    # Execute requested operation
    result = None
    
    try:
        if args.health_check:
            result = await maintenance_service.check_storage_health()
            
        elif args.rotate:
            result = await maintenance_service.rotate_oversized_logs()
            
        elif args.cleanup:
            result = await maintenance_service.cleanup_expired_logs()
            
        elif args.validate:
            result = await maintenance_service.validate_all_logs()
            
        elif args.optimize:
            result = await maintenance_service.optimize_storage()
            
        elif args.full_maintenance:
            result = await maintenance_service.run_scheduled_maintenance()
            
        elif args.report:
            result = await maintenance_service.generate_maintenance_report()
            
        elif args.character_stats is not None:
            result = await log_service.get_log_statistics(args.character_stats)
            
        # Format and output result
        if args.output == "json":
            output = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            output = format_text_output(result, args.verbose)
        
        if args.output_file:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Output saved to {args.output_file}")
        else:
            print(output)
        
        # Exit with appropriate code
        if isinstance(result, dict):
            if result.get('success', True) and not result.get('error'):
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        error_result = {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        
        if args.output == "json":
            print(json.dumps(error_result, indent=2))
        else:
            print(f"Error: {e}")
        
        sys.exit(1)


def format_text_output(result: dict, verbose: bool = False) -> str:
    """Format result as human-readable text."""
    if not isinstance(result, dict):
        return str(result)
    
    output_lines = []
    
    # Handle different operation types
    if 'status' in result:  # Health check
        output_lines.append(f"Storage Health: {result['status'].upper()}")
        output_lines.append(f"Timestamp: {result.get('timestamp', 'Unknown')}")
        
        if result.get('errors'):
            output_lines.append("\nErrors:")
            for error in result['errors']:
                output_lines.append(f"  - {error}")
        
        if result.get('warnings'):
            output_lines.append("\nWarnings:")
            for warning in result['warnings']:
                output_lines.append(f"  - {warning}")
        
        if result.get('recommendations'):
            output_lines.append("\nRecommendations:")
            for rec in result['recommendations']:
                output_lines.append(f"  - {rec}")
        
        if verbose and result.get('checks'):
            output_lines.append("\nDetailed Checks:")
            for check_name, check_result in result['checks'].items():
                output_lines.append(f"  {check_name}: {check_result}")
    
    elif 'operations' in result:  # Full maintenance
        output_lines.append("Maintenance Results")
        output_lines.append(f"Timestamp: {result.get('timestamp', 'Unknown')}")
        
        summary = result.get('summary', {})
        output_lines.append(f"Operations: {summary.get('total_operations', 0)} total, "
                          f"{summary.get('successful_operations', 0)} successful, "
                          f"{summary.get('failed_operations', 0)} failed")
        
        if verbose:
            output_lines.append("\nOperation Details:")
            for op_name, op_result in result.get('operations', {}).items():
                output_lines.append(f"  {op_name}: {op_result.get('success', 'Unknown')}")
    
    elif 'files_rotated' in result:  # Rotation
        output_lines.append("Log Rotation Results")
        output_lines.append(f"Files checked: {result.get('files_checked', 0)}")
        output_lines.append(f"Files rotated: {result.get('files_rotated', 0)}")
        
        if result.get('errors'):
            output_lines.append(f"Errors: {len(result['errors'])}")
            if verbose:
                for error in result['errors']:
                    output_lines.append(f"  - {error}")
    
    elif 'files_archived' in result or 'files_deleted' in result:  # Cleanup
        output_lines.append("Log Cleanup Results")
        output_lines.append(f"Files processed: {result.get('files_processed', 0)}")
        output_lines.append(f"Files archived: {result.get('files_archived', 0)}")
        output_lines.append(f"Files deleted: {result.get('files_deleted', 0)}")
        output_lines.append(f"Space freed: {result.get('space_freed_mb', 0)} MB")
        output_lines.append(f"Retention period: {result.get('retention_days', 0)} days")
    
    elif 'files_valid' in result:  # Validation
        output_lines.append("Log Validation Results")
        output_lines.append(f"Files checked: {result.get('files_checked', 0)}")
        output_lines.append(f"Files valid: {result.get('files_valid', 0)}")
        output_lines.append(f"Files repaired: {result.get('files_repaired', 0)}")
        output_lines.append(f"Files corrupted: {result.get('files_corrupted', 0)}")
    
    elif 'character_id' in result and 'total_entries' in result:  # Character stats
        output_lines.append(f"Character {result['character_id']} Statistics")
        output_lines.append(f"Total entries: {result.get('total_entries', 0)}")
        output_lines.append(f"Total files: {result.get('total_files', 0)}")
        output_lines.append(f"Total size: {result.get('total_size_mb', 0)} MB")
        
        if result.get('oldest_entry'):
            output_lines.append(f"Oldest entry: {result['oldest_entry']}")
        if result.get('newest_entry'):
            output_lines.append(f"Newest entry: {result['newest_entry']}")
        
        if result.get('category_counts'):
            output_lines.append("\nChange Categories:")
            for category, count in result['category_counts'].items():
                output_lines.append(f"  {category}: {count}")
    
    else:
        # Generic output
        if result.get('error'):
            output_lines.append(f"Error: {result['error']}")
        else:
            output_lines.append("Operation completed")
            if result.get('timestamp'):
                output_lines.append(f"Timestamp: {result['timestamp']}")
    
    return "\n".join(output_lines)


if __name__ == "__main__":
    asyncio.run(main())