"""
Parser core interfaces for modular character markdown generation.

This module defines the core interfaces used throughout the parser system
for formatters, template managers, and text processors.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class IFormatter(ABC):
    """Interface for all character data formatters."""
    
    @abstractmethod
    def format(self, character_data: Dict[str, Any]) -> str:
        """
        Format character data into markdown text.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Formatted markdown string
        """
        pass
    
    @abstractmethod
    def validate_input(self, character_data: Dict[str, Any]) -> bool:
        """
        Validate that required fields are present in character data.
        
        Args:
            character_data: Character data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        pass


class ITemplateManager(ABC):
    """Interface for template management systems."""
    
    @abstractmethod
    def get_template(self, template_name: str) -> str:
        """
        Retrieve a template by name.
        
        Args:
            template_name: Name of the template to retrieve
            
        Returns:
            Template content as string
        """
        pass
    
    @abstractmethod
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template with provided context.
        
        Args:
            template_name: Name of the template to render
            context: Context data for template rendering
            
        Returns:
            Rendered template content
        """
        pass
    
    @abstractmethod
    def template_exists(self, template_name: str) -> bool:
        """
        Check if a template exists.
        
        Args:
            template_name: Name of the template to check
            
        Returns:
            True if template exists, False otherwise
        """
        pass


class ITextProcessor(ABC):
    """Interface for text processing utilities."""
    
    @abstractmethod
    def clean_text(self, text: str) -> str:
        """
        Clean and sanitize text for markdown output.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        pass
    
    @abstractmethod
    def clean_html(self, text: str) -> str:
        """
        Remove HTML tags from text.
        
        Args:
            text: Text containing HTML tags
            
        Returns:
            Text with HTML tags removed
        """
        pass
    
    @abstractmethod
    def truncate_text(self, text: str, max_length: int = 200) -> str:
        """
        Truncate text to specified length with ellipsis.
        
        Args:
            text: Text to truncate
            max_length: Maximum length before truncation
            
        Returns:
            Truncated text with ellipsis if needed
        """
        pass


class IValidationService(ABC):
    """Interface for input validation services."""
    
    @abstractmethod
    def validate_character_data(self, character_data: Dict[str, Any]) -> bool:
        """
        Validate complete character data structure.
        
        Args:
            character_data: Character data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def validate_section(self, section_name: str, section_data: Any) -> bool:
        """
        Validate a specific section of character data.
        
        Args:
            section_name: Name of the section to validate
            section_data: Data for the section
            
        Returns:
            True if section is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_validation_errors(self) -> List[str]:
        """
        Get list of validation errors from last validation.
        
        Returns:
            List of error messages
        """
        pass


class IPerformanceMonitor(ABC):
    """Interface for performance monitoring services."""
    
    @abstractmethod
    def start_timing(self, operation_name: str) -> None:
        """
        Start timing an operation.
        
        Args:
            operation_name: Name of the operation being timed
        """
        pass
    
    @abstractmethod
    def end_timing(self, operation_name: str) -> float:
        """
        End timing an operation and return duration.
        
        Args:
            operation_name: Name of the operation being timed
            
        Returns:
            Duration in seconds
        """
        pass
    
    @abstractmethod
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get summary of performance metrics.
        
        Returns:
            Dictionary containing performance metrics
        """
        pass