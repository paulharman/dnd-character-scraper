"""
Data adapter utilities for bridging v6.0.0 and backup structure differences.

This module provides utilities to transform v6.0.0 character data into a format
that matches what the original parser expects, ensuring compatibility between
the refactored parser and the v6.0.0 data structure.
"""

from typing import Dict, Any, Optional, List, Tuple
import logging
import re


class V6ToV5Adapter:
    """
    Adapter to transform v6.0.0 character data structure to backup-compatible format.
    
    This adapter ensures that the refactored parser can extract the same data
    values from v6.0.0 structure that the original parser would extract from backup.
    """
    
    def __init__(self):
        """Initialize the adapter."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def adapt_character_data(self, v6_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform v6.0.0 character data to backup-compatible format.
        
        Args:
            v6_data: v6.0.0 character data structure with character_info, combat, abilities, etc.
            
        Returns:
            Backup-compatible character data structure with basic_info and flat top-level stats
        """
        # Check if data is current v6.0.0 format (has character_info and abilities sections)
        # v6.0.0 doesn't always have combat section, so we check for the key identifying fields
        if 'character_info' in v6_data and 'abilities' in v6_data and 'scraper_version' in v6_data:
            self.logger.debug("Adapting v6.0.0 structure to backup-compatible format")
            return self._transform_v6_to_backup_format(v6_data)
        
        # Check if data is already in backup format (has basic_info at top level)
        elif 'basic_info' in v6_data:
            self.logger.debug("Data already in backup-compatible format")
            return v6_data.copy()
        
        # Fallback: assume it's some other format and pass through
        else:
            self.logger.warning("Unknown data format, passing through unchanged")
            return v6_data.copy()
    
    def _transform_v6_to_backup_format(self, v6_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform v6.0.0 grouped structure to backup flat structure."""
        adapted_data = {}
        
        # Extract character_info to basic_info
        char_info = v6_data.get('character_info', {})
        combat_data = v6_data.get('combat', {})
        
        # Extract hit points for basic_info (backup original expects this structure)
        hit_points_data = combat_data.get('hit_points', {})
        
        adapted_data['basic_info'] = {
            'character_id': char_info.get('character_id', 0),
            'name': char_info.get('name', 'Unknown Character'),
            'level': char_info.get('level', 1),
            'proficiency_bonus': char_info.get('proficiency_bonus', 2),
            'classes': char_info.get('classes', []),
            'avatarUrl': char_info.get('avatarUrl', ''),
            'experience': char_info.get('experience_points', 0),
            # Backup original expects hit_points in basic_info
            'hit_points': {
                'maximum': hit_points_data.get('maximum', 1) if hit_points_data else max(1, char_info.get('level', 1) * 6),
                'current': hit_points_data.get('current', 1) if hit_points_data else max(1, char_info.get('level', 1) * 6),
                'temporary': hit_points_data.get('temporary', 0) if hit_points_data else 0
            },
            # Backup original expects these in basic_info too
            'armor_class': {'total': combat_data.get('armor_class', 10) if combat_data else 10},
            'initiative': {'total': combat_data.get('initiative_bonus', 0) if combat_data else 0},
            'speed': {'walking': {'total': combat_data.get('speed', 30) if combat_data else 30}}
        }
        
        # Extract combat stats to top level (for compatibility)
        # Use fallback values if combat_data is missing
        adapted_data['armor_class'] = combat_data.get('armor_class', 10) if combat_data else 10
        adapted_data['initiative_bonus'] = combat_data.get('initiative_bonus', 0) if combat_data else 0
        adapted_data['speed'] = combat_data.get('speed', 30) if combat_data else 30
        
        # Hit points (for compatibility) - calculate from level and con mod if missing
        if hit_points_data:
            adapted_data['max_hp'] = hit_points_data.get('maximum', 1)
            adapted_data['current_hp'] = hit_points_data.get('current', 1)
            adapted_data['hit_dice'] = {'used': hit_points_data.get('hit_dice_used', 0)}
        else:
            # Fallback: calculate basic HP from level (will be refined by formatters)
            char_level = char_info.get('level', 1)
            adapted_data['max_hp'] = max(1, char_level * 6)  # Rough estimate
            adapted_data['current_hp'] = adapted_data['max_hp']
            adapted_data['hit_dice'] = {'used': 0}
        
        # Extract abilities to top level
        abilities_data = v6_data.get('abilities', {})
        if abilities_data:
            adapted_data['ability_scores'] = abilities_data.get('ability_scores', {})
            adapted_data['ability_modifiers'] = abilities_data.get('ability_modifiers', {})
            adapted_data['ability_score_breakdown'] = abilities_data.get('ability_score_breakdown', {})
            adapted_data['proficiency_bonus'] = abilities_data.get('proficiency_bonus', 2)
        
        # Extract character info fields to top level
        adapted_data['species'] = char_info.get('species', {})
        adapted_data['background'] = char_info.get('background', {})
        
        # Extract spellcasting to top level  
        spellcasting_data = v6_data.get('spellcasting', {})
        if spellcasting_data:
            adapted_data['is_spellcaster'] = True
            adapted_data['spellcasting_ability'] = spellcasting_data.get('spellcasting_ability', 'intelligence')
            adapted_data['spell_save_dc'] = spellcasting_data.get('spell_save_dc', 10)
            adapted_data['spell_slots'] = spellcasting_data.get('spell_slots', {})
        else:
            adapted_data['is_spellcaster'] = False
            adapted_data['spellcasting_ability'] = 'intelligence'
            adapted_data['spell_save_dc'] = 10
            adapted_data['spell_slots'] = {}
        
        # Extract other sections to top level  
        spells_data = v6_data.get('spells', {})
        spell_actions_data = v6_data.get('combat', {}).get('spell_actions', [])
        adapted_data['spells'] = self._enhance_spells_data(spells_data, spell_actions_data)
        adapted_data['features'] = v6_data.get('features', {})
        equipment_data = v6_data.get('equipment', {})
        adapted_data['equipment'] = equipment_data
        
        # Extract inventory, wealth, and encumbrance from v6.0.0 structure
        inventory, wealth, encumbrance = self._extract_inventory_data(equipment_data, adapted_data)
        adapted_data['inventory'] = inventory
        adapted_data['wealth'] = wealth
        adapted_data['encumbrance'] = encumbrance
        
        # Map appearance section to top level (critical for backup compatibility)
        appearance_data = v6_data.get('appearance', {})
        if appearance_data:
            adapted_data['appearance'] = appearance_data
        
        # Map notes section to top level (critical for backup compatibility)
        notes_data = v6_data.get('notes', {})
        if notes_data:
            adapted_data['notes'] = notes_data
        
        # Add meta section
        adapted_data['meta'] = {
            'character_id': char_info.get('character_id', 0),
            'rule_version': char_info.get('rule_version', 'unknown')
        }
        
        return adapted_data
    
    def _enhance_spells_data(self, spells_data: Dict[str, Any], spell_actions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Enhance spells data with missing casting_time, range, and components information.
        
        Args:
            spells_data: Original spells data from v6.0.0
            spell_actions_data: Spell actions data with casting_time and range info
            
        Returns:
            Enhanced spells data with additional fields
        """
        if not spells_data:
            return {}
        
        # Create a lookup dictionary for spell_actions by name
        spell_actions_lookup = {}
        for action in spell_actions_data:
            spell_name = action.get('name', '')
            if spell_name:
                spell_actions_lookup[spell_name] = action
        
        enhanced_spells = {}
        
        # Process each spell source
        for source, spell_list in spells_data.items():
            if not isinstance(spell_list, list):
                enhanced_spells[source] = spell_list
                continue
                
            enhanced_spell_list = []
            
            for spell in spell_list:
                if not isinstance(spell, dict):
                    enhanced_spell_list.append(spell)
                    continue
                
                # Create enhanced spell copy
                enhanced_spell = spell.copy()
                spell_name = spell.get('name', '')
                
                # Extract components from description
                components = self._extract_components_from_description(spell.get('description', ''))
                enhanced_spell['components'] = components
                
                # Get casting_time and range from spell_actions if available
                if spell_name in spell_actions_lookup:
                    action_data = spell_actions_lookup[spell_name]
                    
                    # Extract casting_time
                    casting_time = action_data.get('casting_time', '')
                    if casting_time:
                        enhanced_spell['casting_time'] = casting_time
                    
                    # Extract range
                    range_data = action_data.get('range', {})
                    if isinstance(range_data, dict):
                        range_value = range_data.get('rangeValue', 0)
                        if range_value and range_value > 0:
                            enhanced_spell['range'] = f"{range_value} feet"
                        else:
                            # Handle self-targeting spells
                            origin = range_data.get('origin', '')
                            if origin == 'Self':
                                enhanced_spell['range'] = 'Self'
                            else:
                                enhanced_spell['range'] = 'Self'
                    
                    # Extract duration
                    duration_data = action_data.get('duration', {})
                    if isinstance(duration_data, dict):
                        duration_type = duration_data.get('durationType', '')
                        if duration_type:
                            enhanced_spell['duration'] = duration_type
                
                # Add fallback values for missing data
                if 'casting_time' not in enhanced_spell:
                    enhanced_spell['casting_time'] = self._get_fallback_casting_time(spell_name)
                
                if 'range' not in enhanced_spell:
                    enhanced_spell['range'] = self._get_fallback_range(spell_name)
                
                if 'duration' not in enhanced_spell:
                    enhanced_spell['duration'] = self._get_fallback_duration(spell_name)
                
                enhanced_spell_list.append(enhanced_spell)
            
            enhanced_spells[source] = enhanced_spell_list
        
        return enhanced_spells
    
    def _extract_components_from_description(self, description: str) -> Dict[str, Any]:
        """
        Extract spell components from spell description.
        
        Args:
            description: Spell description HTML text
            
        Returns:
            Dictionary with component information
        """
        if not description:
            return {'verbal': False, 'somatic': False, 'material': False}
        
        # Remove HTML tags for analysis
        clean_desc = re.sub(r'<[^>]+>', '', description)
        
        # Look for component patterns in the description
        # This is a heuristic approach since v6.0.0 doesn't have explicit component data
        components = {
            'verbal': False,
            'somatic': False,
            'material': False,
            'material_description': ''
        }
        
        # Check for material components first (they often indicate the spell needs M)
        material_patterns = [
            r'(?:requires?|needs?|uses?|with)\s+(?:a|an|the)\s+([^.]+?)(?:\s+worth\s+[\d,]+\s*(?:cp|sp|ep|gp|pp))?',
            r'(?:a|an|the)\s+([^.]+?)\s+worth\s+[\d,]+\s*(?:cp|sp|ep|gp|pp)',
            r'(?:copper wire|bit of fleece|diamond|drop of alcohol|weapon)',
        ]
        
        for pattern in material_patterns:
            match = re.search(pattern, clean_desc, re.IGNORECASE)
            if match:
                components['material'] = True
                if match.groups():
                    components['material_description'] = match.group(1).strip()
                break
        
        # Heuristic: Most spells require verbal and somatic components unless specifically noted
        # This matches the general D&D pattern where most spells have V, S components
        components['verbal'] = True
        components['somatic'] = True
        
        # Special cases for spells that are known to be different
        description_lower = clean_desc.lower()
        
        # Some spells are purely mental/touch-based
        if any(term in description_lower for term in ['purely mental', 'thought', 'telepathic']):
            components['somatic'] = False
        
        return components
    
    def _get_fallback_casting_time(self, spell_name: str) -> str:
        """Get fallback casting time for known spells."""
        spell_name_lower = spell_name.lower()
        
        # Known casting times from D&D rules
        casting_time_map = {
            'shield': '1 reaction',
            'healing word': '1 bonus action',
            'cure wounds': '1 action',
            'misty step': '1 bonus action',
            'counterspell': '1 reaction',
            'fireball': '1 action',
            'magic missile': '1 action',
            'find familiar': '1 hour',
            'ritual spells': '10 minutes'
        }
        
        return casting_time_map.get(spell_name_lower, '1 action')
    
    def _get_fallback_range(self, spell_name: str) -> str:
        """Get fallback range for known spells."""
        spell_name_lower = spell_name.lower()
        
        # Known ranges from D&D rules
        range_map = {
            'shield': 'Self',
            'cure wounds': 'Touch',
            'healing word': '60 feet',
            'fireball': '150 feet',
            'magic missile': '120 feet',
            'counterspell': '60 feet',
            'misty step': '30 feet',
            'message': '120 feet',
            'minor illusion': '30 feet',
            'prestidigitation': '10 feet',
            'true strike': '30 feet',
            'chromatic orb': '90 feet',
            'false life': 'Self',
            'thunderwave': 'Self (15-foot cube)'
        }
        
        return range_map.get(spell_name_lower, 'Touch')
    
    def _get_fallback_duration(self, spell_name: str) -> str:
        """Get fallback duration for known spells."""
        spell_name_lower = spell_name.lower()
        
        # Known durations from D&D rules
        duration_map = {
            'shield': '1 round',
            'cure wounds': 'Instantaneous',
            'healing word': 'Instantaneous',
            'fireball': 'Instantaneous',
            'magic missile': 'Instantaneous',
            'counterspell': 'Instantaneous',
            'misty step': 'Instantaneous',
            'message': 'Instantaneous',
            'minor illusion': '1 minute',
            'prestidigitation': '1 hour',
            'true strike': 'Instantaneous',
            'chromatic orb': 'Instantaneous',
            'false life': 'Instantaneous',
            'thunderwave': 'Instantaneous'
        }
        
        return duration_map.get(spell_name_lower, 'Instantaneous')
    
    def _extract_inventory_data(self, equipment_data: Dict[str, Any], character_data: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any], Dict[str, Any]]:
        """
        Extract inventory, wealth, and encumbrance data from v6.0.0 equipment structure.
        
        Args:
            equipment_data: Equipment data from v6.0.0 structure
            character_data: Character data for strength calculation
            
        Returns:
            Tuple of (inventory_list, wealth_dict, encumbrance_dict)
        """
        inventory = []
        wealth = {}
        encumbrance = {}
        
        # Extract inventory from basic_equipment and enhanced_equipment
        basic_items = equipment_data.get('basic_equipment', [])
        enhanced_items = equipment_data.get('enhanced_equipment', [])
        
        # Combine all items for inventory
        all_items = basic_items + enhanced_items
        
        for item in all_items:
            if isinstance(item, dict):
                # Transform v6.0.0 item structure to backup-compatible format
                inventory_item = {
                    'id': item.get('id', 0),
                    'name': item.get('name', 'Unknown Item'),
                    'type': item.get('item_type', 'Item'),
                    'quantity': item.get('quantity', 1),
                    'weight': item.get('weight', 0.0),
                    'cost': item.get('cost', 0.0),
                    'rarity': item.get('rarity', 'Common'),
                    'equipped': item.get('equipped', False),
                    'description': item.get('description', ''),
                    'is_magic': item.get('is_magic', False),
                    'requires_attunement': item.get('requires_attunement', False),
                    'attuned': item.get('attuned', False),
                    'total_weight': item.get('total_weight', item.get('weight', 0.0) * item.get('quantity', 1))
                }
                inventory.append(inventory_item)
        
        # Extract wealth from equipment_summary
        equipment_summary = equipment_data.get('equipment_summary', {})
        wealth_summary = equipment_summary.get('wealth_summary', {})
        
        if wealth_summary:
            wealth = {
                'total_gp': wealth_summary.get('total_gp', 0.0),
                'currency_count': wealth_summary.get('currency_count', 0),
                'copper': 0,
                'silver': 0, 
                'electrum': 0,
                'gold': wealth_summary.get('total_gp', 0.0),  # Use total_gp as gold for compatibility
                'platinum': 0
            }
        else:
            # Fallback: calculate wealth from item costs
            total_value = 0.0
            for item in inventory:
                cost = item.get('cost', 0.0)
                quantity = item.get('quantity', 1)
                if cost and isinstance(cost, (int, float)):
                    total_value += cost * quantity
            
            wealth = {
                'total_gp': total_value,
                'currency_count': 1 if total_value > 0 else 0,
                'copper': 0,
                'silver': 0,
                'electrum': 0,
                'gold': total_value,
                'platinum': 0
            }
        
        # Extract encumbrance from equipment_summary
        weight_distribution = equipment_summary.get('weight_distribution', {})
        
        if weight_distribution:
            encumbrance = {
                'total_weight': weight_distribution.get('total_weight', 0.0),
                'equipped_weight': weight_distribution.get('equipped_weight', 0.0),
                'unequipped_weight': weight_distribution.get('unequipped_weight', 0.0),
                'encumbrance_level': weight_distribution.get('encumbrance_level', 0),
                'carrying_capacity': self._calculate_carrying_capacity(character_data),
                'percentage_used': 0.0
            }
            
            # Calculate percentage used
            total_weight = encumbrance.get('total_weight', 0.0)
            carrying_capacity = encumbrance.get('carrying_capacity', 1.0)
            if carrying_capacity > 0:
                encumbrance['percentage_used'] = (total_weight / carrying_capacity) * 100
                
        else:
            # Fallback: calculate encumbrance from inventory
            total_weight = sum(item.get('total_weight', 0.0) for item in inventory)
            carrying_capacity = self._calculate_carrying_capacity(character_data)
            
            encumbrance = {
                'total_weight': total_weight,
                'equipped_weight': sum(item.get('total_weight', 0.0) for item in inventory if item.get('equipped', False)),
                'unequipped_weight': sum(item.get('total_weight', 0.0) for item in inventory if not item.get('equipped', False)),
                'encumbrance_level': 0,
                'carrying_capacity': carrying_capacity,
                'percentage_used': (total_weight / carrying_capacity) * 100 if carrying_capacity > 0 else 0.0
            }
        
        return inventory, wealth, encumbrance
    
    def _calculate_carrying_capacity(self, character_data: Dict[str, Any]) -> float:
        """
        Calculate carrying capacity based on character strength.
        
        Args:
            character_data: Character data with ability scores
            
        Returns:
            Carrying capacity in pounds
        """
        # Get strength score from character data
        ability_scores = character_data.get('ability_scores', {})
        strength_data = ability_scores.get('strength', {})
        
        # Extract strength score - try different possible structures
        strength_score = 10  # Default strength
        if isinstance(strength_data, dict):
            strength_score = strength_data.get('score', 10)
        elif isinstance(strength_data, int):
            strength_score = strength_data
        
        # D&D 5e carrying capacity: Strength × 15 pounds
        return float(strength_score * 15)