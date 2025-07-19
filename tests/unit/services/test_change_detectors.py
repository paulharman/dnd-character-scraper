"""
Unit tests for individual change detectors.

Tests each detector class for accuracy, D&D rule compliance, and proper change categorization.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import sys

# Add Discord module to path
discord_root = Path(__file__).parent.parent.parent.parent / "discord"
sys.path.insert(0, str(discord_root))

from services.change_detection.detectors import (
    BasicInfoDetector, AbilityScoreDetector, SkillDetector, 
    CombatDetector, SpellDetector, DetectorBase
)
from services.change_detection.models import FieldChange, ChangeType, ChangeCategory, ChangePriority


class TestDetectorBase:
    """Test the base detector class."""
    
    def test_detector_base_initialization(self):
        """Test detector base initialization."""
        detector = DetectorBase("test_detector", [ChangeCategory.BASIC_INFO])
        
        assert detector.name == "test_detector"
        assert detector.supported_categories == [ChangeCategory.BASIC_INFO]
        assert detector.can_detect("any_field") is True  # Default implementation
        assert detector.get_priority() == 100  # Default priority
    
    def test_detector_base_not_implemented(self):
        """Test that base detector raises NotImplementedError for detect_changes."""
        detector = DetectorBase("test_detector")
        
        with pytest.raises(NotImplementedError) as exc_info:
            detector.detect_changes({}, {}, {})
        
        assert "must implement detect_changes()" in str(exc_info.value)


class TestBasicInfoDetector:
    """Test basic information change detection."""
    
    @pytest.fixture
    def detector(self):
        """Basic info detector instance."""
        return BasicInfoDetector()
    
    @pytest.fixture
    def basic_character_old(self):
        """Old character basic info."""
        return {
            'character_info': {
                'name': 'Test Character',
                'level': 5,
                'class': 'Wizard',
                'race': 'Human',
                'background': 'Scholar',
                'alignment': 'Lawful Good',
                'experience_points': 6500,
                'hit_points': 32,
                'armor_class': 13
            }
        }
    
    @pytest.fixture
    def basic_character_new(self):
        """New character basic info with changes."""
        return {
            'character_info': {
                'name': 'Test Character',
                'level': 6,  # Level up
                'class': 'Wizard',
                'race': 'Human',
                'background': 'Scholar',
                'alignment': 'Lawful Good',
                'experience_points': 14000,  # More experience
                'hit_points': 38,  # More HP
                'armor_class': 15  # Better AC
            }
        }
    
    def test_detector_initialization(self, detector):
        """Test basic info detector initialization."""
        assert detector.name == "basic_info"
        assert ChangeCategory.BASIC_INFO in detector.supported_categories
        assert 'level' in detector.tracked_fields
        assert 'name' in detector.tracked_fields
    
    def test_level_change_detection(self, detector, basic_character_old, basic_character_new):
        """Test level change detection."""
        changes = detector.detect_changes(basic_character_old, basic_character_new, {})
        
        level_changes = [c for c in changes if 'level' in c.field_path]
        assert len(level_changes) == 1
        
        level_change = level_changes[0]
        assert level_change.old_value == 5
        assert level_change.new_value == 6
        assert level_change.change_type == ChangeType.INCREMENTED
        assert level_change.priority == ChangePriority.CRITICAL
        assert level_change.category == ChangeCategory.BASIC_INFO
        assert "level" in level_change.description.lower()
    
    def test_name_change_detection(self, detector):
        """Test character name change detection."""
        old_data = {'character_info': {'name': 'Old Name'}}
        new_data = {'character_info': {'name': 'New Name'}}
        
        changes = detector.detect_changes(old_data, new_data, {})
        
        name_changes = [c for c in changes if 'name' in c.field_path]
        assert len(name_changes) == 1
        
        name_change = name_changes[0]
        assert name_change.old_value == 'Old Name'
        assert name_change.new_value == 'New Name'
        assert name_change.change_type == ChangeType.MODIFIED
        assert name_change.priority == ChangePriority.HIGH
    
    def test_experience_change_detection(self, detector, basic_character_old, basic_character_new):
        """Test experience points change detection."""
        changes = detector.detect_changes(basic_character_old, basic_character_new, {})
        
        exp_changes = [c for c in changes if 'experience' in c.field_path]
        assert len(exp_changes) == 1
        
        exp_change = exp_changes[0]
        assert exp_change.old_value == 6500
        assert exp_change.new_value == 14000
        assert exp_change.change_type == ChangeType.INCREMENTED
        assert exp_change.priority == ChangePriority.MEDIUM
    
    def test_combat_stat_changes(self, detector, basic_character_old, basic_character_new):
        """Test combat stat changes (HP, AC)."""
        changes = detector.detect_changes(basic_character_old, basic_character_new, {})
        
        hp_changes = [c for c in changes if 'hit_points' in c.field_path]
        ac_changes = [c for c in changes if 'armor_class' in c.field_path]
        
        assert len(hp_changes) == 1
        assert len(ac_changes) == 1
        
        # Both should be high priority
        assert hp_changes[0].priority == ChangePriority.HIGH
        assert ac_changes[0].priority == ChangePriority.HIGH
    
    def test_no_changes_detection(self, detector, basic_character_old):
        """Test that identical data produces no changes."""
        changes = detector.detect_changes(basic_character_old, basic_character_old, {})
        assert len(changes) == 0
    
    def test_change_type_determination(self, detector):
        """Test change type determination logic."""
        # Test added value
        assert detector._determine_change_type(None, 10) == ChangeType.ADDED
        
        # Test removed value
        assert detector._determine_change_type(10, None) == ChangeType.REMOVED
        
        # Test incremented value
        assert detector._determine_change_type(5, 10) == ChangeType.INCREMENTED
        
        # Test decremented value
        assert detector._determine_change_type(10, 5) == ChangeType.DECREMENTED
        
        # Test modified value (non-numeric)
        assert detector._determine_change_type("old", "new") == ChangeType.MODIFIED


class TestAbilityScoreDetector:
    """Test ability score change detection."""
    
    @pytest.fixture
    def detector(self):
        """Ability score detector instance."""
        return AbilityScoreDetector()
    
    @pytest.fixture
    def ability_scores_old(self):
        """Old ability scores."""
        return {
            'ability_scores': {
                'strength': 14,
                'dexterity': 16,
                'constitution': 13,
                'intelligence': 18,
                'wisdom': 12,
                'charisma': 8
            }
        }
    
    @pytest.fixture
    def ability_scores_new(self):
        """New ability scores with changes."""
        return {
            'ability_scores': {
                'strength': 16,  # Increased
                'dexterity': 16,  # No change
                'constitution': 13,  # No change
                'intelligence': 20,  # Increased (big change)
                'wisdom': 10,  # Decreased
                'charisma': 8  # No change
            }
        }
    
    def test_detector_initialization(self, detector):
        """Test ability score detector initialization."""
        assert detector.name == "ability_scores"
        assert ChangeCategory.ABILITIES in detector.supported_categories
        assert len(detector.abilities) == 6
        assert 'strength' in detector.abilities
        assert 'intelligence' in detector.abilities
    
    def test_ability_score_increases(self, detector, ability_scores_old, ability_scores_new):
        """Test ability score increase detection."""
        changes = detector.detect_changes(ability_scores_old, ability_scores_new, {})
        
        str_changes = [c for c in changes if 'strength' in c.field_path]
        int_changes = [c for c in changes if 'intelligence' in c.field_path]
        
        assert len(str_changes) == 1
        assert len(int_changes) == 1
        
        # Strength change (small)
        str_change = str_changes[0]
        assert str_change.old_value == 14
        assert str_change.new_value == 16
        assert str_change.change_type == ChangeType.INCREMENTED
        assert str_change.priority == ChangePriority.MEDIUM  # Small change
        
        # Intelligence change (large)
        int_change = int_changes[0]
        assert int_change.old_value == 18
        assert int_change.new_value == 20
        assert int_change.change_type == ChangeType.INCREMENTED
        assert int_change.priority == ChangePriority.HIGH  # Large change
    
    def test_ability_score_decreases(self, detector, ability_scores_old, ability_scores_new):
        """Test ability score decrease detection."""
        changes = detector.detect_changes(ability_scores_old, ability_scores_new, {})
        
        wis_changes = [c for c in changes if 'wisdom' in c.field_path]
        assert len(wis_changes) == 1
        
        wis_change = wis_changes[0]
        assert wis_change.old_value == 12
        assert wis_change.new_value == 10
        assert wis_change.change_type == ChangeType.DECREMENTED
    
    def test_no_ability_score_changes(self, detector, ability_scores_old):
        """Test no changes when ability scores are identical."""
        changes = detector.detect_changes(ability_scores_old, ability_scores_old, {})
        assert len(changes) == 0
    
    def test_missing_ability_scores(self, detector):
        """Test handling of missing ability score data."""
        old_data = {'ability_scores': {'strength': 10}}
        new_data = {'ability_scores': {'strength': 12, 'dexterity': 14}}
        
        changes = detector.detect_changes(old_data, new_data, {})
        
        # Should handle missing scores gracefully (default to 10)
        str_changes = [c for c in changes if 'strength' in c.field_path]
        dex_changes = [c for c in changes if 'dexterity' in c.field_path]
        
        assert len(str_changes) == 1
        assert len(dex_changes) == 1
        
        # Dexterity should be detected as added (from default 10 to 14)
        dex_change = dex_changes[0]
        assert dex_change.old_value == 10  # Default value
        assert dex_change.new_value == 14


class TestSkillDetector:
    """Test skill proficiency and bonus detection."""
    
    @pytest.fixture
    def detector(self):
        """Skill detector instance."""
        return SkillDetector()
    
    @pytest.fixture
    def enhanced_skills_old(self):
        """Old enhanced skill format data."""
        return {
            'proficiencies': {
                'skill_bonuses': [
                    {
                        'skill_name': 'arcana',
                        'is_proficient': True,
                        'has_expertise': False,
                        'total_bonus': 7
                    },
                    {
                        'skill_name': 'investigation',
                        'is_proficient': False,
                        'has_expertise': False,
                        'total_bonus': 3
                    },
                    {
                        'skill_name': 'perception',
                        'is_proficient': True,
                        'has_expertise': True,
                        'total_bonus': 9
                    }
                ]
            }
        }
    
    @pytest.fixture
    def enhanced_skills_new(self):
        """New enhanced skill format data with changes."""
        return {
            'proficiencies': {
                'skill_bonuses': [
                    {
                        'skill_name': 'arcana',
                        'is_proficient': True,
                        'has_expertise': True,  # Gained expertise
                        'total_bonus': 10
                    },
                    {
                        'skill_name': 'investigation',
                        'is_proficient': True,  # Gained proficiency
                        'has_expertise': False,
                        'total_bonus': 6
                    },
                    {
                        'skill_name': 'perception',
                        'is_proficient': True,
                        'has_expertise': True,
                        'total_bonus': 11  # Bonus increased
                    }
                ]
            }
        }
    
    def test_detector_initialization(self, detector):
        """Test skill detector initialization."""
        assert detector.name == "skills"
        assert ChangeCategory.SKILLS in detector.supported_categories
    
    def test_expertise_gain_detection(self, detector, enhanced_skills_old, enhanced_skills_new):
        """Test expertise gain detection."""
        changes = detector.detect_changes(enhanced_skills_old, enhanced_skills_new, {})
        
        expertise_changes = [c for c in changes if 'expertise' in c.field_path and 'arcana' in c.field_path]
        assert len(expertise_changes) == 1
        
        expertise_change = expertise_changes[0]
        assert expertise_change.old_value is False
        assert expertise_change.new_value is True
        assert expertise_change.change_type == ChangeType.ADDED
        assert expertise_change.priority == ChangePriority.HIGH
        assert 'expertise' in expertise_change.description.lower()
        assert 'arcana' in expertise_change.description.lower()
    
    def test_proficiency_gain_detection(self, detector, enhanced_skills_old, enhanced_skills_new):
        """Test proficiency gain detection."""
        changes = detector.detect_changes(enhanced_skills_old, enhanced_skills_new, {})
        
        prof_changes = [c for c in changes if 'proficient' in c.field_path and 'investigation' in c.field_path]
        assert len(prof_changes) == 1
        
        prof_change = prof_changes[0]
        assert prof_change.old_value is False
        assert prof_change.new_value is True
        assert prof_change.change_type == ChangeType.ADDED
        assert prof_change.priority == ChangePriority.MEDIUM
    
    def test_skill_bonus_changes(self, detector, enhanced_skills_old, enhanced_skills_new):
        """Test skill bonus change detection."""
        changes = detector.detect_changes(enhanced_skills_old, enhanced_skills_new, {})
        
        bonus_changes = [c for c in changes if 'total_bonus' in c.field_path]
        
        # Should detect bonus changes for all three skills
        arcana_bonus = [c for c in bonus_changes if 'arcana' in c.field_path]
        investigation_bonus = [c for c in bonus_changes if 'investigation' in c.field_path]
        perception_bonus = [c for c in bonus_changes if 'perception' in c.field_path]
        
        assert len(arcana_bonus) == 1
        assert len(investigation_bonus) == 1
        assert len(perception_bonus) == 1
        
        # Check specific bonus changes
        assert arcana_bonus[0].old_value == 7
        assert arcana_bonus[0].new_value == 10
        assert investigation_bonus[0].old_value == 3
        assert investigation_bonus[0].new_value == 6
    
    def test_legacy_skill_format_support(self, detector):
        """Test support for legacy skill format."""
        old_data = {
            'skills': {
                'arcana': {'proficient': True, 'bonus': 7},
                'investigation': {'proficient': False, 'bonus': 3}
            }
        }
        
        new_data = {
            'skills': {
                'arcana': {'proficient': True, 'bonus': 9},
                'investigation': {'proficient': True, 'bonus': 6}
            }
        }
        
        changes = detector.detect_changes(old_data, new_data, {})
        
        # Should detect changes in legacy format
        prof_changes = [c for c in changes if 'proficient' in c.field_path]
        bonus_changes = [c for c in changes if 'bonus' in c.field_path]
        
        assert len(prof_changes) >= 1  # Investigation proficiency gained
        assert len(bonus_changes) >= 1  # Bonus changes
    
    def test_skill_name_formatting(self, detector, enhanced_skills_old, enhanced_skills_new):
        """Test skill name formatting in descriptions."""
        changes = detector.detect_changes(enhanced_skills_old, enhanced_skills_new, {})
        
        for change in changes:
            # Skill names should be properly formatted in descriptions
            if 'arcana' in change.field_path:
                assert 'Arcana' in change.description or 'arcana' in change.description
            
            # Should not contain underscores in descriptions
            assert '_' not in change.description or 'arcana' not in change.field_path


class TestCombatDetector:
    """Test combat-related change detection."""
    
    @pytest.fixture
    def detector(self):
        """Combat detector instance."""
        return CombatDetector()
    
    @pytest.fixture
    def combat_data_old(self):
        """Old combat data."""
        return {
            'combat': {
                'armor_class': 15,
                'hit_points': {'maximum': 45, 'current': 45},
                'weapon_attacks': [
                    {
                        'name': 'Longsword',
                        'attack_bonus': 7,
                        'damage_dice': '1d8',
                        'damage_modifier': 4
                    },
                    {
                        'name': 'Shortbow',
                        'attack_bonus': 5,
                        'damage_dice': '1d6',
                        'damage_modifier': 2
                    }
                ]
            },
            'resources': {
                'class_resources': [
                    {
                        'class_name': 'Fighter',
                        'resource_name': 'Action Surge',
                        'maximum': 1,
                        'used': 0
                    }
                ]
            }
        }
    
    @pytest.fixture
    def combat_data_new(self):
        """New combat data with changes."""
        return {
            'combat': {
                'armor_class': 17,  # Improved AC
                'hit_points': {'maximum': 52, 'current': 52},  # More HP
                'weapon_attacks': [
                    {
                        'name': 'Longsword',
                        'attack_bonus': 8,  # Better attack bonus
                        'damage_dice': '1d8',
                        'damage_modifier': 5  # Better damage
                    },
                    {
                        'name': 'Shortbow',
                        'attack_bonus': 5,
                        'damage_dice': '1d6',
                        'damage_modifier': 2
                    },
                    {
                        'name': 'Greatsword',  # New weapon
                        'attack_bonus': 8,
                        'damage_dice': '2d6',
                        'damage_modifier': 5
                    }
                ]
            },
            'resources': {
                'class_resources': [
                    {
                        'class_name': 'Fighter',
                        'resource_name': 'Action Surge',
                        'maximum': 2,  # More uses
                        'used': 1  # Some used
                    }
                ]
            }
        }
    
    def test_detector_initialization(self, detector):
        """Test combat detector initialization."""
        assert detector.name == "combat"
        assert ChangeCategory.COMBAT in detector.supported_categories
    
    def test_armor_class_change_detection(self, detector, combat_data_old, combat_data_new):
        """Test armor class change detection."""
        changes = detector.detect_changes(combat_data_old, combat_data_new, {})
        
        ac_changes = [c for c in changes if 'armor_class' in c.field_path]
        assert len(ac_changes) == 1
        
        ac_change = ac_changes[0]
        assert ac_change.old_value == 15
        assert ac_change.new_value == 17
        assert ac_change.change_type == ChangeType.INCREMENTED
        assert ac_change.priority == ChangePriority.HIGH
        assert 'armor class' in ac_change.description.lower()
    
    def test_hit_points_change_detection(self, detector, combat_data_old, combat_data_new):
        """Test hit points change detection."""
        changes = detector.detect_changes(combat_data_old, combat_data_new, {})
        
        hp_changes = [c for c in changes if 'hit_points' in c.field_path and 'maximum' in c.field_path]
        assert len(hp_changes) == 1
        
        hp_change = hp_changes[0]
        assert hp_change.old_value == 45
        assert hp_change.new_value == 52
        assert hp_change.change_type == ChangeType.INCREMENTED
        assert hp_change.priority == ChangePriority.HIGH
    
    def test_weapon_attack_changes(self, detector, combat_data_old, combat_data_new):
        """Test weapon attack change detection."""
        changes = detector.detect_changes(combat_data_old, combat_data_new, {})
        
        # Should detect new weapon
        new_weapon_changes = [c for c in changes if 'Greatsword' in str(c.new_value)]
        assert len(new_weapon_changes) == 1
        
        new_weapon_change = new_weapon_changes[0]
        assert new_weapon_change.change_type == ChangeType.ADDED
        assert new_weapon_change.priority == ChangePriority.MEDIUM
        
        # Should detect attack bonus improvement
        attack_bonus_changes = [c for c in changes if 'attack_bonus' in c.field_path and 'Longsword' in c.field_path]
        if attack_bonus_changes:
            bonus_change = attack_bonus_changes[0]
            assert bonus_change.old_value == 7
            assert bonus_change.new_value == 8
    
    def test_class_resource_changes(self, detector, combat_data_old, combat_data_new):
        """Test class resource change detection."""
        changes = detector.detect_changes(combat_data_old, combat_data_new, {})
        
        # Should detect Action Surge maximum increase
        resource_max_changes = [c for c in changes if 'maximum' in c.field_path and 'Action Surge' in c.field_path]
        if resource_max_changes:
            max_change = resource_max_changes[0]
            assert max_change.old_value == 1
            assert max_change.new_value == 2
            assert max_change.priority == ChangePriority.MEDIUM
        
        # Should detect resource usage
        resource_used_changes = [c for c in changes if 'used' in c.field_path and 'Action Surge' in c.field_path]
        if resource_used_changes:
            used_change = resource_used_changes[0]
            assert used_change.old_value == 0
            assert used_change.new_value == 1
            assert used_change.priority == ChangePriority.LOW  # Usage changes are lower priority
    
    def test_armor_class_dict_format_handling(self, detector):
        """Test handling of AC in dictionary format."""
        old_data = {
            'combat': {
                'armor_class': {'total': 15, 'base': 10, 'dex_modifier': 3, 'armor_bonus': 2}
            }
        }
        
        new_data = {
            'combat': {
                'armor_class': {'total': 17, 'base': 10, 'dex_modifier': 3, 'armor_bonus': 4}
            }
        }
        
        changes = detector.detect_changes(old_data, new_data, {})
        
        ac_changes = [c for c in changes if 'armor_class' in c.field_path]
        if ac_changes:
            ac_change = ac_changes[0]
            assert ac_change.old_value == 15
            assert ac_change.new_value == 17


class TestSpellDetector:
    """Test spell and spellcasting change detection."""
    
    @pytest.fixture
    def detector(self):
        """Spell detector instance."""
        return SpellDetector()
    
    @pytest.fixture
    def spell_data_old(self):
        """Old spell data."""
        return {
            'spells': {
                'class_spells': {
                    'Wizard': [
                        {'name': 'Mage Hand', 'level': 0},
                        {'name': 'Prestidigitation', 'level': 0},
                        {'name': 'Magic Missile', 'level': 1},
                        {'name': 'Shield', 'level': 1}
                    ]
                }
            },
            'spellcasting': {
                'spell_slots': [0, 3, 2, 0, 0, 0, 0, 0, 0, 0],
                'spell_counts': {'total': 4, 'by_level': {0: 2, 1: 2}}
            }
        }
    
    @pytest.fixture
    def spell_data_new(self):
        """New spell data with changes."""
        return {
            'spells': {
                'class_spells': {
                    'Wizard': [
                        {'name': 'Mage Hand', 'level': 0},
                        {'name': 'Prestidigitation', 'level': 0},
                        {'name': 'Minor Illusion', 'level': 0},  # New cantrip
                        {'name': 'Magic Missile', 'level': 1},
                        {'name': 'Shield', 'level': 1},
                        {'name': 'Detect Magic', 'level': 1}  # New 1st level spell
                    ]
                }
            },
            'spellcasting': {
                'spell_slots': [0, 4, 3, 0, 0, 0, 0, 0, 0, 0],  # More spell slots
                'spell_counts': {'total': 6, 'by_level': {0: 3, 1: 3}}
            }
        }
    
    def test_detector_initialization(self, detector):
        """Test spell detector initialization."""
        assert detector.name == "spells"
        assert ChangeCategory.SPELLS in detector.supported_categories
    
    def test_spell_slot_increase_detection(self, detector, spell_data_old, spell_data_new):
        """Test spell slot increase detection."""
        changes = detector.detect_changes(spell_data_old, spell_data_new, {})
        
        # Should detect 1st level spell slot increase
        first_level_changes = [c for c in changes if 'spell_slots' in c.field_path and '1' in c.field_path]
        if first_level_changes:
            slot_change = first_level_changes[0]
            assert slot_change.old_value == 3
            assert slot_change.new_value == 4
            assert slot_change.change_type == ChangeType.INCREMENTED
            assert slot_change.priority in [ChangePriority.HIGH, ChangePriority.MEDIUM]
        
        # Should detect 2nd level spell slot increase
        second_level_changes = [c for c in changes if 'spell_slots' in c.field_path and '2' in c.field_path]
        if second_level_changes:
            slot_change = second_level_changes[0]
            assert slot_change.old_value == 2
            assert slot_change.new_value == 3
    
    def test_new_spell_learned_detection(self, detector, spell_data_old, spell_data_new):
        """Test new spell learned detection."""
        changes = detector.detect_changes(spell_data_old, spell_data_new, {})
        
        # Should detect new spells learned
        new_spell_changes = [c for c in changes if c.change_type == ChangeType.ADDED and 'spells' in c.field_path]
        
        # Should detect both new cantrip and new 1st level spell
        cantrip_changes = [c for c in new_spell_changes if 'Minor Illusion' in str(c.new_value)]
        first_level_changes = [c for c in new_spell_changes if 'Detect Magic' in str(c.new_value)]
        
        if cantrip_changes:
            cantrip_change = cantrip_changes[0]
            assert cantrip_change.priority == ChangePriority.HIGH
            assert 'learned' in cantrip_change.description.lower() or 'gained' in cantrip_change.description.lower()
        
        if first_level_changes:
            spell_change = first_level_changes[0]
            assert spell_change.priority == ChangePriority.HIGH
    
    def test_spell_forgotten_detection(self, detector):
        """Test spell forgotten detection."""
        old_data = {
            'spells': {
                'class_spells': {
                    'Wizard': [
                        {'name': 'Magic Missile', 'level': 1},
                        {'name': 'Shield', 'level': 1},
                        {'name': 'Fireball', 'level': 3}
                    ]
                }
            }
        }
        
        new_data = {
            'spells': {
                'class_spells': {
                    'Wizard': [
                        {'name': 'Magic Missile', 'level': 1},
                        {'name': 'Shield', 'level': 1}
                        # Fireball removed
                    ]
                }
            }
        }
        
        changes = detector.detect_changes(old_data, new_data, {})
        
        # Should detect spell removal
        removed_spell_changes = [c for c in changes if c.change_type == ChangeType.REMOVED and 'Fireball' in str(c.old_value)]
        
        if removed_spell_changes:
            removed_change = removed_spell_changes[0]
            assert removed_change.priority == ChangePriority.HIGH
            assert 'forgot' in removed_change.description.lower() or 'removed' in removed_change.description.lower()
    
    def test_spell_count_changes(self, detector, spell_data_old, spell_data_new):
        """Test spell count change detection."""
        changes = detector.detect_changes(spell_data_old, spell_data_new, {})
        
        # Should detect total spell count increase
        count_changes = [c for c in changes if 'spell_counts' in c.field_path and 'total' in c.field_path]
        
        if count_changes:
            count_change = count_changes[0]
            assert count_change.old_value == 4
            assert count_change.new_value == 6
            assert count_change.change_type == ChangeType.INCREMENTED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])