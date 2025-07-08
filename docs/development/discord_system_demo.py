#!/usr/bin/env python3
"""
Discord Data Group System - Comprehensive Demonstration

This script demonstrates the complete data group system with realistic
character change scenarios and shows how filtering would work in practice.
"""

import json
from typing import Dict, Any, List
from dataclasses import asdict

# Import our implementation
from discord_data_groups_implementation import (
    DataGroupFilter, FieldChange, Priority
)


class CharacterChangeSimulator:
    """Simulates realistic character changes for testing the filter system"""
    
    def __init__(self):
        self.scenarios = {
            "level_up": self._create_level_up_scenario,
            "combat_damage": self._create_combat_damage_scenario,
            "spell_preparation": self._create_spell_prep_scenario,
            "equipment_change": self._create_equipment_scenario,
            "backstory_update": self._create_backstory_scenario,
            "ability_score_improvement": self._create_asi_scenario,
            "shopping_trip": self._create_shopping_scenario,
            "long_rest": self._create_long_rest_scenario
        }
    
    def _create_level_up_scenario(self) -> List[FieldChange]:
        """Simulate a character leveling up"""
        return [
            FieldChange("basic_info.level", 4, 5, "modified", Priority.HIGH),
            FieldChange("basic_info.experience", 6500, 8000, "modified", Priority.MEDIUM),
            FieldChange("basic_info.hit_points.maximum", 32, 38, "modified", Priority.HIGH),
            FieldChange("basic_info.hit_points.current", 32, 38, "modified", Priority.HIGH),
            FieldChange("meta.proficiency_bonus", 2, 3, "modified", Priority.HIGH),
            FieldChange("spell_slots.level_3", 0, 2, "added", Priority.HIGH),
            FieldChange("feats.2.name", None, "Fey Touched", "added", Priority.HIGH),
            FieldChange("feats.2.description", None, "You learn Misty Step and one 1st-level spell...", "added", Priority.MEDIUM),
            FieldChange("spells.Feat.0.name", None, "Misty Step", "added", Priority.HIGH),
            FieldChange("spells.Feat.1.name", None, "Gift of Alacrity", "added", Priority.HIGH),
            FieldChange("ability_scores.charisma.score", 14, 16, "modified", Priority.HIGH),
            FieldChange("ability_scores.charisma.modifier", 2, 3, "modified", Priority.HIGH),
        ]
    
    def _create_combat_damage_scenario(self) -> List[FieldChange]:
        """Simulate taking damage in combat"""
        return [
            FieldChange("basic_info.hit_points.current", 38, 22, "modified", Priority.HIGH),
            FieldChange("spell_slots.level_1", 4, 3, "modified", Priority.MEDIUM),
            FieldChange("spell_slots.level_2", 3, 2, "modified", Priority.MEDIUM),
            FieldChange("basic_info.hit_points.temporary", 0, 8, "modified", Priority.MEDIUM),
        ]
    
    def _create_spell_prep_scenario(self) -> List[FieldChange]:
        """Simulate preparing different spells"""
        return [
            FieldChange("spells.Wizard.4.is_prepared", True, False, "modified", Priority.MEDIUM),
            FieldChange("spells.Wizard.4.effective_prepared", True, False, "modified", Priority.MEDIUM),
            FieldChange("spells.Wizard.7.is_prepared", False, True, "modified", Priority.MEDIUM),
            FieldChange("spells.Wizard.7.effective_prepared", False, True, "modified", Priority.MEDIUM),
            FieldChange("spells.Wizard.12.is_prepared", False, True, "modified", Priority.MEDIUM),
            FieldChange("spells.Wizard.12.effective_prepared", False, True, "modified", Priority.MEDIUM),
        ]
    
    def _create_equipment_scenario(self) -> List[FieldChange]:
        """Simulate equipment changes"""
        return [
            FieldChange("inventory.5.name", "Leather Armor", "Studded Leather Armor", "modified", Priority.MEDIUM),
            FieldChange("inventory.5.equipped", True, True, "unchanged", Priority.LOW),
            FieldChange("basic_info.armor_class.total", 12, 13, "modified", Priority.HIGH),
            FieldChange("basic_info.armor_class.calculation", "Leather (11 + Dex)", "Studded Leather (12 + Dex)", "modified", Priority.MEDIUM),
            FieldChange("inventory.15.name", None, "Ring of Protection", "added", Priority.HIGH),
            FieldChange("inventory.15.equipped", None, True, "added", Priority.MEDIUM),
            FieldChange("inventory.15.attuned", None, True, "added", Priority.MEDIUM),
            FieldChange("basic_info.armor_class.total", 13, 14, "modified", Priority.HIGH),
        ]
    
    def _create_backstory_scenario(self) -> List[FieldChange]:
        """Simulate backstory and character development"""
        return [
            FieldChange("notes.character_notes", "", "Met the mysterious hooded figure again in Waterdeep...", "modified", Priority.LOW),
            FieldChange("background.allies", "Friendly blacksmith in Phandalin", 
                       "Friendly blacksmith in Phandalin; Sildar Hallwinter (Lords' Alliance)", "modified", Priority.LOW),
            FieldChange("background.enemies", "", "Glasstaff and his Redbrands", "modified", Priority.LOW),
            FieldChange("appearance.traits", "Young and eager", "Battle-scarred but determined", "modified", Priority.LOW),
        ]
    
    def _create_asi_scenario(self) -> List[FieldChange]:
        """Simulate ability score improvement"""
        return [
            FieldChange("ability_scores.intelligence.score", 16, 18, "modified", Priority.HIGH),
            FieldChange("ability_scores.intelligence.modifier", 3, 4, "modified", Priority.HIGH),
            FieldChange("ability_scores.intelligence.source_breakdown.base", 15, 15, "unchanged", Priority.LOW),
            FieldChange("ability_scores.intelligence.source_breakdown.feat", 1, 1, "unchanged", Priority.LOW),
            FieldChange("ability_scores.intelligence.source_breakdown.asi", None, 2, "added", Priority.HIGH),
            FieldChange("spells.Wizard.0.save_dc", 13, 14, "modified", Priority.MEDIUM),
            FieldChange("spells.Wizard.0.attack_bonus", 5, 6, "modified", Priority.MEDIUM),
            FieldChange("skills.arcana", 5, 6, "modified", Priority.MEDIUM),
            FieldChange("skills.investigation", 7, 8, "modified", Priority.MEDIUM),
        ]
    
    def _create_shopping_scenario(self) -> List[FieldChange]:
        """Simulate a shopping trip with lots of inventory changes"""
        return [
            FieldChange("meta.total_wealth_gp", 245, 89, "modified", Priority.MEDIUM),
            FieldChange("meta.individual_currencies.gold", 245, 89, "modified", Priority.MEDIUM),
            FieldChange("inventory.20.name", None, "Healing Potion", "added", Priority.MEDIUM),
            FieldChange("inventory.20.quantity", None, 3, "added", Priority.MEDIUM),
            FieldChange("inventory.21.name", None, "Rope (50 feet)", "added", Priority.LOW),
            FieldChange("inventory.22.name", None, "Thieves' Tools", "added", Priority.MEDIUM),
            FieldChange("inventory.23.name", None, "Spell Scroll (Fireball)", "added", Priority.HIGH),
            FieldChange("inventory.8.quantity", 20, 0, "modified", Priority.LOW),  # Sold arrows
            FieldChange("inventory.8.name", "Arrows", None, "removed", Priority.LOW),
        ]
    
    def _create_long_rest_scenario(self) -> List[FieldChange]:
        """Simulate a long rest recovery"""
        return [
            FieldChange("basic_info.hit_points.current", 22, 38, "modified", Priority.MEDIUM),
            FieldChange("basic_info.hit_points.temporary", 8, 0, "modified", Priority.LOW),
            FieldChange("spell_slots.level_1", 2, 4, "modified", Priority.MEDIUM),
            FieldChange("spell_slots.level_2", 1, 3, "modified", Priority.MEDIUM),
            FieldChange("spell_slots.level_3", 0, 2, "modified", Priority.MEDIUM),
        ]
    
    def get_scenario(self, scenario_name: str) -> List[FieldChange]:
        """Get a specific scenario's changes"""
        if scenario_name in self.scenarios:
            return self.scenarios[scenario_name]()
        else:
            raise ValueError(f"Unknown scenario: {scenario_name}")
    
    def get_all_scenarios(self) -> Dict[str, List[FieldChange]]:
        """Get all scenarios"""
        return {name: func() for name, func in self.scenarios.items()}


