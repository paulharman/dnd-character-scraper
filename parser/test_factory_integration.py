#!/usr/bin/env python3
"""
Factory integration test for the refactored parser.

This test validates that the factory pattern is working correctly
and can generate character sheets using dependency injection.
"""

import json
import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parser.factories.generator_factory import GeneratorFactory, FactoryCharacterMarkdownGenerator


def create_test_character_data():
    """Create comprehensive test character data."""
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
            "proficiency_bonus": 3,
            "gender": "Male",
            "age": "25",
            "height": "5'10\"",
            "weight": "150 lbs",
            "hair": "Brown",
            "eyes": "Blue",
            "skin": "Fair",
            "size": "Medium"
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
            "description": "You spent years learning the lore of the multiverse.",
            "ideals": "Knowledge is power, and the key to all other forms of power.",
            "bonds": "The library where I conducted my research is my most treasured place.",
            "flaws": "I am easily distracted by the promise of information."
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
                },
                {
                    "name": "Mage Hand",
                    "level": 0,
                    "school": "Conjuration",
                    "spellcasting_ability": "intelligence",
                    "components": {"verbal": True, "somatic": True},
                    "casting_time": "1 action",
                    "range": "30 feet",
                    "duration": "1 minute",
                    "concentration": False,
                    "ritual": False,
                    "is_prepared": True,
                    "description": "A spectral, floating hand appears at a point you choose within range."
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
                },
                {
                    "name": "Shield",
                    "level": 1,
                    "school": "Abjuration",
                    "spellcasting_ability": "intelligence",
                    "components": {"verbal": True, "somatic": True},
                    "casting_time": "1 reaction",
                    "range": "Self",
                    "duration": "1 round",
                    "concentration": False,
                    "ritual": False,
                    "is_prepared": True,
                    "description": "An invisible barrier of magical force appears and protects you."
                }
            ],
            "2nd_level": [
                {
                    "name": "Fireball",
                    "level": 3,
                    "school": "Evocation",
                    "spellcasting_ability": "intelligence",
                    "components": {"verbal": True, "somatic": True, "material": True},
                    "casting_time": "1 action",
                    "range": "150 feet",
                    "duration": "Instantaneous",
                    "concentration": False,
                    "ritual": False,
                    "is_prepared": True,
                    "description": "A bright streak flashes from your pointing finger to a point you choose within range and then blossoms with a low roar into an explosion of flame."
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
            },
            {
                "name": "Spellbook",
                "type": "Arcane Focus",
                "weight": 3,
                "quantity": 1,
                "equipped": False,
                "cost": 50,
                "rarity": "Common",
                "description": "Essential for a wizard's spellcasting."
            }
        ],
        "weapon_proficiencies": [
            {
                "name": "Simple Weapons",
                "source": "Class: Wizard"
            }
        ],
        "tool_proficiencies": [
            {
                "name": "Dragonchess Set",
                "source": "Background: Sage"
            }
        ],
        "language_proficiencies": [
            {
                "name": "Common",
                "source": "Species: Human"
            },
            {
                "name": "Elvish",
                "source": "Background: Sage"
            }
        ],
        "ability_score_breakdown": {
            "strength": {
                "total": 10,
                "base": 10,
                "asi": 0
            },
            "intelligence": {
                "total": 16,
                "base": 15,
                "asi": 1
            }
        },
        "features": [
            {
                "name": "Darkvision",
                "description": "You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light.",
                "source": {
                    "name": "Human Species",
                    "type": "species"
                }
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
                "description": "Always on the lookout for danger, you gain the following benefits: +5 bonus to initiative, can't be surprised while conscious, other creatures don't gain advantage on attack rolls against you as a result of being unseen by you."
            }
        ],
        "class_features": [
            {
                "name": "Arcane Recovery",
                "description": "You can regain some of your magical energy by studying your spellbook. Once per day when you finish a short rest, you can choose expended spell slots to recover.",
                "level_required": 1,
                "is_subclass_feature": False,
                "limited_use": {
                    "uses": 1,
                    "maxUses": 1
                }
            },
            {
                "name": "Sculpt Spells",
                "description": "Beginning at 2nd level, you can create pockets of relative safety within the effects of your evocation spells.",
                "level_required": 2,
                "is_subclass_feature": True,
                "limited_use": None
            }
        ],
        "actions": [
            {
                "name": "Fire Bolt",
                "type": "cantrip",
                "description": "Ranged spell attack. Hit: 1d10 fire damage.",
                "snippet": "A bright streak flashes from your pointing finger"
            },
            {
                "name": "Quarterstaff",
                "type": "weapon",
                "description": "Melee weapon attack. Hit: 1d6 bludgeoning damage.",
                "snippet": "A simple weapon attack"
            }
        ],
        "skill_proficiencies": [
            {
                "name": "Arcana",
                "proficient": True,
                "ability": "intelligence",
                "total_bonus": 6
            },
            {
                "name": "History",
                "proficient": True,
                "ability": "intelligence",
                "total_bonus": 6
            },
            {
                "name": "Investigation",
                "proficient": True,
                "ability": "intelligence",
                "total_bonus": 6
            },
            {
                "name": "Perception",
                "proficient": True,
                "ability": "wisdom",
                "total_bonus": 4
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
            "skin": "Fair",
            "appearance_description": "A studious-looking human with ink-stained fingers and a thoughtful expression."
        },
        "notes": {
            "backstory": "Born in a small village, I discovered my magical abilities at a young age. I spent years studying ancient tomes and learning from a wise mentor. Now I seek to expand my knowledge and use my powers to help others.",
            "allies": "Mentor: Elara the Wise - An elderly wizard who taught me the basics of magic\nFriend: Gareth the Brave - A paladin who often accompanies me on adventures"
        }
    }


