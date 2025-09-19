"""
Text processing utilities for character markdown generation.

This module provides text cleaning, HTML processing, and other text
manipulation utilities used throughout the parser system.
"""

import re
import html
from typing import Optional, Dict, Any
import logging

# Import interface using absolute import
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.interfaces import ITextProcessor


class TextProcessor(ITextProcessor):
    """
    Text processing utilities for markdown generation.
    
    Handles text cleaning, HTML tag removal, and other text manipulation
    tasks required for generating clean markdown output.
    """
    
    def __init__(self):
        """Initialize the text processor."""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Compile regex patterns for better performance
        self.html_tag_pattern = re.compile(r'<[^>]+>')
        self.whitespace_pattern = re.compile(r'[ \t]+')  # Only horizontal whitespace, not newlines
        self.line_break_pattern = re.compile(r'[\n\r]+')
    
    def clean_text(self, text: str) -> str:
        """
        Clean and sanitize text for markdown output.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text safe for markdown
        """
        if not text:
            return ""
        
        # Use the full preprocessing pipeline to handle tables, formatting, etc.
        text = self._preprocess_dnd_html(text)
        text = self.clean_html_preserve_mdash(text)
        text = self._convert_dnd_formatting(text)
        text = self._postprocess_dnd_content(text)
        
        # Note: YAML escaping removed to preserve table structure in feature descriptions
        
        # Normalize whitespace while preserving paragraph structure
        text = self._normalize_spell_whitespace(text)
        
        return text.strip()
    
    def clean_html(self, text: str) -> str:
        """
        Remove HTML tags from text.
        
        Args:
            text: Text containing HTML tags
            
        Returns:
            Text with HTML tags removed
        """
        if not text:
            return ""
        
        # Remove HTML tags using compiled regex
        text = self.html_tag_pattern.sub('', text)
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Handle common HTML entities that html.unescape might miss
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        text = text.replace('&nbsp;', ' ')
        
        return text
    
    def clean_html_preserve_mdash(self, text: str) -> str:
        """
        Remove HTML tags from text but preserve &mdash; to match backup original.
        
        Args:
            text: Text containing HTML tags
            
        Returns:
            Text with HTML tags removed but &mdash; preserved
        """
        if not text:
            return ""
        
        # Remove HTML tags using compiled regex
        text = self.html_tag_pattern.sub('', text)
        
        # Decode HTML entities EXCEPT &mdash; to match backup original
        # First, temporarily protect &mdash;
        text = text.replace('&mdash;', '§MDASH§')
        
        # Decode other HTML entities
        text = html.unescape(text)
        
        # Handle common HTML entities that html.unescape might miss
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        text = text.replace('&nbsp;', ' ')
        
        # Restore &mdash; to match backup original
        text = text.replace('§MDASH§', '&mdash;')
        
        return text
    
    def truncate_text(self, text: str, max_length: int = 200) -> str:
        """
        Truncate text to specified length with ellipsis.
        
        Args:
            text: Text to truncate
            max_length: Maximum length before truncation
            
        Returns:
            Truncated text with ellipsis if needed
        """
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        # Find the last space before max_length to avoid cutting words
        truncate_at = max_length - 3  # Account for ellipsis
        last_space = text.rfind(' ', 0, truncate_at)
        
        if last_space > 0:
            return text[:last_space] + "..."
        else:
            return text[:truncate_at] + "..."
    
    def _escape_yaml_special_chars(self, text: str) -> str:
        """
        Escape special characters for YAML safety.
        
        Args:
            text: Text to escape
            
        Returns:
            Text with YAML special characters escaped
        """
        if not text:
            return ""
        
        # Escape double quotes
        text = text.replace('"', '\\"')
        
        # Replace line breaks with spaces for YAML values
        text = self.line_break_pattern.sub(' ', text)
        
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text.
        
        Args:
            text: Text to normalize
            
        Returns:
            Text with normalized whitespace
        """
        if not text:
            return ""
        
        # Replace multiple whitespace characters with single space
        return self.whitespace_pattern.sub(' ', text)
    
    def clean_markdown_text(self, text: str) -> str:
        """
        Clean text specifically for markdown content (not YAML).
        
        Args:
            text: Text to clean for markdown
            
        Returns:
            Cleaned text suitable for markdown content
        """
        if not text:
            return ""
        
        # Remove HTML tags
        text = self.clean_html(text)
        
        # Escape markdown special characters
        text = self._escape_markdown_chars(text)
        
        # Normalize whitespace but preserve line breaks
        text = self._normalize_markdown_whitespace(text)
        
        return text.strip()
    
    def _escape_markdown_chars(self, text: str) -> str:
        """
        Escape special markdown characters.
        
        Args:
            text: Text to escape
            
        Returns:
            Text with markdown characters escaped
        """
        if not text:
            return ""
        
        # Escape common markdown special characters
        markdown_chars = ['*', '_', '`', '[', ']', '(', ')', '#', '!', '|']
        for char in markdown_chars:
            text = text.replace(char, f'\\{char}')
        
        return text
    
    def _normalize_markdown_whitespace(self, text: str) -> str:
        """
        Normalize whitespace for markdown content.
        
        Args:
            text: Text to normalize
            
        Returns:
            Text with normalized whitespace preserving line breaks
        """
        if not text:
            return ""
        
        # Split into lines and normalize each line
        lines = text.split('\n')
        normalized_lines = []
        
        for line in lines:
            # Normalize whitespace within each line
            normalized_line = self.whitespace_pattern.sub(' ', line.strip())
            normalized_lines.append(normalized_line)
        
        return '\n'.join(normalized_lines)
    
    def format_spell_description(self, description: str) -> str:
        """
        Format spell description for markdown output with enhanced D&D Beyond support.
        
        Args:
            description: Raw spell description from D&D Beyond
            
        Returns:
            Formatted spell description for markdown
        """
        if not description:
            return ""
        
        # Handle D&D Beyond specific HTML patterns before general cleaning
        description = self._preprocess_dnd_html(description)
        
        # Clean HTML but preserve some formatting, keeping &mdash; to match backup original
        description = self.clean_html_preserve_mdash(description)
        
        # Convert common D&D formatting patterns
        description = self._convert_dnd_formatting(description)
        
        # Post-process D&D Beyond specific content
        description = self._postprocess_dnd_content(description)
        
        # Normalize whitespace but preserve paragraph breaks
        description = self._normalize_spell_whitespace(description)
        
        return description.strip()
    
    def _convert_dnd_formatting(self, text: str) -> str:
        """
        Convert D&D specific formatting patterns to markdown.
        
        Args:
            text: Text with D&D formatting
            
        Returns:
            Text with markdown formatting
        """
        if not text:
            return ""
        
        # Convert D&D Beyond bold patterns (already in markdown format, ensure proper escaping)
        text = re.sub(r'\*\*([^*]+)\*\*', r'**\1**', text)
        
        # Convert D&D Beyond italic patterns
        text = re.sub(r'\*([^*]+)\*', r'*\1*', text)
        
        # Convert dice notation to inline code with better pattern matching
        # Only convert dice notation that isn't already backticked
        text = re.sub(r'(?<!`)(\d+d\d+(?:\s*[+-]\s*\d+)?)(?!`)', r'`\1`', text)
        
        # Convert "At Higher Levels" sections to bold
        text = re.sub(r'^(At Higher Levels\.?)(.*)$', r'**\1**\2', text, flags=re.MULTILINE)
        
        # Convert spell component abbreviations to more readable format
        text = re.sub(r'\b([VSM])\b', r'**\1**', text)
        
        # Convert damage types to emphasized text
        damage_types = ['acid', 'bludgeoning', 'cold', 'fire', 'force', 'lightning', 
                       'necrotic', 'piercing', 'poison', 'psychic', 'radiant', 'slashing', 'thunder']
        for damage_type in damage_types:
            text = re.sub(rf'\b({damage_type})\s+damage\b', rf'*\1 damage*', text, flags=re.IGNORECASE)
        
        # Convert condition names to emphasized text
        conditions = ['blinded', 'charmed', 'deafened', 'exhaustion', 'frightened', 'grappled', 
                     'incapacitated', 'invisible', 'paralyzed', 'petrified', 'poisoned', 'prone', 
                     'restrained', 'stunned', 'unconscious']
        for condition in conditions:
            text = re.sub(rf'\b({condition})\b', rf'*\1*', text, flags=re.IGNORECASE)
        
        return text
    
    def _preprocess_dnd_html(self, text: str) -> str:
        """
        Handle D&D Beyond specific HTML patterns before general HTML cleaning.
        
        Args:
            text: Raw HTML text from D&D Beyond
            
        Returns:
            Text with D&D specific HTML patterns converted
        """
        if not text:
            return ""
        
        # Convert D&D Beyond paragraph tags to markdown line breaks
        # Handle both regular <p> tags and <p class="..."> tags
        text = re.sub(r'<p[^>]*>', '', text)  # Remove opening p tags
        text = re.sub(r'</p>', '\n\n', text)  # Replace closing p tags with double newline
        
        # Clean up \r\n sequences that interfere with paragraph splitting
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\r', '\n', text)
        
        # Convert D&D Beyond strong/em tags with classes
        text = re.sub(r'<strong[^>]*>([^<]+)</strong>', r'**\1**', text)
        text = re.sub(r'<em[^>]*>([^<]+)</em>', r'*\1*', text)
        
        # Convert D&D Beyond span tags with inline subheading classes
        text = re.sub(r'<span[^>]*[Ii]nline-[Ss]ubhead[^>]*>([^<]+)</span>', r'**\1**', text)
        
        # Handle D&D Beyond specific line break patterns
        text = re.sub(r'<br\s*/?\s*>', '\n', text)
        text = re.sub(r'&nbsp;', ' ', text)
        
        # Handle D&D Beyond action tags
        text = re.sub(r'\[action\]([^[]+)\[/action\]', r'**\1**', text)
        text = re.sub(r'\[items\]([^[]+)\[/items\]', r'*\1*', text)
        
        # Convert HTML tables to markdown format
        text = self._convert_html_tables_to_markdown(text)
        text = re.sub(r'\[wprop\]([^[]+)\[/wprop\]', r'*\1*', text)
        
        return text
    
    def _postprocess_dnd_content(self, text: str) -> str:
        """
        Post-process D&D content for better markdown formatting.
        
        Args:
            text: Text after HTML cleaning
            
        Returns:
            Text with improved D&D content formatting
        """
        if not text:
            return ""
        
        # Fix common D&D Beyond formatting quirks
        text = re.sub(r'\s+&mdash;\s+', ' — ', text)
        text = re.sub(r'\s+—\s+', ' — ', text)
        
        # Clean up excessive whitespace around punctuation (preserve newlines)
        text = re.sub(r'[ \t]+([.,:;!?])', r'\1', text)
        text = re.sub(r'([.,:;!?])[ \t]+', r'\1 ', text)
        
        # Ensure proper spacing around backticked content without doubling backticks
        text = re.sub(r'(\S)`([^`]+)`(\S)', r'\1 `\2` \3', text)  # Add spaces around backticked content
        text = re.sub(r'^`([^`]+)`(\S)', r'`\1` \2', text, flags=re.MULTILINE)  # Space after at start of line
        text = re.sub(r'(\S)`([^`]+)`$', r'\1 `\2`', text, flags=re.MULTILINE)  # Space before at end of line
        
        # Fix double markdown formatting
        text = re.sub(r'\*\*\*\*([^*]+)\*\*\*\*', r'**\1**', text)
        text = re.sub(r'\*\*\*([^*]+)\*\*\*', r'**\1**', text)
        
        return text
    
    def _normalize_spell_whitespace(self, text: str) -> str:
        """
        Normalize whitespace for spell descriptions while preserving paragraph structure.
        
        Args:
            text: Spell text to normalize
            
        Returns:
            Text with normalized whitespace
        """
        if not text:
            return ""
        
        # Split into paragraphs first
        paragraphs = text.split('\n\n')
        normalized_paragraphs = []
        
        for paragraph in paragraphs:
            if paragraph.strip():
                # Normalize whitespace within each paragraph but preserve single line breaks
                lines = paragraph.split('\n')
                normalized_lines = []
                
                for line in lines:
                    normalized_line = self.whitespace_pattern.sub(' ', line.strip())
                    if normalized_line:
                        normalized_lines.append(normalized_line)
                
                if normalized_lines:
                    normalized_paragraphs.append('\n'.join(normalized_lines))
        
        return '\n\n'.join(normalized_paragraphs)
    
    def format_item_description(self, description: str, max_length: int = 200) -> str:
        """
        Format item description for inventory lists.
        
        Args:
            description: Raw item description
            max_length: Maximum length before truncation
            
        Returns:
            Formatted and truncated item description
        """
        if not description:
            return ""
        
        # Clean and normalize
        description = self.clean_text(description)
        
        # Truncate if necessary
        description = self.truncate_text(description, max_length)
        
        return description
    
    def format_character_name(self, name: str) -> str:
        """
        Format character name for consistent display.
        
        Args:
            name: Raw character name
            
        Returns:
            Formatted character name
        """
        if not name:
            return "Unknown Character"
        
        # Clean and normalize
        name = self.clean_text(name)
        
        # Capitalize first letter of each word
        return name.title()
    
    def format_class_string(self, classes: list) -> str:
        """
        Format class information into a readable string.
        
        Args:
            classes: List of class dictionaries
            
        Returns:
            Formatted class string
        """
        if not classes:
            return "Unknown Class"
        
        formatted_classes = []
        for cls in classes:
            name = cls.get('name', 'Unknown')
            level = cls.get('level', 1)
            formatted_classes.append(f"{name} {level}")
        
        return ", ".join(formatted_classes)
    
    def _convert_html_tables_to_markdown(self, text: str) -> str:
        """
        Convert HTML tables to markdown table format.
        
        Args:
            text: Text containing HTML tables
            
        Returns:
            Text with HTML tables converted to markdown
        """
        if not text:
            return ""
        
        # Simple table conversion - extract table content and format as markdown
        table_pattern = re.compile(r'<table[^>]*>.*?</table>', re.DOTALL | re.IGNORECASE)
        
        def convert_table(match):
            table_html = match.group(0)
            
            # Extract caption if present
            caption_match = re.search(r'<caption[^>]*>([^<]+)</caption>', table_html, re.IGNORECASE)
            caption = caption_match.group(1) if caption_match else ""
            
            # Extract rows
            row_pattern = re.compile(r'<tr[^>]*>(.*?)</tr>', re.DOTALL | re.IGNORECASE)
            rows = row_pattern.findall(table_html)
            
            if not rows:
                return ""
            
            markdown_rows = []
            headers = []
            
            for i, row in enumerate(rows):
                # Extract cells (th or td)
                cell_pattern = re.compile(r'<t[hd][^>]*>(.*?)</t[hd]>', re.DOTALL | re.IGNORECASE)
                cells = cell_pattern.findall(row)
                
                if not cells:
                    continue
                
                # Clean cell content
                cleaned_cells = []
                for cell in cells:
                    # Remove HTML tags and clean up
                    cell_text = re.sub(r'<[^>]+>', '', cell).strip()
                    cell_text = re.sub(r'\s+', ' ', cell_text)
                    cleaned_cells.append(cell_text)
                
                if i == 0 and not headers:
                    # First row is likely headers
                    headers = cleaned_cells
                    markdown_rows.append('| ' + ' | '.join(headers) + ' |')
                    # Add separator row
                    separator = '|' + ''.join([' --- |' for _ in headers])
                    markdown_rows.append(separator)
                else:
                    # Data row
                    markdown_rows.append('| ' + ' | '.join(cleaned_cells) + ' |')
            
            # Build final table
            result = ""
            if caption:
                result += f"**{caption}**\n\n"
            
            if markdown_rows:
                result += '\n'.join(markdown_rows)
            
            return result
        
        # Replace all tables with markdown versions
        text = table_pattern.sub(convert_table, text)
        
        return text