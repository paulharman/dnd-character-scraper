#!/usr/bin/env python3
"""
Discord Notifier CLI Interface Example

This demonstrates how the data group system would be integrated into 
a command-line interface for the Discord notifier.
"""

import argparse
import sys
from typing import List, Optional
from pathlib import Path

# Import our data group system (would be in actual implementation)
from discord_data_groups_implementation import (
    DataGroupFilter, DATA_GROUPS, NESTED_GROUPS, COMPOSITE_GROUPS
)


class DiscordNotifierCLI:
    """Command-line interface for the Discord notifier with data group support"""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser with all options"""
        parser = argparse.ArgumentParser(
            description="Discord notifier for D&D Beyond character changes",
            epilog=self._get_help_epilog(),
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Basic arguments
        parser.add_argument(
            "character_id",
            help="D&D Beyond character ID to monitor"
        )
        
        parser.add_argument(
            "--config", "-c",
            type=Path,
            default="discord_config.yml",
            help="Configuration file path (default: discord_config.yml)"
        )
        
        # Data group filtering
        group_filter = parser.add_argument_group("Data Group Filtering")
        
        group_filter.add_argument(
            "--include",
            type=str,
            help="Comma-separated list of groups to include (default: all)"
        )
        
        group_filter.add_argument(
            "--exclude", 
            type=str,
            help="Comma-separated list of groups to exclude (default: none)"
        )
        
        group_filter.add_argument(
            "--preset",
            choices=["combat_only", "level_up", "roleplay_session", "shopping_trip", "minimal", "debug"],
            help="Use a predefined group preset"
        )
        
        # Information commands
        info_group = parser.add_argument_group("Information")
        
        info_group.add_argument(
            "--list-groups",
            action="store_true",
            help="List all available data groups and exit"
        )
        
        info_group.add_argument(
            "--describe-group",
            type=str,
            metavar="GROUP",
            help="Describe a specific group and its fields"
        )
        
        info_group.add_argument(
            "--explain-preset",
            type=str,
            metavar="PRESET",
            help="Explain what a preset includes/excludes"
        )
        
        # Monitoring options
        monitor_group = parser.add_argument_group("Monitoring Options")
        
        monitor_group.add_argument(
            "--interval",
            type=int,
            default=600,  # 10 minutes
            help="Check interval in seconds (default: 600)"
        )
        
        monitor_group.add_argument(
            "--once",
            action="store_true",
            help="Check once and exit (don't monitor continuously)"
        )
        
        monitor_group.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be sent without actually sending"
        )
        
        # Output options
        output_group = parser.add_argument_group("Output Options")
        
        output_group.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Verbose output"
        )
        
        output_group.add_argument(
            "--format",
            choices=["compact", "detailed", "json"],
            default="detailed",
            help="Output format (default: detailed)"
        )
        
        output_group.add_argument(
            "--show-field-paths",
            action="store_true",
            help="Include field paths in output (useful for debugging)"
        )
        
        return parser
    
    def _get_help_epilog(self) -> str:
        """Generate help epilog with examples and group information"""
        return """
Examples:
  # Monitor combat changes only
  %(prog)s 145081718 --include combat,spells.slots
  
  # Monitor everything except metadata
  %(prog)s 145081718 --exclude meta
  
  # Use a preset for level-up sessions
  %(prog)s 145081718 --preset level_up
  
  # Check once with detailed output
  %(prog)s 145081718 --once --verbose --format detailed
  
  # Dry run to see what would be tracked
  %(prog)s 145081718 --include basic,combat --dry-run
  
  # List all available groups
  %(prog)s --list-groups
  
  # Describe a specific group
  %(prog)s --describe-group combat

Available Groups:
  Core Groups: basic, stats, combat, spells, inventory, features, appearance, background, meta
  Nested Groups: stats.abilities, combat.hp, spells.slots, inventory.wealth, etc.
  Composite Groups: progression, mechanics, roleplay, resources
  
