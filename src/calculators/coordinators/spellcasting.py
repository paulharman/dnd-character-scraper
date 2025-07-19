"""
Spellcasting Coordinator

Coordinates the calculation of spellcasting abilities including spell slots,
save DC, attack bonuses, and spell management with multiclass support.
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass

from ..interfaces.coordination import ICoordinator
from ..utils.performance import monitor_performance
from ..services.interfaces import CalculationContext, CalculationResult, CalculationStatus
from ..services.spell_service import SpellProcessingService

logger = logging.getLogger(__name__)


@dataclass
class SpellcastingData:
    """Data class for spellcasting calculation results."""
    is_spellcaster: bool
    spellcasting_ability: Optional[str]
    spell_save_dc: Optional[int]
    spell_attack_bonus: Optional[int]
    spell_slots: List[int]
    pact_slots: int
    pact_slot_level: int
    caster_level: int
    spell_slot_breakdown: Dict[str, Any]
    spell_counts: Dict[str, Any]
    metadata: Dict[str, Any]


class SpellcastingCoordinator(ICoordinator):
    """
    Coordinates spellcasting calculations with comprehensive multiclass support.
    
    This coordinator handles:
    - Full caster progression (Wizard, Sorcerer, Cleric, Druid, Bard)
    - Half caster progression (Paladin, Ranger, Artificer)
    - Third casters (Eldritch Knight, Arcane Trickster)
    - Warlock pact magic (separate from regular slots)
    - Multiclass spell slot calculation
    - Spell save DC and attack bonus calculation
    - Primary spellcasting ability detection
    - Spell counts and spell list management
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize the spellcasting coordinator.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Spellcasting classifications
        self.full_casters = {
            'wizard', 'sorcerer', 'cleric', 'druid', 'bard'
        }
        self.half_casters = {
            'paladin', 'ranger', 'artificer'
        }
        self.third_casters = {
            'eldritch knight', 'arcane trickster'
        }
        
        # Spellcasting ability mappings
        self.spellcasting_abilities = {
            'wizard': 'intelligence',
            'sorcerer': 'charisma',
            'cleric': 'wisdom',
            'druid': 'wisdom',
            'bard': 'charisma',
            'warlock': 'charisma',
            'paladin': 'charisma',
            'ranger': 'wisdom',
            'artificer': 'intelligence',
            'eldritch knight': 'intelligence',
            'arcane trickster': 'intelligence'
        }
        
        # Spell slot progression table (index 0 = 1st level caster, etc.)
        self.spell_slot_table = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0],  # 0th level (no caster)
            [2, 0, 0, 0, 0, 0, 0, 0, 0],  # 1st level
            [3, 0, 0, 0, 0, 0, 0, 0, 0],  # 2nd level
            [4, 2, 0, 0, 0, 0, 0, 0, 0],  # 3rd level
            [4, 3, 0, 0, 0, 0, 0, 0, 0],  # 4th level
            [4, 3, 2, 0, 0, 0, 0, 0, 0],  # 5th level
            [4, 3, 3, 0, 0, 0, 0, 0, 0],  # 6th level
            [4, 3, 3, 1, 0, 0, 0, 0, 0],  # 7th level
            [4, 3, 3, 2, 0, 0, 0, 0, 0],  # 8th level
            [4, 3, 3, 3, 1, 0, 0, 0, 0],  # 9th level
            [4, 3, 3, 3, 2, 0, 0, 0, 0],  # 10th level
            [4, 3, 3, 3, 2, 1, 0, 0, 0],  # 11th level
            [4, 3, 3, 3, 2, 1, 0, 0, 0],  # 12th level
            [4, 3, 3, 3, 2, 1, 1, 0, 0],  # 13th level
            [4, 3, 3, 3, 2, 1, 1, 0, 0],  # 14th level
            [4, 3, 3, 3, 2, 1, 1, 1, 0],  # 15th level
            [4, 3, 3, 3, 2, 1, 1, 1, 0],  # 16th level
            [4, 3, 3, 3, 2, 1, 1, 1, 1],  # 17th level
            [4, 3, 3, 3, 3, 1, 1, 1, 1],  # 18th level
            [4, 3, 3, 3, 3, 2, 1, 1, 1],  # 19th level
            [4, 3, 3, 3, 3, 2, 2, 1, 1],  # 20th level
        ]
        
        # Warlock pact magic progression
        self.pact_magic_table = [
            (0, 0),  # 0th level
            (1, 1),  # 1st level
            (2, 1),  # 2nd level
            (2, 2),  # 3rd level
            (2, 2),  # 4th level
            (2, 3),  # 5th level
            (2, 3),  # 6th level
            (2, 4),  # 7th level
            (2, 4),  # 8th level
            (2, 5),  # 9th level
            (2, 5),  # 10th level
            (3, 5),  # 11th level
            (3, 5),  # 12th level
            (3, 5),  # 13th level
            (3, 5),  # 14th level
            (3, 5),  # 15th level
            (3, 5),  # 16th level
            (4, 5),  # 17th level
            (4, 5),  # 18th level
            (4, 5),  # 19th level
            (4, 5),  # 20th level
        ]
    
    @property
    def coordinator_name(self) -> str:
        """Get the coordinator name."""
        return "spellcasting"
    
    @property
    def dependencies(self) -> List[str]:
        """Get the list of dependencies."""
        return ["character_info", "abilities"]  # Depends on character info and ability scores
    
    @property
    def priority(self) -> int:
        """Get the execution priority (lower = higher priority)."""
        return 40  # Medium priority - depends on abilities and character info
    
    @monitor_performance("spellcasting_coordinate")
    def coordinate(self, raw_data: Dict[str, Any], context: CalculationContext) -> CalculationResult:
        """
        Coordinate the calculation of spellcasting abilities.
        
        Args:
            raw_data: Raw character data from D&D Beyond
            context: Calculation context
            
        Returns:
            CalculationResult with spellcasting data
        """
        self.logger.info(f"Coordinating spellcasting calculation for character {raw_data.get('id', 'unknown')}")
        
        try:
            # Check if character is a spellcaster
            is_spellcaster = self._is_spellcaster(raw_data)
            
            if not is_spellcaster:
                # Non-spellcaster result
                result_data = {
                    'is_spellcaster': False,
                    'spellcasting_ability': None,
                    'spell_save_dc': None,
                    'spell_attack_bonus': None,
                    'spell_slots': [0] * 9,
                    'pact_slots': 0,
                    'pact_slot_level': 0,
                    'caster_level': 0,
                    'spell_slot_breakdown': {},
                    'spell_counts': {},
                    'metadata': {
                        'is_spellcaster': False,
                        'has_cantrips': False,
                        'has_pact_magic': False,
                        'multiclass_caster': False
                    }
                }
                
                return CalculationResult(
                    service_name=self.coordinator_name,
                    status=CalculationStatus.COMPLETED,
                    data=result_data,
                    errors=[],
                    warnings=[]
                )
            
            # Get dependencies from context
            ability_modifiers = self._get_ability_modifiers(raw_data, context)
            proficiency_bonus = self._get_proficiency_bonus(raw_data, context)
            
            # Determine spellcasting ability
            spellcasting_ability = self._detect_spellcasting_ability(raw_data)
            
            # Calculate spell save DC and attack bonus
            spell_save_dc = None
            spell_attack_bonus = None
            
            if spellcasting_ability:
                ability_modifier = ability_modifiers.get(spellcasting_ability, 0)
                spell_save_dc = 8 + proficiency_bonus + ability_modifier
                spell_attack_bonus = proficiency_bonus + ability_modifier
            
            # Calculate spell slots
            spell_slots_info = self._calculate_spell_slots(raw_data)
            
            # Get spell counts and information
            spell_counts = self._get_spell_counts(raw_data)
            
            # Create result data
            result_data = {
                'is_spellcaster': True,
                'spellcasting_ability': spellcasting_ability,
                'spell_save_dc': spell_save_dc,
                'spell_attack_bonus': spell_attack_bonus,
                'spell_slots': spell_slots_info['regular_slots'],
                'pact_slots': spell_slots_info['pact_slots'],
                'pact_slot_level': spell_slots_info['pact_slot_level'],
                'caster_level': spell_slots_info['caster_level'],
                'spell_slot_breakdown': spell_slots_info['breakdown'],
                'spell_counts': spell_counts,
                'metadata': {
                    'is_spellcaster': True,
                    'has_cantrips': spell_counts.get('cantrips', 0) > 0,
                    'has_pact_magic': spell_slots_info['pact_slots'] > 0,
                    'multiclass_caster': len(spell_slots_info['breakdown']) > 1,
                    'total_spell_slots': sum(spell_slots_info['regular_slots']),
                    'highest_spell_level': self._get_highest_spell_level(spell_slots_info['regular_slots']),
                    'spellcasting_modifier': ability_modifiers.get(spellcasting_ability, 0) if spellcasting_ability else 0
                }
            }
            
            attack_str = f"{spell_attack_bonus:+d}" if spell_attack_bonus is not None else "N/A"
            self.logger.info(f"Successfully calculated spellcasting. DC: {spell_save_dc}, Attack: {attack_str}")
            
            return CalculationResult(
                service_name=self.coordinator_name,
                status=CalculationStatus.COMPLETED,
                data=result_data,
                errors=[],
                warnings=[]
            )
            
        except Exception as e:
            self.logger.error(f"Error coordinating spellcasting calculation: {str(e)}")
            return CalculationResult(
                service_name=self.coordinator_name,
                status=CalculationStatus.FAILED,
                data={},
                errors=[f"Spellcasting calculation failed: {str(e)}"]
            )
    
    def _is_spellcaster(self, raw_data: Dict[str, Any]) -> bool:
        """Check if character is a spellcaster."""
        classes = raw_data.get('classes', [])
        
        for class_data in classes:
            class_def = class_data.get('definition', {})
            class_name = class_def.get('name', '').lower()
            
            # Check if class is a known spellcaster
            if (class_name in self.full_casters or 
                class_name in self.half_casters or 
                class_name == 'warlock' or
                self._is_third_caster(class_name, class_data)):
                return True
        
        # Check for spells in character data
        spells = raw_data.get('spells', [])
        if spells:
            return True
        
        # Check for spell slots
        spell_slots = raw_data.get('spellSlots', [])
        if spell_slots and sum(slot.get('level', 0) * slot.get('available', 0) for slot in spell_slots) > 0:
            return True
        
        return False
    
    def _is_third_caster(self, class_name: str, class_data: Dict[str, Any]) -> bool:
        """Check if class is a third caster (Eldritch Knight, Arcane Trickster)."""
        class_level = class_data.get('level', 0)
        
        # Eldritch Knight Fighter (gets spells at 3rd level)
        if class_name == 'fighter' and class_level >= 3:
            subclass = class_data.get('subclass', {})
            if subclass:
                subclass_def = subclass.get('definition', {})
                subclass_name = subclass_def.get('name', '').lower()
                if 'eldritch knight' in subclass_name:
                    return True
        
        # Arcane Trickster Rogue (gets spells at 3rd level)
        if class_name == 'rogue' and class_level >= 3:
            subclass = class_data.get('subclass', {})
            if subclass:
                subclass_def = subclass.get('definition', {})
                subclass_name = subclass_def.get('name', '').lower()
                if 'arcane trickster' in subclass_name:
                    return True
        
        return False
    
    def _detect_spellcasting_ability(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """Detect the primary spellcasting ability using backup original logic."""
        # First try to get spellcasting ability from spell data itself (backup original logic)
        spells_data = raw_data.get('spells', {})
        
        # Handle different spell data formats
        all_spells = []
        if isinstance(spells_data, dict):
            for source, spells_list in spells_data.items():
                if isinstance(spells_list, list):
                    all_spells.extend(spells_list)
        elif isinstance(spells_data, list):
            all_spells = spells_data
        
        # Check for spellcasting_ability in spell data
        for spell in all_spells:
            if isinstance(spell, dict):
                spellcasting_ability = spell.get('spellcasting_ability')
                if spellcasting_ability:
                    self.logger.debug(f"Found spellcasting ability from spell data: {spellcasting_ability}")
                    return spellcasting_ability
        
        # Check for pre-calculated spellcasting data in the root
        spellcasting_data = raw_data.get('spellcasting', {})
        if isinstance(spellcasting_data, dict):
            ability = spellcasting_data.get('spellcasting_ability')
            if ability:
                self.logger.debug(f"Found spellcasting ability from spellcasting data: {ability}")
                return ability
        
        # Fallback: Use class-based logic as before
        classes = raw_data.get('classes', [])
        
        # Find the highest level spellcaster
        highest_caster_level = 0
        primary_ability = None
        
        for class_data in classes:
            class_def = class_data.get('definition', {})
            class_name = class_def.get('name', '').lower()
            class_level = class_data.get('level', 0)
            
            # Check if this is a spellcaster and get its ability
            ability = None
            if class_name in self.spellcasting_abilities:
                ability = self.spellcasting_abilities[class_name]
            elif self._is_third_caster(class_name, class_data):
                if class_name == 'fighter':
                    ability = 'intelligence'  # Eldritch Knight
                elif class_name == 'rogue':
                    ability = 'intelligence'  # Arcane Trickster
            
            if ability and class_level > highest_caster_level:
                highest_caster_level = class_level
                primary_ability = ability
                self.logger.debug(f"Found spellcasting ability from class mapping: {ability} for class: {class_name}")
        
        return primary_ability
    
    def _calculate_spell_slots(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate spell slots with multiclass support."""
        # Check if spell slots are provided by API
        spell_slots_data = raw_data.get('spellSlots', [])
        if spell_slots_data:
            api_slots = self._parse_api_spell_slots(spell_slots_data)
            if sum(api_slots) > 0:
                # Use API data but still calculate pact magic
                pact_slots, pact_level = self._calculate_pact_magic(raw_data)
                return {
                    'regular_slots': api_slots,
                    'pact_slots': pact_slots,
                    'pact_slot_level': pact_level,
                    'caster_level': sum(api_slots),
                    'breakdown': {'api': {'source': 'api'}}
                }
        
        # Calculate from class levels
        classes = raw_data.get('classes', [])
        
        # Separate Warlock from other casters
        warlock_levels = 0
        caster_levels = {}
        
        for class_data in classes:
            class_def = class_data.get('definition', {})
            class_name = class_def.get('name', '').lower()
            class_level = class_data.get('level', 0)
            
            if class_name == 'warlock':
                warlock_levels = class_level
            elif class_name in self.full_casters:
                caster_levels[class_name] = {'level': class_level, 'type': 'full'}
            elif class_name in self.half_casters:
                caster_levels[class_name] = {'level': class_level, 'type': 'half'}
            elif self._is_third_caster(class_name, class_data):
                subclass_name = self._get_subclass_name(class_data)
                full_name = f"{class_name} ({subclass_name})" if subclass_name else class_name
                caster_levels[full_name] = {'level': class_level, 'type': 'third'}
        
        # Calculate multiclass caster level
        total_caster_level = 0
        breakdown = {}
        
        for class_name, info in caster_levels.items():
            level = info['level']
            caster_type = info['type']
            
            if caster_type == 'full':
                contribution = level
            elif caster_type == 'half':
                contribution = level // 2
            elif caster_type == 'third':
                contribution = level // 3
            else:
                contribution = 0
            
            total_caster_level += contribution
            breakdown[class_name] = {
                'class_level': level,
                'caster_type': caster_type,
                'contribution': contribution
            }
        
        # Get spell slots for caster level
        if total_caster_level > 0:
            regular_slots = self._get_spell_slots_for_level(total_caster_level)
        else:
            regular_slots = [0] * 9
        
        # Calculate Warlock pact magic
        pact_slots, pact_level = self._calculate_pact_magic(raw_data)
        
        return {
            'regular_slots': regular_slots,
            'pact_slots': pact_slots,
            'pact_slot_level': pact_level,
            'caster_level': total_caster_level,
            'breakdown': breakdown
        }
    
    def _parse_api_spell_slots(self, spell_slots_data: List[Dict[str, Any]]) -> List[int]:
        """Parse spell slots from API data."""
        slots = [0] * 9
        
        for slot_data in spell_slots_data:
            level = slot_data.get('level', 0)
            available = slot_data.get('available', 0)
            
            if 1 <= level <= 9:
                slots[level - 1] = available
        
        return slots
    
    def _get_spell_slots_for_level(self, caster_level: int) -> List[int]:
        """Get spell slots for a given caster level."""
        if caster_level <= 0:
            return [0] * 9
        
        # Cap at 20th level
        caster_level = min(caster_level, 20)
        
        return self.spell_slot_table[caster_level].copy()
    
    def _calculate_pact_magic(self, raw_data: Dict[str, Any]) -> Tuple[int, int]:
        """Calculate Warlock pact magic slots."""
        classes = raw_data.get('classes', [])
        
        for class_data in classes:
            class_def = class_data.get('definition', {})
            class_name = class_def.get('name', '').lower()
            
            if class_name == 'warlock':
                warlock_level = class_data.get('level', 0)
                if warlock_level > 0:
                    # Cap at 20th level
                    warlock_level = min(warlock_level, 20)
                    pact_slots, pact_level = self.pact_magic_table[warlock_level]
                    return pact_slots, pact_level
        
        return 0, 0
    
    def _get_spell_counts(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get spell counts by level - only counts known spells."""
        spells_data = raw_data.get('spells', {})
        spell_counts = {
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
        
        # Handle spells from different sources - only count known spells
        all_spells = []
        
        # Handle spells dict format (by source)
        if isinstance(spells_data, dict):
            for source, spells_list in spells_data.items():
                if isinstance(spells_list, list):
                    # Only include known spells, always prepared spells, or prepared spells
                    for spell_data in spells_list:
                        if isinstance(spell_data, dict):
                            counts_as_known = spell_data.get('countsAsKnownSpell', False)
                            is_always_prepared = spell_data.get('alwaysPrepared', False)
                            # For non-class spells, include if prepared or always prepared
                            is_prepared = spell_data.get('prepared', False)
                            
                            if counts_as_known or is_always_prepared or is_prepared:
                                all_spells.append(spell_data)
        elif isinstance(spells_data, list):
            # Only include known spells, always prepared spells, or prepared spells
            for spell_data in spells_data:
                if isinstance(spell_data, dict):
                    counts_as_known = spell_data.get('countsAsKnownSpell', False)
                    is_always_prepared = spell_data.get('alwaysPrepared', False)
                    is_prepared = spell_data.get('prepared', False)
                    
                    if counts_as_known or is_always_prepared or is_prepared:
                        all_spells.append(spell_data)
        
        # Also process classSpells - only count known spells
        class_spells_data = raw_data.get('classSpells', [])
        for class_spell_data in class_spells_data:
            if isinstance(class_spell_data, dict):
                class_spells = class_spell_data.get('spells', [])
                if isinstance(class_spells, list):
                    # Only include known spells (for class spells, use countsAsKnownSpell)
                    for spell_data in class_spells:
                        if isinstance(spell_data, dict):
                            counts_as_known = spell_data.get('countsAsKnownSpell', False)
                            is_always_prepared = spell_data.get('alwaysPrepared', False)
                            
                            if counts_as_known or is_always_prepared:
                                all_spells.append(spell_data)
        
        for spell in all_spells:
            if not isinstance(spell, dict):
                continue
                
            spell_def = spell.get('definition', {})
            raw_level = spell_def.get('level', 0)
            
            # Handle malformed spell levels
            try:
                if isinstance(raw_level, str):
                    if raw_level.lower() == 'cantrip':
                        spell_level = 0
                    else:
                        spell_level = int(raw_level)
                else:
                    spell_level = int(raw_level)
            except (ValueError, TypeError):
                spell_level = 0  # Default to cantrip for invalid levels
            
            # Clamp to valid range
            spell_level = max(0, min(9, spell_level))
            
            if spell_level == 0:
                spell_counts['cantrips'] += 1
            elif 1 <= spell_level <= 9:
                spell_counts[f'level_{spell_level}'] += 1
            
            spell_counts['total'] += 1
        
        return spell_counts
    
    def _get_highest_spell_level(self, spell_slots: List[int]) -> int:
        """Get the highest spell level available."""
        for level in range(8, -1, -1):  # Check from 9th to 1st level
            if spell_slots[level] > 0:
                return level + 1
        return 0
    
    def _get_subclass_name(self, class_data: Dict[str, Any]) -> Optional[str]:
        """Get the subclass name from class data."""
        subclass = class_data.get('subclass')
        if subclass:
            subclass_def = subclass.get('definition', {})
            return subclass_def.get('name')
        return None
    
    def _get_ability_modifiers(self, raw_data: Dict[str, Any], context: CalculationContext) -> Dict[str, int]:
        """Get ability modifiers from context or calculate from raw data."""
        # Try to get from context first (from abilities coordinator)
        if context and hasattr(context, 'metadata') and context.metadata:
            abilities_data = context.metadata.get('abilities', {})
            if 'ability_modifiers' in abilities_data:
                return abilities_data['ability_modifiers']
        
        # Fallback: calculate from raw data
        ability_modifiers = {}
        stats = raw_data.get('stats', [])
        
        ability_id_map = {
            1: "strength",
            2: "dexterity", 
            3: "constitution",
            4: "intelligence",
            5: "wisdom",
            6: "charisma"
        }
        
        for stat in stats:
            ability_id = stat.get('id')
            ability_score = stat.get('value', 10)
            
            if ability_id in ability_id_map:
                ability_name = ability_id_map[ability_id]
                modifier = (ability_score - 10) // 2
                ability_modifiers[ability_name] = modifier
        
        # Ensure all abilities are present
        for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            if ability not in ability_modifiers:
                ability_modifiers[ability] = 0
        
        return ability_modifiers
    
    def _get_proficiency_bonus(self, raw_data: Dict[str, Any], context: CalculationContext) -> int:
        """Get proficiency bonus from context or calculate from character level."""
        # Try to get from context first (from character_info coordinator)
        if context and hasattr(context, 'metadata') and context.metadata:
            character_info = context.metadata.get('character_info', {})
            if 'proficiency_bonus' in character_info:
                return character_info['proficiency_bonus']
        
        # Fallback: calculate from character level
        classes = raw_data.get('classes', [])
        total_level = sum(cls.get('level', 0) for cls in classes)
        character_level = max(1, total_level)
        return ((character_level - 1) // 4) + 2
    
    def validate_input(self, raw_data: Dict[str, Any]) -> bool:
        """
        Validate that the input data is suitable for this coordinator.
        
        Args:
            raw_data: Raw character data to validate
            
        Returns:
            True if data is valid for this coordinator
        """
        # Spellcasting calculation is optional and can work with minimal data
        if not isinstance(raw_data, dict):
            return False
        
        # We can handle characters without classes - they just won't be spellcasters
        # This allows processing of malformed/empty characters
        return True
    
    def can_coordinate(self, raw_data: Dict[str, Any]) -> bool:
        """
        Check if this coordinator can handle the given data.
        
        Args:
            raw_data: Raw character data
            
        Returns:
            True if coordinator can handle this data
        """
        return self.validate_input(raw_data)
    
    def get_output_schema(self) -> Dict[str, Any]:
        """
        Get the schema for data this coordinator produces.
        
        Returns:
            Schema describing the output data structure
        """
        return {
            "type": "object",
            "properties": {
                "is_spellcaster": {"type": "boolean"},
                "spellcasting_ability": {"type": ["string", "null"]},
                "spell_save_dc": {"type": ["integer", "null"], "minimum": 8, "maximum": 30},
                "spell_attack_bonus": {"type": ["integer", "null"]},
                "spell_slots": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 0},
                    "minItems": 9,
                    "maxItems": 9
                },
                "pact_slots": {"type": "integer", "minimum": 0},
                "pact_slot_level": {"type": "integer", "minimum": 0, "maximum": 5},
                "caster_level": {"type": "integer", "minimum": 0, "maximum": 20},
                "spell_slot_breakdown": {"type": "object"},
                "spell_counts": {
                    "type": "object",
                    "properties": {
                        "cantrips": {"type": "integer", "minimum": 0},
                        "total": {"type": "integer", "minimum": 0}
                    }
                },
                "metadata": {"type": "object"}
            },
            "required": [
                "is_spellcaster", "spell_slots", "pact_slots", "pact_slot_level",
                "caster_level", "spell_slot_breakdown", "spell_counts"
            ]
        }