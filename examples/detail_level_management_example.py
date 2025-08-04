#!/usr/bin/env python3
"""
Detail Level Management Example

This example demonstrates how the DetailLevelManager handles different levels of detail
for Discord notifications vs comprehensive change logs, with various change types and
attribution scenarios.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from discord.services.detail_level_manager import DetailLevelManager, DetailLevel
from src.models.change_detection import FieldChange, ChangeType, ChangePriority
from discord.services.change_detection.models import ChangeCategory
from src.models.change_log import ChangeAttribution, ChangeCausation


def create_sample_changes():
    """Create sample changes with various attribution types."""
    
    # Feat addition change
    feat_change = FieldChange(
        field_path="features.feats.great_weapon_master",
        old_value=None,
        new_value={"name": "Great Weapon Master", "description": "You've learned to put the weight of a weapon to your advantage..."},
        change_type=ChangeType.ADDED,
        priority=ChangePriority.HIGH,
        category=ChangeCategory.FEATURES,
        description="Added feat: Great Weapon Master",
        detection_timestamp=datetime.now(),
        metadata={}
    )
    
    feat_attribution = ChangeAttribution(
        source='feat_selection',
        source_name='Great Weapon Master',
        source_type='feat',
        impact_summary='Enables power attacks (-5 attack, +10 damage) and bonus action attacks on critical hits or kills'
    )
    
    feat_causation = ChangeCausation(
        trigger='feat_selection',
        trigger_details={
            'feat_name': 'Great Weapon Master',
            'level_gained': 4,
            'class': 'Fighter'
        },
        related_changes=[
            'combat.attack_options.great_weapon_master_attack',
            'combat.bonus_actions.great_weapon_master_bonus'
        ],
        cascade_depth=0
    )
    
    # Level progression change
    level_change = FieldChange(
        field_path="basic_info.level",
        old_value=3,
        new_value=4,
        change_type=ChangeType.INCREMENTED,
        priority=ChangePriority.HIGH,
        category=ChangeCategory.PROGRESSION,
        description="Level: 3 → 4",
        detection_timestamp=datetime.now(),
        metadata={}
    )
    
    level_attribution = ChangeAttribution(
        source='level_progression',
        source_name='Level 4 Fighter',
        source_type='class_feature',
        impact_summary='Gained Ability Score Improvement, increased proficiency bonus, and new class features'
    )
    
    # Magic item equipment change
    equipment_change = FieldChange(
        field_path="combat.armor_class",
        old_value=15,
        new_value=16,
        change_type=ChangeType.INCREMENTED,
        priority=ChangePriority.MEDIUM,
        category=ChangeCategory.COMBAT,
        description="AC: 15 → 16 (+1)",
        detection_timestamp=datetime.now(),
        metadata={}
    )
    
    equipment_attribution = ChangeAttribution(
        source='equipment_change',
        source_name='Ring of Protection',
        source_type='magic_item',
        impact_summary='Provides +1 AC and +1 to all saving throws'
    )
    
    # Racial trait change
    racial_change = FieldChange(
        field_path="senses.darkvision",
        old_value=None,
        new_value=60,
        change_type=ChangeType.ADDED,
        priority=ChangePriority.MEDIUM,
        category=ChangeCategory.ABILITIES,
        description="Gained Darkvision (60 ft)",
        detection_timestamp=datetime.now(),
        metadata={}
    )
    
    racial_attribution = ChangeAttribution(
        source='racial_bonus',
        source_name='Draconic Ancestry',
        source_type='race',
        impact_summary='Grants darkvision and draconic heritage abilities'
    )
    
    # Ability score change
    ability_change = FieldChange(
        field_path="ability_scores.strength.modifier",
        old_value=3,
        new_value=4,
        change_type=ChangeType.INCREMENTED,
        priority=ChangePriority.MEDIUM,
        category=ChangeCategory.ABILITIES,
        description="Strength modifier: +3 → +4",
        detection_timestamp=datetime.now(),
        metadata={}
    )
    
    ability_attribution = ChangeAttribution(
        source='ability_score_improvement',
        source_name='Strength +2 (ASI)',
        source_type='ability_score',
        impact_summary='Increases attack rolls, damage rolls, and Athletics checks'
    )
    
    # Minor currency change
    currency_change = FieldChange(
        field_path="currency.gold",
        old_value=100,
        new_value=150,
        change_type=ChangeType.INCREMENTED,
        priority=ChangePriority.LOW,
        category=ChangeCategory.EQUIPMENT,
        description="GP: 100 → 150 (+50)",
        detection_timestamp=datetime.now(),
        metadata={}
    )
    
    return [
        (feat_change, feat_attribution, feat_causation),
        (level_change, level_attribution, None),
        (equipment_change, equipment_attribution, None),
        (racial_change, racial_attribution, None),
        (ability_change, ability_attribution, None),
        (currency_change, None, None)
    ]


def demonstrate_discord_formatting():
    """Demonstrate Discord formatting at different detail levels."""
    print("=" * 80)
    print("DISCORD FORMATTING EXAMPLES")
    print("=" * 80)
    
    detail_manager = DetailLevelManager()
    changes_data = create_sample_changes()
    
    for detail_level in [DetailLevel.DISCORD_BRIEF, DetailLevel.DISCORD_DETAILED]:
        print(f"\n{detail_level.value.upper()} FORMATTING:")
        print("-" * 50)
        
        for change, attribution, causation in changes_data:
            formatted = detail_manager.format_change_for_discord(
                change, attribution, causation, detail_level
            )
            print(f"• {formatted}")


def demonstrate_change_log_formatting():
    """Demonstrate comprehensive change log formatting."""
    print("\n" + "=" * 80)
    print("CHANGE LOG FORMATTING EXAMPLES")
    print("=" * 80)
    
    detail_manager = DetailLevelManager()
    changes_data = create_sample_changes()
    
    for change, attribution, causation in changes_data:
        formatted = detail_manager.format_change_for_log(change, attribution, causation)
        print(f"\n{change.field_path}:")
        print(f"  {formatted}")


def demonstrate_filtering():
    """Demonstrate change filtering for different contexts."""
    print("\n" + "=" * 80)
    print("CHANGE FILTERING EXAMPLES")
    print("=" * 80)
    
    detail_manager = DetailLevelManager()
    changes_data = create_sample_changes()
    
    changes = [item[0] for item in changes_data]
    attributions = {item[0].field_path: item[1] for item in changes_data if item[1]}
    
    print(f"\nTotal changes: {len(changes)}")
    
    # Discord filtering
    discord_changes = detail_manager.filter_changes_for_context(
        changes, attributions, 'discord'
    )
    print(f"Discord changes: {len(discord_changes)}")
    for change in discord_changes:
        print(f"  • {change.description}")
    
    # Discord filtering with strict config
    strict_config = {'discord_only_high_priority': True}
    strict_discord_changes = detail_manager.filter_changes_for_context(
        changes, attributions, 'discord', strict_config
    )
    print(f"\nDiscord changes (high priority only): {len(strict_discord_changes)}")
    for change in strict_discord_changes:
        print(f"  • {change.description}")
    
    # Change log filtering
    log_changes = detail_manager.filter_changes_for_context(
        changes, attributions, 'change_log'
    )
    print(f"\nChange log changes: {len(log_changes)}")
    for change in log_changes:
        print(f"  • {change.description}")


def demonstrate_priority_boosting():
    """Demonstrate priority boosting based on attribution."""
    print("\n" + "=" * 80)
    print("PRIORITY BOOSTING EXAMPLES")
    print("=" * 80)
    
    detail_manager = DetailLevelManager()
    changes_data = create_sample_changes()
    
    for change, attribution, causation in changes_data:
        original_priority = change.priority
        boosted_priority = detail_manager.get_priority_for_discord(change, attribution)
        
        print(f"\n{change.field_path}:")
        print(f"  Original priority: {original_priority.name}")
        print(f"  Discord priority: {boosted_priority.name}")
        if attribution:
            print(f"  Attribution: {attribution.source_type} - {attribution.source_name}")


def demonstrate_importance_scoring():
    """Demonstrate importance scoring for prioritization."""
    print("\n" + "=" * 80)
    print("IMPORTANCE SCORING EXAMPLES")
    print("=" * 80)
    
    detail_manager = DetailLevelManager()
    changes_data = create_sample_changes()
    
    scored_changes = []
    for change, attribution, causation in changes_data:
        score = detail_manager.get_change_importance_score(change, attribution)
        scored_changes.append((score, change, attribution))
    
    # Sort by score (highest first)
    scored_changes.sort(key=lambda x: x[0], reverse=True)
    
    print("\nChanges ranked by importance:")
    for score, change, attribution in scored_changes:
        attribution_info = f" ({attribution.source_type}: {attribution.source_name})" if attribution else ""
        print(f"  {score:3d} - {change.description}{attribution_info}")


def demonstrate_discord_summary():
    """Demonstrate Discord summary creation."""
    print("\n" + "=" * 80)
    print("DISCORD SUMMARY EXAMPLES")
    print("=" * 80)
    
    detail_manager = DetailLevelManager()
    changes_data = create_sample_changes()
    
    changes = [item[0] for item in changes_data]
    attributions = {item[0].field_path: item[1] for item in changes_data if item[1]}
    
    # Full summary
    full_summary = detail_manager.create_discord_summary(changes, attributions)
    print(f"\nFull summary: {full_summary}")
    
    # Summary with just high priority changes
    high_priority_changes = [c for c in changes if c.priority.value >= ChangePriority.HIGH.value]
    high_priority_summary = detail_manager.create_discord_summary(high_priority_changes, attributions)
    print(f"High priority summary: {high_priority_summary}")
    
    # Summary with just attributed changes
    attributed_changes = [c for c in changes if c.field_path in attributions]
    attributed_summary = detail_manager.create_discord_summary(attributed_changes, attributions)
    print(f"Attributed changes summary: {attributed_summary}")


def demonstrate_end_to_end_workflow():
    """Demonstrate complete end-to-end workflow."""
    print("\n" + "=" * 80)
    print("END-TO-END WORKFLOW EXAMPLE")
    print("=" * 80)
    
    detail_manager = DetailLevelManager()
    changes_data = create_sample_changes()
    
    changes = [item[0] for item in changes_data]
    attributions = {item[0].field_path: item[1] for item in changes_data if item[1]}
    causations = {item[0].field_path: item[2] for item in changes_data if item[2]}
    
    print(f"\nProcessing {len(changes)} changes...")
    
    # Step 1: Filter for Discord
    discord_changes = detail_manager.filter_changes_for_context(
        changes, attributions, 'discord'
    )
    print(f"Filtered to {len(discord_changes)} changes for Discord")
    
    # Step 2: Determine detail level for Discord
    discord_detail_level = detail_manager.get_detail_level_for_context(
        'discord', len(discord_changes)
    )
    print(f"Using {discord_detail_level.value} for Discord formatting")
    
    # Step 3: Format for Discord
    print("\nDiscord notifications:")
    for change in discord_changes:
        attribution = attributions.get(change.field_path)
        causation = causations.get(change.field_path)
        formatted = detail_manager.format_change_for_discord(
            change, attribution, causation, discord_detail_level
        )
        print(f"  • {formatted}")
    
    # Step 4: Create Discord summary if many changes
    if len(discord_changes) > 3:
        summary = detail_manager.create_discord_summary(discord_changes, attributions)
        print(f"\nDiscord summary: {summary}")
    
    # Step 5: Filter for change log
    log_changes = detail_manager.filter_changes_for_context(
        changes, attributions, 'change_log'
    )
    print(f"\nFiltered to {len(log_changes)} changes for change log")
    
    # Step 6: Format for change log
    print("\nChange log entries:")
    for change in log_changes:
        attribution = attributions.get(change.field_path)
        causation = causations.get(change.field_path)
        formatted = detail_manager.format_change_for_log(change, attribution, causation)
        print(f"  {change.field_path}: {formatted}")


def main():
    """Run all demonstration examples."""
    print("Detail Level Management Demonstration")
    print("=====================================")
    print("This example shows how the DetailLevelManager handles different")
    print("levels of detail for Discord notifications vs change logs.")
    
    demonstrate_discord_formatting()
    demonstrate_change_log_formatting()
    demonstrate_filtering()
    demonstrate_priority_boosting()
    demonstrate_importance_scoring()
    demonstrate_discord_summary()
    demonstrate_end_to_end_workflow()
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("The DetailLevelManager provides comprehensive control over how")
    print("changes are formatted and filtered for different contexts.")


if __name__ == '__main__':
    main()