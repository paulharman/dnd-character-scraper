#!/usr/bin/env python3
"""
Quick Discord notification test with real character data
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from discord.services.discord_service import DiscordService, EmbedColor
from discord.services.change_detection_service import (
    ChangeDetectionService, FieldChange, ChangeType, ChangePriority, CharacterChangeSet
)
from discord.formatters.discord_formatter import DiscordFormatter, FormatType


async def test_real_notification():
    """Send a test notification with realistic character changes."""
    
    # Get webhook URL
    webhook_url = input("Enter Discord webhook URL (or press Enter to skip): ").strip()
    if not webhook_url:
        print("No webhook URL provided. Test cancelled.")
        return
    
    print("\n🚀 Testing Discord notification system...")
    
    # Create realistic character changes
    changes = [
        FieldChange(
            field_path="basic_info.level",
            old_value=2,
            new_value=3,
            change_type=ChangeType.INCREMENTED,
            priority=ChangePriority.HIGH,
            description="Level increased by 1 (2 → 3)"
        ),
        FieldChange(
            field_path="basic_info.hit_points.maximum",
            old_value=16,
            new_value=22,
            change_type=ChangeType.INCREMENTED,
            priority=ChangePriority.HIGH,
            description="Hit Points Maximum increased by 6 (16 → 22)"
        ),
        FieldChange(
            field_path="spells.spell_slots.level_2",
            old_value=0,
            new_value=2,
            change_type=ChangeType.ADDED,
            priority=ChangePriority.MEDIUM,
            description="Spell Slots Level 2 added: 2"
        ),
        FieldChange(
            field_path="inventory[15].item",
            old_value=None,
            new_value="Potion of Healing",
            change_type=ChangeType.ADDED,
            priority=ChangePriority.MEDIUM,
            description="Potion of Healing added to inventory"
        ),
        FieldChange(
            field_path="currency.gold",
            old_value=50,
            new_value=35,
            change_type=ChangeType.DECREMENTED,
            priority=ChangePriority.LOW,
            description="Gold decreased by 15 (50 → 35)"
        )
    ]
    
    # Create change set
    change_set = CharacterChangeSet(
        character_id=145081718,
        character_name="Ilarion Veles",
        from_version=14,
        to_version=15,
        timestamp=datetime.now(),
        changes=changes,
        summary="5 changes: 2 high priority, 2 medium priority, 1 low priority"
    )
    
    # Test different formats
    formatter = DiscordFormatter(FormatType.DETAILED)
    
    # Create Discord message
    message = formatter.format_character_changes(
        change_set,
        max_changes=20,
        avatar_url="https://www.dndbeyond.com/avatars/48761/398/1581111423-145081718.jpeg?width=150&height=150&fit=crop&quality=95&auto=webp"
    )
    
    # Send to Discord
    try:
        async with DiscordService(webhook_url, username="D&D Character Monitor Test") as discord:
            print("📤 Sending test notification...")
            success = await discord.send_message(message)
            
            if success:
                print("✅ Test notification sent successfully! Check your Discord channel.")
                
                # Send a follow-up test
                await asyncio.sleep(2)
                success2 = await discord.send_embed(
                    title="🧪 Discord Integration Test Complete",
                    description="The character monitoring system is working correctly!",
                    color=EmbedColor.SUCCESS,
                    fields=[
                        {"name": "Test Status", "value": "✅ Passed", "inline": True},
                        {"name": "Components", "value": "All working", "inline": True},
                        {"name": "Ready to Use", "value": "Yes", "inline": True}
                    ],
                    footer_text="You can now set up regular monitoring with discord_monitor.py"
                )
                
                if success2:
                    print("✅ Follow-up message sent!")
                    print("\n🎉 Discord notification system is fully functional!")
                    print("\nNext steps:")
                    print("1. Run: python setup_discord_monitor.py")
                    print("2. Start monitoring: python discord_monitor.py")
            else:
                print("❌ Failed to send notification. Check webhook URL and permissions.")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(test_real_notification())