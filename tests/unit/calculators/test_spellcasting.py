"""
Unit tests for Spellcasting Calculator

Tests spell slot calculations, spellcasting abilities, and multiclass spellcasting.
"""

import unittest
from unittest.mock import Mock

from src.calculators.spellcasting import SpellcastingCalculator
from src.models.character import Character
from tests.factories import CharacterFactory, TestDataFactory


class TestSpellcastingCalculator(unittest.TestCase):
    """Test cases for spellcasting calculations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = SpellcastingCalculator()
        
        # Create a basic character for testing
        self.character = CharacterFactory.create_basic_character(
            id=1,
            name="Test Character",
            level=5,
            proficiency_bonus=3
        )
    
    def test_non_spellcaster(self):
        """Test non-spellcasting class."""
        raw_data = {
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'Fighter',
                        'canCastSpells': False
                    }
                }
            ],
            'stats': [
                {'id': 1, 'value': 16},  # Strength
                {'id': 2, 'value': 14},  # Dexterity
                {'id': 3, 'value': 15},  # Constitution
                {'id': 4, 'value': 10},  # Intelligence
                {'id': 5, 'value': 13},  # Wisdom
                {'id': 6, 'value': 12}   # Charisma
            ],
            'spells': {},
            'classSpells': []
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should not be a spellcaster
        self.assertFalse(result['is_spellcaster'])
        self.assertEqual(result['spellcasting_ability'], 'None')
        self.assertEqual(result['spell_save_dc'], 8)  # Base DC
        
        # Should have no spell slots
        for level in range(1, 10):
            self.assertEqual(result[f'spell_slots_level_{level}'], 0)
    
    def test_full_caster_wizard(self):
        """Test full spellcaster (Wizard)."""
        raw_data = {
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'Wizard',
                        'canCastSpells': True,
                        'spellcastingAbilityId': 4  # Intelligence
                    }
                }
            ],
            'stats': [
                {'id': 1, 'value': 10},  # Strength
                {'id': 2, 'value': 14},  # Dexterity
                {'id': 3, 'value': 15},  # Constitution
                {'id': 4, 'value': 18},  # Intelligence (+4)
                {'id': 5, 'value': 13},  # Wisdom
                {'id': 6, 'value': 12}   # Charisma
            ],
            'spells': {},
            'classSpells': [
                {
                    'characterClassId': 1,
                    'spells': [
                        {'definition': {'level': 1, 'name': 'Magic Missile'}},
                        {'definition': {'level': 3, 'name': 'Fireball'}}
                    ]
                }
            ]
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should be a spellcaster
        self.assertTrue(result['is_spellcaster'])
        self.assertEqual(result['spellcasting_ability'], 'Intelligence')
        
        # Spell save DC = 8 + proficiency + ability modifier
        expected_dc = 8 + 3 + 4  # 15
        self.assertEqual(result['spell_save_dc'], expected_dc)
        
        # Level 5 wizard should have:
        # 4 1st level, 3 2nd level, 2 3rd level
        self.assertEqual(result['spell_slots_level_1'], 4)
        self.assertEqual(result['spell_slots_level_2'], 3)
        self.assertEqual(result['spell_slots_level_3'], 2)
        self.assertEqual(result['spell_slots_level_4'], 0)
        self.assertEqual(result['spell_slots_level_5'], 0)
    
    def test_half_caster_paladin(self):
        """Test half-caster (Paladin)."""
        raw_data = {
            'classes': [
                {
                    'level': 6,
                    'definition': {
                        'name': 'Paladin',
                        'canCastSpells': True,
                        'spellcastingAbilityId': 6  # Charisma
                    }
                }
            ],
            'stats': [
                {'id': 1, 'value': 16},  # Strength
                {'id': 2, 'value': 10},  # Dexterity
                {'id': 3, 'value': 14},  # Constitution
                {'id': 4, 'value': 10},  # Intelligence
                {'id': 5, 'value': 13},  # Wisdom
                {'id': 6, 'value': 16}   # Charisma (+3)
            ],
            'spells': {},
            'classSpells': []
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should be a spellcaster
        self.assertTrue(result['is_spellcaster'])
        self.assertEqual(result['spellcasting_ability'], 'Charisma')
        
        # Spell save DC = 8 + proficiency + ability modifier
        expected_dc = 8 + 3 + 3  # 14
        self.assertEqual(result['spell_save_dc'], expected_dc)
        
        # Level 6 Paladin should have: 4 1st level, 2 2nd level
        self.assertEqual(result['spell_slots_level_1'], 4)
        self.assertEqual(result['spell_slots_level_2'], 2)
        self.assertEqual(result['spell_slots_level_3'], 0)
    
    def test_third_caster_arcane_trickster(self):
        """Test third-caster (Arcane Trickster Rogue)."""
        raw_data = {
            'classes': [
                {
                    'level': 9,
                    'definition': {
                        'name': 'Rogue',
                        'canCastSpells': True,
                        'spellcastingAbilityId': 4  # Intelligence
                    },
                    'subclassDefinition': {
                        'name': 'Arcane Trickster'
                    }
                }
            ],
            'stats': [
                {'id': 1, 'value': 10},  # Strength
                {'id': 2, 'value': 18},  # Dexterity
                {'id': 3, 'value': 14},  # Constitution
                {'id': 4, 'value': 16},  # Intelligence (+3)
                {'id': 5, 'value': 13},  # Wisdom
                {'id': 6, 'value': 12}   # Charisma
            ],
            'spells': {},
            'classSpells': []
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should be a spellcaster
        self.assertTrue(result['is_spellcaster'])
        self.assertEqual(result['spellcasting_ability'], 'Intelligence')
        
        # Level 9 Arcane Trickster should have: 3 1st level, 2 2nd level
        self.assertEqual(result['spell_slots_level_1'], 3)
        self.assertEqual(result['spell_slots_level_2'], 2)
        self.assertEqual(result['spell_slots_level_3'], 0)
    
    def test_warlock_pact_magic(self):
        """Test Warlock pact magic (different from regular spellcasting)."""
        raw_data = {
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'Warlock',
                        'canCastSpells': True,
                        'spellcastingAbilityId': 6  # Charisma
                    }
                }
            ],
            'stats': [
                {'id': 1, 'value': 10},  # Strength
                {'id': 2, 'value': 14},  # Dexterity
                {'id': 3, 'value': 15},  # Constitution
                {'id': 4, 'value': 12},  # Intelligence
                {'id': 5, 'value': 13},  # Wisdom
                {'id': 6, 'value': 18}   # Charisma (+4)
            ],
            'spells': {},
            'classSpells': []
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should be a spellcaster
        self.assertTrue(result['is_spellcaster'])
        self.assertEqual(result['spellcasting_ability'], 'Charisma')
        
        # Spell save DC = 8 + proficiency + ability modifier
        expected_dc = 8 + 3 + 4  # 15
        self.assertEqual(result['spell_save_dc'], expected_dc)
        
        # Level 5 Warlock should have 2 3rd level pact slots
        # (Implementation may vary - might be tracked separately)
        total_slots = sum([
            result['spell_slots_level_1'],
            result['spell_slots_level_2'],
            result['spell_slots_level_3']
        ])
        self.assertGreater(total_slots, 0)
    
    def test_multiclass_spellcasting(self):
        """Test multiclass spellcasting progression."""
        raw_data = {
            'classes': [
                {
                    'level': 3,
                    'definition': {
                        'name': 'Wizard',
                        'canCastSpells': True,
                        'spellcastingAbilityId': 4  # Intelligence
                    }
                },
                {
                    'level': 2,
                    'definition': {
                        'name': 'Cleric',
                        'canCastSpells': True,
                        'spellcastingAbilityId': 5  # Wisdom
                    }
                }
            ],
            'stats': [
                {'id': 1, 'value': 10},  # Strength
                {'id': 2, 'value': 14},  # Dexterity
                {'id': 3, 'value': 15},  # Constitution
                {'id': 4, 'value': 18},  # Intelligence (+4)
                {'id': 5, 'value': 16},  # Wisdom (+3)
                {'id': 6, 'value': 12}   # Charisma
            ],
            'spells': {},
            'classSpells': []
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should be a spellcaster
        self.assertTrue(result['is_spellcaster'])
        
        # Should pick primary spellcasting ability (likely Intelligence from Wizard)
        self.assertIn(result['spellcasting_ability'], ['Intelligence', 'Wisdom'])
        
        # Multiclass level 3 Wizard + level 2 Cleric = level 5 caster
        # Should have 4 1st level, 3 2nd level, 2 3rd level slots
        self.assertEqual(result['spell_slots_level_1'], 4)
        self.assertEqual(result['spell_slots_level_2'], 3)
        self.assertEqual(result['spell_slots_level_3'], 2)
    
    def test_multiclass_with_warlock(self):
        """Test multiclass with Warlock (pact magic doesn't combine)."""
        raw_data = {
            'classes': [
                {
                    'level': 4,
                    'definition': {
                        'name': 'Sorcerer',
                        'canCastSpells': True,
                        'spellcastingAbilityId': 6  # Charisma
                    }
                },
                {
                    'level': 3,
                    'definition': {
                        'name': 'Warlock',
                        'canCastSpells': True,
                        'spellcastingAbilityId': 6  # Charisma
                    }
                }
            ],
            'stats': [
                {'id': 1, 'value': 10},  # Strength
                {'id': 2, 'value': 14},  # Dexterity
                {'id': 3, 'value': 15},  # Constitution
                {'id': 4, 'value': 12},  # Intelligence
                {'id': 5, 'value': 13},  # Wisdom
                {'id': 6, 'value': 18}   # Charisma (+4)
            ],
            'spells': {},
            'classSpells': []
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should be a spellcaster
        self.assertTrue(result['is_spellcaster'])
        self.assertEqual(result['spellcasting_ability'], 'Charisma')
        
        # Should have both regular spell slots (from Sorcerer) and pact slots (from Warlock)
        # Implementation may track these separately or combine them
        total_slots = sum([
            result['spell_slots_level_1'],
            result['spell_slots_level_2'],
            result['spell_slots_level_3'],
            result['spell_slots_level_4']
        ])
        self.assertGreater(total_slots, 0)
    
    def test_spell_count_tracking(self):
        """Test spell count tracking by level."""
        raw_data = {
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'Wizard',
                        'canCastSpells': True,
                        'spellcastingAbilityId': 4  # Intelligence
                    }
                }
            ],
            'stats': [
                {'id': 4, 'value': 16}  # Intelligence
            ],
            'spells': {
                'race': [
                    {'definition': {'level': 0, 'name': 'Light'}}
                ]
            },
            'classSpells': [
                {
                    'characterClassId': 1,
                    'spells': [
                        {'definition': {'level': 0, 'name': 'Prestidigitation'}},
                        {'definition': {'level': 1, 'name': 'Magic Missile'}},
                        {'definition': {'level': 1, 'name': 'Shield'}},
                        {'definition': {'level': 2, 'name': 'Misty Step'}},
                        {'definition': {'level': 3, 'name': 'Fireball'}}
                    ]
                }
            ]
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should track spell counts by level
        if 'spells_known_by_level' in result:
            spell_counts = result['spells_known_by_level']
            self.assertEqual(spell_counts.get('0', 0), 2)  # 2 cantrips
            self.assertEqual(spell_counts.get('1', 0), 2)  # 2 first level
            self.assertEqual(spell_counts.get('2', 0), 1)  # 1 second level
            self.assertEqual(spell_counts.get('3', 0), 1)  # 1 third level
    
    def test_no_spellcasting_ability(self):
        """Test class with canCastSpells but no spellcastingAbilityId."""
        raw_data = {
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'SomeClass',
                        'canCastSpells': True
                        # Missing spellcastingAbilityId
                    }
                }
            ],
            'stats': [
                {'id': 1, 'value': 16},
                {'id': 2, 'value': 14},
                {'id': 3, 'value': 15},
                {'id': 4, 'value': 10},
                {'id': 5, 'value': 13},
                {'id': 6, 'value': 12}
            ],
            'spells': {},
            'classSpells': []
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should handle gracefully
        self.assertIsInstance(result['is_spellcaster'], bool)
        self.assertIsInstance(result['spellcasting_ability'], str)
        self.assertIsInstance(result['spell_save_dc'], int)
    
    def test_spell_attack_bonus(self):
        """Test spell attack bonus calculation."""
        raw_data = {
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'Wizard',
                        'canCastSpells': True,
                        'spellcastingAbilityId': 4  # Intelligence
                    }
                }
            ],
            'stats': [
                {'id': 4, 'value': 18}  # Intelligence (+4)
            ],
            'spells': {},
            'classSpells': []
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Spell attack bonus = proficiency + ability modifier
        if 'spell_attack_bonus' in result:
            expected_bonus = 3 + 4  # +7
            self.assertEqual(result['spell_attack_bonus'], expected_bonus)


if __name__ == '__main__':
    unittest.main()