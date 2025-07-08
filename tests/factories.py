"""
Test data factories for creating valid Character and related objects.

These factories provide sensible defaults for testing while allowing easy customization.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from src.models.character import (
    Character, AbilityScores, CharacterClass, Species, Background,
    HitPoints, ArmorClass, Spellcasting, Skill
)
from src.models.base import SourcedValue, Modifier
from src.interfaces.rule_engine import RuleVersion


class CharacterFactory:
    """Factory for creating test Character objects."""

    @staticmethod
    def create_ability_scores(
        strength: int = 15,
        dexterity: int = 14,
        constitution: int = 13,
        intelligence: int = 12,
        wisdom: int = 11,
        charisma: int = 10,
        **kwargs
    ) -> AbilityScores:
        """Create test ability scores with sensible defaults."""
        return AbilityScores(
            strength=strength,
            dexterity=dexterity,
            constitution=constitution,
            intelligence=intelligence,
            wisdom=wisdom,
            charisma=charisma,
            **kwargs
        )

    @staticmethod
    def create_character_class(
        name: str = "Fighter",
        level: int = 5,
        hit_die: int = 10,
        subclass: Optional[str] = None,
        is_spellcaster: bool = False,
        **kwargs
    ) -> CharacterClass:
        """Create test character class with sensible defaults."""
        return CharacterClass(
            name=name,
            level=level,
            hit_die=hit_die,
            subclass=subclass,
            is_spellcaster=is_spellcaster,
            **kwargs
        )

    @staticmethod
    def create_species(
        name: str = "Human",
        subrace: Optional[str] = None,
        speed: int = 30,
        **kwargs
    ) -> Species:
        """Create test species with sensible defaults."""
        return Species(
            name=name,
            subrace=subrace,
            speed=speed,
            **kwargs
        )

    @staticmethod
    def create_background(
        name: str = "Folk Hero",
        **kwargs
    ) -> Background:
        """Create test background with sensible defaults."""
        return Background(
            name=name,
            **kwargs
        )

    @staticmethod
    def create_hit_points(
        maximum: int = 45,
        current: Optional[int] = None,
        temporary: int = 0,
        **kwargs
    ) -> HitPoints:
        """Create test hit points with sensible defaults."""
        if current is None:
            current = maximum
        
        return HitPoints(
            maximum=maximum,
            current=current,
            temporary=temporary,
            **kwargs
        )

    @staticmethod
    def create_armor_class(
        total: int = 16,
        base: int = 10,
        armor_bonus: int = 4,
        dexterity_bonus: int = 2,
        **kwargs
    ) -> ArmorClass:
        """Create test armor class with sensible defaults."""
        return ArmorClass(
            total=total,
            base=base,
            armor_bonus=armor_bonus,
            dexterity_bonus=dexterity_bonus,
            **kwargs
        )

    @staticmethod
    def create_spellcasting(
        is_spellcaster: bool = False,
        spellcasting_ability: Optional[str] = None,
        **kwargs
    ) -> Spellcasting:
        """Create test spellcasting with sensible defaults."""
        return Spellcasting(
            is_spellcaster=is_spellcaster,
            spellcasting_ability=spellcasting_ability,
            **kwargs
        )

    @staticmethod
    def create_skill(
        name: str = "Athletics",
        ability: str = "strength",
        proficient: bool = False,
        expertise: bool = False,
        bonus: int = 0,
        total_bonus: int = 0,
        **kwargs
    ) -> Skill:
        """Create test skill with sensible defaults."""
        return Skill(
            name=name,
            ability=ability,
            proficient=proficient,
            expertise=expertise,
            bonus=bonus,
            total_bonus=total_bonus,
            **kwargs
        )

    @classmethod
    def create_character(
        cls,
        id: int = 12345,
        name: str = "Test Character",
        level: int = 5,
        proficiency_bonus: int = 3,
        rule_version: RuleVersion = RuleVersion.RULES_2014,
        ability_scores: Optional[AbilityScores] = None,
        classes: Optional[List[CharacterClass]] = None,
        species: Optional[Species] = None,
        background: Optional[Background] = None,
        hit_points: Optional[HitPoints] = None,
        armor_class: Optional[ArmorClass] = None,
        spellcasting: Optional[Spellcasting] = None,
        skills: Optional[List[Skill]] = None,
        saving_throw_proficiencies: Optional[List[str]] = None,
        initiative_bonus: int = 2,
        speed: int = 30,
        alignment: Optional[str] = "Lawful Good",
        experience_points: int = 6500,
        equipment: Optional[List[Dict[str, Any]]] = None,
        modifiers: Optional[List[Modifier]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        raw_data_summary: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Character:
        """Create a complete test character with all required fields."""
        
        # Create defaults for required fields if not provided
        if ability_scores is None:
            ability_scores = cls.create_ability_scores()
        
        if classes is None:
            classes = [cls.create_character_class(level=level)]
        
        if species is None:
            species = cls.create_species()
        
        if background is None:
            background = cls.create_background()
        
        if hit_points is None:
            hit_points = cls.create_hit_points()
        
        if armor_class is None:
            armor_class = cls.create_armor_class()
        
        if spellcasting is None:
            spellcasting = cls.create_spellcasting()
        
        if skills is None:
            skills = []
        
        if saving_throw_proficiencies is None:
            saving_throw_proficiencies = ["Strength", "Constitution"]
        
        if equipment is None:
            equipment = []
        
        if modifiers is None:
            modifiers = []
        
        if raw_data_summary is None:
            raw_data_summary = {}
        
        return Character(
            id=id,
            name=name,
            level=level,
            proficiency_bonus=proficiency_bonus,
            rule_version=rule_version,
            ability_scores=ability_scores,
            classes=classes,
            species=species,
            background=background,
            hit_points=hit_points,
            armor_class=armor_class,
            spellcasting=spellcasting,
            skills=skills,
            saving_throw_proficiencies=saving_throw_proficiencies,
            initiative_bonus=initiative_bonus,
            speed=speed,
            alignment=alignment,
            experience_points=experience_points,
            equipment=equipment,
            modifiers=modifiers,
            created_at=created_at,
            updated_at=updated_at,
            raw_data_summary=raw_data_summary,
            **kwargs
        )

    @classmethod
    def create_basic_character(cls, **overrides) -> Character:
        """Create a basic character for simple tests."""
        return cls.create_character(**overrides)

    @classmethod
    def create_fighter(cls, level: int = 5, **overrides) -> Character:
        """Create a Fighter character for tests."""
        fighter_class = cls.create_character_class(
            name="Fighter",
            level=level,
            hit_die=10,
            is_spellcaster=False
        )
        
        return cls.create_character(
            level=level,
            classes=[fighter_class],
            saving_throw_proficiencies=["Strength", "Constitution"],
            **overrides
        )

    @classmethod
    def create_wizard(cls, level: int = 5, **overrides) -> Character:
        """Create a Wizard character for spellcasting tests."""
        wizard_class = cls.create_character_class(
            name="Wizard",
            level=level,
            hit_die=6,
            is_spellcaster=True,
            spellcasting_ability="intelligence",
            spellcasting_type="full"
        )
        
        spellcasting = cls.create_spellcasting(
            is_spellcaster=True,
            spellcasting_ability="intelligence",
            spell_save_dc=14,
            spell_attack_bonus=6,
            spell_slots_level_1=4,
            spell_slots_level_2=3,
            spell_slots_level_3=2
        )
        
        return cls.create_character(
            level=level,
            classes=[wizard_class],
            spellcasting=spellcasting,
            saving_throw_proficiencies=["Intelligence", "Wisdom"],
            **overrides
        )

    @classmethod
    def create_rogue(cls, level: int = 5, **overrides) -> Character:
        """Create a Rogue character for skill tests."""
        rogue_class = cls.create_character_class(
            name="Rogue",
            level=level,
            hit_die=8,
            is_spellcaster=False
        )
        
        # Create typical rogue skills
        skills = [
            cls.create_skill("Stealth", "dexterity", proficient=True, expertise=True, total_bonus=9),
            cls.create_skill("Sleight of Hand", "dexterity", proficient=True, total_bonus=5),
            cls.create_skill("Perception", "wisdom", proficient=True, total_bonus=4),
            cls.create_skill("Investigation", "intelligence", proficient=True, total_bonus=3),
        ]
        
        return cls.create_character(
            level=level,
            classes=[rogue_class],
            skills=skills,
            saving_throw_proficiencies=["Dexterity", "Intelligence"],
            **overrides
        )

    @classmethod
    def create_multiclass_character(cls, **overrides) -> Character:
        """Create a multiclass character for complex tests."""
        fighter_class = cls.create_character_class(
            name="Fighter",
            level=3,
            hit_die=10,
            is_spellcaster=False
        )
        
        wizard_class = cls.create_character_class(
            name="Wizard",
            level=2,
            hit_die=6,
            is_spellcaster=True,
            spellcasting_ability="intelligence",
            spellcasting_type="full"
        )
        
        spellcasting = cls.create_spellcasting(
            is_spellcaster=True,
            spellcasting_ability="intelligence",
            spell_save_dc=13,
            spell_attack_bonus=5,
            spell_slots_level_1=3
        )
        
        return cls.create_character(
            level=5,
            classes=[fighter_class, wizard_class],
            spellcasting=spellcasting,
            saving_throw_proficiencies=["Strength", "Constitution", "Intelligence", "Wisdom"],
            **overrides
        )


class TestDataFactory:
    """Factory for creating test raw data structures."""

    @staticmethod
    def create_basic_raw_data() -> Dict[str, Any]:
        """Create basic raw D&D Beyond API response data for testing."""
        return {
            'id': 12345,
            'name': 'Test Character',
            'level': 5,
            'stats': [
                {'id': 1, 'value': 15},  # Strength
                {'id': 2, 'value': 14},  # Dexterity
                {'id': 3, 'value': 13},  # Constitution
                {'id': 4, 'value': 12},  # Intelligence
                {'id': 5, 'value': 11},  # Wisdom
                {'id': 6, 'value': 10}   # Charisma
            ],
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'Fighter',
                        'hitDie': 10
                    }
                }
            ],
            'race': {
                'definition': {
                    'name': 'Human'
                }
            },
            'background': {
                'definition': {
                    'name': 'Folk Hero'
                }
            },
            'baseHitPoints': 45,
            'modifiers': {
                'race': [],
                'class': [],
                'background': [],
                'item': [],
                'feat': []
            },
            'spells': {
                'race': [],
                'class': [],
                'feat': [],
                'item': []
            },
            'classSpells': []
        }

    @staticmethod
    def create_spellcaster_raw_data() -> Dict[str, Any]:
        """Create raw data for a spellcasting character."""
        data = TestDataFactory.create_basic_raw_data()
        data['classes'] = [
            {
                'level': 5,
                'definition': {
                    'name': 'Wizard',
                    'hitDie': 6,
                    'spellcastingAbilityId': 4  # Intelligence
                }
            }
        ]
        data['classSpells'] = [
            {
                'characterClassId': 1,
                'spells': [
                    {
                        'definition': {
                            'id': 1,
                            'name': 'Magic Missile',
                            'level': 1
                        }
                    }
                ]
            }
        ]
        return data

    @staticmethod
    def create_proficiency_raw_data() -> Dict[str, Any]:
        """Create raw data with various proficiencies."""
        data = TestDataFactory.create_basic_raw_data()
        data['modifiers']['class'] = [
            {
                'subType': 'proficiency',
                'type': 'proficiency',
                'friendlyTypeName': 'Skill',
                'friendlySubtypeName': 'Athletics'
            },
            {
                'subType': 'saving-throws',
                'type': 'proficiency',
                'friendlyTypeName': 'Saving Throw',
                'friendlySubtypeName': 'Strength'
            }
        ]
        return data