Use --list-groups for complete details.
""" % {"prog": "discord_notifier.py"}
    
    def parse_args(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """Parse command line arguments"""
        return self.parser.parse_args(args)
    
    def handle_info_commands(self, args: argparse.Namespace) -> bool:
        """Handle information commands that don't require monitoring"""
        
        if args.list_groups:
            self._list_groups()
            return True
        
        if args.describe_group:
            self._describe_group(args.describe_group)
            return True
        
        if args.explain_preset:
            self._explain_preset(args.explain_preset)
            return True
        
        return False
    
    def _list_groups(self):
        """List all available data groups"""
        print("Available Data Groups:")
        print("=" * 50)
        
        print("\n📊 CORE GROUPS:")
        for name, group_def in DATA_GROUPS.items():
            priority_indicator = {"LOW": "🔵", "MEDIUM": "🟡", "HIGH": "🔴"}[group_def.priority.name]
            print(f"  {priority_indicator} {name:<12} - {group_def.description}")
        
        print("\n🔍 NESTED GROUPS:")
        for name in sorted(NESTED_GROUPS.keys()):
            parent, child = name.split('.', 1)
            print(f"     {name:<12} - {child} within {parent}")
        
        print("\n📦 COMPOSITE GROUPS:")
        for name, included_groups in COMPOSITE_GROUPS.items():
            print(f"     {name:<12} - includes: {', '.join(included_groups)}")
        
        print("\n🎯 PRESETS:")
        presets = {
            "combat_only": "Track only combat-relevant changes",
            "level_up": "Track character advancement", 
            "roleplay_session": "Track story and roleplay elements",
            "shopping_trip": "Track equipment changes",
            "minimal": "Only essential changes",
            "debug": "Track everything including metadata"
        }
        for name, description in presets.items():
            print(f"     {name:<16} - {description}")
    
    def _describe_group(self, group_name: str):
        """Describe a specific group in detail"""
        print(f"Group: {group_name}")
        print("=" * (7 + len(group_name)))
        
        # Check main groups
        if group_name in DATA_GROUPS:
            group_def = DATA_GROUPS[group_name]
            print(f"Description: {group_def.description}")
            print(f"Priority: {group_def.priority.name}")
            print(f"Fields:")
            for field in group_def.fields:
                print(f"  - {field}")
            
            if group_def.subgroups:
                print(f"Subgroups: {', '.join(group_def.subgroups)}")
        
        # Check nested groups  
        elif group_name in NESTED_GROUPS:
            parent, child = group_name.split('.', 1)
            print(f"Description: {child} fields within {parent} group")
            print(f"Fields:")
            for field in NESTED_GROUPS[group_name]:
                print(f"  - {field}")
        
        # Check composite groups
        elif group_name in COMPOSITE_GROUPS:
            included_groups = COMPOSITE_GROUPS[group_name]
            print(f"Description: Composite group including multiple groups")
            print(f"Includes: {', '.join(included_groups)}")
            print(f"Effective fields:")
            filter_obj = DataGroupFilter(include_groups=[group_name])
            for pattern in sorted(filter_obj.include_patterns):
                print(f"  - {pattern}")
        
        else:
            print(f"❌ Unknown group: {group_name}")
            print(f"Use --list-groups to see available groups")
    
    def _explain_preset(self, preset_name: str):
        """Explain what a preset includes/excludes"""
        presets = {
            "combat_only": {
                "include": ["combat", "spells.slots", "inventory.equipment"],
                "exclude": [],
                "description": "Track combat stats, spell slots, and equipment changes"
            },
            "level_up": {
                "include": ["progression"],
                "exclude": ["meta"],
                "description": "Track all character advancement (composite group 'progression')"
            },
            "roleplay_session": {
                "include": ["background", "appearance", "inventory.wealth"],
                "exclude": ["stats", "combat", "spells", "meta"],
                "description": "Focus on story elements and wealth changes"
            },
            "shopping_trip": {
                "include": ["inventory", "combat.ac"],
                "exclude": ["inventory.wealth"],
                "description": "Track equipment and AC changes, ignore wealth spam"
            },
            "minimal": {
                "include": ["basic", "combat.hp"],
                "exclude": [],
                "description": "Only level changes and hit point modifications"
            },
            "debug": {
                "include": ["*"],
                "exclude": [],
                "description": "Track everything including system metadata"
            }
        }
        
        if preset_name not in presets:
            print(f"❌ Unknown preset: {preset_name}")
            print(f"Available presets: {', '.join(presets.keys())}")
            return
        
        preset = presets[preset_name]
        print(f"Preset: {preset_name}")
        print("=" * (8 + len(preset_name)))
        print(f"Description: {preset['description']}")
        
        if preset['include']:
            print(f"Includes: {', '.join(preset['include'])}")
        
        if preset['exclude']:
            print(f"Excludes: {', '.join(preset['exclude'])}")
        
        # Show effective field patterns
        print(f"\nEffective filtering:")
        filter_obj = DataGroupFilter(
            include_groups=preset['include'] if preset['include'] else None,
            exclude_groups=preset['exclude'] if preset['exclude'] else None
        )
        
        print(f"  Include patterns: {len(filter_obj.include_patterns)}")
        if len(filter_obj.include_patterns) <= 20:
            for pattern in sorted(filter_obj.include_patterns):
                print(f"    + {pattern}")
        else:
            print(f"    (too many to display - {len(filter_obj.include_patterns)} patterns)")
        
        if filter_obj.exclude_patterns:
            print(f"  Exclude patterns: {len(filter_obj.exclude_patterns)}")
            for pattern in sorted(filter_obj.exclude_patterns):
                print(f"    - {pattern}")
    
    def create_filter(self, args: argparse.Namespace) -> DataGroupFilter:
        """Create a DataGroupFilter based on CLI arguments"""
        include_groups = None
        exclude_groups = None
        
        # Handle preset
        if args.preset:
            presets = {
                "combat_only": (["combat", "spells.slots", "inventory.equipment"], []),
                "level_up": (["progression"], ["meta"]),
                "roleplay_session": (["background", "appearance", "inventory.wealth"], 
                                   ["stats", "combat", "spells", "meta"]),
                "shopping_trip": (["inventory", "combat.ac"], ["inventory.wealth"]),
                "minimal": (["basic", "combat.hp"], []),
                "debug": (["*"], [])
            }
            
            if args.preset in presets:
                preset_include, preset_exclude = presets[args.preset]
                include_groups = preset_include
                exclude_groups = preset_exclude
        
        # Handle explicit include/exclude (override preset)
        if args.include:
            include_groups = [g.strip() for g in args.include.split(',')]
        
        if args.exclude:
            exclude_groups = [g.strip() for g in args.exclude.split(',')]
        
        return DataGroupFilter(include_groups=include_groups, exclude_groups=exclude_groups)


