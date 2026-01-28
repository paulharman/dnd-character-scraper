#!/usr/bin/env python3
"""
Centralized spell processing service for D&D Beyond character data.

This service processes spells once and provides the data needed for both
general spell listings and combat attack filtering.
"""

import logging
from typing import Dict, Any, List, Optional, NamedTuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SpellInfo:
    """Processed spell information with all needed metadata."""
    name: str
    level: int
    school: str
    source: str
    description: str
    is_legacy: bool
    is_known: bool
    is_prepared: bool
    is_always_prepared: bool
    ritual: bool
    concentration: bool
    
    # Combat-specific fields
    can_be_combat_attack: bool
    attack_bonus: Optional[int] = None
    save_dc: Optional[int] = None
    spellcasting_ability: Optional[str] = None
    casting_time: Optional[str] = None
    range_info: Optional[Dict[str, Any]] = None
    duration: Optional[Dict[str, Any]] = None
    components: Optional[List[int]] = None
    components_description: Optional[str] = None
    snippet: Optional[str] = None


class SpellProcessingService:
    """
    Centralized service for processing D&D Beyond spell data.
    
    Processes spells once and provides filtered views for different use cases:
    - Known spells (for general display/Discord)
    - Prepared spells (for combat attacks)
    - All spells with metadata (for comprehensive display)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_character_spells(
        self, 
        raw_data: Dict[str, Any], 
        spell_attack_bonus: Optional[int] = None,
        spell_save_dc: Optional[int] = None
    ) -> Dict[str, List[SpellInfo]]:
        """
        Process all spells for a character and return organized spell data.
        
        Args:
            raw_data: Raw D&D Beyond character data
            spell_attack_bonus: Character's spell attack bonus
            spell_save_dc: Character's spell save DC
            
        Returns:
            Dictionary mapping spell sources to lists of SpellInfo objects
        """
        processed_spells = {}
        
        # Get spells data from raw character data
        spells_data = raw_data.get('spells', {})
        
        # Validate that spells_data is a dictionary
        if not isinstance(spells_data, dict):
            self.logger.warning(f"Expected spells data to be a dictionary, got {type(spells_data).__name__}: {spells_data}")
            return processed_spells
        
        if not spells_data:
            return processed_spells
        
        # Process class spells (from classSpells)
        class_spells_data = spells_data.get('classSpells', [])
        if class_spells_data and isinstance(class_spells_data, list):
            self._process_class_spells(
                class_spells_data, 
                raw_data, 
                processed_spells,
                spell_attack_bonus,
                spell_save_dc
            )
        elif class_spells_data:
            self.logger.warning(f"Expected classSpells to be a list, got {type(class_spells_data).__name__}: {class_spells_data}")
        
        # Process non-class spells (racial, feat, item, background)
        for source_type, spell_list in spells_data.items():
            if source_type != 'classSpells' and isinstance(spell_list, list) and spell_list:
                source_name = self._get_spell_source_name(source_type)
                self._process_spell_list(
                    spell_list,
                    source_name,
                    processed_spells,
                    spell_attack_bonus,
                    spell_save_dc,
                    is_class_spell=False
                )
        
        return processed_spells
    
    def _process_class_spells(
        self,
        class_spells_data: List[Dict[str, Any]],
        raw_data: Dict[str, Any],
        processed_spells: Dict[str, List[SpellInfo]],
        spell_attack_bonus: Optional[int],
        spell_save_dc: Optional[int]
    ) -> None:
        """Process class spells (Wizard, Cleric, etc.)."""
        for class_spell_entry in class_spells_data:
            if not isinstance(class_spell_entry, dict):
                self.logger.warning(f"Expected class spell entry to be a dictionary, got {type(class_spell_entry).__name__}: {class_spell_entry}")
                continue
                
            character_class_id = class_spell_entry.get('characterClassId')
            spells = class_spell_entry.get('spells', [])
            
            if spells and isinstance(spells, list):
                # Get class name from character classes
                class_name = self._get_class_name_by_id(raw_data, character_class_id)
                self._process_spell_list(
                    spells,
                    class_name,
                    processed_spells,
                    spell_attack_bonus,
                    spell_save_dc,
                    is_class_spell=True
                )
            elif spells:
                self.logger.warning(f"Expected spells to be a list, got {type(spells).__name__}: {spells}")
    
    def _process_spell_list(
        self,
        spell_list: List[Dict[str, Any]],
        source_name: str,
        processed_spells: Dict[str, List[SpellInfo]],
        spell_attack_bonus: Optional[int],
        spell_save_dc: Optional[int],
        is_class_spell: bool = False
    ) -> None:
        """Process a list of spells from a specific source."""
        if source_name not in processed_spells:
            processed_spells[source_name] = []
        
        for spell_data in spell_list:
            spell_info = self._create_spell_info(
                spell_data, 
                source_name, 
                spell_attack_bonus, 
                spell_save_dc,
                is_class_spell
            )
            if spell_info:
                processed_spells[source_name].append(spell_info)
    
    def _create_spell_info(
        self,
        spell_data: Dict[str, Any],
        source: str,
        spell_attack_bonus: Optional[int],
        spell_save_dc: Optional[int],
        is_class_spell: bool = False
    ) -> Optional[SpellInfo]:
        """Create SpellInfo object from raw spell data."""
        if not isinstance(spell_data, dict):
            return None
        
        # Get spell definition
        spell_def = spell_data.get('definition', {})
        if not spell_def:
            return None
        
        # Basic spell info
        name = spell_def.get('name', 'Unknown Spell')
        level = spell_def.get('level', 0)
        school = spell_def.get('school', {}).get('name', 'Unknown')
        description = spell_def.get('description', '')
        is_legacy = spell_data.get('isLegacy', False)
        ritual = spell_def.get('ritual', False)
        concentration = spell_def.get('concentration', False)
        
        # Determine spell availability
        is_known = self._is_spell_known(spell_data, is_class_spell)
        is_prepared = spell_data.get('prepared', False)
        is_always_prepared = spell_data.get('alwaysPrepared', False)
        
        # Extract spell details for ALL spells (not just combat spells)
        casting_time = spell_def.get('activation', {}).get('activationTime')
        range_info = spell_def.get('range')
        duration = spell_def.get('duration')
        components = spell_def.get('components', [])
        components_description = spell_def.get('componentsDescription', '')

        # Combat attack info
        can_be_combat_attack = self._can_spell_be_combat_attack(spell_def)
        attack_bonus = None
        save_dc = None
        spellcasting_ability = None
        snippet = None

        if can_be_combat_attack:
            attack_bonus = spell_attack_bonus
            save_dc = spell_save_dc
            spellcasting_ability = spell_data.get('spellcasting_ability')
            snippet = f"Spell Attack: +{attack_bonus} to hit" if attack_bonus else None
        
        return SpellInfo(
            name=name,
            level=level,
            school=school,
            source=source,
            description=description,
            is_legacy=is_legacy,
            is_known=is_known,
            is_prepared=is_prepared,
            is_always_prepared=is_always_prepared,
            ritual=ritual,
            concentration=concentration,
            can_be_combat_attack=can_be_combat_attack,
            attack_bonus=attack_bonus,
            save_dc=save_dc,
            spellcasting_ability=spellcasting_ability,
            casting_time=casting_time,
            range_info=range_info,
            duration=duration,
            components=components,
            components_description=components_description,
            snippet=snippet
        )
    
    def _is_spell_known(self, spell_data: Dict[str, Any], is_class_spell: bool) -> bool:
        """Determine if a spell is known by the character."""
        if is_class_spell:
            # For class spells, use countsAsKnownSpell
            return spell_data.get('countsAsKnownSpell', False) or spell_data.get('alwaysPrepared', False)
        else:
            # For non-class spells, use prepared, always prepared, or known status
            return (spell_data.get('prepared', False) or 
                   spell_data.get('alwaysPrepared', False) or
                   spell_data.get('countsAsKnownSpell', False))
    
    def _can_spell_be_combat_attack(self, spell_def: Dict[str, Any]) -> bool:
        """Check if a spell can be used as a combat attack."""
        # Check if spell has attack roll or saving throw
        activation = spell_def.get('activation', {})
        if not activation:
            return False
        
        activation_type = activation.get('activationType')
        if activation_type in [1, 2, 3, 4, 5, 6]:  # Action, Bonus Action, Reaction, etc.
            # Check if spell has attack or save components
            has_attack = any(
                component.get('typeId') in [1, 2] for component in spell_def.get('components', [])
            )
            has_save = any(
                component.get('typeId') in [3, 4] for component in spell_def.get('components', [])
            )
            return has_attack or has_save
        
        return False
    
    def _get_class_name_by_id(self, raw_data: Dict[str, Any], character_class_id: int) -> str:
        """Get class name by character class ID."""
        classes = raw_data.get('classes', [])
        for class_data in classes:
            if class_data.get('id') == character_class_id:
                class_definition = class_data.get('definition', {})
                return class_definition.get('name', 'Unknown Class')
        return 'Unknown Class'
    
    def _get_spell_source_name(self, source_type: str) -> str:
        """Map source type to friendly name."""
        source_mapping = {
            'race': 'Species',
            'feat': 'Feat',
            'item': 'Item',
            'background': 'Background',
            'class': 'Class',
            'subclass': 'Subclass'
        }
        return source_mapping.get(source_type, source_type.title())
    
    def get_known_spells(self, processed_spells: Dict[str, List[SpellInfo]]) -> Dict[str, List[SpellInfo]]:
        """Get only known spells (for Discord/general display)."""
        known_spells = {}
        for source, spells in processed_spells.items():
            known_spells[source] = [spell for spell in spells if spell.is_known]
        return known_spells
    
    def get_prepared_spells(self, processed_spells: Dict[str, List[SpellInfo]]) -> Dict[str, List[SpellInfo]]:
        """Get only prepared spells (for combat attacks)."""
        prepared_spells = {}
        for source, spells in processed_spells.items():
            prepared_spells[source] = [
                spell for spell in spells 
                if spell.is_prepared or spell.is_always_prepared
            ]
        return prepared_spells
    
    def get_combat_spell_attacks(self, processed_spells: Dict[str, List[SpellInfo]]) -> List[Dict[str, Any]]:
        """Get spell attacks for combat (prepared spells that can be attacks)."""
        attacks = []
        for source, spells in processed_spells.items():
            for spell in spells:
                if (spell.can_be_combat_attack and 
                    (spell.is_prepared or spell.is_always_prepared)):
                    
                    attack_info = {
                        'name': spell.name,
                        'description': spell.description,
                        'type': 'spell_attack',
                        'spell_level': spell.level,
                        'attack_bonus': spell.attack_bonus,
                        'save_dc': spell.save_dc,
                        'spellcasting_ability': spell.spellcasting_ability,
                        'casting_time': spell.casting_time,
                        'range': spell.range_info,
                        'duration': spell.duration,
                        'snippet': spell.snippet
                    }
                    attacks.append(attack_info)
        
        return attacks
    
    def get_spell_counts(self, processed_spells: Dict[str, List[SpellInfo]]) -> Dict[str, int]:
        """Get spell counts by level (for known spells)."""
        counts = {
            'cantrips': 0,
            'level_1': 0,
            'level_2': 0,
            'level_3': 0,
            'level_4': 0,
            'level_5': 0,
            'level_6': 0,
            'level_7': 0,
            'level_8': 0,
            'level_9': 0,
            'total': 0
        }
        
        for source, spells in processed_spells.items():
            for spell in spells:
                if spell.is_known:
                    if spell.level == 0:
                        counts['cantrips'] += 1
                    else:
                        counts[f'level_{spell.level}'] += 1
                    counts['total'] += 1
        
        return counts