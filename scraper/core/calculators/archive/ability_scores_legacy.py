"""
Ability Score Calculator

Calculates ability scores from D&D Beyond data with full source breakdown.
Handles 2014 vs 2024 rule differences.
"""

from typing import Dict, Any, List, Optional, Tuple
import logging

from scraper.core.interfaces.calculator import AbilityScoreCalculatorInterface
from shared.models.character import Character
from shared.models.base import SourcedValue
from shared.config.manager import get_config_manager

logger = logging.getLogger(__name__)


class AbilityScoreCalculator(AbilityScoreCalculatorInterface):
    """
    Calculator for ability scores with comprehensive source tracking.
    
    Handles:
    - Base ability scores from character creation
    - Species/racial bonuses (2014 vs 2024 differences)
    - ASI choices from leveling up
    - Feat bonuses
    - Item bonuses
    - Manual overrides and "set" type modifiers
    """
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.constants = self.config_manager.get_constants_config()
        
        # Ability mappings
        self.ability_names = self.constants.abilities.names
        self.ability_id_map = self.constants.abilities.id_mappings
        self.choice_mappings = self.constants.abilities.choice_mappings
        
    def calculate(self, character: Character, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate all ability scores with complete breakdown.
        
        Returns:
            Dictionary containing final scores, modifiers, and source breakdown
        """
        logger.info(f"Calculating ability scores for character {character.id}")
        
        # Calculate final scores with sources
        ability_breakdown = self.calculate_final_scores(raw_data)
        
        # Extract final scores and modifiers
        final_scores = {}
        final_modifiers = {}
        
        for ability in self.ability_names:
            final_scores[ability] = ability_breakdown[ability]['total']
            final_modifiers[ability] = (final_scores[ability] - 10) // 2
        
        # Format ability scores as individual objects for compatibility
        ability_scores = {}
        for ability in self.ability_names:
            # Create simple breakdown format
            total_score = final_scores[ability]
            simple_breakdown = {}
            
            # Attempt to reconstruct base + racial format
            # Look at the source breakdown to understand the composition
            sources = ability_breakdown[ability]['sources']
            
            if len(sources) == 1:
                # Single source
                source = sources[0]
                if source['source_type'] == 'base':
                    # If base score differs from 10, it's the only source
                    if source['value'] != 10:
                        simple_breakdown['base'] = source['value']
                    else:
                        # Base score is 10, this shouldn't be a single source
                        simple_breakdown['base'] = source['value']
                elif source['source_type'] == 'asi':
                    # Single ASI source - treat as racial for compatibility
                    simple_breakdown['base'] = 10
                    simple_breakdown['race'] = source['value']
                else:
                    simple_breakdown['base'] = source['value']
            elif len(sources) == 2:
                # Two sources - base + one other (likely base + racial/asi/feat)
                base_value = 0
                racial_value = 0
                feat_value = 0
                asi_value = 0
                item_value = 0
                other_value = 0
                
                for source in sources:
                    if source['source_type'] == 'base':
                        base_value = source['value']
                    elif source['source_type'] in ['racial', 'race']:
                        racial_value += source['value']
                    elif source['source_type'] == 'feat':
                        feat_value += source['value']
                    elif source['source_type'] == 'asi':
                        asi_value += source['value']
                    elif source['source_type'] == 'item':
                        item_value += source['value']
                    elif source['source_type'] == 'other':
                        other_value += source['value']
                
                simple_breakdown['base'] = base_value
                if racial_value > 0:
                    simple_breakdown['race'] = racial_value
                if feat_value > 0:
                    simple_breakdown['feat'] = feat_value
                if asi_value > 0:
                    simple_breakdown['asi'] = asi_value
                if item_value > 0:
                    simple_breakdown['item'] = item_value
                if other_value > 0:
                    simple_breakdown['other'] = other_value
            else:
                # Multiple sources - sum up by type
                base_total = 0
                racial_total = 0
                feat_total = 0
                asi_total = 0
                item_total = 0
                other_total = 0
                
                for source in sources:
                    if source['source_type'] == 'base':
                        base_total = source['value']
                    elif source['source_type'] in ['racial', 'race']:
                        racial_total += source['value']
                    elif source['source_type'] == 'feat':
                        feat_total += source['value']
                    elif source['source_type'] == 'asi':
                        asi_total += source['value']
                    elif source['source_type'] == 'item':
                        item_total += source['value']
                    elif source['source_type'] == 'other':
                        other_total += source['value']
                
                simple_breakdown['base'] = base_total
                if racial_total > 0:
                    simple_breakdown['race'] = racial_total
                if feat_total > 0:
                    simple_breakdown['feat'] = feat_total
                if asi_total > 0:
                    simple_breakdown['asi'] = asi_total
                if item_total > 0:
                    simple_breakdown['item'] = item_total
                if other_total > 0:
                    simple_breakdown['other'] = other_total
            
            # If we still don't have a breakdown, provide fallback
            if not simple_breakdown:
                simple_breakdown['base'] = total_score
            
            # Calculate save bonus (modifier + proficiency if proficient)
            save_bonus = self._calculate_save_bonus(ability, final_modifiers[ability], raw_data)
            
            ability_scores[ability] = {
                'score': final_scores[ability],
                'modifier': final_modifiers[ability],
                'save_bonus': save_bonus,
                'source_breakdown': simple_breakdown
            }
        
        result = {
            'ability_scores': ability_scores,
            'ability_modifiers': final_modifiers,
            'ability_score_breakdown': ability_breakdown,
            'calculation_method': 'comprehensive'
        }
        
        logger.debug(f"Calculated ability scores: {final_scores}")
        return result
    
    def validate_inputs(self, character: Character, raw_data: Dict[str, Any]) -> bool:
        """Validate that we have sufficient data for ability score calculation."""
        required_fields = ['stats']
        
        for field in required_fields:
            if field not in raw_data:
                logger.error(f"Missing required field for ability scores: {field}")
                return False
        
        # Check that stats array has data
        stats = raw_data.get('stats', [])
        if not stats or len(stats) < 6:
            logger.error(f"Insufficient ability score data: expected 6 abilities, got {len(stats)}")
            return False
        
        return True
    
    def calculate_base_scores(self, raw_data: Dict[str, Any]) -> Dict[str, int]:
        """
        Calculate base ability scores from character creation (before modifiers).
        
        Args:
            raw_data: Raw D&D Beyond character data
            
        Returns:
            Dictionary of base ability scores
        """
        logger.debug("Calculating base ability scores")
        
        base_scores = {}
        stats = raw_data.get('stats', [])
        
        for stat in stats:
            ability_id = stat.get('id')
            base_value = stat.get('value', 10)
            
            if ability_id in self.ability_id_map:
                ability_name = self.ability_id_map[ability_id]
                base_scores[ability_name] = base_value
                logger.debug(f"Base {ability_name}: {base_value}")
        
        # Ensure all abilities are present
        for ability in self.ability_names:
            if ability not in base_scores:
                base_scores[ability] = 10
                logger.warning(f"Missing base score for {ability}, defaulting to 10")
        
        return base_scores
    
    def calculate_racial_bonuses(self, raw_data: Dict[str, Any]) -> Dict[str, int]:
        """
        Calculate ability score bonuses from species/race.
        
        Args:
            raw_data: Raw D&D Beyond character data
            
        Returns:
            Dictionary of racial ability score bonuses
        """
        logger.debug("Calculating racial ability score bonuses")
        
        racial_bonuses = {ability: 0 for ability in self.ability_names}
        
        # Check race data
        race_data = raw_data.get('race', {})
        if not race_data:
            logger.debug("No race data found")
            return racial_bonuses
        
        # Method 1: Get racial ASI from race definition (traditional approach)
        race_definition = race_data.get('definition', {})
        ability_score_increases = race_definition.get('abilityScoreIncreases', [])
        
        for asi in ability_score_increases:
            ability_id = asi.get('entityId')
            value = asi.get('value', 0)
            
            if ability_id in self.ability_id_map:
                ability_name = self.ability_id_map[ability_id]
                racial_bonuses[ability_name] += value
                logger.debug(f"Racial bonus {ability_name}: +{value} (from definition)")
        
        # Also check for subrace bonuses
        if 'subRace' in race_data and race_data['subRace']:
            subrace_definition = race_data['subRace'].get('definition', {})
            subrace_asi = subrace_definition.get('abilityScoreIncreases', [])
            
            for asi in subrace_asi:
                ability_id = asi.get('entityId')
                value = asi.get('value', 0)
                
                if ability_id in self.ability_id_map:
                    ability_name = self.ability_id_map[ability_id]
                    racial_bonuses[ability_name] += value
                    logger.debug(f"Subrace bonus {ability_name}: +{value} (from definition)")
        
        # Method 2: Check for racial ability score modifiers in modifiers.race 
        # (needed for some races like Warforged where bonuses are stored as modifiers)
        # Only use this if no 2024 racial ASI choices are detected to avoid double-counting
        has_2024_racial_asi = self._has_2024_racial_asi_choices(raw_data)
        
        if not has_2024_racial_asi:
            modifiers = raw_data.get('modifiers', {})
            race_modifiers = modifiers.get('race', [])
            
            for modifier in race_modifiers:
                if self._is_ability_score_modifier(modifier):
                    ability_name, bonus = self._extract_ability_modifier(modifier)
                    if ability_name:
                        racial_bonuses[ability_name] += bonus
                        logger.debug(f"Racial bonus {ability_name}: +{bonus} (from modifiers)")
        else:
            logger.debug("Skipping modifier-based racial bonuses - 2024 racial ASI choices detected")
        
        return racial_bonuses
    
    def calculate_feat_bonuses(self, raw_data: Dict[str, Any]) -> Dict[str, int]:
        """
        Calculate ability score bonuses from feats.
        
        Args:
            raw_data: Raw D&D Beyond character data
            
        Returns:
            Dictionary of feat ability score bonuses
        """
        logger.debug("Calculating feat ability score bonuses")
        
        feat_bonuses = {ability: 0 for ability in self.ability_names}
        
        # Check modifiers for feat-based ability score increases
        modifiers = raw_data.get('modifiers', {})
        
        # Look in feat modifiers
        feat_modifiers = modifiers.get('feat', [])
        
        for modifier in feat_modifiers:
            if self._is_ability_score_modifier(modifier):
                ability_name, bonus = self._extract_ability_modifier(modifier)
                if ability_name:
                    feat_bonuses[ability_name] += bonus
                    logger.debug(f"Feat bonus {ability_name}: +{bonus}")
        
        return feat_bonuses
    
    def calculate_final_scores(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate final ability scores with complete source breakdown.
        
        Args:
            raw_data: Raw D&D Beyond character data
            
        Returns:
            Dictionary with detailed breakdown for each ability
        """
        logger.debug("Calculating final ability scores with breakdown")
        
        # Get base scores
        base_scores = self.calculate_base_scores(raw_data)
        racial_bonuses = self.calculate_racial_bonuses(raw_data)
        feat_bonuses = self.calculate_feat_bonuses(raw_data)
        
        # Calculate ASI and choice bonuses
        asi_bonuses = self._calculate_asi_bonuses(raw_data)
        item_bonuses = self._calculate_item_bonuses(raw_data)
        other_bonuses = self._calculate_other_bonuses(raw_data)
        
        # Build comprehensive breakdown
        breakdown = {}
        
        for ability in self.ability_names:
            base = base_scores.get(ability, 10)
            racial = racial_bonuses.get(ability, 0)
            feat = feat_bonuses.get(ability, 0)
            asi = asi_bonuses.get(ability, 0)
            item = item_bonuses.get(ability, 0)
            other = other_bonuses.get(ability, 0)
            
            total = base + racial + feat + asi + item + other
            
            # Build source list - always include base, and others if non-zero
            sources = []
            sources.append(SourcedValue(value=base, source="Base Score", source_type="base"))
            if racial != 0:
                sources.append(SourcedValue(value=racial, source="Species/Race", source_type="racial"))
            if feat != 0:
                sources.append(SourcedValue(value=feat, source="Feats", source_type="feat"))
            if asi != 0:
                sources.append(SourcedValue(value=asi, source="ASI/Choices", source_type="asi"))
            if item != 0:
                sources.append(SourcedValue(value=item, source="Items", source_type="item"))
            if other != 0:
                sources.append(SourcedValue(value=other, source="Other", source_type="other"))
            
            breakdown[ability] = {
                'total': total,
                'base': base,
                'racial': racial,
                'feat': feat,
                'asi': asi,
                'item': item,
                'other': other,
                'sources': [source.dict() for source in sources]
            }
            
            logger.debug(f"{ability.title()}: {total} (base:{base} racial:{racial} feat:{feat} asi:{asi} item:{item} other:{other})")
        
        return breakdown
    
    def _calculate_asi_bonuses(self, raw_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate ability score improvements from ASI choices and class leveling."""
        asi_bonuses = {ability: 0 for ability in self.ability_names}
        
        # Method 1: Check choices for ASI selections
        choices = raw_data.get('choices', {})
        
        for source_type, choice_list in choices.items():
            if not isinstance(choice_list, list):
                continue
                
            for choice in choice_list:
                if self._is_asi_choice(choice):
                    ability_name, bonus = self._extract_asi_choice(choice)
                    if ability_name:
                        asi_bonuses[ability_name] += bonus
                        logger.debug(f"ASI choice {ability_name}: +{bonus}")
                elif self._is_2024_racial_asi_choice(choice):
                    ability_name, bonus = self._extract_2024_racial_asi_choice(choice, raw_data)
                    if ability_name:
                        asi_bonuses[ability_name] += bonus
                        logger.debug(f"2024 Racial ASI {ability_name}: +{bonus}")
        
        # Method 2: Check class modifiers for ASI improvements (when choices don't capture them)
        modifiers = raw_data.get('modifiers', {})
        class_modifiers = modifiers.get('class', [])
        
        for modifier in class_modifiers:
            if self._is_ability_score_modifier(modifier):
                ability_name, bonus = self._extract_ability_modifier(modifier)
                if ability_name:
                    asi_bonuses[ability_name] += bonus
                    logger.debug(f"Class ASI {ability_name}: +{bonus} (from modifiers)")
        
        return asi_bonuses
    
    def _calculate_item_bonuses(self, raw_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate ability score bonuses from magic items. Handles both additive bonuses and "set" type modifiers."""
        item_bonuses = {ability: 0 for ability in self.ability_names}
        item_set_values = {}  # Track "set" type modifiers separately
        
        # Check modifiers for item-based ability score increases
        modifiers = raw_data.get('modifiers', {})
        item_modifiers = modifiers.get('item', [])
        
        for modifier in item_modifiers:
            if self._is_ability_score_modifier(modifier):
                ability_name, value = self._extract_ability_modifier(modifier)
                if ability_name:
                    if value < -999000:  # Special encoding for "set" type
                        set_value = value + 999999
                        item_set_values[ability_name] = set_value
                        logger.debug(f"Item sets {ability_name} to: {set_value}")
                    else:
                        item_bonuses[ability_name] += value
                        logger.debug(f"Item bonus {ability_name}: +{value}")
        
        # Apply set values by calculating the difference from base
        if item_set_values:
            base_scores = self.calculate_base_scores(raw_data)
            for ability_name, set_value in item_set_values.items():
                base_score = base_scores.get(ability_name, 10)
                # Calculate what bonus would be needed to reach the set value
                needed_bonus = set_value - base_score
                item_bonuses[ability_name] = needed_bonus
                logger.debug(f"Item sets {ability_name} from {base_score} to {set_value} (bonus: {needed_bonus})")
        
        return item_bonuses
    
    def _calculate_other_bonuses(self, raw_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate ability score bonuses from other sources (excluding ASI from classes)."""
        other_bonuses = {ability: 0 for ability in self.ability_names}
        
        # Check for other modifier sources
        modifiers = raw_data.get('modifiers', {})
        
        for source_type, modifier_list in modifiers.items():
            if source_type in ['race', 'feat', 'item', 'class']:
                continue  # Already handled in dedicated methods or should be treated as ASI
                
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                if self._is_ability_score_modifier(modifier):
                    ability_name, bonus = self._extract_ability_modifier(modifier)
                    if ability_name:
                        other_bonuses[ability_name] += bonus
                        logger.debug(f"Other bonus {ability_name}: +{bonus} (source: {source_type})")
        
        return other_bonuses
    
    def _is_ability_score_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier affects ability scores."""
        modifies_id = modifier.get('modifiesId')
        modifies_type_id = modifier.get('modifiesTypeId')
        sub_type = modifier.get('subType', '')
        
        # Method 1: Traditional ability score modifiers with modifiesTypeId 1
        if modifies_type_id == 1 and modifies_id in self.ability_id_map:
            return True
            
        # Method 2: New format with subType ending in "-score"
        if sub_type.endswith('-score'):
            ability_name = sub_type.replace('-score', '').replace('-', '_')
            return ability_name in self.ability_names
            
        return False
    
    def _extract_ability_modifier(self, modifier: Dict[str, Any]) -> Tuple[Optional[str], int]:
        """Extract ability name and bonus from a modifier."""
        modifies_id = modifier.get('modifiesId')
        sub_type = modifier.get('subType', '')
        bonus = modifier.get('bonus', 0) or modifier.get('value', 0) or modifier.get('fixedValue', 0)
        
        # Method 1: Traditional format with modifiesId
        if modifies_id in self.ability_id_map:
            ability_name = self.ability_id_map[modifies_id]
            return ability_name, bonus
            
        # Method 2: New format with subType ending in "-score"
        if sub_type.endswith('-score'):
            ability_name = sub_type.replace('-score', '').replace('-', '_')
            if ability_name in self.ability_names:
                return ability_name, bonus
        
        return None, 0
    
    def _is_asi_choice(self, choice: Dict[str, Any]) -> bool:
        """Check if a choice is an ASI selection."""
        choice_id = choice.get('choiceId')
        return choice_id in self.choice_mappings
    
    def _extract_asi_choice(self, choice: Dict[str, Any]) -> Tuple[Optional[str], int]:
        """Extract ability name and bonus from an ASI choice."""
        choice_id = choice.get('choiceId')
        
        if choice_id in self.choice_mappings:
            ability_name = self.choice_mappings[choice_id]
            # ASI choices are typically +1
            bonus = 1
            return ability_name, bonus
        
        return None, 0
    
    def _is_2024_racial_asi_choice(self, choice: Dict[str, Any]) -> bool:
        """Check if a choice is a 2024 racial ASI selection."""
        label = choice.get('label') or ''
        return 'Ability Score' in label and ('increase by' in label or 'Increase by' in label)
    
    def _extract_2024_racial_asi_choice(self, choice: Dict[str, Any], raw_data: Dict[str, Any]) -> Tuple[Optional[str], int]:
        """Extract ability name and bonus from a 2024 racial ASI choice using choice definitions."""
        option_value = choice.get('optionValue')
        label = choice.get('label') or ''
        
        # Determine bonus amount from the choice label
        if 'increase by 2' in label.lower():
            bonus = 2
        elif 'increase by 1' in label.lower():
            bonus = 1
        else:
            bonus = 1  # Default
        
        # Look up the option value in choice definitions to get the ability name
        choice_definitions = raw_data.get('choices', {}).get('choiceDefinitions', [])
        
        for choice_def in choice_definitions:
            if not isinstance(choice_def, dict):
                continue
                
            options = choice_def.get('options', [])
            for option in options:
                if not isinstance(option, dict):
                    continue
                    
                if option.get('id') == option_value:
                    # Found the matching option
                    option_label = option.get('label', '')
                    
                    # Extract ability name from label (e.g., "Strength Score" -> "strength")
                    ability_name = None
                    for ability in self.ability_names:
                        if ability.lower() in option_label.lower():
                            ability_name = ability
                            break
                    
                    if ability_name:
                        logger.debug(f"Resolved 2024 ASI choice: {ability_name} +{bonus} "
                                   f"(optionValue: {option_value}, label: {option_label})")
                        return ability_name, bonus
                    else:
                        logger.warning(f"Could not extract ability name from option label: {option_label}")
                        return None, 0
        
        # Option value not found in definitions
        logger.warning(f"Could not find option value {option_value} in choice definitions. "
                      f"Choice label: {label}")
        return None, 0
    
    def _has_2024_racial_asi_choices(self, raw_data: Dict[str, Any]) -> bool:
        """Check if character has 2024-style racial ASI choices."""
        choices = raw_data.get('choices', {})
        
        for source_type, choice_list in choices.items():
            if not isinstance(choice_list, list):
                continue
                
            for choice in choice_list:
                if self._is_2024_racial_asi_choice(choice):
                    logger.debug("Found 2024 racial ASI choice")
                    return True
        
        return False
    
    def _calculate_save_bonus(self, ability: str, modifier: int, raw_data: Dict[str, Any]) -> int:
        """Calculate saving throw bonus including proficiency if applicable."""
        # Get proficiency bonus
        proficiency_bonus = self._get_proficiency_bonus(raw_data)
        
        # Check if proficient in this save
        save_proficiencies = self._get_save_proficiencies(raw_data)
        
        # Debug logging
        logger.debug(f"Save bonus calculation for {ability}: modifier={modifier}, proficiency={proficiency_bonus}")
        logger.debug(f"Save proficiencies: {save_proficiencies}")
        
        # Check both ability name and ability_save format
        if ability in save_proficiencies or f"{ability}_save" in save_proficiencies:
            result = modifier + proficiency_bonus
            logger.debug(f"Save bonus for {ability}: {modifier} + {proficiency_bonus} = {result} (proficient)")
            return result
        else:
            logger.debug(f"Save bonus for {ability}: {modifier} (not proficient)")
            return modifier
    
    def _get_proficiency_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Get character's proficiency bonus based on level."""
        classes = raw_data.get('classes', [])
        total_level = sum(cls.get('level', 0) for cls in classes) or 1
        return ((total_level - 1) // 4) + 2
    
    def _get_save_proficiencies(self, raw_data: Dict[str, Any]) -> set:
        """Get set of saving throw proficiencies."""
        save_proficiencies = set()
        
        # Check class proficiencies
        classes = raw_data.get('classes', [])
        for class_data in classes:
            class_def = class_data.get('definition', {})
            saving_throws = class_def.get('savingThrows', [])
            
            for save_throw in saving_throws:
                save_id = save_throw.get('id')
                if save_id in self.ability_id_map:
                    ability_name = self.ability_id_map[save_id]
                    # Add both formats for compatibility
                    save_proficiencies.add(ability_name)
                    save_proficiencies.add(f"{ability_name}_save")
        
        return save_proficiencies
    
    def _is_ability_score_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier affects ability scores."""
        sub_type = modifier.get('subType', '')
        return sub_type.endswith('-score') and sub_type in [
            'strength-score', 'dexterity-score', 'constitution-score',
            'intelligence-score', 'wisdom-score', 'charisma-score'
        ]
    
    def _extract_ability_modifier(self, modifier: Dict[str, Any]) -> Tuple[Optional[str], int]:
        """Extract ability name and bonus from a modifier."""
        sub_type = modifier.get('subType', '')
        value = modifier.get('value', 0)
        modifier_type = modifier.get('type', '')
        
        # Map sub_type to ability name
        ability_map = {
            'strength-score': 'strength',
            'dexterity-score': 'dexterity', 
            'constitution-score': 'constitution',
            'intelligence-score': 'intelligence',
            'wisdom-score': 'wisdom',
            'charisma-score': 'charisma'
        }
        
        ability_name = ability_map.get(sub_type)
        if ability_name and value:
            # Handle "set" type modifiers differently than additive bonuses
            if modifier_type == 'set':
                # For set modifiers, return a special indicator
                # We'll handle this in the calling code
                return ability_name, -999999 + value  # Special encoding: -999999 + set_value
            else:
                # Regular additive bonus
                return ability_name, value
        
        return None, 0