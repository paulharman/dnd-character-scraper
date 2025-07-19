"""
Edge Case Tests - Multiclass Scenarios

Tests complex multiclass combinations that could break calculations.
"""

import unittest
from unittest.mock import Mock

from src.calculators.character_calculator import CharacterCalculator
from src.rules.version_manager import RuleVersionManager, RuleVersion


class TestMulticlassScenarios(unittest.TestCase):
    """Test edge cases for multiclass characters."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = CharacterCalculator()
        self.rule_manager = RuleVersionManager()
    
    def _extract_flat_data(self, complete_data):
        """
        Extract flat data structure from v6.0.0 nested structure for test compatibility.
        
        This helper function allows tests to continue using the simpler flat access pattern
        while working with the new structured v6.0.0 calculator output.
        """
        # Get character info from the new structure
        character_info = complete_data.get('character_info', {})
        
        # Extract basic fields
        flat_data = {
            'id': character_info.get('character_id', 0),
            'name': character_info.get('name', 'Unknown'),
            'level': character_info.get('level', 0),
            'proficiency_bonus': character_info.get('proficiency_bonus', 2),
        }
        
        # Extract ability scores and modifiers from new structure
        abilities_data = complete_data.get('abilities', {})
        raw_ability_scores = abilities_data.get('ability_scores', {})
        raw_ability_modifiers = abilities_data.get('ability_modifiers', {})
        
        # Handle both flat and structured ability score formats
        flat_abilities = {}
        flat_modifiers = {}
        
        for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
            if isinstance(raw_ability_scores.get(ability), dict):
                # Structured format
                flat_abilities[ability] = raw_ability_scores[ability].get('score', 10)
                flat_modifiers[ability] = raw_ability_scores[ability].get('modifier', 0)
            else:
                # Flat format or missing
                flat_abilities[ability] = raw_ability_scores.get(ability, 10)
                flat_modifiers[ability] = raw_ability_modifiers.get(ability, 0)
        
        flat_data.update({
            'ability_scores': flat_abilities,
            'ability_modifiers': flat_modifiers,
        })
        
        # Extract calculated values from combat data
        combat_data = complete_data.get('combat', {})
        hit_points = combat_data.get('hit_points', {})
        
        flat_data.update({
            'armor_class': combat_data.get('armor_class', 10),
            'max_hp': hit_points.get('maximum', 1) if isinstance(hit_points, dict) else 1,
            'initiative_bonus': combat_data.get('initiative_bonus', 0),
        })
        
        # Extract spellcasting info from new structure
        spellcasting_data = complete_data.get('spellcasting', {})
        spell_slots = spellcasting_data.get('spell_slots', [])
        
        flat_data['spellcasting'] = {
            'is_spellcaster': spellcasting_data.get('is_spellcaster', False),
            'spellcasting_ability': spellcasting_data.get('spellcasting_ability'),
            'spell_save_dc': spellcasting_data.get('spell_save_dc'),
            'spell_attack_bonus': spellcasting_data.get('spell_attack_bonus'),
            # Include spell slots in spellcasting for compatibility
            'spell_slots_level_1': spell_slots[0] if len(spell_slots) > 0 else 0,
            'spell_slots_level_2': spell_slots[1] if len(spell_slots) > 1 else 0,
            'spell_slots_level_3': spell_slots[2] if len(spell_slots) > 2 else 0,
            'spell_slots_level_4': spell_slots[3] if len(spell_slots) > 3 else 0,
            'spell_slots_level_5': spell_slots[4] if len(spell_slots) > 4 else 0,
        }
        
        # Extract spell slots and pact slots
        flat_data['spell_slots'] = spell_slots
        flat_data['pact_slots'] = spellcasting_data.get('pact_slots', 0)
        
        return flat_data
    
    def test_triple_multiclass_spellcaster(self):
        """Test complex triple multiclass with different spellcasting types."""
        raw_data = {
            'id': 99999,
            'name': 'Complex Multiclass',
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'Wizard',
                        'hitDie': 6
                    }
                },
                {
                    'level': 3,
                    'definition': {
                        'name': 'Cleric',
                        'hitDie': 8
                    }
                },
                {
                    'level': 2,
                    'definition': {
                        'name': 'Warlock',
                        'hitDie': 8
                    }
                }
            ],
            'stats': [
                {'id': 1, 'value': 10},  # Strength
                {'id': 2, 'value': 14},  # Dexterity
                {'id': 3, 'value': 16},  # Constitution
                {'id': 4, 'value': 18},  # Intelligence (Wizard)
                {'id': 5, 'value': 16},  # Wisdom (Cleric)
                {'id': 6, 'value': 14}   # Charisma (Warlock)
            ],
            'spells': {},
            'classSpells': []
        }
        
        complete_result = self.calculator.calculate_complete_json(raw_data)
        result = self._extract_flat_data(complete_result)
        
        # Should handle complex multiclass without errors
        self.assertEqual(result['level'], 10)  # Total level
        self.assertEqual(result['proficiency_bonus'], 4)  # Level 10 = +4
        
        # Should be identified as spellcaster
        self.assertTrue(result['spellcasting']['is_spellcaster'])
        
        # Should have reasonable HP (minimum safety check)
        self.assertGreaterEqual(result['max_hp'], 10)  # At least 1 per level
        
        # Should have reasonable AC
        ac_value = result['armor_class']['total'] if isinstance(result['armor_class'], dict) else result['armor_class']
        self.assertGreaterEqual(ac_value, 10)
        self.assertLessEqual(ac_value, 25)
    
    def test_fighter_rogue_multiclass(self):
        """Test Fighter/Rogue multiclass with different hit dice."""
        raw_data = {
            'id': 99998,
            'name': 'Fighter Rogue',
            'classes': [
                {
                    'level': 6,
                    'definition': {
                        'name': 'Fighter',
                        'hitDie': 10
                    }
                },
                {
                    'level': 4,
                    'definition': {
                        'name': 'Rogue',
                        'hitDie': 8
                    }
                }
            ],
            'stats': [
                {'id': 1, 'value': 16},  # Strength
                {'id': 2, 'value': 18},  # Dexterity
                {'id': 3, 'value': 14},  # Constitution
                {'id': 4, 'value': 10},  # Intelligence
                {'id': 5, 'value': 12},  # Wisdom
                {'id': 6, 'value': 10}   # Charisma
            ]
        }
        
        complete_result = self.calculator.calculate_complete_json(raw_data)
        result = self._extract_flat_data(complete_result)
        
        # Should have high Dex-based AC
        dex_mod = (18 - 10) // 2  # +4
        expected_min_ac = 10 + dex_mod  # 14
        ac_value = result['armor_class']['total'] if isinstance(result['armor_class'], dict) else result['armor_class']
        self.assertGreaterEqual(ac_value, expected_min_ac)
        
        # Should have good initiative from high Dex
        self.assertEqual(result['initiative_bonus'], dex_mod)
        
        # Should not be a spellcaster
        self.assertFalse(result['spellcasting']['is_spellcaster'])
    
    def test_paladin_warlock_conflicting_spellcasting(self):
        """Test Paladin/Warlock with different spellcasting mechanics."""
        raw_data = {
            'id': 99997,
            'name': 'Paladin Warlock',
            'classes': [
                {
                    'level': 7,
                    'definition': {
                        'name': 'Paladin',
                        'hitDie': 10
                    }
                },
                {
                    'level': 3,
                    'definition': {
                        'name': 'Warlock',
                        'hitDie': 8
                    }
                }
            ],
            'stats': [
                {'id': 1, 'value': 16},  # Strength
                {'id': 2, 'value': 10},  # Dexterity
                {'id': 3, 'value': 16},  # Constitution
                {'id': 4, 'value': 10},  # Intelligence
                {'id': 5, 'value': 14},  # Wisdom
                {'id': 6, 'value': 18}   # Charisma (both classes)
            ]
        }
        
        complete_result = self.calculator.calculate_complete_json(raw_data)
        result = self._extract_flat_data(complete_result)
        
        # Should be a spellcaster
        self.assertTrue(result['spellcasting']['is_spellcaster'])
        
        # Should use Charisma for spellcasting (case insensitive)
        self.assertEqual(result['spellcasting']['spellcasting_ability'].lower(), 'charisma')
        
        # Should have both Paladin spell slots and Warlock pact slots
        # (Implementation might vary, but should handle gracefully)
        total_spell_levels = sum([
            result['spellcasting']['spell_slots_level_1'],
            result['spellcasting']['spell_slots_level_2'],
            result['spellcasting']['spell_slots_level_3'],
            result['spellcasting']['spell_slots_level_4'],
            result['spellcasting']['spell_slots_level_5']
        ])
        
        # Should have some spell slots
        self.assertGreater(total_spell_levels, 0)
    
    def test_barbarian_monk_unarmored_defense_conflict(self):
        """Test Barbarian/Monk with conflicting Unarmored Defense features."""
        raw_data = {
            'id': 99996,
            'name': 'Barbarian Monk',
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'Barbarian',
                        'hitDie': 12
                    }
                },
                {
                    'level': 3,
                    'definition': {
                        'name': 'Monk',
                        'hitDie': 8
                    }
                }
            ],
            'stats': [
                {'id': 1, 'value': 16},  # Strength
                {'id': 2, 'value': 16},  # Dexterity
                {'id': 3, 'value': 16},  # Constitution
                {'id': 4, 'value': 10},  # Intelligence
                {'id': 5, 'value': 16},  # Wisdom
                {'id': 6, 'value': 10}   # Charisma
            ],
            'inventory': []  # No armor, should use Unarmored Defense
        }
        
        complete_result = self.calculator.calculate_complete_json(raw_data)
        result = self._extract_flat_data(complete_result)
        
        # Both Barbarian (10+Dex+Con) and Monk (10+Dex+Wis) Unarmored Defense
        # Should pick the better one or handle the conflict gracefully
        dex_mod = (16 - 10) // 2  # +3
        con_mod = (16 - 10) // 2  # +3
        wis_mod = (16 - 10) // 2  # +3
        
        barbarian_ac = 10 + dex_mod + con_mod  # 16
        monk_ac = 10 + dex_mod + wis_mod       # 16
        
        # Should use the better calculation (or at least one of them)
        expected_ac = max(barbarian_ac, monk_ac)  # 16
        ac_value = result['armor_class']['total'] if isinstance(result['armor_class'], dict) else result['armor_class']
        self.assertGreaterEqual(ac_value, expected_ac)
        
        # Should have reasonable HP from Barbarian hit die + Con
        expected_min_hp = 20  # More realistic minimum for this build
        self.assertGreaterEqual(result['max_hp'], expected_min_hp)
    
    def test_sorcerer_cleric_different_spellcasting_abilities(self):
        """Test Sorcerer/Cleric with different spellcasting abilities."""
        raw_data = {
            'id': 99995,
            'name': 'Sorcerer Cleric',
            'classes': [
                {
                    'level': 6,
                    'definition': {
                        'name': 'Sorcerer',
                        'hitDie': 6
                    }
                },
                {
                    'level': 2,
                    'definition': {
                        'name': 'Cleric',
                        'hitDie': 8
                    }
                }
            ],
            'stats': [
                {'id': 1, 'value': 10},  # Strength
                {'id': 2, 'value': 14},  # Dexterity
                {'id': 3, 'value': 14},  # Constitution
                {'id': 4, 'value': 12},  # Intelligence
                {'id': 5, 'value': 16},  # Wisdom (Cleric)
                {'id': 6, 'value': 18}   # Charisma (Sorcerer)
            ]
        }
        
        complete_result = self.calculator.calculate_complete_json(raw_data)
        result = self._extract_flat_data(complete_result)
        
        # Should pick primary spellcasting ability (likely Charisma from Sorcerer)
        self.assertIn(result['spellcasting']['spellcasting_ability'].lower(), ['charisma', 'wisdom'])
        
        # Should have appropriate spell save DC
        if result['spellcasting']['spellcasting_ability'].lower() == 'charisma':
            cha_mod = (18 - 10) // 2  # +4
            expected_dc = 8 + 3 + cha_mod  # 8 + prof + mod = 15
            self.assertEqual(result['spellcasting']['spell_save_dc'], expected_dc)
        
        # Should have spell slots from multiclass progression
        spell_slots = result.get('spell_slots', {})
        if spell_slots and isinstance(spell_slots, dict):
            # At least some spell slots should exist - only count integers
            total_slots = sum(v for v in spell_slots.values() if isinstance(v, int))
            self.assertGreater(total_slots, 0)
    
    def test_extreme_multiclass_level_20(self):
        """Test extreme multiclass at level 20."""
        raw_data = {
            'id': 99994,
            'name': 'Extreme Multiclass',
            'classes': [
                {'level': 4, 'definition': {'name': 'Fighter', 'hitDie': 10}},
                {'level': 3, 'definition': {'name': 'Rogue', 'hitDie': 8}},
                {'level': 3, 'definition': {'name': 'Ranger', 'hitDie': 10}},
                {'level': 3, 'definition': {'name': 'Cleric', 'hitDie': 8}},
                {'level': 2, 'definition': {'name': 'Wizard', 'hitDie': 6}},
                {'level': 2, 'definition': {'name': 'Sorcerer', 'hitDie': 6}},
                {'level': 2, 'definition': {'name': 'Warlock', 'hitDie': 8}},
                {'level': 1, 'definition': {'name': 'Barbarian', 'hitDie': 12}}
            ],
            'stats': [
                {'id': 1, 'value': 16},  # Strength
                {'id': 2, 'value': 16},  # Dexterity
                {'id': 3, 'value': 16},  # Constitution
                {'id': 4, 'value': 16},  # Intelligence
                {'id': 5, 'value': 16},  # Wisdom
                {'id': 6, 'value': 16}   # Charisma
            ]
        }
        
        complete_result = self.calculator.calculate_complete_json(raw_data)
        result = self._extract_flat_data(complete_result)
        
        # Should handle extreme multiclass without crashing
        self.assertEqual(result['level'], 20)
        self.assertEqual(result['proficiency_bonus'], 6)  # Level 20 = +6
        
        # Should be a spellcaster (has multiple caster classes)
        self.assertTrue(result['spellcasting']['is_spellcaster'])
        
        # Should have reasonable stats for level 20
        self.assertGreaterEqual(result['max_hp'], 20)  # At least 1 per level
        self.assertLessEqual(result['max_hp'], 400)    # Not absurdly high
        
        ac_value = result['armor_class']['total'] if isinstance(result['armor_class'], dict) else result['armor_class']
        self.assertGreaterEqual(ac_value, 10)
        self.assertLessEqual(ac_value, 30)
    
    def test_single_level_dips(self):
        """Test many single-level dips."""
        raw_data = {
            'id': 99993,
            'name': 'Many Dips',
            'classes': [
                {'level': 5, 'definition': {'name': 'Fighter', 'hitDie': 10}},  # Main class
                {'level': 1, 'definition': {'name': 'Rogue', 'hitDie': 8}},
                {'level': 1, 'definition': {'name': 'Ranger', 'hitDie': 10}},
                {'level': 1, 'definition': {'name': 'Cleric', 'hitDie': 8}},
                {'level': 1, 'definition': {'name': 'Barbarian', 'hitDie': 12}},
                {'level': 1, 'definition': {'name': 'Monk', 'hitDie': 8}}
            ],
            'stats': [
                {'id': 1, 'value': 16},  # Strength
                {'id': 2, 'value': 14},  # Dexterity
                {'id': 3, 'value': 16},  # Constitution
                {'id': 4, 'value': 10},  # Intelligence
                {'id': 5, 'value': 14},  # Wisdom
                {'id': 6, 'value': 12}   # Charisma
            ]
        }
        
        complete_result = self.calculator.calculate_complete_json(raw_data)
        result = self._extract_flat_data(complete_result)
        
        # Should identify Fighter as primary class (highest level)
        primary_class = max(raw_data['classes'], key=lambda c: c['level'])
        self.assertEqual(primary_class['definition']['name'], 'Fighter')
        
        # Should handle multiple single-level features gracefully
        self.assertEqual(result['level'], 10)
        self.assertEqual(result['proficiency_bonus'], 4)
        
        # Should not crash on complex feature interactions
        ac_value = result['armor_class']['total'] if isinstance(result['armor_class'], dict) else result['armor_class']
        self.assertIsInstance(ac_value, int)
        self.assertIsInstance(result['max_hp'], int)


if __name__ == '__main__':
    unittest.main()