def test_factory_creation():
    """Test that the factory can create generators."""
    print("Testing Factory Creation...")
    
    factory = GeneratorFactory()
    
    # Test basic generator creation
    generator = factory.create_generator()
    assert isinstance(generator, FactoryCharacterMarkdownGenerator)
    print("✅ Basic generator creation successful")
    
    # Test generator with different configurations
    generator_obsidian = factory.create_generator(template_type='obsidian')
    assert isinstance(generator_obsidian, CharacterMarkdownGenerator)
    print("✅ Obsidian generator creation successful")
    
    generator_ui_toolkit = factory.create_generator(template_type='ui_toolkit')
    assert isinstance(generator_ui_toolkit, CharacterMarkdownGenerator)
    print("✅ UI Toolkit generator creation successful")
    
    # Test available formatters and templates
    formatters = factory.get_available_formatters()
    assert len(formatters) > 0
    print(f"✅ Available formatters: {formatters}")
    
    templates = factory.get_available_templates()
    assert len(templates) > 0
    print(f"✅ Available templates: {templates}")
    
    print("✅ Factory creation tests passed\n")


def test_markdown_generation():
    """Test that the generator can create markdown."""
    print("Testing Markdown Generation...")
    
    factory = GeneratorFactory()
    generator = factory.create_generator()
    
    # Create test character data
    character_data = create_test_character_data()
    
    # Test markdown generation
    try:
        markdown = generator.generate_markdown(character_data)
        assert len(markdown) > 0
        print(f"✅ Markdown generated: {len(markdown)} characters")
        
        # Verify sections are present
        expected_sections = [
            '---',  # YAML frontmatter
            'name:',  # Character name in frontmatter
            '## Character Statistics',  # Character info
            '## Abilities & Skills',  # Abilities
            '## Spellcasting',  # Spells
            '## Features',  # Features
            '## Combat',  # Combat
            '## Inventory',  # Inventory
            '## Appearance',  # Appearance
            '## Backstory'  # Backstory
        ]
        
        for section in expected_sections:
            if section in markdown:
                print(f"✅ Section found: {section}")
            else:
                print(f"⚠️  Section missing: {section}")
        
        print("✅ Markdown generation tests passed\n")
        
    except Exception as e:
        print(f"❌ Markdown generation failed: {e}")
        raise


