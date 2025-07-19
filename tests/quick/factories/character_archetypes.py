"""
Character archetype factories for quick tests.

Provides pre-built character data for common D&D archetypes.
"""

from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class CharacterArchetype:
    """Base character archetype data."""
    name: str
    level: int
    classes: List[Dict[str, Any]]
    ability_scores: Dict[str, int]
    race: str
    background: str
    expected_ac: int
    expected_hp: int
    is_spellcaster: bool = False

class CharacterArchetypeFactory:
    """Factory for creating character archetype test data."""
    
    @staticmethod
    def create_fighter(level: int = 1) -> Dict[str, Any]:
        """Create a basic fighter character."""
        return {
            "name": "Test Fighter",
            "level": level,
            "classes": [{
                "name": "Fighter",
                "level": level,
                "hit_die": 10,
                "subclass": None
            }],
            "ability_scores": {
                "strength": 16,
                "dexterity": 14,
                "constitution": 15,
                "intelligence": 10,
                "wisdom": 12,
                "charisma": 8
            },
            "species": {"name": "Human"},
            "background": {"name": "Soldier"},
            "armor_class": 16,  # Chain mail
            "hit_points": 10 + ((level - 1) * 6),  # d10 + con mod
            "is_spellcaster": False,
            "proficiency_bonus": 2 + ((level - 1) // 4)
        }
    
    @staticmethod
    def create_wizard(level: int = 1) -> Dict[str, Any]:
        """Create a basic wizard character."""
        return {
            "name": "Test Wizard",
            "level": level,
            "classes": [{
                "name": "Wizard",
                "level": level,
                "hit_die": 6,
                "subclass": "School of Evocation" if level >= 2 else None
            }],
            "ability_scores": {
                "strength": 8,
                "dexterity": 14,
                "constitution": 13,
                "intelligence": 16,
                "wisdom": 12,
                "charisma": 10
            },
            "species": {"name": "High Elf"},
            "background": {"name": "Sage"},
            "armor_class": 12,  # Mage armor
            "hit_points": 6 + ((level - 1) * 4),  # d6 + con mod
            "is_spellcaster": True,
            "proficiency_bonus": 2 + ((level - 1) // 4),
            "spell_slots": {
                "1": min(level + 1, 4) if level >= 1 else 0,
                "2": min(level - 1, 3) if level >= 3 else 0,
                "3": min(level - 3, 3) if level >= 5 else 0,
                "4": min(level - 5, 3) if level >= 7 else 0,
                "5": 1 if level >= 9 else 0,  # Level 9 gets 1 5th level slot
                "6": min(level - 9, 1) if level >= 11 else 0,
                "7": min(level - 11, 1) if level >= 13 else 0,
                "8": min(level - 13, 1) if level >= 15 else 0,
                "9": min(level - 15, 1) if level >= 17 else 0,
            }
        }
    
    @staticmethod
    def create_rogue(level: int = 1) -> Dict[str, Any]:
        """Create a basic rogue character."""
        return {
            "name": "Test Rogue",
            "level": level,
            "classes": [{
                "name": "Rogue",
                "level": level,
                "hit_die": 8,
                "subclass": "Thief" if level >= 3 else None
            }],
            "ability_scores": {
                "strength": 10,
                "dexterity": 16,
                "constitution": 14,
                "intelligence": 12,
                "wisdom": 13,
                "charisma": 8
            },
            "species": {"name": "Halfling"},
            "background": {"name": "Criminal"},
            "armor_class": 13,  # Leather armor + dex
            "hit_points": 8 + ((level - 1) * 5),  # d8 + con mod
            "is_spellcaster": False,
            "proficiency_bonus": 2 + ((level - 1) // 4)
        }
    
    @staticmethod
    def create_multiclass_fighter_wizard(fighter_level: int = 3, wizard_level: int = 2) -> Dict[str, Any]:
        """Create a multiclass fighter/wizard character."""
        total_level = fighter_level + wizard_level
        return {
            "name": "Test Multiclass",
            "level": total_level,
            "classes": [
                {
                    "name": "Fighter",
                    "level": fighter_level,
                    "hit_die": 10,
                    "subclass": None
                },
                {
                    "name": "Wizard", 
                    "level": wizard_level,
                    "hit_die": 6,
                    "subclass": None
                }
            ],
            "ability_scores": {
                "strength": 14,
                "dexterity": 14,
                "constitution": 15,
                "intelligence": 15,
                "wisdom": 12,
                "charisma": 10
            },
            "species": {"name": "Half-Elf"},
            "background": {"name": "Noble"},
            "armor_class": 16,  # Chain mail
            "hit_points": 10 + 6 + ((total_level - 2) * 5),  # Fighter d10 + Wizard d6 + avg
            "is_spellcaster": True,
            "proficiency_bonus": 2 + ((total_level - 1) // 4),
            "spell_slots": {
                "1": min(wizard_level + 1, 4) if wizard_level >= 1 else 0,
                "2": min(wizard_level - 1, 3) if wizard_level >= 3 else 0,
                "3": min(wizard_level - 3, 3) if wizard_level >= 5 else 0,
                "4": min(wizard_level - 5, 3) if wizard_level >= 7 else 0,
                "5": 1 if wizard_level >= 9 else 0,
                "6": min(wizard_level - 9, 1) if wizard_level >= 11 else 0,
                "7": min(wizard_level - 11, 1) if wizard_level >= 13 else 0,
                "8": min(wizard_level - 13, 1) if wizard_level >= 15 else 0,
                "9": min(wizard_level - 15, 1) if wizard_level >= 17 else 0,
            }
        }
    
    @staticmethod
    def create_level_20_barbarian() -> Dict[str, Any]:
        """Create a level 20 barbarian for extreme testing."""
        return {
            "name": "Test Barbarian Max Level",
            "level": 20,
            "classes": [{
                "name": "Barbarian",
                "level": 20,
                "hit_die": 12,
                "subclass": "Path of the Berserker"
            }],
            "ability_scores": {
                "strength": 24,  # 20 + 4 from ability score improvements
                "dexterity": 14,
                "constitution": 20,  # 15 + 4 from ability score improvements + 1 from race
                "intelligence": 8,
                "wisdom": 12,
                "charisma": 10
            },
            "species": {"name": "Half-Orc"},
            "background": {"name": "Outlander"},
            "armor_class": 17,  # Unarmored defense: 10 + dex(2) + con(5)
            "hit_points": 285,  # Max HP for level 20 barbarian
            "is_spellcaster": False,
            "proficiency_bonus": 6,
            "features": ["Rage", "Unarmored Defense", "Primal Champion"]
        }
    
    @staticmethod
    def get_archetype_by_name(name: str, level: int = 1) -> Dict[str, Any]:
        """Get archetype by name."""
        archetypes = {
            'fighter': CharacterArchetypeFactory.create_fighter,
            'wizard': CharacterArchetypeFactory.create_wizard,
            'rogue': CharacterArchetypeFactory.create_rogue,
            'barbarian': CharacterArchetypeFactory.create_level_20_barbarian if level == 20 else lambda l: CharacterArchetypeFactory.create_fighter(l)
        }
        
        if name not in archetypes:
            raise ValueError(f"Unknown archetype: {name}. Available: {list(archetypes.keys())}")
        
        return archetypes[name](level) if name != 'barbarian' or level != 20 else archetypes[name]()
    
    @staticmethod
    def get_all_archetypes() -> List[str]:
        """Get list of all available archetypes."""
        return ['fighter', 'wizard', 'rogue', 'barbarian', 'multiclass']