def demonstrate_filtering(scenario_name: str, changes: List[FieldChange], 
                         filter_config: Dict[str, Any]):
    """Demonstrate filtering for a specific scenario"""
    print(f"\n{'='*60}")
    print(f"📋 SCENARIO: {scenario_name.upper().replace('_', ' ')}")
    print(f"{'='*60}")
    
    # Create filter
    data_filter = DataGroupFilter(
        include_groups=filter_config.get('include'),
        exclude_groups=filter_config.get('exclude')
    )
    
    # Show configuration
    config_desc = []
    if filter_config.get('include'):
        config_desc.append(f"Include: {', '.join(filter_config['include'])}")
    if filter_config.get('exclude'):
        config_desc.append(f"Exclude: {', '.join(filter_config['exclude'])}")
    if not config_desc:
        config_desc.append("Include: all groups")
    
    print(f"📊 Filter: {' | '.join(config_desc)}")
    print(f"🔍 Total changes detected: {len(changes)}")
    
    # Apply filtering
    filtered_changes = data_filter.filter_changes(changes)
    print(f"✅ Changes after filtering: {len(filtered_changes)}")
    
    if filtered_changes:
        print("\n📝 Filtered Changes:")
        for change in filtered_changes:
            priority_icon = {"LOW": "🔵", "MEDIUM": "🟡", "HIGH": "🔴"}[change.priority.name]
            change_icon = {"added": "➕", "removed": "➖", "modified": "🔄", "unchanged": "➡️"}[change.change_type]
            
            if change.change_type == "added":
                print(f"  {priority_icon} {change_icon} {change.field_path}: {change.new_value}")
            elif change.change_type == "removed":
                print(f"  {priority_icon} {change_icon} {change.field_path}: removed")
            elif change.change_type == "modified":
                print(f"  {priority_icon} {change_icon} {change.field_path}: {change.old_value} → {change.new_value}")
    else:
        print("  (No changes match the filter)")
    
    # Show what was filtered out
    filtered_out = len(changes) - len(filtered_changes)
    if filtered_out > 0:
        print(f"\n🚫 {filtered_out} changes filtered out")


