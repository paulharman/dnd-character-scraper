"""
Generator factory for dependency injection in the character parser.

This module provides factory classes for creating and configuring parser
components with proper dependency injection, allowing for flexible
configuration and testing.
"""

from typing import Dict, Any, Optional, List
import logging
import sys
import os

# Add project root to path for config manager access
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from shared.config.manager import get_config_manager

# Add parser directory to path for absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parser_dir = os.path.dirname(current_dir)
sys.path.insert(0, parser_dir)

from core.interfaces import IFormatter, ITemplateManager, ITextProcessor, IValidationService
from utils.text import TextProcessor
from utils.validation import ValidationService
from templates.obsidian import ObsidianTemplateManager
from templates.ui_toolkit import UIToolkitTemplateManager
from formatters.metadata import MetadataFormatter
from formatters.spellcasting import SpellcastingFormatter
from formatters.character_info import CharacterInfoFormatter
from formatters.abilities import AbilitiesFormatter
from formatters.combat import CombatFormatter
from formatters.features import FeaturesFormatter
from formatters.inventory import InventoryFormatter
from formatters.background import BackgroundFormatter
from formatters.proficiency import ProficiencyFormatter
from formatters.racial_traits import RacialTraitsFormatter


class GeneratorFactory:
    """
    Factory for creating configured character markdown generators.
    
    Provides dependency injection for all parser components including
    formatters, templates, and utilities.
    """
    
    def __init__(self):
        """Initialize the generator factory."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._text_processor = None
        self._validation_service = None
        self._template_managers = {}
        self._formatters = {}
    
    def create_generator(self, 
                        use_yaml_frontmatter: bool = True,
                        use_enhanced_spells: bool = True,
                        template_type: str = 'obsidian',
                        custom_config: Optional[Dict[str, Any]] = None) -> 'FactoryCharacterMarkdownGenerator':
        """
        Create a configured character markdown generator.
        
        Args:
            use_yaml_frontmatter: Whether to include YAML frontmatter
            use_enhanced_spells: Whether to use enhanced spell formatting
            template_type: Type of template manager to use ('obsidian' or 'ui_toolkit')
            custom_config: Optional custom configuration
            
        Returns:
            Configured CharacterMarkdownGenerator instance
        """
        # Create core services
        text_processor = self._get_text_processor()
        validation_service = self._get_validation_service()
        template_manager = self._get_template_manager(template_type, text_processor)
        
        # Create formatters
        formatters = self._create_formatters(
            text_processor, 
            use_yaml_frontmatter, 
            use_enhanced_spells,
            custom_config or {}
        )
        
        # Create and return generator
        return FactoryCharacterMarkdownGenerator(
            formatters=formatters,
            template_manager=template_manager,
            validation_service=validation_service,
            text_processor=text_processor
        )
    
    def _get_text_processor(self) -> ITextProcessor:
        """Get or create text processor instance."""
        if self._text_processor is None:
            self._text_processor = TextProcessor()
        return self._text_processor
    
    def _get_validation_service(self) -> IValidationService:
        """Get or create validation service instance."""
        if self._validation_service is None:
            self._validation_service = ValidationService()
        return self._validation_service
    
    def _get_template_manager(self, template_type: str, text_processor: ITextProcessor) -> ITemplateManager:
        """Get or create template manager instance."""
        if template_type not in self._template_managers:
            if template_type == 'obsidian':
                self._template_managers[template_type] = ObsidianTemplateManager(text_processor)
            elif template_type == 'ui_toolkit':
                self._template_managers[template_type] = UIToolkitTemplateManager(text_processor)
            else:
                self.logger.warning(f"Unknown template type: {template_type}, using obsidian")
                self._template_managers[template_type] = ObsidianTemplateManager(text_processor)
        
        return self._template_managers[template_type]
    
    def _create_formatters(self, 
                          text_processor: ITextProcessor, 
                          use_yaml_frontmatter: bool,
                          use_enhanced_spells: bool,
                          custom_config: Dict[str, Any]) -> Dict[str, IFormatter]:
        """Create configured formatter instances."""
        formatters = {}
        
        # Create all formatters with text processor
        formatter_classes = {
            'metadata': MetadataFormatter,
            'character_info': CharacterInfoFormatter,
            'abilities': AbilitiesFormatter,
            'combat': CombatFormatter,
            'features': FeaturesFormatter,
            'inventory': InventoryFormatter,
            'background': BackgroundFormatter,
            'spellcasting': SpellcastingFormatter,
            'proficiency': ProficiencyFormatter,
            'racial_traits': RacialTraitsFormatter,
        }
        
        # Create the background formatter instance
        background_formatter = BackgroundFormatter(text_processor)
        
        for formatter_name, formatter_class in formatter_classes.items():
            try:
                formatter = formatter_class(text_processor)
                
                # Apply custom configuration if available
                if formatter_name in custom_config:
                    formatter_config = custom_config[formatter_name]
                    if hasattr(formatter, 'configure'):
                        formatter.configure(formatter_config)
                
                formatters[formatter_name] = formatter
                
            except Exception as e:
                self.logger.error(f"Failed to create {formatter_name} formatter: {e}")
                raise
        
        # Add appearance and backstory as separate formatter wrappers
        # These use the same BackgroundFormatter instance but call specific methods
        class AppearanceFormatter:
            def __init__(self, background_formatter):
                self.background_formatter = background_formatter
            
            def format(self, character_data):
                return self.background_formatter.format_appearance(character_data)
        
        class BackstoryFormatter:
            def __init__(self, background_formatter):
                self.background_formatter = background_formatter
            
            def format(self, character_data):
                return self.background_formatter.format_backstory(character_data)
        
        # Override the background formatter to only format the background section
        class BackgroundOnlyFormatter:
            def __init__(self, background_formatter):
                self.background_formatter = background_formatter
            
            def format(self, character_data):
                return self.background_formatter.format_background(character_data)
        
        # Replace the background formatter with the background-only version
        formatters['background'] = BackgroundOnlyFormatter(background_formatter)
        
        # Add the individual formatters
        formatters['appearance'] = AppearanceFormatter(background_formatter)
        formatters['backstory'] = BackstoryFormatter(background_formatter)
        
        return formatters
    
    def create_formatter(self, formatter_type: str, text_processor: Optional[ITextProcessor] = None) -> IFormatter:
        """
        Create a single formatter instance.
        
        Args:
            formatter_type: Type of formatter to create
            text_processor: Optional text processor instance
            
        Returns:
            Configured formatter instance
        """
        if text_processor is None:
            text_processor = self._get_text_processor()
        
        formatter_classes = {
            'metadata': MetadataFormatter,
            'spellcasting': SpellcastingFormatter,
            'character_info': CharacterInfoFormatter,
            'abilities': AbilitiesFormatter,
            'combat': CombatFormatter,
            'features': FeaturesFormatter,
            'inventory': InventoryFormatter,
            'background': BackgroundFormatter,
            'proficiency': ProficiencyFormatter,
            'racial_traits': RacialTraitsFormatter,
        }
        
        if formatter_type not in formatter_classes:
            raise ValueError(f"Unknown formatter type: {formatter_type}")
        
        formatter_class = formatter_classes[formatter_type]
        return formatter_class(text_processor)
    
    def get_available_formatters(self) -> List[str]:
        """
        Get list of available formatter types.
        
        Returns:
            List of available formatter type names
        """
        return [
            'metadata',
            'spellcasting', 
            'character_info',
            'abilities',
            'combat',
            'features',
            'inventory',
            'background',
            'proficiency',
            'racial_traits'
        ]
    
    def get_available_templates(self) -> List[str]:
        """
        Get list of available template types.
        
        Returns:
            List of available template type names
        """
        return ['obsidian', 'ui_toolkit']
    
    def validate_configuration(self, config: Dict[str, Any]) -> bool:
        """
        Validate generator configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if configuration is valid, False otherwise
        """
        # Validate template type
        template_type = config.get('template_type', 'obsidian')
        if template_type not in self.get_available_templates():
            self.logger.error(f"Invalid template type: {template_type}")
            return False
        
        # Validate formatter configuration
        formatter_configs = config.get('formatters', {})
        for formatter_name in formatter_configs:
            if formatter_name not in self.get_available_formatters():
                self.logger.error(f"Invalid formatter name: {formatter_name}")
                return False
        
        return True


class FactoryCharacterMarkdownGenerator:
    """
    Main character markdown generator with dependency injection.
    
    Orchestrates the generation of character markdown using configured
    formatters and templates.
    """
    
    def __init__(self, 
                 formatters: Dict[str, IFormatter],
                 template_manager: ITemplateManager,
                 validation_service: IValidationService,
                 text_processor: ITextProcessor):
        """
        Initialize the character markdown generator.
        
        Args:
            formatters: Dictionary of configured formatters
            template_manager: Template manager instance
            validation_service: Validation service instance
            text_processor: Text processor instance
        """
        self.formatters = formatters
        self.template_manager = template_manager
        self.validation_service = validation_service
        self.text_processor = text_processor
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def generate_markdown(self, character_data: Dict[str, Any]) -> str:
        """
        Generate complete character markdown.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Generated markdown content
        """
        # Validate input
        if not self.validation_service.validate_character_data(character_data):
            errors = self.validation_service.get_validation_errors()
            self.logger.error(f"Character data validation failed: {errors}")
            raise ValueError(f"Invalid character data: {errors}")
        
        sections = []
        
        # Get section order from config, with fallback to default
        section_order = self._get_section_order()
        
        for section_name in section_order:
            formatter = self.formatters.get(section_name)
            if formatter:
                try:
                    section_content = formatter.format(character_data)
                    if section_content:
                        sections.append(section_content)
                except Exception as e:
                    self.logger.error(f"Failed to format {section_name}: {e}")
                    # Continue with other sections
        
        # Join sections with appropriate spacing
        if sections:
            return '\n\n'.join(sections)
        else:
            return "# Character Sheet\n\n*No content generated*"
    
    def _get_section_order(self) -> List[str]:
        """
        Get section order from config with fallback to default.
        
        Returns:
            List of section names in order
        """
        try:
            config_manager = get_config_manager()
            config_order = config_manager.get_config_value('parser', 'output', 'section_order', default=None)
            
            if config_order and isinstance(config_order, list):
                return config_order
        except Exception as e:
            self.logger.warning(f"Failed to get section order from config: {e}")
        
        # Default order (matches original behavior)
        return [
            'metadata',
            'character_info', 
            'abilities',
            'appearance',
            'spellcasting',
            'features',
            'racial_traits',
            'combat',
            'proficiency',
            'background',
            'backstory',
            'inventory'
        ]
    
    def generate_section(self, section_name: str, character_data: Dict[str, Any]) -> str:
        """
        Generate a specific section of the character sheet.
        
        Args:
            section_name: Name of the section to generate
            character_data: Complete character data dictionary
            
        Returns:
            Generated section content
        """
        formatter = self.formatters.get(section_name)
        if not formatter:
            raise ValueError(f"Unknown section: {section_name}")
        
        return formatter.format(character_data)
    
    def get_available_sections(self) -> List[str]:
        """
        Get list of available section names.
        
        Returns:
            List of available section names
        """
        return list(self.formatters.keys())
    
    def validate_character_data(self, character_data: Dict[str, Any]) -> bool:
        """
        Validate character data using the validation service.
        
        Args:
            character_data: Character data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        return self.validation_service.validate_character_data(character_data)
    
    def get_validation_errors(self) -> List[str]:
        """
        Get validation errors from the last validation.
        
        Returns:
            List of validation error messages
        """
        return self.validation_service.get_validation_errors()