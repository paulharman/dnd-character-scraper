"""
Edge case factories for quick tests.

Provides edge case scenarios for testing boundary conditions.
"""

from typing import Dict, Any, List
from .character_archetypes import CharacterArchetypeFactory

class EdgeCaseFactory:
    """Factory for creating edge case test scenarios."""
    
    @staticmethod
    def create_level_1_character() -> Dict[str, Any]:
        """Create a level 1 character for minimum level testing."""
        return {
            "name": "Level 1 Edge Case",
            "level": 1,
            "classes": [{
                "name": "Fighter",
                "level": 1,
                "hit_die": 10,
                "subclass": None
            }],
            "ability_scores": {
                "strength": 8,  # Minimum practical score
                "dexterity": 8,
                "constitution": 8,
                "intelligence": 8,
                "wisdom": 8,
                "charisma": 8
            },
            "race": "Human",
            "background": "Folk Hero",
            "armor_class": 10,  # No armor, minimum dex
            "hit_points": 9,    # d10 + con mod (-1)
            "is_spellcaster": False,
            "proficiency_bonus": 2
        }
    
    @staticmethod
    def create_level_20_character() -> Dict[str, Any]:
        """Create a level 20 character for maximum level testing."""
        return {
            "name": "Level 20 Edge Case",
            "level": 20,
            "classes": [{
                "name": "Paladin",
                "level": 20,
                "hit_die": 10,
                "subclass": "Oath of Devotion"
            }],
            "ability_scores": {
                "strength": 20,
                "dexterity": 12,
                "constitution": 18,
                "intelligence": 10,
                "wisdom": 14,
                "charisma": 20
            },
            "race": "Dragonborn",
            "background": "Noble",
            "armor_class": 20,  # Plate armor + shield
            "hit_points": 190,  # High HP for level 20
            "is_spellcaster": True,
            "proficiency_bonus": 6,
            "spell_slots": {
                "1": 4, "2": 3, "3": 3, "4": 3, "5": 2
            }
        }
    
    @staticmethod
    def create_extreme_stats_character() -> Dict[str, Any]:
        """Create a character with extreme ability scores."""
        return {
            "name": "Extreme Stats Character",
            "level": 10,
            "classes": [{
                "name": "Barbarian",
                "level": 10,
                "hit_die": 12,
                "subclass": "Path of the Berserker"
            }],
            "ability_scores": {
                "strength": 30,  # Maximum possible
                "dexterity": 1,   # Minimum possible
                "constitution": 30,
                "intelligence": 1,
                "wisdom": 1,
                "charisma": 1
            },
            "race": "Custom",
            "background": "Custom",
            "armor_class": 15,  # Unarmored defense with extreme stats
            "hit_points": 250,  # Very high HP
            "is_spellcaster": False,
            "proficiency_bonus": 4
        }
    
    @staticmethod
    def create_complex_multiclass() -> Dict[str, Any]:
        """Create a complex multiclass character."""
        return {
            "name": "Complex Multiclass",
            "level": 20,
            "classes": [
                {
                    "name": "Fighter",
                    "level": 5,
                    "hit_die": 10,
                    "subclass": "Champion"
                },
                {
                    "name": "Rogue",
                    "level": 5,
                    "hit_die": 8,
                    "subclass": "Assassin"
                },
                {
                    "name": "Ranger",
                    "level": 5,
                    "hit_die": 10,
                    "subclass": "Hunter"
                },
                {
                    "name": "Cleric",
                    "level": 5,
                    "hit_die": 8,
                    "subclass": "Life Domain"
                }
            ],
            "ability_scores": {
                "strength": 14,
                "dexterity": 16,
                "constitution": 14,
                "intelligence": 12,
                "wisdom": 16,
                "charisma": 10
            },
            "race": "Half-Elf",
            "background": "Outlander",
            "armor_class": 17,
            "hit_points": 140,
            "is_spellcaster": True,
            "proficiency_bonus": 6,
            "spell_slots": {
                "1": 4, "2": 3, "3": 2
            }
        }
    
    @staticmethod
    def create_no_spellcaster_with_spell_slots() -> Dict[str, Any]:
        """Create edge case with spell slots but no spellcaster flag."""
        return {
            "name": "Spell Slots Edge Case",
            "level": 5,
            "classes": [{
                "name": "Eldritch Knight",
                "level": 5,
                "hit_die": 10,
                "subclass": "Eldritch Knight"
            }],
            "ability_scores": {
                "strength": 16,
                "dexterity": 14,
                "constitution": 15,
                "intelligence": 14,
                "wisdom": 12,
                "charisma": 10
            },
            "race": "Human",
            "background": "Soldier",
            "armor_class": 18,
            "hit_points": 42,
            "is_spellcaster": False,  # Edge case: has spell slots but flag is false
            "proficiency_bonus": 3,
            "spell_slots": {
                "1": 2
            }
        }
    
    @staticmethod
    def create_empty_character() -> Dict[str, Any]:
        """Create a character with minimal data."""
        return {
            "name": "Empty Character",
            "level": 1,
            "classes": [],
            "ability_scores": {},
            "race": None,
            "background": None,
            "armor_class": None,
            "hit_points": None,
            "is_spellcaster": False,
            "proficiency_bonus": None
        }
    
    @staticmethod
    def create_conflicting_features_character() -> Dict[str, Any]:
        """Create a character with conflicting features (e.g., Barbarian/Monk)."""
        return {
            "name": "Conflicting Features",
            "level": 6,
            "classes": [
                {
                    "name": "Barbarian",
                    "level": 3,
                    "hit_die": 12,
                    "subclass": "Path of the Berserker"
                },
                {
                    "name": "Monk",
                    "level": 3,
                    "hit_die": 8,
                    "subclass": "Way of the Open Hand"
                }
            ],
            "ability_scores": {
                "strength": 15,
                "dexterity": 16,
                "constitution": 14,
                "intelligence": 10,
                "wisdom": 15,
                "charisma": 8
            },
            "race": "Human",
            "background": "Hermit",
            "armor_class": 13,  # Conflicting unarmored defense calculations
            "hit_points": 45,
            "is_spellcaster": False,
            "proficiency_bonus": 3,
            "features": ["Unarmored Defense (Barbarian)", "Unarmored Defense (Monk)", "Rage"]
        }
    
    @staticmethod
    def get_edge_case_by_name(name: str) -> Dict[str, Any]:
        """Get edge case by name."""
        edge_cases = {
            'level_1': EdgeCaseFactory.create_level_1_character,
            'level_20': EdgeCaseFactory.create_level_20_character,
            'extreme_stats': EdgeCaseFactory.create_extreme_stats_character,
            'complex_multiclass': EdgeCaseFactory.create_complex_multiclass,
            'spell_slots_edge': EdgeCaseFactory.create_no_spellcaster_with_spell_slots,
            'empty': EdgeCaseFactory.create_empty_character,
            'conflicting_features': EdgeCaseFactory.create_conflicting_features_character
        }
        
        if name not in edge_cases:
            raise ValueError(f"Unknown edge case: {name}. Available: {list(edge_cases.keys())}")
        
        return edge_cases[name]()
    
    @staticmethod
    def get_all_edge_cases() -> List[str]:
        """Get list of all available edge cases."""
        return [
            'level_1', 'level_20', 'extreme_stats', 'complex_multiclass',
            'spell_slots_edge', 'empty', 'conflicting_features'
        ]