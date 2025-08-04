#!/usr/bin/env python3
"""
Enhanced Change Detection Integration Example

Demonstrates the integration between enhanced change detection service and change log service,
including causation analysis, detail level management, and error handling.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from discord.services.change_detection.models import DetectionContext
from src.services.enhanced_change_detection_service import EnhancedChangeDetectionService
from src.services.change_log_service import ChangeLogService
from src.models.enhanced_change_detection import ChangeDetectionConfig
from src.models.change_log import ChangeLogConfig


async def main():
    """Demonstrate enhanced change detection with logging integration."""
    
    print("Enhanced Change Detection Integration Example")
    print("=" * 50)
    
    # Setup temporary storage
    temp_dir = Path("temp_change_logs")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Configure change detection with logging enabled
        detection_config = ChangeDetectionConfig(
            enable_change_logging=True,
            change_log_storage_dir=str(temp_dir),
            enable_causation_analysis=True,
            change_log_retention_days=30
        )
        
        # Configure change log service
        log_config = ChangeLogConfig(
            storage_dir=temp_dir,
            enable_causation_analysis=True,
            enable_detailed_descriptions=True
        )
        
        # Create services
        change_log_service = ChangeLogService(log_config)
        enhanced_service = EnhancedChangeDetectionService(detection_config, change_log_service)
        
        print(f"✓ Services initialized")
        print(f"  - {len(enhanced_service.detectors)} detectors available")
        print(f"  - Change logging: {'enabled' if detection_config.enable_change_logging else 'disabled'}")
        print(f"  - Causation analysis: {'enabled' if detection_config.enable_causation_analysis else 'disabled'}")
        print()
        
        # Create sample character data
        character_id = 12345
        character_name = "Thorin Ironforge"
        
        old_character_data = {
            "character": {
                "character_info": {
                    "name": character_name,
                    "level": 5,
                    "classes": [{"name": "Fighter", "level": 5}]
                },
                "hit_points": {"maximum": 45, "current": 45},
                "ability_scores": {
                    "strength": 16,
                    "constitution": 15
                },
                "features": {
                    "feats": []
                }
            }
        }
        
        # Simulate character progression
        new_character_data = {
            "character": {
                "character_info": {
                    "name": character_name,
                    "level": 6,
                    "classes": [{"name": "Fighter", "level": 6}]
                },
                "hit_points": {"maximum": 52, "current": 52},  # +7 HP from level up
                "ability_scores": {
                    "strength": 18,  # Ability Score Improvement
                    "constitution": 15
                },
                "features": {
                    "feats": [{
                        "name": "Great Weapon Master",
                        "description": "You've learned to put the weight of a weapon to your advantage"
                    }]
                }
            }
        }
        
        # Create detection context
        context = DetectionContext(
            character_id=character_id,
            character_name=character_name,
            rule_version="2014"
        )
        
        print("Detecting and logging changes...")
        print(f"Character: {character_name} (ID: {character_id})")
        print(f"Level progression: 5 → 6")
        print(f"Strength improvement: 16 → 18")
        print(f"Added feat: Great Weapon Master")
        print()
        
        # Detect and log changes
        changes = await enhanced_service.detect_and_log_changes(
            character_id, old_character_data, new_character_data, context
        )
        
        print(f"✓ Detected {len(changes)} changes:")
        for i, change in enumerate(changes, 1):
            print(f"  {i}. {change.description}")
            print(f"     Field: {change.field_path}")
            print(f"     Priority: {change.priority.name}")
            print(f"     Category: {change.category.name}")
            if hasattr(change, 'metadata') and 'causation_analysis' in change.metadata:
                causation = change.metadata['causation_analysis']
                if causation['primary_causes']:
                    cause = causation['primary_causes'][0]
                    print(f"     Likely cause: {cause['type']}")
            print()
        
        # Format changes for Discord
        discord_changes = enhanced_service.format_changes_for_discord(changes)
        print("Discord notification format:")
        for change in discord_changes:
            print(f"  • {change['description']} [{change['priority']}]")
        print()
        
        # Retrieve change history
        print("Retrieving change history...")
        history = await enhanced_service.get_change_history(character_id, limit=10)
        
        print(f"✓ Found {len(history)} entries in change history:")
        for entry in history:
            timestamp = entry.get('timestamp', 'Unknown')
            description = entry.get('description', 'No description')
            print(f"  • {timestamp}: {description}")
        print()
        
        # Get service statistics
        stats = enhanced_service.get_statistics()
        print("Service Statistics:")
        print(f"  • Total detectors: {stats['total_detectors']}")
        print(f"  • Enabled detectors: {stats['enabled_detectors']}")
        print(f"  • Change logging: {'enabled' if stats['change_logging_enabled'] else 'disabled'}")
        print(f"  • Causation analysis: {'enabled' if stats['causation_analysis_enabled'] else 'disabled'}")
        print()
        
        # Demonstrate error handling
        print("Testing error handling...")
        
        # Simulate a logging error by corrupting the service temporarily
        original_log_service = enhanced_service.change_log_service
        enhanced_service.change_log_service = None
        
        # This should still detect changes even if logging fails
        error_test_changes = await enhanced_service.detect_and_log_changes(
            character_id, old_character_data, new_character_data, context
        )
        
        print(f"✓ Error handling test: detected {len(error_test_changes)} changes even with logging disabled")
        
        # Restore the service
        enhanced_service.change_log_service = original_log_service
        
        print()
        print("Integration example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in integration example: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            import shutil
            shutil.rmtree(temp_dir)
            print("✓ Temporary files cleaned up")
        except Exception as e:
            print(f"Warning: Could not clean up temporary files: {e}")


if __name__ == "__main__":
    asyncio.run(main())