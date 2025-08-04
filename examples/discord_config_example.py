#!/usr/bin/env python3
"""
Discord Configuration Example

Demonstrates how to use the updated Discord configuration with enhanced
change tracking, change log integration, and causation analysis.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any


def load_discord_config(config_path: str = "config/discord.yaml") -> Dict[str, Any]:
    """Load Discord configuration from file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        print(f"✓ Loaded Discord configuration from {config_path}")
        return config
    except FileNotFoundError:
        print(f"✗ Configuration file not found: {config_path}")
        return {}
    except yaml.YAMLError as e:
        print(f"✗ Error parsing YAML configuration: {e}")
        return {}


def validate_enhanced_config(config: Dict[str, Any]) -> bool:
    """Validate enhanced Discord configuration structure."""
    required_sections = [
        'webhook_url',
        'character_id',
        'enhanced_change_tracking',
        'change_log',
        'causation_analysis',
        'enhanced_notifications'
    ]
    
    print("\n=== Configuration Validation ===")
    
    valid = True
    for section in required_sections:
        if section in config:
            print(f"✓ {section} section present")
        else:
            print(f"✗ {section} section missing")
            valid = False
    
    # Validate enhanced change tracking
    if 'enhanced_change_tracking' in config:
        ect_config = config['enhanced_change_tracking']
        if 'enabled' in ect_config and ect_config['enabled']:
            print("✓ Enhanced change tracking enabled")
        else:
            print("⚠ Enhanced change tracking disabled")
        
        if 'change_type_config' in ect_config:
            change_types = ect_config['change_type_config']
            enabled_types = [ct for ct, cfg in change_types.items() if cfg.get('enabled', False)]
            print(f"✓ {len(enabled_types)} change types enabled: {', '.join(enabled_types[:5])}{'...' if len(enabled_types) > 5 else ''}")
        else:
            print("✗ No change type configuration found")
            valid = False
    
    # Validate change log configuration
    if 'change_log' in config:
        cl_config = config['change_log']
        if cl_config.get('enabled', False):
            print("✓ Change logging enabled")
            storage_dir = cl_config.get('storage_directory', cl_config.get('storage_dir', 'character_data/change_logs'))
            print(f"  Storage directory: {storage_dir}")
            print(f"  Detail level: {cl_config.get('detail_level', 'comprehensive')}")
            print(f"  Retention: {cl_config.get('retention_days', 365)} days")
        else:
            print("⚠ Change logging disabled")
    
    # Validate causation analysis
    if 'causation_analysis' in config:
        ca_config = config['causation_analysis']
        if ca_config.get('enabled', False):
            print("✓ Causation analysis enabled")
            print(f"  Confidence threshold: {ca_config.get('confidence_threshold', 0.7)}")
            print(f"  Max cascade depth: {ca_config.get('max_cascade_depth', 3)}")
        else:
            print("⚠ Causation analysis disabled")
    
    return valid


def demonstrate_change_type_configuration(config: Dict[str, Any]):
    """Demonstrate change type configuration options."""
    print("\n=== Change Type Configuration ===")
    
    if 'enhanced_change_tracking' not in config:
        print("✗ Enhanced change tracking not configured")
        return
    
    change_types = config['enhanced_change_tracking'].get('change_type_config', {})
    
    # Group by priority
    priority_groups = {'HIGH': [], 'MEDIUM': [], 'LOW': []}
    
    for change_type, type_config in change_types.items():
        priority = type_config.get('priority', 'MEDIUM')
        enabled = type_config.get('enabled', False)
        discord_enabled = type_config.get('discord_enabled', False)
        
        status = "✓" if enabled else "✗"
        discord_status = "Discord" if discord_enabled else "Log only"
        
        priority_groups[priority].append(f"{status} {change_type} ({discord_status})")
    
    for priority, types in priority_groups.items():
        if types:
            print(f"\n{priority} Priority:")
            for type_info in types:
                print(f"  {type_info}")


def demonstrate_notification_settings(config: Dict[str, Any]):
    """Demonstrate notification configuration options."""
    print("\n=== Notification Settings ===")
    
    if 'enhanced_notifications' not in config:
        print("✗ Enhanced notifications not configured")
        return
    
    notifications = config['enhanced_notifications']
    
    print(f"Detail level: {notifications.get('detail_level', 'summary')}")
    print(f"Include attribution: {notifications.get('include_attribution', True)}")
    print(f"Include causation: {notifications.get('include_causation', True)}")
    print(f"Minimum priority: {notifications.get('min_priority', 'LOW')}")
    print(f"Group related changes: {notifications.get('group_related_changes', True)}")
    print(f"Use embeds: {notifications.get('use_embeds', True)}")
    print(f"Color code by priority: {notifications.get('color_code_by_priority', True)}")


