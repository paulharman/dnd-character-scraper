"""
Attacks formatter for weapon attacks and combat actions.

This module handles the generation of the standalone Attacks section
with detailed weapon information.
"""

from typing import Dict, Any, List, Optional

# Import interfaces and utilities using absolute import
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging

from formatters.base import BaseFormatter
from utils.text import TextProcessor


class AttacksFormatter(BaseFormatter):
    """
    Handles attacks section generation for character sheets.
    
    Generates comprehensive attack information including weapon details,
    attack bonuses, and damage information.
    """
    
    def __init__(self, text_processor: TextProcessor):
        """
        Initialize the attacks formatter.
        
        Args:
            text_processor: Text processing utilities
        """
        super().__init__(text_processor)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _get_required_fields(self) -> List[str]:
        """Get list of required fields for attacks formatting."""
        return []
    
    def _validate_internal(self, character_data: Dict[str, Any]) -> bool:
        """Validate character data structure for attacks formatting."""
        return True
    
    def _format_internal(self, character_data: Dict[str, Any]) -> str:
        """
        Generate attacks section.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Attacks section markdown
        """
        sections = []
        sections.append("## Attacks")
        sections.append("")
        sections.append('<span class="right-link">[[#Character Statistics|Top]]</span>')
        sections.append("")
        sections.append(">")
        
        # Get weapon attacks from inventory or actions
        attacks = self._extract_weapon_attacks(character_data)
        
        if not attacks:
            sections.append("> No weapon attacks available.")
        else:
            for attack in attacks:
                sections.extend(self._format_attack(attack))
        
        sections.append("> ^attacks")
        sections.append("")
        sections.append("---")
        
        return '\n'.join(sections)
    
    def _extract_weapon_attacks(self, character_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract weapon attacks from enhanced scraper-provided attack data."""
        attacks = []
        
        # Use enhanced weapon attacks from combat section (new format)
        combat_data = character_data.get('combat', {})
        weapon_attacks = combat_data.get('weapon_attacks', [])
        
        if isinstance(weapon_attacks, list) and weapon_attacks:
            attacks.extend(weapon_attacks)
        else:
            # Fallback to legacy attack actions
            attack_actions = combat_data.get('attack_actions', [])
            if isinstance(attack_actions, list):
                attacks.extend(attack_actions)
        
        return attacks
    
    def _inventory_item_to_attack(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert an inventory item to attack format."""
        name = item.get('name', 'Unknown Weapon')
        if not name or name.lower() in ['unknown', 'unknown weapon']:
            return None
        
        # Basic attack structure
        attack = {
            'name': name,
            'type': item.get('type', 'Weapon'),
            'attack_bonus': item.get('attack_bonus', 0),
            'damage': item.get('damage', '1d4'),
            'damage_type': item.get('damage_type', 'piercing'),
            'weight': item.get('weight', 0.0)
        }
        
        return attack
    
    
    def _format_attack(self, attack: Dict[str, Any]) -> List[str]:
        """Format a single attack entry with enhanced breakdown information."""
        lines = []
        
        name = attack.get('name', 'Unknown Attack')
        attack_type = attack.get('attack_type', attack.get('type', 'Weapon'))
        
        lines.append(f"> ### {name}")
        lines.append(f"> **Type:** {attack_type.capitalize()}")
        
        # Attack bonus with breakdown
        attack_bonus = attack.get('attack_bonus', 0)
        if isinstance(attack_bonus, (int, float)):
            sign = '+' if attack_bonus >= 0 else ''
            lines.append(f"> **Attack Bonus:** {sign}{attack_bonus}")
            
            # Add breakdown if available
            breakdown = attack.get('breakdown', {})
            if breakdown and isinstance(breakdown, dict):
                description = breakdown.get('description', '')
                if description:
                    lines.append(f">   *{description}*")
        else:
            lines.append(f"> **Attack Bonus:** {attack_bonus}")
        
        # Damage with enhanced information
        damage_dice = attack.get('damage_dice', attack.get('damage', ''))
        damage_modifier = attack.get('damage_bonus', attack.get('damage_modifier', 0))
        damage_type = attack.get('damage_type', '')
        
        if damage_dice:
            damage_str = damage_dice
            if damage_modifier and damage_modifier != 0:
                sign = '+' if damage_modifier >= 0 else ''
                damage_str += f" {sign}{damage_modifier}"
            
            if damage_type:
                lines.append(f"> **Damage:** {damage_str} {damage_type}")
            else:
                lines.append(f"> **Damage:** {damage_str}")
        
        # Weapon properties
        properties = attack.get('properties', [])
        if properties:
            if isinstance(properties, list):
                props_str = ', '.join(properties)
            else:
                props_str = str(properties)
            lines.append(f"> **Properties:** {props_str}")
        
        # Range for ranged weapons
        range_info = attack.get('range', '')
        if range_info and range_info != 'Melee':
            lines.append(f"> **Range:** {range_info}")
        
        # Weight (if available)
        weight = attack.get('weight', 0.0)
        if weight:
            lines.append(f"> **Weight:** {weight} lbs")
        
        # Attack snippet (if available)
        snippet = attack.get('snippet', '')
        if snippet:
            lines.append(f"> **Quick Reference:** *{snippet}*")
        
        lines.append("> ")
        
        return lines