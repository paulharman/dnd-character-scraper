#!/usr/bin/env python3
"""
Discord Notification System Test Script

Tests all components of the Discord notification system with mock data.
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from discord.services.discord_service import DiscordService, EmbedColor
from discord.services.change_detection_service import (
    ChangeDetectionService, FieldChange, ChangeType, ChangePriority
)
from discord.formatters.discord_formatter import DiscordFormatter, FormatType
from discord.services.notification_manager import NotificationConfig
from src.interfaces.storage import CharacterSnapshot
from src.models.character import Character

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_mock_character_data(level: int, hp: int, experience: int) -> dict:
    """Create mock character data for testing."""
    return {
        'basic_info': {
            'name': 'Test Character',
            'level': level,
            'experience': experience,
            'hit_points': {
                'current': hp,
                'maximum': hp
            },
            'armor_class': {
                'total': 13
            },
            'classes': [
                {'name': 'Wizard', 'level': level}
            ]
        },
        'ability_scores': {
            'strength': 10,
            'dexterity': 14,
            'constitution': 16,
            'intelligence': 16,
            'wisdom': 12,
            'charisma': 10
        },
        'spells': {
            'known': ['Fire Bolt', 'Mage Hand', 'Magic Missile'],
            'spell_slots': {
                'level_1': 2 if level >= 1 else 0,
                'level_2': 1 if level >= 3 else 0
            }
        },
        'inventory': [
            {
                'name': 'Backpack',
                'type': 'Equipment',
                'equipped': True,
                'weight': 5
            },
            {
                'name': 'Gold Pieces',
                'type': 'Currency', 
                'quantity': 25,
                'weight': 0
            }
        ],
        'meta': {
            'character_id': 12345,
            'processed_date': datetime.now().isoformat(),
            'scraper_version': '6.0.0-test'
        }
    }


async def test_discord_service(webhook_url: str):
    """Test the Discord service component."""
    print("\n🔍 Testing Discord Service...")
    
    async with DiscordService(webhook_url, username="Test Bot") as discord:
        # Test simple message
        success = await discord.send_simple_message("🧪 Testing Discord service...")
        if not success:
            print("❌ Simple message test failed")
            return False
        
        # Test embed message
        success = await discord.send_embed(
            title="🧙‍♂️ Discord Service Test",
            description="Testing embed functionality with rich formatting",
            color=EmbedColor.SUCCESS,
            fields=[
                {'name': 'Component', 'value': 'Discord Service', 'inline': True},
                {'name': 'Status', 'value': '✅ Working', 'inline': True},
                {'name': 'Features', 'value': '• Rich embeds\n• Rate limiting\n• Error handling', 'inline': False}
            ],
            footer_text="Test completed successfully"
        )
        
        if success:
            print("✅ Discord service test passed")
            return True
        else:
            print("❌ Discord service test failed")
            return False


def test_change_detection():
    """Test the change detection service."""
    print("\n🔍 Testing Change Detection Service...")
    
    detector = ChangeDetectionService()
    
    # Create mock snapshots
    old_data = create_mock_character_data(level=2, hp=16, experience=300)
    new_data = create_mock_character_data(level=3, hp=22, experience=900)
    
    # Add a new spell to test additions
    new_data['spells']['known'].append('Shield')
    
    # Modify gold amount
    new_data['inventory'][1]['quantity'] = 50
    
    # Create snapshots
    old_snapshot = CharacterSnapshot(
        character_id=12345,
        version=1,
        character_data=old_data,
        timestamp=datetime.now() - timedelta(hours=1)
    )
    
    new_snapshot = CharacterSnapshot(
        character_id=12345,
        version=2,
        character_data=new_data,
        timestamp=datetime.now()
    )
    
    # Detect changes
    change_set = detector.detect_changes(old_snapshot, new_snapshot)
    
    print(f"Detected {len(change_set.changes)} changes:")
    for change in change_set.changes:
        priority_symbol = {
            ChangePriority.LOW: "🔵",
            ChangePriority.MEDIUM: "🟡", 
            ChangePriority.HIGH: "🟠",
            ChangePriority.CRITICAL: "🔴"
        }[change.priority]
        
        type_symbol = {
            ChangeType.ADDED: "➕",
            ChangeType.REMOVED: "➖",
            ChangeType.MODIFIED: "🔄",
            ChangeType.INCREMENTED: "⬆️",
            ChangeType.DECREMENTED: "⬇️"
        }[change.change_type]
        
        print(f"  {priority_symbol} {type_symbol} {change.description}")
    
    # Test filtering
    filtered_changes = detector.filter_changes_by_groups(
        change_set.changes,
        include_groups={'basic', 'combat'},
        exclude_groups={'meta'}
    )
    
    print(f"After filtering: {len(filtered_changes)} changes")
    
    if change_set.changes:
        print("✅ Change detection test passed")
        return True, change_set
    else:
        print("❌ Change detection test failed - no changes detected")
        return False, None


def test_discord_formatter(change_set):
    """Test the Discord formatter."""
    print("\n🔍 Testing Discord Formatter...")
    
    formatters = [
        (FormatType.COMPACT, "Compact"),
        (FormatType.DETAILED, "Detailed"),
        (FormatType.JSON, "JSON")
    ]
    
    for format_type, name in formatters:
        formatter = DiscordFormatter(format_type)
        message = formatter.format_character_changes(change_set)
        
        if message and message.embeds:
            print(f"✅ {name} format test passed")
            
            # Show preview of detailed format
            if format_type == FormatType.DETAILED:
                embed = message.embeds[0]
                print(f"  Preview: {embed.title}")
                print(f"  Description: {embed.description}")
                if embed.fields:
                    print(f"  Fields: {len(embed.fields)} categories")
        else:
            print(f"❌ {name} format test failed")
            return False
    
    return True


async def test_integration(webhook_url: str, change_set):
    """Test full integration with real Discord notification."""
    print("\n🔍 Testing Full Integration...")
    
    formatter = DiscordFormatter(FormatType.DETAILED)
    message = formatter.format_character_changes(change_set)
    
    # Add test indicator to message
    if message.embeds:
        embed = message.embeds[0]
        embed.title = f"🧪 TEST: {embed.title}"
        embed.footer = {'text': f"{embed.footer.get('text', '')} | Integration Test"}
    
    async with DiscordService(webhook_url, username="Integration Test") as discord:
        success = await discord.send_message(message)
        
        if success:
            print("✅ Integration test passed - check Discord for notification")
            return True
        else:
            print("❌ Integration test failed")
            return False


async def main():
    """Main test function."""
    print("🧪 D&D Discord Notification System Test Suite")
    print("=" * 50)
    
    # Get webhook URL
    webhook_url = input("Enter Discord webhook URL: ").strip()
    if not webhook_url:
        print("❌ Webhook URL is required for testing")
        return
    
    try:
        # Test 1: Discord Service
        discord_success = await test_discord_service(webhook_url)
        
        # Test 2: Change Detection
        change_success, change_set = test_change_detection()
        
        # Test 3: Formatter
        if change_set:
            format_success = test_discord_formatter(change_set)
        else:
            format_success = False
            print("❌ Skipping formatter test - no change set available")
        
        # Test 4: Integration
        if change_set and discord_success:
            integration_success = await test_integration(webhook_url, change_set)
        else:
            integration_success = False
            print("❌ Skipping integration test - dependencies failed")
        
        # Summary
        print("\n📊 Test Summary")
        print("=" * 20)
        print(f"Discord Service:    {'✅ PASS' if discord_success else '❌ FAIL'}")
        print(f"Change Detection:   {'✅ PASS' if change_success else '❌ FAIL'}")
        print(f"Message Formatting: {'✅ PASS' if format_success else '❌ FAIL'}")
        print(f"Full Integration:   {'✅ PASS' if integration_success else '❌ FAIL'}")
        
        all_passed = all([discord_success, change_success, format_success, integration_success])
        
        if all_passed:
            print("\n🎉 All tests passed! The Discord notification system is ready to use.")
            print("\nNext steps:")
            print("1. Run: python setup_discord_monitor.py")
            print("2. Configure your character monitoring")
            print("3. Start monitoring: python discord_monitor.py")
        else:
            print("\n⚠️  Some tests failed. Please check the errors above.")
            
        return all_passed
        
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        return False


if __name__ == '__main__':
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n🛑 Test cancelled by user")
        sys.exit(1)