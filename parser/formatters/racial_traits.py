"""
Racial traits formatter for species-specific abilities and traits.

This module handles the generation of racial traits section including
senses, advantages, proficiencies, immunities, and racial spells.
"""

from typing import Dict, Any, List, Optional

# Import interfaces and utilities using absolute import
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging

from formatters.base import BaseFormatter
from utils.text import TextProcessor


class RacialTraitsFormatter(BaseFormatter):
    """
    Handles racial traits section generation for character sheets.
    
    Generates comprehensive racial trait information including senses,
    advantages, proficiencies, immunities, and racial spells.
    """
    
    def __init__(self, text_processor: TextProcessor):
        """
        Initialize the racial traits formatter.
        
        Args:
            text_processor: Text processing utilities
        """
        super().__init__(text_processor)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _get_required_fields(self) -> List[str]:
        """Get list of required fields for racial traits formatting."""
        return []
    
    def _validate_internal(self, character_data: Dict[str, Any]) -> bool:
        """Validate character data structure for racial traits formatting."""
        return True
    
    def _format_internal(self, character_data: Dict[str, Any]) -> str:
        """
        Generate racial traits section.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Racial traits section markdown
        """
        sections = []
        sections.append("## Racial Traits")
        sections.append("")
        sections.append('<span class="right-link">[[#Character Statistics|Top]]</span>')
        
        # Get species information using base formatter method
        species_name = self.get_species_name(character_data)
        
        # Create species-specific traits section
        sections.append(f">### {species_name} Traits")
        sections.append(">")
        
        # Extract traits from features section with trait_type "racial" (v6.0.0 format)
        features = character_data.get('features', {})
        racial_traits = []
        
        # Handle features as dict (v6.0.0 format) - check all feature categories
        if isinstance(features, dict):
            all_features = []
            for feature_category, feature_list in features.items():
                if isinstance(feature_list, list):
                    all_features.extend(feature_list)
        elif isinstance(features, list):
            all_features = features
        else:
            all_features = []
        
        # Filter features to get racial traits
        for feature in all_features:
            if isinstance(feature, dict) and feature.get('trait_type') == 'racial':
                racial_traits.append(feature)
        
        # Fallback: try species.traits if no racial features found
        if not racial_traits:
            species = character_data.get('species', {})
            traits = species.get('traits', [])
            racial_traits = traits
        
        if racial_traits:
            for trait in racial_traits:
                if isinstance(trait, dict):
                    trait_name = trait.get('name', 'Unknown Trait')
                    trait_description = trait.get('description', '')
                    trait_type = trait.get('type', 'feature')
                    
                    # Skip basic traits that are covered elsewhere
                    if trait_name.lower() in ['creature type', 'size', 'speed']:
                        continue
                    
                    sections.append(f">#### {trait_name}")
                    sections.append(">")
                    
                    if trait_description:
                        # Clean HTML from description
                        clean_desc = self.text_processor.clean_text(trait_description)
                        # Add proper blockquote formatting for multiline text (including tables)
                        lines = clean_desc.split('\n')
                        for line in lines:
                            if line.strip():
                                sections.append(f"> {line}")
                            else:
                                sections.append(">")
                        sections.append(">")
                    
                    # Add chosen selections display for traits with choices
                    choices = self.get_feature_choices(character_data, trait_name)
                    if choices:
                        formatted_choices = self.format_feature_choices(choices)
                        for choice in formatted_choices:
                            sections.append(f"> {choice}")
                        sections.append(">")
                    
                    # Add special formatting for specific trait types
                    if trait_type == 'sense':
                        sense_range = trait.get('range')
                        if sense_range:
                            sections.append(f"> *Range: {sense_range} feet*")
                            sections.append(">")
                    elif trait_type == 'spellcasting':
                        # Get actual chosen spells for this trait
                        actual_spells = self._get_actual_racial_spells_for_trait(character_data, trait_name)
                        if actual_spells:
                            spell_list = ', '.join(actual_spells)
                            sections.append(f"> *Chosen Spells: {spell_list}*")
                            sections.append(">")
                        else:
                            # Fallback to generic spell list if no specific choices found
                            spells = trait.get('spells', [])
                            if spells:
                                spell_list = ', '.join(spells)
                                sections.append(f"> *Spells: {spell_list}*")
                                sections.append(">")
        else:
            sections.append("> *No racial traits information available from API.*")
            sections.append(">")
        
        sections.append("> ^racial-traits")
        sections.append("")
        sections.append("---")
        
        return '\n'.join(sections)
    
    def _extract_species_traits(self, character_data: Dict[str, Any], species: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract species-specific traits from features."""
        traits = []
        
        # Look for racial features
        features = character_data.get('features', [])
        if isinstance(features, list):
            for feature in features:
                if isinstance(feature, dict):
                    name = feature.get('name', '')
                    description = feature.get('description', '')
                    source = feature.get('source', {})
                    
                    # Check if it's a racial/species trait
                    if isinstance(source, dict):
                        source_name = source.get('name', '').lower()
                        if ('species' in source_name or 'elf' in source_name or 
                            'racial' in source_name or 'lineage' in source_name):
                            
                            trait = {
                                'name': name,
                                'description': description
                            }
                            
                            # Add specific details for common traits
                            if 'darkvision' in name.lower():
                                trait['details'] = 'Range: 60 feet'
                            elif 'lineage' in name.lower() and 'prestidigitation' in description.lower():
                                trait['details'] = 'Chosen Spells: Prestidigitation'
                            elif 'elven lineage' in name.lower():
                                trait['details'] = 'Chosen Spells: Prestidigitation'
                            
                            traits.append(trait)
        
        return traits
    
    def _extract_senses(self, character_data: Dict[str, Any], species: Dict[str, Any]) -> List[str]:
        """Extract sense-based traits like darkvision."""
        senses = []
        
        # Look for darkvision or other senses in features
        features = character_data.get('features', [])
        if isinstance(features, list):
            for feature in features:
                if isinstance(feature, dict):
                    name = feature.get('name', '').lower()
                    description = feature.get('description', '')
                    
                    if 'darkvision' in name or 'darkvision' in description.lower():
                        if '60 feet' in description:
                            senses.append("You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light.")
                        else:
                            senses.append("You have darkvision.")
                    elif 'keen senses' in name or 'perception' in description.lower():
                        # This will be handled in proficiencies
                        continue
        
        return senses
    
    def _extract_advantages(self, character_data: Dict[str, Any], species: Dict[str, Any]) -> List[str]:
        """Extract advantage-based traits."""
        advantages = []
        
        # Look for Fey Ancestry or similar traits
        features = character_data.get('features', [])
        if isinstance(features, list):
            for feature in features:
                if isinstance(feature, dict):
                    name = feature.get('name', '').lower()
                    description = feature.get('description', '')
                    
                    if 'fey ancestry' in name or 'advantage' in description.lower():
                        if 'saving throw' in description.lower():
                            advantages.append("You have advantage on Saving Throws checks")
                        elif 'charm' in description.lower():
                            advantages.append("You have advantage on saving throws against being charmed")
        
        return advantages
    
    def _extract_racial_proficiencies(self, character_data: Dict[str, Any], species: Dict[str, Any]) -> List[str]:
        """Extract proficiency-based racial traits."""
        proficiencies = []
        
        # Look for racial proficiencies in skill_proficiencies
        skill_proficiencies = character_data.get('skill_proficiencies', {})
        
        if isinstance(skill_proficiencies, dict):
            # Dictionary format: skill_name -> source_info
            for skill, source_info in skill_proficiencies.items():
                if isinstance(source_info, dict):
                    source = source_info.get('source', '').lower()
                elif isinstance(source_info, str):
                    source = source_info.lower()
                else:
                    continue
                
                if 'species' in source or 'elf' in source or 'racial' in source:
                    skill_display = skill.replace('_', ' ').title()
                    proficiencies.append(f"You have proficiency with {skill_display}")
        
        elif isinstance(skill_proficiencies, list):
            # List format: list of proficiency objects
            for proficiency in skill_proficiencies:
                if isinstance(proficiency, dict):
                    skill_name = proficiency.get('name', '')
                    source = proficiency.get('source', '').lower()
                    
                    if 'species' in source or 'elf' in source or 'racial' in source:
                        skill_display = skill_name.replace('_', ' ').title()
                        proficiencies.append(f"You have proficiency with {skill_display}")
        
        return proficiencies
    
    def _extract_immunities(self, character_data: Dict[str, Any], species: Dict[str, Any]) -> List[str]:
        """Extract immunity-based traits."""
        immunities = []
        
        # Look for immunities in features
        features = character_data.get('features', [])
        if isinstance(features, list):
            for feature in features:
                if isinstance(feature, dict):
                    name = feature.get('name', '').lower()
                    description = feature.get('description', '')
                    
                    if 'fey ancestry' in name or 'immunity' in description.lower() or 'immune' in description.lower():
                        if 'sleep' in description.lower() and 'magic' in description.lower():
                            immunities.append("You have immunity to Magical Sleep")
        
        return immunities
    
    def _extract_racial_spells(self, character_data: Dict[str, Any], species: Dict[str, Any]) -> List[str]:
        """Extract spells granted by racial heritage."""
        racial_spells = []
        
        # Look for spells with racial source
        spells = character_data.get('spells', {})
        if isinstance(spells, dict):
            for spell_level, spell_list in spells.items():
                if isinstance(spell_list, list):
                    for spell in spell_list:
                        if isinstance(spell, dict):
                            source = spell.get('source', '').lower()
                            spell_name = spell.get('name', '')
                            
                            if ('species' in source or 'racial' in source or 'elf' in source) and spell_name:
                                racial_spells.append(spell_name)
        
        # Also check for cantrips specifically mentioned as racial
        cantrips = spells.get('cantrips', [])
        if isinstance(cantrips, list):
            for spell in cantrips:
                if isinstance(spell, dict):
                    spell_name = spell.get('name', '')
                    # Prestidigitation is commonly a racial spell for some races
                    if spell_name.lower() in ['prestidigitation'] and spell_name not in racial_spells:
                        racial_spells.append(spell_name)
        
        return racial_spells
    
    def _get_actual_racial_spells_for_trait(self, character_data: Dict[str, Any], trait_name: str) -> List[str]:
        """
        Get the actual spells chosen for a racial trait from the character's spell list.
        
        Args:
            character_data: Complete character data dictionary
            trait_name: Name of the racial trait (e.g., "Elven Lineage")
            
        Returns:
            List of spell names that were actually chosen for this trait
        """
        actual_spells = []
        
        # Only show spells for traits that actually grant spell choices
        spell_granting_traits = [
            'elven lineage', 'draconic ancestry', 'fey magic', 'innate spellcasting',
            'magic resistance', 'spellcasting', 'racial spells', 'lineage spells'
        ]
        
        # Check if this trait typically grants spells
        trait_lower = trait_name.lower()
        grants_spells = any(spell_trait in trait_lower for spell_trait in spell_granting_traits)
        
        if not grants_spells:
            return actual_spells
        
        # Look through all spell sources to find racial spells
        spells = character_data.get('spells', {})
        
        # Common cantrips that are often racial choices
        racial_cantrips = ['prestidigitation', 'detect magic', 'fire bolt', 'dancing lights', 'druidcraft']
        
        # Check all spell levels for racial spells
        for source, spell_list in spells.items():
            if isinstance(spell_list, list):
                for spell in spell_list:
                    if isinstance(spell, dict):
                        spell_name = spell.get('name', '')
                        spell_source = spell.get('source', '').lower()
                        
                        # Check if it's from a racial source or a commonly racial spell
                        if (('racial' in spell_source or 'species' in spell_source or 'elf' in spell_source) 
                            or spell_name.lower() in racial_cantrips):
                            if spell_name and spell_name not in actual_spells:
                                actual_spells.append(spell_name)
        
        return actual_spells