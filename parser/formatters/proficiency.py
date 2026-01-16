"""
Proficiency formatter for skill bonuses, proficiencies, and saving throws.

This module handles the generation of proficiency-related sections including
proficiency sources and comprehensive proficiencies section.
"""

from typing import Dict, Any, List, Optional

# Import interfaces and utilities using absolute import
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging

from formatters.base import BaseFormatter
from utils.text import TextProcessor


class ProficiencyFormatter(BaseFormatter):
    """
    Handles proficiency-related section generation for character sheets.
    
    Generates comprehensive proficiency information including skill bonuses,
    saving throws, weapon/tool/language proficiencies.
    """
    
    def __init__(self, text_processor: TextProcessor):
        """
        Initialize the proficiency formatter.
        
        Args:
            text_processor: Text processing utilities
        """
        super().__init__(text_processor)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _get_required_fields(self) -> List[str]:
        """Get list of required fields for proficiency formatting."""
        return []
    
    def _validate_internal(self, character_data: Dict[str, Any]) -> bool:
        """Validate character data structure for proficiency formatting."""
        return True
    
    def _format_internal(self, character_data: Dict[str, Any]) -> str:
        """
        Generate standalone proficiencies section.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Standalone proficiencies section markdown
        """
        # Generate standalone proficiencies section only
        # The proficiency sources section is handled by the abilities formatter
        return self.format_standalone_proficiencies(character_data)
    
    def format_proficiency_sources(self, character_data: Dict[str, Any]) -> str:
        """Generate the Proficiency Sources subsection."""
        character_info = self.get_character_info(character_data)
        
        sections = []
        sections.append("### Proficiency Sources")
        
        # Get enhanced skill bonuses from v6.0.0 structure
        proficiencies_data = character_data.get('proficiencies', {})
        
        # Try to get enhanced skill bonuses first
        skill_bonuses_data = proficiencies_data.get('skill_bonuses', [])
        
        # Build skill bonuses list with enhanced information
        skill_bonuses = []
        if skill_bonuses_data:
            # Use enhanced skill bonus data
            for skill_bonus in skill_bonuses_data:
                if isinstance(skill_bonus, dict):
                    skill_name = skill_bonus.get('skill_name', 'Unknown').replace('_', ' ').title()
                    total_bonus = skill_bonus.get('total_bonus', 0)
                    is_proficient = skill_bonus.get('is_proficient', False)
                    has_expertise = skill_bonus.get('has_expertise', False)
                    breakdown = skill_bonus.get('breakdown', {})
                    
                    if is_proficient or has_expertise or total_bonus != 0:
                        bonus_str = f"{total_bonus:+d}" if total_bonus != 0 else "+0"
                        
                        # Add expertise indicator
                        expertise_indicator = " (Expertise)" if has_expertise else ""
                        
                        # Add breakdown if available
                        breakdown_text = ""
                        if isinstance(breakdown, dict) and 'calculation' in breakdown:
                            breakdown_text = f" - {breakdown['calculation']}"
                        elif isinstance(breakdown, str):
                            breakdown_text = f" - {breakdown}"
                        
                        skill_bonuses.append(f"> - **{skill_name}** {bonus_str}{expertise_indicator}{breakdown_text}")
        else:
            # Fallback to legacy skill proficiencies
            skill_proficiencies = proficiencies_data.get('skill_proficiencies', [])
            
            # Fallback to legacy structure if v6.0.0 data not found
            if not skill_proficiencies:
                skill_proficiencies = character_data.get('skill_proficiencies', [])
            
            for skill in skill_proficiencies:
                if isinstance(skill, dict) and skill.get('proficient', False):
                    name = skill.get('name', 'Unknown')
                    source = skill.get('source', 'Unknown')
                    skill_bonuses.append(f"> - **{name}** ({source})")
        
        if skill_bonuses:
            sections.append("> **Skill Bonuses:**")
            sections.extend(skill_bonuses)
            sections.append(">")
        
        # Get saving throw proficiencies from v6.0.0 structure
        saving_throw_proficiencies = proficiencies_data.get('saving_throw_proficiencies', [])
        saving_throw_profs = []
        
        # Extract saving throw names from v6.0.0 structure
        for save_prof in saving_throw_proficiencies:
            if isinstance(save_prof, dict):
                save_name = save_prof.get('name', '').lower()
                source = save_prof.get('source', 'Unknown')
                if save_name in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
                    saving_throw_profs.append((save_name, source))
        
        # Fallback to legacy format if v6.0.0 data not found
        if not saving_throw_profs:
            # Try combat structure
            combat_data = character_data.get('combat', {})
            saving_throws = combat_data.get('saving_throws', {})
            for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
                if saving_throws.get(ability, {}).get('proficient', False):
                    saving_throw_profs.append((ability, 'Class'))
            
            # Final fallback to legacy structure
            if not saving_throw_profs:
                legacy_saves = character_data.get('saving_throw_proficiencies', [])
                for save in legacy_saves:
                    if isinstance(save, str):
                        saving_throw_profs.append((save, 'Class'))
        
        # Get ability modifiers and proficiency bonus for saving throw calculations
        ability_scores = self.get_ability_scores(character_data)
        proficiency_bonus = character_info.get('proficiency_bonus', 2)
        
        # Saving throw bonuses with actual bonus values
        save_bonuses = []
        for save_name, source in saving_throw_profs:
            ability_data = ability_scores.get(save_name.lower(), {})
            ability_mod = ability_data.get('modifier', 0)
            save_bonus = ability_mod + proficiency_bonus
            save_display = save_name.capitalize()
            save_bonuses.append(f"> - **{save_display}** +{save_bonus} ({source})")
        
        if save_bonuses:
            sections.append("> **Saving Throw Bonuses:**")
            sections.extend(save_bonuses)
            sections.append(">")
        
        sections.append("> ^proficiency-sources")
        
        return '\n'.join(sections)
    
    def format_standalone_proficiencies(self, character_data: Dict[str, Any]) -> str:
        """Generate the standalone Proficiencies section."""
        character_info = self.get_character_info(character_data)
        
        sections = []
        sections.append("## Proficiencies")
        sections.append("")
        sections.append('<span class="right-link">[[#Character Statistics|Top]]</span>')
        
        # Weapon proficiencies - try v6.0.0 structure first, then legacy
        proficiencies_data = character_data.get('proficiencies', {})
        weapon_proficiencies = proficiencies_data.get('weapon_proficiencies', [])
        
        # Fallback to legacy structure if v6.0.0 not found
        if not weapon_proficiencies:
            weapon_proficiencies = character_data.get('weapon_proficiencies', [])
        
        if weapon_proficiencies:
            sections.append(">### Weapons")
            sections.append(">")
            for weapon in weapon_proficiencies:
                if isinstance(weapon, dict):
                    weapon_name = weapon.get('name', 'Unknown Weapon')
                    source = weapon.get('source', '')
                    if source:
                        display = f"{weapon_name} ({source})"
                    else:
                        display = weapon_name
                else:
                    display = str(weapon)
                sections.append(f"> - {display}")
            sections.append(">")

        # Weapon Masteries (2024 rules feature) - try v6.0.0 structure first, then legacy
        weapon_masteries = proficiencies_data.get('weapon_masteries', [])
        if not weapon_masteries:
            weapon_masteries = character_data.get('weapon_masteries', [])

        if weapon_masteries:
            sections.append(">### Weapon Masteries")
            sections.append(">")
            sections.append(">*Special weapon properties you can use (2024 rules)*")
            sections.append(">")
            for mastery in weapon_masteries:
                if isinstance(mastery, dict):
                    weapon = mastery.get('weapon', 'Unknown')
                    mastery_type = mastery.get('mastery', 'Unknown')
                    description = mastery.get('description', '')

                    sections.append(f"> - **{weapon} ({mastery_type})**")

                    # Add a cleaned snippet of the mastery description
                    if description:
                        # Extract the mastery description (after the property name in bold/italic)
                        clean_desc = self.text_processor.clean_text(description)

                        # Try to find the mastery property description
                        # Format: "<strong><em>Mastery.</em></strong> Description..."
                        import re
                        match = re.search(r'<strong><em>' + mastery_type + r'\.</em></strong>\s*(.*?)(?:<p>|$)', description, re.IGNORECASE | re.DOTALL)
                        if match:
                            clean_desc = self.text_processor.clean_text(match.group(1))

                        # Truncate if too long
                        if len(clean_desc) > 200:
                            clean_desc = clean_desc[:200] + "..."

                        sections.append(f">   {clean_desc}")
                else:
                    sections.append(f"> - {str(mastery)}")
            sections.append(">")

        # Tool proficiencies - try v6.0.0 structure first, then legacy
        tool_proficiencies = proficiencies_data.get('tool_proficiencies', [])
        if not tool_proficiencies:
            tool_proficiencies = character_data.get('tool_proficiencies', [])
            
        if tool_proficiencies:
            sections.append(">### Tools")
            sections.append(">")
            for tool in tool_proficiencies:
                if isinstance(tool, dict):
                    tool_name = tool.get('name', 'Unknown Tool')
                    source = tool.get('source', '')
                    if source:
                        display = f"{tool_name} ({source})"
                    else:
                        display = tool_name
                else:
                    display = str(tool)
                sections.append(f"> - {display}")
            sections.append(">")
        
        # Language proficiencies - try v6.0.0 structure first, then legacy
        language_proficiencies = proficiencies_data.get('language_proficiencies', [])
        if not language_proficiencies:
            language_proficiencies = character_data.get('language_proficiencies', [])
            
        if language_proficiencies:
            sections.append(">### Languages")
            sections.append(">")
            for language in language_proficiencies:
                if isinstance(language, dict):
                    language_name = language.get('name', 'Unknown Language')
                    source = language.get('source', '')
                    if source:
                        display = f"{language_name} ({source})"
                    else:
                        display = language_name
                else:
                    display = str(language)
                sections.append(f"> - {display}")
            sections.append(">")
        
        # Ability score bonuses (if available)
        abilities_data = character_data.get('abilities', {})
        ability_scores = abilities_data.get('ability_scores', {})
        
        # Check if there are any ability score bonuses beyond base
        has_bonuses = False
        for ability, score_data in ability_scores.items():
            if isinstance(score_data, dict):
                source_breakdown = score_data.get('source_breakdown', {})
                if len(source_breakdown) > 1 or (len(source_breakdown) == 1 and 'base' not in source_breakdown):
                    has_bonuses = True
                    break
        
        if has_bonuses:
            sections.append(">### Ability Score Bonuses")
            sections.append(">")
            
            for ability, score_data in ability_scores.items():
                if isinstance(score_data, dict):
                    source_breakdown = score_data.get('source_breakdown', {})
                    if len(source_breakdown) > 1 or (len(source_breakdown) == 1 and 'base' not in source_breakdown):
                        total = score_data.get('score', 0)
                        base = source_breakdown.get('base', 10)
                        
                        ability_display = ability.capitalize()
                        bonus_parts = []
                        
                        # Add each bonus source
                        for source, value in source_breakdown.items():
                            if source != 'base' and value != 0:
                                if source == 'feat':
                                    bonus_parts.append(f"Feat +{value}")
                                elif source == 'racial':
                                    bonus_parts.append(f"Racial +{value}")
                                elif source == 'asi':
                                    bonus_parts.append(f"ASI +{value}")
                                elif source == 'item':
                                    bonus_parts.append(f"Item +{value}")
                                else:
                                    bonus_parts.append(f"{source.capitalize()} +{value}")
                        
                        if bonus_parts:
                            bonus_text = " + ".join(bonus_parts)
                            sections.append(f"> - **{ability_display}** {total} (Base {base} + {bonus_text})")
            
            sections.append(">")
        
        sections.append("> ^proficiencies")
        sections.append("")
        sections.append("---")
        
        return '\n'.join(sections)