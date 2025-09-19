"""
Spellcasting Calculator

Calculates spell slots, save DC, and attack bonuses from D&D Beyond data.
Handles multiclass spellcasting, Warlock pact magic, and all spellcaster types.
"""

from typing import Dict, Any, List, Optional, Tuple
import logging

from scraper.core.interfaces.calculator import SpellcastingCalculatorInterface
from shared.models.character import Character
from shared.config.manager import get_config_manager
from scraper.core.interfaces.rule_engine import RuleVersion

logger = logging.getLogger(__name__)


class SpellcastingCalculator(SpellcastingCalculatorInterface):
    """
    Calculator for spellcasting with comprehensive multiclass support.
    
    Handles:
    - Full caster progression (Wizard, Sorcerer, Cleric, Druid, Bard)
    - Half caster progression (Paladin, Ranger, Artificer)
    - Third casters (Eldritch Knight, Arcane Trickster)
    - Warlock pact magic (separate from regular slots)
    - Multiclass spell slot calculation
    - Spell save DC and attack bonus calculation
    - Primary spellcasting ability detection
    """
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.constants = self.config_manager.get_constants_config()
        
        # Spellcasting classifications
        self.full_casters = set(self.constants.classes.full_casters)
        self.half_casters = set(self.constants.classes.half_casters)
        self.third_casters = set(self.constants.classes.third_casters)
        
        # Spellcasting ability mappings
        self.default_spellcasting_abilities = {
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
            'arcane trickster': 'intelligence',
            'fighter': 'intelligence',  # For Eldritch Knight
            'rogue': 'intelligence'     # For Arcane Trickster
        }
        
    def calculate(self, character: Character, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate all spellcasting information.
        
        Returns:
            Dictionary containing spell slots, save DC, attack bonus, and spell lists
        """
        logger.info(f"Calculating spellcasting for character {character.id}")
        
        # Determine if character is a spellcaster
        is_spellcaster = self._is_spellcaster(raw_data)
        
        if not is_spellcaster:
            # Return base spell save DC for non-spellcasters
            base_dc = self.config_manager.get_app_config().calculations.spell_save_dc_base
            result = {
                'is_spellcaster': False,
                'spell_slots': [0] * 9,
                'pact_slots': 0,
                'pact_slot_level': 0,
                'spell_save_dc': base_dc,
                'spell_attack_bonus': None,
                'spellcasting_ability': 'None'
            }
            # Add individual spell slot levels for backward compatibility
            for i in range(1, 10):
                result[f'spell_slots_level_{i}'] = 0
            return result
        
        # Calculate spell slots
        spell_slots = self.calculate_spell_slots(character, raw_data)
        
        # Calculate spell save DC and attack bonus
        spell_save_dc = self.calculate_spell_save_dc(character, raw_data)
        spell_attack_bonus = self.calculate_spell_attack_bonus(character, raw_data)
        spellcasting_ability = self.detect_spellcasting_ability(character, raw_data)
        
        # Get spell information
        spell_info = self._get_spell_information(raw_data)
        
        # Capitalize spellcasting ability for consistency with tests
        formatted_ability = spellcasting_ability.capitalize() if spellcasting_ability else 'None'
        
        result = {
            'is_spellcaster': True,
            'spellcasting_ability': formatted_ability,
            'spell_save_dc': spell_save_dc,
            'spell_attack_bonus': spell_attack_bonus,
            'spell_slots': spell_slots.get('regular_slots', [0] * 9),
            'pact_slots': spell_slots.get('pact_slots', 0),
            'pact_slot_level': spell_slots.get('pact_slot_level', 0),
            'caster_level': spell_slots.get('caster_level', 0),
            'spell_slot_breakdown': spell_slots.get('breakdown', {}),
            'spell_counts': spell_info
        }
        
        # Add individual spell slot levels for backward compatibility
        regular_slots = spell_slots.get('regular_slots', [0] * 9)
        pact_slots = spell_slots.get('pact_slots', 0)
        pact_slot_level = spell_slots.get('pact_slot_level', 0)
        
        for i in range(1, 10):
            regular_count = regular_slots[i-1] if i-1 < len(regular_slots) else 0
            # For Warlocks, add pact slots to the appropriate level
            if i == pact_slot_level and pact_slots > 0:
                result[f'spell_slots_level_{i}'] = regular_count + pact_slots
            else:
                result[f'spell_slots_level_{i}'] = regular_count
        
        logger.debug(f"Spellcasting: DC {spell_save_dc}, Attack +{spell_attack_bonus}, Ability {spellcasting_ability}")
        logger.debug(f"Spell slots: {spell_slots.get('regular_slots', [])}, Pact: {spell_slots.get('pact_slots', 0)}")
        
        return result
    
    def validate_inputs(self, character: Character, raw_data: Dict[str, Any]) -> bool:
        """Validate that we have sufficient data for spellcasting calculation."""
        # Spellcasting calculation is optional and can work with minimal data
        return True
    
    def calculate_spell_slots(self, character: Character, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate spell slots by level with multiclass support.
        
        Args:
            character: Character data model
            raw_data: Raw D&D Beyond character data
            
        Returns:
            Dictionary with spell slot information
        """
        logger.debug("Calculating spell slots")
        
        # Check if spell slots are directly provided in API with meaningful values
        spell_slots_data = raw_data.get('spellSlots', [])
        if spell_slots_data:
            regular_slots = self._parse_api_spell_slots(spell_slots_data)
            # Only use API data if it has non-zero values
            if sum(regular_slots) > 0:
                logger.debug(f"Using API spell slots: {regular_slots}")
                
                # Still calculate pact magic separately
                pact_slots, pact_level = self._calculate_pact_magic(raw_data)
                
                return {
                    'regular_slots': regular_slots,
                    'pact_slots': pact_slots,
                    'pact_slot_level': pact_level,
                    'source': 'api',
                    'caster_level': sum(regular_slots)  # Rough estimate
                }
            else:
                logger.debug(f"API spell slots are all zero: {regular_slots}, calculating from class levels")
        
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
                caster_levels[class_name] = {'level': class_level, 'type': 'third'}
        
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
        
        # Get spell slot progression
        if total_caster_level > 0:
            regular_slots = self._get_spell_slots_for_level(total_caster_level)
        else:
            regular_slots = [0] * 9
        
        # Calculate Warlock pact magic
        pact_slots, pact_level = self._calculate_pact_magic_from_level(warlock_levels)
        
        logger.debug(f"Multiclass caster level: {total_caster_level}")
        logger.debug(f"Regular slots: {regular_slots}")
        logger.debug(f"Pact magic: {pact_slots} slots of level {pact_level}")
        
        return {
            'regular_slots': regular_slots,
            'pact_slots': pact_slots,
            'pact_slot_level': pact_level,
            'caster_level': total_caster_level,
            'breakdown': breakdown,
            'source': 'calculated'
        }
    
    def calculate_spell_save_dc(self, character: Character, raw_data: Dict[str, Any]) -> Optional[int]:
        """
        Calculate spell save DC.
        
        Args:
            character: Character data model
            raw_data: Raw D&D Beyond character data
            
        Returns:
            Spell save DC or None if not a spellcaster
        """
        logger.debug("Calculating spell save DC")
        
        # PRIORITY 1: Check for direct spell_save_dc field (v6.0.0 structure)
        spellcasting_data = raw_data.get('spellcasting', {})
        if 'spell_save_dc' in spellcasting_data:
            save_dc = spellcasting_data['spell_save_dc']
            logger.debug(f"Using direct spell save DC: {save_dc}")
            return save_dc
        
        # PRIORITY 2: Calculate from spellcasting ability
        # Get spellcasting ability
        spellcasting_ability = self.detect_spellcasting_ability(character, raw_data)
        if not spellcasting_ability:
            return None
        
        # Get ability modifier
        ability_modifier = self._get_ability_modifier(raw_data, spellcasting_ability)
        
        # Get proficiency bonus
        proficiency_bonus = self._get_proficiency_bonus(raw_data)
        
        # Calculate save DC: 8 + proficiency + ability modifier
        base_dc = self.config_manager.get_app_config().calculations.spell_save_dc_base
        save_dc = base_dc + proficiency_bonus + ability_modifier
        
        logger.debug(f"Spell save DC: {save_dc} (base:{base_dc} + prof:{proficiency_bonus} + {spellcasting_ability}:{ability_modifier})")
        return save_dc
    
    def calculate_spell_attack_bonus(self, character: Character, raw_data: Dict[str, Any]) -> Optional[int]:
        """
        Calculate spell attack bonus.
        
        Args:
            character: Character data model
            raw_data: Raw D&D Beyond character data
            
        Returns:
            Spell attack bonus or None if not a spellcaster
        """
        logger.debug("Calculating spell attack bonus")
        
        # PRIORITY 1: Check for direct spell_attack_bonus field (v6.0.0 structure)
        spellcasting_data = raw_data.get('spellcasting', {})
        if 'spell_attack_bonus' in spellcasting_data:
            attack_bonus = spellcasting_data['spell_attack_bonus']
            logger.debug(f"Using direct spell attack bonus: {attack_bonus}")
            return attack_bonus
        
        # PRIORITY 2: Calculate from spellcasting ability
        # Get spellcasting ability
        spellcasting_ability = self.detect_spellcasting_ability(character, raw_data)
        if not spellcasting_ability:
            return None
        
        # Get ability modifier
        ability_modifier = self._get_ability_modifier(raw_data, spellcasting_ability)
        
        # Get proficiency bonus
        proficiency_bonus = self._get_proficiency_bonus(raw_data)
        
        # Calculate attack bonus: proficiency + ability modifier
        attack_bonus = proficiency_bonus + ability_modifier
        
        logger.debug(f"Spell attack bonus: +{attack_bonus} (prof:{proficiency_bonus} + {spellcasting_ability}:{ability_modifier})")
        return attack_bonus
    
    def detect_spellcasting_ability(self, character: Character, raw_data: Dict[str, Any]) -> Optional[str]:
        """
        Detect primary spellcasting ability.
        
        Args:
            character: Character data model
            raw_data: Raw D&D Beyond character data
            
        Returns:
            Primary spellcasting ability name or None
        """
        logger.debug("Detecting spellcasting ability")
        
        # PRIORITY 1: Check character-level spellcasting data first (v6.0.0 structure)
        spellcasting_data = raw_data.get('spellcasting', {})
        if spellcasting_data.get('spellcasting_ability'):
            ability = spellcasting_data['spellcasting_ability']
            logger.debug(f"Using character-level spellcasting ability: {ability}")
            return ability
        
        # PRIORITY 2: Fall back to class-based detection
        classes = raw_data.get('classes', [])
        
        # For multiclass, find the highest level spellcaster
        best_caster = None
        best_level = 0
        
        for class_data in classes:
            class_def = class_data.get('definition', {})
            class_name = class_def.get('name', '').lower()
            class_level = class_data.get('level', 0)
            
            # Check if this is a spellcaster (including third-casters)
            is_caster = (class_name in self.default_spellcasting_abilities or 
                        self._is_third_caster(class_name, class_data) or
                        class_def.get('canCastSpells', False))
            
            if is_caster:
                # Prioritize full casters, then higher levels
                priority = 0
                if class_name in self.full_casters:
                    priority = class_level * 3
                elif class_name in self.half_casters:
                    priority = class_level * 2
                elif class_name == 'warlock':
                    priority = class_level * 3  # Warlock is effectively full caster for this
                elif self._is_third_caster(class_name, class_data):
                    priority = class_level * 1  # Third casters have lower priority
                else:
                    priority = class_level
                
                if priority > best_level:
                    best_caster = class_name
                    best_level = priority
        
        if best_caster:
            spellcasting_ability = self.default_spellcasting_abilities[best_caster]
            logger.debug(f"Primary spellcasting ability: {spellcasting_ability} (from {best_caster})")
            return spellcasting_ability
        
        # Check if any class has explicit spellcasting ability
        for class_data in classes:
            class_def = class_data.get('definition', {})
            if class_def.get('canCastSpells', False):
                ability_id = class_def.get('spellcastingAbilityId')
                if ability_id:
                    ability_map = {1: 'strength', 2: 'dexterity', 3: 'constitution', 4: 'intelligence', 5: 'wisdom', 6: 'charisma'}
                    ability = ability_map.get(ability_id)
                    if ability:
                        logger.debug(f"Spellcasting ability from class definition: {ability}")
                        return ability
        
        return None
    
    def _is_spellcaster(self, raw_data: Dict[str, Any]) -> bool:
        """Check if character has any spellcasting capabilities."""
        classes = raw_data.get('classes', [])
        
        for class_data in classes:
            class_def = class_data.get('definition', {})
            class_name = class_def.get('name', '').lower()
            
            if (class_name in self.full_casters or 
                class_name in self.half_casters or 
                class_name == 'warlock' or
                self._is_third_caster(class_name, class_data)):
                return True
        
        # Also check for spells from other sources
        spells = raw_data.get('spells', {})
        class_spells = raw_data.get('classSpells', [])
        
        if spells or class_spells:
            return True
        
        return False
    
    def _is_third_caster(self, class_name: str, class_data: Dict[str, Any]) -> bool:
        """Check if character has third-caster subclass (Eldritch Knight, Arcane Trickster)."""
        if class_name not in ['fighter', 'rogue']:
            return False
        
        # Check if the class is explicitly marked as a spellcaster
        class_def = class_data.get('definition', {})
        if class_def.get('canCastSpells', False):
            return True
        
        subclass_def = class_data.get('subclassDefinition', {})
        if not subclass_def:
            return False
        
        subclass_name = subclass_def.get('name', '').lower()
        
        third_caster_subclasses = ['eldritch knight', 'arcane trickster']
        
        return subclass_name in third_caster_subclasses
    
    def _parse_api_spell_slots(self, spell_slots_data: List[Dict[str, Any]]) -> List[int]:
        """Parse spell slots from D&D Beyond API data."""
        slots = [0] * 9
        
        for slot_data in spell_slots_data:
            level = slot_data.get('level', 0)
            available = slot_data.get('available', 0)
            
            if 1 <= level <= 9:
                slots[level - 1] = available
        
        return slots
    
    def _calculate_pact_magic(self, raw_data: Dict[str, Any]) -> Tuple[int, int]:
        """Calculate Warlock pact magic slots from API data."""
        # Check for pact magic in spell slots
        spell_slots_data = raw_data.get('spellSlots', [])
        
        for slot_data in spell_slots_data:
            slot_type = slot_data.get('type', '').lower()
            if 'pact' in slot_type or 'warlock' in slot_type:
                slots = slot_data.get('available', 0)
                level = slot_data.get('level', 1)
                return slots, level
        
        # Fallback to calculating from Warlock levels
        classes = raw_data.get('classes', [])
        for class_data in classes:
            class_def = class_data.get('definition', {})
            if class_def.get('name', '').lower() == 'warlock':
                warlock_level = class_data.get('level', 0)
                return self._calculate_pact_magic_from_level(warlock_level)
        
        return 0, 0
    
    def _calculate_pact_magic_from_level(self, warlock_level: int) -> Tuple[int, int]:
        """Calculate pact magic slots and level from Warlock level."""
        if warlock_level == 0:
            return 0, 0
        elif warlock_level == 1:
            return 1, 1
        elif warlock_level <= 2:
            return 2, 1
        elif warlock_level <= 4:
            return 2, 2
        elif warlock_level <= 6:
            return 2, 3
        elif warlock_level <= 8:
            return 2, 4
        elif warlock_level <= 10:
            return 2, 5
        elif warlock_level <= 16:
            return 3, 5
        elif warlock_level <= 18:
            return 4, 5
        else:  # Level 19-20
            return 4, 5
    
    def _get_spell_slots_for_level(self, caster_level: int) -> List[int]:
        """Get spell slot array for given caster level."""
        # Use 2024 rules by default, fall back to 2014
        rules_2024 = self.config_manager.get_rules_config("2024")
        progression = rules_2024.spell_progressions.full_caster
        
        if caster_level in progression:
            return progression[caster_level]
        elif caster_level > 20:
            return progression[20]  # Max out at level 20
        else:
            return [0] * 9
    
    def _get_ability_modifier(self, raw_data: Dict[str, Any], ability_name: str) -> int:
        """Get ability modifier for given ability, including bonuses."""
        # Try new data structure first (abilities.ability_scores)
        abilities = raw_data.get('abilities', {})
        ability_scores = abilities.get('ability_scores', {})

        if ability_scores and ability_name in ability_scores:
            modifier = ability_scores[ability_name].get('modifier', 0)
            logger.debug(f"Found {ability_name} modifier {modifier} in new data structure")
            return modifier

        # Fallback to old data structure - calculate effective ability score including bonuses
        effective_score = self._get_effective_ability_score(raw_data, ability_name)
        modifier = (effective_score - 10) // 2
        logger.debug(f"Calculated {ability_name} effective score {effective_score}, modifier {modifier}")
        return modifier

    def _get_effective_ability_score(self, raw_data: Dict[str, Any], ability_name: str) -> int:
        """Get effective ability score (base + bonuses) for given ability."""
        ability_id_map = {
            'strength': 1,
            'dexterity': 2,
            'constitution': 3,
            'intelligence': 4,
            'wisdom': 5,
            'charisma': 6
        }

        ability_id = ability_id_map.get(ability_name.lower())
        if not ability_id:
            logger.debug(f"No ability ID found for {ability_name}")
            return 10

        # Get base score from stats array
        base_score = 10
        stats = raw_data.get('stats', [])
        for stat in stats:
            if stat.get('id') == ability_id:
                base_score = stat.get('value', 10)
                break

        # Calculate bonuses from modifiers
        total_bonus = 0
        modifiers = raw_data.get('modifiers', [])

        for modifier in modifiers:
            if not isinstance(modifier, dict):
                continue

            # Check if this modifier affects this ability score
            if self._modifier_affects_ability(modifier, ability_name, ability_id):
                bonus = self._extract_ability_bonus(modifier, ability_name, ability_id)
                if bonus:
                    total_bonus += bonus
                    logger.debug(f"Found {ability_name} bonus +{bonus} from modifier: {modifier.get('friendlyTypeName', 'Unknown')}")

        # Check bonusStats for additional bonuses
        bonus_stats = raw_data.get('bonusStats', [])
        for bonus_stat in bonus_stats:
            if isinstance(bonus_stat, dict) and bonus_stat.get('id') == ability_id:
                bonus_value = bonus_stat.get('value')
                if bonus_value is not None and bonus_value != 0:
                    total_bonus += bonus_value
                    logger.debug(f"Found {ability_name} bonus +{bonus_value} from bonusStats")

        # Check choices for ability score improvements (especially from feats/backgrounds)
        choices = raw_data.get('choices', {})
        feat_choices = choices.get('feat', [])

        for choice in feat_choices:
            if not isinstance(choice, dict):
                continue

            # Look for ability score choices (subType 5)
            if choice.get('subType') == 5:
                option_value = choice.get('optionValue')
                bonus = self._get_ability_bonus_from_choice_option(option_value, ability_name)
                if bonus > 0:
                    total_bonus += bonus
                    component_id = choice.get('componentId')
                    logger.debug(f"Found {ability_name} bonus +{bonus} from feat choice (component {component_id}, option {option_value})")

        effective_score = base_score + total_bonus
        logger.debug(f"{ability_name}: base {base_score} + bonus {total_bonus} = effective {effective_score}")
        return effective_score

    def _get_ability_bonus_from_choice_option(self, option_value: int, ability_name: str) -> int:
        """Map choice option values to ability score bonuses."""
        if not option_value:
            return 0

        # Known mappings from D&D Beyond choice options
        # These are based on the Sage background ability score choices
        ability_choice_mappings = {
            # +2 bonuses (Constitution, Intelligence, Wisdom)
            6260: ('constitution', 2),
            6261: ('intelligence', 2),
            6262: ('wisdom', 2),
            # +1 bonuses (Constitution, Intelligence, Wisdom)
            6263: ('constitution', 1),
            6264: ('intelligence', 1),
            6265: ('wisdom', 1),
        }

        if option_value in ability_choice_mappings:
            mapped_ability, bonus = ability_choice_mappings[option_value]
            if mapped_ability.lower() == ability_name.lower():
                return bonus

        return 0

    def _modifier_affects_ability(self, modifier: Dict[str, Any], ability_name: str, ability_id: int) -> bool:
        """Check if a modifier affects the specified ability score."""
        # Check subType for ability score modifiers
        sub_type = modifier.get('subType', '')
        if sub_type == f"{ability_name.lower()}-score":
            return True

        # Check friendlySubTypeName
        friendly_sub_type = modifier.get('friendlySubTypeName', '').lower()
        if ability_name.lower() in friendly_sub_type and 'score' in friendly_sub_type:
            return True

        # Check componentId and componentTypeId for ability score improvements
        component_type_id = modifier.get('componentTypeId')
        if component_type_id == 12:  # Ability Score Improvement component type
            # Check if this ASI affects our ability
            component_id = modifier.get('componentId')
            if component_id == ability_id:
                return True

        return False

    def _extract_ability_bonus(self, modifier: Dict[str, Any], ability_name: str, ability_id: int) -> int:
        """Extract the bonus value from an ability score modifier."""
        # Check fixedValue for simple bonuses
        fixed_value = modifier.get('fixedValue')
        if fixed_value is not None:
            return fixed_value

        # Check value field
        value = modifier.get('value')
        if value is not None:
            return value

        # Some modifiers store the bonus in other fields
        bonus = modifier.get('bonus')
        if bonus is not None:
            return bonus

        # Default to +1 for ability score improvements if no explicit value
        component_type_id = modifier.get('componentTypeId')
        if component_type_id == 12:  # Ability Score Improvement
            return 1

        return 0
    
    def _get_proficiency_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Get proficiency bonus based on character level."""
        total_level = 0
        classes = raw_data.get('classes', [])
        
        for class_data in classes:
            total_level += class_data.get('level', 0)
        
        # Proficiency bonus progression
        proficiency_bonus = self.constants.proficiency_bonus.get(total_level, 2)
        
        return proficiency_bonus
    
    def _get_spell_information(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get spell count information."""
        # Count spells from various sources
        class_spells = raw_data.get('classSpells', [])
        other_spells = raw_data.get('spells', {})
        
        total_spells = 0
        cantrips = 0
        leveled_spells = 0
        
        # Count class spells
        for class_spell_data in class_spells:
            spells = class_spell_data.get('spells', [])
            for spell in spells:
                spell_def = spell.get('definition', {})
                level = spell_def.get('level', 0)
                
                total_spells += 1
                if level == 0:
                    cantrips += 1
                else:
                    leveled_spells += 1
        
        # Count other spells (race, feat, item)
        for source, spells in other_spells.items():
            if isinstance(spells, list):
                for spell in spells:
                    spell_def = spell.get('definition', {})
                    level = spell_def.get('level', 0)
                    
                    total_spells += 1
                    if level == 0:
                        cantrips += 1
                    else:
                        leveled_spells += 1
        
        return {
            'total_spells': total_spells,
            'cantrips': cantrips,
            'leveled_spells': leveled_spells
        }