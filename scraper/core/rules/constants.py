"""
D&D Beyond Character Scraper - Game Constants

Comprehensive D&D 5e game constants and mappings for both 2014 and 2024 rule sets.
Contains source IDs, class progressions, spell data, and other game mechanics data.
"""

from typing import Dict, List, Set, Any
from enum import Enum


class SpellcastingType(Enum):
    """Types of spellcasting progression."""
    FULL = "full"           # Cleric, Druid, Sorcerer, Wizard
    HALF = "half"           # Paladin, Ranger
    THIRD = "third"         # Arcane Trickster, Eldritch Knight
    WARLOCK = "warlock"     # Warlock (Pact Magic)
    NONE = "none"           # Non-spellcasters


class GameConstants:
    """
    Comprehensive game constants for D&D 5e, supporting both 2014 and 2024 rules.
    """
    
    # =============================================================================
    # SOURCE BOOK IDS
    # =============================================================================
    
    # 2024 D&D Beyond Source IDs
    SOURCE_2024_IDS: Set[int] = {142, 143, 144}  # PHB 2024, DMG 2024, MM 2024
    
    # Common 2014 Source IDs (non-exhaustive)
    SOURCE_2014_IDS: Set[int] = {
        1,   # Player's Handbook
        2,   # Monster Manual  
        3,   # Dungeon Master's Guide
        4,   # Curse of Strahd
        5,   # Storm King's Thunder
        6,   # Volo's Guide to Monsters
        7,   # The Rise of Tiamat
        8,   # Princes of the Apocalypse
        9,   # Out of the Abyss
        17,  # Sword Coast Adventurer's Guide
        39,  # Xanathar's Guide to Everything
        40,  # Mordenkainen's Tome of Foes
        48,  # Tasha's Cauldron of Everything
        # Add more as needed
    }
    
    # =============================================================================
    # CLASS INFORMATION
    # =============================================================================
    
    # Class hit dice
    CLASS_HIT_DICE: Dict[str, int] = {
        "Artificer": 8,
        "Barbarian": 12,
        "Bard": 8,
        "Cleric": 8,
        "Druid": 8,
        "Fighter": 10,
        "Monk": 8,
        "Paladin": 10,
        "Ranger": 10,
        "Rogue": 8,
        "Sorcerer": 6,
        "Warlock": 8,
        "Wizard": 6
    }
    
    # Spellcasting progression by class
    CLASS_SPELLCASTING: Dict[str, SpellcastingType] = {
        "Artificer": SpellcastingType.HALF,
        "Bard": SpellcastingType.FULL,
        "Cleric": SpellcastingType.FULL,
        "Druid": SpellcastingType.FULL,
        "Paladin": SpellcastingType.HALF,
        "Ranger": SpellcastingType.HALF,
        "Sorcerer": SpellcastingType.FULL,
        "Warlock": SpellcastingType.WARLOCK,
        "Wizard": SpellcastingType.FULL,
        # Subclass-based spellcasting
        "Fighter": SpellcastingType.NONE,  # Eldritch Knight = THIRD
        "Rogue": SpellcastingType.NONE,    # Arcane Trickster = THIRD
        "Barbarian": SpellcastingType.NONE,
        "Monk": SpellcastingType.NONE
    }
    
    # Subclasses with spellcasting
    SPELLCASTING_SUBCLASSES: Dict[str, Dict[str, SpellcastingType]] = {
        "Fighter": {
            "Eldritch Knight": SpellcastingType.THIRD
        },
        "Rogue": {
            "Arcane Trickster": SpellcastingType.THIRD
        }
    }
    
    # Primary spellcasting abilities
    SPELLCASTING_ABILITIES: Dict[str, str] = {
        "Artificer": "Intelligence",
        "Bard": "Charisma", 
        "Cleric": "Wisdom",
        "Druid": "Wisdom",
        "Paladin": "Charisma",
        "Ranger": "Wisdom",
        "Sorcerer": "Charisma",
        "Warlock": "Charisma",
        "Wizard": "Intelligence",
        "Fighter": "Intelligence",  # Eldritch Knight
        "Rogue": "Intelligence"     # Arcane Trickster
    }
    
    # =============================================================================
    # SPELL SLOT PROGRESSIONS
    # =============================================================================
    
    # Full caster spell slots by level
    FULL_CASTER_SLOTS: Dict[int, List[int]] = {
        1:  [2, 0, 0, 0, 0, 0, 0, 0, 0],
        2:  [3, 0, 0, 0, 0, 0, 0, 0, 0],
        3:  [4, 2, 0, 0, 0, 0, 0, 0, 0],
        4:  [4, 3, 0, 0, 0, 0, 0, 0, 0],
        5:  [4, 3, 2, 0, 0, 0, 0, 0, 0],
        6:  [4, 3, 3, 0, 0, 0, 0, 0, 0],
        7:  [4, 3, 3, 1, 0, 0, 0, 0, 0],
        8:  [4, 3, 3, 2, 0, 0, 0, 0, 0],
        9:  [4, 3, 3, 3, 1, 0, 0, 0, 0],
        10: [4, 3, 3, 3, 2, 0, 0, 0, 0],
        11: [4, 3, 3, 3, 2, 1, 0, 0, 0],
        12: [4, 3, 3, 3, 2, 1, 0, 0, 0],
        13: [4, 3, 3, 3, 2, 1, 1, 0, 0],
        14: [4, 3, 3, 3, 2, 1, 1, 0, 0],
        15: [4, 3, 3, 3, 2, 1, 1, 1, 0],
        16: [4, 3, 3, 3, 2, 1, 1, 1, 0],
        17: [4, 3, 3, 3, 2, 1, 1, 1, 1],
        18: [4, 3, 3, 3, 3, 1, 1, 1, 1],
        19: [4, 3, 3, 3, 3, 2, 1, 1, 1],
        20: [4, 3, 3, 3, 3, 2, 2, 1, 1]
    }
    
    # Half caster spell slots by level (Paladin, Ranger)
    HALF_CASTER_SLOTS: Dict[int, List[int]] = {
        1:  [0, 0, 0, 0, 0, 0, 0, 0, 0],
        2:  [2, 0, 0, 0, 0, 0, 0, 0, 0],
        3:  [3, 0, 0, 0, 0, 0, 0, 0, 0],
        4:  [3, 0, 0, 0, 0, 0, 0, 0, 0],
        5:  [4, 2, 0, 0, 0, 0, 0, 0, 0],
        6:  [4, 2, 0, 0, 0, 0, 0, 0, 0],
        7:  [4, 3, 0, 0, 0, 0, 0, 0, 0],
        8:  [4, 3, 0, 0, 0, 0, 0, 0, 0],
        9:  [4, 3, 2, 0, 0, 0, 0, 0, 0],
        10: [4, 3, 2, 0, 0, 0, 0, 0, 0],
        11: [4, 3, 3, 0, 0, 0, 0, 0, 0],
        12: [4, 3, 3, 0, 0, 0, 0, 0, 0],
        13: [4, 3, 3, 1, 0, 0, 0, 0, 0],
        14: [4, 3, 3, 1, 0, 0, 0, 0, 0],
        15: [4, 3, 3, 2, 0, 0, 0, 0, 0],
        16: [4, 3, 3, 2, 0, 0, 0, 0, 0],
        17: [4, 3, 3, 3, 1, 0, 0, 0, 0],
        18: [4, 3, 3, 3, 1, 0, 0, 0, 0],
        19: [4, 3, 3, 3, 2, 0, 0, 0, 0],
        20: [4, 3, 3, 3, 2, 0, 0, 0, 0]
    }
    
    # Third caster spell slots by level (Arcane Trickster, Eldritch Knight)
    THIRD_CASTER_SLOTS: Dict[int, List[int]] = {
        1:  [0, 0, 0, 0, 0, 0, 0, 0, 0],
        2:  [0, 0, 0, 0, 0, 0, 0, 0, 0],
        3:  [2, 0, 0, 0, 0, 0, 0, 0, 0],
        4:  [3, 0, 0, 0, 0, 0, 0, 0, 0],
        5:  [3, 0, 0, 0, 0, 0, 0, 0, 0],
        6:  [3, 0, 0, 0, 0, 0, 0, 0, 0],
        7:  [4, 2, 0, 0, 0, 0, 0, 0, 0],
        8:  [4, 2, 0, 0, 0, 0, 0, 0, 0],
        9:  [4, 2, 0, 0, 0, 0, 0, 0, 0],
        10: [4, 3, 0, 0, 0, 0, 0, 0, 0],
        11: [4, 3, 0, 0, 0, 0, 0, 0, 0],
        12: [4, 3, 0, 0, 0, 0, 0, 0, 0],
        13: [4, 3, 2, 0, 0, 0, 0, 0, 0],
        14: [4, 3, 2, 0, 0, 0, 0, 0, 0],
        15: [4, 3, 2, 0, 0, 0, 0, 0, 0],
        16: [4, 3, 3, 0, 0, 0, 0, 0, 0],
        17: [4, 3, 3, 0, 0, 0, 0, 0, 0],
        18: [4, 3, 3, 0, 0, 0, 0, 0, 0],
        19: [4, 3, 3, 1, 0, 0, 0, 0, 0],
        20: [4, 3, 3, 1, 0, 0, 0, 0, 0]
    }
    
    # Warlock spell slots by level (Pact Magic)
    WARLOCK_SLOTS: Dict[int, Dict[str, int]] = {
        1:  {"slots": 1, "level": 1},
        2:  {"slots": 2, "level": 1},
        3:  {"slots": 2, "level": 2},
        4:  {"slots": 2, "level": 2},
        5:  {"slots": 2, "level": 3},
        6:  {"slots": 2, "level": 3},
        7:  {"slots": 2, "level": 4},
        8:  {"slots": 2, "level": 4},
        9:  {"slots": 2, "level": 5},
        10: {"slots": 2, "level": 5},
        11: {"slots": 3, "level": 5},
        12: {"slots": 3, "level": 5},
        13: {"slots": 3, "level": 5},
        14: {"slots": 3, "level": 5},
        15: {"slots": 3, "level": 5},
        16: {"slots": 3, "level": 5},
        17: {"slots": 4, "level": 5},
        18: {"slots": 4, "level": 5},
        19: {"slots": 4, "level": 5},
        20: {"slots": 4, "level": 5}
    }
    
    # =============================================================================
    # ABILITY SCORES
    # =============================================================================
    
    # Ability score names
    ABILITIES: List[str] = [
        "strength", "dexterity", "constitution", 
        "intelligence", "wisdom", "charisma"
    ]
    
    # Ability score choice mappings (from D&D Beyond API)
    ABILITY_CHOICE_MAPPING: Dict[int, str] = {
        1: "strength",
        2: "dexterity", 
        3: "constitution",
        4: "intelligence",
        5: "wisdom",
        6: "charisma"
    }
    
    # =============================================================================
    # PROFICIENCY AND SKILLS
    # =============================================================================
    
    # Skills mapped to their governing abilities
    SKILL_ABILITIES: Dict[str, str] = {
        "Acrobatics": "dexterity",
        "Animal Handling": "wisdom",
        "Arcana": "intelligence",
        "Athletics": "strength",
        "Deception": "charisma",
        "History": "intelligence",
        "Insight": "wisdom",
        "Intimidation": "charisma",
        "Investigation": "intelligence",
        "Medicine": "wisdom",
        "Nature": "intelligence",
        "Perception": "wisdom",
        "Performance": "charisma",
        "Persuasion": "charisma",
        "Religion": "intelligence",
        "Sleight of Hand": "dexterity",
        "Stealth": "dexterity",
        "Survival": "wisdom"
    }
    
    # Proficiency bonus by character level
    PROFICIENCY_BONUS: Dict[int, int] = {
        1: 2, 2: 2, 3: 2, 4: 2,
        5: 3, 6: 3, 7: 3, 8: 3,
        9: 4, 10: 4, 11: 4, 12: 4,
        13: 5, 14: 5, 15: 5, 16: 5,
        17: 6, 18: 6, 19: 6, 20: 6
    }
    
    # =============================================================================
    # RULE VERSION DIFFERENCES
    # =============================================================================
    
    # 2024 specific feat categories
    FEAT_CATEGORIES_2024: Set[str] = {
        "origin", "general", "fighting_style", "epic_boon"
    }
    
    # Species that are new or changed in 2024
    SPECIES_CHANGES_2024: Dict[str, str] = {
        # New in 2024 PHB
        "Aasimar": "new_2024",
        "Goliath": "new_2024", 
        "Orc": "new_2024",
        
        # Legacy in 2024 (compatibility mode)
        "Half-Elf": "legacy",
        "Half-Orc": "legacy"
    }
    
    # =============================================================================
    # ARMOR CLASS CALCULATIONS
    # =============================================================================
    
    # Base AC calculation methods
    AC_CALCULATIONS: Dict[str, Dict[str, Any]] = {
        "Natural": {"base": 10, "dex": True, "max_dex": None},
        "Unarmored Defense (Barbarian)": {"base": 10, "dex": True, "con": True, "max_dex": None},
        "Unarmored Defense (Monk)": {"base": 10, "dex": True, "wis": True, "max_dex": None},
        "Mage Armor": {"base": 13, "dex": True, "max_dex": None},
        "Draconic Resilience": {"base": 13, "dex": True, "max_dex": None}
    }
    
    # Armor types and their AC calculations
    ARMOR_AC: Dict[str, Dict[str, Any]] = {
        # Light Armor
        "Padded": {"base": 11, "dex": True, "max_dex": None},
        "Leather": {"base": 11, "dex": True, "max_dex": None},
        "Studded Leather": {"base": 12, "dex": True, "max_dex": None},
        
        # Medium Armor  
        "Hide": {"base": 12, "dex": True, "max_dex": 2},
        "Chain Shirt": {"base": 13, "dex": True, "max_dex": 2},
        "Scale Mail": {"base": 14, "dex": True, "max_dex": 2},
        "Breastplate": {"base": 14, "dex": True, "max_dex": 2},
        "Half Plate": {"base": 15, "dex": True, "max_dex": 2},
        
        # Heavy Armor
        "Ring Mail": {"base": 14, "dex": False, "max_dex": 0},
        "Chain Mail": {"base": 16, "dex": False, "max_dex": 0},
        "Splint": {"base": 17, "dex": False, "max_dex": 0},
        "Plate": {"base": 18, "dex": False, "max_dex": 0}
    }
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    @classmethod
    def get_ability_modifier(cls, score: int) -> int:
        """Calculate ability modifier from ability score."""
        return (score - 10) // 2
    
    @classmethod
    def get_proficiency_bonus(cls, level: int) -> int:
        """Get proficiency bonus for character level."""
        return cls.PROFICIENCY_BONUS.get(level, 2)
    
    @classmethod
    def get_spell_slots(cls, class_name: str, level: int, rule_version: str = "2014") -> List[int]:
        """Get spell slots for a class at given level."""
        spellcasting_type = cls.CLASS_SPELLCASTING.get(class_name, SpellcastingType.NONE)
        
        if spellcasting_type == SpellcastingType.FULL:
            return cls.FULL_CASTER_SLOTS.get(level, [0] * 9)
        elif spellcasting_type == SpellcastingType.HALF:
            return cls.HALF_CASTER_SLOTS.get(level, [0] * 9)
        elif spellcasting_type == SpellcastingType.THIRD:
            return cls.THIRD_CASTER_SLOTS.get(level, [0] * 9)
        elif spellcasting_type == SpellcastingType.WARLOCK:
            warlock_data = cls.WARLOCK_SLOTS.get(level, {"slots": 0, "level": 1})
            slots = [0] * 9
            if warlock_data["slots"] > 0:
                slot_level = warlock_data["level"] - 1  # Convert to 0-based index
                if 0 <= slot_level < 9:
                    slots[slot_level] = warlock_data["slots"]
            return slots
        else:
            return [0] * 9
    
    @classmethod
    def is_spellcaster(cls, class_name: str, subclass_name: str = None) -> bool:
        """Check if a class/subclass combination is a spellcaster."""
        base_spellcasting = cls.CLASS_SPELLCASTING.get(class_name, SpellcastingType.NONE)
        
        if base_spellcasting != SpellcastingType.NONE:
            return True
        
        # Check subclass spellcasting
        if subclass_name and class_name in cls.SPELLCASTING_SUBCLASSES:
            subclass_spellcasting = cls.SPELLCASTING_SUBCLASSES[class_name].get(
                subclass_name, SpellcastingType.NONE
            )
            return subclass_spellcasting != SpellcastingType.NONE
        
        return False
    
    @classmethod
    def get_spellcasting_ability(cls, class_name: str) -> str:
        """Get the primary spellcasting ability for a class."""
        return cls.SPELLCASTING_ABILITIES.get(class_name, "Intelligence")