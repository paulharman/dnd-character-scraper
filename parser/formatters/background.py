"""
Background formatter for backstory, appearance, and background details.

This module handles the generation of background-related sections including
appearance, background details, and backstory information.
"""

import re
from typing import Dict, Any, List, Optional

# Import interfaces and utilities using absolute import
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging

from formatters.base import BaseFormatter
from utils.text import TextProcessor


class BackgroundFormatter(BaseFormatter):
    """
    Handles background-related section generation for character sheets.
    
    Generates comprehensive background information including appearance,
    background details, and backstory sections.
    """
    
    def __init__(self, text_processor: TextProcessor):
        """
        Initialize the background formatter.
        
        Args:
            text_processor: Text processing utilities
        """
        super().__init__(text_processor)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _get_required_fields(self) -> List[str]:
        """Get list of required fields for background formatting."""
        return []
    
    def _validate_internal(self, character_data: Dict[str, Any]) -> bool:
        """Validate character data structure for background formatting."""
        # Background formatting is flexible - most fields are optional
        return True
    
    def _format_internal(self, character_data: Dict[str, Any]) -> str:
        """
        Generate all background-related sections.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Combined background sections (appearance, background, backstory)
        """
        sections = []
        
        # Generate appearance section
        appearance_section = self.format_appearance(character_data)
        if appearance_section:
            sections.append(appearance_section)
        
        # Generate background section
        background_section = self.format_background(character_data)
        if background_section:
            sections.append(background_section)
        
        # Generate backstory section
        backstory_section = self.format_backstory(character_data)
        if backstory_section:
            sections.append(backstory_section)
        
        return '\n\n'.join(sections)
    
    def format_appearance(self, character_data: Dict[str, Any]) -> str:
        """
        Format appearance section with physical description.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Formatted appearance section
        """
        if not self.validate_input(character_data):
            return ""
        
        # Extract appearance data - check v6.0.0 structure first
        character_info = character_data.get('character_info', {})
        appearance_data = character_data.get('appearance', {})
        
        # Extract appearance details (prefer appearance section, fallback to character_info)
        gender = appearance_data.get('gender', '') or character_info.get('gender', '')
        age = appearance_data.get('age', '') or character_info.get('age', '')
        height = appearance_data.get('height', '') or character_info.get('height', '')
        weight = appearance_data.get('weight', '') or character_info.get('weight', '')
        hair = appearance_data.get('hair', '') or character_info.get('hair', '')
        eyes = appearance_data.get('eyes', '') or character_info.get('eyes', '')
        skin = appearance_data.get('skin', '') or character_info.get('skin', '')
        size = character_info.get('size', 'Medium')
        
        # Get narrative physical description if available
        physical_description = (
            appearance_data.get('description', '') or
            appearance_data.get('appearance_description', '') or 
            appearance_data.get('physical_description', '') or 
            character_data.get('description', '')
        )
        
        section = f"""## Appearance

<span class="right-link">[[#Character Statistics|Top]]</span>
> **Gender:** {gender}
> **Age:** {age}
> **Height:** {height}
> **Weight:** {weight}
> **Hair:** {hair}
> **Eyes:** {eyes}
> **Skin:** {skin}
> **Size:** {size}
>
> ^appearance"""
        
        # Add physical description if available
        if physical_description:
            clean_description = self.text_processor.clean_html(physical_description)
            section += f"""

### Physical Description

{clean_description}"""
        
        section += "\n\n---"
        
        return section
    
    def format_background(self, character_data: Dict[str, Any]) -> str:
        """
        Format background section with character background details.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Formatted background section
        """
        if not self.validate_input(character_data):
            return ""
        
        # Get background from v6.0.0 structure first, then fallback
        character_info = character_data.get('character_info', {})
        background_data = character_info.get('background', character_data.get('background', {}))
        
        if not background_data:
            return ""
        
        section = """## Background

<span class="right-link">[[#Character Statistics|Top]]</span>
"""
        
        background_name = background_data.get('name', 'Unknown')
        background_description = background_data.get('description', '')
        
        section += f">### {background_name}\n>\n"
        
        # If no description, use fallback based on background name
        if not background_description:
            background_description = self._get_fallback_background_description(background_name)
        
        # Format the main background description
        if background_description:
            # Use the existing HTML formatting method
            formatted_description = self._format_background_description(background_description)
            section += formatted_description
        else:
            section += "> Background description not available.\n>\n"
        
        # Add background proficiencies from character data
        section = self._add_background_proficiencies(section, character_data, background_name)
        
        # Add enhanced background details from JSON data
        background_details_added = False
        
        # Personal Possessions
        if background_data.get("personal_possessions"):
            section += ">### Personal Possessions\n>\n"
            section += f"> {background_data['personal_possessions']}\n>\n"
            background_details_added = True
        
        # Organizations
        if background_data.get("organizations"):
            section += ">### Organizations\n>\n"
            section += f"> {background_data['organizations']}\n>\n"
            background_details_added = True
        
        # Allies & Contacts (moved from backstory)
        notes = character_data.get('notes', {})
        allies = notes.get('allies', '')
        if allies:
            section += ">### Allies & Contacts\n>\n"
            # Format allies with proper indentation
            ally_lines = allies.split('\n')
            for line in ally_lines:
                if line.strip():
                    section += f"> {line.strip()}\n"
            section += ">\n"
            background_details_added = True
        
        # Enemies
        if background_data.get("enemies"):
            section += ">### Enemies\n>\n"
            section += f"> {background_data['enemies']}\n>\n"
            background_details_added = True
        
        # Ideals
        if background_data.get("ideals"):
            section += ">### Ideals\n>\n"
            section += f"> {background_data['ideals']}\n>\n"
            background_details_added = True
        
        # Bonds
        if background_data.get("bonds"):
            section += ">### Bonds\n>\n"
            # Format bonds with proper line breaks
            bonds_text = background_data['bonds']
            # Split on double newlines for paragraphs
            bond_paragraphs = bonds_text.split('\n\n')
            for para in bond_paragraphs:
                if para.strip():
                    section += f"> {para.strip()}\n>\n"
            background_details_added = True
        
        # Flaws
        if background_data.get("flaws"):
            section += ">### Flaws\n>\n"
            # Format flaws with proper line breaks
            flaws_text = background_data['flaws']
            flaw_lines = flaws_text.split('\n\n')
            for flaw in flaw_lines:
                if flaw.strip():
                    section += f"> {flaw.strip()}\n>\n"
            background_details_added = True
        
        # Personality Traits
        if background_data.get("personality_traits"):
            section += ">### Personality Traits\n>\n"
            # Format personality traits with proper line breaks
            traits_text = background_data['personality_traits']
            trait_lines = traits_text.split('\n\n')
            for trait in trait_lines:
                if trait.strip():
                    section += f"> {trait.strip()}\n>\n"
            background_details_added = True
        
        # Other Holdings
        if background_data.get("other_holdings"):
            section += ">### Other Holdings\n>\n"
            section += f"> {background_data['other_holdings']}\n>\n"
            background_details_added = True
        
        # Lifestyle information
        lifestyle_info = self._generate_lifestyle_info(character_data)
        if lifestyle_info:
            section += ">### Lifestyle\n>\n"
            section += f"> {lifestyle_info}\n>\n"
            background_details_added = True
        
        section += "> ^background"
        section += "\n\n---"
        
        return section
    
    def format_backstory(self, character_data: Dict[str, Any]) -> str:
        """
        Format backstory section with character backstory.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Formatted backstory section
        """
        if not self.validate_input(character_data):
            return ""
        
        section = """## Backstory

<span class="right-link">[[#Character Statistics|Top]]</span>
> """
        
        # Extract backstory from notes (allies moved to background section)
        notes = character_data.get('notes', {})
        backstory = notes.get('backstory', '')
        
        if backstory:
            # Split backstory into paragraphs and format with proper line breaks
            paragraphs = backstory.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    section += para.strip() + "\n>\n> "
        else:
            section += "*No backstory available.*\n> "
        
        # Note: Allies & Contacts section has been moved to Background section
        section += "\n> ^backstory\n\n---"
        
        return section
    
    def _format_background_description(self, description: str) -> str:
        """Format background description with proper structure and line breaks."""
        if not description:
            return "> Background description not available.\n>\n"
        
        # Handle HTML structure properly - the content uses <strong>Label:</strong>&nbsp;content<br /> format
        cleaned = description
        
        # Convert HTML entities
        cleaned = re.sub(r'&nbsp;', ' ', cleaned)
        cleaned = re.sub(r'&mdash;', '—', cleaned)
        cleaned = re.sub(r'\r\n', '\n', cleaned)
        
        # Convert HTML line breaks to newlines
        cleaned = re.sub(r'<br\s*/?>', '\n', cleaned)
        
        # Split into paragraphs first
        paragraphs = re.split(r'</p>\s*<p>', cleaned)
        
        formatted_lines = []
        
        for paragraph in paragraphs:
            # Remove paragraph tags
            para_content = re.sub(r'</?p[^>]*>', '', paragraph).strip()
            
            if not para_content:
                continue
                
            # Check if this paragraph contains structured data (with <strong> tags)
            if '<strong>' in para_content:
                # Split on line breaks within the structured paragraph
                lines = para_content.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Convert <strong>Label:</strong> to **Label:**
                    formatted_line = re.sub(r'<strong>([^<]+):</strong>', r'**\1:**', line)
                    # Remove any remaining HTML tags
                    formatted_line = re.sub(r'<[^>]+>', '', formatted_line)
                    # Clean up extra spaces
                    formatted_line = re.sub(r'\s+', ' ', formatted_line).strip()
                    
                    if formatted_line:
                        formatted_lines.append(formatted_line)
                        formatted_lines.append("")  # Add blank line after each structured line
            else:
                # This is descriptive text - clean up HTML and add as-is
                clean_para = re.sub(r'<[^>]+>', '', para_content)
                clean_para = re.sub(r'\s+', ' ', clean_para).strip()
                
                if clean_para:
                    formatted_lines.append(clean_para)
                    formatted_lines.append("")  # Add blank line after descriptive paragraph
        
        # Remove trailing empty line if present
        while formatted_lines and not formatted_lines[-1].strip():
            formatted_lines.pop()
        
        # Join lines and add proper markdown block formatting
        if formatted_lines:
            # Replace empty lines with proper line breaks in blockquotes
            formatted_result = []
            for line in formatted_lines:
                if line == "":  # Empty line
                    formatted_result.append(">")
                else:
                    formatted_result.append(f"> {line}")
            result = "\n".join(formatted_result) + "\n>\n"
        else:
            result = "> Background description not available.\n>\n"
        
        return result
    
    def _get_fallback_background_description(self, background_name: str) -> str:
        """
        Provide fallback background descriptions when none are available.
        
        Args:
            background_name: Name of the background
            
        Returns:
            Fallback description for the background
        """
        fallback_descriptions = {
            'Noble': """You understand wealth, power, and privilege. You carry a noble title, and your family owns land, collects taxes, and wields significant political influence. You might be a pampered aristocrat unfamiliar with work or discomfort, a former merchant just elevated to the nobility, or a disinherited scoundrel with a disproportionate sense of entitlement.

Or you could be an honest, hard-working landowner who cares deeply about the people who live and work on your land, keenly aware of your responsibility to them.

**Skill Proficiencies:** History, Persuasion

**Languages:** One of your choice

**Equipment:** A set of fine clothes, a signet ring, a scroll of pedigree, and a purse containing 25 gp""",
            
            'Acolyte': """You have spent your life in the service of a temple to a specific god or pantheon of gods. You act as an intermediary between the realm of the holy and the mortal world, performing sacred rites and offering sacrifices in order to conduct worshipers into the presence of the divine.

**Skill Proficiencies:** Insight, Religion
**Languages:** Two of your choice
**Equipment:** A holy symbol, a prayer book or prayer wheel, 5 sticks of incense, vestments, a set of common clothes, and a belt pouch containing 15 gp""",
            
            'Criminal': """You are an experienced criminal with a history of breaking the law. You have spent a lot of time among other criminals and still have contacts within the criminal underworld.

**Skill Proficiencies:** Deception, Stealth
**Tool Proficiencies:** One type of gaming set, thieves' tools
**Equipment:** A crowbar, a set of dark common clothes including a hood, and a belt pouch containing 15 gp""",
            
            'Folk Hero': """You come from a humble social rank, but you are destined for so much more. Already the people of your home village regard you as their champion, and your destiny calls you to stand against the tyrants and monsters that threaten the common folk everywhere.

**Skill Proficiencies:** Animal Handling, Survival
**Tool Proficiencies:** One type of artisan's tools, vehicles (land)
**Equipment:** A set of artisan's tools, a shovel, a set of common clothes, and a belt pouch containing 10 gp""",
            
            'Hermit': """You lived in seclusion for a formative part of your life. In your time apart from the clamor of society, you found quiet, solitude, and perhaps some of the answers you were looking for.

**Skill Proficiencies:** Medicine, Religion
**Tool Proficiencies:** Herbalism kit
**Languages:** One of your choice
**Equipment:** A herbalism kit, a scroll case stuffed full of notes from your studies or prayers, a winter blanket, a set of common clothes, and a belt pouch containing 5 gp""",
            
            'Soldier': """War has been your life for as long as you care to remember. You trained as a youth, studied the use of weapons and armor, learned basic survival techniques, including how to stay alive on the battlefield.

**Skill Proficiencies:** Athletics, Intimidation
**Tool Proficiencies:** One type of gaming set, vehicles (land)
**Equipment:** An insignia of rank, a trophy taken from a fallen enemy, a deck of cards, a set of common clothes, and a belt pouch containing 10 gp""",
            
            'Merchant': """You have been involved in commerce and trade, learning the ins and outs of business and negotiation. Whether you ran a family business, worked for a trading company, or struck out on your own, you understand the value of goods and how to move them profitably.

**Skill Proficiencies:** Animal Handling, Persuasion
**Tool Proficiencies:** Navigator's Tools
**Equipment:** A merchant's pack, a set of fine clothes, a signet ring, and a belt pouch containing 15 gp"""
        }
        
        return fallback_descriptions.get(background_name, f"Background: {background_name}")
    
    def _add_background_proficiencies(self, section: str, character_data: Dict[str, Any], background_name: str) -> str:
        """
        Add background-granted proficiencies to the section.
        
        Args:
            section: Current section content
            character_data: Complete character data dictionary
            background_name: Name of the background
            
        Returns:
            Updated section with background proficiencies
        """
        # Extract proficiencies from the proficiencies structure
        proficiencies = character_data.get('proficiencies', {})
        
        # Extract skill proficiencies from background
        skill_proficiencies = proficiencies.get('skill_proficiencies', [])
        background_skills = [
            skill for skill in skill_proficiencies 
            if skill.get('source_type') == 'background' and background_name.lower() in skill.get('source', '').lower()
        ]
        
        # Extract tool proficiencies from background
        tool_proficiencies = proficiencies.get('tool_proficiencies', [])
        background_tools = [
            tool for tool in tool_proficiencies 
            if tool.get('source_type') == 'background' and background_name.lower() in tool.get('source', '').lower()
        ]
        
        # Extract language proficiencies from background
        language_proficiencies = proficiencies.get('language_proficiencies', [])
        background_languages = [
            lang for lang in language_proficiencies 
            if lang.get('source_type') == 'background' and background_name.lower() in lang.get('source', '').lower()
        ]
        
        # Extract background features from the features structure
        features_data = character_data.get('features', {})
        background_features = features_data.get('background_features', [])
        
        # Add proficiency information
        if background_skills or background_tools or background_languages or background_features:
            section += ">\n>### Background Benefits\n>\n"
            
            if background_skills:
                section += "> **Skill Proficiencies:** "
                skill_names = [skill.get('name', '') for skill in background_skills]
                section += ", ".join(skill_names) + "\n>\n"
            
            if background_tools:
                section += "> **Tool Proficiencies:** "
                tool_names = [tool.get('name', '') for tool in background_tools]
                section += ", ".join(tool_names) + "\n>\n"
            
            if background_languages:
                section += "> **Language Proficiencies:** "
                lang_names = [lang.get('name', '') for lang in background_languages]
                section += ", ".join(lang_names) + "\n>\n"
            
            if background_features:
                for feature in background_features:
                    feature_name = feature.get('name', 'Unknown Feature')
                    feature_description = feature.get('description', '')
                    section += f">\n>#### {feature_name}\n>\n"
                    if feature_description:
                        # Clean HTML and format description
                        clean_description = self.text_processor.clean_html(feature_description)
                        # Split into lines and format for blockquotes
                        desc_lines = clean_description.split('\n')
                        for line in desc_lines:
                            if line.strip():
                                section += f"> {line.strip()}\n"
                        section += ">\n"
                    else:
                        section += "> *No description available*\n>\n"
        
        return section
    
    def _generate_lifestyle_info(self, character_data: Dict[str, Any]) -> str:
        """Generate lifestyle information if available."""
        # Get lifestyle from v6.0.0 structure first, then fallback
        character_info = character_data.get('character_info', {})
        lifestyle_id = character_info.get('lifestyleId')
        if not lifestyle_id:
            return ""
        
        # Map lifestyle IDs to names (from D&D Beyond data)
        lifestyle_map = {
            1: "Wretched",
            2: "Squalid", 
            3: "Poor",
            4: "Modest",
            5: "Comfortable",
            6: "Wealthy",
            7: "Aristocratic",
            8: "Aristocratic"  # Sometimes aristocratic uses ID 8
        }
        
        lifestyle_name = lifestyle_map.get(lifestyle_id, "Unknown")
        if lifestyle_name != "Unknown":
            return f"**Lifestyle:** {lifestyle_name}"
        return ""
    
    def get_background_summary(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key background information for summary purposes.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Dictionary containing key background information
        """
        # Get data from v6.0.0 structure first, then fallback
        character_info = character_data.get('character_info', {})
        background_data = character_info.get('background', character_data.get('background', {}))
        appearance_data = character_data.get('appearance', {})
        notes = character_data.get('notes', {})
        
        # Extract key information
        background_name = background_data.get('name', 'Unknown')
        has_description = bool(background_data.get('description', ''))
        has_backstory = bool(notes.get('backstory', ''))
        
        # Count appearance details
        appearance_fields = ['gender', 'age', 'height', 'weight', 'hair', 'eyes', 'skin']
        appearance_details = sum(1 for field in appearance_fields 
                               if appearance_data.get(field) or character_info.get(field))
        
        # Count background details
        background_sections = ['personal_possessions', 'organizations', 'enemies', 
                             'ideals', 'bonds', 'flaws', 'personality_traits', 'other_holdings']
        background_details = sum(1 for section in background_sections 
                               if background_data.get(section))
        
        # Check for allies
        has_allies = bool(notes.get('allies', ''))
        
        return {
            'background_name': background_name,
            'has_description': has_description,
            'has_backstory': has_backstory,
            'appearance_details_count': appearance_details,
            'background_details_count': background_details,
            'has_allies': has_allies,
            'lifestyle_id': character_info.get('lifestyleId')
        }
    
    def has_background_data(self, character_data: Dict[str, Any]) -> bool:
        """
        Check if the character has any background data to display.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            True if character has background data, False otherwise
        """
        # Get data from v6.0.0 structure first, then fallback
        character_info = character_data.get('character_info', {})
        background_data = character_info.get('background', character_data.get('background', {}))
        appearance_data = character_data.get('appearance', {})
        notes = character_data.get('notes', {})
        
        # Check for any meaningful background data
        has_background = bool(background_data.get('name') or background_data.get('description'))
        has_appearance = bool(appearance_data or any(character_info.get(field) for field in 
                                                   ['gender', 'age', 'height', 'weight', 'hair', 'eyes', 'skin']))
        has_backstory = bool(notes.get('backstory', ''))
        
        return has_background or has_appearance or has_backstory