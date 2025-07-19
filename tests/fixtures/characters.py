"""
Character test fixtures for validation and testing.

This module provides standardized character data for testing instead of
character-specific scripts. Use these fixtures for consistent testing.
"""

from typing import Dict, Any, List
from datetime import datetime


class CharacterFixtures:
    """Collection of character test fixtures."""
    
    # Basic Fighter - Simple character for basic testing
    BASIC_FIGHTER = {
        "id": 100001,
        "name": "Test Fighter",
        "level": 5,
        "proficiency_bonus": 3,
        "rule_version": "2014",
        "ability_scores": {
            "strength": 16,
            "dexterity": 14,
            "constitution": 15,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 8
        },
        "classes": [
            {
                "name": "Fighter",
                "level": 5,
                "hit_die": 10,
                "subclass": "Champion",
                "is_spellcaster": False
            }
        ],
        "species": {
            "name": "Human",
            "subrace": "Variant",
            "speed": 30
        },
        "background": {
            "name": "Soldier"
        },
        "hit_points": {
            "maximum": 47,
            "current": 47,
            "temporary": 0
        },
        "armor_class": {
            "total": 18,
            "base": 10,
            "armor_bonus": 6,
            "dexterity_bonus": 2
        },
        "spellcasting": {
            "is_spellcaster": False
        },
        "skills": [
            {"name": "Athletics", "ability": "strength", "proficient": True, "total_bonus": 6},
            {"name": "Intimidation", "ability": "charisma", "proficient": True, "total_bonus": 2}
        ],
        "saving_throw_proficiencies": ["Strength", "Constitution"],
        "equipment": [
            {"name": "Chain Mail", "type": "armor", "ac_bonus": 6},
            {"name": "Shield", "type": "shield", "ac_bonus": 2},
            {"name": "Longsword", "type": "weapon", "damage": "1d8+3"}
        ]
    }
    
    # Spellcaster Wizard - For spell testing
    WIZARD_SPELLCASTER = {
        "id": 100002,
        "name": "Test Wizard",
        "level": 5,
        "proficiency_bonus": 3,
        "rule_version": "2014",
        "ability_scores": {
            "strength": 8,
            "dexterity": 14,
            "constitution": 13,
            "intelligence": 16,
            "wisdom": 12,
            "charisma": 10
        },
        "classes": [
            {
                "name": "Wizard",
                "level": 5,
                "hit_die": 6,
                "subclass": "School of Evocation",
                "is_spellcaster": True,
                "spellcasting_ability": "intelligence",
                "spellcasting_type": "full"
            }
        ],
        "species": {
            "name": "High Elf",
            "subrace": None,
            "speed": 30
        },
        "background": {
            "name": "Sage"
        },
        "hit_points": {
            "maximum": 32,
            "current": 32,
            "temporary": 0
        },
        "armor_class": {
            "total": 12,
            "base": 10,
            "dexterity_bonus": 2
        },
        "spellcasting": {
            "is_spellcaster": True,
            "spellcasting_ability": "intelligence",
            "spell_save_dc": 14,
            "spell_attack_bonus": 6,
            "spell_slots": {
                "1": {"max": 4, "used": 1, "remaining": 3},
                "2": {"max": 3, "used": 0, "remaining": 3},
                "3": {"max": 2, "used": 1, "remaining": 1}
            }
        },
        "spells": [
            # Cantrips
            {"name": "Fire Bolt", "level": 0, "school": "Evocation", "source": "Racial"},
            {"name": "Mage Hand", "level": 0, "school": "Transmutation", "source": "Wizard"},
            {"name": "Prestidigitation", "level": 0, "school": "Transmutation", "source": "Wizard"},
            # 1st Level
            {"name": "Magic Missile", "level": 1, "school": "Evocation", "source": "Wizard"},
            {"name": "Shield", "level": 1, "school": "Abjuration", "source": "Wizard"},
            {"name": "Detect Magic", "level": 1, "school": "Divination", "source": "Racial"},
            # 2nd Level
            {"name": "Misty Step", "level": 2, "school": "Conjuration", "source": "Wizard"},
            {"name": "Web", "level": 2, "school": "Conjuration", "source": "Wizard"},
            # 3rd Level
            {"name": "Fireball", "level": 3, "school": "Evocation", "source": "Wizard"}
        ],
        "skills": [
            {"name": "Arcana", "ability": "intelligence", "proficient": True, "total_bonus": 6},
            {"name": "History", "ability": "intelligence", "proficient": True, "total_bonus": 6},
            {"name": "Investigation", "ability": "intelligence", "proficient": True, "total_bonus": 6}
        ],
        "saving_throw_proficiencies": ["Intelligence", "Wisdom"]
    }
    
    # Multiclass Character - For complex testing
    MULTICLASS_FIGHTER_WIZARD = {
        "id": 100003,
        "name": "Test Multiclass",
        "level": 6,
        "proficiency_bonus": 3,
        "rule_version": "2014",
        "ability_scores": {
            "strength": 15,
            "dexterity": 14,
            "constitution": 14,
            "intelligence": 15,
            "wisdom": 12,
            "charisma": 10
        },
        "classes": [
            {
                "name": "Fighter",
                "level": 4,
                "hit_die": 10,
                "subclass": "Eldritch Knight",
                "is_spellcaster": True,
                "spellcasting_ability": "intelligence",
                "spellcasting_type": "third"
            },
            {
                "name": "Wizard",
                "level": 2,
                "hit_die": 6,
                "subclass": "School of Abjuration",
                "is_spellcaster": True,
                "spellcasting_ability": "intelligence",
                "spellcasting_type": "full"
            }
        ],
        "species": {
            "name": "Half-Elf",
            "subrace": None,
            "speed": 30
        },
        "background": {
            "name": "Noble"
        },
        "hit_points": {
            "maximum": 52,
            "current": 52,
            "temporary": 0
        },
        "armor_class": {
            "total": 18,
            "base": 10,
            "armor_bonus": 6,
            "dexterity_bonus": 2
        },
        "spellcasting": {
            "is_spellcaster": True,
            "spellcasting_ability": "intelligence",
            "spell_save_dc": 13,
            "spell_attack_bonus": 5,
            "spell_slots": {
                "1": {"max": 3, "used": 0, "remaining": 3},
                "2": {"max": 2, "used": 1, "remaining": 1}
            }
        },
        "spells": [
            # Cantrips
            {"name": "Mage Hand", "level": 0, "school": "Transmutation", "source": "Fighter"},
            {"name": "Minor Illusion", "level": 0, "school": "Illusion", "source": "Fighter"},
            {"name": "Fire Bolt", "level": 0, "school": "Evocation", "source": "Wizard"},
            # 1st Level
            {"name": "Shield", "level": 1, "school": "Abjuration", "source": "Fighter"},
            {"name": "Magic Missile", "level": 1, "school": "Evocation", "source": "Fighter"},
            {"name": "Detect Magic", "level": 1, "school": "Divination", "source": "Wizard"},
            # 2nd Level
            {"name": "Misty Step", "level": 2, "school": "Conjuration", "source": "Wizard"}
        ],
        "skills": [
            {"name": "Athletics", "ability": "strength", "proficient": True, "total_bonus": 5},
            {"name": "Arcana", "ability": "intelligence", "proficient": True, "total_bonus": 5},
            {"name": "Persuasion", "ability": "charisma", "proficient": True, "total_bonus": 3}
        ],
        "saving_throw_proficiencies": ["Strength", "Constitution", "Intelligence", "Wisdom"]
    }
    
    # Rogue with Expertise - For skill testing
    ROGUE_WITH_EXPERTISE = {
        "id": 100004,
        "name": "Test Rogue",
        "level": 8,
        "proficiency_bonus": 3,
        "rule_version": "2014",
        "ability_scores": {
            "strength": 10,
            "dexterity": 18,
            "constitution": 14,
            "intelligence": 12,
            "wisdom": 13,
            "charisma": 14
        },
        "classes": [
            {
                "name": "Rogue",
                "level": 8,
                "hit_die": 8,
                "subclass": "Arcane Trickster",
                "is_spellcaster": True,
                "spellcasting_ability": "intelligence",
                "spellcasting_type": "third"
            }
        ],
        "species": {
            "name": "Halfling",
            "subrace": "Lightfoot",
            "speed": 25
        },
        "background": {
            "name": "Criminal"
        },
        "hit_points": {
            "maximum": 58,
            "current": 58,
            "temporary": 0
        },
        "armor_class": {
            "total": 15,
            "base": 10,
            "armor_bonus": 1,
            "dexterity_bonus": 4
        },
        "spellcasting": {
            "is_spellcaster": True,
            "spellcasting_ability": "intelligence",
            "spell_save_dc": 12,
            "spell_attack_bonus": 4,
            "spell_slots": {
                "1": {"max": 2, "used": 0, "remaining": 2}
            }
        },
        "spells": [
            # Cantrips
            {"name": "Mage Hand", "level": 0, "school": "Transmutation", "source": "Rogue"},
            {"name": "Minor Illusion", "level": 0, "school": "Illusion", "source": "Rogue"},
            # 1st Level
            {"name": "Charm Person", "level": 1, "school": "Enchantment", "source": "Rogue"},
            {"name": "Sleep", "level": 1, "school": "Enchantment", "source": "Rogue"}
        ],
        "skills": [
            {"name": "Stealth", "ability": "dexterity", "proficient": True, "expertise": True, "total_bonus": 13},
            {"name": "Sleight of Hand", "ability": "dexterity", "proficient": True, "expertise": True, "total_bonus": 13},
            {"name": "Thieves' Tools", "ability": "dexterity", "proficient": True, "expertise": True, "total_bonus": 13},
            {"name": "Perception", "ability": "wisdom", "proficient": True, "total_bonus": 4},
            {"name": "Investigation", "ability": "intelligence", "proficient": True, "total_bonus": 4},
            {"name": "Deception", "ability": "charisma", "proficient": True, "total_bonus": 5}
        ],
        "saving_throw_proficiencies": ["Dexterity", "Intelligence"]
    }
    
    # Edge Case Character - For testing boundary conditions
    EDGE_CASE_CHARACTER = {
        "id": 100005,
        "name": "Edge Case Test",
        "level": 20,
        "proficiency_bonus": 6,
        "rule_version": "2014",
        "ability_scores": {
            "strength": 30,  # Beyond normal limits
            "dexterity": 1,   # Minimum
            "constitution": 20,
            "intelligence": 8,
            "wisdom": 30,    # Beyond normal limits
            "charisma": 1    # Minimum
        },
        "classes": [
            {
                "name": "Barbarian",
                "level": 20,
                "hit_die": 12,
                "subclass": "Path of the Totem Warrior",
                "is_spellcaster": False
            }
        ],
        "species": {
            "name": "Goliath",
            "subrace": None,
            "speed": 30
        },
        "background": {
            "name": "Outlander"
        },
        "hit_points": {
            "maximum": 285,  # Very high HP
            "current": 285,
            "temporary": 0
        },
        "armor_class": {
            "total": 24,  # Very high AC
            "base": 10,
            "armor_bonus": 0,
            "dexterity_bonus": -5,  # Negative modifier
            "natural_armor": 19
        },
        "spellcasting": {
            "is_spellcaster": False
        },
        "skills": [
            {"name": "Athletics", "ability": "strength", "proficient": True, "total_bonus": 22},  # Very high
            {"name": "Survival", "ability": "wisdom", "proficient": True, "total_bonus": 16}
        ],
        "saving_throw_proficiencies": ["Strength", "Constitution"]
    }


