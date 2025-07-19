import unittest
from src.calculators.enhanced_weapon_attacks import EnhancedWeaponAttackCalculator, WeaponAttack

class TestEnhancedWeaponAttackCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = EnhancedWeaponAttackCalculator()
    
    def test_calculate_longsword_attack(self):
        """Test calculation for a character with a longsword."""
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
                        'name': 'Longsword',
                        'type': 'weapon',
                        'weapon_category': 'martial',
                        'weapon_properties': [{'name': 'versatile'}],
                        'damage': {'damage_dice': '1d8', 'damage_type': 'slashing'}
                    }
                ]
            },
            'character_info': {
                'level': 5
            }
        }
        
        result = self.calculator.calculate(character_data)
        
        # Verify result structure
        self.assertIn('weapon_attacks', result)
        self.assertEqual(len(result['weapon_attacks']), 1)
        
        # Verify attack details
        attack = result['weapon_attacks'][0]
        self.assertEqual(attack.name, 'Longsword')
        self.assertEqual(attack.attack_bonus, 6)  # 3 (STR) + 3 (Prof)
        self.assertEqual(attack.damage_dice, '1d8')
        self.assertEqual(attack.damage_modifier, 3)  # 3 (STR)
        self.assertEqual(attack.damage_type, 'slashing')
        self.assertEqual(attack.weapon_type, 'melee')
        self.assertIn('versatile', attack.properties)
        
        # Verify breakdown
        self.assertEqual(attack.breakdown['ability_modifier'], 3)
        self.assertEqual(attack.breakdown['ability_used'], 'STR')
        self.assertEqual(attack.breakdown['proficiency_bonus'], 3)
        self.assertEqual(attack.breakdown['magic_bonus'], 0)
    
    def test_calculate_finesse_weapon(self):
        """Test calculation for a character with a finesse weapon (rapier)."""
        character_data = {
            'abilities': {
                'ability_scores': {
                    'strength': {'score': 10, 'modifier': 0},
                    'dexterity': {'score': 18, 'modifier': 4}
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
                        'name': 'Rapier',
                        'type': 'weapon',
                        'weapon_category': 'martial',
                        'weapon_properties': [{'name': 'finesse'}],
                        'damage': {'damage_dice': '1d8', 'damage_type': 'piercing'}
                    }
                ]
            },
            'character_info': {
                'level': 5
            }
        }
        
        result = self.calculator.calculate(character_data)
        
        # Verify attack details
        attack = result['weapon_attacks'][0]
        self.assertEqual(attack.name, 'Rapier')
        self.assertEqual(attack.attack_bonus, 7)  # 4 (DEX) + 3 (Prof)
        self.assertEqual(attack.damage_modifier, 4)  # 4 (DEX)
        self.assertEqual(attack.breakdown['ability_used'], 'DEX')
    
    def test_calculate_magic_weapon(self):
        """Test calculation for a character with a magic weapon."""
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
                        'attack_bonus': 2
                    }
                ]
            },
            'character_info': {
                'level': 5
            }
        }
        
        result = self.calculator.calculate(character_data)
        
        # Verify attack details
        attack = result['weapon_attacks'][0]
        self.assertEqual(attack.name, 'Longsword +2')
        self.assertEqual(attack.attack_bonus, 8)  # 3 (STR) + 3 (Prof) + 2 (Magic)
        self.assertEqual(attack.damage_modifier, 5)  # 3 (STR) + 2 (Magic)
        self.assertEqual(attack.breakdown['magic_bonus'], 2)
    
    def test_calculate_ranged_weapon(self):
        """Test calculation for a character with a ranged weapon."""
        character_data = {
            'abilities': {
                'ability_scores': {
                    'strength': {'score': 12, 'modifier': 1},
                    'dexterity': {'score': 16, 'modifier': 3}
                }
            },
            'proficiencies': {
                'weapon_proficiencies': [
                    {'name': 'simple weapons'}
                ]
            },
            'inventory': {
                'equipped_items': [
                    {
                        'name': 'Shortbow',
                        'type': 'weapon',
                        'weapon_category': 'simple',
                        'weapon_properties': [{'name': 'ammunition'}, {'name': 'two-handed'}],
                        'damage': {'damage_dice': '1d6', 'damage_type': 'piercing'},
                        'range': {'normal': 80, 'long': 320}
                    }
                ]
            },
            'character_info': {
                'level': 3
            }
        }
        
        result = self.calculator.calculate(character_data)
        
        # Verify attack details
        attack = result['weapon_attacks'][0]
        self.assertEqual(attack.name, 'Shortbow')
        self.assertEqual(attack.attack_bonus, 5)  # 3 (DEX) + 2 (Prof)
        self.assertEqual(attack.damage_modifier, 3)  # 3 (DEX)
        self.assertEqual(attack.weapon_type, 'ranged')
        self.assertEqual(attack.breakdown['ability_used'], 'DEX')
        self.assertEqual(attack.range_normal, 80)
        self.assertEqual(attack.range_long, 320)
    
    def test_calculate_no_proficiency(self):
        """Test calculation for a weapon without proficiency."""
        character_data = {
            'abilities': {
                'ability_scores': {
                    'strength': {'score': 14, 'modifier': 2},
                    'dexterity': {'score': 12, 'modifier': 1}
                }
            },
            'proficiencies': {
                'weapon_proficiencies': [
                    {'name': 'simple weapons'}  # No martial weapon proficiency
                ]
            },
            'inventory': {
                'equipped_items': [
                    {
                        'name': 'Longsword',
                        'type': 'weapon',
                        'weapon_category': 'martial',
                        'weapon_properties': [{'name': 'versatile'}],
                        'damage': {'damage_dice': '1d8', 'damage_type': 'slashing'}
                    }
                ]
            },
            'character_info': {
                'level': 3
            }
        }
        
        result = self.calculator.calculate(character_data)
        
        # Verify attack details (no proficiency bonus)
        attack = result['weapon_attacks'][0]
        self.assertEqual(attack.attack_bonus, 2)  # 2 (STR) + 0 (No Prof)
        self.assertEqual(attack.breakdown['proficiency_bonus'], 0)
    
    def test_calculate_empty_data(self):
        """Test calculation with empty character data."""
        result = self.calculator.calculate({})
        self.assertEqual(result, {})
    
    def test_calculate_no_weapons(self):
        """Test calculation for character with no equipped weapons."""
        character_data = {
            'abilities': {
                'ability_scores': {
                    'strength': {'score': 14, 'modifier': 2},
                    'dexterity': {'score': 12, 'modifier': 1}
                }
            },
            'proficiencies': {
                'weapon_proficiencies': []
            },
            'inventory': {
                'equipped_items': []
            },
            'character_info': {
                'level': 1
            }
        }
        
        result = self.calculator.calculate(character_data)
        
        # Should return empty weapon attacks list
        self.assertIn('weapon_attacks', result)
        self.assertEqual(len(result['weapon_attacks']), 0)
    
    def test_proficiency_bonus_calculation(self):
        """Test proficiency bonus calculation at different levels."""
        # Level 1-4: +2
        self.assertEqual(self.calculator._calculate_proficiency_bonus(1), 2)
        self.assertEqual(self.calculator._calculate_proficiency_bonus(4), 2)
        
        # Level 5-8: +3
        self.assertEqual(self.calculator._calculate_proficiency_bonus(5), 3)
        self.assertEqual(self.calculator._calculate_proficiency_bonus(8), 3)
        
        # Level 9-12: +4
        self.assertEqual(self.calculator._calculate_proficiency_bonus(9), 4)
        self.assertEqual(self.calculator._calculate_proficiency_bonus(12), 4)
        
        # Level 13-16: +5
        self.assertEqual(self.calculator._calculate_proficiency_bonus(13), 5)
        self.assertEqual(self.calculator._calculate_proficiency_bonus(16), 5)
        
        # Level 17-20: +6
        self.assertEqual(self.calculator._calculate_proficiency_bonus(17), 6)
        self.assertEqual(self.calculator._calculate_proficiency_bonus(20), 6)
    
    def test_damage_calculation_integration(self):
        """Test that damage calculation is integrated with weapon attacks."""
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
                        'name': 'Longsword',
                        'type': 'weapon',
                        'weapon_category': 'martial',
                        'weapon_properties': [{'name': 'versatile'}],
                        'damage': {'damage_dice': '1d8', 'damage_type': 'slashing'},
                        'definition': {
                            'damage': {
                                'diceString': '1d8',
                                'versatileDiceString': '1d10'
                            },
                            'damageType': 'slashing'
                        }
                    }
                ]
            },
            'character_info': {
                'level': 5
            }
        }
        
        result = self.calculator.calculate(character_data)
        attack = result['weapon_attacks'][0]
        
        # Verify damage calculation is present
        self.assertIsNotNone(attack.damage_calculation)
        self.assertEqual(attack.damage_calculation.weapon_name, 'Longsword')
        self.assertEqual(attack.damage_calculation.base_damage_dice, '1d8')
        self.assertEqual(attack.damage_calculation.damage_modifier, 3)
        self.assertEqual(attack.damage_calculation.versatile_damage_dice, '1d10')
        
        # Verify full damage expression
        expected_expression = '1d8 + 3 slashing'
        self.assertEqual(attack.full_damage_expression, expected_expression)

if __name__ == '__main__':
    unittest.main()