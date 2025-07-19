import unittest
from src.calculators.damage_calculator import DamageCalculator, WeaponDamage

class TestDamageCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = DamageCalculator()
    
    def test_calculate_longsword_damage(self):
        """Test damage calculation for a longsword."""
        weapon = {
            'name': 'Longsword',
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
        
        ability_scores = {
            'strength': {'score': 16, 'modifier': 3},
            'dexterity': {'score': 14, 'modifier': 2}
        }
        
        # Test one-handed
        damage = self.calculator.calculate_weapon_damage(weapon, ability_scores, is_two_handed=False)
        
        self.assertEqual(damage.weapon_name, 'Longsword')
        self.assertEqual(damage.base_damage_dice, '1d8')
        self.assertEqual(damage.damage_modifier, 3)  # STR modifier
        self.assertEqual(damage.damage_type, 'slashing')
        self.assertEqual(damage.versatile_damage_dice, '1d10')
        self.assertEqual(damage.total_damage_expression, '1d8 + 3 slashing')
        self.assertEqual(damage.versatile_damage_expression, '1d10 + 3 slashing (versatile)')
        
        # Test two-handed
        two_handed_damage = self.calculator.calculate_weapon_damage(weapon, ability_scores, is_two_handed=True)
        self.assertEqual(two_handed_damage.base_damage_dice, '1d10')  # Uses versatile dice
        self.assertEqual(two_handed_damage.versatile_damage_dice, '1d8')  # Original becomes versatile
    
    def test_calculate_rapier_damage(self):
        """Test damage calculation for a finesse weapon (rapier)."""
        weapon = {
            'name': 'Rapier',
            'weapon_category': 'martial',
            'weapon_properties': [{'name': 'finesse'}],
            'damage': {'damage_dice': '1d8', 'damage_type': 'piercing'}
        }
        
        ability_scores = {
            'strength': {'score': 10, 'modifier': 0},
            'dexterity': {'score': 18, 'modifier': 4}
        }
        
        damage = self.calculator.calculate_weapon_damage(weapon, ability_scores)
        
        self.assertEqual(damage.weapon_name, 'Rapier')
        self.assertEqual(damage.base_damage_dice, '1d8')
        self.assertEqual(damage.damage_modifier, 4)  # DEX modifier (higher than STR)
        self.assertEqual(damage.damage_type, 'piercing')
        self.assertEqual(damage.breakdown['ability_used'], 'DEX')
        self.assertEqual(damage.total_damage_expression, '1d8 + 4 piercing')
    
    def test_calculate_magic_weapon_damage(self):
        """Test damage calculation for a magic weapon."""
        weapon = {
            'name': 'Longsword +2',
            'weapon_category': 'martial',
            'weapon_properties': [{'name': 'versatile'}],
            'damage': {'damage_dice': '1d8', 'damage_type': 'slashing'},
            'damage_bonus': 2
        }
        
        ability_scores = {
            'strength': {'score': 16, 'modifier': 3},
            'dexterity': {'score': 14, 'modifier': 2}
        }
        
        damage = self.calculator.calculate_weapon_damage(weapon, ability_scores)
        
        self.assertEqual(damage.weapon_name, 'Longsword +2')
        self.assertEqual(damage.base_damage_dice, '1d8')
        self.assertEqual(damage.damage_modifier, 3)  # STR modifier
        self.assertEqual(damage.magic_damage_bonus, 2)
        self.assertEqual(damage.total_damage_expression, '1d8 + 3 + 2 (magic) slashing')
    
    def test_calculate_shortbow_damage(self):
        """Test damage calculation for a ranged weapon."""
        weapon = {
            'name': 'Shortbow',
            'weapon_category': 'simple',
            'weapon_type': 'ranged',
            'weapon_properties': [{'name': 'ammunition'}, {'name': 'two-handed'}],
            'damage': {'damage_dice': '1d6', 'damage_type': 'piercing'}
        }
        
        ability_scores = {
            'strength': {'score': 12, 'modifier': 1},
            'dexterity': {'score': 16, 'modifier': 3}
        }
        
        damage = self.calculator.calculate_weapon_damage(weapon, ability_scores)
        
        self.assertEqual(damage.weapon_name, 'Shortbow')
        self.assertEqual(damage.base_damage_dice, '1d6')
        self.assertEqual(damage.damage_modifier, 3)  # DEX modifier for ranged
        self.assertEqual(damage.damage_type, 'piercing')
        self.assertEqual(damage.breakdown['ability_used'], 'DEX')
        self.assertEqual(damage.total_damage_expression, '1d6 + 3 piercing')
    
    def test_calculate_multiple_weapons(self):
        """Test damage calculation for multiple weapons."""
        weapons = [
            {
                'name': 'Longsword',
                'weapon_category': 'martial',
                'weapon_properties': [{'name': 'versatile'}],
                'damage': {'damage_dice': '1d8', 'damage_type': 'slashing'},
                'definition': {
                    'damage': {
                        'diceString': '1d8',
                        'versatileDiceString': '1d10'
                    }
                }
            },
            {
                'name': 'Dagger',
                'weapon_category': 'simple',
                'weapon_properties': [{'name': 'finesse'}, {'name': 'light'}, {'name': 'thrown'}],
                'damage': {'damage_dice': '1d4', 'damage_type': 'piercing'}
            }
        ]
        
        ability_scores = {
            'strength': {'score': 16, 'modifier': 3},
            'dexterity': {'score': 14, 'modifier': 2}
        }
        
        damage_list = self.calculator.calculate_multiple_weapons(weapons, ability_scores)
        
        # Should have 3 entries: Longsword, Longsword (Two-Handed), Dagger
        self.assertEqual(len(damage_list), 3)
        
        # Check longsword one-handed
        longsword_one = damage_list[0]
        self.assertEqual(longsword_one.weapon_name, 'Longsword')
        self.assertEqual(longsword_one.base_damage_dice, '1d8')
        
        # Check longsword two-handed
        longsword_two = damage_list[1]
        self.assertEqual(longsword_two.weapon_name, 'Longsword (Two-Handed)')
        self.assertEqual(longsword_two.base_damage_dice, '1d10')
        
        # Check dagger
        dagger = damage_list[2]
        self.assertEqual(dagger.weapon_name, 'Dagger')
        self.assertEqual(dagger.base_damage_dice, '1d4')
        self.assertEqual(dagger.damage_modifier, 3)  # STR is higher than DEX for finesse
    
    def test_weapon_damage_with_additional_damage(self):
        """Test weapon with additional damage sources."""
        weapon = {
            'name': 'Flametongue Longsword',
            'weapon_category': 'martial',
            'weapon_properties': [{'name': 'versatile'}],
            'damage': {'damage_dice': '1d8', 'damage_type': 'slashing'}
        }
        
        ability_scores = {
            'strength': {'score': 16, 'modifier': 3},
            'dexterity': {'score': 14, 'modifier': 2}
        }
        
        magic_bonuses = {
            'flametongue longsword': {
                'damage_bonus': 1,
                'additional_damage': [
                    {'dice': '2d6', 'bonus': 0, 'type': 'fire'}
                ]
            }
        }
        
        damage = self.calculator.calculate_weapon_damage(
            weapon, ability_scores, magic_bonuses=magic_bonuses
        )
        
        self.assertEqual(damage.weapon_name, 'Flametongue Longsword')
        self.assertEqual(len(damage.additional_damage), 1)
        self.assertEqual(damage.additional_damage[0]['dice'], '2d6')
        self.assertEqual(damage.additional_damage[0]['type'], 'fire')
        self.assertIn('+ 2d6 fire', damage.total_damage_expression)
    
    def test_damage_die_increase(self):
        """Test damage die increase for versatile weapons."""
        test_cases = [
            ('1d4', '1d6'),
            ('1d6', '1d8'),
            ('1d8', '1d10'),
            ('1d10', '1d12'),
            ('1d12', '2d6')
        ]
        
        for base_die, expected_increase in test_cases:
            result = self.calculator._increase_damage_die(base_die)
            self.assertEqual(result, expected_increase, 
                           f"Expected {base_die} to increase to {expected_increase}, got {result}")
    
    def test_negative_damage_modifier(self):
        """Test damage calculation with negative ability modifier."""
        weapon = {
            'name': 'Dagger',
            'weapon_category': 'simple',
            'weapon_properties': [{'name': 'finesse'}],
            'damage': {'damage_dice': '1d4', 'damage_type': 'piercing'}
        }
        
        ability_scores = {
            'strength': {'score': 8, 'modifier': -1},
            'dexterity': {'score': 6, 'modifier': -2}
        }
        
        damage = self.calculator.calculate_weapon_damage(weapon, ability_scores)
        
        # Should use the higher (less negative) modifier
        self.assertEqual(damage.damage_modifier, -1)  # STR is higher than DEX
        self.assertEqual(damage.breakdown['ability_used'], 'STR')
        self.assertEqual(damage.total_damage_expression, '1d4 - 1 piercing')
    
    def test_weapon_damage_dataclass_properties(self):
        """Test WeaponDamage dataclass properties."""
        damage = WeaponDamage(
            weapon_name='Test Sword',
            base_damage_dice='1d8',
            damage_modifier=3,
            damage_type='slashing',
            versatile_damage_dice='1d10',
            versatile_damage_modifier=3,
            magic_damage_bonus=2,
            additional_damage=[
                {'dice': '1d6', 'bonus': 0, 'type': 'fire'}
            ]
        )
        
        # Test total damage expression
        expected_total = '1d8 + 3 + 2 (magic) + 1d6 fire slashing'
        self.assertEqual(damage.total_damage_expression, expected_total)
        
        # Test versatile damage expression
        expected_versatile = '1d10 + 3 + 2 (magic) slashing (versatile)'
        self.assertEqual(damage.versatile_damage_expression, expected_versatile)
    
    def test_magic_bonus_from_name(self):
        """Test extracting magic bonus from weapon name."""
        weapon = {
            'name': 'Longsword +3',
            'weapon_category': 'martial',
            'damage': {'damage_dice': '1d8', 'damage_type': 'slashing'}
        }
        
        ability_scores = {
            'strength': {'score': 16, 'modifier': 3},
            'dexterity': {'score': 14, 'modifier': 2}
        }
        
        damage = self.calculator.calculate_weapon_damage(weapon, ability_scores)
        
        self.assertEqual(damage.magic_damage_bonus, 3)
        self.assertEqual(damage.total_damage_expression, '1d8 + 3 + 3 (magic) slashing')

if __name__ == '__main__':
    unittest.main()