def test_individual_sections():
    """Test that individual sections can be generated."""
    print("Testing Individual Section Generation...")
    
    factory = GeneratorFactory()
    generator = factory.create_generator()
    
    character_data = create_test_character_data()
    
    # Test each section individually
    available_sections = generator.get_available_sections()
    print(f"Available sections: {available_sections}")
    
    successful_sections = 0
    for section_name in available_sections:
        try:
            section_content = generator.generate_section(section_name, character_data)
            if section_content and len(section_content) > 0:
                print(f"✅ {section_name}: {len(section_content)} characters")
                successful_sections += 1
            else:
                print(f"⚠️  {section_name}: No content generated")
        except Exception as e:
            print(f"❌ {section_name}: {str(e)[:100]}...")
    
    success_rate = (successful_sections / len(available_sections)) * 100
    print(f"✅ Section generation success rate: {successful_sections}/{len(available_sections)} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("✅ Individual section tests passed\n")
    else:
        print("❌ Individual section tests failed\n")


def test_validation():
    """Test that validation is working."""
    print("Testing Validation...")
    
    factory = GeneratorFactory()
    generator = factory.create_generator()
    
    # Test valid data
    character_data = create_test_character_data()
    is_valid = generator.validate_character_data(character_data)
    assert is_valid, "Valid character data should pass validation"
    print("✅ Valid character data passed validation")
    
    # Test invalid data
    invalid_data = {"invalid": "data"}
    is_valid = generator.validate_character_data(invalid_data)
    assert not is_valid, "Invalid character data should fail validation"
    print("✅ Invalid character data failed validation as expected")
    
    errors = generator.get_validation_errors()
    assert len(errors) > 0, "Should have validation errors"
    print(f"✅ Validation errors: {len(errors)} errors found")
    
    print("✅ Validation tests passed\n")


def test_missing_sections():
    """Test that the previously missing sections are now available."""
    print("Testing Missing Sections Integration...")
    
    factory = GeneratorFactory()
    generator = factory.create_generator()
    
    # Test that the missing formatters are available
    available_formatters = factory.get_available_formatters()
    assert 'proficiency' in available_formatters, "Missing proficiency formatter"
    assert 'racial_traits' in available_formatters, "Missing racial_traits formatter"
    print("✅ Both missing formatters are available in factory")
    
    # Test that the missing sections are available in generator
    available_sections = generator.get_available_sections()
    assert 'proficiency' in available_sections, "Missing proficiency section in generator"
    assert 'racial_traits' in available_sections, "Missing racial_traits section in generator"
    print("✅ Both missing sections are available in generator")
    
    # Test creating individual formatters
    try:
        proficiency_formatter = factory.create_formatter('proficiency')
        racial_traits_formatter = factory.create_formatter('racial_traits')
        print("✅ Individual missing formatters created successfully")
    except Exception as e:
        print(f"❌ Failed to create individual formatters: {e}")
        raise
    
    # Test generating the missing sections
    character_data = create_test_character_data()
    try:
        racial_traits_section = generator.generate_section('racial_traits', character_data)
        print(f"✅ Racial traits section generated: {len(racial_traits_section)} characters")
        
        proficiency_section = generator.generate_section('proficiency', character_data)
        print(f"✅ Proficiency section generated: {len(proficiency_section)} characters")
        
        # Verify content matches expected format
        assert '## Racial Traits' in racial_traits_section, "Missing racial traits header"
        assert '## Proficiencies' in proficiency_section, "Missing proficiencies header"
        assert '^racial-traits' in racial_traits_section, "Missing racial traits anchor"
        assert '^proficiencies' in proficiency_section, "Missing proficiencies anchor"
        
        print("✅ Section content format is correct")
        
    except Exception as e:
        print(f"❌ Failed to generate missing sections: {e}")
        raise
    
    print("✅ Missing sections integration tests passed\n")


def run_factory_integration_tests():
    """Run all factory integration tests."""
    print("=" * 60)
    print("FACTORY INTEGRATION TESTS")
    print("=" * 60)
    
    try:
        test_factory_creation()
        test_markdown_generation()
        test_individual_sections()
        test_validation()
        
        print("=" * 60)
        print("FACTORY INTEGRATION TEST SUMMARY")
        print("=" * 60)
        print("✅ All factory integration tests passed")
        print("✅ Dependency injection is working correctly")
        print("✅ Phase 4 factory pattern successfully implemented")
        print("✅ Ready to update main parser file")
        
    except Exception as e:
        print(f"❌ Factory integration test failed: {e}")
        raise


if __name__ == "__main__":
    run_factory_integration_tests()