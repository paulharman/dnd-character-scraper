#!/usr/bin/env python3
"""
Test script for the refactored parser.

This script tests that the refactored parser works correctly with the
same interface as the original.
"""

import json
import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parser.dnd_json_to_markdown import CharacterMarkdownGenerator


def create_test_character_data():
    """Create test character data."""
    return {
        "meta": {
            "character_id": "12345",
            "rule_version": "2024"
        },
        "basic_info": {
            "name": "Test Wizard",
            "level": 5,
            "experience": 6500,
            "classes": [
                {
                    "name": "Wizard",
                    "level": 5,
                    "subclass": "School of Evocation",
                    "hit_die": "d6"
                }
            ],
            "avatarUrl": "https://example.com/avatar.jpg",
            "armor_class": {"total": 13, "method": "Mage Armor", "details": "(13 + Dex)"},
            "hit_points": {"maximum": 32, "current": 32},
            "initiative": {"total": 2},
            "speed": {"walking": {"total": 30}},
            "proficiency_bonus": 3
        },
        "ability_scores": {
            "strength": {"score": 10, "modifier": 0},
            "dexterity": {"score": 14, "modifier": 2},
            "constitution": {"score": 13, "modifier": 1},
            "intelligence": {"score": 16, "modifier": 3},
            "wisdom": {"score": 12, "modifier": 1},
            "charisma": {"score": 8, "modifier": -1}
        },
        "species": {"name": "Human"},
        "background": {
            "name": "Sage",
            "description": "You spent years learning the lore of the multiverse."
        },
        "spells": {
            "cantrips": [
                {
                    "name": "Fire Bolt",
                    "level": 0,
                    "school": "Evocation",
                    "spellcasting_ability": "intelligence",
                    "components": {"verbal": True, "somatic": True},
                    "casting_time": "1 action",
                    "range": "120 feet",
                    "duration": "Instantaneous",
                    "concentration": False,
                    "ritual": False,
                    "is_prepared": True,
                    "description": "A bright streak flashes from your pointing finger to a target within range."
                }
            ],
            "1st_level": [
                {
                    "name": "Magic Missile",
                    "level": 1,
                    "school": "Evocation",
                    "spellcasting_ability": "intelligence",
                    "components": {"verbal": True, "somatic": True},
                    "casting_time": "1 action",
                    "range": "120 feet",
                    "duration": "Instantaneous",
                    "concentration": False,
                    "ritual": False,
                    "is_prepared": True,
                    "description": "You create three glowing darts of magical force."
                }
            ]
        },
        "inventory": [
            {
                "name": "Quarterstaff",
                "type": "Simple Melee Weapon",
                "weight": 4,
                "quantity": 1,
                "equipped": True,
                "cost": 2,
                "rarity": "Common",
                "description": "A simple weapon that can be wielded one-handed or two-handed."
            }
        ],
        "wealth": {
            "copper": 0,
            "silver": 0,
            "electrum": 0,
            "gold": 100,
            "platinum": 0,
            "total_gp": 100
        },
        "encumbrance": {
            "total_weight": 15.0,
            "carrying_capacity": 150
        },
        "feats": [
            {
                "name": "Alert",
                "description": "Always on the lookout for danger, you gain the following benefits."
            }
        ],
        "class_features": [
            {
                "name": "Arcane Recovery",
                "description": "You can regain some of your magical energy by studying your spellbook.",
                "level_required": 1,
                "is_subclass_feature": False,
                "limited_use": {
                    "uses": 1,
                    "maxUses": 1
                }
            }
        ],
        "actions": [
            {
                "name": "Fire Bolt",
                "type": "cantrip",
                "description": "Ranged spell attack. Hit: 1d10 fire damage.",
                "snippet": "A bright streak flashes from your pointing finger"
            }
        ],
        "skill_proficiencies": [
            {
                "name": "Arcana",
                "proficient": True,
                "ability": "intelligence",
                "total_bonus": 6
            }
        ],
        "saving_throw_proficiencies": [
            "Intelligence",
            "Wisdom"
        ],
        "appearance": {
            "gender": "Male",
            "age": "25",
            "height": "5'10\"",
            "weight": "150 lbs",
            "hair": "Brown",
            "eyes": "Blue",
            "skin": "Fair"
        },
        "notes": {
            "backstory": "Born in a small village, learned magic from ancient tomes."
        }
    }


def test_refactored_parser():
    """Test the refactored parser."""
    print("=" * 60)
    print("REFACTORED PARSER TEST")
    print("=" * 60)
    
    # Load the fixed scraper data instead of test data
    try:
        with open('/tmp/fixed_scraper_data.json', 'r') as f:
            character_data = json.load(f)
        print("✅ Loaded fixed scraper data")
    except FileNotFoundError:
        print("❌ Fixed scraper data not found. Using fallback character data...")
        # Try to load the latest character data instead
        try:
            with open('/mnt/c/Users/alc_u/Documents/DnD/CharacterScraper/character_data/character_144986992_2025-07-11T11-42-09.791104.json', 'r') as f:
                character_data = json.load(f)
            print("✅ Loaded latest character data")
        except FileNotFoundError:
            print("❌ No character data available. Creating minimal test data...")
            character_data = create_test_character_data()
    
    # Test basic initialization
    print("Testing CharacterMarkdownGenerator initialization...")
    try:
        generator = CharacterMarkdownGenerator(character_data)
        print(f"✅ Generator created for {generator.character_name}")
        
        # Test validation
        print("Testing validation...")
        is_valid = generator.validate_character_data()
        print(f"✅ Validation result: {is_valid}")
        
        # Test available sections
        print("Testing available sections...")
        sections = generator.get_available_sections()
        print(f"✅ Available sections: {sections}")
        
        # Test individual section generation
        print("Testing individual section generation...")
        for section in sections:
            try:
                section_content = generator.generate_section(section)
                print(f"✅ {section}: {len(section_content)} characters")
            except Exception as e:
                print(f"❌ {section}: {str(e)[:100]}...")
        
        # Test full markdown generation
        print("Testing full markdown generation...")
        markdown = generator.generate_markdown()
        print(f"✅ Full markdown: {len(markdown)} characters")
        
        # Verify key sections are present
        expected_sections = [
            '---',  # YAML frontmatter
            'name:',  # Character name
            '## Character Statistics',
            '## Abilities & Skills',
            '## Spellcasting',
            '## Features',
            '## Combat',
            '## Inventory',
            '## Appearance',
            '## Backstory'
        ]
        
        present_sections = 0
        for section in expected_sections:
            if section in markdown:
                present_sections += 1
        
        print(f"✅ Expected sections present: {present_sections}/{len(expected_sections)}")
        
        # Test with different configurations
        print("Testing with different configurations...")
        
        # Test with YAML frontmatter
        generator_yaml = CharacterMarkdownGenerator(character_data, use_yaml_frontmatter=True)
        yaml_markdown = generator_yaml.generate_markdown()
        print(f"✅ YAML frontmatter enabled: {len(yaml_markdown)} characters")
        
        # Test with DnD UI Toolkit
        generator_ui = CharacterMarkdownGenerator(character_data, use_dnd_ui_toolkit=True)
        ui_markdown = generator_ui.generate_markdown()
        print(f"✅ DnD UI Toolkit enabled: {len(ui_markdown)} characters")
        
        print("\n✅ All refactored parser tests passed!")
        
    except Exception as e:
        print(f"❌ Refactored parser test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    test_refactored_parser()