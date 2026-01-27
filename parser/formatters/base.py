"""
Base formatter class for character markdown generation.

This module provides the base formatter class that all specific formatters
inherit from, ensuring consistent behavior and interface implementation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

# Import interfaces and utilities using absolute import
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.interfaces import IFormatter, ITextProcessor, IPerformanceMonitor
# Removed V6ToV5Adapter import - no longer needed


class BaseFormatter(IFormatter, ABC):
    """
    Base class for all character data formatters.
    
    Provides common functionality and ensures consistent interface
    implementation across all formatters.
    """
    
    def __init__(self, text_processor: ITextProcessor, 
                 performance_monitor: Optional[IPerformanceMonitor] = None):
        """
        Initialize the base formatter.
        
        Args:
            text_processor: Text processing utilities
            performance_monitor: Optional performance monitoring service
        """
        self.text_processor = text_processor
        self.performance_monitor = performance_monitor
        self.logger = logging.getLogger(self.__class__.__name__)
# Removed data adapter - formatters now work directly with current format
    
    def format(self, character_data: Dict[str, Any]) -> str:
        """
        Format character data into markdown text with performance monitoring.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Formatted markdown string
        """
        if not self.validate_input(character_data):
            raise ValueError(f"Invalid character data for {self.__class__.__name__}")
        
        # Work directly with the current character data format
        
        # Start performance monitoring if available
        if self.performance_monitor:
            self.performance_monitor.start_timing(f"{self.__class__.__name__}.format")
        
        try:
            result = self._format_internal(character_data)
            return result
        except Exception as e:
            self.logger.error(f"Error formatting character data: {e}")
            raise
        finally:
            # End performance monitoring if available
            if self.performance_monitor:
                duration = self.performance_monitor.end_timing(f"{self.__class__.__name__}.format")
                self.logger.debug(f"Parser:   Formatting completed in {duration:.3f}s")
    
    @abstractmethod
    def _format_internal(self, character_data: Dict[str, Any]) -> str:
        """
        Internal formatting method to be implemented by subclasses.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Formatted markdown string
        """
        pass
    
    def validate_input(self, character_data: Dict[str, Any]) -> bool:
        """
        Base validation that checks for required top-level fields.
        
        Args:
            character_data: Character data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        if not isinstance(character_data, dict):
            self.logger.error("Character data must be a dictionary")
            return False
        
        # Check for character info section (either new or old format)
        if not (character_data.get('character_info') or character_data.get('basic_info')):
            self.logger.error("Missing required field: character_info or basic_info")
            return False
        
        # Check other required fields
        required_fields = self._get_required_fields()
        for field in required_fields:
            if field not in character_data:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        return self._validate_internal(character_data)
    
    def _get_required_fields(self) -> List[str]:
        """
        Get list of required fields for this formatter.
        
        Override in subclasses to specify required fields.
        Note: character info fields (basic_info/character_info) are handled separately
        
        Returns:
            List of required field names
        """
        return []  # Character info validation is handled in validate_input
    
    def get_character_info(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get character info from current v6.0.0 or backup format.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Character info dictionary
        """
        # Try new v6.0.0 format first (character_info), then backup format (basic_info)
        return character_data.get('character_info', character_data.get('basic_info', {}))
    
    def get_meta_info(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get meta info from adapted data format.
        
        Args:
            character_data: Complete character data dictionary (adapted to v5.2.0 format)
            
        Returns:
            Meta info dictionary
        """
        return character_data.get('meta', {})
    
    def get_ability_scores(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get ability scores from current v6.0.0 or backup format.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Ability scores dictionary
        """
        # Try new v6.0.0 format first (abilities.ability_scores), then backup format (ability_scores)
        abilities = character_data.get('abilities', {})
        if 'ability_scores' in abilities:
            return abilities['ability_scores']
        
        # Fallback to backup format
        return character_data.get('ability_scores', {})
    
    def get_spells(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get spells from current v6.0.0 or backup format.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Spells dictionary organized by source
        """
        # Both v6.0.0 and backup formats use 'spells' key with same structure
        return character_data.get('spells', {})
    
    def get_feature_choices(self, character_data: Dict[str, Any], feature_name: str) -> Dict[str, List[str]]:
        """
        Extract actual choices made for a feature (spells, languages, skills, etc.).
        
        Args:
            character_data: Complete character data
            feature_name: Name of the feature to find choices for
            
        Returns:
            Dictionary with choice types as keys and lists of choices as values
        """
        choices = {}
        
        # Get spells granted by this feature
        spells = character_data.get('spells', {})
        feature_spells = []
        for source, spell_list in spells.items():
            for spell in spell_list:
                if isinstance(spell, dict):
                    spell_source = spell.get('source', '')
                    # Check for exact match first
                    if spell_source == feature_name:
                        feature_spells.append(spell.get('name', 'Unknown Spell'))
                    # Check for racial spells with intelligent matching
                    elif self._should_show_racial_spells_for_feature(feature_name, spell.get('name', ''), character_data) and spell_source == 'Racial':
                        feature_spells.append(spell.get('name', 'Unknown Spell'))
        
        if feature_spells:
            choices['spells'] = feature_spells
        
        # Get languages granted by this feature
        proficiencies = character_data.get('proficiencies', {})
        language_profs = proficiencies.get('language_proficiencies', [])
        feature_languages = []
        for lang in language_profs:
            if isinstance(lang, dict) and feature_name.lower() in lang.get('source', '').lower():
                feature_languages.append(lang.get('name', 'Unknown Language'))
        
        if feature_languages:
            choices['languages'] = feature_languages
        
        # Get skills granted by this feature
        skill_profs = proficiencies.get('skill_proficiencies', [])
        feature_skills = []
        for skill in skill_profs:
            if isinstance(skill, dict) and feature_name.lower() in skill.get('source', '').lower():
                feature_skills.append(skill.get('name', 'Unknown Skill'))
        
        if feature_skills:
            choices['skills'] = feature_skills
        
        # Get tool proficiencies granted by this feature
        tool_profs = proficiencies.get('tool_proficiencies', [])
        feature_tools = []
        for tool in tool_profs:
            if isinstance(tool, dict) and feature_name.lower() in tool.get('source', '').lower():
                feature_tools.append(tool.get('name', 'Unknown Tool'))
        
        if feature_tools:
            choices['tools'] = feature_tools
        
        return choices
    
    def format_feature_choices(self, choices: Dict[str, List[str]]) -> List[str]:
        """
        Format feature choices for display.
        
        Args:
            choices: Dictionary of choice types and their values
            
        Returns:
            List of formatted choice strings
        """
        formatted_choices = []
        
        # Order choices by importance/frequency
        choice_order = ['spells', 'languages', 'skills', 'tools', 'fighting_styles', 'expertise']
        
        for choice_type in choice_order:
            if choice_type in choices and choices[choice_type]:
                choice_list = ', '.join(choices[choice_type])
                if choice_type == 'spells':
                    formatted_choices.append(f"*Chosen Spells: {choice_list}*")
                elif choice_type == 'languages':
                    formatted_choices.append(f"*Chosen Languages: {choice_list}*")
                elif choice_type == 'skills':
                    formatted_choices.append(f"*Chosen Skills: {choice_list}*")
                elif choice_type == 'tools':
                    formatted_choices.append(f"*Chosen Tools: {choice_list}*")
                elif choice_type == 'fighting_styles':
                    formatted_choices.append(f"*Chosen Fighting Style: {choice_list}*")
                elif choice_type == 'expertise':
                    formatted_choices.append(f"*Expertise: {choice_list}*")
        
        return formatted_choices
    
    def _should_show_racial_spells_for_feature(self, feature_name: str, spell_name: str, character_data: Dict[str, Any]) -> bool:
        """
        Determine if a racial spell should be shown for a specific feature.
        
        Args:
            feature_name: Name of the feature to check
            spell_name: Name of the spell to check
            character_data: Complete character data
            
        Returns:
            True if this spell should be shown for this feature
        """
        # Only show racial spells for the "Elven Lineage" trait specifically
        if feature_name.lower() != 'elven lineage':
            return False
        
        # Get the trait description to analyze spell progression
        features = character_data.get('features', {})
        all_features = []
        
        # Collect all features from different categories
        if isinstance(features, dict):
            for feature_category, feature_list in features.items():
                if isinstance(feature_list, list):
                    all_features.extend(feature_list)
        elif isinstance(features, list):
            all_features = features
        
        # Find the Elven Lineage trait
        elven_lineage_trait = None
        for feature in all_features:
            if isinstance(feature, dict) and feature.get('name', '').lower() == 'elven lineage':
                elven_lineage_trait = feature
                break
        
        if not elven_lineage_trait:
            return False
        
        # Extract character level to determine which spells should be available
        character_info = self.get_character_info(character_data)
        character_level = character_info.get('level', 1)
        
        # Map spells to their availability levels based on Elven Lineage description
        spell_levels = {
            'prestidigitation': 1,    # Level 1 cantrip (High Elf)
            'dancing lights': 1,      # Level 1 cantrip (Drow)
            'druidcraft': 1,         # Level 1 cantrip (Wood Elf)
            'detect magic': 3,        # Level 3 spell (High Elf)
            'faerie fire': 3,        # Level 3 spell (Drow)
            'longstrider': 3,        # Level 3 spell (Wood Elf)
            'misty step': 5,         # Level 5 spell (High Elf)
            'darkness': 5,           # Level 5 spell (Drow)
            'pass without trace': 5   # Level 5 spell (Wood Elf)
        }
        
        spell_lower = spell_name.lower()
        required_level = spell_levels.get(spell_lower, 999)
        
        # Only show spells that the character should have access to at their level
        return character_level >= required_level
    
    def get_inventory(self, character_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get inventory from current v6.0.0 or backup format.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Inventory list
        """
        # Try new v6.0.0 format first (equipment section with basic_equipment and enhanced_equipment)
        equipment = character_data.get('equipment', {})
        if equipment:
            inventory_items = []
            
            # Collect items from basic_equipment
            basic_equipment = equipment.get('basic_equipment', [])
            if basic_equipment:
                inventory_items.extend(basic_equipment)
            
            # Collect items from enhanced_equipment (avoid duplicates by checking IDs)
            enhanced_equipment = equipment.get('enhanced_equipment', [])
            if enhanced_equipment:
                basic_ids = {item.get('id') for item in inventory_items if item.get('id')}
                for item in enhanced_equipment:
                    if item.get('id') not in basic_ids:
                        inventory_items.append(item)
            
            if inventory_items:
                return inventory_items
        
        # Try legacy container_inventory format
        container_inventory = character_data.get('container_inventory', {})
        if container_inventory and 'inventory_items' in container_inventory:
            return container_inventory['inventory_items']
        
        # Fallback to backup format
        return character_data.get('inventory', [])
    
    def get_inventory_with_containers(self, character_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get inventory items with container information included.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            List of inventory items with container information
        """
        equipment_data = character_data.get('equipment', {})
        container_inventory = equipment_data.get('container_inventory', {})
        
        if container_inventory:
            # Use container-aware extraction
            return self._extract_inventory_with_containers(container_inventory, equipment_data)
        else:
            # Fallback to base method without container info
            items = self.get_inventory(character_data)
            # Add default container info
            for item in items:
                if 'container' not in item:
                    item['container'] = 'Character'
            return items
    
    def _extract_inventory_with_containers(self, container_inventory: Dict[str, Any], equipment_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract inventory items from containers data with container information."""
        # Get item details from basic_equipment
        basic_equipment = equipment_data.get('basic_equipment', [])
        container_mapping = container_inventory.get('containers', {})
        
        # Create item lookup by ID
        item_lookup = {item.get('id'): item for item in basic_equipment}
        
        inventory_items = []
        for container_id, container_info in container_mapping.items():
            container_name = container_info.get('name', 'Unknown Container')
            is_character = container_info.get('is_character', False)
            
            for item_id in container_info.get('items', []):
                if item_id in item_lookup:
                    item = item_lookup[item_id].copy()  # Don't modify original
                    # Add container information
                    item['container'] = 'Character' if is_character else container_name
                    inventory_items.append(item)
        
        return inventory_items
    
    def get_wealth(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get wealth from adapted data format.
        
        Args:
            character_data: Complete character data dictionary (adapted to v5.2.0 format)
            
        Returns:
            Wealth dictionary
        """
        # In adapted format, wealth should be at top level
        return character_data.get('wealth', {})
    
    def get_species_name(self, character_data: Dict[str, Any]) -> str:
        """
        Get species/race name from current v6.0.0 or backup format.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Species name string
        """
        # Try new v6.0.0 format first (character_info.species), then backup format (species)
        char_info = character_data.get('character_info', {})
        if 'species' in char_info:
            return char_info['species'].get('name', 'Unknown')
        
        # Fallback to backup format
        species = character_data.get('species', {})
        return species.get('name', 'Unknown')
    
    def get_background_name(self, character_data: Dict[str, Any]) -> str:
        """
        Get background name from current v6.0.0 or backup format.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Background name string
        """
        # Try new v6.0.0 format first (character_info.background), then backup format (background)
        char_info = character_data.get('character_info', {})
        if 'background' in char_info and char_info['background'] is not None:
            return char_info['background'].get('name', 'Unknown')

        # Fallback to backup format
        background = character_data.get('background', {})
        if background:
            return background.get('name', 'Unknown')
        return 'Unknown'
    
    def _validate_internal(self, character_data: Dict[str, Any]) -> bool:
        """
        Internal validation method to be implemented by subclasses.
        
        Args:
            character_data: Character data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        return True
    
    def _safe_get(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """
        Safely get a value from a dictionary with logging.
        
        Args:
            data: Dictionary to get value from
            key: Key to retrieve
            default: Default value if key not found
            
        Returns:
            Value from dictionary or default
        """
        try:
            return data.get(key, default)
        except (AttributeError, TypeError):
            self.logger.warning(f"Could not get key '{key}' from data, using default: {default}")
            return default
    
    def _clean_and_truncate(self, text: str, max_length: int = 200) -> str:
        """
        Clean and truncate text using text processor.
        
        Args:
            text: Text to clean and truncate
            max_length: Maximum length before truncation
            
        Returns:
            Cleaned and truncated text
        """
        if not text:
            return ""
        
        cleaned = self.text_processor.clean_text(text)
        return self.text_processor.truncate_text(cleaned, max_length)
    
    def _format_list(self, items: List[Any], formatter_func: callable = None) -> str:
        """
        Format a list of items into markdown list format.
        
        Args:
            items: List of items to format
            formatter_func: Optional function to format each item
            
        Returns:
            Formatted markdown list
        """
        if not items:
            return ""
        
        if formatter_func is None:
            formatter_func = str
        
        formatted_items = []
        for item in items:
            try:
                formatted_item = formatter_func(item)
                if formatted_item:
                    formatted_items.append(f"- {formatted_item}")
            except Exception as e:
                self.logger.warning(f"Error formatting list item: {e}")
                continue
        
        return "\n".join(formatted_items)
    
    def _format_dict(self, data: Dict[str, Any], key_formatter: callable = None,
                    value_formatter: callable = None) -> str:
        """
        Format a dictionary into markdown format.
        
        Args:
            data: Dictionary to format
            key_formatter: Optional function to format keys
            value_formatter: Optional function to format values
            
        Returns:
            Formatted markdown content
        """
        if not data:
            return ""
        
        if key_formatter is None:
            key_formatter = str
        if value_formatter is None:
            value_formatter = str
        
        formatted_items = []
        for key, value in data.items():
            try:
                formatted_key = key_formatter(key)
                formatted_value = value_formatter(value)
                if formatted_key and formatted_value:
                    formatted_items.append(f"**{formatted_key}**: {formatted_value}")
            except Exception as e:
                self.logger.warning(f"Error formatting dict item {key}: {e}")
                continue
        
        return "\n".join(formatted_items)
    
    
    
