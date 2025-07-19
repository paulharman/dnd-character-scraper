"""
DnD UI Toolkit template manager for character sheet generation.

This module provides templates for DnD UI Toolkit code blocks including
stats, abilities, skills, healthpoints, consumables, and other game-specific
formatting components.
"""

from typing import Dict, Any, List, Optional
import logging

# Import interface and utilities using absolute import
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.interfaces import ITemplateManager
from utils.text import TextProcessor


class UIToolkitTemplateManager(ITemplateManager):
    """
    Template manager for DnD UI Toolkit code blocks.
    
    Provides templates for game-specific UI components like ability scores,
    spell slots, health points, and other D&D-specific formatting.
    """
    
    def __init__(self, text_processor: TextProcessor):
        """
        Initialize the DnD UI Toolkit template manager.
        
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
    
    def _get_stats_template(self, **kwargs) -> str:
        """Get stats block template."""
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
    
    def _get_ability_template(self, **kwargs) -> str:
        """Get ability scores block template."""
        abilities = kwargs.get('abilities', {})
        proficiencies = kwargs.get('proficiencies', [])
        
        template = "```ability\n"
        template += "abilities:\n"
        
        # Standard ability order
        ability_order = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        
        for ability_name in ability_order:
            if ability_name in abilities:
                template += f"  {ability_name}: {abilities[ability_name]}\n"
        
        if proficiencies:
            template += "\nproficiencies:\n"
            for prof in proficiencies:
                template += f"  - {prof}\n"
        
        template += "```"
        
        return template
    
    def _get_skills_template(self, **kwargs) -> str:
        """Get skills block template."""
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
    
    def _get_healthpoints_template(self, **kwargs) -> str:
        """Get health points block template."""
        state_key = kwargs.get('state_key', 'character_health')
        health = kwargs.get('health', 0)
        hit_dice = kwargs.get('hit_dice', {})
        
        template = "```healthpoints\n"
        template += f"state_key: {state_key}\n"
        template += f"health: {health}\n"
        
        if hit_dice:
            template += "hitdice:\n"
            template += f"  dice: {hit_dice.get('dice', 'd6')}\n"
            template += f"  value: {hit_dice.get('value', 1)}\n"
        
        template += "```"
        
        return template
    
    def _get_consumable_template(self, **kwargs) -> str:
        """Get consumable block template."""
        label = kwargs.get('label', '')
        state_key = kwargs.get('state_key', '')
        uses = kwargs.get('uses', 0)
        items = kwargs.get('items', [])
        
        template = "```consumable\n"
        
        if items:
            # Multiple items format
            template += "items:\n"
            for item in items:
                template += f"  - label: \"{item.get('label', '')}\"\n"
                template += f"    state_key: {item.get('state_key', '')}\n"
                template += f"    uses: {item.get('uses', 0)}\n"
        else:
            # Single item format
            template += f"label: \"{label}\"\n"
            template += f"state_key: {state_key}\n"
            template += f"uses: {uses}\n"
        
        template += "```"
        
        return template
    
    def _get_spellslots_template(self, **kwargs) -> str:
        """Get spell slots consumable block template."""
        state_key = kwargs.get('state_key', 'character_spellslots')
        slots = kwargs.get('slots', {})
        
        template = "```consumable\n"
        template += "items:\n"
        
        # Standard spell slot levels
        for level in range(1, 10):
            level_key = f"level_{level}"
            if level_key in slots and slots[level_key] > 0:
                template += f"  - label: \"Level {level}\"\n"
                template += f"    state_key: {state_key}_level_{level}\n"
                template += f"    uses: {slots[level_key]}\n"
        
        template += "```"
        
        return template
    
    def _get_badges_template(self, **kwargs) -> str:
        """Get badges block template."""
        items = kwargs.get('items', [])
        
        template = "```badges\n"
        template += "items:\n"
        
        for item in items:
            template += f"  - label: {item.get('label', 'Unknown')}\n"
            template += f"    value: {item.get('value', '')}\n"
        
        template += "```"
        
        return template
    
    def _get_datacorejsx_template(self, **kwargs) -> str:
        """Get DataCore JSX block template."""
        jsx_components_dir = kwargs.get('jsx_components_dir', 'z_Templates')
        component_name = kwargs.get('component_name', 'Component')
        character_name = kwargs.get('character_name', 'Unknown Character')
        
        template = "```datacorejsx\n"
        template += f"const {{ {component_name} }} = await dc.require(\"{jsx_components_dir}/{component_name}.jsx\");\n"
        template += f"return <{component_name} characterName=\"{character_name}\" />;\n"
        template += "```"
        
        return template
    
    def _get_inventory_query_template(self, **kwargs) -> str:
        """Get inventory query DataCore JSX template."""
        jsx_components_dir = kwargs.get('jsx_components_dir', 'z_Templates')
        inventory_component = kwargs.get('inventory_component', 'InventoryManager.jsx')
        character_name = kwargs.get('character_name', 'Unknown Character')
        
        template = "```datacorejsx\n"
        template += f"const {{ InventoryQuery }} = await dc.require(\"{jsx_components_dir}/{inventory_component}\");\n"
        template += f"return <InventoryQuery characterName=\"{character_name}\" />;\n"
        template += "```"
        
        return template
    
    def _get_spell_query_template(self, **kwargs) -> str:
        """Get spell query DataCore JSX template."""
        jsx_components_dir = kwargs.get('jsx_components_dir', 'z_Templates')
        spell_component = kwargs.get('spell_component', 'SpellManager.jsx')
        character_name = kwargs.get('character_name', 'Unknown Character')
        
        template = "```datacorejsx\n"
        template += f"const {{ SpellQuery }} = await dc.require(\"{jsx_components_dir}/{spell_component}\");\n"
        template += f"return <SpellQuery characterName=\"{character_name}\" />;\n"
        template += "```"
        
        return template
    
    def _get_character_actions_template(self, **kwargs) -> str:
        """Get character actions DataCore JSX template."""
        jsx_components_dir = kwargs.get('jsx_components_dir', 'z_Templates')
        actions_component = kwargs.get('actions_component', 'ActionsManager.jsx')
        character_name = kwargs.get('character_name', 'Unknown Character')
        
        template = "```datacorejsx\n"
        template += f"const {{ ActionsQuery }} = await dc.require(\"{jsx_components_dir}/{actions_component}\");\n"
        template += f"return <ActionsQuery characterName=\"{character_name}\" />;\n"
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
        template_vars = {
            'stats': ['items', 'columns'],
            'ability': ['abilities', 'proficiencies'],
            'skills': ['proficiencies', 'expertise'],
            'healthpoints': ['state_key', 'health', 'hit_dice'],
            'consumable': ['label', 'state_key', 'uses', 'items'],
            'spellslots': ['state_key', 'slots'],
            'badges': ['items'],
            'datacorejsx': ['jsx_components_dir', 'component_name', 'character_name'],
            'inventory_query': ['jsx_components_dir', 'inventory_component', 'character_name'],
            'spell_query': ['jsx_components_dir', 'spell_component', 'character_name'],
            'character_actions': ['jsx_components_dir', 'actions_component', 'character_name']
        }
        
        return template_vars.get(template_name, [])
    
    def create_custom_block(self, block_type: str, content: str) -> str:
        """
        Create a custom DnD UI Toolkit block.
        
        Args:
            block_type: Type of the block
            content: YAML content for the block
            
        Returns:
            Formatted code block
        """
        # Clean the content
        clean_content = self.text_processor.clean_text(content)
        
        # Format the block
        block = f"```{block_type}\n"
        block += clean_content
        if not clean_content.endswith('\n'):
            block += '\n'
        block += "```"
        
        return block
    
    def validate_block_syntax(self, block_type: str, content: str) -> bool:
        """
        Validate YAML syntax for a UI Toolkit block.
        
        Args:
            block_type: Type of the block
            content: YAML content to validate
            
        Returns:
            True if syntax is valid, False otherwise
        """
        try:
            import yaml
            yaml.safe_load(content)
            return True
        except yaml.YAMLError as e:
            self.logger.warning(f"Invalid YAML syntax in {block_type} block: {e}")
            return False
        except ImportError:
            # If yaml is not available, skip validation
            self.logger.warning("PyYAML not available, skipping validation")
            return True