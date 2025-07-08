#!/usr/bin/env python3
"""
Discord Monitor Setup Script

Interactive script to help set up Discord monitoring configuration.
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any


def get_input(prompt: str, default: str = None, required: bool = True) -> str:
    """Get user input with optional default."""
    full_prompt = prompt
    if default:
        full_prompt += f" (default: {default})"
    full_prompt += ": "
    
    value = input(full_prompt).strip()
    
    if not value and default:
        return default
    elif not value and required:
        print("This field is required!")
        return get_input(prompt, default, required)
    
    return value


def get_yes_no(prompt: str, default: bool = None) -> bool:
    """Get yes/no input from user."""
    default_str = ""
    if default is True:
        default_str = " (Y/n)"
    elif default is False:
        default_str = " (y/N)"
    else:
        default_str = " (y/n)"
    
    while True:
        response = input(f"{prompt}{default_str}: ").strip().lower()
        
        if not response and default is not None:
            return default
        elif response in ['y', 'yes', 'true', '1']:
            return True
        elif response in ['n', 'no', 'false', '0']:
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no")


def get_character_ids() -> list:
    """Get character IDs from user."""
    print("\n=== Character Configuration ===")
    
    multiple = get_yes_no("Do you want to monitor multiple characters?", False)
    
    if not multiple:
        # Single character
        char_id = get_input("Enter character ID")
        try:
            return [int(char_id)]
        except ValueError:
            print("Invalid character ID! Please enter a number.")
            return get_character_ids()
    else:
        # Multiple characters
        characters = []
        print("Enter character IDs one by one (press Enter with empty input to finish):")
        
        while True:
            char_id = get_input(f"Character ID #{len(characters) + 1}", required=False)
            if not char_id:
                break
            
            try:
                characters.append(int(char_id))
                print(f"Added character ID: {char_id}")
            except ValueError:
                print("Invalid character ID! Please enter a number.")
        
        if not characters:
            print("At least one character ID is required!")
            return get_character_ids()
        
        return characters


def get_filtering_config() -> Dict[str, Any]:
    """Get filtering configuration from user."""
    print("\n=== Notification Filtering ===")
    
    presets = {
        '1': 'combat_only',
        '2': 'level_up', 
        '3': 'roleplay_session',
        '4': 'shopping_trip',
        '5': 'minimal',
        '6': 'debug'
    }
    
    print("Choose a filtering preset:")
    print("1. Combat Only - HP, AC, spell slots")
    print("2. Level Up - Level, abilities, spells, skills")
    print("3. Roleplay Session - Basic info, inventory, currency")
    print("4. Shopping Trip - Inventory, currency, equipment")
    print("5. Minimal - Level and basic info only")
    print("6. Debug - All changes (verbose)")
    
    while True:
        choice = get_input("Select preset (1-6)", "2")
        if choice in presets:
            return {'preset': presets[choice]}
        else:
            print("Invalid choice! Please enter 1-6.")


def main():
    """Main setup function."""
    try:
        print("🎲 Discord Character Monitor Setup")
    except UnicodeEncodeError:
        print("[DICE] Discord Character Monitor Setup")
    print("=" * 40)
    
    print("This script will help you create a configuration file for the Discord character monitor.")
    print()
    
    config = {}
    
    # Discord webhook
    print("=== Discord Configuration ===")
    webhook_url = get_input("Discord webhook URL")
    config['webhook_url'] = webhook_url
    
    # Character IDs
    character_ids = get_character_ids()
    if len(character_ids) == 1:
        config['character_id'] = character_ids[0]
    else:
        config['characters'] = [{'character_id': char_id} for char_id in character_ids]
    
    # Basic settings
    print("\n=== Basic Settings ===")
    
    check_interval = get_input("Check interval in seconds", "300")
    try:
        config['check_interval'] = int(check_interval)
    except ValueError:
        config['check_interval'] = 300
    
    format_types = {'1': 'compact', '2': 'detailed', '3': 'json'}
    print("Message format:")
    print("1. Compact - Brief summary")
    print("2. Detailed - Full information with categories")
    print("3. JSON - Raw data (for debugging)")
    
    format_choice = get_input("Select format (1-3)", "2")
    config['format_type'] = format_types.get(format_choice, 'detailed')
    
    # Filtering
    config['filtering'] = get_filtering_config()
    
    # Optional settings
    print("\n=== Optional Settings ===")
    
    if get_yes_no("Do you have a D&D Beyond session cookie for private characters?", False):
        session_cookie = get_input("Session cookie", required=False)
        if session_cookie:
            config['session_cookie'] = session_cookie
    
    # Storage directory
    storage_dir = get_input("Storage directory for character data", "character_data")
    config['storage_dir'] = storage_dir
    
    # Notification settings
    config['notifications'] = {}
    
    username = get_input("Discord bot username", "D&D Beyond Monitor")
    config['notifications']['username'] = username
    
    if get_yes_no("Configure mentions for special events?", False):
        config['notifications']['mentions'] = {}
        
        level_up_mention = get_input("Mention for level ups (e.g. @DM, @everyone)", required=False)
        if level_up_mention:
            config['notifications']['mentions']['level_up'] = level_up_mention
        
        high_priority_mention = get_input("Mention for high priority changes", required=False) 
        if high_priority_mention:
            config['notifications']['mentions']['high_priority'] = high_priority_mention
    
    # Advanced settings
    if get_yes_no("Configure advanced settings?", False):
        config['advanced'] = {}
        
        max_changes = get_input("Maximum changes per notification", "20")
        try:
            config['advanced']['max_changes_per_notification'] = int(max_changes)
        except ValueError:
            config['advanced']['max_changes_per_notification'] = 20
    
    # Log level
    log_levels = {'1': 'ERROR', '2': 'WARNING', '3': 'INFO', '4': 'DEBUG'}
    print("Log level:")
    print("1. ERROR - Only errors")
    print("2. WARNING - Warnings and errors")
    print("3. INFO - General information (recommended)")
    print("4. DEBUG - Verbose debugging")
    
    log_choice = get_input("Select log level (1-4)", "3")
    config['log_level'] = log_levels.get(log_choice, 'INFO')
    
    # Save configuration
    print("\n=== Configuration Complete ===")
    
    config_filename = get_input("Configuration filename", "discord_config.yml")
    if not config_filename.endswith('.yml') and not config_filename.endswith('.yaml'):
        config_filename += '.yml'
    
    # Check if file exists
    if Path(config_filename).exists():
        if not get_yes_no(f"File {config_filename} exists. Overwrite?", False):
            print("Setup cancelled.")
            return
    
    # Write configuration
    try:
        with open(config_filename, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        print(f"✅ Configuration saved to {config_filename}")
        print()
        print("To start monitoring:")
        print(f"  python discord_monitor.py --config {config_filename}")
        print()
        print("To test the Discord webhook:")
        print(f"  python discord_monitor.py --config {config_filename} --test")
        
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return
    
    # Show next steps
    print("\n=== Next Steps ===")
    print("1. Test the Discord webhook connection")
    print("2. Run a test monitoring cycle")
    print("3. Set up as a service or scheduled task for continuous monitoring")
    print()
    print("For help and documentation, see the README.md file.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)