def demonstrate_filtering_configuration(config: Dict[str, Any]):
    """Demonstrate filtering configuration options."""
    print("\n=== Filtering Configuration ===")
    
    if 'filtering' not in config:
        print("✗ Filtering configuration not found")
        return
    
    change_types = config['filtering'].get('change_types', [])
    
    # Separate legacy and enhanced types
    legacy_types = [
        'level', 'experience', 'hit_points', 'armor_class', 'ability_scores',
        'spells_known', 'spell_slots', 'inventory_items', 'equipment',
        'currency', 'skills', 'proficiencies', 'feats', 'class_features',
        'appearance', 'background'
    ]
    
    enhanced_types = [
        'subclass', 'spells', 'inventory', 'max_hp', 'race_species',
        'multiclass', 'personality', 'spellcasting_stats', 'initiative',
        'passive_skills', 'alignment', 'size', 'movement_speed'
    ]
    
    legacy_enabled = [ct for ct in change_types if ct in legacy_types]
    enhanced_enabled = [ct for ct in change_types if ct in enhanced_types]
    
    print(f"Legacy change types enabled: {len(legacy_enabled)}/{len(legacy_types)}")
    print(f"Enhanced change types enabled: {len(enhanced_enabled)}/{len(enhanced_types)}")
    
    if enhanced_enabled:
        print(f"Enhanced types: {', '.join(enhanced_enabled)}")


def create_sample_configuration():
    """Create a sample Discord configuration for demonstration."""
    print("\n=== Creating Sample Configuration ===")
    
    sample_config = {
        'webhook_url': '${DISCORD_WEBHOOK_URL}',
        'character_id': 145081718,
        'run_continuous': False,
        'check_interval': 600,
        'storage_dir': '../character_data',
        'log_level': 'INFO',
        
        'notifications': {
            'username': 'D&D Beyond Monitor',
            'avatar_url': None,
            'timezone': 'UTC'
        },
        
        'enhanced_change_tracking': {
            'enabled': True,
            'detect_minor_changes': False,
            'change_type_config': {
                'feats': {
                    'enabled': True,
                    'priority': 'HIGH',
                    'discord_enabled': True,
                    'causation_analysis': True
                },
                'spells': {
                    'enabled': True,
                    'priority': 'MEDIUM',
                    'discord_enabled': True,
                    'causation_analysis': True
                },
                'inventory': {
                    'enabled': True,
                    'priority': 'MEDIUM',
                    'discord_enabled': False,  # Log only
                    'causation_analysis': True
                }
            }
        },
        
        'change_log': {
            'enabled': True,
            'storage_dir': 'character_data/change_logs',
            'retention_days': 365,
            'detail_level': 'comprehensive',
            'discord_detail_level': 'summary',
            'enable_causation_analysis': True,
            'min_priority_for_discord': 'MEDIUM'
        },
        
        'causation_analysis': {
            'enabled': True,
            'confidence_threshold': 0.7,
            'max_cascade_depth': 3,
            'detect_feat_causation': True,
            'detect_level_progression': True,
            'detect_equipment_causation': True
        },
        
        'enhanced_notifications': {
            'detail_level': 'summary',
            'include_attribution': True,
            'include_causation': True,
            'min_priority': 'MEDIUM',
            'group_related_changes': True,
            'use_embeds': True,
            'color_code_by_priority': True
        }
    }
    
    # Save sample configuration
    sample_path = Path("config/discord_sample.yaml")
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(sample_path, 'w') as f:
        yaml.dump(sample_config, f, default_flow_style=False, indent=2)
    
    print(f"✓ Sample configuration saved to {sample_path}")
    return sample_config


def demonstrate_backward_compatibility():
    """Demonstrate backward compatibility with legacy configurations."""
    print("\n=== Backward Compatibility ===")
    
    legacy_config = {
        'webhook_url': '${DISCORD_WEBHOOK_URL}',
        'character_id': 145081718,
        'run_continuous': False,
        'filtering': {
            'change_types': [
                'level', 'feats', 'spells_known', 'inventory_items'
            ]
        }
    }
    
    print("Legacy configuration structure:")
    print(json.dumps(legacy_config, indent=2))
    
    print("\n✓ Legacy configurations continue to work")
    print("✓ New sections are optional and additive")
    print("✓ Existing change types are preserved")
    print("✓ Webhook URLs and basic settings unchanged")


def main():
    """Main demonstration function."""
    print("Discord Configuration Example")
    print("=" * 50)
    
    # Try to load existing configuration
    config = load_discord_config()
    
    if not config:
        print("Creating sample configuration for demonstration...")
        config = create_sample_configuration()
    
    # Validate configuration
    is_valid = validate_enhanced_config(config)
    
    if is_valid:
        print("\n✓ Configuration is valid")
    else:
        print("\n⚠ Configuration has issues")
    
    # Demonstrate various aspects
    demonstrate_change_type_configuration(config)
    demonstrate_notification_settings(config)
    demonstrate_filtering_configuration(config)
    demonstrate_backward_compatibility()
    
    print("\n=== Usage Examples ===")
    print("1. Enable only high-priority changes for Discord:")
    print("   enhanced_notifications.min_priority: 'HIGH'")
    
    print("\n2. Log everything but only notify on important changes:")
    print("   change_log.min_priority_for_logging: 'LOW'")
    print("   change_log.min_priority_for_discord: 'HIGH'")
    
    print("\n3. Focus on character progression:")
    print("   Enable: feats, multiclass, ability_scores, subclass")
    print("   Disable: personality, passive_skills, movement_speed")
    
    print("\n4. Performance optimization:")
    print("   causation_analysis.analysis_timeout_seconds: 15")
    print("   change_log.max_entries_per_batch: 50")
    
    print("\n=== Next Steps ===")
    print("1. Copy config/discord.yaml.example to config/discord.yaml")
    print("2. Set your DISCORD_WEBHOOK_URL environment variable")
    print("3. Configure your character_id")
    print("4. Customize change types and priorities")
    print("5. Test with: python discord/discord_monitor.py --config config/discord.yaml")


if __name__ == "__main__":
    main()