def main():
    """Run comprehensive demonstration"""
    print("🎭 Discord Data Group System - Comprehensive Demonstration")
    print("=" * 65)
    
    # Initialize simulator
    simulator = CharacterChangeSimulator()
    
    # Define test configurations
    test_configs = {
        "Combat Session": {
            "include": ["combat", "spells.slots"],
            "exclude": []
        },
        "Level Up Tracking": {
            "include": ["progression"],
            "exclude": []
        },
        "Roleplay Session": {
            "include": ["background", "appearance"],
            "exclude": ["meta"]
        },
        "Equipment Only": {
            "include": ["inventory", "combat.ac"],
            "exclude": ["inventory.wealth"]
        },
        "Minimal Notifications": {
            "include": ["basic", "combat.hp"],
            "exclude": []
        },
        "Everything Except Meta": {
            "include": [],
            "exclude": ["meta"]
        }
    }
    
    # Test scenarios that would benefit from different filtering
    scenario_configs = {
        "level_up": ["Level Up Tracking", "Everything Except Meta"],
        "combat_damage": ["Combat Session", "Minimal Notifications"],
        "spell_preparation": ["Combat Session", "Level Up Tracking"],
        "equipment_change": ["Equipment Only", "Combat Session"],
        "backstory_update": ["Roleplay Session", "Everything Except Meta"],
        "shopping_trip": ["Equipment Only", "Minimal Notifications"],
        "long_rest": ["Combat Session", "Minimal Notifications"]
    }
    
    # Run demonstrations
    for scenario_name, config_names in scenario_configs.items():
        changes = simulator.get_scenario(scenario_name)
        
        for config_name in config_names:
            config = test_configs[config_name]
            demonstrate_filtering(f"{scenario_name} ({config_name})", changes, config)
    
    # Summary statistics
    print(f"\n{'='*60}")
    print("📊 SUMMARY STATISTICS")
    print(f"{'='*60}")
    
    all_scenarios = simulator.get_all_scenarios()
    total_changes = sum(len(changes) for changes in all_scenarios.values())
    
    print(f"🎬 Total scenarios: {len(all_scenarios)}")
    print(f"🔄 Total changes across all scenarios: {total_changes}")
    
    # Show effectiveness of different filter strategies
    print(f"\n📈 Filter Effectiveness:")
    
    for config_name, config in test_configs.items():
        data_filter = DataGroupFilter(
            include_groups=config.get('include'),
            exclude_groups=config.get('exclude')
        )
        
        total_filtered = 0
        total_original = 0
        
        for changes in all_scenarios.values():
            filtered = data_filter.filter_changes(changes)
            total_filtered += len(filtered)
            total_original += len(changes)
        
        reduction_percent = ((total_original - total_filtered) / total_original) * 100 if total_original > 0 else 0
        
        print(f"  {config_name:<25} - {total_filtered:3d}/{total_original:3d} changes ({reduction_percent:5.1f}% reduction)")
    
    print(f"\n💡 This demonstrates how different filter strategies can significantly")
    print(f"   reduce notification noise while preserving relevant information.")


if __name__ == "__main__":
    main()