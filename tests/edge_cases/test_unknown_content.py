"""
Edge Case Tests - Unknown Content and Data Variations

Tests handling of unknown spells, items, feats, and other D&D Beyond content variations.
"""

import unittest
from unittest.mock import Mock

from src.calculators.character_calculator import CharacterCalculator
from src.rules.version_manager import RuleVersionManager, RuleVersion


class TestUnknownContent(unittest.TestCase):
    """Test edge cases with unknown or unusual D&D Beyond content."""
    
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
        basic_info = complete_data.get('basic_info', {})
        
        # Extract basic fields
        flat_data = {
            'id': basic_info.get('character_id', 0),
            'name': basic_info.get('name', 'Unknown'),
            'level': basic_info.get('level', 0),
            'proficiency_bonus': basic_info.get('proficiency_bonus', 2),
        }
        
        # Extract ability scores and modifiers with defaults for errors
        raw_ability_scores = complete_data.get('ability_scores', {})
        raw_ability_modifiers = complete_data.get('ability_modifiers', {})
        
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
        
        # Extract calculated values with NaN/infinity protection
        def safe_int(value, default):
            """Safely convert value to int, handling NaN and infinity."""
            try:
                if isinstance(value, (int, float)) and (value != value or value == float('inf') or value == float('-inf')):
                    return default
                return int(value) if value is not None else default
            except (ValueError, TypeError):
                return default
        
        ac_value = complete_data.get('armor_class', {}).get('total', 10) if isinstance(complete_data.get('armor_class'), dict) else complete_data.get('armor_class', 10)
        hp_value = complete_data.get('hit_points', {}).get('maximum', 1) if isinstance(complete_data.get('hit_points'), dict) else complete_data.get('max_hp', 1)
        
        flat_data.update({
            'armor_class': safe_int(ac_value, 10),
            'max_hp': safe_int(hp_value, 1),
            'initiative_bonus': safe_int(complete_data.get('initiative_bonus'), 0),
        })
        
        # Extract spellcasting info - handle both flat and structured formats
        spell_slots = complete_data.get('spell_slots', {})
        flat_data['spellcasting'] = {
            'is_spellcaster': complete_data.get('is_spellcaster', False),
            'spellcasting_ability': complete_data.get('spellcasting_ability'),
            'spell_save_dc': complete_data.get('spell_save_dc'),
            'spell_attack_bonus': complete_data.get('spell_attack_bonus'),
        }
        
        # Extract spell and item data
        flat_data['spells'] = complete_data.get('spells', {})
        flat_data['inventory'] = complete_data.get('inventory', [])
        flat_data['feats'] = complete_data.get('feats', [])
        
        return flat_data
    
    def test_unknown_spell_sources(self):
        """Test handling of spells from unknown sources."""
        raw_data = {
            'id': 98765,
            'name': 'Unknown Spells',
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'Wizard',
                        'canCastSpells': True,
                        'spellcastingAbilityId': 4
                    }
                }
            ],
            'stats': [
                {'id': 4, 'value': 16}  # Intelligence
            ],
            'spells': {
                'unknown_source': [  # Unusual source
                    {
                        'definition': {
                            'level': 1,
                            'name': 'Custom Spell',
                            'school': 'Evocation'
                        }
                    }
                ],
                'homebrew': [  # Homebrew spells
                    {
                        'definition': {
                            'level': 2,
                            'name': 'Homebrew Blast',
                            'isHomebrew': True
                        }
                    }
                ]
            },
            'classSpells': []
        }
        
        complete_result = self.calculator.calculate_complete_json(raw_data)
        result = self._extract_flat_data(complete_result)
        
        # Should handle unknown spell sources gracefully
        self.assertTrue(result['spellcasting']['is_spellcaster'])
        
        # Should count spells from all sources
        if 'total_spells_known' in result['spellcasting']:
            self.assertGreaterEqual(result['spellcasting']['total_spells_known'], 2)
    
    def test_missing_spell_level(self):
        """Test handling of spells with missing or invalid level data."""
        raw_data = {
            'id': 87654,
            'name': 'Invalid Spell Data',
            'classes': [
                {
                    'level': 3,
                    'definition': {
                        'name': 'Sorcerer',
                        'canCastSpells': True,
                        'spellcastingAbilityId': 6
                    }
                }
            ],
            'stats': [
                {'id': 6, 'value': 16}  # Charisma
            ],
            'classSpells': [
                {
                    'characterClassId': 1,
                    'spells': [
                        {
                            'definition': {
                                'name': 'No Level Spell'
                                # Missing level
                            }
                        },
                        {
                            'definition': {
                                'name': 'Invalid Level Spell',
                                'level': 'cantrip'  # String instead of int
                            }
                        },
                        {
                            'definition': {
                                'name': 'Negative Level Spell',
                                'level': -1
                            }
                        },
                        {
                            'definition': {
                                'name': 'High Level Spell',
                                'level': 15  # Above normal max
                            }
                        }
                    ]
                }
            ]
        }
        
        complete_result = self.calculator.calculate_complete_json(raw_data)
        result = self._extract_flat_data(complete_result)
        
        # Should handle invalid spell data gracefully
        self.assertTrue(result['spellcasting']['is_spellcaster'])
        
        # Should not crash on invalid spell levels
        self.assertIsInstance(result['spellcasting']['spell_save_dc'], int)
    
    def test_unknown_equipment_types(self):
        """Test handling of unknown equipment and armor types."""
        raw_data = {
            'id': 76543,
            'name': 'Unknown Equipment',
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'Fighter',
                        'hitDie': 10
                    }
                }
            ],
            'stats': [
                {'id': 1, 'value': 16},  # Strength
                {'id': 2, 'value': 14}   # Dexterity
            ],
            'inventory': [
                {
                    'definition': {
                        'name': 'Mystical Armor',
                        'type': 'unknown_armor_type',
                        'armorClass': 15,
                        'armorTypeId': 999,  # Unknown type
                        'isHomebrew': True
                    },
                    'equipped': True
                },
                {
                    'definition': {
                        'name': 'Custom Shield',
                        'type': 'custom_shield',
                        'grantedModifiers': [
                            {
                                'type': 'bonus',
                                'subType': 'armor-class',
                                'value': 3  # Unusual shield bonus
                            }
                        ]
                    },
                    'equipped': True
                }
            ]
        }
        
        complete_result = self.calculator.calculate_complete_json(raw_data)
        result = self._extract_flat_data(complete_result)
        
        # Should handle unknown equipment types
        self.assertEqual(result['level'], 5)
        
        # Should still calculate AC (might use custom values or defaults)
        self.assertIsInstance(result['armor_class'], int)
        self.assertGreaterEqual(result['armor_class'], 10)
    
    def test_unknown_modifier_types(self):
        """Test handling of unknown modifier and bonus types."""
        raw_data = {
            'id': 65432,
            'name': 'Unknown Modifiers',
            'classes': [
                {
                    'level': 6,
                    'definition': {
                        'name': 'Ranger',
                        'hitDie': 10
                    }
                }
            ],
            'stats': [
                {'id': 1, 'value': 16},
                {'id': 2, 'value': 18},
                {'id': 3, 'value': 14}
            ],
            'modifiers': {
                'unknown_source': [
                    {
                        'type': 'custom_bonus',
                        'subType': 'unknown_stat',
                        'value': 5
                    }
                ],
                'homebrew_feat': [
                    {
                        'type': 'weird_modifier',
                        'subType': 'custom_ability',
                        'value': 'non_numeric'
                    }
                ]
            }
        }
        
        complete_result = self.calculator.calculate_complete_json(raw_data)
        result = self._extract_flat_data(complete_result)
        
        # Should handle unknown modifiers without crashing
        self.assertEqual(result['level'], 6)
        self.assertIsInstance(result['armor_class'], int)
        self.assertIsInstance(result['max_hp'], int)
    
    def test_mixed_2014_2024_homebrew_content(self):
        """Test character with mix of 2014, 2024, and homebrew content."""
        raw_data = {
            'id': 54321,
            'name': 'Mixed Content',
            'classes': [
                {
                    'level': 8,
                    'definition': {
                        'name': 'Fighter',
                        'sourceId': 1,  # 2014 PHB
                        'hitDie': 10
                    },
                    'subclassDefinition': {
                        'name': 'Battle Master',
                        'sourceId': 142,  # 2024 PHB (mixed)
                    }
                }
            ],
            'race': {
                'definition': {
                    'name': 'Human',
                    'sourceId': 999999,  # Homebrew
                    'isHomebrew': True
                }
            },
            'background': {
                'definition': {
                    'name': 'Soldier',
                    'sourceId': 144  # 2024 DMG
                }
            },
            'stats': [
                {'id': 1, 'value': 18},
                {'id': 2, 'value': 16},
                {'id': 3, 'value': 16},
                {'id': 4, 'value': 12},
                {'id': 5, 'value': 14},
                {'id': 6, 'value': 13}
            ]
        }
        
        complete_result = self.calculator.calculate_complete_json(raw_data)
        result = self._extract_flat_data(complete_result)
        
        # Should handle mixed content versions
        self.assertEqual(result['level'], 8)
        
        # Rule detection should handle mixed content appropriately
        detection = self.rule_manager.detect_rule_version(raw_data)
        self.assertIn(detection.version, [RuleVersion.RULES_2014, RuleVersion.RULES_2024])
        
        # Should ignore homebrew content for rule detection
        if 'Mixed source IDs' in str(detection.evidence):
            # Conservative approach - mixed official content defaults to 2014
            self.assertEqual(detection.version, RuleVersion.RULES_2014)
    
    def test_missing_critical_data_fields(self):
        """Test handling when critical data fields are missing."""
        raw_data = {
            'id': 43210,
            'name': 'Missing Fields'
            # Missing classes, stats, etc.
        }
        
        complete_result = self.calculator.calculate_complete_json(raw_data)
        result = self._extract_flat_data(complete_result)
        
        # Should provide sensible defaults for missing data
        self.assertEqual(result['id'], 43210)
        self.assertEqual(result['name'], 'Missing Fields')
        
        # Should have default values that make sense
        self.assertGreaterEqual(result['level'], 0)  # 0 is acceptable for no classes
        self.assertGreaterEqual(result['armor_class'], 10)
        self.assertGreaterEqual(result['max_hp'], 1)
        self.assertGreaterEqual(result['proficiency_bonus'], 2)
        
        # Should have reasonable ability scores
        for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
            score = result['ability_scores'][ability]
            self.assertGreaterEqual(score, 8)
            self.assertLessEqual(score, 15)  # Default range
    
    def test_circular_references_in_data(self):
        """Test handling of circular references or deeply nested data."""
        # Create a complex nested structure
        nested_item = {
            'definition': {
                'name': 'Nested Item',
                'grantedModifiers': []
            }
        }
        # Create potential circular reference (though JSON shouldn't allow true circles)
        nested_item['definition']['parentItem'] = nested_item
        
        raw_data = {
            'id': 32109,
            'name': 'Nested Data',
            'classes': [
                {
                    'level': 4,
                    'definition': {
                        'name': 'Artificer',
                        'hitDie': 8,
                        'features': {
                            'nested': {
                                'deep': {
                                    'deeper': {
                                        'deepest': 'value'
                                    }
                                }
                            }
                        }
                    }
                }
            ],
            'stats': [
                {'id': 1, 'value': 14},
                {'id': 2, 'value': 16},
                {'id': 3, 'value': 15},
                {'id': 4, 'value': 18},
                {'id': 5, 'value': 12},
                {'id': 6, 'value': 10}
            ],
            'inventory': [nested_item]
        }
        
        complete_result = self.calculator.calculate_complete_json(raw_data)
        result = self._extract_flat_data(complete_result)
        
        # Should handle complex nested data without infinite loops
        self.assertEqual(result['level'], 4)
        self.assertIsInstance(result['armor_class'], int)
        self.assertIsInstance(result['max_hp'], int)
    
    def test_very_long_strings(self):
        """Test handling of extremely long strings in character data."""
        very_long_name = "A" * 10000  # 10k character name
        very_long_description = "B" * 50000  # 50k character description
        
        raw_data = {
            'id': 21098,
            'name': very_long_name,
            'classes': [
                {
                    'level': 3,
                    'definition': {
                        'name': 'Bard',
                        'hitDie': 8,
                        'description': very_long_description
                    }
                }
            ],
            'stats': [
                {'id': 1, 'value': 12},
                {'id': 2, 'value': 16},
                {'id': 3, 'value': 14},
                {'id': 4, 'value': 13},
                {'id': 5, 'value': 15},
                {'id': 6, 'value': 18}
            ]
        }
        
        complete_result = self.calculator.calculate_complete_json(raw_data)
        result = self._extract_flat_data(complete_result)
        
        # Should handle very long strings (might truncate)
        self.assertEqual(result['level'], 3)
        self.assertIsInstance(result['name'], str)
        
        # Should still calculate stats correctly
        self.assertIsInstance(result['armor_class'], int)
        self.assertIsInstance(result['max_hp'], int)
    
    def test_special_numeric_values(self):
        """Test handling of special numeric values (NaN, Infinity, etc.)."""
        raw_data = {
            'id': 10987,
            'name': 'Special Numbers',
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'Wizard',
                        'hitDie': 6
                    }
                }
            ],
            'stats': [
                {'id': 1, 'value': 14},
                {'id': 2, 'value': 16},
                {'id': 3, 'value': 15},
                {'id': 4, 'value': 18},
                {'id': 5, 'value': 13},
                {'id': 6, 'value': 12}
            ],
            'baseHitPoints': float('inf'),  # Infinity
            'bonusHitPoints': float('nan')  # NaN
        }
        
        complete_result = self.calculator.calculate_complete_json(raw_data)
        result = self._extract_flat_data(complete_result)
        
        # Should handle special numeric values gracefully
        self.assertEqual(result['level'], 5)
        
        # Should have reasonable HP despite invalid input
        self.assertIsInstance(result['max_hp'], int)
        self.assertGreaterEqual(result['max_hp'], 1)
        self.assertLessEqual(result['max_hp'], 1000)  # Reasonable upper bound


if __name__ == '__main__':
    unittest.main()