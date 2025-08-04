"""
Change Log Query Interface Example

Demonstrates comprehensive querying, filtering, and analysis capabilities
for character change logs with causation details.
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.change_log_service import ChangeLogService
from src.services.change_log_query_interface import (
    ChangeLogQueryInterface, QueryOptions, QueryFilter, QueryOperator, 
    SortOrder
)
from src.models.change_log import ChangeLogConfig
from discord.services.change_detection.models import (
    FieldChange, ChangeCategory, ChangePriority, ChangeType
)


async def main():
    """Demonstrate change log query interface functionality."""
    print("=== Change Log Query Interface Example ===\n")
    
    # Setup
    config = ChangeLogConfig(
        storage_dir=Path("example_logs"),
        enable_causation_analysis=True,
        enable_detailed_descriptions=True
    )
    
    change_log_service = ChangeLogService(config)
    query_interface = ChangeLogQueryInterface(change_log_service)
    
    character_id = 143359582
    character_data = {
        "character_info": {"name": "Thorin Ironforge"},
        "level": 5,
        "class": "Fighter"
    }
    
    # Create sample changes
    await create_sample_changes(change_log_service, character_id, character_data)
    
    # Demonstrate various query capabilities
    await demonstrate_basic_querying(query_interface, character_id)
    await demonstrate_filtering(query_interface, character_id)
    await demonstrate_sorting_and_pagination(query_interface, character_id)
    await demonstrate_text_search(query_interface, character_id)
    await demonstrate_causation_analysis(query_interface, character_id)
    await demonstrate_maintenance_operations(query_interface, character_id)
    
    print("\n=== Example completed successfully! ===")


async def create_sample_changes(change_log_service: ChangeLogService, 
                              character_id: int, character_data: dict):
    """Create sample changes for demonstration."""
    print("Creating sample change log entries...")
    
    now = datetime.now()
    changes = []
    
    # Level progression changes
    changes.extend([
        FieldChange(
            field_path="character_info.level",
            old_value=4,
            new_value=5,
            change_type=ChangeType.MODIFIED,
            category=ChangeCategory.METADATA,
            priority=ChangePriority.HIGH,
            description="Level increased to 5",
            detection_timestamp=now - timedelta(hours=1),
            metadata={"class": "Fighter", "level_gained": 5}
        ),
        FieldChange(
            field_path="combat.hit_points.maximum",
            old_value=42,
            new_value=50,
            change_type=ChangeType.MODIFIED,
            category=ChangeCategory.COMBAT,
            priority=ChangePriority.MEDIUM,
            description="Maximum HP increased to 50",
            detection_timestamp=now - timedelta(hours=1, minutes=5),
            metadata={"level_gained": 5, "class": "Fighter", "hp_gain": 8}
        )
    ])
    
    # Feat selection
    changes.append(FieldChange(
        field_path="features.feats.great_weapon_master",
        old_value=None,
        new_value={
            "name": "Great Weapon Master",
            "description": "You've learned to put the weight of a weapon to your advantage...",
            "source": "Player's Handbook"
        },
        change_type=ChangeType.ADDED,
        category=ChangeCategory.FEATURES,
        priority=ChangePriority.HIGH,
        description="Added Great Weapon Master feat",
        detection_timestamp=now - timedelta(hours=2),
        metadata={"level_gained": 4, "feat_choice": True}
    ))
    
    # Ability score improvement
    changes.extend([
        FieldChange(
            field_path="abilities.strength.score",
            old_value=16,
            new_value=18,
            change_type=ChangeType.MODIFIED,
            category=ChangeCategory.ABILITIES,
            priority=ChangePriority.HIGH,
            description="Strength increased to 18",
            detection_timestamp=now - timedelta(hours=2, minutes=10),
            metadata={"source": "ability_score_improvement", "level": 4}
        ),
        FieldChange(
            field_path="abilities.strength.modifier",
            old_value=3,
            new_value=4,
            change_type=ChangeType.MODIFIED,
            category=ChangeCategory.ABILITIES,
            priority=ChangePriority.MEDIUM,
            description="Strength modifier increased to +4",
            detection_timestamp=now - timedelta(hours=2, minutes=10),
            metadata={"caused_by": "ability_score_change"}
        )
    ])
    
    # Equipment changes
    changes.extend([
        FieldChange(
            field_path="equipment.weapons.greatsword_plus_1",
            old_value=None,
            new_value={
                "name": "Greatsword +1",
                "damage": "2d6+1",
                "properties": ["heavy", "two-handed"],
                "rarity": "uncommon"
            },
            change_type=ChangeType.ADDED,
            category=ChangeCategory.EQUIPMENT,
            priority=ChangePriority.MEDIUM,
            description="Acquired Greatsword +1",
            detection_timestamp=now - timedelta(hours=3),
            metadata={"source": "treasure", "location": "Dragon's Hoard"}
        ),
        FieldChange(
            field_path="combat.attack_bonus.melee",
            old_value=7,
            new_value=8,
            change_type=ChangeType.MODIFIED,
            category=ChangeCategory.COMBAT,
            priority=ChangePriority.MEDIUM,
            description="Melee attack bonus increased to +8",
            detection_timestamp=now - timedelta(hours=3, minutes=5),
            metadata={"caused_by": "magic_weapon"}
        )
    ])
    
    # Spell changes (multiclass)
    changes.extend([
        FieldChange(
            field_path="spells.known.shield",
            old_value=None,
            new_value={
                "name": "Shield",
                "level": 1,
                "school": "Abjuration",
                "casting_time": "1 reaction"
            },
            change_type=ChangeType.ADDED,
            category=ChangeCategory.SPELLS,
            priority=ChangePriority.MEDIUM,
            description="Learned Shield spell",
            detection_timestamp=now - timedelta(hours=4),
            metadata={"multiclass": "Wizard", "level": 1}
        ),
        FieldChange(
            field_path="spellcasting.spell_slots.1",
            old_value=0,
            new_value=2,
            change_type=ChangeType.MODIFIED,
            category=ChangeCategory.SPELLS,
            priority=ChangePriority.LOW,
            description="Gained 2 first-level spell slots",
            detection_timestamp=now - timedelta(hours=4, minutes=5),
            metadata={"multiclass": "Wizard", "level": 1}
        )
    ])
    
    # Log all changes
    success = await change_log_service.log_changes(character_id, changes, character_data)
    print(f"✓ Created {len(changes)} sample changes (success: {success})\n")


async def demonstrate_basic_querying(query_interface: ChangeLogQueryInterface, character_id: int):
    """Demonstrate basic querying capabilities."""
    print("=== Basic Querying ===")
    
    # Get all changes
    options = QueryOptions()
    result = await query_interface.query_changes(character_id, options)
    
    print(f"Total changes: {result.total_count}")
    print(f"Query time: {result.query_time_ms:.2f}ms")
    print(f"Recent changes:")
    
    for i, entry in enumerate(result.entries[:3]):
        print(f"  {i+1}. {entry.description} ({entry.category.value})")
    
    print()


async def demonstrate_filtering(query_interface: ChangeLogQueryInterface, character_id: int):
    """Demonstrate filtering capabilities."""
    print("=== Filtering Examples ===")
    
    # Filter by category
    options = QueryOptions(categories={ChangeCategory.FEATURES, ChangeCategory.ABILITIES})
    result = await query_interface.query_changes(character_id, options)
    print(f"Features and abilities changes: {len(result.entries)}")
    
    # Filter by priority
    options = QueryOptions(priorities={ChangePriority.HIGH})
    result = await query_interface.query_changes(character_id, options)
    print(f"High priority changes: {len(result.entries)}")
    
    # Filter by date range (last 3 hours)
    now = datetime.now()
    options = QueryOptions(
        start_date=now - timedelta(hours=3),
        end_date=now
    )
    result = await query_interface.query_changes(character_id, options)
    print(f"Changes in last 3 hours: {len(result.entries)}")
    
    # Custom filter by change type
    options = QueryOptions(
        filters=[QueryFilter("change_type", QueryOperator.EQUALS, "added")]
    )
    result = await query_interface.query_changes(character_id, options)
    print(f"Added items: {len(result.entries)}")
    
    # Filter by field path pattern
    options = QueryOptions(
        filters=[QueryFilter("field_path", QueryOperator.CONTAINS, "abilities")]
    )
    result = await query_interface.query_changes(character_id, options)
    print(f"Ability-related changes: {len(result.entries)}")
    
    print()


async def demonstrate_sorting_and_pagination(query_interface: ChangeLogQueryInterface, character_id: int):
    """Demonstrate sorting and pagination."""
    print("=== Sorting and Pagination ===")
    
    # Sort by priority (ascending)
    options = QueryOptions(sort_by="priority", sort_order=SortOrder.ASC)
    result = await query_interface.query_changes(character_id, options)
    print("Changes sorted by priority (low to high):")
    for entry in result.entries[:3]:
        print(f"  - {entry.description} ({entry.priority.value})")
    
    # Pagination example
    print("\nPagination example (2 items per page):")
    for page in range(3):
        options = QueryOptions(limit=2, offset=page * 2)
        result = await query_interface.query_changes(character_id, options)
        
        print(f"  Page {page + 1}:")
        for entry in result.entries:
            print(f"    - {entry.description}")
        
        if not result.has_more:
            break
    
    print()


async def demonstrate_text_search(query_interface: ChangeLogQueryInterface, character_id: int):
    """Demonstrate text search capabilities."""
    print("=== Text Search ===")
    
    # Search for "weapon" in descriptions
    result = await query_interface.search_changes(character_id, "weapon")
    print(f"Changes mentioning 'weapon': {len(result)}")
    for entry in result:
        print(f"  - {entry.description}")
    
    # Search for "spell" in descriptions
    result = await query_interface.search_changes(character_id, "spell")
    print(f"\nChanges mentioning 'spell': {len(result)}")
    for entry in result:
        print(f"  - {entry.description}")
    
    # Search in specific fields
    result = await query_interface.search_changes(
        character_id, "strength", 
        search_fields=["description", "field_path"]
    )
    print(f"\nStrength-related changes: {len(result)}")
    for entry in result:
        print(f"  - {entry.description} ({entry.field_path})")
    
    print()


async def demonstrate_causation_analysis(query_interface: ChangeLogQueryInterface, character_id: int):
    """Demonstrate causation analysis and reporting."""
    print("=== Causation Analysis ===")
    
    # Generate causation report
    report = await query_interface.generate_causation_report(character_id)
    
    print(f"Character: {report.character_name}")
    print(f"Total changes analyzed: {report.total_changes}")
    
    print("\nCausation breakdown:")
    for trigger, count in report.causation_breakdown.items():
        print(f"  {trigger}: {count} changes")
    
    print("\nAttribution breakdown:")
    for source_type, count in report.attribution_breakdown.items():
        print(f"  {source_type}: {count} changes")
    
    print("\nTop causes:")
    for cause_type, cause_name, count in report.top_causes[:5]:
        print(f"  {cause_name} ({cause_type}): {count} changes")
    
    print("\nCascade analysis:")
    for trigger, affected_fields in report.cascade_analysis.items():
        print(f"  {trigger} affects: {', '.join(affected_fields[:3])}{'...' if len(affected_fields) > 3 else ''}")
    
    # Get changes by specific cause
    feat_changes = await query_interface.get_changes_by_cause(
        character_id, "feat_selection", "Great Weapon Master"
    )
    print(f"\nChanges caused by Great Weapon Master feat: {len(feat_changes)}")
    
    # Get related changes
    related = await query_interface.get_related_changes(
        character_id, "abilities.strength.score", time_window_hours=1
    )
    print(f"Changes related to strength score (1 hour window): {len(related)}")
    
    print()


async def demonstrate_maintenance_operations(query_interface: ChangeLogQueryInterface, character_id: int):
    """Demonstrate maintenance and cleanup operations."""
    print("=== Maintenance Operations ===")
    
    # Get maintenance info
    info = await query_interface.get_log_maintenance_info(character_id)
    print(f"Log statistics:")
    print(f"  Total entries: {info.get('total_entries', 0)}")
    print(f"  Total size: {info.get('total_size_mb', 0):.2f} MB")
    print(f"  Oldest entry: {info.get('oldest_entry', 'N/A')}")
    print(f"  Newest entry: {info.get('newest_entry', 'N/A')}")
    
    if info.get('recommendations'):
        print("\nMaintenance recommendations:")
        for rec in info['recommendations']:
            print(f"  {rec['severity'].upper()}: {rec['message']}")
    
    # Demonstrate cleanup (remove low priority changes older than 1 hour)
    cleanup_criteria = {
        'max_age_days': 0.04,  # ~1 hour in days
        'min_priority': ChangePriority.MEDIUM.value
    }
    
    print(f"\nPerforming cleanup with criteria: {cleanup_criteria}")
    cleanup_result = await query_interface.cleanup_logs_by_criteria(
        character_id, cleanup_criteria
    )
    
    if 'error' not in cleanup_result:
        print(f"  Entries before cleanup: {cleanup_result['entries_before']}")
        print(f"  Entries after cleanup: {cleanup_result['entries_after']}")
        print(f"  Entries removed: {cleanup_result['entries_removed']}")
        if cleanup_result['categories_cleaned']:
            print(f"  Categories cleaned: {', '.join(cleanup_result['categories_cleaned'])}")
    
    print()


async def demonstrate_advanced_queries(query_interface: ChangeLogQueryInterface, character_id: int):
    """Demonstrate advanced query combinations."""
    print("=== Advanced Query Examples ===")
    
    # Complex filter combination
    options = QueryOptions(
        categories={ChangeCategory.COMBAT, ChangeCategory.ABILITIES},
        priorities={ChangePriority.HIGH, ChangePriority.MEDIUM},
        start_date=datetime.now() - timedelta(hours=6),
        filters=[
            QueryFilter("description", QueryOperator.CONTAINS, "increased")
        ],
        sort_by="timestamp",
        sort_order=SortOrder.DESC,
        limit=5
    )
    
    result = await query_interface.query_changes(character_id, options)
    print(f"Complex query results: {len(result.entries)} entries")
    print("Recent combat/ability increases:")
    for entry in result.entries:
        print(f"  - {entry.description} ({entry.timestamp.strftime('%H:%M')})")
    
    # Get changes by multiple types
    result = await query_interface.get_changes_by_type(
        character_id, ["added", "modified"]
    )
    print(f"\nAdded or modified changes: {len(result)}")
    
    # Date range query
    yesterday = datetime.now() - timedelta(days=1)
    today = datetime.now()
    result = await query_interface.get_changes_by_date_range(
        character_id, yesterday, today
    )
    print(f"Changes in last 24 hours: {len(result)}")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())