"""
HTML Cleaning Utilities

Provides utilities for cleaning HTML content from D&D Beyond API responses.
"""

import re
import logging
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)


class HTMLCleaner:
    """Utility class for cleaning HTML content from character data."""
    
    @staticmethod
    def clean_html(text: str) -> str:
        """
        Remove HTML tags from text.
        
        Args:
            text: Text potentially containing HTML tags
            
        Returns:
            Text with HTML tags removed and whitespace normalized
        """
        if not text or not isinstance(text, str):
            return text or ""
            
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode common HTML entities
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' ',
            '&mdash;': '—',
            '&ndash;': '–',
            '&hellip;': '…',
        }
        
        for entity, replacement in html_entities.items():
            text = text.replace(entity, replacement)
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @staticmethod
    def clean_character_data(data: Dict[str, Any], clean_html: bool = True) -> Dict[str, Any]:
        """
        Recursively clean HTML from character data.
        
        Args:
            data: Character data dictionary
            clean_html: Whether to clean HTML (can be disabled)
            
        Returns:
            Character data with HTML cleaned from text fields
        """
        if not clean_html:
            return data
            
        return HTMLCleaner._clean_recursive(data)
    
    @staticmethod
    def _clean_recursive(obj: Any) -> Any:
        """Recursively clean HTML from nested data structures."""
        if isinstance(obj, dict):
            cleaned = {}
            for key, value in obj.items():
                # Clean specific text fields that commonly contain HTML
                if key in ['description', 'snippet', 'notes', 'text', 'content']:
                    cleaned[key] = HTMLCleaner.clean_html(value) if isinstance(value, str) else value
                else:
                    cleaned[key] = HTMLCleaner._clean_recursive(value)
            return cleaned
            
        elif isinstance(obj, list):
            return [HTMLCleaner._clean_recursive(item) for item in obj]
            
        elif isinstance(obj, str):
            # For standalone strings, only clean if they look like they contain HTML
            if '<' in obj and '>' in obj:
                return HTMLCleaner.clean_html(obj)
            return obj
            
        else:
            # Return other types unchanged
            return obj


def clean_character_data(data: Dict[str, Any], config_manager=None) -> Dict[str, Any]:
    """
    Clean HTML from character data based on configuration.
    
    Args:
        data: Character data dictionary
        config_manager: Configuration manager to check settings
        
    Returns:
        Character data with HTML optionally cleaned
    """
    if config_manager:
        clean_html = config_manager.get_config_value('output', 'clean_html', default=False)
    else:
        clean_html = False
        
    if clean_html:
        logger.info("Cleaning HTML tags from character data")
        return HTMLCleaner.clean_character_data(data, clean_html=True)
    
    return data