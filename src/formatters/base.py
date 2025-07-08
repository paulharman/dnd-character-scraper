"""
Base formatter interface and common formatting utilities.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import re


class BaseFormatter(ABC):
    """Base class for all formatters."""
    
    def __init__(self, character_data: Dict[str, Any]):
        """Initialize formatter with character data."""
        self.character_data = character_data
        self.character_name = character_data.get('name', 'Unknown Character')
        self.character_level = character_data.get('level', 1)
        self.rule_version = character_data.get('rule_version', 'unknown')
    
    @abstractmethod
    def format(self) -> str:
        """Format the character data into the target format."""
        pass
    
    def clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        if not text:
            return ""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def sanitize_filename(self, name: str) -> str:
        """Sanitize a name for use as a filename."""
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
        sanitized = re.sub(r'\s+', '_', sanitized)
        return sanitized
    
    def format_modifier(self, modifier: int) -> str:
        """Format ability modifier with proper +/- sign."""
        if modifier >= 0:
            return f"+{modifier}"
        return str(modifier)
    
    def capitalize_words(self, text: str) -> str:
        """Capitalize each word in text."""
        return ' '.join(word.capitalize() for word in text.split())


class FormatterError(Exception):
    """Exception raised by formatters."""
    pass