import unittest
from src.calculators.equipment_integration import EquipmentIntegrationCalculator, EquipmentBonuses
from src.calculators.utils.magic_item_parser import MagicItemBonus

class TestEquipmentIntegrationCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = EquipmentIntegrationCalculator()
    
    def test_calculate_weapon_bonuses(self):
        """Test calculating weapon bonuses from equipped magic weapons."""
        character_data = {
            'inventory': {
                'equipped_items': [
                    {
                        'name': 'Longsword +2',
                        'definition': {
                            'filterType': 'weapon',
                            'type': 'martial weapon'
                        }
                    },
                    {
                        'name': 'Flame Tongue',
                        'definition': {
                            'description': 'You have a +1 bonus to attack and damage rolls made with this magic weapon.',
                            'filterType': 'weapon',
                            'type': 'martial weapon'
                        }
                    }
                ]
            }
        }
        
        result = self.calculator.calculate(character_data)
        equipment_bonuses = result['equipment_bonuses']
        
        # Should have weapon attack and damage bonuses
        self.assertGreater(equipment_bonuses.get_total_weapon_attack_bonus(), 0)
        self.assertGreater(equipment_bonuses.get_total_weapon_damage_bonus(), 0)
    
    def test_calculate_skill_bonuses(self):
        """Test calculating skill bonuses from equipped magic items."""
        character_data = {
            'inventory': {
                'equipped_items': [
                    {
                        'name': 'Cloak of Elvenkind',
                        'definition': {
                            'description': 'While you wear this cloak, you have advantage on Dexterity (Stealth) checks. You also gain a +2 bonus to Perception checks.',
                            'filterType': 'wondrous-item'
                        }
                    }
                ]
            }
        }
        
        result = self.calculator.calculate(character_data)
        equipment_bonuses = result['equipment_bonuses']
        
        # Should have skill bonuses
        self.assertEqual(equipment_bonuses.get_skill_bonus('stealth'), 5)  # Advantage = +5
        self.assertEqual(equipment_bonuses.get_skill_bonus('perception'), 2)
    
    def test_calculate_ac_bonuses(self):
        """Test calculating AC bonuses from equipped magic items."""
        character_data = {
            'inventory': {
                'equipped_items': [
                    {
                        'name': 'Ring of Protection',
                        'definition': {
                            'description': 'You gain a +1 bonus to AC and saving throws while wearing this ring.',
                            'filterType': 'ring'
                        }
                    },
                    {
                        'name': 'Chain Mail +2',
                        'definition': {
                            'filterType': 'armor',
                            'type': 'heavy armor'
                        }
                    }
                ]
            }
        }
        
        result = self.calculator.calculate(character_data)
        equipment_bonuses = result['equipment_bonuses']
        
        # Should have AC bonuses from both items
        self.assertEqual(equipment_bonuses.ac_bonuses, 3)  # +1 from ring, +2 from armor
    
    def test_calculate_ability_bonuses(self):
        """Test calculating ability score bonuses from equipped magic items."""
        character_data = {
            'inventory': {
                'equipped_items': [
                    {
                        'name': 'Gauntlets of Ogre Power',
                        'definition': {
                            'description': 'Your Strength score is 19 while you wear these gauntlets.',
                            'filterType': 'wondrous-item'
                        }
                    },
                    {
                        'name': 'Headband of Intellect',
                        'definition': {
                            'description': 'Your Intelligence score is 19 while you wear this headband.',
                            'filterType': 'wondrous-item'
                        }
                    }
                ]
            }
        }
        
        result = self.calculator.calculate(character_data)
        equipment_bonuses = result['equipment_bonuses']
        
        # Should have ability set values
        self.assertEqual(equipment_bonuses.get_ability_set_value('strength'), 19)
        self.assertEqual(equipment_bonuses.get_ability_set_value('intelligence'), 19)
    
    def test_apply_ability_bonuses_to_scores(self):
        """Test applying magic item bonuses to ability scores."""
        base_scores = {
            'strength': 14,
            'dexterity': 16,
            'constitution': 13,
            'intelligence': 12,
            'wisdom': 15,
            'charisma': 10
        }
        
        character_data = {
            'inventory': {
                'equipped_items': [
                    {
                        'name': 'Gauntlets of Ogre Power',
                        'definition': {
                            'description': 'Your Strength score is 19 while you wear these gauntlets.',
                            'filterType': 'wondrous-item'
                        }
                    }
                ]
            }
        }
        
        enhanced_scores = self.calculator.apply_ability_bonuses_to_scores(base_scores, character_data)
        
        # Strength should be set to 19
        self.assertEqual(enhanced_scores['strength']['final_score'], 19)
        self.assertEqual(enhanced_scores['strength']['modifier'], 4)  # (19-10)//2 = 4
        
        # Other abilities should remain unchanged
        self.assertEqual(enhanced_scores['dexterity']['final_score'], 16)
        self.assertEqual(enhanced_scores['dexterity']['modifier'], 3)
    
    def test_equipment_bonuses_consolidation(self):
        """Test that bonuses from multiple items are properly consolidated."""
        bonuses = EquipmentBonuses()
        
        # Add bonuses from multiple items
        item_bonuses_1 = [
            MagicItemBonus('attack', 1, 'weapon'),
            MagicItemBonus('skill', 2, 'stealth')
        ]
        
        item_bonuses_2 = [
            MagicItemBonus('attack', 2, 'weapon'),
            MagicItemBonus('skill', 1, 'stealth'),
            MagicItemBonus('ac', 1, 'armor')
        ]
        
        self.calculator._integrate_item_bonuses(bonuses, item_bonuses_1, 'Item 1')
        self.calculator._integrate_item_bonuses(bonuses, item_bonuses_2, 'Item 2')
        
        # Bonuses should stack
        self.assertEqual(bonuses.get_total_weapon_attack_bonus(), 3)  # 1 + 2
        self.assertEqual(bonuses.get_skill_bonus('stealth'), 3)  # 2 + 1
        self.assertEqual(bonuses.ac_bonuses, 1)
    
    def test_conditional_bonuses_tracking(self):
        """Test that conditional bonuses are properly tracked."""
        character_data = {
            'inventory': {
                'equipped_items': [
                    {
                        'name': 'Cloak of Protection',
                        'definition': {
                            'description': 'You gain a +1 bonus to AC and saving throws while wearing this cloak.',
                            'filterType': 'wondrous-item'
                        }
                    }
                ]
            }
        }
        
        conditional_bonuses = self.calculator.get_conditional_bonuses_for_character(character_data)
        
        # Should track conditional bonuses (items with "while" conditions)
        # Note: This depends on the magic item parser detecting conditions
        # For now, just verify the method works
        self.assertIsInstance(conditional_bonuses, list)
    
    def test_weapon_specific_bonuses(self):
        """Test weapon-specific bonuses vs general weapon bonuses."""
        bonuses = EquipmentBonuses()
        bonuses.weapon_attack_bonuses['weapon'] = 1  # General weapon bonus
        bonuses.weapon_attack_bonuses['longsword'] = 2  # Specific weapon bonus
        
        # General weapon should get general bonus only
        self.assertEqual(bonuses.get_total_weapon_attack_bonus(), 1)
        
        # Specific weapon should get both bonuses
        self.assertEqual(bonuses.get_total_weapon_attack_bonus('Longsword'), 3)
    
    def test_empty_equipment(self):
        """Test handling of characters with no equipped items."""
        character_data = {
            'inventory': {
                'equipped_items': []
            }
        }
        
        result = self.calculator.calculate(character_data)
        equipment_bonuses = result['equipment_bonuses']
        
        # Should have no bonuses
        self.assertEqual(equipment_bonuses.get_total_weapon_attack_bonus(), 0)
        self.assertEqual(equipment_bonuses.get_skill_bonus('stealth'), 0)
        self.assertEqual(equipment_bonuses.ac_bonuses, 0)
    
    def test_invalid_equipment_data(self):
        """Test handling of invalid equipment data."""
        character_data = {
            'inventory': {
                'equipped_items': [
                    None,  # Invalid item
                    {},    # Empty item
                    {      # Item with no definition
                        'name': 'Broken Item'
                    }
                ]
            }
        }
        
        # Should not crash
        result = self.calculator.calculate(character_data)
        equipment_bonuses = result['equipment_bonuses']
        
        # Should have no bonuses from invalid items
        self.assertEqual(equipment_bonuses.get_total_weapon_attack_bonus(), 0)
    
    def test_get_helper_methods(self):
        """Test the convenience helper methods."""
        character_data = {
            'inventory': {
                'equipped_items': [
                    {
                        'name': 'Ring of Protection',
                        'definition': {
                            'description': 'You gain a +1 bonus to AC and saving throws while wearing this ring.',
                            'filterType': 'ring'
                        }
                    }
                ]
            }
        }
        
        # Test helper methods
        skill_bonuses = self.calculator.get_skill_bonuses_for_character(character_data)
        ac_bonus = self.calculator.get_ac_bonus_for_character(character_data)
        ability_bonuses = self.calculator.get_ability_bonuses_for_character(character_data)
        
        self.assertIsInstance(skill_bonuses, dict)
        self.assertEqual(ac_bonus, 1)
        self.assertIsInstance(ability_bonuses, dict)

if __name__ == '__main__':
    unittest.main()