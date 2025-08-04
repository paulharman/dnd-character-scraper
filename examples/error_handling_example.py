"""
Error Handling Example

Demonstrates the error handling and recovery capabilities of the enhanced
Discord change tracking system.
"""

import asyncio
import logging
from pathlib import Path
from datetime import datetime

from src.services.enhanced_change_detection_service import EnhancedChangeDetectionService
from src.services.change_log_service import ChangeLogService
from src.services.error_handler import ErrorHandler, ErrorHandlerConfig
from src.utils.error_monitoring import ErrorMonitor
from src.models.enhanced_change_detection import ChangeDetectionConfig
from src.models.change_log import ChangeLogConfig
from discord.services.change_detection.models import DetectionContext
from tests.fixtures.characters import get_character_fixture

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demonstrate_error_handling():
    """Demonstrate various error handling scenarios."""
    
    print("=== Enhanced Discord Change Tracking - Error Handling Demo ===\n")
    
    # Setup configurations
    error_handler_config = ErrorHandlerConfig(
        error_log_path=Path("custom_logs/demo_error_log.json"),
        enable_monitoring=True,
        enable_alerting=False
    )
    
    change_log_config = ChangeLogConfig(
        storage_dir=Path("custom_logs/demo_change_logs"),
        enable_causation_analysis=True,
        enable_detailed_descriptions=True
    )
    
    detection_config = ChangeDetectionConfig(
        enabled_change_types={'feats', 'ability_scores', 'spells'},
        enable_causation_analysis=True,
        enable_change_logging=True
    )
    
    # Initialize services
    error_handler = ErrorHandler(error_handler_config)
    change_log_service = ChangeLogService(change_log_config, error_handler_config)
    enhanced_service = EnhancedChangeDetectionService(
        detection_config, change_log_service, error_handler_config
    )
    error_monitor = ErrorMonitor(error_handler)
    
    print("✓ Services initialized successfully\n")
    
    # Get test character data
    character_data = get_character_fixture("BASIC_FIGHTER")
    modified_character_data = character_data.copy()
    
    # Add a feat to create a change
    if 'character' not in modified_character_data:
        modified_character_data['character'] = {}
    if 'feats' not in modified_character_data['character']:
        modified_character_data['character']['feats'] = []
    
    modified_character_data['character']['feats'].append({
        'name': 'Great Weapon Master',
        'description': 'You can attack recklessly with heavy weapons'
    })
    
    context = DetectionContext(character_id=12345, character_name="Demo Character")
    
    # Scenario 1: Normal operation
    print("1. Testing normal operation...")
    try:
        changes = await enhanced_service.detect_and_log_changes(
            12345, character_data, modified_character_data, context
        )
        print(f"   ✓ Detected {len(changes)} changes successfully")
    except Exception as e:
        print(f"   ✗ Error in normal operation: {e}")
    
    # Scenario 2: Simulate detector failure
    print("\n2. Testing detector failure handling...")
    try:
        # Temporarily break a detector
        original_detect = enhanced_service.detectors['feats'].detect_changes
        enhanced_service.detectors['feats'].detect_changes = lambda *args: (_ for _ in ()).throw(ValueError("Simulated detector failure"))
        
        changes = enhanced_service.detect_changes(character_data, modified_character_data, context)
        print(f"   ✓ Graceful degradation: {len(changes)} changes from remaining detectors")
        
        # Restore detector
        enhanced_service.detectors['feats'].detect_changes = original_detect
        
    except Exception as e:
        print(f"   ✗ Error in detector failure test: {e}")
    
    # Scenario 3: Test malformed data handling
    print("\n3. Testing malformed data handling...")
    try:
        malformed_data = {
            'character_info': {'name': 'Test', 'level': 'invalid'},
            'ability_scores': {'strength': 'not_a_number'}
        }
        
        changes = await enhanced_service.detect_and_log_changes(
            12346, malformed_data, character_data, context
        )
        print(f"   ✓ Handled malformed data: {len(changes)} changes")
        
    except Exception as e:
        print(f"   ✗ Error in malformed data test: {e}")
    
    # Scenario 4: Simulate storage failure
    print("\n4. Testing storage failure with retry...")
    try:
        # This will be handled by the error handler's retry logic
        await error_handler.handle_storage_error(
            "demo_operation",
            IOError("Simulated storage failure"),
            character_id=12345,
            context={'demo': True}
        )
        print("   ✓ Storage error handled with retry logic")
        
    except Exception as e:
        print(f"   ✗ Error in storage failure test: {e}")
    
    # Generate error statistics and health report
    print("\n5. Generating error statistics and health report...")
    try:
        stats = error_handler.get_error_statistics(hours=1)
        health_report = error_monitor.generate_health_report(hours=1)
        
        print(f"   ✓ Total errors in last hour: {stats.get('total_errors', 0)}")
        print(f"   ✓ System health score: {health_report.get('overall_health_score', 'N/A')}/100")
        print(f"   ✓ System status: {health_report.get('system_status', 'unknown')}")
        
        # Show error breakdown by category
        error_categories = stats.get('errors_by_category', {})
        if error_categories:
            print("   ✓ Error breakdown by category:")
            for category, count in error_categories.items():
                print(f"     - {category}: {count}")
        
        # Show component health
        component_health = error_handler.get_component_health_status()
        healthy_components = len([c for c in component_health.values() if c['healthy']])
        total_components = len(component_health)
        print(f"   ✓ Component health: {healthy_components}/{total_components} healthy")
        
    except Exception as e:
        print(f"   ✗ Error generating statistics: {e}")
    
    # Check alert conditions
    print("\n6. Checking alert conditions...")
    try:
        alerts = error_monitor.check_alert_conditions()
        if alerts:
            print(f"   ⚠ {len(alerts)} alert conditions detected:")
            for alert in alerts:
                print(f"     - {alert['type']}: {alert['message']}")
        else:
            print("   ✓ No alert conditions detected")
        
    except Exception as e:
        print(f"   ✗ Error checking alerts: {e}")
    
    # Export comprehensive error report
    print("\n7. Exporting error report...")
    try:
        report_path = Path("custom_logs/demo_error_report.json")
        success = error_monitor.export_error_report(report_path, hours=1)
        
        if success:
            print(f"   ✓ Error report exported to: {report_path}")
        else:
            print("   ✗ Failed to export error report")
        
    except Exception as e:
        print(f"   ✗ Error exporting report: {e}")
    
    # Cleanup old errors (demo with very short retention)
    print("\n8. Testing error cleanup...")
    try:
        cleaned_count = await error_handler.cleanup_old_errors(retention_days=0)  # Clean all for demo
        print(f"   ✓ Cleaned up {cleaned_count} old error records")
        
    except Exception as e:
        print(f"   ✗ Error in cleanup: {e}")
    
    print("\n=== Error Handling Demo Complete ===")
    print("\nKey Features Demonstrated:")
    print("• Graceful degradation when detectors fail")
    print("• Malformed data sanitization and recovery")
    print("• Storage failure retry logic with exponential backoff")
    print("• Comprehensive error monitoring and statistics")
    print("• Health scoring and alert condition detection")
    print("• Error pattern analysis and trending")
    print("• Automated error cleanup and retention policies")
    
    # Show final system health
    final_health = error_monitor.generate_health_report(hours=1)
    print(f"\nFinal System Health Score: {final_health.get('overall_health_score', 'N/A')}/100")


if __name__ == "__main__":
    asyncio.run(demonstrate_error_handling())