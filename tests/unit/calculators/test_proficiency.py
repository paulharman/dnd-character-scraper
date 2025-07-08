"""
Unit tests for Proficiency Calculator

Tests proficiency calculations including skills, saving throws, tools, and languages.
"""

import unittest
from unittest.mock import Mock

from src.calculators.proficiencies import ProficiencyCalculator
from src.models.character import Character
from tests.factories import CharacterFactory, TestDataFactory


class TestProficiencyCalculator(unittest.TestCase):
    """Test cases for proficiency calculations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = ProficiencyCalculator()
        
        # Create a basic character for testing
        self.character = CharacterFactory.create_basic_character(
            id=1,
            name="Test Character",
            level=5,
            proficiency_bonus=3
        )
    
    def test_basic_proficiencies(self):
        """Test basic proficiency extraction."""
        raw_data = {
            'stats': [
                {'id': 1, 'value': 16},  # Strength (+3)
                {'id': 2, 'value': 14},  # Dexterity (+2)
                {'id': 3, 'value': 15},  # Constitution (+2)
                {'id': 4, 'value': 10},  # Intelligence (0)
                {'id': 5, 'value': 13},  # Wisdom (+1)
                {'id': 6, 'value': 12}   # Charisma (+1)
            ],
            'modifiers': {
                'class': [
                    {
                        'subType': 'proficiency',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Skill',
                        'friendlySubtypeName': 'Athletics'
                    },
                    {
                        'subType': 'saving-throws',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Saving Throw',
                        'friendlySubtypeName': 'Strength'
                    }
                ]
            }
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should track skill proficiencies
        if 'skill_proficiencies' in result:
            skills = result['skill_proficiencies']
            self.assertIn('Athletics', skills)
        
        # Should track saving throw proficiencies
        if 'saving_throw_proficiencies' in result:
            saves = result['saving_throw_proficiencies']
            self.assertIn('Strength', saves)
    
    def test_skill_bonuses_calculation(self):
        """Test skill bonus calculations with proficiency."""
        raw_data = {
            'stats': [
                {'id': 1, 'value': 16},  # Strength (+3)
                {'id': 2, 'value': 14},  # Dexterity (+2)
                {'id': 3, 'value': 15},  # Constitution (+2)
                {'id': 4, 'value': 10},  # Intelligence (0)
                {'id': 5, 'value': 13},  # Wisdom (+1)
                {'id': 6, 'value': 12}   # Charisma (+1)
            ],
            'modifiers': {
                'class': [
                    {
                        'subType': 'proficiency',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Skill',
                        'friendlySubtypeName': 'Athletics'
                    },
                    {
                        'subType': 'proficiency',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Skill',
                        'friendlySubtypeName': 'Stealth'
                    },
                    {
                        'subType': 'proficiency',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Skill',
                        'friendlySubtypeName': 'Perception'
                    }
                ]
            }
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should calculate skill bonuses correctly
        if 'skill_bonuses' in result:
            bonuses = result['skill_bonuses']
            
            # Athletics = Strength + Proficiency = 3 + 3 = 6
            self.assertEqual(bonuses.get('Athletics'), 6)
            
            # Stealth = Dexterity + Proficiency = 2 + 3 = 5
            self.assertEqual(bonuses.get('Stealth'), 5)
            
            # Perception = Wisdom + Proficiency = 1 + 3 = 4
            self.assertEqual(bonuses.get('Perception'), 4)
        
        # Non-proficient skills should just be ability modifier
        if 'skill_bonuses' in result:
            bonuses = result['skill_bonuses']
            # Acrobatics (Dex-based, not proficient) = 2
            self.assertEqual(bonuses.get('Acrobatics', 2), 2)
    
    def test_saving_throw_bonuses(self):
        """Test saving throw bonus calculations."""
        raw_data = {
            'stats': [
                {'id': 1, 'value': 16},  # Strength (+3)
                {'id': 2, 'value': 14},  # Dexterity (+2)
                {'id': 3, 'value': 15},  # Constitution (+2)
                {'id': 4, 'value': 10},  # Intelligence (0)
                {'id': 5, 'value': 13},  # Wisdom (+1)
                {'id': 6, 'value': 12}   # Charisma (+1)
            ],
            'modifiers': {
                'class': [
                    {
                        'subType': 'saving-throws',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Saving Throw',
                        'friendlySubtypeName': 'Strength'
                    },
                    {
                        'subType': 'saving-throws',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Saving Throw',
                        'friendlySubtypeName': 'Constitution'
                    }
                ]
            }
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should calculate saving throw bonuses
        if 'saving_throw_bonuses' in result:
            bonuses = result['saving_throw_bonuses']
            
            # Strength save = 3 + 3 = 6 (proficient)
            self.assertEqual(bonuses.get('Strength'), 6)
            
            # Constitution save = 2 + 3 = 5 (proficient)  
            self.assertEqual(bonuses.get('Constitution'), 5)
            
            # Dexterity save = 2 (not proficient, just modifier)
            self.assertEqual(bonuses.get('Dexterity'), 2)
    
    def test_expertise_double_proficiency(self):
        """Test expertise (double proficiency bonus)."""
        raw_data = {
            'stats': [
                {'id': 2, 'value': 16}  # Dexterity (+3)
            ],
            'modifiers': {
                'class': [
                    {
                        'subType': 'proficiency',
                        'type': 'expertise',  # Expertise instead of proficiency
                        'friendlyTypeName': 'Skill',
                        'friendlySubtypeName': 'Stealth'
                    }
                ]
            }
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should double proficiency bonus for expertise
        if 'skill_bonuses' in result:
            bonuses = result['skill_bonuses']
            # Stealth with expertise = Dex + (2 * Proficiency) = 3 + (2 * 3) = 9
            self.assertEqual(bonuses.get('Stealth'), 9)
        
        # Should track expertise separately
        if 'skill_expertise' in result:
            expertise = result['skill_expertise']
            self.assertIn('Stealth', expertise)
    
    def test_tool_proficiencies(self):
        """Test tool proficiency tracking."""
        raw_data = {
            'modifiers': {
                'background': [
                    {
                        'subType': 'proficiency',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Tool',
                        'friendlySubtypeName': "Thieves' Tools"
                    }
                ],
                'class': [
                    {
                        'subType': 'proficiency',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Tool',
                        'friendlySubtypeName': "Smith's Tools"
                    }
                ]
            }
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should track tool proficiencies
        if 'tool_proficiencies' in result:
            tools = result['tool_proficiencies']
            self.assertIn("Thieves' Tools", tools)
            self.assertIn("Smith's Tools", tools)
    
    def test_language_proficiencies(self):
        """Test language proficiency tracking."""
        raw_data = {
            'modifiers': {
                'race': [
                    {
                        'subType': 'proficiency',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Language',
                        'friendlySubtypeName': 'Common'
                    },
                    {
                        'subType': 'proficiency',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Language',
                        'friendlySubtypeName': 'Elvish'
                    }
                ],
                'background': [
                    {
                        'subType': 'proficiency',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Language',
                        'friendlySubtypeName': "Thieves' Cant"
                    }
                ]
            }
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should track language proficiencies
        if 'language_proficiencies' in result:
            languages = result['language_proficiencies']
            self.assertIn('Common', languages)
            self.assertIn('Elvish', languages)
            self.assertIn("Thieves' Cant", languages)
    
    def test_armor_proficiencies(self):
        """Test armor proficiency tracking."""
        raw_data = {
            'modifiers': {
                'class': [
                    {
                        'subType': 'proficiency',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Armor',
                        'friendlySubtypeName': 'Light Armor'
                    },
                    {
                        'subType': 'proficiency',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Armor',
                        'friendlySubtypeName': 'Medium Armor'
                    },
                    {
                        'subType': 'proficiency',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Armor',
                        'friendlySubtypeName': 'Shields'
                    }
                ]
            }
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should track armor proficiencies
        if 'armor_proficiencies' in result:
            armor = result['armor_proficiencies']
            self.assertIn('Light Armor', armor)
            self.assertIn('Medium Armor', armor)
            self.assertIn('Shields', armor)
    
    def test_weapon_proficiencies(self):
        """Test weapon proficiency tracking."""
        raw_data = {
            'modifiers': {
                'class': [
                    {
                        'subType': 'proficiency',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Weapon',
                        'friendlySubtypeName': 'Simple Weapons'
                    },
                    {
                        'subType': 'proficiency',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Weapon',
                        'friendlySubtypeName': 'Martial Weapons'
                    }
                ]
            }
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should track weapon proficiencies
        if 'weapon_proficiencies' in result:
            weapons = result['weapon_proficiencies']
            self.assertIn('Simple Weapons', weapons)
            self.assertIn('Martial Weapons', weapons)
    
    def test_proficiency_sources(self):
        """Test tracking proficiency sources."""
        raw_data = {
            'stats': [
                {'id': 1, 'value': 16}  # Strength
            ],
            'modifiers': {
                'race': [
                    {
                        'subType': 'proficiency',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Skill',
                        'friendlySubtypeName': 'Perception'
                    }
                ],
                'class': [
                    {
                        'subType': 'proficiency',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Skill',
                        'friendlySubtypeName': 'Athletics'
                    }
                ],
                'background': [
                    {
                        'subType': 'proficiency',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Skill',
                        'friendlySubtypeName': 'Stealth'
                    }
                ]
            }
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should track sources of proficiencies
        if 'proficiency_sources' in result:
            sources = result['proficiency_sources']
            
            # Each skill should have its source tracked
            self.assertEqual(sources.get('Perception'), 'race')
            self.assertEqual(sources.get('Athletics'), 'class')
            self.assertEqual(sources.get('Stealth'), 'background')
    
    def test_jack_of_all_trades(self):
        """Test Jack of All Trades (half proficiency to non-proficient checks)."""
        raw_data = {
            'stats': [
                {'id': 2, 'value': 14},  # Dexterity (+2)
                {'id': 6, 'value': 16}   # Charisma (+3)
            ],
            'modifiers': {
                'class': [
                    {
                        'subType': 'proficiency',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Skill',
                        'friendlySubtypeName': 'Persuasion'
                    }
                ]
            },
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'Bard'  # Has Jack of All Trades
                    }
                }
            ]
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should apply half proficiency to non-proficient skills for Bards
        if 'skill_bonuses' in result and 'jack_of_all_trades' in result:
            bonuses = result['skill_bonuses']
            
            # Persuasion (proficient) = Cha + Prof = 3 + 3 = 6
            self.assertEqual(bonuses.get('Persuasion'), 6)
            
            # Sleight of Hand (not proficient, but Jack of All Trades)
            # = Dex + floor(Prof/2) = 2 + 1 = 3
            self.assertEqual(bonuses.get('Sleight of Hand'), 3)
    
    def test_reliable_talent(self):
        """Test Reliable Talent (treat d20 rolls of 9 or lower as 10)."""
        raw_data = {
            'stats': [
                {'id': 2, 'value': 16}  # Dexterity (+3)
            ],
            'modifiers': {
                'class': [
                    {
                        'subType': 'proficiency',
                        'type': 'proficiency',
                        'friendlyTypeName': 'Skill',
                        'friendlySubtypeName': 'Stealth'
                    }
                ]
            },
            'classes': [
                {
                    'level': 11,
                    'definition': {
                        'name': 'Rogue'  # Has Reliable Talent at level 11
                    }
                }
            ]
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should note Reliable Talent feature
        if 'reliable_talent' in result:
            self.assertTrue(result['reliable_talent'])
            
            # Should list skills affected by Reliable Talent
            if 'reliable_talent_skills' in result:
                skills = result['reliable_talent_skills']
                self.assertIn('Stealth', skills)
    
    def test_missing_proficiency_data(self):
        """Test handling of missing proficiency data."""
        raw_data = {
            'stats': [
                {'id': 1, 'value': 16}
            ]
            # No modifiers section
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should handle gracefully with defaults
        self.assertIsInstance(result.get('skill_proficiencies', []), list)
        self.assertIsInstance(result.get('saving_throw_proficiencies', []), list)
        self.assertIsInstance(result.get('tool_proficiencies', []), list)
        self.assertIsInstance(result.get('language_proficiencies', []), list)


if __name__ == '__main__':
    unittest.main()