def main():
    """Main CLI entry point"""
    cli = DiscordNotifierCLI()
    args = cli.parse_args()
    
    # Handle information commands
    if cli.handle_info_commands(args):
        return 0
    
    # Validate character ID is provided for monitoring commands
    if not hasattr(args, 'character_id') or not args.character_id:
        print("❌ Character ID is required for monitoring")
        cli.parser.print_help()
        return 1
    
    # Create filter based on arguments
    data_filter = cli.create_filter(args)
    
    # Show what will be tracked in verbose or dry-run mode
    if args.verbose or args.dry_run:
        print(f"🎯 Monitoring character: {args.character_id}")
        print(f"📊 Include patterns: {len(data_filter.include_patterns)}")
        print(f"🚫 Exclude patterns: {len(data_filter.exclude_patterns)}")
        
        if args.show_field_paths:
            print("\nInclude patterns:")
            for pattern in sorted(data_filter.include_patterns):
                print(f"  + {pattern}")
            
            if data_filter.exclude_patterns:
                print("\nExclude patterns:")
                for pattern in sorted(data_filter.exclude_patterns):
                    print(f"  - {pattern}")
    
    if args.dry_run:
        print("🧪 Dry run mode - no actual monitoring will occur")
        return 0
    
    # In a real implementation, this would start the monitoring loop
    print(f"🚀 Starting Discord notifier for character {args.character_id}")
    print(f"⏱️  Check interval: {args.interval} seconds")
    print(f"📝 Format: {args.format}")
    
    if args.once:
        print("🔍 Performing single check...")
        # Simulate single check
        print("✅ Check completed - no changes detected")
    else:
        print("🔄 Monitoring continuously (Ctrl+C to stop)")
        print("💡 This would start the actual monitoring loop in a real implementation")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())