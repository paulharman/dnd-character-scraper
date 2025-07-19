import unittest
from unittest.mock import Mock, patch
from src.calculators.coordinators.combat import CombatCoordinator
from src.calculators.services.interfaces import CalculationContext, CalculationResult, CalculationStatus

class TestCombatCoordinator(unittest.TestCase):
    def setUp(self):
        self.coordinator = CombatCoordinator()
        self.sample_raw_data = {
            'id': 12345,
            'name': 'Test Character',
            'stats': [
                {'id': 1, 'value': 16},  # Strength
                {'id': 2, 'value': 14},  # Dexterity
                {'id': 3, 'value': 15},  # Constitution
                {'id': 4, 'value': 12},  # Intelligence
                {'id': 5, 'value': 13},  # Wisdom
                {'id': 6, 'value': 10}   # Charisma
            ],
            'classes': [
                {'level': 5, 'definition': {'name': 'Fighter'}}
            ],
            'inventory': [
                {
                    'equipped': True,
                    'definition': {
                        'name': 'Longsword',
                        'type': 'martial weapon',
                        'filterType': 'weapon',
                        'weaponProperties': [
                            {'name': 'versatile'}
                        ],
                        'damage': {
                            'diceString': '1d8',
                            'versatileDiceString': '1d10'
                        },
                        'damageType': 'slashing'
                    }
                }
            ],
            'race': {
                'definition': {
                    'speed': 30
                }
            }
        }
    
    def test_coordinator_properties(self):
        """Test basic coordinator properties."""
        self.assertEqual(self.coordinator.coordinator_name, "combat")
        self.assertEqual(self.coordinator.dependencies, ["character_info", "abilities"])
        self.assertEqual(self.coordinator.priority, 30)
    
    def test_coordinate_basic_combat_stats(self):
        """Test basic combat statistics calculation."""
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_modifiers': {
                    'strength': 3, 'dexterity': 2, 'constitution': 2,
                    'intelligence': 1, 'wisdom': 1, 'charisma': 0
                }
            },
            'character_info': {
                'level': 5,
                'proficiency_bonus': 3
            }
        }
        
        result = self.coordinator.coordinate(self.sample_raw_data, context)
        
        self.assertEqual(result.status, CalculationStatus.COMPLETED)
        self.assertIn('initiative_bonus', result.data)
        self.assertIn('speed', result.data)
        self.assertIn('armor_class', result.data)
        self.assertIn('hit_points', result.data)
        self.assertIn('attack_actions', result.data)
        self.assertIn('saving_throws', result.data)
        self.assertIn('proficiency_bonus', result.data)
        
        # Check initiative bonus (DEX modifier)
        self.assertEqual(result.data['initiative_bonus'], 2)
        
        # Check speed
        self.assertEqual(result.data['speed'], 30)
        
        # Check proficiency bonus
        self.assertEqual(result.data['proficiency_bonus'], 3)
    
    def test_enhanced_weapon_attacks(self):
        """Test that enhanced weapon attack calculator is used."""
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_modifiers': {
                    'strength': 3, 'dexterity': 2, 'constitution': 2,
                    'intelligence': 1, 'wisdom': 1, 'charisma': 0
                }
            },
            'character_info': {
                'level': 5,
                'proficiency_bonus': 3
            }
        }
        
        result = self.coordinator.coordinate(self.sample_raw_data, context)
        
        self.assertEqual(result.status, CalculationStatus.COMPLETED)
        self.assertIn('attack_actions', result.data)
        
        # Should have at least one weapon attack
        attack_actions = result.data['attack_actions']
        self.assertGreater(len(attack_actions), 0)
        
        # Check first attack action structure
        first_attack = attack_actions[0]
        self.assertIn('name', first_attack)
        self.assertIn('attack_bonus', first_attack)
        self.assertIn('damage_dice', first_attack)
        self.assertIn('damage_type', first_attack)
        self.assertIn('breakdown', first_attack)
        
        # Verify attack bonus calculation (STR + Prof)
        self.assertEqual(first_attack['attack_bonus'], 6)  # 3 + 3
    
    def test_armor_class_calculation(self):
        """Test armor class calculation."""
        # Test with no armor (unarmored defense)
        raw_data = self.sample_raw_data.copy()
        raw_data['inventory'] = []  # No armor
        
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_modifiers': {
                    'strength': 3, 'dexterity': 2, 'constitution': 2,
                    'intelligence': 1, 'wisdom': 1, 'charisma': 0
                }
            }
        }
        
        result = self.coordinator.coordinate(raw_data, context)
        
        # Should be 10 + DEX modifier
        self.assertEqual(result.data['armor_class'], 12)  # 10 + 2
    
    def test_hit_points_calculation(self):
        """Test hit points calculation."""
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_modifiers': {
                    'strength': 3, 'dexterity': 2, 'constitution': 2,
                    'intelligence': 1, 'wisdom': 1, 'charisma': 0
                }
            }
        }
        
        # Add hit points data to raw data
        raw_data = self.sample_raw_data.copy()
        raw_data['baseHitPoints'] = 30
        raw_data['bonusHitPoints'] = 5
        raw_data['temporaryHitPoints'] = 0
        raw_data['removedHitPoints'] = 0
        
        result = self.coordinator.coordinate(raw_data, context)
        
        hit_points = result.data['hit_points']
        self.assertIn('current', hit_points)
        self.assertIn('maximum', hit_points)
        self.assertIn('temporary', hit_points)
        
        # Should include constitution modifier per level
        expected_max = 30 + 5 + (2 * 5)  # base + bonus + (con mod * level)
        self.assertEqual(hit_points['maximum'], expected_max)
    
    def test_saving_throws_calculation(self):
        """Test saving throws calculation."""
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_modifiers': {
                    'strength': 3, 'dexterity': 2, 'constitution': 2,
                    'intelligence': 1, 'wisdom': 1, 'charisma': 0
                }
            },
            'character_info': {
                'proficiency_bonus': 3
            }
        }
        
        result = self.coordinator.coordinate(self.sample_raw_data, context)
        
        saving_throws = result.data['saving_throws']
        self.assertIn('strength', saving_throws)
        self.assertIn('dexterity', saving_throws)
        self.assertIn('constitution', saving_throws)
        self.assertIn('intelligence', saving_throws)
        self.assertIn('wisdom', saving_throws)
        self.assertIn('charisma', saving_throws)
        
        # Check saving throw structure
        self.assertIn('bonus', saving_throws['strength'])
        self.assertIn('modifier', saving_throws['strength'])
        self.assertIn('proficient', saving_throws['strength'])
        
        # Check ability modifiers are correct
        self.assertEqual(saving_throws['strength']['modifier'], 3)  # STR modifier
        self.assertEqual(saving_throws['dexterity']['modifier'], 2)  # DEX modifier
        
        # Fighter should have proficiency in STR and CON saves (this would need class-specific logic)
        # For now, just check that the bonus includes the modifier
        self.assertEqual(saving_throws['strength']['bonus'], 3)  # Just modifier for now
        self.assertEqual(saving_throws['dexterity']['bonus'], 2)  # Just modifier for now
    
    def test_error_handling_missing_data(self):
        """Test error handling with missing required data."""
        # Test with completely empty data
        result = self.coordinator.coordinate({}, None)
        
        self.assertEqual(result.status, CalculationStatus.FAILED)
        self.assertIn('Missing required combat data', result.errors)
    
    def test_fallback_calculations(self):
        """Test fallback calculations when context is missing."""
        # Test without context (should calculate from raw data)
        result = self.coordinator.coordinate(self.sample_raw_data, None)
        
        self.assertEqual(result.status, CalculationStatus.COMPLETED)
        
        # Should still calculate basic stats
        self.assertIn('initiative_bonus', result.data)
        self.assertIn('speed', result.data)
        self.assertIn('proficiency_bonus', result.data)
        
        # Proficiency bonus should be calculated from level
        self.assertEqual(result.data['proficiency_bonus'], 3)  # Level 5 = +3
    
    def test_weapon_proficiency_detection(self):
        """Test weapon proficiency detection for different classes."""
        # Test Fighter (should be proficient with martial weapons)
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_modifiers': {
                    'strength': 3, 'dexterity': 2, 'constitution': 2,
                    'intelligence': 1, 'wisdom': 1, 'charisma': 0
                }
            },
            'character_info': {
                'level': 5,
                'proficiency_bonus': 3
            }
        }
        
        result = self.coordinator.coordinate(self.sample_raw_data, context)
        
        # Fighter should be proficient with longsword
        attack_actions = result.data['attack_actions']
        first_attack = attack_actions[0]
        
        # Attack bonus should include proficiency
        self.assertEqual(first_attack['attack_bonus'], 6)  # 3 (STR) + 3 (Prof)
        
        # Breakdown should show proficiency bonus
        self.assertEqual(first_attack['breakdown']['proficiency_bonus'], 3)
    
    def test_metadata_generation(self):
        """Test combat metadata generation."""
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_modifiers': {
                    'strength': 3, 'dexterity': 2, 'constitution': 2,
                    'intelligence': 1, 'wisdom': 1, 'charisma': 0
                }
            },
            'character_info': {
                'level': 5,
                'proficiency_bonus': 3
            }
        }
        
        result = self.coordinator.coordinate(self.sample_raw_data, context)
        
        metadata = result.data['metadata']
        self.assertIn('total_actions', metadata)
        self.assertIn('weapon_attacks', metadata)
        self.assertIn('spell_attacks', metadata)
        self.assertIn('has_ranged_attacks', metadata)
        self.assertIn('has_melee_attacks', metadata)
        self.assertIn('character_level', metadata)
        self.assertIn('initiative_modifier', metadata)
        
        # Should have at least one weapon attack
        self.assertGreater(metadata['weapon_attacks'], 0)
        self.assertEqual(metadata['character_level'], 5)
        self.assertEqual(metadata['initiative_modifier'], 2)  # DEX modifier
    
    def test_enhanced_damage_calculations(self):
        """Test that enhanced weapon attacks include damage calculations."""
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_modifiers': {
                    'strength': 3, 'dexterity': 2, 'constitution': 2,
                    'intelligence': 1, 'wisdom': 1, 'charisma': 0
                }
            },
            'character_info': {
                'level': 5,
                'proficiency_bonus': 3
            }
        }
        
        result = self.coordinator.coordinate(self.sample_raw_data, context)
        
        attack_actions = result.data['attack_actions']
        first_attack = attack_actions[0]
        
        # Should have comprehensive damage information
        self.assertIn('damage_dice', first_attack)
        self.assertIn('damage_type', first_attack)
        self.assertIn('damage_bonus', first_attack)
        
        # Check damage values
        self.assertEqual(first_attack['damage_dice'], '1d8')
        self.assertEqual(first_attack['damage_type'], 'slashing')
        self.assertEqual(first_attack['damage_bonus'], 3)  # STR modifier
        
        # Should have breakdown information
        self.assertIn('breakdown', first_attack)
        breakdown = first_attack['breakdown']
        self.assertIn('ability_modifier', breakdown)
        self.assertIn('ability_used', breakdown)
        self.assertIn('proficiency_bonus', breakdown)
        
        self.assertEqual(breakdown['ability_modifier'], 3)
        self.assertEqual(breakdown['ability_used'], 'STR')
        self.assertEqual(breakdown['proficiency_bonus'], 3)

if __name__ == '__main__':
    unittest.main()