class RawDataFixtures:
    """Raw D&D Beyond API response fixtures for testing."""
    
    @staticmethod
    def get_basic_fighter_raw() -> Dict[str, Any]:
        """Get raw D&D Beyond data for basic fighter."""
        return {
            "id": 100001,
            "name": "Test Fighter",
            "level": 5,
            "stats": [
                {"id": 1, "value": 16},  # Strength
                {"id": 2, "value": 14},  # Dexterity
                {"id": 3, "value": 15},  # Constitution
                {"id": 4, "value": 10},  # Intelligence
                {"id": 5, "value": 12},  # Wisdom
                {"id": 6, "value": 8}    # Charisma
            ],
            "classes": [
                {
                    "level": 5,
                    "definition": {
                        "name": "Fighter",
                        "hitDie": 10
                    },
                    "subclassDefinition": {
                        "name": "Champion"
                    }
                }
            ],
            "race": {
                "definition": {
                    "name": "Human"
                },
                "subRaceDefinition": {
                    "name": "Variant"
                }
            },
            "background": {
                "definition": {
                    "name": "Soldier"
                }
            },
            "baseHitPoints": 47,
            "modifiers": {
                "race": [],
                "class": [
                    {
                        "subType": "proficiency",
                        "type": "proficiency",
                        "friendlyTypeName": "Skill",
                        "friendlySubtypeName": "Athletics"
                    }
                ],
                "background": [],
                "item": [],
                "feat": []
            },
            "spells": {
                "race": [],
                "class": [],
                "feat": [],
                "item": []
            },
            "classSpells": []
        }
    
    @staticmethod
    def get_wizard_spellcaster_raw() -> Dict[str, Any]:
        """Get raw D&D Beyond data for wizard spellcaster."""
        return {
            "id": 100002,
            "name": "Test Wizard",
            "level": 5,
            "stats": [
                {"id": 1, "value": 8},   # Strength
                {"id": 2, "value": 14},  # Dexterity
                {"id": 3, "value": 13},  # Constitution
                {"id": 4, "value": 16},  # Intelligence
                {"id": 5, "value": 12},  # Wisdom
                {"id": 6, "value": 10}   # Charisma
            ],
            "classes": [
                {
                    "level": 5,
                    "definition": {
                        "name": "Wizard",
                        "hitDie": 6,
                        "spellcastingAbilityId": 4  # Intelligence
                    },
                    "subclassDefinition": {
                        "name": "School of Evocation"
                    }
                }
            ],
            "race": {
                "definition": {
                    "name": "Elf"
                },
                "subRaceDefinition": {
                    "name": "High Elf"
                }
            },
            "background": {
                "definition": {
                    "name": "Sage"
                }
            },
            "baseHitPoints": 32,
            "spells": {
                "race": [
                    {
                        "definition": {
                            "id": 1,
                            "name": "Fire Bolt",
                            "level": 0,
                            "school": {"name": "Evocation"}
                        }
                    },
                    {
                        "definition": {
                            "id": 2,
                            "name": "Detect Magic",
                            "level": 1,
                            "school": {"name": "Divination"}
                        }
                    }
                ],
                "class": [],
                "feat": [],
                "item": []
            },
            "classSpells": [
                {
                    "characterClassId": 1,
                    "spells": [
                        {
                            "definition": {
                                "id": 3,
                                "name": "Mage Hand",
                                "level": 0,
                                "school": {"name": "Transmutation"}
                            }
                        },
                        {
                            "definition": {
                                "id": 4,
                                "name": "Magic Missile",
                                "level": 1,
                                "school": {"name": "Evocation"}
                            }
                        },
                        {
                            "definition": {
                                "id": 5,
                                "name": "Fireball",
                                "level": 3,
                                "school": {"name": "Evocation"}
                            }
                        }
                    ]
                }
            ]
        }


