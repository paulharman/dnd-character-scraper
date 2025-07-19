import unittest
from src.calculators.utils.magic_item_parser import MagicItemParser, MagicItemBonus

class TestMagicItemParser(unittest.TestCase):
    def setUp(self):
        self.parser = MagicItemParser()
    
    def test_parse_magic_weapon_from_name(self):
        """Test parsing magic weapon bonuses from item name."""
        weapon = {
            'name': 'Longsword +2',
            'definition': {
                'filterType': 'weapon',
                'type': 'martial weapon',
                'weaponProperties': [{'name': 'versatile'}]
            }
        }
        
        bonuses = self.parser.parse_item_bonuses(weapon)
        
        # Should find attack and damage bonuses
        self.assertEqual(len(bonuses), 2)
        
        bonus_types = [b.bonus_type for b in bonuses]
        self.assertIn('attack', bonus_types)
        self.assertIn('damage', bonus_types)
        
        # Both should be +2
        for bonus in bonuses:
            self.assertEqual(bonus.bonus_value, 2)
            self.assertEqual(bonus.target, 'weapon')
    
    def test_parse_magic_armor_from_name(self):
        """Test parsing magic armor bonuses from item name."""
        armor = {
            'name': 'Chain Mail +1',
            'definition': {
                'filterType': 'armor',
                'type': 'heavy armor'
            }
        }
        
        bonuses = self.parser.parse_item_bonuses(armor)
        
        # Should find AC bonus
        self.assertEqual(len(bonuses), 1)
        self.assertEqual(bonuses[0].bonus_type, 'ac')
        self.assertEqual(bonuses[0].bonus_value, 1)
        self.assertEqual(bonuses[0].target, 'armor')
    
    def test_parse_skill_bonus_from_description(self):
        """Test parsing skill bonuses from item description."""
        item = {
            'name': 'Cloak of Elvenkind',
            'definition': {
                'description': 'While you wear this cloak, you have advantage on Dexterity (Stealth) checks. You also gain a +2 bonus to Perception checks.',
                'filterType': 'wondrous-item'
            }
        }
        
        bonuses = self.parser.parse_item_bonuses(item)
        
        # Should find bonuses for Stealth (advantage = +5) and Perception (+2)
        skill_bonuses = self.parser.get_skill_bonuses(bonuses)
        
        self.assertIn('stealth', skill_bonuses)
        self.assertIn('perception', skill_bonuses)
        self.assertEqual(skill_bonuses['stealth'], 5)  # Advantage
        self.assertEqual(skill_bonuses['perception'], 2)
    
    def test_parse_ability_score_bonus(self):
        """Test parsing ability score bonuses from description."""
        item = {
            'name': 'Gauntlets of Ogre Power',
            'definition': {
                'description': 'Your Strength score is 19 while you wear these gauntlets. They have no effect on you if your Strength is already 19 or higher.',
                'filterType': 'wondrous-item'
            }
        }
        
        bonuses = self.parser.parse_item_bonuses(item)
        
        # Should find ability score bonus
        ability_bonuses = [b for b in bonuses if b.bonus_type == 'ability_set']
        self.assertEqual(len(ability_bonuses), 1)
        self.assertEqual(ability_bonuses[0].target, 'strength')
        self.assertEqual(ability_bonuses[0].bonus_value, 19)  # Set to 19
    
    def test_parse_ac_bonus_from_description(self):
        """Test parsing AC bonuses from item description."""
        item = {
            'name': 'Ring of Protection',
            'definition': {
                'description': 'You gain a +1 bonus to AC and saving throws while wearing this ring.',
                'filterType': 'ring'
            }
        }
        
        bonuses = self.parser.parse_item_bonuses(item)
        
        # Should find AC bonus
        ac_bonus = self.parser.get_ac_bonus(bonuses)
        self.assertEqual(ac_bonus, 1)
    
    def test_parse_weapon_bonuses_from_description(self):
        """Test parsing weapon bonuses from description text."""
        weapon = {
            'name': 'Flame Tongue',
            'definition': {
                'description': 'You can use a bonus action to speak this magic sword\'s command word, causing flames to erupt from the blade. These flames shed bright light in a 40-foot radius and dim light for an additional 40 feet. While the sword is ablaze, it deals an extra 2d6 fire damage to any target it hits. You have a +1 bonus to attack and damage rolls made with this magic weapon.',
                'filterType': 'weapon',
                'type': 'martial weapon'
            }
        }
        
        bonuses = self.parser.parse_item_bonuses(weapon)
        weapon_bonuses = self.parser.get_weapon_bonuses(bonuses)
        
        # Should find +1 attack and damage bonuses
        self.assertEqual(weapon_bonuses['attack_bonus'], 1)
        self.assertEqual(weapon_bonuses['damage_bonus'], 1)
    
    def test_parse_modifiers(self):
        """Test parsing bonuses from D&D Beyond modifiers."""
        item = {
            'name': 'Bracers of Archery',
            'definition': {
                'modifiers': [
                    {
                        'type': 'bonus',
                        'subType': 'attack-roll',
                        'value': 2,
                        'friendlySubtypeName': 'Ranged Weapon Attack'
                    },
                    {
                        'type': 'bonus',
                        'subType': 'damage-roll',
                        'value': 2,
                        'friendlySubtypeName': 'Ranged Weapon Damage'
                    }
                ]
            }
        }
        
        bonuses = self.parser.parse_item_bonuses(item)
        weapon_bonuses = self.parser.get_weapon_bonuses(bonuses)
        
        # Should find attack and damage bonuses from modifiers
        self.assertEqual(weapon_bonuses['attack_bonus'], 2)
        self.assertEqual(weapon_bonuses['damage_bonus'], 2)
    
    def test_skill_name_normalization(self):
        """Test skill name normalization."""
        # Test space to underscore conversion
        self.assertEqual(self.parser._normalize_skill_name('sleight of hand'), 'sleight_of_hand')
        self.assertEqual(self.parser._normalize_skill_name('animal handling'), 'animal_handling')
        
        # Test already normalized names
        self.assertEqual(self.parser._normalize_skill_name('stealth'), 'stealth')
        self.assertEqual(self.parser._normalize_skill_name('perception'), 'perception')
        
        # Test invalid skill names
        self.assertIsNone(self.parser._normalize_skill_name('invalid_skill'))
        self.assertIsNone(self.parser._normalize_skill_name(''))
    
    def test_ability_name_normalization(self):
        """Test ability name normalization."""
        # Test abbreviations
        self.assertEqual(self.parser._normalize_ability_name('str'), 'strength')
        self.assertEqual(self.parser._normalize_ability_name('dex'), 'dexterity')
        self.assertEqual(self.parser._normalize_ability_name('con'), 'constitution')
        self.assertEqual(self.parser._normalize_ability_name('int'), 'intelligence')
        self.assertEqual(self.parser._normalize_ability_name('wis'), 'wisdom')
        self.assertEqual(self.parser._normalize_ability_name('cha'), 'charisma')
        
        # Test full names
        self.assertEqual(self.parser._normalize_ability_name('strength'), 'strength')
        self.assertEqual(self.parser._normalize_ability_name('dexterity'), 'dexterity')
        
        # Test invalid ability names
        self.assertIsNone(self.parser._normalize_ability_name('invalid'))
        self.assertIsNone(self.parser._normalize_ability_name(''))
    
    def test_item_type_detection(self):
        """Test item type detection methods."""
        # Test weapon detection
        weapon = {
            'definition': {
                'filterType': 'weapon',
                'weaponProperties': [{'name': 'versatile'}]
            }
        }
        self.assertTrue(self.parser._is_weapon(weapon))
        
        # Test armor detection
        armor = {
            'definition': {
                'filterType': 'armor',
                'type': 'heavy armor'
            }
        }
        self.assertTrue(self.parser._is_armor(armor))
        
        # Test shield detection
        shield = {
            'definition': {
                'type': 'shield',
                'name': 'Shield'
            }
        }
        self.assertTrue(self.parser._is_shield(shield))
    
    def test_organize_bonuses_by_type(self):
        """Test organizing bonuses by type."""
        bonuses = [
            MagicItemBonus('attack', 2, 'weapon'),
            MagicItemBonus('damage', 2, 'weapon'),
            MagicItemBonus('skill', 3, 'stealth'),
            MagicItemBonus('ac', 1, 'armor')
        ]
        
        organized = self.parser.organize_bonuses_by_type(bonuses)
        
        self.assertIn('attack', organized)
        self.assertIn('damage', organized)
        self.assertIn('skill', organized)
        self.assertIn('ac', organized)
        
        self.assertEqual(len(organized['attack']), 1)
        self.assertEqual(len(organized['damage']), 1)
        self.assertEqual(len(organized['skill']), 1)
        self.assertEqual(len(organized['ac']), 1)
    
    def test_get_weapon_bonuses(self):
        """Test extracting weapon bonuses."""
        bonuses = [
            MagicItemBonus('attack', 2, 'weapon'),
            MagicItemBonus('damage', 3, 'weapon'),
            MagicItemBonus('skill', 1, 'stealth'),  # Should be ignored
            MagicItemBonus('attack', 1, 'all_weapons')  # Should be included
        ]
        
        weapon_bonuses = self.parser.get_weapon_bonuses(bonuses)
        
        self.assertEqual(weapon_bonuses['attack_bonus'], 3)  # 2 + 1
        self.assertEqual(weapon_bonuses['damage_bonus'], 3)
    
    def test_get_skill_bonuses(self):
        """Test extracting skill bonuses."""
        bonuses = [
            MagicItemBonus('skill', 2, 'stealth'),
            MagicItemBonus('skill', 3, 'perception'),
            MagicItemBonus('skill', 1, 'stealth'),  # Should stack
            MagicItemBonus('attack', 2, 'weapon')  # Should be ignored
        ]
        
        skill_bonuses = self.parser.get_skill_bonuses(bonuses)
        
        self.assertEqual(skill_bonuses['stealth'], 3)  # 2 + 1
        self.assertEqual(skill_bonuses['perception'], 3)
        self.assertNotIn('weapon', skill_bonuses)
    
    def test_get_ac_bonus(self):
        """Test extracting AC bonuses."""
        bonuses = [
            MagicItemBonus('ac', 2, 'armor'),
            MagicItemBonus('ac', 1, 'shield'),
            MagicItemBonus('skill', 3, 'stealth')  # Should be ignored
        ]
        
        ac_bonus = self.parser.get_ac_bonus(bonuses)
        self.assertEqual(ac_bonus, 3)  # 2 + 1
    
    def test_complex_item_parsing(self):
        """Test parsing a complex magic item with multiple bonuses."""
        item = {
            'name': 'Cloak of Protection +1',
            'definition': {
                'description': 'You gain a +1 bonus to AC and saving throws while wearing this cloak. Additionally, you have advantage on Dexterity (Stealth) checks made in dim light or darkness.',
                'filterType': 'wondrous-item',
                'modifiers': [
                    {
                        'type': 'bonus',
                        'subType': 'armor-class',
                        'value': 1
                    }
                ]
            }
        }
        
        bonuses = self.parser.parse_item_bonuses(item)
        
        # Should find AC bonus and skill bonus
        ac_bonus = self.parser.get_ac_bonus(bonuses)
        skill_bonuses = self.parser.get_skill_bonuses(bonuses)
        
        # AC bonus should be 2 (1 from description + 1 from modifier)
        self.assertEqual(ac_bonus, 2)
        self.assertIn('stealth', skill_bonuses)
        self.assertEqual(skill_bonuses['stealth'], 5)  # Advantage
    
    def test_empty_item_handling(self):
        """Test handling of empty or invalid item data."""
        # Test empty dict
        bonuses = self.parser.parse_item_bonuses({})
        self.assertEqual(len(bonuses), 0)
        
        # Test None
        bonuses = self.parser.parse_item_bonuses(None)
        self.assertEqual(len(bonuses), 0)
        
        # Test item with no bonuses
        item = {
            'name': 'Rope',
            'definition': {
                'description': 'A simple rope.',
                'filterType': 'adventuring-gear'
            }
        }
        bonuses = self.parser.parse_item_bonuses(item)
        self.assertEqual(len(bonuses), 0)

if __name__ == '__main__':
    unittest.main()