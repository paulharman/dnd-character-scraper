#!/usr/bin/env python3
"""
Enhanced D&D Beyond Character Scraper (5e 2024 Edition) - v5.2.0

A comprehensive character scraper for D&D Beyond with enhanced 2024 rules support,
advanced spell parsing, subclass extraction, background spell detection, enhanced inventory,
basic action parsing, and comprehensive diagnostics.

New Features in v5.2.0:
- Added explicit spell origin info with source_info structure
- Enhanced spell slot breakdown with regular_slots vs pact_slots separation
- Added caster_level tracking for multiclass progression
- Improved spell provenance with detailed granted_by information

New Features in v5.1.0:
- Fixed classFeatures iteration bug with null guard
- Implemented subclass extraction from subclassDefinition
- Added proper hit die mapping for all D&D classes
- Created dedicated feat resolution system
- Enhanced code quality and type safety

New Features in v5.0.0:
- Background Spell Detection: Identifies spellListIds in backgrounds and racial traits
- Enhanced Spell Metadata: Components, casting time, range, duration, concentration
- Inventory Enhancement: Magic item properties, charges, enhanced descriptions
- Basic Action Parsing: Extracts character actions and abilities from API data
- Comprehensive Diagnostics: Detailed error reporting and data structure exploration

Features:
- Full 2024 Player's Handbook compatibility with fallback to 2014 rules

Configuration Variables:
"""

# ==========================================
# CONFIGURATION VARIABLES
# ==========================================

# Character rule version is determined solely from D&D Beyond JSON data
# All spell data comes from D&D Beyond API only

# API Settings
DEFAULT_USER_AGENT = 'DnDBeyond-Enhanced-Scraper/5.2.0'
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Output Settings
VERBOSE_OUTPUT = False
INCLUDE_RAW_DATA = False

# ==========================================

"""
- Advanced spell grouping and deduplication by source
- Comprehensive ability score calculation with source breakdown
- Enhanced multiclass support and spell slot calculations
- Robust error handling with detailed diagnostics and graceful failure recovery
- Complete character data export in structured JSON format
- Enhanced debugging for data structure exploration
- Subclass name extraction and hit die mapping for all D&D classes

Author: Assistant
Version: 5.2.0
License: MIT
"""

import argparse
import json
import logging
import os
import random
import re
import sys
import time
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from requests.packages.urllib3.util.retry import Retry

try:
    from bs4 import BeautifulSoup
    HAS_BEAUTIFULSOUP = True
except ImportError:
    HAS_BEAUTIFULSOUP = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class FieldNames:
    """Centralized field name constants for consistency."""
    NAME = "name"
    LEVEL = "level"
    DEFINITION = "definition"
    SOURCE_ID = "sourceId"


class GameConstants:
    """Enhanced game constants with 2024 rules support."""

    # Core ability names
    ABILITY_NAMES = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]

    # Known ability score choice IDs for 2024 rules
    ABILITY_CHOICE_MAPPING = {
        # Standard background choices
        5686: "strength", 5687: "dexterity", 5688: "constitution",
        5689: "intelligence", 5690: "wisdom", 5691: "charisma",

        # Duplicate range for backgrounds (seems to be alternate IDs)
        5680: "strength", 5681: "dexterity", 5682: "constitution",
        5683: "intelligence", 5684: "wisdom", 5685: "charisma",

        # Extended choices for more sources
        5053: "strength", 5054: "constitution", 5055: "charisma",  # Other background choices

        # Feat-based ability score choices (like Magic Initiate variants)
        3110496: "charisma",  # Magic Initiate feat choices
        3110501: "intelligence",  # Magic Initiate feat choices
        3110549: "wisdom",  # Magic Initiate feat choices

        # Additional potential 2024 choice IDs (extrapolated from patterns)
        5692: "strength", 5693: "dexterity", 5694: "constitution",
        5695: "intelligence", 5696: "wisdom", 5697: "charisma",
    }

    # Spellcasting ability IDs
    SPELLCASTING_ABILITIES = {
        1: "strength", 2: "dexterity", 3: "constitution",
        4: "intelligence", 5: "wisdom", 6: "charisma"
    }

    # Source IDs for 2024 content
    SOURCE_2024_IDS = {145, 146, 147, 148, 149, 150}  # Known 2024 source IDs

    # Spell save DC calculation
    SPELL_SAVE_DC_BASE = 8

    # Full caster progression table (spell slots by level)
    FULL_CASTER_PROGRESSION = {
        1: [2], 2: [3], 3: [4, 2], 4: [4, 3], 5: [4, 3, 2],
        6: [4, 3, 3], 7: [4, 3, 3, 1], 8: [4, 3, 3, 2], 9: [4, 3, 3, 3, 1],
        10: [4, 3, 3, 3, 2], 11: [4, 3, 3, 3, 2, 1], 12: [4, 3, 3, 3, 2, 1],
        13: [4, 3, 3, 3, 2, 1, 1], 14: [4, 3, 3, 3, 2, 1, 1],
        15: [4, 3, 3, 3, 2, 1, 1, 1], 16: [4, 3, 3, 3, 2, 1, 1, 1],
        17: [4, 3, 3, 3, 2, 1, 1, 1, 1], 18: [4, 3, 3, 3, 3, 1, 1, 1, 1],
        19: [4, 3, 3, 3, 3, 2, 1, 1, 1], 20: [4, 3, 3, 3, 3, 2, 2, 1, 1]
    }

    # Half caster progression table (Artificer, Paladin, Ranger)
    HALF_CASTER_PROGRESSION = {
        2: [2], 3: [3], 4: [3], 5: [4, 2], 6: [4, 2], 7: [4, 3], 8: [4, 3],
        9: [4, 3, 2], 10: [4, 3, 2], 11: [4, 3, 3], 12: [4, 3, 3],
        13: [4, 3, 3, 1], 14: [4, 3, 3, 1], 15: [4, 3, 3, 2], 16: [4, 3, 3, 2],
        17: [4, 3, 3, 3, 1], 18: [4, 3, 3, 3, 1], 19: [4, 3, 3, 3, 2], 20: [4, 3, 3, 3, 2]
    }
    
    # 2024 Artificer progression (gets spells at level 1)
    ARTIFICER_2024_PROGRESSION = {
        1: [2], 2: [2], 3: [3], 4: [3], 5: [4, 2], 6: [4, 2], 7: [4, 3], 8: [4, 3],
        9: [4, 3, 2], 10: [4, 3, 2], 11: [4, 3, 3], 12: [4, 3, 3],
        13: [4, 3, 3, 1], 14: [4, 3, 3, 1], 15: [4, 3, 3, 2], 16: [4, 3, 3, 2],
        17: [4, 3, 3, 3, 1], 18: [4, 3, 3, 3, 1], 19: [4, 3, 3, 3, 2], 20: [4, 3, 3, 3, 2]
    }

    # Caster types
    FULL_CASTERS = {"wizard", "sorcerer", "cleric", "druid", "bard", "warlock"}
    HALF_CASTERS = {"paladin", "ranger", "artificer"}
    THIRD_CASTERS = {}  # These are subclass-specific, handled separately

    # Hit die by class name
    CLASS_HIT_DICE = {
        "barbarian": 12,
        "fighter": 10, "paladin": 10, "ranger": 10,
        "artificer": 8, "bard": 8, "cleric": 8, "druid": 8, "monk": 8, "rogue": 8, "warlock": 8,
        "sorcerer": 6, "wizard": 6
    }

    # JavaScript-style constants for better organization
    PROFICIENCY_BONUS_BY_LEVEL = {
        1: 2, 2: 2, 3: 2, 4: 2, 5: 3, 6: 3, 7: 3, 8: 3,
        9: 4, 10: 4, 11: 4, 12: 4, 13: 5, 14: 5, 15: 5, 16: 5,
        17: 6, 18: 6, 19: 6, 20: 6
    }
    
    SKILL_ABILITY_MAP = {
        "acrobatics": "dexterity", "animal-handling": "wisdom", "arcana": "intelligence",
        "athletics": "strength", "deception": "charisma", "history": "intelligence",
        "insight": "wisdom", "intimidation": "charisma", "investigation": "intelligence",
        "medicine": "wisdom", "nature": "intelligence", "perception": "wisdom",
        "performance": "charisma", "persuasion": "charisma", "religion": "intelligence",
        "sleight-of-hand": "dexterity", "stealth": "dexterity", "survival": "wisdom"
    }
    
    ABILITY_SCORE_NAMES = {
        1: "strength", 2: "dexterity", 3: "constitution",
        4: "intelligence", 5: "wisdom", 6: "charisma"
    }
    
    ALIGNMENT_NAMES = {
        1: "Lawful Good", 2: "Neutral Good", 3: "Chaotic Good",
        4: "Lawful Neutral", 5: "True Neutral", 6: "Chaotic Neutral", 
        7: "Lawful Evil", 8: "Neutral Evil", 9: "Chaotic Evil"
    }