class ValidationFixtures:
    """Fixtures for validation testing."""
    
    EXPECTED_SPELL_COUNTS = {
        "BASIC_FIGHTER": 0,
        "WIZARD_SPELLCASTER": 9,
        "MULTICLASS_FIGHTER_WIZARD": 7,
        "ROGUE_WITH_EXPERTISE": 4,
        "EDGE_CASE_CHARACTER": 0
    }
    
    EXPECTED_SKILL_COUNTS = {
        "BASIC_FIGHTER": 2,
        "WIZARD_SPELLCASTER": 3,
        "MULTICLASS_FIGHTER_WIZARD": 3,
        "ROGUE_WITH_EXPERTISE": 6,
        "EDGE_CASE_CHARACTER": 2
    }
    
    EXPECTED_AC_VALUES = {
        "BASIC_FIGHTER": 18,
        "WIZARD_SPELLCASTER": 12,
        "MULTICLASS_FIGHTER_WIZARD": 18,
        "ROGUE_WITH_EXPERTISE": 15,
        "EDGE_CASE_CHARACTER": 24
    }


def get_character_fixture(name: str) -> Dict[str, Any]:
    """Get a character fixture by name."""
    fixtures = {
        "BASIC_FIGHTER": CharacterFixtures.BASIC_FIGHTER,
        "WIZARD_SPELLCASTER": CharacterFixtures.WIZARD_SPELLCASTER,
        "MULTICLASS_FIGHTER_WIZARD": CharacterFixtures.MULTICLASS_FIGHTER_WIZARD,
        "ROGUE_WITH_EXPERTISE": CharacterFixtures.ROGUE_WITH_EXPERTISE,
        "EDGE_CASE_CHARACTER": CharacterFixtures.EDGE_CASE_CHARACTER
    }
    
    if name not in fixtures:
        raise ValueError(f"Unknown fixture: {name}. Available: {list(fixtures.keys())}")
    
    return fixtures[name]


def get_raw_data_fixture(name: str) -> Dict[str, Any]:
    """Get a raw data fixture by name."""
    fixtures = {
        "BASIC_FIGHTER": RawDataFixtures.get_basic_fighter_raw,
        "WIZARD_SPELLCASTER": RawDataFixtures.get_wizard_spellcaster_raw
    }
    
    if name not in fixtures:
        raise ValueError(f"Unknown raw data fixture: {name}. Available: {list(fixtures.keys())}")
    
    return fixtures[name]()


def get_all_character_fixtures() -> List[Dict[str, Any]]:
    """Get all character fixtures for comprehensive testing."""
    return [
        CharacterFixtures.BASIC_FIGHTER,
        CharacterFixtures.WIZARD_SPELLCASTER,
        CharacterFixtures.MULTICLASS_FIGHTER_WIZARD,
        CharacterFixtures.ROGUE_WITH_EXPERTISE,
        CharacterFixtures.EDGE_CASE_CHARACTER
    ]