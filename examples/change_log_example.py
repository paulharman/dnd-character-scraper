#!/usr/bin/env python3
"""
Example demonstrating the Change Log Service functionality.

This script shows how to use the Change Log Service to track character changes
with detailed attribution and causation analysis.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from discord.services.change_detection.models import FieldChange, ChangeType, ChangePriority, ChangeCategory
from src.models.change_log import ChangeLogConfig
from src.services.change_log_service import ChangeLogService


async def main():
    """Demonstrate Change Log Service functionality."""
    print("🔍 Change Log Service Example")
    print("=" * 50)
    
    # Create service with example configuration
    config = ChangeLogConfig(
        storage_dir=Path("example_logs"),
        enable_causation_analysis=True,
        enable_detailed_descriptions=True,
        log_retention_days=90
    )
    
    service = ChangeLogService(config)
    print(f"✅ Initialized Change Log Service with storage at: {config.storage_dir}")
    
    # Example character data
    character_id = 143359582
    character_name = "Thorin Ironforge"
    
    # Simulate character progression: Level 4 Fighter gains Great Weapon Master feat
    old_character_data = {
        "character_info": {
            "name": character_name,
            "level": 4,
            "classes": [{"name": "Fighter", "level": 4}]
        },
        "abilities": {
            "ability_scores": {
                "strength": 15,
                "dexterity": 14,
                "constitution": 16
            }
        },
        "combat": {
            "hit_points": {"maximum": 32, "current": 32},
            "armor_class": {"total": 18}
        },
        "features": {
            "feats": []
        },
        "spellcasting": {
            "spell_slots_level_1": 0
        }
    }
    
    new_character_data = {
        "character_info": {
            "name": character_name,
            "level": 5,
            "classes": [{"name": "Fighter", "level": 5}]
        },
        "abilities": {
            "ability_scores": {
                "strength": 16,  # +1 from feat
                "dexterity": 14,
                "constitution": 16
            }
        },
        "combat": {
            "hit_points": {"maximum": 39, "current": 39},  # +7 from level up
            "armor_class": {"total": 18}
        },
        "features": {
            "feats": [
                {
                    "name": "Great Weapon Master",
                    "description": "You've learned to put the weight of a weapon to your advantage..."
                }
            ]
        },
        "spellcasting": {
            "spell_slots_level_1": 0
        }
    }
    
    # Create detected changes
    changes = [
        FieldChange(
            field_path="character_info.level",
            old_value=4,
            new_value=5,
            change_type=ChangeType.INCREMENTED,
            priority=ChangePriority.HIGH,
            category=ChangeCategory.PROGRESSION,
            description="Level increased from 4 to 5",
            detection_timestamp=datetime.now()
        ),
        FieldChange(
            field_path="features.feats.great_weapon_master",
            old_value=None,
            new_value={
                "name": "Great Weapon Master",
                "description": "You've learned to put the weight of a weapon to your advantage..."
            },
            change_type=ChangeType.ADDED,
            priority=ChangePriority.HIGH,
            category=ChangeCategory.FEATURES,
            description="Added feat: Great Weapon Master (level 4 feat choice)",
            detection_timestamp=datetime.now()
        ),
        FieldChange(
            field_path="abilities.ability_scores.strength",
            old_value=15,
            new_value=16,
            change_type=ChangeType.INCREMENTED,
            priority=ChangePriority.MEDIUM,
            category=ChangeCategory.ABILITIES,
            description="Strength increased from 15 to 16",
            detection_timestamp=datetime.now()
        ),
        FieldChange(
            field_path="combat.hit_points.maximum",
            old_value=32,
            new_value=39,
            change_type=ChangeType.INCREMENTED,
            priority=ChangePriority.MEDIUM,
            category=ChangeCategory.COMBAT,
            description="Maximum hit points increased from 32 to 39",
            detection_timestamp=datetime.now()
        )
    ]
    
    print(f"\n📝 Logging {len(changes)} changes for {character_name}...")
    
    # Log the changes with causation analysis
    success = await service.log_changes(
        character_id, 
        changes, 
        new_character_data, 
        old_character_data
    )
    
    if success:
        print("✅ Changes logged successfully!")
    else:
        print("❌ Failed to log changes")
        return
    
    # Demonstrate retrieving change history
    print(f"\n📚 Retrieving change history for {character_name}...")
    history = await service.get_change_history(character_id, include_causation=True)
    
    print(f"Found {len(history)} change entries:")
    for i, entry in enumerate(history, 1):
        print(f"\n{i}. {entry.description}")
        print(f"   Field: {entry.field_path}")
        print(f"   Change: {entry.old_value} → {entry.new_value}")
        print(f"   Priority: {entry.priority.name}")
        print(f"   Category: {entry.category.value}")
        
        if entry.attribution:
            print(f"   Attribution: {entry.attribution.impact_summary}")
            print(f"   Source: {entry.attribution.source_name} ({entry.attribution.source_type})")
        
        if entry.causation:
            print(f"   Causation: {entry.causation.trigger}")
            if entry.causation.trigger_details:
                details = ", ".join(f"{k}={v}" for k, v in entry.causation.trigger_details.items())
                print(f"   Details: {details}")
        
        if entry.detailed_description != entry.description:
            print(f"   Detailed: {entry.detailed_description}")
    
    # Demonstrate querying by specific cause
    print(f"\n🔍 Searching for changes caused by feats...")
    feat_changes = await service.get_changes_by_cause(character_id, "feat_selection", "Great Weapon Master")
    
    if feat_changes:
        print(f"Found {len(feat_changes)} changes caused by Great Weapon Master feat:")
        for change in feat_changes:
            print(f"  - {change.description}")
    else:
        print("No changes found with specific feat attribution (causation analysis may not have linked them)")
    
    # Show log statistics
    print(f"\n📊 Log Statistics for {character_name}:")
    stats = await service.get_log_statistics(character_id)
    
    print(f"  Total Entries: {stats['total_entries']}")
    print(f"  Total Files: {stats['total_files']}")
    print(f"  Storage Size: {stats['total_size_mb']} MB")
    print(f"  Storage File: {stats['storage_file']}")
    
    if stats['category_counts']:
        print("  Changes by Category:")
        for category, count in stats['category_counts'].items():
            print(f"    {category}: {count}")
    
    # Show the actual log file structure
    print(f"\n📁 Log File Structure:")
    log_files = service._get_character_log_files(character_id)
    for log_file in log_files:
        print(f"  {log_file}")
        
        # Show a snippet of the JSON structure
        with open(log_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"    Character: {data['character_name']}")
        print(f"    Entries: {data['total_entries']}")
        print(f"    Created: {data['created_at']}")
    
    print(f"\n🎉 Example completed! Check the '{config.storage_dir}' directory for generated log files.")


if __name__ == "__main__":
    asyncio.run(main())