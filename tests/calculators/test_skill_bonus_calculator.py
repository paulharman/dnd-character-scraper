import unittest
from src.calculators.skill_bonus_calculator import SkillBonusCalculator, SkillBonus

class TestSkillBonusCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = SkillBonusCalculator()
    
    def test_skill_abilities_mapping(self):
        """Test that all standard D&D 5e skills are mapped to correct abilities."""
        expected_mappings = {
            'acrobatics': 'dexterity',
            'animal_handling': 'wisdom',
            'arcana': 'intelligence',
            'athletics': 'strength',
            'deception': 'charisma',
            'history': 'intelligence',
            'insight': 'wisdom',
            'intimidation': 'charisma',
            'investigation': 'intelligence',
            'medicine': 'wisdom',
            'nature': 'intelligence',
            'perception': 'wisdom',
            'performance': 'charisma',
            'persuasion': 'charisma',
            'religion': 'intelligence',
            'sleight_of_hand': 'dexterity',
            'stealth': 'dexterity',
            'survival': 'wisdom'
        }
        
        self.assertEqual(self.calculator.SKILL_ABILITIES, expected_mappings)
    
    def test_calculate_basic_skill_bonuses(self):
        """Test basic skill bonus calculation without proficiency."""
        character_data = {
            'abilities': {
                'ability_scores': {
                    'strength': {'score': 16, 'modifier': 3},
                    'dexterity': {'score': 14, 'modifier': 2},
                    'constitution': {'score': 15, 'modifier': 2},
                    'intelligence': {'score': 12, 'modifier': 1},
                    'wisdom': {'score': 13, 'modifier': 1},
                    'charisma': {'score': 10, 'modifier': 0}
                }
            },
            'proficiencies': {
                'skill_proficiencies': [],
                'skill_expertise': []
            },
            'character_info': {
                'level': 5
            },
            'equipment': {
                'equipped_items': []
            }
        }
        
        result = self.calculator.calculate(character_data)
        skill_bonuses = result['skill_bonuses']
        
        # Should have all 18 skills
        self.assertEqual(len(skill_bonuses), 18)
        
        # Check specific skills
        athletics = next(sb for sb in skill_bonuses if sb.skill_name == 'athletics')
        self.assertEqual(athletics.ability_name, 'strength')
        self.assertEqual(athletics.ability_modifier, 3)
        self.assertEqual(athletics.proficiency_bonus, 0)
        self.assertEqual(athletics.total_bonus, 3)
        self.assertFalse(athletics.is_proficient)
        
        stealth = next(sb for sb in skill_bonuses if sb.skill_name == 'stealth')
        self.assertEqual(stealth.ability_name, 'dexterity')
        self.assertEqual(stealth.ability_modifier, 2)
        self.assertEqual(stealth.total_bonus, 2)
    
    def test_calculate_with_proficiency(self):
        """Test skill bonus calculation with proficiency."""
        character_data = {
            'abilities': {
                'ability_scores': {
                    'strength': {'score': 16, 'modifier': 3},
                    'dexterity': {'score': 14, 'modifier': 2},
                    'constitution': {'score': 15, 'modifier': 2},
                    'intelligence': {'score': 12, 'modifier': 1},
                    'wisdom': {'score': 13, 'modifier': 1},
                    'charisma': {'score': 10, 'modifier': 0}
                }
            },
            'proficiencies': {
                'skill_proficiencies': [
                    {'name': 'athletics'},
                    {'name': 'stealth'},
                    {'name': 'perception'}
                ],
                'skill_expertise': []
            },
            'character_info': {
                'level': 5  # Proficiency bonus +3
            },
            'equipment': {
                'equipped_items': []
            }
        }
        
        result = self.calculator.calculate(character_data)
        skill_bonuses = result['skill_bonuses']
        
        # Check proficient skills
        athletics = next(sb for sb in skill_bonuses if sb.skill_name == 'athletics')
        self.assertEqual(athletics.ability_modifier, 3)
        self.assertEqual(athletics.proficiency_bonus, 3)
        self.assertEqual(athletics.total_bonus, 6)  # 3 + 3
        self.assertTrue(athletics.is_proficient)
        
        stealth = next(sb for sb in skill_bonuses if sb.skill_name == 'stealth')
        self.assertEqual(stealth.ability_modifier, 2)
        self.assertEqual(stealth.proficiency_bonus, 3)
        self.assertEqual(stealth.total_bonus, 5)  # 2 + 3
        self.assertTrue(stealth.is_proficient)
        
        # Check non-proficient skill
        acrobatics = next(sb for sb in skill_bonuses if sb.skill_name == 'acrobatics')
        self.assertEqual(acrobatics.proficiency_bonus, 0)
        self.assertEqual(acrobatics.total_bonus, 2)  # Just DEX modifier
        self.assertFalse(acrobatics.is_proficient)
    
    def test_calculate_with_expertise(self):
        """Test skill bonus calculation with expertise."""
        character_data = {
            'abilities': {
                'ability_scores': {
                    'strength': {'score': 16, 'modifier': 3},
                    'dexterity': {'score': 14, 'modifier': 2},
                    'constitution': {'score': 15, 'modifier': 2},
                    'intelligence': {'score': 12, 'modifier': 1},
                    'wisdom': {'score': 13, 'modifier': 1},
                    'charisma': {'score': 10, 'modifier': 0}
                }
            },
            'proficiencies': {
                'skill_proficiencies': [
                    {'name': 'athletics'},
                    {'name': 'stealth'},
                    {'name': 'perception'}
                ],
                'skill_expertise': [
                    {'name': 'stealth'},
                    {'name': 'perception'}
                ]
            },
            'character_info': {
                'level': 5  # Proficiency bonus +3
            },
            'equipment': {
                'equipped_items': []
            }
        }
        
        result = self.calculator.calculate(character_data)
        skill_bonuses = result['skill_bonuses']
        
        # Check expertise skills
        stealth = next(sb for sb in skill_bonuses if sb.skill_name == 'stealth')
        self.assertEqual(stealth.ability_modifier, 2)
        self.assertEqual(stealth.proficiency_bonus, 3)
        self.assertEqual(stealth.expertise_bonus, 3)  # Double proficiency
        self.assertEqual(stealth.total_bonus, 8)  # 2 + 3 + 3
        self.assertTrue(stealth.is_proficient)
        self.assertTrue(stealth.has_expertise)
        
        perception = next(sb for sb in skill_bonuses if sb.skill_name == 'perception')
        self.assertEqual(perception.ability_modifier, 1)
        self.assertEqual(perception.proficiency_bonus, 3)
        self.assertEqual(perception.expertise_bonus, 3)
        self.assertEqual(perception.total_bonus, 7)  # 1 + 3 + 3
        self.assertTrue(perception.has_expertise)
        
        # Check proficient but not expertise skill
        athletics = next(sb for sb in skill_bonuses if sb.skill_name == 'athletics')
        self.assertEqual(athletics.expertise_bonus, 0)
        self.assertEqual(athletics.total_bonus, 6)  # 3 + 3 + 0
        self.assertFalse(athletics.has_expertise)
    
    def test_calculate_specific_skill(self):
        """Test calculating bonus for a specific skill."""
        character_data = {
            'abilities': {
                'ability_scores': {
                    'strength': {'score': 16, 'modifier': 3},
                    'dexterity': {'score': 14, 'modifier': 2},
                    'constitution': {'score': 15, 'modifier': 2},
                    'intelligence': {'score': 12, 'modifier': 1},
                    'wisdom': {'score': 13, 'modifier': 1},
                    'charisma': {'score': 10, 'modifier': 0}
                }
            },
            'proficiencies': {
                'skill_proficiencies': [{'name': 'athletics'}],
                'skill_expertise': []
            },
            'character_info': {
                'level': 5
            },
            'equipment': {
                'equipped_items': []
            }
        }
        
        athletics_bonus = self.calculator.calculate_specific_skill('athletics', character_data)
        
        self.assertIsNotNone(athletics_bonus)
        self.assertEqual(athletics_bonus.skill_name, 'athletics')
        self.assertEqual(athletics_bonus.ability_name, 'strength')
        self.assertEqual(athletics_bonus.total_bonus, 6)  # 3 + 3
        
        # Test invalid skill
        invalid_skill = self.calculator.calculate_specific_skill('invalid_skill', character_data)
        self.assertIsNone(invalid_skill)
    
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
    
    def test_skill_bonus_dataclass_properties(self):
        """Test SkillBonus dataclass properties."""
        skill_bonus = SkillBonus(
            skill_name='athletics',
            ability_name='strength',
            ability_modifier=3,
            proficiency_bonus=3,
            expertise_bonus=0,
            magic_bonus=2,
            total_bonus=8,
            is_proficient=True,
            has_expertise=False
        )
        
        # Test bonus expression
        expected_expression = "+3 (STR) +3 (Prof) +2 (Magic) = +8"
        self.assertEqual(skill_bonus.bonus_expression, expected_expression)
    
    def test_skill_bonus_expression_negative_modifier(self):
        """Test skill bonus expression with negative ability modifier."""
        skill_bonus = SkillBonus(
            skill_name='athletics',
            ability_name='strength',
            ability_modifier=-2,
            proficiency_bonus=3,
            expertise_bonus=0,
            magic_bonus=0,
            total_bonus=1,
            is_proficient=True,
            has_expertise=False
        )
        
        expected_expression = "-2 (STR) +3 (Prof) = +1"
        self.assertEqual(skill_bonus.bonus_expression, expected_expression)
    
    def test_skill_bonus_expression_zero_bonus(self):
        """Test skill bonus expression with zero total bonus."""
        skill_bonus = SkillBonus(
            skill_name='athletics',
            ability_name='strength',
            ability_modifier=0,
            proficiency_bonus=0,
            expertise_bonus=0,
            magic_bonus=0,
            total_bonus=0,
            is_proficient=False,
            has_expertise=False
        )
        
        self.assertEqual(skill_bonus.bonus_expression, "0")
    
    def test_get_skills_by_ability(self):
        """Test getting skills by ability score."""
        dex_skills = self.calculator.get_skills_by_ability('dexterity')
        expected_dex_skills = ['acrobatics', 'sleight_of_hand', 'stealth']
        self.assertEqual(sorted(dex_skills), sorted(expected_dex_skills))
        
        int_skills = self.calculator.get_skills_by_ability('intelligence')
        expected_int_skills = ['arcana', 'history', 'investigation', 'nature', 'religion']
        self.assertEqual(sorted(int_skills), sorted(expected_int_skills))
        
        cha_skills = self.calculator.get_skills_by_ability('charisma')
        expected_cha_skills = ['deception', 'intimidation', 'performance', 'persuasion']
        self.assertEqual(sorted(cha_skills), sorted(expected_cha_skills))
    
    def test_get_proficient_skills(self):
        """Test getting list of proficient skills."""
        character_data = {
            'proficiencies': {
                'skill_proficiencies': [
                    {'name': 'athletics'},
                    {'name': 'stealth'},
                    {'name': 'perception'}
                ]
            }
        }
        
        proficient_skills = self.calculator.get_proficient_skills(character_data)
        expected_skills = ['athletics', 'stealth', 'perception']
        self.assertEqual(sorted(proficient_skills), sorted(expected_skills))
    
    def test_get_expertise_skills(self):
        """Test getting list of expertise skills."""
        character_data = {
            'proficiencies': {
                'skill_expertise': [
                    {'name': 'stealth'},
                    {'name': 'perception'}
                ]
            }
        }
        
        expertise_skills = self.calculator.get_expertise_skills(character_data)
        expected_skills = ['stealth', 'perception']
        self.assertEqual(sorted(expertise_skills), sorted(expected_skills))
    
    def test_skill_name_normalization(self):
        """Test that skill names with spaces are properly normalized."""
        character_data = {
            'abilities': {
                'ability_scores': {
                    'dexterity': {'score': 14, 'modifier': 2}
                }
            },
            'proficiencies': {
                'skill_proficiencies': [
                    {'name': 'Sleight of Hand'},  # With spaces and capitals
                    'Animal Handling'  # String format with spaces
                ],
                'skill_expertise': []
            },
            'character_info': {
                'level': 5
            },
            'equipment': {
                'equipped_items': []
            }
        }
        
        proficient_skills = self.calculator.get_proficient_skills(character_data)
        self.assertIn('sleight_of_hand', proficient_skills)
        self.assertIn('animal_handling', proficient_skills)

if __name__ == '__main__':
    unittest.main()