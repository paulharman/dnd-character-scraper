"""
Obsidian template manager for character sheet generation.

This module provides templates and formatting for Obsidian-specific
markdown features including callouts, links, and block references.
"""

from typing import Dict, Any, List, Optional
import logging

# Import interface and utilities using absolute import
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.interfaces import ITemplateManager
from utils.text import TextProcessor


class ObsidianTemplateManager(ITemplateManager):
    """
    Template manager for Obsidian-specific markdown features.
    
    Provides templates for Obsidian callouts, internal links,
    block references, and other Obsidian-specific formatting.
    """
    
    def __init__(self, text_processor: TextProcessor):
        """
        Initialize the Obsidian template manager.
        
        Args:
            text_processor: Text processing utilities
        """
        self.text_processor = text_processor
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_template(self, template_name: str) -> str:
        """
        Retrieve a template by name.
        
        Args:
            template_name: Name of the template to retrieve
            
        Returns:
            Template content as string
        """
        template_method = getattr(self, f"_get_{template_name}_template", None)
        if not template_method:
            self.logger.warning(f"Template '{template_name}' not found")
            return ""
        
        return template_method()
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template with provided context.
        
        Args:
            template_name: Name of the template to render
            context: Context data for template rendering
            
        Returns:
            Rendered template content
        """
        template_method = getattr(self, f"_get_{template_name}_template", None)
        if not template_method:
            self.logger.warning(f"Template '{template_name}' not found")
            return ""
        
        return template_method(**context)
    
    def template_exists(self, template_name: str) -> bool:
        """
        Check if a template exists.
        
        Args:
            template_name: Name of the template to check
            
        Returns:
            True if template exists, False otherwise
        """
        return hasattr(self, f"_get_{template_name}_template")
    
    def format_callout(self, callout_type: str, title: str, content: str, collapsible: bool = False) -> str:
        """
        Format an Obsidian callout block.
        
        Args:
            callout_type: Type of callout (info, warning, danger, success, etc.)
            title: Title for the callout
            content: Content of the callout
            collapsible: Whether the callout should be collapsible
            
        Returns:
            Formatted callout block
        """
        collapse_symbol = "+" if collapsible else ""
        
        # Clean the content
        clean_content = self.text_processor.clean_text(content)
        
        # Format the callout
        callout = f"> [!{callout_type}]{collapse_symbol} {title}\n"
        
        # Add content with proper indentation
        if clean_content:
            content_lines = clean_content.split('\n')
            for line in content_lines:
                callout += f"> {line}\n"
        
        return callout
    
    def format_internal_link(self, target: str, display_text: Optional[str] = None) -> str:
        """
        Format an Obsidian internal link.
        
        Args:
            target: Target of the link (can include headers with #)
            display_text: Optional display text for the link
            
        Returns:
            Formatted internal link
        """
        if display_text:
            return f"[[{target}|{display_text}]]"
        else:
            return f"[[{target}]]"
    
    def format_block_reference(self, block_id: str) -> str:
        """
        Format an Obsidian block reference.
        
        Args:
            block_id: ID of the block to reference
            
        Returns:
            Formatted block reference
        """
        return f"^{block_id}"
    
    def format_tag(self, tag_name: str) -> str:
        """
        Format an Obsidian tag.
        
        Args:
            tag_name: Name of the tag (without #)
            
        Returns:
            Formatted tag
        """
        return f"#{tag_name}"
    
    def format_embed(self, file_path: str, section: Optional[str] = None, width: Optional[int] = None) -> str:
        """
        Format an Obsidian embed.
        
        Args:
            file_path: Path to the file to embed
            section: Optional section to embed
            width: Optional width for image embeds
            
        Returns:
            Formatted embed
        """
        embed_target = file_path
        if section:
            embed_target += f"#{section}"
        
        embed = f"![[{embed_target}]]"
        
        if width:
            embed = f"![[{embed_target}|{width}]]"
        
        return embed
    
    def _get_character_infobox_template(self, **kwargs) -> str:
        """Get character infobox template."""
        character_name = kwargs.get('character_name', '{character_name}')
        avatar_url = kwargs.get('avatar_url', '')
        
        template = f"> [!infobox]+ ^character-info\n"
        template += f"> # {character_name}\n"
        
        if avatar_url:
            template += f"> ![Character Avatar|200]({avatar_url})\n"
        
        template += "> ###### Character Details\n"
        template += "> |  |  |\n"
        template += "> | --- | --- |\n"
        
        return template
    
    def _get_section_header_template(self, **kwargs) -> str:
        """Get section header template with navigation."""
        section_title = kwargs.get('section_title', 'Section')
        top_link = kwargs.get('top_link', 'Character Statistics')
        
        template = f"## {section_title}\n\n"
        template += f'<span class="right-link">[[#{top_link}|Top]]</span>'
        
        return template
    
    def _get_stats_block_template(self, **kwargs) -> str:
        """Get stats block template for DnD UI Toolkit."""
        items = kwargs.get('items', [])
        columns = kwargs.get('columns', 2)
        
        template = "```stats\n"
        template += "items:\n"
        
        for item in items:
            template += f"  - label: {item.get('label', 'Unknown')}\n"
            template += f"    value: '{item.get('value', '')}'\n"
            if 'sublabel' in item:
                template += f"    sublabel: {item['sublabel']}\n"
        
        template += f"\ngrid:\n"
        template += f"  columns: {columns}\n"
        template += "```"
        
        return template
    
    def _get_ability_block_template(self, **kwargs) -> str:
        """Get ability block template for DnD UI Toolkit."""
        abilities = kwargs.get('abilities', {})
        proficiencies = kwargs.get('proficiencies', [])
        
        template = "```ability\n"
        template += "abilities:\n"
        
        for ability_name, score in abilities.items():
            template += f"  {ability_name}: {score}\n"
        
        if proficiencies:
            template += "\nproficiencies:\n"
            for prof in proficiencies:
                template += f"  - {prof}\n"
        
        template += "```"
        
        return template
    
    def _get_skills_block_template(self, **kwargs) -> str:
        """Get skills block template for DnD UI Toolkit."""
        proficiencies = kwargs.get('proficiencies', [])
        expertise = kwargs.get('expertise', [])
        
        template = "```skills\n"
        
        if proficiencies:
            template += "proficiencies:\n"
            for prof in proficiencies:
                template += f"  - {prof}\n"
        
        if expertise:
            template += "\nexpertise:\n"
            for exp in expertise:
                template += f"  - {exp}\n"
        
        template += "```"
        
        return template
    
    def _get_consumable_block_template(self, **kwargs) -> str:
        """Get consumable block template for DnD UI Toolkit."""
        label = kwargs.get('label', '')
        state_key = kwargs.get('state_key', '')
        uses = kwargs.get('uses', 0)
        
        template = "```consumable\n"
        template += f'label: "{label}"\n'
        template += f'state_key: {state_key}\n'
        template += f'uses: {uses}\n'
        template += "```"
        
        return template
    
    def _get_healthpoints_block_template(self, **kwargs) -> str:
        """Get health points block template for DnD UI Toolkit."""
        state_key = kwargs.get('state_key', '')
        health = kwargs.get('health', 0)
        hit_dice = kwargs.get('hit_dice', {})
        
        template = "```healthpoints\n"
        template += f'state_key: {state_key}\n'
        template += f'health: {health}\n'
        
        if hit_dice:
            template += "hitdice:\n"
            template += f"  dice: {hit_dice.get('dice', 'd6')}\n"
            template += f"  value: {hit_dice.get('value', 1)}\n"
        
        template += "```"
        
        return template
    
    def _get_badges_block_template(self, **kwargs) -> str:
        """Get badges block template for DnD UI Toolkit."""
        items = kwargs.get('items', [])
        
        template = "```badges\n"
        template += "items:\n"
        
        for item in items:
            template += f"  - label: {item.get('label', 'Unknown')}\n"
            template += f"    value: {item.get('value', '')}\n"
        
        template += "```"
        
        return template
    
    def get_available_templates(self) -> List[str]:
        """
        Get list of available template names.
        
        Returns:
            List of available template names
        """
        templates = []
        for attr_name in dir(self):
            if attr_name.startswith('_get_') and attr_name.endswith('_template'):
                # Extract template name from method name
                template_name = attr_name[5:-9]  # Remove '_get_' and '_template'
                templates.append(template_name)
        
        return templates
    
    def get_template_variables(self, template_name: str) -> List[str]:
        """
        Get list of variables expected by a template.
        
        Args:
            template_name: Name of the template
            
        Returns:
            List of variable names expected by the template
        """
        # This is a simple implementation - in a real system,
        # you might want to parse the template method to extract parameters
        template_vars = {
            'character_infobox': ['character_name', 'avatar_url'],
            'section_header': ['section_title', 'top_link'],
            'stats_block': ['items', 'columns'],
            'ability_block': ['abilities', 'proficiencies'],
            'skills_block': ['proficiencies', 'expertise'],
            'consumable_block': ['label', 'state_key', 'uses'],
            'healthpoints_block': ['state_key', 'health', 'hit_dice'],
            'badges_block': ['items']
        }
        
        return template_vars.get(template_name, [])