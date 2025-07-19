import unittest
from src.calculators.enhanced_weapon_attacks import EnhancedWeaponAttackCalculator
from src.calculators.skill_bonus_calculator import SkillBonusCalculator

class TestMagicItemIntegration(unittest.TestCase):
    def setUp(self):
        self.weapon_calculator = EnhancedWeaponAttackCalculator()
        self.skill_calculator = SkillBonusCalculator()
    
    def test_magic_weapon_attack_bonus_integration(self):
        """Test that magic weapon bonuses are properly integrated into attack calculations."""
        character_data = {
            'abilities': {
                'ability_scores': {
                    'strength': {'score': 16, 'modifier': 3},
                    'dexterity': {'score': 14, 'modifier': 2}
                }
            },
            'proficiencies': {
                'weapon_proficiencies': [
                    {'name': 'martial weapons'}
                ]
            },
            'inventory': {
                'equipped_items': [
                    {
                        'name': 'Longsword +2',
                        'type': 'weapon',
                        'weapon_category': 'martial',
                        'weapon_properties': [{'name': 'versatile'}],
                        'damage': {'damage_dice': '1d8', 'damage_type': 'slashing'},
                        'definition': {
                            'filterType': 'weapon',
                            'type': 'martial weapon'
                        }
                    }
                ]
            },
            'character_info': {
                'level': 5
            }
        }
        
        result = self.weapon_calculator.calculate(character_data)
        weapon_attacks = result.get('weapon_attacks', [])
        
        # Should have one weapon attack
        self.assertEqual(len(weapon_attacks), 1)
        
        longsword_attack = weapon_attacks[0]
        
        # Attack bonus should be: STR mod (3) + Prof bonus (3) + Magic bonus (2) = 8
        self.assertEqual(longsword_attack.attack_bonus, 8)
        
        # Damage modifier should be: STR mod (3) + Magic bonus (2) = 5
        self.assertEqual(longsword_attack.damage_modifier, 5)
        
        # Should have magic bonus in breakdown
        self.assertEqual(longsword_attack.breakdown['magic_bonus'], 2)
    
    def test_magic_item_skill_bonus_integration(self):
        """Test that magic item skill bonuses are properly integrated into skill calculations."""
        character_data = {
            'abilities': {
                'ability_scores': {
                    'dexterity': {'score': 16, 'modifier': 3},
                    'wisdom': {'score': 14, 'modifier': 2}
                }
            },
            'proficiencies': {
                'skill_proficiencies': [
                    {'name': 'stealth'}
                ]
            },
            'equipment': {
                'equipped_items': [
                    {
                        'name': 'Cloak of Elvenkind',
                        'definition': {
                            'description': 'While you wear this cloak, you have advantage on Dexterity (Stealth) checks. You also gain a +2 bonus to Perception checks.',
                            'filterType': 'wondrous-item'
                        }
                    }
                ]
            },
            'character_info': {
                'level': 5
            }
        }
        
        result = self.skill_calculator.calculate(character_data)
        skill_bonuses = result.get('skill_bonuses', [])
        
        # Find stealth and perception bonuses
        stealth_bonus = None
        perception_bonus = None
        
        for skill_bonus in skill_bonuses:
            if skill_bonus.skill_name == 'stealth':
                stealth_bonus = skill_bonus
            elif skill_bonus.skill_name == 'perception':
                perception_bonus = skill_bonus
        
        # Stealth should have magic bonus from advantage (treated as +5)
        self.assertIsNotNone(stealth_bonus)
        self.assertEqual(stealth_bonus.magic_bonus, 5)  # Advantage = +5
        
        # Total stealth bonus: DEX mod (3) + Prof bonus (3) + Magic bonus (5) = 11
        self.assertEqual(stealth_bonus.total_bonus, 11)
        
        # Perception should have magic bonus of +2
        self.assertIsNotNone(perception_bonus)
        self.assertEqual(perception_bonus.magic_bonus, 2)
        
        # Total perception bonus: WIS mod (2) + Magic bonus (2) = 4 (no proficiency)
        self.assertEqual(perception_bonus.total_bonus, 4)
    
    def test_magic_weapon_from_description(self):
        """Test parsing magic weapon bonuses from item description."""
        character_data = {
            'abilities': {
                'ability_scores': {
                    'strength': {'score': 16, 'modifier': 3}
                }
            },
            'proficiencies': {
                'weapon_proficiencies': [
                    {'name': 'martial weapons'}
                ]
            },
            'inventory': {
                'equipped_items': [
                    {
                        'name': 'Flame Tongue',
                        'type': 'weapon',
                        'weapon_category': 'martial',
                        'damage': {'damage_dice': '1d8', 'damage_type': 'slashing'},
                        'definition': {
                            'description': 'You have a +1 bonus to attack and damage rolls made with this magic weapon.',
                            'filterType': 'weapon',
                            'type': 'martial weapon'
                        }
                    }
                ]
            },
            'character_info': {
                'level': 3
            }
        }
        
        result = self.weapon_calculator.calculate(character_data)
        weapon_attacks = result.get('weapon_attacks', [])
        
        # Should have one weapon attack
        self.assertEqual(len(weapon_attacks), 1)
        
        flame_tongue_attack = weapon_attacks[0]
        
        # Attack bonus should be: STR mod (3) + Prof bonus (2) + Magic bonus (1) = 6
        self.assertEqual(flame_tongue_attack.attack_bonus, 6)
        
        # Should have magic bonus in breakdown
        self.assertEqual(flame_tongue_attack.breakdown['magic_bonus'], 1)
    
    def test_no_magic_items(self):
        """Test that calculations work correctly when no magic items are equipped."""
        character_data = {
            'abilities': {
                'ability_scores': {
                    'strength': {'score': 16, 'modifier': 3},
                    'dexterity': {'score': 14, 'modifier': 2}
                }
            },
            'proficiencies': {
                'weapon_proficiencies': [
                    {'name': 'martial weapons'}
                ],
                'skill_proficiencies': [
                    {'name': 'athletics'}
                ]
            },
            'inventory': {
                'equipped_items': [
                    {
                        'name': 'Longsword',
                        'type': 'weapon',
                        'weapon_category': 'martial',
                        'damage': {'damage_dice': '1d8', 'damage_type': 'slashing'}
                    }
                ]
            },
            'equipment': {
                'equipped_items': []
            },
            'character_info': {
                'level': 3
            }
        }
        
        # Test weapon calculations
        weapon_result = self.weapon_calculator.calculate(character_data)
        weapon_attacks = weapon_result.get('weapon_attacks', [])
        
        self.assertEqual(len(weapon_attacks), 1)
        longsword_attack = weapon_attacks[0]
        
        # Attack bonus should be: STR mod (3) + Prof bonus (2) + Magic bonus (0) = 5
        self.assertEqual(longsword_attack.attack_bonus, 5)
        self.assertEqual(longsword_attack.breakdown['magic_bonus'], 0)
        
        # Test skill calculations
        skill_result = self.skill_calculator.calculate(character_data)
        skill_bonuses = skill_result.get('skill_bonuses', [])
        
        athletics_bonus = None
        for skill_bonus in skill_bonuses:
            if skill_bonus.skill_name == 'athletics':
                athletics_bonus = skill_bonus
                break
        
        self.assertIsNotNone(athletics_bonus)
        # Athletics bonus should be: STR mod (3) + Prof bonus (2) + Magic bonus (0) = 5
        self.assertEqual(athletics_bonus.total_bonus, 5)
        self.assertEqual(athletics_bonus.magic_bonus, 0)

if __name__ == '__main__':
    unittest.main()