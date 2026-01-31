"""
Combat formatter for attacks, actions, and combat-related information.

This module handles the generation of combat sections including
action economy, attacks, and weapon information.
"""

import re
from typing import Dict, Any, List, Optional, Tuple

# Import interfaces and utilities using absolute import
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging

from formatters.base import BaseFormatter
from utils.text import TextProcessor


class CombatFormatter(BaseFormatter):
    """
    Handles combat section generation for character sheets.
    
    Generates comprehensive combat information including action economy,
    attacks, weapon details, and combat actions.
    """
    
    def __init__(self, text_processor: TextProcessor):
        """
        Initialize the combat formatter.
        
        Args:
            text_processor: Text processing utilities
        """
        super().__init__(text_processor)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _get_required_fields(self) -> List[str]:
        """Get list of required fields for combat formatting."""
        return []
    
    def _validate_internal(self, character_data: Dict[str, Any]) -> bool:
        """Validate character data structure for combat formatting."""
        character_info = self.get_character_info(character_data)
        inventory = character_data.get('inventory', [])
        
        # Basic validation
        if not isinstance(inventory, list):
            self.logger.error("Inventory must be a list")
            return False
        
        return True
    
    def _format_internal(self, character_data: Dict[str, Any]) -> str:
        """
        Generate comprehensive combat section.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Formatted combat section
        """
        sections = []
        
        # Header
        sections.append(self._generate_header())
        
        # Action Economy
        sections.append(self._generate_action_economy(character_data))

        # Special Abilities (Other Actions)
        sections.append(self._generate_special_abilities(character_data))

        # Attacks
        sections.append(self._generate_attacks(character_data))
        
        return '\n'.join(section for section in sections if section)
    
    def _generate_header(self) -> str:
        """Generate combat section header."""
        return """## Attacks

<span class="right-link">[[#Character Statistics|Top]]</span>"""
    
    def _generate_action_economy(self, character_data: Dict[str, Any]) -> str:
        """Generate action economy section with proper formatting."""
        section = "\n### Action Economy\n\n"

        # Add explanatory note
        section += ">*Note: Shows cantrips (always available), prepared spells, ritual spells (can be cast unprepared), and always-prepared spells.*\n>\n"

        # Get spells data - this is the primary source for actions
        spells_data = character_data.get('spells', {})
        inventory = character_data.get('inventory', [])
        features = character_data.get('features', {})
        combat_data = character_data.get('combat', {})

        # Process all spells to build action lists
        action_spells, bonus_action_list, reaction_list = self._process_spells_for_actions(spells_data)

        # Add inventory-based actions
        inventory_bonus_actions, inventory_reactions = self._process_inventory_for_actions(inventory)
        bonus_action_list.extend(inventory_bonus_actions)
        reaction_list.extend(inventory_reactions)

        # Add class feature actions
        feature_bonus_actions, feature_reactions = self._process_features_for_actions(features)
        bonus_action_list.extend(feature_bonus_actions)
        reaction_list.extend(feature_reactions)

        # Add attack actions (bonus actions and reactions from combat)
        attack_bonus_actions, attack_reactions = self._process_attack_actions(combat_data)
        bonus_action_list.extend(attack_bonus_actions)
        reaction_list.extend(attack_reactions)
        
        # Sort spells by level then name
        action_spells.sort(key=lambda x: (x[0], x[1]))

        # Get proficiencies data for weapon mastery
        proficiencies_data = character_data.get('proficiencies', {})

        # Build action lists
        section += ">**Action:**\n"
        for level, spell_name in action_spells:
            section += f">- {spell_name}\n"

        # Add weapon attacks with mastery info
        weapon_attacks = combat_data.get('weapon_attacks', [])
        if weapon_attacks:
            for attack in weapon_attacks:
                attack_name = attack.get('name', 'Unknown Weapon')

                # Check if this weapon has mastery
                weapon_masteries = proficiencies_data.get('weapon_masteries', [])
                mastery_type = None
                for mastery in weapon_masteries:
                    if isinstance(mastery, dict) and mastery.get('weapon', '').lower() in attack_name.lower():
                        mastery_type = mastery.get('mastery')
                        break

                if mastery_type:
                    section += f">- {attack_name} ({mastery_type} mastery)\n"
                else:
                    section += f">- {attack_name}\n"

        # Add standard actions
        section += ">- **Standard Actions:** Attack, Cast a Spell, Dash, Disengage, Dodge, Help, Hide, Ready, Search, Use Object\n>\n"
        
        section += ">**Bonus Action:**\n"
        
        # Process bonus actions
        regular_bonus_actions, conditional_bonus_actions = self._categorize_bonus_actions(
            bonus_action_list, spells_data
        )
        
        # Add conditional bonus actions first (from ongoing spells)
        if conditional_bonus_actions:
            section += ">If cast:\n"
            for cba in conditional_bonus_actions:
                section += f">- {cba}\n"
        
        # Add regular bonus actions
        for ba in regular_bonus_actions:
            section += f">- {ba}\n"

        # Add weapon mastery notes (2024 rules)
        weapon_masteries = proficiencies_data.get('weapon_masteries', [])
        if weapon_masteries:
            # Check for Nick mastery specifically as it affects action economy
            nick_weapons = [m.get('weapon') for m in weapon_masteries if isinstance(m, dict) and m.get('mastery') == 'Nick']
            if nick_weapons:
                weapons_str = ', '.join(nick_weapons)
                section += f">- **Nick Mastery ({weapons_str}):** Light weapon extra attack as part of Attack action (not bonus action)\n"

        # Add default bonus actions
        section += ">- **Standard:** Two-Weapon Fighting, Off-Hand Attack\n>\n"
        
        section += ">**Reaction:**\n"
        # Remove duplicates and sort
        unique_reactions = sorted(list(set(reaction_list)))
        for reaction in unique_reactions:
            section += f">- {reaction}\n"
        
        section += ">\n"

        return section

    def _generate_special_abilities(self, character_data: Dict[str, Any]) -> str:
        """
        Generate special abilities section (activation type 8 actions).

        These are special abilities like Sneak Attack, Uncanny Metabolism, Feline Agility, etc.
        that appear in D&D Beyond's "Other" actions section for quick reference during combat.

        Args:
            character_data: Complete character data dictionary

        Returns:
            Formatted special abilities section, or empty string if none found
        """
        # Get special abilities from combat data
        combat_data = character_data.get('combat', {})
        special_abilities = combat_data.get('special_abilities', [])

        # If no special abilities found, return empty string
        if not special_abilities:
            return ""

        # Build the section
        section = "\n### Other Actions\n\n>\n"
        section += ">*Special abilities and passive features available during combat.*\n"
        section += ">\n"

        for ability in special_abilities:
            name = ability.get('name', 'Unknown')
            activation = ability.get('activation', 'Special')
            snippet = ability.get('snippet', '')
            uses = ability.get('uses', {})

            section += f"> #### {name}\n"

            # Format uses information
            uses_text = activation
            if uses:
                max_uses = uses.get('max_uses')
                reset_type = uses.get('reset_type')
                if max_uses:
                    uses_text += f" ({max_uses} use{'s' if max_uses > 1 else ''} per {reset_type})"

            section += f"> **Activation:** {uses_text}\n"

            if snippet:
                # Clean up HTML and formatting
                clean_snippet = self.text_processor.clean_text(snippet)

                # Truncate snippet to reasonable length for quick reference
                if len(clean_snippet) > 200:
                    clean_snippet = clean_snippet[:200] + "..."
                section += f"> **Effect:** {clean_snippet}\n"

            section += "> \n"

        return section

    def _generate_attacks(self, character_data: Dict[str, Any]) -> str:
        """Generate attacks section using enhanced scraper-provided attack data."""
        section = "\n### Attacks\n\n>\n"
        
        # Use enhanced weapon attacks from combat section (new format)
        combat_data = character_data.get('combat', {})
        weapon_attacks = combat_data.get('weapon_attacks', [])
        
        if weapon_attacks:
            for attack in weapon_attacks:
                weapon_section = self._format_enhanced_attack(attack)
                section += weapon_section
        else:
            # Fallback to legacy attack actions
            attack_actions = combat_data.get('attack_actions', [])
            if attack_actions:
                for attack in attack_actions:
                    weapon_section = self._format_scraper_attack(attack)
                    section += weapon_section
            else:
                section += "> *No weapon attacks available. Use equipped weapons or spells for combat.*\n"
        
        section += "> ^combat\n\n---"
        return section
    
    def _format_scraper_attack(self, attack: Dict[str, Any]) -> str:
        """Format a single attack using scraper-provided data."""
        name = attack.get('name', 'Unknown Attack')
        attack_bonus = attack.get('attack_bonus', 0)
        damage_dice = attack.get('damage_dice', '1d4')
        damage_modifier = attack.get('damage_modifier', 0)
        damage_type = attack.get('damage_type', 'piercing')
        attack_type = attack.get('attack_type', 'melee')
        weapon_name = attack.get('weapon_name', 'Unknown Weapon')
        
        section = f"> #### {weapon_name}\n"
        section += f"> **Type:** {attack_type.title()} Weapon\n"
        section += f"> **Attack Bonus:** +{attack_bonus}\n"
        
        # Format damage
        damage_text = damage_dice
        if damage_modifier > 0:
            damage_text += f" + {damage_modifier}"
        elif damage_modifier < 0:
            damage_text += f" - {abs(damage_modifier)}"
        section += f"> **Damage:** {damage_text} {damage_type}\n"
        
        # Add range for ranged attacks
        if attack_type == 'ranged':
            range_normal = attack.get('range_normal', 20)
            range_long = attack.get('range_long', range_normal * 3)
            section += f"> **Range:** {range_normal}/{range_long} ft\n"
        
        section += "> \n"
        
        return section
    
    def _format_enhanced_attack(self, attack: Dict[str, Any]) -> str:
        """Format a single attack using enhanced scraper-provided data with breakdowns."""
        name = attack.get('name', 'Unknown Attack')
        attack_bonus = attack.get('attack_bonus', 0)
        damage_dice = attack.get('damage_dice', '1d4')
        damage_modifier = attack.get('damage_modifier', attack.get('damage_bonus', 0))
        damage_type = attack.get('damage_type', 'piercing')
        attack_type = attack.get('attack_type', attack.get('weapon_type', 'melee'))
        properties = attack.get('properties', [])
        range_info = attack.get('range', '')
        breakdown = attack.get('breakdown', {})

        # Check if this is an action attack (unarmed, racial, etc.) vs weapon attack
        source_type = attack.get('type', 'weapon')
        activation = attack.get('activation_type', '')

        section = f"> #### {name}\n"

        # Format type based on whether it's an action attack or weapon attack
        if source_type == 'action_attack':
            # For action attacks, show the attack type and activation
            type_label = f"{attack_type.title()} Attack"
            if activation:
                activation_formatted = activation.replace('_', ' ').title()
                type_label += f" ({activation_formatted})"
            section += f"> **Type:** {type_label}\n"
        else:
            # For weapon attacks, use the traditional format
            section += f"> **Type:** {attack_type.title()} Weapon\n"

        section += f"> **Attack Bonus:** +{attack_bonus}\n"
        
        # Add breakdown if available
        if breakdown and isinstance(breakdown, dict):
            description = breakdown.get('description', '')
            if description:
                section += f">   *{description}*\n"
        
        # Format damage
        damage_text = damage_dice
        if damage_modifier > 0:
            damage_text += f" + {damage_modifier}"
        elif damage_modifier < 0:
            damage_text += f" - {abs(damage_modifier)}"
        section += f"> **Damage:** {damage_text} {damage_type}\n"
        
        # Add weapon properties
        if properties:
            if isinstance(properties, list):
                props_str = ', '.join(properties)
            else:
                props_str = str(properties)
            section += f"> **Properties:** {props_str}\n"
        
        # Add range for ranged weapons or if range info is available
        if range_info and range_info != 'Melee':
            section += f"> **Range:** {range_info}\n"
        elif attack_type == 'ranged':
            range_normal = attack.get('range_normal', 20)
            range_long = attack.get('range_long', range_normal * 3)
            section += f"> **Range:** {range_normal}/{range_long} ft\n"
        
        section += "> \n"
        
        return section
    
    def _process_spells_for_actions(self, spells_data: Dict[str, Any]) -> Tuple[List[Tuple[int, str]], List[str], List[str]]:
        """Process spells to extract actions, bonus actions, and reactions."""
        action_spells = []
        bonus_action_list = []
        reaction_list = ['Opportunity Attack', 'Ready Action Trigger']
        
        for spell_source in spells_data.values():
            if isinstance(spell_source, list):
                for spell in spell_source:
                    if isinstance(spell, dict):
                        spell_name = spell.get('name', '')
                        spell_level = spell.get('level', 0)
                        description = spell.get('description', '')
                        casting_time = spell.get('casting_time', '')
                        is_prepared = spell.get('is_prepared', False)
                        always_prepared = spell.get('always_prepared', False)
                        ritual = spell.get('ritual', False)
                        
                        if not spell_name:
                            continue
                            
                        # Include cantrips (level 0), prepared spells, always prepared spells, and ritual spells
                        if spell_level == 0 or is_prepared or always_prepared or ritual:
                            # Add to action spells
                            if spell_level == 0:
                                action_spells.append((0, spell_name))
                            else:
                                level_text = f" ({spell_level}{'st' if spell_level == 1 else 'nd' if spell_level == 2 else 'rd' if spell_level == 3 else 'th'} level)"
                                action_spells.append((spell_level, f"{spell_name}{level_text}"))
                            
                            # Check for bonus actions in spell description or casting time
                            if self._has_bonus_action_capability(spell_name, description, casting_time):
                                bonus_action_list.append(spell_name)
                            
                            # Check for reactions
                            if self._has_reaction_capability(spell_name, description, casting_time):
                                reaction_list.append(spell_name)
        
        return action_spells, bonus_action_list, reaction_list
    
    def _process_inventory_for_actions(self, inventory: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
        """Process inventory items for bonus actions and reactions."""
        bonus_actions = []
        reactions = []
        
        for item in inventory:
            if isinstance(item, dict):
                item_name = item.get('name', '') or ''
                description = item.get('description', '') or ''
                item_type = str(item.get('type', '') or '')

                if not item_name or not description:
                    continue

                desc_lower = description.lower()
                item_type_lower = item_type.lower()
                item_name_lower = item_name.lower()

                # Check for bonus action items
                if 'bonus action' in desc_lower:
                    if 'potion' in item_type_lower and 'healing' in item_name_lower:
                        bonus_actions.append('Potion of Healing')
                    elif 'fire breath' in item_name_lower:
                        bonus_actions.append('Fire Breath Potion')
                    elif 'antitoxin' in item_name_lower:
                        bonus_actions.append('Antitoxin')
                    elif 'cloak' in item_name_lower and 'elvenkind' in item_name_lower:
                        bonus_actions.append('Cloak of Elvenkind')

                # Check for reaction items
                if 'reaction' in desc_lower:
                    if 'ring' in item_type_lower or 'amulet' in item_type_lower:
                        reactions.append(item_name)
        
        return bonus_actions, reactions
    
    def _process_features_for_actions(self, features: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Process class features for bonus actions and reactions."""
        bonus_actions = []
        reactions = []
        
        class_features = features.get('class_features', [])
        for feature in class_features:
            if isinstance(feature, dict):
                feature_name = feature.get('name', '') or ''
                description = feature.get('description', '') or ''

                if not feature_name or not description:
                    continue

                desc_lower = description.lower()
                feature_name_lower = feature_name.lower()

                # Check for bonus action features
                if 'bonus action' in desc_lower:
                    if 'cunning action' in feature_name_lower:
                        bonus_actions.append('Cunning Action')
                    elif 'healing word' in feature_name_lower:
                        bonus_actions.append('Healing Word')
                    elif 'bardic inspiration' in feature_name_lower:
                        bonus_actions.append('Bardic Inspiration')

                # Check for reaction features
                if 'reaction' in desc_lower:
                    if 'uncanny dodge' in feature_name_lower:
                        reactions.append('Uncanny Dodge')
                    elif 'counterspell' in feature_name_lower:
                        reactions.append('Counterspell')
        
        return bonus_actions, reactions

    def _process_attack_actions(self, combat_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Process attack actions for bonus actions and reactions."""
        bonus_actions = []
        reactions = []

        # Check both attack_actions and weapon_attacks
        attack_actions = combat_data.get('attack_actions', [])

        for attack in attack_actions:
            if isinstance(attack, dict):
                attack_name = attack.get('name', '')
                activation_type = attack.get('activation_type', '')

                if not attack_name:
                    continue

                # Check for bonus action attacks
                if activation_type == 'bonus_action':
                    bonus_actions.append(attack_name)

                # Check for reaction attacks
                elif activation_type == 'reaction':
                    reactions.append(attack_name)

        return bonus_actions, reactions

    def _has_bonus_action_capability(self, spell_name: str, description: str, casting_time: str) -> bool:
        """Check if spell has bonus action capabilities."""
        # Guard against None values
        description = str(description or '')
        casting_time = str(casting_time or '')
        spell_name = str(spell_name or '')

        desc_lower = description.lower()
        cast_lower = casting_time.lower()
        name_lower = spell_name.lower()
        
        # Direct bonus action casting time
        if 'bonus action' in cast_lower:
            return True
        
        # Spells that provide ongoing bonus actions
        ongoing_bonus_patterns = [
            'as a bonus action.*you can',
            'bonus action.*move',
            'bonus action.*command',
            'bonus action.*see through',
            'bonus action.*dash',
            'bonus action.*attack'
        ]
        
        for pattern in ongoing_bonus_patterns:
            if re.search(pattern, desc_lower):
                return True
        
        # Specific spell checks
        if any(spell in name_lower for spell in ['healing word', 'spiritual weapon', 'expeditious retreat', 'misty step']):
            return True
        
        return False
    
    def _has_reaction_capability(self, spell_name: str, description: str, casting_time: str) -> bool:
        """Check if spell has reaction capabilities."""
        # Guard against None values
        description = str(description or '')
        casting_time = str(casting_time or '')
        spell_name = str(spell_name or '')

        desc_lower = description.lower()
        cast_lower = casting_time.lower()
        name_lower = spell_name.lower()
        
        # Direct reaction casting time
        if 'reaction' in cast_lower:
            return True
        
        # Spells that provide ongoing reactions
        if 'reaction' in desc_lower:
            return True
        
        # Specific spell checks
        if any(spell in name_lower for spell in ['counterspell', 'shield', 'absorb elements', 'hellish rebuke']):
            return True
        
        return False
    
    def _categorize_bonus_actions(self, bonus_action_list: List[str], 
                                 spells_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Categorize bonus actions into regular and conditional."""
        regular_bonus_actions = []
        conditional_bonus_actions = []
        
        for ba in bonus_action_list:
            # Get spell details for dynamic analysis
            spell_desc = ""
            spell_cast_time = ""
            
            # Find spell in character data
            for spell_source in spells_data.values():
                if isinstance(spell_source, list):
                    for spell in spell_source:
                        if isinstance(spell, dict) and spell.get('name', '').lower() == ba.lower():
                            spell_desc = spell.get('description', '')
                            spell_cast_time = spell.get('casting_time', '')
                            break
            
            # Check if it's conditional
            is_conditional, conditional_desc = self._is_conditional_bonus_spell(ba, spell_desc, spell_cast_time)
            
            if is_conditional:
                conditional_bonus_actions.append(conditional_desc)
            else:
                regular_bonus_actions.append(ba)
        
        return regular_bonus_actions, conditional_bonus_actions
    
    def _is_conditional_bonus_spell(self, spell_name: str, description: str, casting_time: str) -> Tuple[bool, Optional[str]]:
        """Dynamically detect if a spell provides conditional bonus actions."""
        # Guard against None values
        spell_name = str(spell_name or '')
        description = str(description or '')
        casting_time = str(casting_time or '')

        name_lower = spell_name.lower()
        desc_lower = description.lower()
        cast_lower = casting_time.lower()
        
        # Skip if cast as bonus action AND doesn't have ongoing effects
        if 'bonus action' in cast_lower:
            # Check for hybrid spells (cast as bonus action AND provide ongoing)
            ongoing_patterns = [
                r'later turns?', r'subsequent turns?', r'until the spell ends',
                r'while the spell', r'on your turn.*you can', r'on your\s+later\s+turns'
            ]
            if any(re.search(pattern, desc_lower) for pattern in ongoing_patterns):
                if 'expeditious retreat' in name_lower:
                    return True, "Expeditious Retreat - Dash"
                elif 'spiritual weapon' in name_lower:
                    return True, "Spiritual Weapon - Attack"
                return True, f"{spell_name} - Ongoing"
            return False, None
        
        # Check for conditional bonus action patterns
        conditional_patterns = [
            (r'as a\s+bonus action.*you can', 'Move/Command'),
            (r'as a\s+[Bb]onus\s+[Aa]ction.*can', 'Action'),
            (r'on your\s+(?:later\s+)?turns?.*bonus action', 'Repeat'),
            (r'bonus action.*on your\s+(?:later\s+)?turns?', 'Repeat'),
            (r'until the spell ends.*bonus action', 'Duration'),
            (r'while.*spell.*bonus action', 'Active'),
            (r'command.*bonus action', 'Command'),
            (r'move.*bonus action', 'Move'),
            (r'bonus action.*move', 'Move'),
            (r'control.*bonus action', 'Control')
        ]
        
        for pattern, action_type in conditional_patterns:
            if re.search(pattern, desc_lower):
                # Specific spell handling
                if 'familiar' in name_lower:
                    return True, "Find Familiar - Command"
                elif 'servant' in name_lower:
                    return True, "Unseen Servant - Command"
                elif 'weapon' in name_lower:
                    return True, "Spiritual Weapon - Attack"
                elif 'arcane eye' in name_lower:
                    return True, "Arcane Eye - Move"
                elif 'healing word' in name_lower:
                    return True, "Healing Word"
                else:
                    return True, f"{spell_name} - {action_type}"
        
        return False, None
    
    def _is_weapon(self, item: Dict[str, Any]) -> bool:
        """Check if an item is a weapon based on type and description."""
        item_type = str(item.get('type') or '').lower()
        item_name = str(item.get('name') or '').lower()
        description = str(item.get('description') or '').lower()
        
        # Exclude ammunition and non-weapon items
        non_weapon_items = [
            'bolts', 'arrows', 'bullets', 'sling bullets', 'blowgun needles',
            'gear', 'wondrous item', 'potion', 'scroll', 'ammunition',
            'adventuring gear', 'tool', 'kit', 'supplies'
        ]
        
        # Check if it's explicitly not a weapon
        for non_weapon in non_weapon_items:
            if non_weapon in item_type or non_weapon in item_name:
                return False
        
        # Check for weapon types
        weapon_types = [
            'sword', 'dagger', 'shortsword', 'longsword', 'greatsword', 'scimitar', 'rapier',
            'axe', 'handaxe', 'battleaxe', 'greataxe', 'hatchet',
            'mace', 'club', 'warhammer', 'maul', 'flail',
            'spear', 'javelin', 'pike', 'halberd', 'glaive', 'trident',
            'bow', 'longbow', 'shortbow', 'crossbow', 'heavy crossbow', 'light crossbow',
            'sling', 'dart', 'blowgun',
            'quarterstaff', 'staff', 'whip', 'net',
            'weapon'  # Generic weapon type
        ]
        
        # Check if the type contains any weapon keywords
        for weapon_type in weapon_types:
            if weapon_type in item_type or weapon_type in item_name:
                return True
        
        # Check description for weapon indicators
        weapon_indicators = [
            'proficiency with a', 'attack roll', 'weapon attack',
            'damage roll', 'melee weapon', 'ranged weapon',
            'versatile', 'finesse', 'heavy', 'light', 'reach',
            'thrown'
        ]
        
        # Don't count items that are only ammunition
        if 'ammunition' in description and not any(weapon_type in item_type or weapon_type in item_name for weapon_type in weapon_types):
            return False
        
        for indicator in weapon_indicators:
            if indicator in description:
                return True
        
        return False
    
    
    def format_action_economy_only(self, character_data: Dict[str, Any]) -> str:
        """
        Format only the action economy section.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Action economy section only
        """
        if not self.validate_input(character_data):
            raise ValueError("Invalid character data for action economy formatting")
        
        return self._generate_action_economy(character_data)
    
    def format_attacks_only(self, character_data: Dict[str, Any]) -> str:
        """
        Format only the attacks section.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Attacks section only
        """
        if not self.validate_input(character_data):
            raise ValueError("Invalid character data for attacks formatting")
        
        return self._generate_attacks(character_data)
    
    def get_combat_summary(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key combat information for summary purposes.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Dictionary containing key combat information
        """
        inventory = self.get_inventory(character_data)
        combat_data = character_data.get('combat', {})
        actions = combat_data.get('all_actions', character_data.get('actions', []))
        
        # Count weapons
        weapons = [item for item in inventory if item.get('equipped', False) and self._is_weapon(item)]
        weapon_count = len(weapons)
        
        # Count actions by type
        action_count = len([a for a in actions if a.get('type') not in ['cantrip', 'spell']])
        spell_actions = len([a for a in actions if a.get('type') in ['cantrip', 'spell']])
        
        return {
            'weapon_count': weapon_count,
            'equipped_weapons': [w.get('name', 'Unknown') for w in weapons],
            'action_count': action_count,
            'spell_actions': spell_actions,
            'total_actions': len(actions)
        }