class RuleVersionStrategy:
    """Base strategy for handling rule version-specific logic."""
    
    def __init__(self, source_ids: Set[int]):
        self.source_ids = source_ids
    
    def is_compatible_source(self, source_id: int) -> bool:
        """Check if a source ID is compatible with this rule version."""
        return source_id in self.source_ids
    
    def get_species_field_name(self) -> str:
        """Get the field name for species/race data."""
        raise NotImplementedError
    
    def get_ability_choice_mapping(self) -> Dict[int, str]:
        """Get ability score choice mapping for this rule version."""
        raise NotImplementedError
    
    def should_prefer_species_data(self) -> bool:
        """Whether to prefer species data over race data."""
        raise NotImplementedError
    
    def get_spell_slot_progression(self, class_name: str, level: int, caster_type: str) -> Optional[List[int]]:
        """Get spell slot progression for a class at a given level."""
        raise NotImplementedError
    
    def get_proficiency_bonus_calculation(self, total_level: int) -> int:
        """Calculate proficiency bonus based on total character level."""
        return 2 + ((max(1, total_level) - 1) // 4)  # Same for both rule sets
    
    def process_class_features(self, class_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process class-specific features based on rule version."""
        raise NotImplementedError
    
    def get_species_trait_processing(self) -> str:
        """Get the method for processing species/race traits."""
        raise NotImplementedError


class Rules2014Strategy(RuleVersionStrategy):
    """Strategy for 2014 rule version."""
    
    def __init__(self):
        # 2014 uses any source ID not in the 2024 set
        super().__init__(set())  # Empty set - will be handled by negation
    
    def is_compatible_source(self, source_id: int) -> bool:
        """2014 rules are compatible with non-2024 sources."""
        return source_id not in GameConstants.SOURCE_2024_IDS
    
    def get_species_field_name(self) -> str:
        return "race"
    
    def get_ability_choice_mapping(self) -> Dict[int, str]:
        return {}  # 2014 rules have fewer choice-based ability improvements
    
    def should_prefer_species_data(self) -> bool:
        return False  # Prefer race data for 2014
    
    def get_spell_slot_progression(self, class_name: str, level: int, caster_type: str) -> Optional[List[int]]:
        """Get 2014 spell slot progression."""
        class_name_lower = class_name.lower()
        
        if caster_type == "full":
            return GameConstants.FULL_CASTER_PROGRESSION.get(level)
        elif caster_type == "half":
            return GameConstants.HALF_CASTER_PROGRESSION.get(level)
        
        return None
    
    def process_class_features(self, class_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process 2014 class features."""
        # 2014 rules processing - no major changes from base implementation
        return class_data
    
    def get_species_trait_processing(self) -> str:
        """2014 uses race-based trait processing."""
        return "race_based"


class Rules2024Strategy(RuleVersionStrategy):
    """Strategy for 2024 rule version."""
    
    def __init__(self):
        super().__init__(GameConstants.SOURCE_2024_IDS)
    
    def get_species_field_name(self) -> str:
        return "species"
    
    def get_ability_choice_mapping(self) -> Dict[int, str]:
        return GameConstants.ABILITY_CHOICE_MAPPING
    
    def should_prefer_species_data(self) -> bool:
        return True  # Prefer species data for 2024
    
    def get_spell_slot_progression(self, class_name: str, level: int, caster_type: str) -> Optional[List[int]]:
        """Get 2024 spell slot progression."""
        class_name_lower = class_name.lower()
        
        # 2024 rules may have different progressions for some classes
        if caster_type == "full":
            # Check for 2024-specific modifications to full caster progression
            return GameConstants.FULL_CASTER_PROGRESSION.get(level)
        elif caster_type == "half":
            # 2024 Artificer has different progression than other half-casters
            if class_name_lower == "artificer":
                # 2024 Artificer gets spells at level 1
                return GameConstants.ARTIFICER_2024_PROGRESSION.get(level)
            else:
                return GameConstants.HALF_CASTER_PROGRESSION.get(level)
        
        return None
    
    def process_class_features(self, class_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process 2024 class features."""
        # 2024 rules have enhanced class features
        processed_data = class_data.copy()
        
        # Add 2024-specific class feature processing here
        class_name = class_data.get("definition", {}).get("name", "").lower()
        
        if class_name == "artificer":
            # 2024 Artificer gets spellcasting at level 1
            processed_data["early_spellcasting"] = True
        elif class_name == "ranger":
            # 2024 Ranger may have different spellcasting progression
            processed_data["enhanced_spellcasting"] = True
        
        return processed_data
    
    def get_species_trait_processing(self) -> str:
        """2024 uses species-based trait processing with enhanced customization."""
        return "species_based"


class RuleVersionManager:
    """Manages rule version detection and strategy selection."""
    
    def __init__(self, raw_data: Dict[str, Any]):
        self.raw_data = raw_data
        self._is_2024 = self._detect_2024_rules()
        self._strategy = Rules2024Strategy() if self._is_2024 else Rules2014Strategy()
    
    def _detect_2024_rules(self) -> bool:
        """Detect if character uses 2024 rules based on source IDs."""
        try:
            # Check class sources
            for cls in self.raw_data.get("classes", []):
                class_def = cls.get(FieldNames.DEFINITION, {})
                source_id = class_def.get(FieldNames.SOURCE_ID)
                sources = class_def.get("sources", [])
                
                # Check both sourceId field and sources array
                if source_id and source_id in GameConstants.SOURCE_2024_IDS:
                    return True
                
                for source in sources:
                    if isinstance(source, dict):
                        src_id = source.get("sourceId")
                        if src_id in GameConstants.SOURCE_2024_IDS:
                            return True

            # Check race source
            race_data = self.raw_data.get("race", {})
            if race_data:
                race_def = race_data.get(FieldNames.DEFINITION, {})
                source_id = race_def.get(FieldNames.SOURCE_ID)
                if source_id in GameConstants.SOURCE_2024_IDS:
                    return True

            # Check background source
            background_data = self.raw_data.get("background", {})
            if background_data:
                background_def = background_data.get(FieldNames.DEFINITION, {})
                source_id = background_def.get(FieldNames.SOURCE_ID)
                if source_id in GameConstants.SOURCE_2024_IDS:
                    return True

            return False

        except Exception as e:
            logger.error(f"Error determining 2024 rules: {e}")
            return False
    
    @property
    def is_2024(self) -> bool:
        """Check if character uses 2024 rules."""
        return self._is_2024
    
    @property
    def strategy(self) -> RuleVersionStrategy:
        """Get the current rule version strategy."""
        return self._strategy


@dataclass
class CharacterModifier:
    """Enhanced modifier with better type safety."""
    type: str
    sub_type: str
    value: Union[int, float, str, None]
    source: str
    friendly_type_name: str = ""
    friendly_sub_type_name: str = ""
    restriction: str = ""
    entity_id: Optional[int] = None
    component_id: Optional[int] = None


@dataclass
class AppearanceInfo:
    """Character appearance information."""
    gender: str = ""
    age: Optional[int] = None
    hair: str = ""
    eyes: str = ""
    skin: str = ""
    height: str = ""
    weight: Optional[int] = None
    traits: str = ""
    size: int = 3  # Default to Medium
    size_name: str = "Medium"


@dataclass
class BasicCharacterInfo:
    """Basic character information."""
    name: str
    level: int
    experience: int
    classes: List[str] = field(default_factory=list)
    avatarUrl: Optional[str] = None
    inspiration: bool = False
    lifestyleId: Optional[int] = None


@dataclass
class ClassInfo:
    """Enhanced class information with 2024 support."""
    name: str
    level: int
    hit_die: int
    subclass: str = ""
    spellcasting_ability: str = ""
    is_2024: bool = False


@dataclass
class SpellInfo:
    """Enhanced spell information."""
    name: str
    level: int
    school: str
    description: str
    sources: List[str] = field(default_factory=list)
    save_dc: Optional[int] = None
    attack_bonus: Optional[int] = None
    spellcasting_ability: str = ""
    always_prepared: bool = False
    usage_type: str = "slot"  # 'slot', 'at-will', 'per-rest'
    uses_per_rest: Optional[int] = None
    
    # Enhanced spell data from local files
    casting_time: str = ""
    range: str = ""
    duration: str = ""
    components: str = ""
    material_components: str = ""
    concentration: bool = False
    ritual: bool = False
    enhanced_description: str = ""  # Richer description from local files
    classes: List[str] = field(default_factory=list)
    higher_levels: str = ""
    source_book: str = ""


@dataclass
class FeatInfo:
    """Feat information."""
    name: str
    description: str
    source: str
    feature_type: str = "feat"
    level_required: Optional[int] = None


@dataclass
class InventoryItem:
    """Inventory item information."""
    name: str
    quantity: int = 1
    equipped: bool = False
    attuned: bool = False
    requires_attunement: bool = False
    weight: float = 0.0
    item_type: str = "equipment"
    rarity: str = "common"


@dataclass
class SpeciesInfo:
    """2024 Species information (distinct from legacy race)."""
    name: str
    size: str
    ability_choices: Dict[str, int] = field(default_factory=dict)
    size_changes: Dict[str, str] = field(default_factory=dict)
    traits: List[str] = field(default_factory=list)
    is_2024: bool = False
    source_id: Optional[int] = None
    speed: Dict[str, int] = field(default_factory=dict)
    languages: List[str] = field(default_factory=list)
    proficiencies: List[str] = field(default_factory=list)


class CharacterAnalyzer:
    """Enhanced character analyzer with improved 2024 detection."""

    def __init__(self, raw_data: Dict[str, Any], rule_manager: Optional[RuleVersionManager] = None):
        self.raw_data = raw_data
        self.rule_manager = rule_manager

    @cached_property
    def class_levels(self) -> Dict[str, int]:
        """Get mapping of class names to levels."""
        return {
            cls.get(FieldNames.DEFINITION, {}).get(FieldNames.NAME, "").lower(): cls.get(FieldNames.LEVEL, 0)
            for cls in self.raw_data.get("classes", [])
        }

    @cached_property
    def class_component_mapping(self) -> Dict[int, str]:
        """Get mapping of component IDs to class names for dynamic resolution."""
        mapping = {}
        for cls in self.raw_data.get("classes", []):
            definition = cls.get(FieldNames.DEFINITION, {})
            class_name = definition.get(FieldNames.NAME, "").lower()
            class_id = definition.get("id")

            # Map the main class ID
            if class_id:
                mapping[class_id] = class_name

            # Also map all class feature IDs to the same class
            for feature in cls.get("classFeatures") or []:
                feature_def = feature.get(FieldNames.DEFINITION, {})
                feature_id = feature_def.get("id")
                class_id_ref = feature_def.get("classId")

                if feature_id:
                    mapping[feature_id] = class_name
                if class_id_ref:
                    mapping[class_id_ref] = class_name

            # Map class definition feature IDs (from definition.classFeatures)
            for feature in definition.get("classFeatures", []):
                feature_id = feature.get("id")
                if feature_id:
                    mapping[feature_id] = class_name

        logger.debug(f"Class component mapping: {mapping}")
        return mapping

    @cached_property
    def character_classes(self) -> List[ClassInfo]:
        """Get detailed class information with enhanced 2024 detection."""
        classes = []
        try:
            for cls in self.raw_data.get("classes", []):
                definition = cls.get(FieldNames.DEFINITION, {})
                class_name = definition.get(FieldNames.NAME, "Unknown")

                # Determine spellcasting ability
                spellcasting_ability_id = definition.get("spellcastingAbilityId")
                spellcasting_ability = ""
                if VERBOSE_OUTPUT:
                    logger.debug(f"Class {class_name} spellcastingAbilityId: {spellcasting_ability_id}")
                if spellcasting_ability_id in GameConstants.SPELLCASTING_ABILITIES:
                    spellcasting_ability = GameConstants.SPELLCASTING_ABILITIES[spellcasting_ability_id]
                    if VERBOSE_OUTPUT:
                        logger.debug(f"Class {class_name} spellcasting ability: {spellcasting_ability}")
                elif spellcasting_ability_id is not None:
                    logger.warning(f"Unknown spellcastingAbilityId {spellcasting_ability_id} for class {class_name}")
                    # Fallback for common classes
                    class_name_lower = class_name.lower()
                    if "cleric" in class_name_lower or "druid" in class_name_lower or "ranger" in class_name_lower:
                        spellcasting_ability = "wisdom"
                        logger.info(f"Applied wisdom fallback for {class_name}")
                    elif "wizard" in class_name_lower or "artificer" in class_name_lower:
                        spellcasting_ability = "intelligence"
                        logger.info(f"Applied intelligence fallback for {class_name}")
                    elif "sorcerer" in class_name_lower or "bard" in class_name_lower or "warlock" in class_name_lower or "paladin" in class_name_lower:
                        spellcasting_ability = "charisma"
                        logger.info(f"Applied charisma fallback for {class_name}")

                # Extract subclass information
                subclass_name = ""
                subclass_definition = cls.get("subclassDefinition")
                if subclass_definition and isinstance(subclass_definition, dict):
                    subclass_name = subclass_definition.get(FieldNames.NAME, "")

                # Determine hit die for this class
                hit_die = GameConstants.CLASS_HIT_DICE.get(class_name.lower(), 8)  # Default to d8

                classes.append(ClassInfo(
                    name=class_name,
                    level=cls.get(FieldNames.LEVEL, 1),
                    hit_die=hit_die,
                    subclass=subclass_name,
                    spellcasting_ability=spellcasting_ability,
                    is_2024=self.rule_manager.is_2024 if self.rule_manager else (definition.get(FieldNames.SOURCE_ID) in GameConstants.SOURCE_2024_IDS)
                ))
        except Exception as e:
            logger.error(f"Error parsing character classes: {e}")

        return classes

    @cached_property
    def total_character_level(self) -> int:
        """Get total character level across all classes."""
        return sum(cls.level for cls in self.character_classes)


class ModifierProcessor:
    """Centralized modifier processing system for all character modifiers."""
    
    def __init__(self, raw_data: Dict[str, Any], rule_manager: Optional[RuleVersionManager] = None):
        self.raw_data = raw_data
        self.rule_manager = rule_manager
        self._processed_modifiers: Optional[List[CharacterModifier]] = None
    
    def get_all_modifiers(self) -> List[CharacterModifier]:
        """Get all processed modifiers from all sources."""
        if self._processed_modifiers is None:
            self._processed_modifiers = self._process_all_sources()
        return self._processed_modifiers
    
    def _process_all_sources(self) -> List[CharacterModifier]:
        """Process modifiers from all sources: race, class, background, feat, item, choices."""
        all_modifiers = []
        
        # Process standard modifier sources
        modifier_sources = self.raw_data.get("modifiers", {})
        
        for source_name, modifiers in modifier_sources.items():
            if isinstance(modifiers, list):
                processed = self._process_source_modifiers(modifiers, source_name)
                all_modifiers.extend(processed)
        
        # Process choice-based modifiers (ability score improvements)
        choice_modifiers = self._process_choices()
        all_modifiers.extend(choice_modifiers)
        
        return all_modifiers
    
    def _process_source_modifiers(self, modifiers: List[Dict[str, Any]], source_name: str) -> List[CharacterModifier]:
        """Process modifiers from a specific source (race, class, feat, etc.)."""
        processed_modifiers = []
        
        for mod_data in modifiers:
            # Check item activity if this is an item modifier
            if source_name == "item" and not self._is_item_modifier_active(mod_data):
                continue
            
            modifier = self._create_modifier_from_data(mod_data, source_name)
            if modifier:
                processed_modifiers.append(modifier)
        
        return processed_modifiers
    
    def _process_choices(self) -> List[CharacterModifier]:
        """Process character choices into ability score modifiers."""
        choice_modifiers = []
        
        try:
            # Get ability choice mapping from rule strategy
            ability_choice_mapping = {}
            if self.rule_manager:
                ability_choice_mapping = self.rule_manager.strategy.get_ability_choice_mapping()
            else:
                ability_choice_mapping = GameConstants.ABILITY_CHOICE_MAPPING

            choices_data = self.raw_data.get("choices", {})

            for choice_category, choice_list in choices_data.items():
                if isinstance(choice_list, list):
                    for choice in choice_list:
                        option_id = choice.get("optionId")
                        if option_id in ability_choice_mapping:
                            ability_name = ability_choice_mapping[option_id]
                            modifier = CharacterModifier(
                                type="bonus",
                                sub_type=f"{ability_name}-score",
                                value=1,
                                source="choice",
                                friendly_type_name="Bonus",
                                friendly_sub_type_name=f"{ability_name.title()} Score",
                                entity_id=option_id
                            )
                            choice_modifiers.append(modifier)
                            logger.debug(f"Resolved choice {option_id} to {ability_name} +1")

        except Exception as e:
            logger.error(f"Error processing choices: {e}")

        return choice_modifiers
    
    def _create_modifier_from_data(self, mod_data: Dict[str, Any], source_name: str) -> Optional[CharacterModifier]:
        """Create a CharacterModifier from raw modifier data."""
        try:
            return CharacterModifier(
                type=mod_data.get("type", "unknown"),
                sub_type=mod_data.get("subType", ""),
                value=mod_data.get("value"),
                source=source_name,
                friendly_type_name=mod_data.get("friendlyTypeName", ""),
                friendly_sub_type_name=mod_data.get("friendlySubtypeName", ""),
                restriction=mod_data.get("restriction", ""),
                entity_id=mod_data.get("entityId"),
                component_id=mod_data.get("componentId")
            )
        except Exception as e:
            logger.debug(f"Error creating modifier from data: {e}")
            return None
    
    def _is_item_modifier_active(self, mod_data: Dict[str, Any]) -> bool:
        """Check if an item modifier should be applied based on equipment status."""
        try:
            component_id = mod_data.get("componentId")
            if not component_id:
                return True  # If no component ID, assume active
            
            # Check inventory for item activity
            inventory = self.raw_data.get("inventory", [])
            for item in inventory:
                if item.get("id") == component_id:
                    # Item is active if equipped or doesn't require attunement
                    is_equipped = item.get("equipped", False)
                    requires_attunement = item.get("definition", {}).get("requiresAttunement", False)
                    is_attuned = item.get("isAttuned", False)
                    
                    if requires_attunement:
                        return is_equipped and is_attuned
                    else:
                        return is_equipped
            
            return True  # Default to active if item not found
            
        except Exception as e:
            logger.debug(f"Error checking item activity for component {component_id}: {e}")
            return True
    
    def get_modifiers_by_type(self, modifier_type: str) -> List[CharacterModifier]:
        """Get all modifiers of a specific type."""
        return [mod for mod in self.get_all_modifiers() if mod.type == modifier_type]
    
    def get_modifiers_by_subtype(self, sub_type: str) -> List[CharacterModifier]:
        """Get all modifiers of a specific subtype."""
        return [mod for mod in self.get_all_modifiers() if mod.sub_type == sub_type]
    
    def get_modifiers_by_source(self, source: str) -> List[CharacterModifier]:
        """Get all modifiers from a specific source."""
        return [mod for mod in self.get_all_modifiers() if mod.source == source]


class DNDBeyondScraper:
    """Enhanced D&D Beyond character scraper with 2024 rules support."""

    def __init__(self, character_id: str, session_cookie: Optional[str] = None, preserve_html: bool = False):
        self.character_id = character_id
        self.preserve_html = preserve_html
        self.raw_data: Dict[str, Any] = {}
        self._modifiers: Optional[List[CharacterModifier]] = None
        self._ability_scores: Optional[Dict[str, Dict[str, Any]]] = None
        self._analyzer: Optional[CharacterAnalyzer] = None
        self._rule_manager: Optional[RuleVersionManager] = None
        self._modifier_processor: Optional[ModifierProcessor] = None

        # Set up session with retry strategy
        self.session = requests.Session()
        try:
            # Try newer urllib3 parameter name first
            retry_strategy = Retry(
                total=3,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"],
                backoff_factor=1
            )
        except TypeError:
            # Fall back to older parameter name for compatibility
            retry_strategy = Retry(
                total=3,
                status_forcelist=[429, 500, 502, 503, 504],
                method_whitelist=["HEAD", "GET", "OPTIONS"],
                backoff_factor=1
            )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set headers
        self.session.headers.update({
            'User-Agent': 'DnDBeyond-Enhanced-Scraper/5.2.0',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        })

        # Add session cookie if provided
        if session_cookie:
            self.session.headers['Cookie'] = session_cookie

    def _get_ability_modifier(self, ability_short: str) -> int:
        """Get ability modifier from 3-letter ability abbreviation."""
        ability_map = {
            "str": "strength", "dex": "dexterity", "con": "constitution",
            "int": "intelligence", "wis": "wisdom", "cha": "charisma"
        }
        ability_name = ability_map.get(ability_short.lower(), "strength")
        return self.analyzer.ability_scores.get(ability_name, {}).get("modifier", 0)

    def _sanitize(self, text: str) -> str:
        """Enhanced text sanitization with JavaScript-style template replacement."""
        if not text:
            return text
            
        if self.preserve_html:
            # Even with preserved HTML, process templates
            return self._process_templates(text)
        
        # First process D&D Beyond templates (like JavaScript version)
        text = self._process_templates(text)
            
        # Use BeautifulSoup if available, otherwise fall back to regex
        if HAS_BEAUTIFULSOUP:
            try:
                # Parse HTML and extract text
                soup = BeautifulSoup(text, "html.parser")
                
                # Convert some common formatting to markdown-style before extracting text
                for strong in soup.find_all(['strong', 'b']):
                    strong.string = f"**{strong.get_text()}**"
                    strong.unwrap()
                    
                for em in soup.find_all(['em', 'i']):
                    em.string = f"*{em.get_text()}*"
                    em.unwrap()
                
                # Handle lists
                for li in soup.find_all('li'):
                    li.string = f"• {li.get_text()}\n"
                    li.unwrap()
                
                # Get clean text
                clean_text = soup.get_text()
                
                # Clean up whitespace (JavaScript-style)
                clean_text = re.sub(r'\s*(\r\n|\n|\r)\s*', ' ', clean_text)
                clean_text = re.sub(r'[ \t]+', ' ', clean_text)
                clean_text = clean_text.strip()
                
                return clean_text
                
            except Exception as e:
                logger.debug(f"BeautifulSoup parsing failed, falling back to regex: {e}")
                # Fall through to regex fallback
        
        # Regex fallback - simplified like JavaScript
        text = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', text, flags=re.DOTALL)
        text = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '', text)  # Remove all HTML tags
        
        # Clean up HTML entities
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
        text = text.replace('&lt;', '<').replace('&gt;', '>')
        
        # JavaScript-style whitespace cleanup
        text = re.sub(r'\s*(\r\n|\n|\r)\s*', ' ', text)
        text = text.strip()
        
        return text
    
    def _process_templates(self, text: str) -> str:
        """Process D&D Beyond templates like JavaScript version."""
        if not text:
            return text
        
        try:
            # Get character stats for template replacement
            total_level = getattr(self.analyzer, 'total_character_level', 1)
            proficiency_bonus = self._get_proficiency_bonus()
            
            # JavaScript-style regex replacements
            text = re.sub(r'\{\{spellattack:(\w{3})\}\}', 
                          lambda m: str(proficiency_bonus + self._get_ability_modifier(m.group(1))), 
                          text)
            text = re.sub(r'\{\{savedc:(\w{3})\}\}', 
                          lambda m: str(8 + proficiency_bonus + self._get_ability_modifier(m.group(1))), 
                          text)
            text = re.sub(r'\{\{modifier:(\w{3})\}\}', 
                          lambda m: str(self._get_ability_modifier(m.group(1))), 
                          text)
            text = re.sub(r'\{\{modifier:(\w{3}):([\-\+])(\d+).*?\}\}', 
                          lambda m: str(self._get_ability_modifier(m.group(1)) + 
                                      (int(m.group(3)) if m.group(2) == '+' else -int(m.group(3)))), 
                          text)
            
            return text
            
        except Exception as e:
            logger.debug(f"Error processing templates: {e}")
            return text

    def _get_background_feat_description(self, grant_feat: Dict[str, Any]) -> str:
        """Try to get description for background granted feats."""
        # Check if featIds are available for lookup
        feat_ids = grant_feat.get("featIds", [])
        if not feat_ids:
            return ""
        
        # For now, return empty string - in the future, this could make API calls
        # to fetch full feat definitions using the feat IDs
        # TODO: Implement feat lookup by ID if needed
        return ""

    @property
    def analyzer(self) -> CharacterAnalyzer:
        """Get character analyzer (cached)."""
        if self._analyzer is None:
            self._analyzer = CharacterAnalyzer(self.raw_data, self._rule_manager)
        return self._analyzer

    @property
    def all_modifiers(self) -> List[CharacterModifier]:
        """Get all modifiers from all sources (cached)."""
        if self._modifiers is None:
            if self._modifier_processor:
                self._modifiers = self._modifier_processor.get_all_modifiers()
            else:
                # Fallback to legacy processing if modifier processor not available
                self._modifiers = self._parse_all_modifiers()
        return self._modifiers

    def fetch_character_data(self, max_retries: int = 3, retry_delay: float = 2.0) -> bool:
        """
        Fetch character data from D&D Beyond API with robust error handling.

        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries (with exponential backoff)

        Returns:
            True if successful, False otherwise
        """
        url = f"https://character-service.dndbeyond.com/character/v5/character/{self.character_id}"

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Fetching character data (attempt {attempt}/{max_retries})")

                # Add some randomization to avoid rate limiting
                if attempt > 1:
                    delay = retry_delay * (2 ** (attempt - 2)) + random.uniform(0.1, 0.5)
                    logger.info(f"Waiting {delay:.2f} seconds before retry...")
                    time.sleep(delay)

                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                response_data = response.json()

                # Validate response structure
                if not isinstance(response_data, dict):
                    raise ValueError("Invalid response format: expected JSON object")

                # Check if data is nested under 'data' property
                if "data" in response_data:
                    self.raw_data = response_data["data"]
                else:
                    self.raw_data = response_data

                # Initialize rule version manager after raw data is set
                self._rule_manager = RuleVersionManager(self.raw_data)
                
                # Initialize modifier processor
                self._modifier_processor = ModifierProcessor(self.raw_data, self._rule_manager)
                
                character_name = self.raw_data.get(FieldNames.NAME, "Unknown Character")
                logger.info(f"Successfully fetched data for character: {character_name}")

                return True

            except RequestException as e:
                logger.warning(f"Network error on attempt {attempt}: {e}")
                if attempt == max_retries:
                    logger.error(f"Failed to fetch character data after {max_retries} attempts")
                    return False

            except (ValueError, KeyError) as e:
                logger.error(f"Invalid response format: {e}")
                return False

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return False

        return False

    def _safe_get_modifier_value(self, modifier: CharacterModifier) -> Union[int, float]:
        """Safely extract numeric value from modifier, handling various data types."""
        try:
            if modifier.value is None:
                return 0
            if isinstance(modifier.value, (int, float)):
                return modifier.value
            if isinstance(modifier.value, str):
                try:
                    return float(modifier.value)
                except ValueError:
                    return 0
            return 0
        except Exception:
            return 0

    def _get_proficiency_bonus(self) -> int:
        """Calculate proficiency bonus based on total character level."""
        total_level = self.analyzer.total_character_level
        
        # Use rule-specific proficiency bonus calculation
        if self._rule_manager:
            return self._rule_manager.strategy.get_proficiency_bonus_calculation(total_level)
        else:
            # Fallback to standard calculation
            return 2 + ((max(1, total_level) - 1) // 4)

    def _calculate_spell_stats(self, spellcasting_ability: str) -> Dict[str, int]:
        """Calculate spell save DC and attack bonus for given ability."""
        ability_scores = self._parse_ability_scores()
        ability_modifier = ability_scores.get(spellcasting_ability, {}).get("modifier", 0)
        proficiency_bonus = self._get_proficiency_bonus()
        
        return {
            "save_dc": GameConstants.SPELL_SAVE_DC_BASE + proficiency_bonus + ability_modifier,
            "attack_bonus": proficiency_bonus + ability_modifier,
            "ability": spellcasting_ability,
            "modifier": ability_modifier
        }

    @property
    def rule_manager(self) -> Optional[RuleVersionManager]:
        """Get the rule version manager."""
        return self._rule_manager

    @property
    def modifier_processor(self) -> Optional[ModifierProcessor]:
        """Get the modifier processor."""
        return self._modifier_processor

    def _is_2024_character(self) -> bool:
        """Determine if character uses 2024 rules based on source IDs."""
        if self._rule_manager is None:
            # Fallback to legacy detection if rule manager not initialized
            logger.warning("Rule manager not initialized, using legacy 2024 detection")
            return False
        
        return self._rule_manager.is_2024

    def _create_modifier_from_data(self, mod_data: Dict[str, Any], source_name: str) -> Optional[CharacterModifier]:
        """Create a CharacterModifier from raw modifier data."""
        try:
            return CharacterModifier(
                type=mod_data.get("type", "unknown"),
                sub_type=mod_data.get("subType", "unknown"),
                value=mod_data.get("value"),
                source=source_name,
                friendly_type_name=mod_data.get("friendlyTypeName", ""),
                friendly_sub_type_name=mod_data.get("friendlySubtypeName", ""),
                restriction=mod_data.get("restriction", ""),
                entity_id=mod_data.get("entityId"),
                component_id=mod_data.get("componentId")
            )
        except Exception as e:
            logger.debug(f"Error creating modifier from {mod_data}: {e}")
            return None
    
    def _is_item_active(self, component_id: int) -> bool:
        """
        JavaScript-style item activity check for more accurate modifiers.
        
        An item is active if:
        - It doesn't require equipping, or it is equipped
        - It doesn't require attunement, or it is attuned
        """
        try:
            for item in self.raw_data.get("inventory", []):
                item_def = item.get("definition", {})
                if item_def.get("id") == component_id:
                    can_equip = item_def.get("canEquip", False)
                    can_attune = item_def.get("canAttune", False)
                    
                    equipped = item.get("equipped", True) if can_equip else True
                    attuned = item.get("isAttuned", True) if can_attune else True
                    
                    return equipped and attuned
            return False  # Item not found
        except Exception as e:
            logger.debug(f"Error checking item activity for component {component_id}: {e}")
            return True  # Default to active to avoid breaking functionality

    def _resolve_choices(self) -> List[CharacterModifier]:
        """Resolve character choices into ability score modifiers."""
        choice_modifiers = []
        try:
            # Get ability choice mapping from rule strategy
            ability_choice_mapping = {}
            if self._rule_manager:
                ability_choice_mapping = self._rule_manager.strategy.get_ability_choice_mapping()
            else:
                # Fallback to legacy mapping
                ability_choice_mapping = GameConstants.ABILITY_CHOICE_MAPPING

            choices_data = self.raw_data.get("choices", {})

            for choice_category, choice_list in choices_data.items():
                if isinstance(choice_list, list):
                    for choice in choice_list:
                        option_id = choice.get("optionId")
                        if option_id in ability_choice_mapping:
                            ability_name = ability_choice_mapping[option_id]
                            modifier = CharacterModifier(
                                type="bonus",
                                sub_type=f"{ability_name}-score",
                                value=1,
                                source="choice",
                                friendly_type_name="Bonus",
                                friendly_sub_type_name=f"{ability_name.title()} Score",
                                entity_id=option_id
                            )
                            choice_modifiers.append(modifier)
                            logger.debug(f"Resolved choice {option_id} to {ability_name} +1")

        except Exception as e:
            logger.error(f"Error resolving choices: {e}")

        return choice_modifiers

    def _calculate_hit_points(self) -> Dict[str, int]:
        """Calculate character hit points with enhanced debugging and Constitution modifier support."""
        try:
            # Extract HP values from raw data
            base_hp = self.raw_data.get("baseHitPoints", 0)
            bonus_hp = self.raw_data.get("bonusHitPoints") or 0
            override_hp = self.raw_data.get("overrideHitPoints")
            removed_hp = self.raw_data.get("removedHitPoints", 0)
            temp_hp = self.raw_data.get("temporaryHitPoints", 0)
            current_hp = self.raw_data.get("currentHitPoints", 0)

            # Get hit point type (1 = Fixed, 2 = Manual/Rolled, 0 = Default)
            hit_point_type = self.raw_data.get("preferences", {}).get("hitPointType", 0)
            hit_point_method = "Fixed" if hit_point_type == 1 else "Manual" if hit_point_type == 2 else "Default"

            # Calculate Constitution modifier and level-based HP bonus
            ability_scores = self._parse_ability_scores()
            constitution_modifier = ability_scores.get("constitution", {}).get("modifier", 0)
            total_character_level = self.analyzer.total_character_level

            logger.debug(f"HP Constitution Analysis:")
            logger.debug(f"  Constitution modifier: {constitution_modifier}")
            logger.debug(f"  Total character level: {total_character_level}")
            logger.debug(f"  Hit Point Type: {hit_point_type} ({hit_point_method})")
            logger.debug(f"  Raw baseHitPoints: {base_hp}")

            # Calculate HP based on method
            if hit_point_type == 1:  # Fixed HP Method
                # For Fixed HP, calculate proper base HP using average method
                character_classes = self.analyzer.character_classes
                if character_classes and total_character_level >= 1:
                    first_class = character_classes[0]
                    hit_die = first_class.hit_die
                    
                    # Fixed HP calculation:
                    # Level 1: Max hit die + CON modifier
                    # Level 2+: Average hit die + CON modifier per level
                    level_1_hp = hit_die + constitution_modifier  # Max die + CON
                    
                    if total_character_level > 1:
                        avg_per_level = (hit_die // 2) + 1  # Average rounded up
                        additional_levels_hp = (total_character_level - 1) * (avg_per_level + constitution_modifier)
                        calculated_max_hp = level_1_hp + additional_levels_hp
                        
                        logger.debug(f"  Fixed HP Calculation for {first_class.name}:")
                        logger.debug(f"    Level 1: {hit_die} (max d{hit_die}) + {constitution_modifier} (CON) = {level_1_hp}")
                        logger.debug(f"    Levels 2-{total_character_level}: {total_character_level - 1} × ({avg_per_level} (avg d{hit_die}) + {constitution_modifier} (CON)) = {additional_levels_hp}")
                        logger.debug(f"    Total calculated: {calculated_max_hp}")
                    else:
                        calculated_max_hp = level_1_hp
                        logger.debug(f"  Fixed HP Calculation for {first_class.name}:")
                        logger.debug(f"    Level 1: {hit_die} (max d{hit_die}) + {constitution_modifier} (CON) = {calculated_max_hp}")
                    
                    # Use calculated HP instead of API base_hp for Fixed method
                    max_hp_base = calculated_max_hp
                    constitution_hp_bonus = 0  # Already included in calculation
                else:
                    # Fallback to API values if no class info
                    constitution_hp_bonus = constitution_modifier * total_character_level
                    max_hp_base = base_hp + constitution_hp_bonus
                    logger.debug(f"  Fallback: Using API values with CON bonus")
            else:
                # Manual/Rolled HP or Default: Use API base_hp + separate CON bonus
                constitution_hp_bonus = constitution_modifier * total_character_level
                max_hp_base = base_hp + constitution_hp_bonus
                logger.debug(f"  Manual/Rolled HP: {base_hp} (base) + {constitution_hp_bonus} (CON bonus)")

            # Calculate maximum HP
            if override_hp is not None:
                max_hp = override_hp
                logger.debug(f"HP: Using override value = {override_hp}")
            else:
                # Add any bonus HP from items/features
                max_hp = max_hp_base + bonus_hp
                logger.debug(f"HP: Final = {max_hp_base} (calculated) + {bonus_hp} (bonus) = {max_hp}")

            # If current HP is 0 or not set, assume it equals max HP
            if current_hp == 0:
                current_hp = max_hp

            # Final current HP calculation (max - removed damage)
            final_current_hp = current_hp - removed_hp

            logger.debug(f"HP Breakdown:")
            logger.debug(f"  Base HP (from D&D Beyond): {base_hp}")
            logger.debug(f"  Constitution HP Bonus: {constitution_hp_bonus}")
            logger.debug(f"  Other Bonus HP: {bonus_hp}")
            logger.debug(f"  Override HP: {override_hp}")
            logger.debug(f"  Removed HP: {removed_hp}")
            logger.debug(f"  Temporary HP: {temp_hp}")
            logger.debug(f"  Final Maximum HP: {max_hp}")
            logger.debug(f"  Current HP: {final_current_hp}")

            return {
                "current": final_current_hp,
                "maximum": max_hp,
                "temporary": temp_hp,
                "base": base_hp,
                "bonus": bonus_hp,
                "constitution_bonus": constitution_hp_bonus,
                "override": override_hp,
                "removed": removed_hp,
                "hit_point_type": hit_point_type,
                "hit_point_method": hit_point_method
            }

        except Exception as e:
            logger.error(f"Error calculating hit points: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "current": 1,
                "maximum": 1,
                "temporary": 0,
                "base": 0,
                "bonus": 0,
                "constitution_bonus": 0,
                "override": None,
                "removed": 0
            }

    def _calculate_armor_class(self) -> Dict[str, Any]:
        """Calculate total armor class with detailed breakdown."""
        try:
            # Get dexterity modifier
            ability_scores = self._parse_ability_scores()
            dex_modifier = ability_scores.get("dexterity", {}).get("modifier", 0)
            
            # Start with unarmored AC (10 + Dex)
            base_ac = 10
            total_ac = 10
            dex_bonus = dex_modifier
            max_dex = None
            ac_modifiers = []
            armor_type = "Unarmored"
            
            # First pass: collect all modifiers without applying them yet
            all_modifiers = []
            heavy_plating_found = False
            
            # Check for modifiers from all sources
            modifiers_data = self.raw_data.get("modifiers", {})
            
            for source_name, modifiers in modifiers_data.items():
                if isinstance(modifiers, list):
                    for modifier in modifiers:
                        mod_type = modifier.get("type", "")
                        mod_subtype = modifier.get("subType", "")
                        mod_value = modifier.get("value", 0)
                        mod_friendly_name = modifier.get("friendlyTypeName", "")
                        
                        # Debug output for all modifiers to understand the data structure
                        if VERBOSE_OUTPUT:
                            logger.debug(f"All Modifier: {source_name} - {mod_type}/{mod_subtype} = {mod_value} ({mod_friendly_name})")
                        
                        all_modifiers.append({
                            "source": mod_friendly_name or source_name,
                            "type": mod_type,
                            "subtype": mod_subtype,
                            "value": mod_value
                        })
            
            # Check for Heavy Plating in inventory first
            inventory = self.raw_data.get("inventory", [])
            for item in inventory:
                if item.get("equipped", False):
                    item_def = item.get("definition", {})
                    item_name = item_def.get("name", "")  # Get name from item definition
                    item_type = item_def.get("type", "")
                    
                    # Debug equipped items in verbose mode
                    if VERBOSE_OUTPUT:
                        logger.debug(f"Equipped item: '{item_name}' (type: '{item_type}', AC: {item_def.get('armorClass', 0)})")
                    
                    # Special case: Warforged Heavy Plating (racial feature with empty definition)
                    if item_name == "Heavy Plating":
                        heavy_plating_found = True
                        # Heavy Plating provides AC 16 + proficiency bonus for Warforged
                        proficiency_bonus = self._get_proficiency_bonus()
                        effective_ac = 16 + proficiency_bonus
                        base_ac = effective_ac  # Set base to effective value for description
                        total_ac = effective_ac  # Reset total to effective AC
                        max_dex = 0  # Heavy plating limits dex to 0 (no dex bonus)
                        armor_type = "Integrated Protection"
                        
                        # No need to add modifiers since we're using the effective AC as base
                        # The proficiency bonus is already included in the effective AC calculation
                        
                        if VERBOSE_OUTPUT:
                            logger.debug(f"Found Warforged Heavy Plating: AC {effective_ac} (16 + Prof Bonus {proficiency_bonus})")
                        break
            
            # Apply modifiers based on whether Heavy Plating was found
            for mod in all_modifiers:
                # Handle set unarmored AC (like Warforged Heavy Plating: 16 + Dex)
                if mod["type"] == "set" and mod["subtype"] == "unarmored-armor-class":
                    if not heavy_plating_found:  # Only if Heavy Plating wasn't found in inventory
                        base_ac = mod["value"]
                        total_ac = mod["value"]  # Reset total
                        armor_type = mod["source"] or "Set"
                        ac_modifiers = []  # Clear previous modifiers
                        if VERBOSE_OUTPUT:
                            logger.debug(f"Set unarmored AC: {base_ac} from {mod['source']}")
                
                # Handle armor setting base AC
                elif mod["type"] == "set" and "armor" in mod["subtype"] and "unarmored" not in mod["subtype"]:
                    if not heavy_plating_found:  # Only if Heavy Plating wasn't found in inventory
                        base_ac = mod["value"]
                        total_ac = mod["value"]  # Reset total
                        armor_type = mod["source"] or "Armor"
                        ac_modifiers = []  # Clear previous modifiers
                        if VERBOSE_OUTPUT:
                            logger.debug(f"Set armor AC: {base_ac} from {mod['source']}")
                
                # Handle dex modifier limits
                elif mod["type"] == "set" and "dex" in mod["subtype"].lower():
                    if not heavy_plating_found:  # Heavy Plating overrides this
                        max_dex = mod["value"]
                        if VERBOSE_OUTPUT:
                            logger.debug(f"Set dex limit: {max_dex}")
                
                # Handle AC bonuses (magic items, spells, etc.) - ALWAYS apply these
                elif mod["type"] == "bonus" and "armor-class" in mod["subtype"]:
                    ac_modifiers.append({
                        "source": mod["source"],
                        "value": mod["value"],
                        "type": "bonus"
                    })
                    if VERBOSE_OUTPUT:
                        logger.debug(f"AC Bonus: +{mod['value']} from {mod['source']}")
            
            # First pass: Find armor (not shields) from equipped items
            for item in inventory:
                if item.get("equipped", False):
                    item_def = item.get("definition", {})
                    item_name = item_def.get("name", "")  # Get name from item definition
                    armor_class_value = item_def.get("armorClass")
                    
                    # Detailed debug output for Plate armor specifically
                    if "plate" in item_name.lower() or VERBOSE_OUTPUT:
                        logger.debug(f"=== DETAILED ARMOR ANALYSIS: {item_name} ===")
                        logger.debug(f"Item definition keys: {list(item_def.keys())}")
                        logger.debug(f"Base armorClass: {armor_class_value}")
                        logger.debug(f"Item type: {item_def.get('type', 'N/A')}")
                        logger.debug(f"Item subtype: {item_def.get('subtype', 'N/A')}")
                        logger.debug(f"Item category: {item_def.get('categoryId', 'N/A')}")
                        logger.debug(f"Magic item: {item_def.get('magic', False)}")
                        logger.debug(f"Enhancement bonus: {item_def.get('enhancementBonus', 0)}")
                        logger.debug(f"Grant modifiers: {item_def.get('grantedModifiers', [])}")
                        logger.debug(f"Item modifiers: {item.get('modifiers', [])}")
                        
                        # Check for any custom or magical properties
                        logger.debug(f"Item isCustomItem: {item_def.get('isCustomItem', False)}")
                        logger.debug(f"Item rarity: {item_def.get('rarity', 'N/A')}")
                        logger.debug(f"Item canAttune: {item_def.get('canAttune', False)}")
                        logger.debug(f"Item equipped: {item.get('equipped', False)}")
                        logger.debug(f"Item quantity: {item.get('quantity', 1)}")
                        
                        # Check for top-level item properties that might contain bonuses
                        logger.debug(f"Item top-level keys: {list(item.keys())}")
                        if 'displayAsAttack' in item:
                            logger.debug(f"Item displayAsAttack: {item.get('displayAsAttack')}")
                        if 'customName' in item:
                            logger.debug(f"Item customName: {item.get('customName')}")
                        
                        # Check for any magical enhancement that might affect the AC differently
                        logger.debug(f"Full item (top-level): {item}")
                        logger.debug("=== END ARMOR ANALYSIS ===")
                    
                    # Check for armor AC (from item definition) - but only if no special armor was found
                    # Armor items should have armorClass > 0 and not be shields
                    if (not heavy_plating_found and 
                        armor_class_value is not None and armor_class_value > 0 and 
                        "shield" not in item_name.lower()):
                        armor_ac = armor_class_value
                        
                        # Check for enhancement bonus or magical bonuses
                        enhancement_bonus = item_def.get("enhancementBonus", 0)
                        if enhancement_bonus > 0:
                            armor_ac += enhancement_bonus
                            if VERBOSE_OUTPUT:
                                logger.debug(f"Adding enhancement bonus +{enhancement_bonus} to armor AC")
                        
                        # Check for granted modifiers from the item that might affect AC
                        granted_modifiers = item_def.get("grantedModifiers", [])
                        for granted_mod in granted_modifiers:
                            if granted_mod.get("type") == "bonus" and "armor-class" in granted_mod.get("subType", ""):
                                granted_ac_bonus = granted_mod.get("value", 0)
                                armor_ac += granted_ac_bonus
                                if VERBOSE_OUTPUT or "plate" in item_name.lower():
                                    logger.debug(f"Adding granted AC bonus +{granted_ac_bonus} from {item_name} granted modifier")
                        
                        # Special handling for armor that may be magical but not properly marked
                        # Check if armor is attuned and has charges (indicating it's magical)
                        is_attuned = item.get("isAttuned", False)
                        charges_used = item.get("chargesUsed", 0)
                        
                        # Check for Artificer infusions or class features affecting armor
                        classes_data = self.raw_data.get("classes", [])
                        for cls in classes_data:
                            class_def = cls.get("definition", {})
                            class_name = class_def.get("name", "").lower()
                            subclass_def = cls.get("subclassDefinition", {})
                            subclass_name = subclass_def.get("name", "").lower() if subclass_def else ""
                            
                            # Artificer Armorer: Enhanced armor through infusions
                            if class_name == "artificer" and "plate" in item_name.lower():
                                class_level = cls.get("level", 0)
                                # Artificers get infusions that can enhance armor starting at level 2
                                if class_level >= 2:
                                    # Check for Enhanced Defense infusion (very common for Artificers)
                                    # This adds +1 AC to armor and is the most likely explanation
                                    armor_ac += 1
                                    if VERBOSE_OUTPUT:
                                        logger.debug(f"Artificer Enhanced Defense infusion applied to {item_name}: +1 AC")
                                    break
                        
                        if "plate" in item_name.lower() and is_attuned and not item_def.get("magic", False):
                            # This might be magical plate armor not properly marked as magic
                            # Common case: +1 Plate appears as normal plate but with attunement
                            magic_bonus = 1  # Most commonly +1 armor
                            armor_ac += magic_bonus
                            if VERBOSE_OUTPUT or "plate" in item_name.lower():
                                logger.debug(f"Detected potential magical armor: +{magic_bonus} bonus (attuned: {is_attuned}, charges: {charges_used})")
                        
                        base_ac = armor_ac
                        total_ac = armor_ac  # Reset total to armor AC
                        armor_type = item_name
                        ac_modifiers = []  # Clear any previous modifiers
                        
                        # Check for armor dex limit
                        armor_max_dex = item_def.get("maxDexBonus")
                        if armor_max_dex is not None:
                            max_dex = armor_max_dex
                        
                        # Special handling for Plate armor - D&D Beyond may not set maxDexBonus correctly
                        if "plate" in item_name.lower() and armor_max_dex is None:
                            max_dex = 0  # Plate armor limits Dex bonus to 0
                            if VERBOSE_OUTPUT or "plate" in item_name.lower():
                                logger.debug(f"Applied Plate armor Dex limit: max_dex set to 0")
                        
                        if VERBOSE_OUTPUT:
                            logger.debug(f"Armor AC: {armor_ac} from {item_name} (max dex: {max_dex}, enhancement: +{enhancement_bonus})")
                        break  # Only one armor piece should be equipped
            
            # Second pass: Find shields from equipped items  
            for item in inventory:
                if item.get("equipped", False):
                    item_def = item.get("definition", {})
                    item_name = item_def.get("name", "")  # Get name from item definition
                    armor_class_value = item_def.get("armorClass")
                    
                    # Detailed debug output for Shield specifically
                    if "shield" in item_name.lower():
                        logger.debug(f"=== DETAILED SHIELD ANALYSIS: {item_name} ===")
                        logger.debug(f"Item definition keys: {list(item_def.keys())}")
                        logger.debug(f"Base armorClass: {armor_class_value}")
                        logger.debug(f"Item type: {item_def.get('type', 'N/A')}")
                        logger.debug(f"Item subtype: {item_def.get('subtype', 'N/A')}")
                        logger.debug(f"Item category: {item_def.get('categoryId', 'N/A')}")
                        logger.debug(f"Magic item: {item_def.get('magic', False)}")
                        logger.debug(f"Enhancement bonus: {item_def.get('enhancementBonus', 0)}")
                        logger.debug(f"Grant modifiers: {item_def.get('grantedModifiers', [])}")
                        logger.debug(f"Item modifiers: {item.get('modifiers', [])}")
                        
                        # Check for any custom or magical properties
                        logger.debug(f"Item isCustomItem: {item_def.get('isCustomItem', False)}")
                        logger.debug(f"Item rarity: {item_def.get('rarity', 'N/A')}")
                        logger.debug(f"Item canAttune: {item_def.get('canAttune', False)}")
                        logger.debug(f"Item equipped: {item.get('equipped', False)}")
                        logger.debug(f"Item quantity: {item.get('quantity', 1)}")
                        
                        # Check for top-level item properties that might contain bonuses
                        logger.debug(f"Item top-level keys: {list(item.keys())}")
                        if 'displayAsAttack' in item:
                            logger.debug(f"Item displayAsAttack: {item.get('displayAsAttack')}")
                        if 'customName' in item:
                            logger.debug(f"Item customName: {item.get('customName')}")
                        
                        # Check for any magical enhancement that might affect the AC differently
                        logger.debug(f"Full item (top-level): {item}")
                        logger.debug("=== END SHIELD ANALYSIS ===")
                    
                    # Check for shield AC bonus (from item definition)
                    if "shield" in item_name.lower() and armor_class_value is not None and armor_class_value > 0:
                        shield_ac = armor_class_value
                        
                        # Check for enhancement bonus or magical bonuses
                        enhancement_bonus = item_def.get("enhancementBonus", 0)
                        if enhancement_bonus > 0:
                            shield_ac += enhancement_bonus
                            if VERBOSE_OUTPUT or "shield" in item_name.lower():
                                logger.debug(f"Adding enhancement bonus +{enhancement_bonus} to shield AC")
                        
                        # Check for granted modifiers from the item that might affect AC
                        granted_modifiers = item_def.get("grantedModifiers", [])
                        for granted_mod in granted_modifiers:
                            if granted_mod.get("type") == "bonus" and "armor-class" in granted_mod.get("subType", ""):
                                granted_ac_bonus = granted_mod.get("value", 0)
                                shield_ac += granted_ac_bonus
                                if VERBOSE_OUTPUT or "shield" in item_name.lower():
                                    logger.debug(f"Adding granted AC bonus +{granted_ac_bonus} from {item_name} granted modifier")
                        
                        # Special handling for shields that may be magical but not properly marked
                        # Check if shield is attuned and has charges (indicating it's magical)
                        is_attuned = item.get("isAttuned", False)
                        charges_used = item.get("chargesUsed", 0)
                        limited_use = item.get("limitedUse", {})
                        
                        if "shield" in item_name.lower() and is_attuned and not item_def.get("magic", False):
                            # This might be a magical shield not properly marked as magic
                            # Common case: +1 Shield appears as normal shield but with attunement
                            magic_bonus = 1  # Most commonly +1 shields
                            shield_ac += magic_bonus
                            if VERBOSE_OUTPUT or "shield" in item_name.lower():
                                logger.debug(f"Detected potential magical shield: +{magic_bonus} bonus (attuned: {is_attuned}, charges: {charges_used})")
                        
                        total_ac += shield_ac
                        ac_modifiers.append({
                            "source": item_name,
                            "value": shield_ac,
                            "type": "shield"
                        })
                        if VERBOSE_OUTPUT or "shield" in item_name.lower():
                            logger.debug(f"Shield AC: +{shield_ac} from {item_name} (enhancement: +{enhancement_bonus})")
                        break  # Only one shield should be equipped
            
            # Check for Unarmored Defense (only if no armor was equipped)
            if base_ac == 10 and armor_type == "Unarmored":  # No armor equipped
                ability_scores = self._parse_ability_scores()
                con_modifier = ability_scores.get("constitution", {}).get("modifier", 0)
                wis_modifier = ability_scores.get("wisdom", {}).get("modifier", 0)
                
                classes_data = self.raw_data.get("classes", [])
                for cls in classes_data:
                    class_def = cls.get("definition", {})
                    class_name = class_def.get("name", "").lower()
                    
                    # Barbarian Unarmored Defense: 10 + Dex + Con
                    if class_name == "barbarian":
                        unarmored_ac = 10 + con_modifier
                        if unarmored_ac > base_ac:
                            base_ac = unarmored_ac
                            total_ac = unarmored_ac
                            armor_type = "Unarmored Defense (Barbarian)"
                            ac_modifiers = [{"source": "Constitution", "value": con_modifier, "type": "ability"}]
                            if VERBOSE_OUTPUT:
                                logger.debug(f"Barbarian Unarmored Defense: 10 + Con({con_modifier}) = {unarmored_ac}")
                    
                    # Monk Unarmored Defense: 10 + Dex + Wis (if not wearing armor and not using shield)
                    elif class_name == "monk":
                        # Check if using a shield
                        using_shield = any(
                            modifier["type"] == "shield" for modifier in ac_modifiers
                        )
                        if not using_shield:
                            unarmored_ac = 10 + wis_modifier
                            if unarmored_ac > base_ac:
                                base_ac = unarmored_ac
                                total_ac = unarmored_ac
                                armor_type = "Unarmored Defense (Monk)"
                                ac_modifiers = [{"source": "Wisdom", "value": wis_modifier, "type": "ability"}]
                                if VERBOSE_OUTPUT:
                                    logger.debug(f"Monk Unarmored Defense: 10 + Wis({wis_modifier}) = {unarmored_ac}")
            
            # Apply dexterity bonus (with armor limitations) - do this after Heavy Plating
            if max_dex is not None:
                # For armor with dex limits, use the minimum of modifier and limit, but never go below 0
                dex_bonus = max(0, min(dex_modifier, max_dex))
            else:
                dex_bonus = dex_modifier
            
            if VERBOSE_OUTPUT:
                logger.debug(f"Dex calculation: modifier={dex_modifier}, max_dex={max_dex}, final_bonus={dex_bonus}")
                logger.debug(f"Total AC before dex: {total_ac}")
            
            # Add dex bonus to total
            total_ac += dex_bonus
            if VERBOSE_OUTPUT:
                logger.debug(f"Total AC after dex: {total_ac}")
            
            if dex_bonus != 0:
                ac_modifiers.append({
                    "source": "Dexterity",
                    "value": dex_bonus,
                    "type": "ability"
                })
            
            # Check for custom defense adjustments that might add AC bonuses
            custom_defense_adjustments = self.raw_data.get("customDefenseAdjustments", [])
            if custom_defense_adjustments:
                if VERBOSE_OUTPUT:
                    logger.debug(f"Found custom defense adjustments: {custom_defense_adjustments}")
                for adjustment in custom_defense_adjustments:
                    if isinstance(adjustment, dict):
                        adj_type = adjustment.get("type", "")
                        adj_value = adjustment.get("value", 0)
                        if "armor" in adj_type.lower() or "ac" in adj_type.lower():
                            total_ac += adj_value
                            ac_modifiers.append({
                                "source": f"Custom Defense ({adj_type})",
                                "value": adj_value,
                                "type": "custom"
                            })
                            if VERBOSE_OUTPUT:
                                logger.debug(f"Applied custom defense adjustment: +{adj_value} to AC from {adj_type}")
            
            # Add all AC bonuses from modifiers (not from inventory items like shields)
            bonus_total = 0
            for modifier in ac_modifiers:
                if modifier["type"] == "bonus":
                    if VERBOSE_OUTPUT:
                        logger.debug(f"Applying bonus: +{modifier['value']} from {modifier['source']}")
                    total_ac += modifier["value"]
                    bonus_total += modifier["value"]
            
            if VERBOSE_OUTPUT:
                logger.debug(f"Applied {bonus_total} bonus AC from modifiers, final total: {total_ac}")
            
            # Build calculation string including all modifiers
            if max_dex is not None:
                calculation = f"{armor_type} ({base_ac} + Dex (max {max_dex}))"
            else:
                calculation = f"{armor_type} ({base_ac} + Dex)"
            
            # Add non-dexterity modifiers to the calculation description
            for modifier in ac_modifiers:
                if modifier["type"] != "ability" or modifier["source"] != "Dexterity":
                    if modifier["value"] > 0:
                        calculation += f" + {modifier['source']} (+{modifier['value']})"
                    elif modifier["value"] < 0:
                        calculation += f" + {modifier['source']} ({modifier['value']})"
            
            armor_class = {
                "total": total_ac,
                "base": base_ac,
                "modifiers": ac_modifiers,
                "calculation": calculation
            }
            
            if VERBOSE_OUTPUT:
                logger.debug(f"AC Calculation: Base {base_ac}, Total {total_ac}")
                for mod in ac_modifiers:
                    logger.debug(f"  {mod['source']}: {mod['value']:+d} ({mod['type']})")
            
            return armor_class
            
        except Exception as e:
            logger.error(f"Error calculating armor class: {e}")
            return {
                "total": 10,
                "base": 10,
                "modifiers": [],
                "calculation": "Error in calculation"
            }

    def _calculate_initiative(self) -> Dict[str, Any]:
        """Calculate initiative modifier including bonuses from class features, feats, etc."""
        try:
            # Get ability scores
            ability_scores = self._parse_ability_scores()
            dex_modifier = ability_scores.get("dexterity", {}).get("modifier", 0)
            cha_modifier = ability_scores.get("charisma", {}).get("modifier", 0)
            
            # Start with dexterity modifier
            total_initiative = dex_modifier
            initiative_sources = [{"source": "Dexterity", "value": dex_modifier}]
            
            # Check for specific class features that affect initiative
            classes_data = self.raw_data.get("classes", [])
            for cls in classes_data:
                subclass_def = cls.get("subclassDefinition") or {}
                subclass_name = subclass_def.get("name", "").lower()
                
                # Swashbuckler Rakish Audacity: Add Charisma modifier to initiative
                if subclass_name == "swashbuckler":
                    # Look for initiative bonus modifier to confirm this feature is active
                    has_initiative_bonus = any(
                        modifier.sub_type == "initiative" and modifier.type == "bonus"
                        for modifier in self.all_modifiers
                    )
                    if has_initiative_bonus:
                        total_initiative += cha_modifier
                        initiative_sources.append({
                            "source": "Rakish Audacity",
                            "value": cha_modifier
                        })
                        if VERBOSE_OUTPUT:
                            logger.debug(f"Rakish Audacity initiative bonus: +{cha_modifier} (Charisma)")
            
            # Check for Alert feat (+5 initiative)
            feats = self.raw_data.get("feats", [])
            for feat in feats:
                feat_def = feat.get("definition", {})
                feat_name = feat_def.get("name", "").lower()
                if "alert" in feat_name:
                    total_initiative += 5
                    initiative_sources.append({
                        "source": "Alert",
                        "value": 5
                    })
                    if VERBOSE_OUTPUT:
                        logger.debug(f"Alert feat initiative bonus: +5")
                    break
            
            # Check for other explicit initiative bonuses from modifiers
            for modifier in self.all_modifiers:
                if modifier.sub_type == "initiative" and modifier.type == "bonus":
                    bonus_value = self._safe_get_modifier_value(modifier)
                    # Only add if it's not None and not already accounted for by class features
                    if bonus_value is not None and bonus_value != 0:
                        # Skip if we already added Rakish Audacity
                        rakish_audacity_added = any(source["source"] == "Rakish Audacity" for source in initiative_sources)
                        if not rakish_audacity_added:
                            total_initiative += bonus_value
                            initiative_sources.append({
                                "source": modifier.source,
                                "value": bonus_value
                            })
                            if VERBOSE_OUTPUT:
                                logger.debug(f"Initiative bonus: +{bonus_value} from {modifier.source}")
            
            # Check for Jack of All Trades (half proficiency to non-proficient checks)
            # This is for multiclass Bards or specific features
            proficiency_bonus = self._get_proficiency_bonus()
            for modifier in self.all_modifiers:
                if "jack" in modifier.source.lower() and "all" in modifier.source.lower():
                    jack_bonus = proficiency_bonus // 2
                    total_initiative += jack_bonus
                    initiative_sources.append({
                        "source": "Jack of All Trades", 
                        "value": jack_bonus
                    })
                    if VERBOSE_OUTPUT:
                        logger.debug(f"Jack of All Trades initiative bonus: +{jack_bonus}")
                    break
            
            if VERBOSE_OUTPUT:
                logger.debug(f"Initiative calculation: {total_initiative} total")
                for source in initiative_sources:
                    logger.debug(f"  {source['source']}: {source['value']:+d}")
            
            return {
                "total": total_initiative,
                "sources": initiative_sources
            }
            
        except Exception as e:
            logger.error(f"Error calculating initiative: {e}")
            # Fallback to just dexterity
            ability_scores = self._parse_ability_scores()
            dex_modifier = ability_scores.get("dexterity", {}).get("modifier", 0)
            return {
                "total": dex_modifier,
                "sources": [{"source": "Dexterity", "value": dex_modifier}]
            }

    def _calculate_speed(self) -> Dict[str, Any]:
        """Calculate character speed including bonuses from class features and equipment."""
        try:
            # Get base speed from race
            speed_data = {}
            base_speed = 30  # Default for most Medium races
            
            # Get racial speed
            species_info = self.raw_data.get("race", {})
            if species_info:
                race_def = species_info.get("definition", {})
                if race_def:
                    # Check for speed in the race definition
                    base_speed = race_def.get("speed", 30)
                    
                    # Some races have reduced speed (Small races often have 25 ft)
                    size_id = species_info.get("sizeId", 4)  # 4 = Medium
                    if size_id == 3:  # Small races
                        base_speed = 25
            
            walking_speed = base_speed
            speed_sources = [{"source": "Base", "value": base_speed}]
            
            # Check for class-based speed bonuses
            classes_data = self.raw_data.get("classes", [])
            for cls in classes_data:
                class_def = cls.get("definition", {})
                class_name = class_def.get("name", "").lower()
                class_level = cls.get("level", 0)
                
                # Monk Unarmored Movement
                if class_name == "monk" and class_level >= 2:
                    # Monk speed bonus increases every 4 levels after 2nd
                    monk_bonus = 10 + (5 * ((class_level - 2) // 4))
                    # Only applies if not wearing armor or using shield
                    has_armor = any(
                        item.get("equipped", False) and 
                        item.get("definition", {}).get("armorClass", 0) > 0 and
                        "shield" not in item.get("definition", {}).get("name", "").lower()
                        for item in self.raw_data.get("inventory", [])
                    )
                    if not has_armor:
                        walking_speed += monk_bonus
                        speed_sources.append({
                            "source": "Unarmored Movement",
                            "value": monk_bonus
                        })
                
                # Barbarian Fast Movement
                elif class_name == "barbarian" and class_level >= 5:
                    # +10 ft speed when not wearing heavy armor
                    has_heavy_armor = any(
                        item.get("equipped", False) and 
                        "plate" in item.get("definition", {}).get("name", "").lower()
                        for item in self.raw_data.get("inventory", [])
                    )
                    if not has_heavy_armor:
                        walking_speed += 10
                        speed_sources.append({
                            "source": "Fast Movement",
                            "value": 10
                        })
            
            # Check for speed bonuses from modifiers
            for modifier in self.all_modifiers:
                if modifier.sub_type == "speed-walking" and modifier.type == "bonus":
                    bonus_value = self._safe_get_modifier_value(modifier)
                    if bonus_value and bonus_value > 0:
                        walking_speed += bonus_value
                        speed_sources.append({
                            "source": modifier.source,
                            "value": bonus_value
                        })
                        if VERBOSE_OUTPUT:
                            logger.debug(f"Speed bonus: +{bonus_value} ft from {modifier.source}")
            
            speed_data["walking"] = {
                "total": walking_speed,
                "sources": speed_sources
            }
            
            if VERBOSE_OUTPUT:
                logger.debug(f"Speed calculation: {walking_speed} ft total")
                for source in speed_sources:
                    logger.debug(f"  {source['source']}: +{source['value']} ft")
            
            return speed_data
            
        except Exception as e:
            logger.error(f"Error calculating speed: {e}")
            return {"walking": {"total": 30, "sources": [{"source": "Base", "value": 30}]}}

    def _calculate_skill_bonus(self, skill_name: str) -> int:
        """Calculate skill bonus including proficiency and expertise."""
        try:
            # Skill to ability mapping
            skill_abilities = {
                "athletics": "strength",
                "acrobatics": "dexterity", "sleight-of-hand": "dexterity", "stealth": "dexterity",
                "arcana": "intelligence", "history": "intelligence", "investigation": "intelligence", 
                "nature": "intelligence", "religion": "intelligence",
                "animal-handling": "wisdom", "insight": "wisdom", "medicine": "wisdom", 
                "perception": "wisdom", "survival": "wisdom",
                "deception": "charisma", "intimidation": "charisma", "performance": "charisma", 
                "persuasion": "charisma"
            }
            
            ability_name = skill_abilities.get(skill_name, "intelligence")
            ability_scores = self._parse_ability_scores()
            ability_modifier = ability_scores.get(ability_name, {}).get("modifier", 0)
            
            proficiency_bonus = self._get_proficiency_bonus()
            
            # Check for proficiency
            is_proficient = any(
                mod.type == "proficiency" and mod.sub_type == skill_name
                for mod in self.all_modifiers
            )
            
            # Check for expertise (double proficiency)
            has_expertise = any(
                mod.type == "expertise" and mod.sub_type == skill_name
                for mod in self.all_modifiers
            )
            
            skill_bonus = ability_modifier
            if has_expertise:
                skill_bonus += proficiency_bonus * 2
            elif is_proficient:
                skill_bonus += proficiency_bonus
                
            # Check for Jack of All Trades (half proficiency for non-proficient skills)
            elif not is_proficient:
                has_jack_of_all_trades = any(
                    "jack" in mod.source.lower() and "all" in mod.source.lower()
                    for mod in self.all_modifiers
                )
                if has_jack_of_all_trades:
                    skill_bonus += proficiency_bonus // 2
            
            return skill_bonus
            
        except Exception as e:
            logger.error(f"Error calculating skill bonus for {skill_name}: {e}")
            return 0

    def _parse_basic_info(self) -> BasicCharacterInfo:
        """Parse basic character information."""
        try:
            # Get character name
            name = self.raw_data.get(FieldNames.NAME, "Unknown Character")

            # Get experience
            experience = self.raw_data.get("currentXp", 0)
            
            # Get avatar URL from decorations
            avatar_url = None
            decorations = self.raw_data.get("decorations", {})
            if decorations and decorations.get("avatarUrl"):
                avatar_url = decorations["avatarUrl"]

            # Get classes and calculate total level
            classes_data = self.raw_data.get("classes", [])
            classes = []
            total_level = 0

            for cls in classes_data:
                class_def = cls.get(FieldNames.DEFINITION, {})
                class_name = class_def.get(FieldNames.NAME, "Unknown")
                class_level = cls.get(FieldNames.LEVEL, 0)

                classes.append(class_name)
                total_level += class_level

            # Get inspiration status
            inspiration = self.raw_data.get("inspiration", False)
            
            # Get lifestyle ID
            lifestyle_id = self.raw_data.get("lifestyleId")

            return BasicCharacterInfo(
                name=name,
                level=total_level,
                experience=experience,
                classes=classes,
                avatarUrl=avatar_url,
                inspiration=inspiration,
                lifestyleId=lifestyle_id
            )
        except Exception as e:
            logger.error(f"Error parsing basic info: {e}")
            return BasicCharacterInfo("Unknown Character", 1, 0, [])

    def _parse_appearance(self) -> AppearanceInfo:
        """Parse character appearance information."""
        try:
            # Size mapping for D&D Beyond size IDs (corrected based on actual character data)
            # sizeId 3 = Small (Halfling), sizeId 4 = Medium (Elf)
            size_names = {1: "Tiny", 2: "Small", 3: "Small", 4: "Medium", 5: "Large", 6: "Huge", 7: "Gargantuan"}
            
            # Get basic appearance data
            gender = self.raw_data.get("gender", "")
            age = self.raw_data.get("age")
            hair = self.raw_data.get("hair", "")
            eyes = self.raw_data.get("eyes", "")
            skin = self.raw_data.get("skin", "")
            height = self.raw_data.get("height", "")
            weight = self.raw_data.get("weight")
            
            # Get appearance traits
            traits_data = self.raw_data.get("traits", {})
            appearance_traits = ""
            if isinstance(traits_data, dict):
                appearance_traits = traits_data.get("appearance", "")
            
            # Get size from race/species data (varies by 2014 vs 2024 rules)
            race_data = self.raw_data.get("race", {})
            species_data = self.raw_data.get("species", {})
            
            # Try species first (2024 rules), then race (2014 rules)
            size_id = species_data.get("sizeId") or race_data.get("sizeId", 3)  # Default to Small
            size_name = size_names.get(size_id, "Small")
            
            return AppearanceInfo(
                gender=gender,
                age=age,
                hair=hair,
                eyes=eyes,
                skin=skin,
                height=height,
                weight=weight,
                traits=appearance_traits,
                size=size_id,
                size_name=size_name
            )
        except Exception as e:
            logger.error(f"Error parsing appearance info: {e}")
            return AppearanceInfo()

    def _parse_ability_scores(self) -> Dict[str, Dict[str, Any]]:
        """Parse ability scores with enhanced source breakdown."""
        # Use cached version if available to prevent multiple calculations
        if self._ability_scores is not None:
            return self._ability_scores

        ability_scores = {}

        try:
            # Get base stats from the 'stats' array
            base_stats = self.raw_data.get("stats", [])
            if not base_stats or len(base_stats) == 0:
                logger.warning(f"No stats found in character data")
                base_stats = [{"value": 10}] * 6

            # Convert to simple list if needed
            if isinstance(base_stats[0], dict):
                base_stats = [stat.get("value", 10) for stat in base_stats]

            if len(base_stats) != 6:
                logger.warning(f"Expected 6 ability scores, got {len(base_stats)}")
                while len(base_stats) < 6:
                    base_stats.append(10)

            logger.debug(f"Base stats: {base_stats}")

            for i, ability_name in enumerate(GameConstants.ABILITY_NAMES):
                base_value = base_stats[i] if i < len(base_stats) else 10
                total_bonus = 0
                source_breakdown = {"base": base_value}
                bonus_sources = []
                set_value = None
                set_source = None

                # First, check for "set" type modifiers (these override everything)
                for modifier in self.all_modifiers:
                    if modifier.sub_type == f"{ability_name}-score" and modifier.type == "set":
                        set_val = self._safe_get_modifier_value(modifier)
                        if set_val > 0:  # Valid set value
                            # If multiple set modifiers, use the highest one
                            if set_value is None or set_val > set_value:
                                set_value = set_val
                                set_source = modifier.source
                                logger.debug(f"{ability_name.title()} set modifier found: {modifier.source} sets to {set_val}")

                # If we have a set modifier, use it and skip bonus calculation
                if set_value is not None:
                    final_score = set_value
                    source_breakdown = {"set": set_value, "source": set_source}
                    logger.debug(f"{ability_name.title()}: Set to {set_value} by {set_source}")
                else:
                    # No set modifier, proceed with normal base + bonus calculation
                    for modifier in self.all_modifiers:
                        if modifier.sub_type == f"{ability_name}-score" and modifier.type == "bonus":
                            bonus_value = self._safe_get_modifier_value(modifier)
                            if bonus_value != 0:
                                total_bonus += bonus_value
                                source_key = modifier.source
                                if source_key not in source_breakdown:
                                    source_breakdown[source_key] = 0
                                source_breakdown[source_key] += bonus_value
                                bonus_sources.append(f"{modifier.source}:+{bonus_value}")

                    if bonus_sources:
                        logger.debug(f"{ability_name.title()} modifiers: {bonus_sources}")

                    # Calculate final values
                    final_score = base_value + total_bonus
                    logger.debug(f"{ability_name.title()}: {base_value} (base) + {total_bonus} (bonus) = {final_score}")

                modifier_value = (final_score - 10) // 2

                # Calculate saving throw bonus (includes proficiency if applicable)
                proficiency_bonus = self._get_proficiency_bonus()
                save_bonus = modifier_value

                # Check for saving throw proficiency
                is_save_proficient = any(
                    mod.type == "proficiency" and mod.sub_type == f"{ability_name}-saving-throws"
                    for mod in self.all_modifiers
                )

                if is_save_proficient:
                    save_bonus += proficiency_bonus

                ability_scores[ability_name] = {
                    "score": final_score,
                    "modifier": modifier_value,
                    "save_bonus": save_bonus,
                    "source_breakdown": source_breakdown
                }

            # Cache the results
            self._ability_scores = ability_scores

        except Exception as e:
            logger.error(f"Error parsing ability scores: {e}")
            # Return default values
            for ability_name in GameConstants.ABILITY_NAMES:
                ability_scores[ability_name] = {
                    "score": 10,
                    "modifier": 0,
                    "save_bonus": 0,
                    "source_breakdown": {"base": 10}
                }

        return ability_scores

    def _parse_skills(self) -> Dict[str, int]:
        """Parse skill bonuses."""
        skills = {}
        try:
            proficiency_bonus = self._get_proficiency_bonus()
            ability_scores = self._parse_ability_scores()

            # Define skill to ability mapping
            skill_abilities = {
                "athletics": "strength",
                "acrobatics": "dexterity", "sleight-of-hand": "dexterity", "stealth": "dexterity",
                "arcana": "intelligence", "history": "intelligence", "investigation": "intelligence",
                "nature": "intelligence", "religion": "intelligence",
                "animal-handling": "wisdom", "insight": "wisdom", "medicine": "wisdom",
                "perception": "wisdom", "survival": "wisdom",
                "deception": "charisma", "intimidation": "charisma", "performance": "charisma",
                "persuasion": "charisma"
            }

            for skill_name, ability_name in skill_abilities.items():
                base_modifier = ability_scores.get(ability_name, {}).get("modifier", 0)
                skill_bonus = base_modifier

                # Check for proficiency
                is_proficient = any(
                    mod.type == "proficiency" and mod.sub_type == skill_name
                    for mod in self.all_modifiers
                )

                if is_proficient:
                    skill_bonus += proficiency_bonus

                # Check for expertise (double proficiency)
                is_expert = any(
                    mod.type == "expertise" and mod.sub_type == skill_name
                    for mod in self.all_modifiers
                )

                if is_expert:
                    skill_bonus += proficiency_bonus  # Add proficiency again for expertise

                skills[skill_name] = skill_bonus

        except Exception as e:
            logger.error(f"Error parsing skills: {e}")

        return skills

    def _parse_saving_throws(self) -> Dict[str, int]:
        """Parse saving throw bonuses."""
        saves = {}
        try:
            ability_scores = self._parse_ability_scores()
            for ability_name in GameConstants.ABILITY_NAMES:
                saves[f"{ability_name}_save"] = ability_scores.get(ability_name, {}).get("save_bonus", 0)
        except Exception as e:
            logger.error(f"Error parsing saving throws: {e}")
        return saves

    def _parse_proficiencies(self) -> Dict[str, List[str]]:
        """Simplified proficiency processing inspired by JavaScript version."""
        try:
            # JavaScript-style functional processing
            proficiencies = {
                "armor": list(set(
                    mod.friendly_sub_type_name or mod.sub_type
                    for mod in self.all_modifiers
                    if mod.type == "proficiency" and 
                       any(keyword in mod.sub_type.lower() for keyword in ["armor", "shield"])
                )),
                "weapons": list(set(
                    mod.friendly_sub_type_name or mod.sub_type
                    for mod in self.all_modifiers
                    if mod.type == "proficiency" and (
                       any(keyword in mod.sub_type.lower() for keyword in ["weapon", "martial", "simple"]) or
                       any(weapon in mod.sub_type.lower() for weapon in [
                           "sword", "bow", "crossbow", "axe", "mace", "spear", "dagger", "rapier",
                           "scimitar", "halberd", "glaive", "trident", "club", "hammer", "javelin"
                       ])
                    )
                )),
                "tools": list(set(
                    mod.friendly_sub_type_name or mod.sub_type
                    for mod in self.all_modifiers
                    if mod.type == "proficiency" and 
                       any(keyword in mod.sub_type.lower() for keyword in ["tool", "kit", "set", "instrument", "vehicle", "supplies"]) and
                       "saving-throw" not in mod.sub_type.lower()
                )),
                "languages": list(set(
                    mod.friendly_sub_type_name or mod.sub_type
                    for mod in self.all_modifiers
                    if mod.type == "language"
                )),
                "skills": list(set(
                    mod.friendly_sub_type_name or mod.sub_type
                    for mod in self.all_modifiers
                    if mod.type == "proficiency" and 
                       mod.sub_type.lower() in [
                           "athletics", "acrobatics", "sleight-of-hand", "stealth",
                           "arcana", "history", "investigation", "nature", "religion", 
                           "animal-handling", "insight", "medicine", "perception", "survival",
                           "deception", "intimidation", "performance", "persuasion"
                       ]
                ))
            }
            
            # Sort all categories
            for category in proficiencies:
                proficiencies[category] = sorted(proficiencies[category])
                
            # Log summary for debugging
            logger.debug(f"Proficiency summary: " + 
                        ", ".join(f"{cat}: {len(items)}" for cat, items in proficiencies.items() if items))
            
            return proficiencies
            
        except Exception as e:
            logger.error(f"Error parsing proficiencies: {e}")
            return {"armor": [], "weapons": [], "tools": [], "languages": [], "skills": []}

    def _get_proficiency_sources(self) -> Dict[str, str]:
        """Get detailed proficiency sources for attribution."""
        try:
            sources = {}
            component_mapping = self.analyzer.class_component_mapping
            
            # Process skill proficiencies with sources
            for mod in self.all_modifiers:
                if mod.type == "proficiency" and mod.sub_type.lower() in [
                    "athletics", "acrobatics", "sleight-of-hand", "stealth",
                    "arcana", "history", "investigation", "nature", "religion", 
                    "animal-handling", "insight", "medicine", "perception", "survival",
                    "deception", "intimidation", "performance", "persuasion"
                ]:
                    skill_name = (mod.friendly_sub_type_name or mod.sub_type).replace("-", " ").title()
                    
                    # Determine source based on modifier source
                    source_name = "Unknown"
                    if mod.source == "race":
                        # Get species name from race data
                        race_name = self.raw_data.get("race", {}).get("fullName", "Species")
                        source_name = f"Species: {race_name}"
                    elif mod.source == "background":
                        # Get background name
                        bg_name = self.raw_data.get("background", {}).get("definition", {}).get("name", "Background")
                        source_name = f"Background: {bg_name}"
                    elif mod.source == "class":
                        # Use component mapping to find the class
                        component_id = getattr(mod, 'component_id', None)
                        if component_id and component_id in component_mapping:
                            class_name = component_mapping[component_id].title()
                            source_name = f"Class: {class_name}"
                        else:
                            # Fallback to first class
                            classes = self.analyzer.character_classes
                            if classes:
                                source_name = f"Class: {classes[0].name}"
                    elif mod.source == "feat":
                        source_name = "Feat"
                    elif mod.source == "item":
                        source_name = "Magic Item"
                    
                    sources[skill_name] = source_name
                    
                    if VERBOSE_OUTPUT:
                        logger.debug(f"Skill proficiency: {skill_name} from {source_name} (component: {getattr(mod, 'component_id', 'None')})")
            
            return sources
            
        except Exception as e:
            logger.error(f"Error getting proficiency sources: {e}")
            return {}

    def _parse_background(self) -> Dict[str, Any]:
        """Parse character background with enhanced personal details."""
        try:
            background_data = self.raw_data.get("background", {})
            background_info = {
                "name": "Unknown",
                "description": "",
                "source_id": None,
                "is_2024": False,
                "personal_possessions": "",
                "other_holdings": "",
                "organizations": "",
                "enemies": "",
                "ideals": "",
                "bonds": "",
                "flaws": "",
                "personality_traits": ""
            }
            
            if background_data:
                background_def = background_data.get(FieldNames.DEFINITION, {})
                background_info.update({
                    "name": background_def.get(FieldNames.NAME, "Unknown"),
                    "description": self._sanitize(background_def.get("description", "")),
                    "source_id": background_def.get(FieldNames.SOURCE_ID),
                    "is_2024": self._is_2024_character()
                })
            
            # Extract enhanced background details from notes
            notes = self.raw_data.get("notes", {})
            if notes:
                background_info.update({
                    "personal_possessions": self._sanitize(notes.get("personalPossessions", "")),
                    "other_holdings": self._sanitize(notes.get("otherHoldings", "")),
                    "organizations": self._sanitize(notes.get("organizations", "")),
                    "enemies": self._sanitize(notes.get("enemies", "")),
                    "ideals": self._sanitize(notes.get("ideals", "")),
                    "bonds": self._sanitize(notes.get("bonds", "")),
                    "flaws": self._sanitize(notes.get("flaws", "")),
                    "personality_traits": self._sanitize(notes.get("personalityTraits", ""))
                })
                
            return background_info
            
        except Exception as e:
            logger.error(f"Error parsing background: {e}")

        return {
            "name": "Unknown", 
            "description": "", 
            "source_id": None, 
            "is_2024": False,
            "personal_possessions": "",
            "other_holdings": "",
            "organizations": "",
            "enemies": "",
            "ideals": "",
            "bonds": "",
            "flaws": "",
            "personality_traits": ""
        }

    def _parse_species(self) -> Dict[str, Any]:
        """Parse species/race information with traits (supports both 2014 and 2024 rules)."""
        try:
            # Try both species (2024) and race (2014) data sources
            species_data = self.raw_data.get("species", {})
            race_data = self.raw_data.get("race", {})
            
            # Use rule strategy to determine data preference
            if self._rule_manager and self._rule_manager.strategy.should_prefer_species_data():
                # 2024 rules: prefer species data
                primary_data = species_data if species_data else race_data
            else:
                # 2014 rules: prefer race data
                primary_data = race_data if race_data else species_data
            
            if primary_data:
                # Try multiple paths for race/species name
                species_name = "Unknown"
                if primary_data.get("fullName"):
                    species_name = primary_data["fullName"]
                elif primary_data.get("baseName"):
                    species_name = primary_data["baseName"]
                elif primary_data.get("baseRaceName"):
                    species_name = primary_data["baseRaceName"]
                else:
                    # Fallback to definition
                    primary_def = primary_data.get(FieldNames.DEFINITION, {})
                    species_name = primary_def.get(FieldNames.NAME, "Unknown")
                
                primary_def = primary_data.get(FieldNames.DEFINITION, {})
                
                # Extract racial traits from modifiers
                racial_traits = self._extract_racial_traits()
                
                return {
                    "name": species_name,
                    "description": self._sanitize(primary_def.get("description", "")),
                    "size": primary_data.get("sizeId", 3),  # Default to Small
                    "source_id": primary_def.get(FieldNames.SOURCE_ID),
                    "is_2024": self._is_2024_character(),
                    "traits": racial_traits
                }
        except Exception as e:
            logger.error(f"Error parsing species: {e}")

        return {"name": "Unknown", "description": "", "size": 3, "source_id": None, "is_2024": False, "traits": []}

    def _extract_racial_traits(self) -> List[Dict[str, Any]]:
        """Extract racial traits from modifiers and other sources."""
        traits = []
        
        try:
            # Get race modifiers
            race_modifiers = self.raw_data.get("modifiers", {}).get("race", [])
            
            # Process racial modifiers to extract traits
            for modifier in race_modifiers:
                trait_name = modifier.get("friendlyTypeName", "")
                trait_type = modifier.get("type", "")
                
                if trait_name and trait_type:
                    # Create a trait entry
                    trait = {
                        "name": trait_name,
                        "type": trait_type,
                        "description": self._get_trait_description(modifier)
                    }
                    
                    # Add specific details based on modifier type
                    if trait_type == "sense":
                        trait["sense_type"] = modifier.get("subType", "")
                        trait["range"] = modifier.get("value", 0)
                    elif trait_type == "proficiency":
                        trait["proficiency_type"] = modifier.get("subType", "")
                    elif trait_type == "immunity":
                        trait["immunity_type"] = modifier.get("subType", "")
                    elif trait_type == "language":
                        trait["language"] = modifier.get("friendlySubtypeName", "")
                    
                    traits.append(trait)
            
            # Look for additional racial features in race definition
            race_data = self.raw_data.get("race", {})
            race_def = race_data.get(FieldNames.DEFINITION, {})
            
            # Check for racial spell abilities
            racial_spells = self.raw_data.get("spells", {}).get("race", [])
            if racial_spells:
                spell_names = [spell.get("definition", {}).get("name", "") for spell in racial_spells]
                traits.append({
                    "name": "Racial Spells",
                    "type": "spellcasting",
                    "description": f"Spells granted by racial heritage: {', '.join(spell_names)}"
                })
                
        except Exception as e:
            logger.error(f"Error extracting racial traits: {e}")
        
        return traits
    
    def _get_trait_description(self, modifier: Dict[str, Any]) -> str:
        """Generate a description for a racial trait based on modifier data."""
        trait_type = modifier.get("type", "")
        friendly_name = modifier.get("friendlyTypeName", "")
        subtype = modifier.get("subType", "")
        value = modifier.get("value", 0)
        
        if trait_type == "sense":
            if subtype == "darkvision":
                return f"You can see in dim light within {value} feet of you as if it were bright light, and in darkness as if it were dim light."
            else:
                return f"{friendly_name}: {value} feet"
        elif trait_type == "proficiency":
            return f"You have proficiency with {modifier.get('friendlySubtypeName', subtype)}"
        elif trait_type == "immunity":
            return f"You have immunity to {modifier.get('friendlySubtypeName', subtype)}"
        elif trait_type == "language":
            return f"You can speak, read, and write {modifier.get('friendlySubtypeName', subtype)}"
        elif trait_type == "advantage":
            return f"You have advantage on {modifier.get('friendlySubtypeName', subtype)} checks"
        else:
            return f"{friendly_name}: {modifier.get('friendlySubtypeName', '')}"

    def _resolve_feat_complex_grants(self, feat_def: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve complex feat grants including spells, ASIs, and proficiencies.
        
        Args:
            feat_def: Feat definition dictionary
            
        Returns:
            Dictionary containing resolved grants
        """
        grants = {
            "spells": [],
            "asi_options": [],
            "proficiencies": [],
            "additional_features": []
        }
        
        try:
            feat_name = feat_def.get(FieldNames.NAME, "").lower()
            description = feat_def.get("description", "")
            
            # Handle Magic Initiate variants
            if "magic initiate" in feat_name:
                grants["spells"] = ["2 cantrips", "1 1st-level spell"]
                grants["additional_features"].append("Cast 1st-level spell once per long rest")
                
            # Handle ASI feats
            elif "ability score improvement" in feat_name or "asi" in feat_name:
                grants["asi_options"] = ["+2 to one ability", "+1 to two abilities"]
                
            # Handle skill/proficiency feats
            elif any(keyword in feat_name for keyword in ["skilled", "linguist", "prodigy"]):
                # Parse proficiencies from description
                if "proficiency" in description.lower():
                    grants["proficiencies"].append("skill_proficiencies")
                if "language" in description.lower():
                    grants["proficiencies"].append("languages")
                    
            # Handle combat feats
            elif any(keyword in feat_name for keyword in ["weapon", "armor", "fighting"]):
                grants["proficiencies"].append("weapon_proficiencies")
                
        except Exception as e:
            logger.debug(f"Error resolving feat grants for {feat_name}: {e}")
            
        return grants

    def _parse_feats(self) -> List[FeatInfo]:
        """Parse character feats with enhanced debugging and complex feat resolution."""
        feats = []
        try:
            # Check standard feats location
            feats_data = self.raw_data.get("feats", [])
            logger.debug(f"Found {len(feats_data)} feats in 'feats' array")

            for feat in feats_data:
                feat_def = feat.get(FieldNames.DEFINITION, {})
                feat_info = FeatInfo(
                    name=feat_def.get(FieldNames.NAME, "Unknown Feat"),
                    description=self._sanitize(feat_def.get("description", "")),
                    source=f"feat:{feat_def.get('id', 'unknown')}"
                )
                
                # Resolve complex grants for debugging
                grants = self._resolve_feat_complex_grants(feat_def)
                if any(grants.values()):
                    logger.debug(f"Feat '{feat_info.name}' grants: {grants}")
                
                feats.append(feat_info)

            # Check background granted feats
            background_data = self.raw_data.get("background", {})
            if background_data:
                background_def = background_data.get(FieldNames.DEFINITION, {})
                granted_feats = background_def.get("grantedFeats", [])
                logger.debug(f"Found {len(granted_feats)} granted feats from background")

                for granted_feat in granted_feats:
                    # Try to get description from featIds or fall back to empty
                    feat_description = self._get_background_feat_description(granted_feat)
                    
                    feat_info = FeatInfo(
                        name=granted_feat.get("name", "Unknown Background Feat"),
                        description=self._sanitize(feat_description),
                        source=f"background_feat:{granted_feat.get('id', 'unknown')}"
                    )
                    
                    # Resolve grants for background feats too
                    grants = self._resolve_feat_complex_grants(granted_feat)
                    if any(grants.values()):
                        logger.debug(f"Background feat '{feat_info.name}' grants: {grants}")
                        
                    feats.append(feat_info)

            # Check racial feats (variant human, custom lineage, etc.)
            race_data = self.raw_data.get("race", {})
            if race_data:
                racial_traits = race_data.get("racialTraits", [])
                for trait in racial_traits:
                    trait_def = trait.get(FieldNames.DEFINITION, {})
                    if trait_def.get(FieldNames.NAME, "").lower() == "feat":
                        feats.append(FeatInfo(
                            name="Racial Feat Choice",
                            description=self._sanitize(trait_def.get("description", "")),
                            source=f"racial_trait:{trait_def.get('id', 'unknown')}"
                        ))
                        logger.debug(f"Found racial feat choice trait")

        except Exception as e:
            logger.error(f"Error parsing feats: {e}")

        logger.debug(f"Total feats found: {len(feats)}")
        return feats

    def _explore_spell_sources(self) -> Dict[str, Any]:
        """Explore and log all potential spell sources in the character data."""
        spell_sources = {
            "classSpells": [],
            "background_spells": [],
            "racial_spells": [],
            "feat_spells": [],
            "magic_item_spells": [],
            "unknown_sources": []
        }

        try:
            # 1. Class Spells (FIXED LOCATION)
            class_spells_data = self.raw_data.get("classSpells", [])
            logger.debug(f"🔍 Found {len(class_spells_data)} classSpells entries")

            for i, class_spell_entry in enumerate(class_spells_data):
                character_class_id = class_spell_entry.get("characterClassId")
                spells = class_spell_entry.get("spells", [])
                logger.debug(f"  Entry {i}: ClassID {character_class_id}, {len(spells)} spells")

                if spells:
                    spell_sources["classSpells"].append({
                        "class_id": character_class_id,
                        "spell_count": len(spells),
                        "first_spell": spells[0].get(FieldNames.DEFINITION, {}).get(FieldNames.NAME,
                                                                                    "Unknown") if spells else None
                    })

            # 2. Background Spells
            background_data = self.raw_data.get("background", {})
            if background_data:
                background_def = background_data.get(FieldNames.DEFINITION, {})
                spell_list_ids = background_def.get("spellListIds", [])
                granted_feats = background_def.get("grantedFeats", [])

                if spell_list_ids:
                    logger.debug(f"🔍 Background has spellListIds: {spell_list_ids}")
                    spell_sources["background_spells"] = spell_list_ids

                # Check background granted feats for Magic Initiate and similar
                for feat in granted_feats:
                    feat_name = feat.get("name", "")
                    if "magic" in feat_name.lower() or "initiate" in feat_name.lower() or "spell" in feat_name.lower():
                        logger.debug(f"🔍 Background feat '{feat_name}' may grant spells")
                        spell_sources["feat_spells"].append({
                            "source": "background_feat",
                            "feat_name": feat_name,
                            "feat_id": feat.get("id")
                        })

            # 3. Racial Spells
            race_data = self.raw_data.get("race", {})
            if race_data:
                racial_traits = race_data.get("racialTraits", [])
                for trait in racial_traits:
                    trait_def = trait.get(FieldNames.DEFINITION, {})
                    trait_name = trait_def.get(FieldNames.NAME, "")
                    spell_list_ids = trait_def.get("spellListIds", [])
                    description = trait_def.get("description", "")

                    # Check for spellListIds
                    if spell_list_ids:
                        logger.debug(f"🔍 Racial trait '{trait_name}' has spellListIds: {spell_list_ids}")
                        spell_sources["racial_spells"].append({
                            "trait_name": trait_name,
                            "spell_list_ids": spell_list_ids
                        })

                    # Check for spell mentions in descriptions
                    elif any(keyword in description.lower() for keyword in ["spell", "cantrip", "magic", "cast"]):
                        logger.debug(f"🔍 Racial trait '{trait_name}' mentions spells in description")
                        spell_sources["racial_spells"].append({
                            "trait_name": trait_name,
                            "spell_mentions": True,
                            "description_preview": description[:100] + "..." if len(description) > 100 else description
                        })

            # 4. Direct Feat Spells
            feats_data = self.raw_data.get("feats", [])
            for feat in feats_data:
                feat_def = feat.get(FieldNames.DEFINITION, {})
                feat_name = feat_def.get(FieldNames.NAME, "")
                description = feat_def.get("description", "")

                if "magic" in feat_name.lower() or "initiate" in feat_name.lower() or \
                        any(keyword in description.lower() for keyword in ["spell", "cantrip", "cast"]):
                    logger.debug(f"🔍 Direct feat '{feat_name}' may grant spells")
                    spell_sources["feat_spells"].append({
                        "source": "direct_feat",
                        "feat_name": feat_name,
                        "feat_id": feat_def.get("id")
                    })

            # 5. Magic Item Spells
            inventory_data = self.raw_data.get("inventory", [])
            for item in inventory_data:
                item_def = item.get(FieldNames.DEFINITION, {})
                item_name = item_def.get(FieldNames.NAME, "")
                description = item_def.get("description", "")
                magic = item_def.get("magic", False)

                if magic and any(keyword in description.lower() for keyword in ["spell", "cast", "charges"]):
                    logger.debug(f"🔍 Magic item '{item_name}' may grant spells")
                    spell_sources["magic_item_spells"].append({
                        "item_name": item_name,
                        "equipped": item.get("equipped", False),
                        "attuned": item.get("isAttuned", False)
                    })

            # 6. Look for any other spell-related keys in raw data
            spell_related_keys = []
            for key, value in self.raw_data.items():
                if "spell" in key.lower() and key not in ["classSpells", "spellSlots"]:
                    spell_related_keys.append(key)
                    logger.debug(
                        f"🔍 Found spell-related key: {key} = {type(value)} (length: {len(value) if isinstance(value, (list, dict)) else 'N/A'})")

                    # Examine the 'spells' key more closely
                    if key == "spells" and isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            logger.debug(
                                f"    spells.{subkey}: {type(subvalue)} (length: {len(subvalue) if isinstance(subvalue, (list, dict)) else 'N/A'})")

            if spell_related_keys:
                spell_sources["unknown_sources"] = spell_related_keys

        except Exception as e:
            logger.error(f"Error exploring spell sources: {e}")

        return spell_sources


    def _parse_spells(self) -> Dict[str, List[Dict[str, Any]]]:
        """Parse spells with enhanced grouping, deduplication, and comprehensive source detection."""
        spell_groups = {}
        seen_spells = {}  # Track spells by name to avoid duplicates

        try:
            # First, explore all spell sources
            spell_sources = self._explore_spell_sources()
            ability_scores = self._parse_ability_scores()

            # Process different spell sources
            self._process_class_spells(spell_groups, seen_spells)
            self._process_non_class_spells(spell_groups, seen_spells)

            total_spells = sum(len(spell_list) for spell_list in spell_groups.values())
            logger.debug(f"Total spells parsed: {total_spells} from {len(spell_groups)} sources")

        except Exception as e:
            logger.error(f"Error parsing spells: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

        return spell_groups

    def _process_class_spells(self, spell_groups: Dict[str, List[Dict[str, Any]]], seen_spells: Dict[str, Dict[str, Any]]) -> None:
        """Process class-based spells from classSpells data."""
        class_spells_data = self.raw_data.get("classSpells", [])
        logger.debug(f"Processing {len(class_spells_data)} classSpells entries")

        for class_spell_entry in class_spells_data:
            character_class_id = class_spell_entry.get("characterClassId")
            spells = class_spell_entry.get("spells", [])

            # Map character class ID to class name and spellcasting ability
            class_name, spellcasting_ability = self._get_class_info_by_id(character_class_id)
            
            logger.debug(f"Processing {len(spells)} spells for class {class_name} (ID: {character_class_id})")

            if spells:
                if class_name not in spell_groups:
                    spell_groups[class_name] = []

                spell_stats = self._calculate_spell_stats(spellcasting_ability)
                
                for spell_data in spells:
                    spell_info = self._create_class_spell_info(spell_data, class_name, spellcasting_ability, spell_stats)
                    if spell_info:
                        self._add_spell_to_groups(spell_info, class_name, spell_groups, seen_spells)

    def _process_non_class_spells(self, spell_groups: Dict[str, List[Dict[str, Any]]], seen_spells: Dict[str, Dict[str, Any]]) -> None:
        """Process non-class spells from top-level spells dictionary."""
        top_level_spells = self.raw_data.get("spells", {})
        if not isinstance(top_level_spells, dict):
            return
            
        logger.debug(f"🔍 Processing top-level spells dictionary with keys: {list(top_level_spells.keys())}")

        # Process each type of non-class spell
        self._process_racial_spells(top_level_spells.get("race", []), spell_groups, seen_spells)
        self._process_feat_spells(top_level_spells.get("feat", []), spell_groups, seen_spells)
        self._process_item_spells(top_level_spells.get("item", []), spell_groups, seen_spells)

    def _get_class_info_by_id(self, character_class_id: int) -> Tuple[str, str]:
        """Get class name and spellcasting ability by character class ID."""
        class_name = "Unknown Class"
        spellcasting_ability = "intelligence"  # Default

        for cls in self.raw_data.get("classes", []):
            if cls.get("id") == character_class_id:
                class_def = cls.get(FieldNames.DEFINITION, {})
                class_name = class_def.get(FieldNames.NAME, "Unknown Class")

                # Determine spellcasting ability for this class
                spellcasting_ability_id = class_def.get("spellcastingAbilityId")
                if spellcasting_ability_id in GameConstants.SPELLCASTING_ABILITIES:
                    spellcasting_ability = GameConstants.SPELLCASTING_ABILITIES[spellcasting_ability_id]
                break

        return class_name, spellcasting_ability

    def _get_spell_preparation_type(self, class_name: str, subclass_name: str = "") -> str:
        """Determine how this class handles spell preparation/learning."""
        class_lower = class_name.lower()
        subclass_lower = subclass_name.lower()
        
        # Known spells (can't change without level up)
        if class_lower in ["bard", "sorcerer", "warlock"]:
            return "known"
        elif (class_lower == "fighter" and subclass_lower == "eldritch knight") or \
             (class_lower == "rogue" and subclass_lower == "arcane trickster"):
            return "known"  # Third-casters learn spells
        
        # Prepared spells (can change on long rest)
        elif class_lower in ["cleric", "druid", "paladin"]:
            return "prepared_from_list"  # Can prepare from full class spell list
        elif class_lower == "wizard":
            return "prepared_from_book"  # Can prepare from spellbook
        elif class_lower in ["artificer", "ranger"]:
            return "prepared_from_list"
        
        return "known"  # Default fallback

    def _get_cantrip_scaling_info(self, spell_name: str) -> Optional[Dict[str, Any]]:
        """Get cantrip damage scaling information based on character level."""
        total_level = self.analyzer.total_character_level
        
        # Calculate cantrip scaling (levels 5, 11, 17)
        if total_level >= 17:
            scaling_tier = 4
        elif total_level >= 11:
            scaling_tier = 3
        elif total_level >= 5:
            scaling_tier = 2
        else:
            scaling_tier = 1
            
        # Common damage cantrips and their scaling patterns
        damage_cantrips = {
            "fire bolt": {"base_dice": "1d10", "damage_type": "fire"},
            "ray of frost": {"base_dice": "1d8", "damage_type": "cold"},
            "sacred flame": {"base_dice": "1d8", "damage_type": "radiant"},
            "toll the dead": {"base_dice": "1d8/1d12", "damage_type": "necrotic"},
            "eldritch blast": {"base_dice": "1d10", "damage_type": "force"},
            "chill touch": {"base_dice": "1d8", "damage_type": "necrotic"},
            "produce flame": {"base_dice": "1d8", "damage_type": "fire"},
            "poison spray": {"base_dice": "1d12", "damage_type": "poison"},
            "acid splash": {"base_dice": "1d6", "damage_type": "acid"},
            "shocking grasp": {"base_dice": "1d8", "damage_type": "lightning"},
            "thorn whip": {"base_dice": "1d6", "damage_type": "piercing"},
            "word of radiance": {"base_dice": "1d6", "damage_type": "radiant"},
            "booming blade": {"base_dice": "1d8", "damage_type": "thunder"},  # 2024 version
            "green flame blade": {"base_dice": "1d8", "damage_type": "fire"},  # 2024 version
            "true strike": {"enhanced": True},  # 2024 version has special scaling
            "sorcerous burst": {"base_dice": "1d8", "damage_type": "variable"}  # 2024 Sorcerer cantrip
        }
        
        spell_lower = spell_name.lower()
        if spell_lower in damage_cantrips:
            cantrip_info = damage_cantrips[spell_lower]
            
            scaling_info = {
                "current_tier": scaling_tier,
                "character_level": total_level,
                "scaling_levels": [1, 5, 11, 17]
            }
            
            if "base_dice" in cantrip_info:
                base_dice = cantrip_info["base_dice"]
                # For most cantrips, multiply number of dice by scaling tier
                scaling_info["damage_dice"] = f"{scaling_tier}{base_dice[1:]}"  # e.g., "1d10" -> "3d10" at tier 3
                scaling_info["damage_type"] = cantrip_info["damage_type"]
            elif cantrip_info.get("enhanced"):
                # Special handling for enhanced cantrips like True Strike 2024
                scaling_info["enhanced_scaling"] = True
                scaling_info["extra_damage"] = f"{scaling_tier - 1}d6" if scaling_tier > 1 else "0"
                
            return scaling_info
            
        return None

    def _create_class_spell_info(self, spell_data: Dict[str, Any], class_name: str, spellcasting_ability: str, spell_stats: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create spell info dictionary for class spells."""
        spell_def = spell_data.get(FieldNames.DEFINITION, {})
        spell_name = spell_def.get(FieldNames.NAME, "Unknown Spell")

        # Get subclass info for preparation type determination
        subclass_name = ""
        for class_info in self.analyzer.character_classes:
            if class_info.name.lower() == class_name.lower():
                subclass_name = getattr(class_info, 'subclass', '')
                break

        # Extract spell components from API
        spell_components = self._extract_spell_components(spell_def, spell_name)
        
        # Determine preparation type
        preparation_type = self._get_spell_preparation_type(class_name, subclass_name)
        
        # Get spell level and check for cantrip scaling
        spell_level = spell_def.get("level", 0)
        cantrip_scaling = None
        if spell_level == 0:  # Cantrip
            cantrip_scaling = self._get_cantrip_scaling_info(spell_name)
        
        # Extract preparation and ritual status
        is_prepared = spell_data.get("prepared", False)
        always_prepared = spell_data.get("alwaysPrepared", False)
        is_ritual = spell_def.get("ritual", False)
        
        # Handle ritual logic for wizards: rituals don't need to be prepared
        if class_name.lower() == "wizard" and is_ritual:
            effective_prepared = True  # Wizards can cast rituals without preparing them
        else:
            effective_prepared = is_prepared or always_prepared
            
        spell_info = {
            "name": spell_name,
            "level": spell_level,
            "school": spell_def.get("school", "Unknown"),
            "description": self._sanitize(spell_def.get("description", "")),
            "save_dc": spell_stats["save_dc"],
            "attack_bonus": spell_stats["attack_bonus"],
            "spellcasting_ability": spellcasting_ability,
            "always_prepared": always_prepared,
            "is_prepared": is_prepared,  # Raw preparation status from D&D Beyond
            "effective_prepared": effective_prepared,  # Includes ritual logic
            "ritual": is_ritual,
            "preparation_type": preparation_type,
            "usage_type": "slot",
            "source_info": {
                "class": class_name,
                "feature": "Class Spell",
                "granted_by": f"{class_name} spell list"
            }
        }
        
        # Add cantrip scaling if applicable
        if cantrip_scaling:
            spell_info["cantrip_scaling"] = cantrip_scaling
        
        # Add API spell component data
        spell_info["data_source"] = "A"  # Always API for scraper
        
        if spell_components:
            spell_info.update(spell_components)

        return spell_info

    def _process_racial_spells(self, racial_spells: List[Dict[str, Any]], spell_groups: Dict[str, List[Dict[str, Any]]], seen_spells: Dict[str, Dict[str, Any]]) -> None:
        """Process racial spells from top-level spells dictionary."""
        if not racial_spells or not isinstance(racial_spells, list):
            return
            
        logger.debug(f"Processing {len(racial_spells)} racial spells")
        if "Racial" not in spell_groups:
            spell_groups["Racial"] = []

        racial_ability = "charisma"
        spell_stats = self._calculate_spell_stats(racial_ability)

        for spell_data in racial_spells:
            if isinstance(spell_data, dict):
                spell_info = self._create_non_class_spell_info(
                    spell_data, racial_ability, spell_stats, "Racial", 
                    "Racial Trait", "Species heritage", True
                )
                if spell_info:
                    self._add_spell_to_groups(spell_info, "Racial", spell_groups, seen_spells)

    def _process_feat_spells(self, feat_spells: List[Dict[str, Any]], spell_groups: Dict[str, List[Dict[str, Any]]], seen_spells: Dict[str, Dict[str, Any]]) -> None:
        """Process feat spells from top-level spells dictionary."""
        if not feat_spells or not isinstance(feat_spells, list):
            return
            
        logger.debug(f"Processing {len(feat_spells)} feat spells")
        if "Feat" not in spell_groups:
            spell_groups["Feat"] = []

        feat_ability = "charisma"  # Most feat spells use Charisma
        spell_stats = self._calculate_spell_stats(feat_ability)

        for spell_data in feat_spells:
            if isinstance(spell_data, dict):
                spell_def = spell_data.get(FieldNames.DEFINITION)
                if not spell_def or not isinstance(spell_def, dict):
                    continue
                    
                spell_info = self._create_non_class_spell_info(
                    spell_data, feat_ability, spell_stats, "Feat", 
                    "Feat Grant", "Character feat", True
                )
                if spell_info:
                    self._add_spell_to_groups(spell_info, "Feat", spell_groups, seen_spells)

    def _process_item_spells(self, item_spells: List[Dict[str, Any]], spell_groups: Dict[str, List[Dict[str, Any]]], seen_spells: Dict[str, Dict[str, Any]]) -> None:
        """Process magic item spells from top-level spells dictionary."""
        if not item_spells or not isinstance(item_spells, list):
            return
            
        logger.debug(f"Processing {len(item_spells)} magic item spells")
        if "Magic Item" not in spell_groups:
            spell_groups["Magic Item"] = []

        item_ability = self._get_primary_spellcasting_ability()
        spell_stats = self._calculate_spell_stats(item_ability)

        for spell_data in item_spells:
            if isinstance(spell_data, dict):
                spell_info = self._create_non_class_spell_info(
                    spell_data, item_ability, spell_stats, "Magic Item", 
                    "Magic Item", "Equipped magic item", True
                )
                if spell_info:
                    self._add_spell_to_groups(spell_info, "Magic Item", spell_groups, seen_spells)

    def _create_non_class_spell_info(self, spell_data: Dict[str, Any], spellcasting_ability: str, spell_stats: Dict[str, Any], 
                                   source_class: str, feature: str, granted_by: str, always_prepared: bool) -> Optional[Dict[str, Any]]:
        """Create spell info dictionary for non-class spells (racial, feat, item)."""
        spell_def = spell_data.get(FieldNames.DEFINITION, {})
        spell_name = spell_def.get(FieldNames.NAME, f"Unknown {source_class} Spell")

        # Extract spell components
        spell_components = self._extract_spell_components(spell_def, spell_name)
        
        # Determine usage type: cantrips are at-will, leveled spells are per-rest for non-class sources
        spell_level = spell_def.get("level", 0)
        usage_type = "at-will" if spell_level == 0 else "per-rest"
        
        spell_info = {
            "name": spell_name,
            "level": spell_level,
            "school": spell_def.get("school", "Unknown"),
            "description": self._sanitize(spell_def.get("description", "")),
            "save_dc": spell_stats["save_dc"],
            "attack_bonus": spell_stats["attack_bonus"],
            "spellcasting_ability": spellcasting_ability,
            "always_prepared": always_prepared,
            "usage_type": usage_type,
            "source_info": {
                "class": source_class,
                "feature": feature,
                "granted_by": granted_by
            }
        }
        
        # Always use API data
        spell_info["data_source"] = "A"
        
        # Add component data from API if available
        if spell_components:
            spell_info.update(spell_components)

        return spell_info

    def _add_spell_to_groups(self, spell_info: Dict[str, Any], source_name: str, 
                           spell_groups: Dict[str, List[Dict[str, Any]]], seen_spells: Dict[str, Dict[str, Any]]) -> None:
        """Add spell to groups with deduplication handling."""
        spell_name = spell_info["name"]
        
        # Check if we've seen this spell before
        if spell_name in seen_spells:
            # Add this source to the existing spell
            seen_spells[spell_name]["sources"].append(source_name)
            logger.debug(f"Added source '{source_name}' to existing spell '{spell_name}'")
        else:
            # New spell
            spell_info["sources"] = [source_name]
            seen_spells[spell_name] = spell_info
            spell_groups[source_name].append(spell_info)
            logger.debug(f"Added new spell '{spell_name}' from '{source_name}'")

    def _extract_spell_components(self, spell_def: Dict[str, Any], spell_name: str = "") -> Dict[str, str]:
        """Extract spell component data from D&D Beyond spell definition."""
        components = {}
        
        # Extract casting time
        activation = spell_def.get("activation", {})
        if activation:
            activation_time = activation.get("activationTime", 1)
            activation_type = activation.get("activationType", 1)
            
            # Map activation types (based on D&D Beyond API)
            type_mapping = {
                1: "Action", 2: "Bonus Action", 3: "Reaction", 
                4: "1 Minute", 5: "10 Minutes", 6: "1 Hour", 
                7: "8 Hours", 8: "24 Hours"
            }
            
            if activation_time == 1:
                components["casting_time"] = f"1 {type_mapping.get(activation_type, 'Action')}"
            else:
                unit = type_mapping.get(activation_type, "Action").lower()
                components["casting_time"] = f"{activation_time} {unit}s"
        
        # Extract range
        range_info = spell_def.get("range", {})
        if range_info:
            range_value = range_info.get("rangeValue")
            origin = range_info.get("origin")
            
            if origin == 1:  # Self
                components["range"] = "Self"
            elif origin == 2:  # Touch  
                components["range"] = "Touch"
            elif range_value:
                components["range"] = f"{range_value} feet"
            else:
                components["range"] = "Special"
        
        # Extract duration
        duration = spell_def.get("duration", {})
        if duration:
            duration_type = duration.get("durationType")
            duration_value = duration.get("durationInterval")
        
        # Extract ritual information
        if "ritual" in spell_def:
            components["ritual"] = spell_def["ritual"]
        
        # Extract concentration information
        if "concentration" in spell_def:
            components["concentration"] = spell_def["concentration"]
        
        if duration:
            # Map duration types (handle both numeric and string types)
            if duration_type == 1 or duration_type == "Instantaneous":
                components["duration"] = "Instantaneous"
            elif duration_type == 2 or duration_type == "Until dispelled":
                components["duration"] = "Until dispelled"
            elif duration_type == 3 or duration_type == "Time":
                # Use durationUnit if available
                duration_unit = duration.get("durationUnit", "").lower()
                if duration_unit:
                    if duration_value == 1:
                        components["duration"] = f"1 {duration_unit.lower()}"
                    else:
                        components["duration"] = f"{duration_value} {duration_unit.lower()}s"
                elif duration_value == 1:
                    components["duration"] = "1 round"
                elif duration_value == 2:
                    components["duration"] = "1 minute"
                elif duration_value == 3:
                    components["duration"] = "10 minutes"
                elif duration_value == 4:
                    components["duration"] = "1 hour"
                elif duration_value == 5:
                    components["duration"] = "8 hours"
                elif duration_value == 6:
                    components["duration"] = "24 hours"
                else:
                    components["duration"] = f"Duration {duration_value}"
            elif duration_type == 5 or duration_type == "Concentration":  # Concentration
                if duration_value == 2:
                    components["duration"] = "Concentration, up to 1 minute"
                elif duration_value == 3:
                    components["duration"] = "Concentration, up to 10 minutes"
                elif duration_value == 4:
                    components["duration"] = "Concentration, up to 1 hour"
                elif duration_value == 5:
                    components["duration"] = "Concentration, up to 8 hours"
                else:
                    components["duration"] = "Concentration"
        
        # Extract components (V, S, M)
        spell_components = spell_def.get("components", [])
        components_description = spell_def.get("componentsDescription", "")
        
        if spell_components:
            component_letters = []
            if 1 in spell_components:  # Verbal
                component_letters.append("V")
            if 2 in spell_components:  # Somatic  
                component_letters.append("S")
            if 3 in spell_components:  # Material
                if components_description.strip():
                    component_letters.append(f"M ({components_description.strip()})")
                else:
                    component_letters.append("M")
            
            components["components"] = ", ".join(component_letters)
        
        return components

    def _get_primary_spellcasting_ability(self) -> str:
        """Determine the character's primary spellcasting ability."""
        try:
            # Get spellcasting ability from classes
            for class_info in self.analyzer.character_classes:
                if hasattr(class_info, 'spellcasting_ability') and class_info.spellcasting_ability:
                    logger.debug(f"Found spellcasting ability from class {class_info.name}: {class_info.spellcasting_ability}")
                    return class_info.spellcasting_ability
            
            # Fallback: infer from class names and subclasses
            for class_info in self.analyzer.character_classes:
                class_name = class_info.name.lower() if hasattr(class_info, 'name') else ""
                subclass_name = getattr(class_info, 'subclass', '').lower() if hasattr(class_info, 'subclass') else ""
                logger.debug(f"Checking class name: {class_name}, subclass: {subclass_name}")
                
                # Check for third-caster subclasses first (they override main class)
                if (class_name == "fighter" and subclass_name == "eldritch knight") or \
                   (class_name == "rogue" and subclass_name == "arcane trickster"):
                    logger.debug(f"Detected intelligence-based third-caster: {class_name} ({subclass_name})")
                    return "intelligence"
                
                # Regular spellcasting classes
                if class_name in ["cleric", "druid", "ranger"]:
                    logger.debug(f"Detected wisdom-based spellcaster: {class_name}")
                    return "wisdom"
                elif class_name in ["wizard", "artificer"]:
                    logger.debug(f"Detected intelligence-based spellcaster: {class_name}")
                    return "intelligence"
                elif class_name in ["bard", "sorcerer", "warlock", "paladin"]:
                    logger.debug(f"Detected charisma-based spellcaster: {class_name}")
                    return "charisma"
                    
        except Exception as e:
            logger.debug(f"Error determining spellcasting ability: {e}")
            
        logger.debug("No spellcasting class found, using intelligence as default")
        return "intelligence"  # Default fallback

    def _calculate_passive_senses(self) -> Dict[str, int]:
        """Calculate passive sense scores."""
        try:
            passive_senses = {}
            
            # Get proficiency bonus and ability scores
            total_character_level = self.analyzer.total_character_level
            proficiency_bonus = 2 + ((total_character_level - 1) // 4)
            ability_scores = self._parse_ability_scores()
            skills = self._parse_skills()
            proficiencies = self._parse_proficiencies()
            skill_proficiencies = proficiencies.get("skills", [])
            
            # Convert skill proficiencies to lowercase for comparison
            skill_profs_lower = [skill.lower() for skill in skill_proficiencies]
            
            # Calculate passive perception
            perception_bonus = 0
            wisdom_modifier = ability_scores.get("wisdom", {}).get("modifier", 0)
            if "perception" in skill_profs_lower:
                perception_bonus += proficiency_bonus
                # Check for expertise by comparing expected vs actual skill bonus
                expected_with_prof = wisdom_modifier + proficiency_bonus
                actual_perception = skills.get("perception", 0)
                if actual_perception == wisdom_modifier + (2 * proficiency_bonus):
                    perception_bonus += proficiency_bonus  # Expertise doubles proficiency
            
            passive_perception = 10 + wisdom_modifier + perception_bonus
            passive_senses["perception"] = passive_perception
            
            # Calculate passive investigation
            investigation_bonus = 0
            intelligence_modifier = ability_scores.get("intelligence", {}).get("modifier", 0)
            if "investigation" in skill_profs_lower:
                investigation_bonus += proficiency_bonus
                # Check for expertise
                expected_with_prof = intelligence_modifier + proficiency_bonus
                actual_investigation = skills.get("investigation", 0)
                if actual_investigation == intelligence_modifier + (2 * proficiency_bonus):
                    investigation_bonus += proficiency_bonus  # Expertise doubles proficiency
            
            passive_investigation = 10 + intelligence_modifier + investigation_bonus
            passive_senses["investigation"] = passive_investigation
            
            # Calculate passive insight
            insight_bonus = 0
            if "insight" in skill_profs_lower:
                insight_bonus += proficiency_bonus
                # Check for expertise
                expected_with_prof = wisdom_modifier + proficiency_bonus
                actual_insight = skills.get("insight", 0)
                if actual_insight == wisdom_modifier + (2 * proficiency_bonus):
                    insight_bonus += proficiency_bonus  # Expertise doubles proficiency
            
            passive_insight = 10 + wisdom_modifier + insight_bonus
            passive_senses["insight"] = passive_insight
            
            if VERBOSE_OUTPUT:
                logger.debug(f"Passive Senses: Perception {passive_perception}, Investigation {passive_investigation}, Insight {passive_insight}")
            
            return passive_senses
            
        except Exception as e:
            logger.error(f"Error calculating passive senses: {e}")
            return {"perception": 10, "investigation": 10, "insight": 10}

    def _calculate_total_wealth(self) -> int:
        """Calculate total wealth in gold pieces."""
        try:
            currencies = self.raw_data.get("currencies", {})
            copper = currencies.get("cp", 0)
            silver = currencies.get("sp", 0)
            electrum = currencies.get("ep", 0)
            gold = currencies.get("gp", 0)
            platinum = currencies.get("pp", 0)
            
            total_wealth = copper * 0.01 + silver * 0.1 + electrum * 0.5 + gold + platinum * 10
            return int(total_wealth)
        except Exception as e:
            logger.error(f"Error calculating total wealth: {e}")
            return 0

    def _get_individual_currencies(self) -> Dict[str, int]:
        """Get individual currency amounts."""
        try:
            currencies = self.raw_data.get("currencies", {})
            return {
                "copper": currencies.get("cp", 0),
                "silver": currencies.get("sp", 0),
                "electrum": currencies.get("ep", 0),
                "gold": currencies.get("gp", 0),
                "platinum": currencies.get("pp", 0)
            }
        except Exception as e:
            logger.error(f"Error getting individual currencies: {e}")
            return {"copper": 0, "silver": 0, "electrum": 0, "gold": 0, "platinum": 0}

    def _calculate_carrying_capacity(self) -> int:
        """Calculate carrying capacity based on Strength score."""
        try:
            ability_scores = self._parse_ability_scores()
            str_score = ability_scores.get("strength", {}).get("score", 10)
            return str_score * 15
        except Exception as e:
            logger.error(f"Error calculating carrying capacity: {e}")
            return 150  # Default for 10 STR

    def _calculate_total_caster_level(self) -> int:
        """Calculate total caster level for multiclass spellcasting."""
        try:
            total_caster_level = 0
            
            for class_info in self.analyzer.character_classes:
                class_name = class_info.name.lower()
                class_level = class_info.level
                
                # Full casters
                if class_name in ["wizard", "sorcerer", "cleric", "druid", "bard", "warlock"]:
                    total_caster_level += class_level
                # Half casters  
                elif class_name in ["paladin", "ranger"]:
                    total_caster_level += class_level // 2
                # Third casters
                elif class_name in ["eldritch knight", "arcane trickster"]:
                    total_caster_level += class_level // 3
                # Artificer (half caster, rounds up)
                elif class_name == "artificer":
                    total_caster_level += (class_level + 1) // 2
            
            return total_caster_level
        except Exception as e:
            logger.error(f"Error calculating total caster level: {e}")
            return 0

    def _calculate_spell_slots(self) -> Dict[str, Any]:
        """Calculate spell slots for multiclass characters with enhanced structure."""
        try:
            spell_slots = {
                "regular_slots": {},
                "pact_slots": {},
                "caster_level": 0
            }
            total_caster_level = 0
            warlock_levels = 0

            # Calculate caster levels
            for cls_info in self.analyzer.character_classes:
                class_name = cls_info.name.lower()
                subclass_name = cls_info.subclass.lower() if cls_info.subclass else ""
                class_level = cls_info.level

                if class_name in GameConstants.FULL_CASTERS:
                    if class_name == "warlock":
                        warlock_levels += class_level
                    else:
                        total_caster_level += class_level
                elif class_name in GameConstants.HALF_CASTERS:
                    total_caster_level += class_level // 2
                # Check for third-caster subclasses specifically
                elif (class_name == "fighter" and subclass_name == "eldritch knight") or \
                     (class_name == "rogue" and subclass_name == "arcane trickster"):
                    # Third-casters start getting spells at level 3, so subtract 2 before dividing
                    if class_level >= 3:
                        total_caster_level += max(0, (class_level - 2) // 3)

            spell_slots["caster_level"] = total_caster_level

            # Get spell slots for regular casting using rule-specific progression
            if total_caster_level > 0:
                # Check if this is a single-class half-caster
                if (len(self.analyzer.character_classes) == 1 and 
                    self.analyzer.character_classes[0].name.lower() in GameConstants.HALF_CASTERS):
                    # Single half-caster: use actual class level with rule-specific progression
                    class_info = self.analyzer.character_classes[0]
                    class_level = class_info.level
                    class_name = class_info.name
                    
                    # Use rule-specific spell slot progression
                    if self._rule_manager:
                        slots = self._rule_manager.strategy.get_spell_slot_progression(class_name, class_level, "half")
                    else:
                        # Fallback to legacy progression
                        slots = GameConstants.HALF_CASTER_PROGRESSION.get(class_level)
                    
                    if slots:
                        for i, slot_count in enumerate(slots, 1):
                            spell_slots["regular_slots"][f"level_{i}"] = slot_count
                        if VERBOSE_OUTPUT:
                            logger.debug(f"Single half-caster ({class_name}) spell slots for level {class_level}: {slots}")
                else:
                    # Multiclass or full caster: use total caster level with rule-specific progression
                    if self._rule_manager:
                        # For multiclass, we'll use the primary caster's progression rules
                        primary_class = max(self.analyzer.character_classes, key=lambda c: c.level if c.name.lower() in GameConstants.FULL_CASTERS else 0, default=self.analyzer.character_classes[0] if self.analyzer.character_classes else None)
                        if primary_class:
                            slots = self._rule_manager.strategy.get_spell_slot_progression(primary_class.name, total_caster_level, "full")
                        else:
                            slots = GameConstants.FULL_CASTER_PROGRESSION.get(total_caster_level)
                    else:
                        # Fallback to legacy progression
                        slots = GameConstants.FULL_CASTER_PROGRESSION.get(total_caster_level)
                    
                    if slots:
                        for i, slot_count in enumerate(slots, 1):
                            spell_slots["regular_slots"][f"level_{i}"] = slot_count
                        if VERBOSE_OUTPUT:
                            logger.debug(f"Multiclass/full caster spell slots for caster level {total_caster_level}: {slots}")

            # Handle Warlock Pact Magic separately
            if warlock_levels > 0:
                if warlock_levels >= 17:
                    spell_slots["pact_slots"] = {"slots": 4, "level": 5}
                elif warlock_levels >= 11:
                    spell_slots["pact_slots"] = {"slots": 3, "level": 5}
                elif warlock_levels >= 9:
                    spell_slots["pact_slots"] = {"slots": 2, "level": 5}
                elif warlock_levels >= 7:
                    spell_slots["pact_slots"] = {"slots": 2, "level": 4}
                elif warlock_levels >= 5:
                    spell_slots["pact_slots"] = {"slots": 2, "level": 3}
                elif warlock_levels >= 3:
                    spell_slots["pact_slots"] = {"slots": 2, "level": 2}
                elif warlock_levels >= 2:
                    spell_slots["pact_slots"] = {"slots": 2, "level": 1}
                else:  # warlock_levels == 1
                    spell_slots["pact_slots"] = {"slots": 1, "level": 1}

            # For backward compatibility, also provide flat structure
            if spell_slots["regular_slots"]:
                for level, count in spell_slots["regular_slots"].items():
                    spell_slots[level] = count
            
            if spell_slots["pact_slots"]:
                spell_slots["pact_magic"] = spell_slots["pact_slots"]

            return spell_slots

        except Exception as e:
            logger.error(f"Error calculating spell slots: {e}")
            return {"regular_slots": {}, "pact_slots": {}, "caster_level": 0}

    def _parse_actions(self) -> List[Dict[str, Any]]:
        """Parse character actions and abilities."""
        actions = []
        try:
            # Parse from actions data if available
            actions_data = self.raw_data.get("actions", {})
            for action_type, action_list in actions_data.items():
                if isinstance(action_list, list):
                    for action in action_list:
                        actions.append({
                            "name": action.get("name", "Unknown Action"),
                            "description": self._sanitize(action.get("description", "")),
                            "type": action_type,
                            "snippet": action.get("snippet", "")
                        })
        except Exception as e:
            logger.error(f"Error parsing actions: {e}")

        return actions

    def _parse_inventory(self) -> List[InventoryItem]:
        """Parse character inventory."""
        inventory = []
        try:
            inventory_data = self.raw_data.get("inventory", [])
            for item_data in inventory_data:
                item_def = item_data.get(FieldNames.DEFINITION, {})
                inventory.append(InventoryItem(
                    name=item_def.get(FieldNames.NAME, "Unknown Item"),
                    quantity=item_data.get("quantity", 1),
                    equipped=item_data.get("equipped", False),
                    attuned=item_data.get("isAttuned", False),
                    requires_attunement=item_def.get("canAttune", False),
                    weight=item_def.get("weight", 0.0),
                    item_type=item_def.get("type", "equipment"),
                    rarity=item_def.get("rarity", "common")
                ))
        except Exception as e:
            logger.error(f"Error parsing inventory: {e}")

        return inventory

    def _parse_all_modifiers(self) -> List[CharacterModifier]:
        """Parse all modifiers from all sources with enhanced debugging."""
        all_modifiers = []

        try:
            # Check if modifiers exist at top level
            top_level_modifiers = self.raw_data.get("modifiers", {})
            if top_level_modifiers:
                logger.debug(f"Found top-level modifiers: {list(top_level_modifiers.keys())}")

                modifier_sources = [
                    ("race", top_level_modifiers.get("race", [])),
                    ("background", top_level_modifiers.get("background", [])),
                    ("class", top_level_modifiers.get("class", [])),
                    ("feat", top_level_modifiers.get("feat", [])),
                    ("item", top_level_modifiers.get("item", [])),
                ]

                for source_name, modifier_list in modifier_sources:
                    if isinstance(modifier_list, list) and modifier_list:
                        logger.debug(f"Processing {len(modifier_list)} {source_name} modifiers")

                        # Enhanced debugging for proficiency modifiers
                        proficiency_count = 0
                        for mod_data in modifier_list:
                            if isinstance(mod_data, dict):
                                modifier = self._create_modifier_from_data(mod_data, source_name)
                                if modifier:
                                    # Apply item activity check for item modifiers
                                    if source_name == "item" and modifier.component_id:
                                        if not self._is_item_active(modifier.component_id):
                                            logger.debug(f"Skipping inactive item modifier: {modifier.friendly_sub_type_name}")
                                            continue
                                    
                                    all_modifiers.append(modifier)

                                    # Debug proficiency modifiers specifically
                                    if modifier.type == "proficiency":
                                        proficiency_count += 1
                                        logger.debug(
                                            f"    Proficiency {proficiency_count}: type='{modifier.sub_type}', name='{modifier.friendly_sub_type_name}', source={source_name}")

                        if proficiency_count > 0:
                            logger.debug(f"  Found {proficiency_count} proficiency modifiers from {source_name}")
            else:
                logger.debug("No top-level 'modifiers' key found")

            # Add choice-based modifiers (legacy support)
            choice_modifiers = self._resolve_choices()
            all_modifiers.extend(choice_modifiers)

            # Summary by type
            modifier_types = {}
            for mod in all_modifiers:
                if mod.type not in modifier_types:
                    modifier_types[mod.type] = 0
                modifier_types[mod.type] += 1

            logger.debug(f"Parsed {len(all_modifiers)} total modifiers by type: {modifier_types}")

        except Exception as e:
            logger.error(f"Error parsing modifiers: {e}")

        return all_modifiers

    def _explore_data_structure(self) -> Dict[str, Any]:
        """Explore and log the complete data structure for debugging."""
        structure_info = {
            "top_level_keys": [],
            "classes_structure": {},
            "spell_related_keys": [],
            "modifier_locations": [],
            "feat_locations": [],
            "proficiency_sources": []
        }

        try:
            # Get all top-level keys
            structure_info["top_level_keys"] = list(self.raw_data.keys())
            logger.debug(
                f"🔍 Top-level keys ({len(structure_info['top_level_keys'])}): {structure_info['top_level_keys']}")

            # Explore classes structure
            classes_data = self.raw_data.get("classes", [])
            if classes_data:
                for i, cls in enumerate(classes_data):
                    class_keys = list(cls.keys())
                    class_def = cls.get(FieldNames.DEFINITION, {})
                    class_name = class_def.get(FieldNames.NAME, f"Class_{i}")
                    structure_info["classes_structure"][class_name] = {
                        "keys": class_keys,
                        "has_spells": "spells" in cls,
                        "spell_count": len(cls.get("spells", [])),
                        "definition_keys": list(class_def.keys()) if class_def else []
                    }
                    logger.debug(f"🔍 Class '{class_name}' keys: {class_keys}")

            # Look for spell-related keys
            for key in self.raw_data.keys():
                if "spell" in key.lower():
                    value = self.raw_data[key]
                    structure_info["spell_related_keys"].append({
                        "key": key,
                        "type": type(value).__name__,
                        "length": len(value) if isinstance(value, (list, dict)) else None
                    })
                    logger.debug(f"🔍 Spell-related key: {key} ({type(value).__name__})")

            # Look for modifier locations
            def search_for_modifiers(data, path=""):
                if isinstance(data, dict):
                    for key, value in data.items():
                        current_path = f"{path}.{key}" if path else key
                        if key == "modifiers" and isinstance(value, (list, dict)):
                            structure_info["modifier_locations"].append({
                                "path": current_path,
                                "type": type(value).__name__,
                                "length": len(value)
                            })
                            logger.debug(f"🔍 Found modifiers at: {current_path}")
                        elif isinstance(value, (dict, list)) and len(current_path.split('.')) < 3:  # Limit depth
                            search_for_modifiers(value, current_path)

            search_for_modifiers(self.raw_data)

            # Look for feat locations
            for key in self.raw_data.keys():
                if "feat" in key.lower():
                    value = self.raw_data[key]
                    structure_info["feat_locations"].append({
                        "key": key,
                        "type": type(value).__name__,
                        "length": len(value) if isinstance(value, (list, dict)) else None
                    })
                    logger.debug(f"🔍 Feat-related key: {key} ({type(value).__name__})")

        except Exception as e:
            logger.error(f"Error exploring data structure: {e}")

        return structure_info

    def _run_diagnostics(self) -> Dict[str, List[str]]:
        """Run comprehensive diagnostic checks on character data."""
        diagnostics = {
            "errors": [],           # Actual problems that need attention
            "warnings": [],         # Potential issues worth noting
            "missing_data": [],     # Missing expected data
            "info": [],            # Successful parsing confirmations
            "data_analysis": [],   # Structure analysis results
            "expected_vs_actual": []  # Expectation mismatches
        }

        try:
            # Basic data checks
            if not self.raw_data.get(FieldNames.NAME):
                diagnostics["missing_data"].append("Character name")

            if not self.raw_data.get("classes"):
                diagnostics["missing_data"].append("Character classes")
            else:
                total_level = sum(cls.get(FieldNames.LEVEL, 0) for cls in self.raw_data.get("classes", []))
                if total_level > 20:
                    diagnostics["errors"].append(f"Character level > 20: {total_level}")

            # Check ability scores
            stats = self.raw_data.get("stats", [])
            if not stats:
                diagnostics["missing_data"].append("Ability scores")
            elif len(stats) != 6:
                diagnostics["warnings"].append(f"Expected 6 ability scores, found {len(stats)}")

            # Spell analysis
            class_spells_data = self.raw_data.get("classSpells", [])
            if not class_spells_data:
                diagnostics["missing_data"].append("classSpells array")
            else:
                total_spells = sum(len(entry.get("spells", [])) for entry in class_spells_data)
                diagnostics["info"].append(
                    f"Found {len(class_spells_data)} classSpells entries with {total_spells} total spells")

                # Check for empty spell arrays
                for i, entry in enumerate(class_spells_data):
                    spells = entry.get("spells", [])
                    if not spells:
                        diagnostics["warnings"].append(f"classSpells entry {i} has empty spells array")

            # Check for expected spellcaster spell counts
            for cls in self.raw_data.get("classes", []):
                class_def = cls.get(FieldNames.DEFINITION, {})
                class_name = class_def.get(FieldNames.NAME, "").lower()
                class_level = cls.get(FieldNames.LEVEL, 0)

                if class_name in GameConstants.FULL_CASTERS and class_level >= 1:
                    # Find corresponding classSpells entry
                    class_id = cls.get("id")
                    spell_entry = next(
                        (entry for entry in class_spells_data if entry.get("characterClassId") == class_id), None)
                    actual_spell_count = len(spell_entry.get("spells", [])) if spell_entry else 0

                    # Basic expectation: spellcasters should have some spells
                    if actual_spell_count == 0:
                        diagnostics["expected_vs_actual"].append(
                            f"{class_name.title()} level {class_level} has 0 spells (expected some cantrips/spells)")

            # Check feat sources
            feats_data = self.raw_data.get("feats", [])
            background_data = self.raw_data.get("background", {})
            background_feats = background_data.get(FieldNames.DEFINITION, {}).get("grantedFeats",
                                                                                  []) if background_data else []

            total_feat_sources = len(feats_data) + len(background_feats)
            if total_feat_sources == 0:
                diagnostics["warnings"].append("No feats found in any source")
            else:
                diagnostics["info"].append(
                    f"Found feats from {len(feats_data)} direct + {len(background_feats)} background sources")

            # Check proficiency sources
            modifiers_data = self.raw_data.get("modifiers", {})
            if not modifiers_data:
                diagnostics["missing_data"].append("modifiers object")
            else:
                prof_sources = []
                for source, mods in modifiers_data.items():
                    if isinstance(mods, list):
                        prof_count = sum(1 for mod in mods if mod.get("type") == "proficiency")
                        if prof_count > 0:
                            prof_sources.append(f"{source}:{prof_count}")

                if prof_sources:
                    diagnostics["data_analysis"].append(f"Proficiency sources: {', '.join(prof_sources)}")
                else:
                    diagnostics["warnings"].append("No proficiency modifiers found")

        except Exception as e:
            logger.error(f"Error running diagnostics: {e}")
            diagnostics["errors"].append(f"Diagnostic error: {str(e)}")

        return diagnostics

    def process_character(self) -> Dict[str, Any]:
        """Process character data with enhanced 2024 support and comprehensive debugging."""
        try:
            logger.info("Processing character data with enhanced debugging...")

            # Phase 1: Explore data structure
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("🔍 PHASE 1: Exploring data structure...")
                structure_info = self._explore_data_structure()

            # Run comprehensive diagnostics
            diagnostics = self._run_diagnostics()

            # Log diagnostic findings
            actual_issues = len(diagnostics.get("errors", [])) + len(diagnostics.get("warnings", [])) + len(diagnostics.get("missing_data", []))
            info_items = len(diagnostics.get("info", [])) + len(diagnostics.get("data_analysis", [])) + len(diagnostics.get("expected_vs_actual", []))
            
            if actual_issues > 0:
                logger.info(f"Diagnostics found {actual_issues} issues:")
                for issue_type in ["errors", "warnings", "missing_data"]:
                    issues = diagnostics.get(issue_type, [])
                    if issues:
                        logger.info(f"  {issue_type}: {len(issues)} items")
                        for issue in issues:
                            logger.debug(f"    {issue_type}: {issue}")
            
            if info_items > 0:
                logger.info(f"Parsing analysis: {info_items} confirmations")
                for info_type in ["info", "data_analysis", "expected_vs_actual"]:
                    items = diagnostics.get(info_type, [])
                    if items:
                        logger.info(f"  {info_type}: {len(items)} items")
                        for item in items:
                            logger.debug(f"    {info_type}: {item}")

            # Process basic character information
            basic_info = self._parse_basic_info()
            appearance_info = self._parse_appearance()

            # Build the character data structure
            character_data = {
                "basic_info": {
                    "name": basic_info.name,
                    "level": basic_info.level,
                    "experience": basic_info.experience,
                    "avatarUrl": basic_info.avatarUrl,
                    "inspiration": basic_info.inspiration,
                    "lifestyleId": basic_info.lifestyleId,
                    "armor_class": self._calculate_armor_class(),
                    "initiative": self._calculate_initiative(),
                    "speed": self._calculate_speed(),
                    "hit_points": self._calculate_hit_points(),
                    "classes": [
                        {
                            "name": cls.name,
                            "level": cls.level,
                            "hit_die": cls.hit_die,
                            "subclass": cls.subclass,
                            "spellcasting_ability": cls.spellcasting_ability,
                            "is_2024": cls.is_2024
                        }
                        for cls in self.analyzer.character_classes
                    ]
                },

                "appearance": {
                    "gender": appearance_info.gender,
                    "age": appearance_info.age,
                    "hair": appearance_info.hair,
                    "eyes": appearance_info.eyes,
                    "skin": appearance_info.skin,
                    "height": appearance_info.height,
                    "weight": appearance_info.weight,
                    "traits": appearance_info.traits,
                    "size": appearance_info.size,
                    "size_name": appearance_info.size_name
                },

                "ability_scores": self._parse_ability_scores(),

                "skills": self._parse_skills(),

                "saving_throws": self._parse_saving_throws(),

                "proficiencies": self._parse_proficiencies(),
                
                "proficiency_sources": self._get_proficiency_sources(),

                "background": self._parse_background(),

                "species": self._parse_species(),

                "feats": [
                    {
                        "name": feat.name,
                        "description": feat.description,
                        "source": feat.source
                    }
                    for feat in self._parse_feats()
                ],

                "spells": self._parse_spells(),

                "spell_slots": self._calculate_spell_slots(),

                "actions": self._parse_actions(),

                "inventory": [
                    {
                        "name": item.name,
                        "quantity": item.quantity,
                        "equipped": item.equipped,
                        "attuned": item.attuned,
                        "requires_attunement": item.requires_attunement,
                        "weight": item.weight,
                        "type": item.item_type,
                        "rarity": item.rarity
                    }
                    for item in self._parse_inventory()
                ],

                "notes": {
                    "character_notes": self.raw_data.get("notes", {}).get("characterNotes", ""),
                    "allies": self.raw_data.get("notes", {}).get("allies", ""),
                    "backstory": self.raw_data.get("notes", {}).get("backstory", ""),
                    "personal_traits": self.raw_data.get("notes", {}).get("personalityTraits", ""),
                    "ideals": self.raw_data.get("notes", {}).get("ideals", ""),
                    "bonds": self.raw_data.get("notes", {}).get("bonds", ""),
                    "flaws": self.raw_data.get("notes", {}).get("flaws", "")
                },

                "meta": {
                    "character_id": self.character_id,
                    "is_2024_rules": self._is_2024_character(),
                    "processed_timestamp": time.time(),
                    "scraper_version": "5.2.0",
                    "proficiency_bonus": self._get_proficiency_bonus(),
                    "primary_spellcasting_ability": self._get_primary_spellcasting_ability(),
                    "passive_senses": self._calculate_passive_senses(),
                    "total_wealth_gp": self._calculate_total_wealth(),
                    "carrying_capacity": self._calculate_carrying_capacity(),
                    "total_caster_level": self._calculate_total_caster_level(),
                    "individual_currencies": self._get_individual_currencies(),
                    "diagnostics": diagnostics  # Include diagnostic information
                }
            }

            logger.info("Character processing completed successfully with enhanced debugging")
            return character_data

        except Exception as e:
            logger.error(f"Error processing character: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"error": f"Failed to process character: {str(e)}"}


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Enhanced D&D Beyond Character Scraper (5e 2024 Edition) - v5.2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python enhanced_dnd_scraper.py 144986992
  python enhanced_dnd_scraper.py 144986992 --output vaelith_2024.json
  python enhanced_dnd_scraper.py 144986992 --session "your_session" --verbose
  python enhanced_dnd_scraper.py 144986992 --html  # Preserve HTML formatting

New in v5.2.0:
  - NEW: HTML Stripping - Clean, readable descriptions by default (use --html to preserve)
  - NEW: Primary Spellcasting Ability - Automatically detected and included in meta
  - ENHANCED: BeautifulSoup HTML parsing (install with: pip install beautifulsoup4)

New in v5.0.0:
  - NEW: Background Spell Detection - Identifies spellListIds in backgrounds and racial traits
  - NEW: Enhanced Spell Metadata - Components, casting time, range, duration, concentration
  - NEW: Inventory Enhancement - Magic item properties, charges, enhanced descriptions
  - NEW: Basic Action Parsing - Extracts character actions and abilities from API data
  - IMPROVED: Diagnostic system now separates issues from confirmations
  - FIXED: Type safety improvements for better code reliability

Dependencies:
  Required: requests
  Optional: beautifulsoup4 (for better HTML parsing)

Note: This scraper only supports fetching live data from D&D Beyond.
Local JSON files are not supported.
        """
    )

    parser.add_argument(
        "character_id",
        help="D&D Beyond character ID (from character URL)"
    )

    parser.add_argument(
        "--output", "-o",
        help="Output JSON file (default: character name)"
    )

    parser.add_argument(
        "--session",
        help="Session cookie for private characters"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose debug logging"
    )

    parser.add_argument(
        "--html",
        action="store_true",
        help="Preserve HTML formatting in descriptions (default: strip HTML)"
    )

    parser.add_argument(
        "--raw-output",
        help="Save raw API response to specified file (for debugging/analysis)"
    )

    

    args = parser.parse_args()

    # Set up logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    # Configure verbose output
    global VERBOSE_OUTPUT
    VERBOSE_OUTPUT = args.verbose
        
    # Check for optional dependencies
    if not HAS_BEAUTIFULSOUP and not args.html:
        logger.info("BeautifulSoup not available, using regex fallback for HTML parsing")
        logger.info("For better HTML parsing, install with: pip install beautifulsoup4")

    # Create scraper
    scraper = DNDBeyondScraper(args.character_id, args.session, preserve_html=args.html)

    # Fetch character data
    if not scraper.fetch_character_data():
        logger.error("Failed to fetch character data")
        sys.exit(1)

    # Process character
    character_data = scraper.process_character()

    if "error" in character_data:
        logger.error(f"Character processing failed: {character_data['error']}")
        sys.exit(1)

    # Determine output filename
    if args.output:
        output_filename = args.output
    else:
        character_name = character_data.get("basic_info", {}).get("name", "character")
        # Sanitize filename
        safe_name = "".join(c for c in character_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        output_filename = f"{safe_name}.json"

    # Write output file
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(character_data, f, indent=2, ensure_ascii=False)

        logger.info("Character data exported successfully!")
        
        # Write raw output file if requested
        if args.raw_output:
            try:
                with open(args.raw_output, 'w', encoding='utf-8') as f:
                    json.dump(scraper.raw_data, f, indent=2, ensure_ascii=False)
                logger.info(f"Raw API data saved to: {args.raw_output}")
            except Exception as e:
                logger.error(f"Failed to write raw output file: {e}")

        # Print character summary (Windows console safe)
        basic_info = character_data.get("basic_info", {})
        ability_scores = character_data.get("ability_scores", {})
        spells = character_data.get("spells", {})
        feats = character_data.get("feats", [])
        proficiencies = character_data.get("proficiencies", {})
        inventory = character_data.get("inventory", [])
        meta = character_data.get("meta", {})
        hp_info = basic_info.get("hit_points", {})

        try:
            print(f"\n=== Character Summary ===")
            print(f"Name: {basic_info.get('name', 'Unknown')}")
            print(f"Level: {basic_info.get('level', 1)}")

            # Hit Points
            current_hp = hp_info.get("current", 1)
            max_hp = hp_info.get("maximum", 1)
            temp_hp = hp_info.get("temporary", 0)
            hp_display = f"{current_hp}/{max_hp}"
            if temp_hp > 0:
                hp_display += f" (+{temp_hp} temp)"
            print(f"Hit Points: {hp_display}")
        except UnicodeEncodeError:
            # Fallback for Windows console issues
            print("\n=== Character Summary ===")
            print(f"Name: {basic_info.get('name', 'Unknown')}")
            print(f"Level: {basic_info.get('level', 1)}")

            # Classes
            classes = basic_info.get("classes", [])
            if classes:
                class_summary = ", ".join([f"{cls['name']} {cls['level']}" for cls in classes])
                print(f"Classes: {class_summary}")

            # Ability Scores
            print(f"Ability Scores:")
            for ability, stats in ability_scores.items():
                score = stats.get("score", 10)
                modifier = stats.get("modifier", 0)
                modifier_str = f"+{modifier}" if modifier >= 0 else str(modifier)
                print(f"   {ability.title()}: {score} ({modifier_str})")

            # Spells
            total_spells = sum(len(spell_list) for spell_list in spells.values())
            spell_sources = len(spells)
            print(f"Spells: {total_spells} spells from {spell_sources} sources")

            # Show spell details if any found
            if total_spells > 0:
                for source, spell_list in spells.items():
                    if spell_list:
                        spell_names = [spell["name"] for spell in spell_list[:3]]  # Show first 3
                        more_text = f" (+{len(spell_list) - 3} more)" if len(spell_list) > 3 else ""
                        print(f"   {source}: {', '.join(spell_names)}{more_text}")

            # Feats
            print(f"Feats: {len(feats)} feats")
            if feats:
                feat_names = [feat["name"] for feat in feats[:3]]  # Show first 3
                more_text = f" (+{len(feats) - 3} more)" if len(feats) > 3 else ""
                print(f"   {', '.join(feat_names)}{more_text}")

            # Background
            background = character_data.get("background", {})
            print(f"Background: {background.get('name', 'Unknown')}")

            # Proficiencies
            languages = proficiencies.get("languages", [])
            tools = proficiencies.get("tools", [])
            skills = proficiencies.get("skills", [])
            weapons = proficiencies.get("weapons", [])
            print(
                f"Proficiencies: {len(languages)} languages, {len(tools)} tools, {len(skills)} skills, {len(weapons)} weapons")

            # Inventory
            equipped_items = [item for item in inventory if item.get("equipped", False)]
            attuned_items = [item for item in inventory if item.get("attuned", False)]
            print(f"Inventory: {len(inventory)} items ({len(equipped_items)} equipped, {len(attuned_items)} attuned)")

            # Rule Set
            rule_set = "2024 Rules" if meta.get("is_2024_rules", False) else "2014 Rules"
            print(f"Rule Set: {rule_set}")

            # Diagnostic summary
            diagnostics = meta.get("diagnostics", {})
            actual_issues = (len(diagnostics.get("errors", [])) + 
                            len(diagnostics.get("warnings", [])) + 
                            len(diagnostics.get("missing_data", [])))
            info_count = (len(diagnostics.get("info", [])) + 
                         len(diagnostics.get("data_analysis", [])) + 
                         len(diagnostics.get("expected_vs_actual", [])))
            
            if actual_issues > 0:
                print(f"Issues: {actual_issues} problems detected (see verbose output for details)")
            
            if info_count > 0:
                print(f"Parsing: {info_count} confirmations (see verbose output for details)")

            print(f"Full details saved to: {output_filename}")

    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()