"""
Features formatter for class features, feats, and traits.

This module handles the generation of features sections including
feats, class features, subclass features, and background abilities.
"""

from typing import Dict, Any, List, Optional

# Import interfaces and utilities using absolute import
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging

from formatters.base import BaseFormatter
from utils.text import TextProcessor


class FeaturesFormatter(BaseFormatter):
    """
    Handles features section generation for character sheets.
    
    Generates comprehensive features information including feats,
    class features, subclass features, and background abilities.
    """
    
    def __init__(self, text_processor: TextProcessor):
        """
        Initialize the features formatter.
        
        Args:
            text_processor: Text processing utilities
        """
        super().__init__(text_processor)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _get_required_fields(self) -> List[str]:
        """Get list of required fields for features formatting."""
        return []
    
    def _validate_internal(self, character_data: Dict[str, Any]) -> bool:
        """Validate character data structure for features formatting."""
        # Use proper character info accessor like other formatters
        character_info = self.get_character_info(character_data)
        
        # Check for character level - this is informational, not a blocker
        if not character_info.get('level'):
            self.logger.debug("Character level not found in character_info")
        
        return True
    
    def _format_internal(self, character_data: Dict[str, Any]) -> str:
        """
        Generate comprehensive features section.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Formatted features section
        """
        sections = []
        
        # Header
        sections.append(self._generate_header())
        
        # Feats
        sections.append(self._generate_feats_section(character_data))
        
        # Class Features
        sections.append(self._generate_class_features_section(character_data))
        
        # Class Resources
        sections.append(self._generate_class_resources_section(character_data))
        
        # Footer
        sections.append(self._generate_footer())
        
        return '\n'.join(section for section in sections if section)
    
    def _generate_header(self) -> str:
        """Generate features section header."""
        return """## Features

<span class="right-link">[[#Character Statistics|Top]]</span>"""
    
    def _generate_feats_section(self, character_data: Dict[str, Any]) -> str:
        """Generate feats section."""
        # Get feats from v6.0.0 structure first, then fallback
        features_data = character_data.get('features', {})
        feats = features_data.get('feats', [])
        
        # Fallback to top-level feats if not found
        if not feats:
            feats = character_data.get('feats', [])
        
        if not feats:
            return ""
        
        section = ""
        
        for feat in feats:
            if isinstance(feat, dict):
                name = feat.get('name', 'Unknown Feat')
                description = feat.get('description', '')
                
                section += f"\n>### {name} (Feat)\n>\n"
                
                if description:
                    # Use proper formatting for feat descriptions (similar to spells)
                    formatted_desc = self.text_processor.format_spell_description(description)
                    # Add proper blockquote formatting for multiline text
                    lines = formatted_desc.split('\n')
                    for line in lines:
                        if line.strip():
                            section += f"> {line}\n"
                        else:
                            section += ">\n"
                    
                    # Add chosen selections display for feats with choices
                    choices = self.get_feature_choices(character_data, name)
                    if choices:
                        formatted_choices = self.format_feature_choices(choices)
                        for choice in formatted_choices:
                            section += f"> {choice}\n"
                        section += ">\n"
                    
                    section += ">\n"
        
        return section
    
    def _generate_class_features_section(self, character_data: Dict[str, Any]) -> str:
        """Generate class features section."""
        # Get class features from v6.0.0 structure first, then fallback
        features_data = character_data.get('features', {})
        class_features = features_data.get('class_features', [])
        
        # Fallback to top-level class_features if not found
        if not class_features:
            class_features = character_data.get('class_features', [])
        character_info = self.get_character_info(character_data)
        character_level = character_info.get('level', 1)
        character_name = character_info.get('name', 'Unknown Character')
        
        if not class_features:
            return ""
        
        section = ""
        
        for feature in class_features:
            if isinstance(feature, dict):
                name = feature.get('name', 'Unknown Feature')
                description = feature.get('description', '')
                snippet = feature.get('snippet', '')
                level_required = feature.get('level_required', 1)
                is_subclass = feature.get('is_subclass_feature', False)
                limited_use = feature.get('limited_use')
                
                # Skip features above current level
                if level_required > character_level:
                    continue
                
                section += f"\n>### {name}\n>\n"
                
                # Add level requirement if different from 1
                if level_required > 1:
                    feature_type = "Subclass" if is_subclass else "Class"
                    section += f"> *{feature_type} Feature (Level {level_required})*\n>\n"
                
                # Add limited use information as consumable block
                if limited_use and isinstance(limited_use, dict):
                    uses = limited_use.get('uses', 0) or limited_use.get('maxUses', 0)
                    if uses > 0:
                        char_key = self._create_state_key(character_name)
                        feature_key = self._create_state_key(name)
                        section += f"> ```consumable\n"
                        section += f"> label: \"\"\n"
                        section += f"> state_key: {char_key}_{feature_key}\n"
                        section += f"> uses: {uses}\n"
                        section += f"> ```\n>\n"
                
                # Use description first (more complete), fallback to snippet if no description
                display_text = description if description else snippet
                if display_text:
                    # Use proper formatting for feature descriptions (similar to spells)
                    formatted_desc = self.text_processor.format_spell_description(display_text)
                    # Add proper blockquote formatting for multiline text
                    lines = formatted_desc.split('\n')
                    for line in lines:
                        if line.strip():
                            section += f"> {line}\n"
                        else:
                            section += ">\n"
                    
                    # Add chosen selections display for class features with choices
                    choices = self.get_feature_choices(character_data, name)
                    if choices:
                        formatted_choices = self.format_feature_choices(choices)
                        for choice in formatted_choices:
                            section += f"> {choice}\n"
                        section += ">\n"
                    
                    section += ">\n"
        
        return section
    
    def _generate_class_resources_section(self, character_data: Dict[str, Any]) -> str:
        """Generate class resources section."""
        # Get class resources from enhanced scraper data
        resources_data = character_data.get('resources', {})
        class_resources = resources_data.get('class_resources', [])
        
        if not class_resources:
            return ""
        
        section = "\n>### Class Resources\n>\n"
        
        # Group resources by class
        resources_by_class = {}
        for resource in class_resources:
            if isinstance(resource, dict):
                class_name = resource.get('class_name', 'Unknown Class')
                if class_name not in resources_by_class:
                    resources_by_class[class_name] = []
                resources_by_class[class_name].append(resource)
        
        # Format resources by class
        for class_name, class_resource_list in resources_by_class.items():
            section += f"> **{class_name}:**\n"
            
            for resource in class_resource_list:
                resource_name = resource.get('resource_name', 'Unknown Resource')
                maximum = resource.get('maximum', 0)
                current = resource.get('current', maximum)
                used = resource.get('used', 0)
                recharge_on = resource.get('recharge_on', 'long_rest')
                description = resource.get('description', '')
                
                # Format recharge type
                recharge_display = recharge_on.replace('_', ' ').title()
                
                # Create resource display
                section += f"> - **{resource_name}:** {current}/{maximum}"
                if recharge_display != 'None':
                    section += f" (Recharges on {recharge_display})"
                section += "\n"
                
                # Add description if available
                if description:
                    section += f">   *{description}*\n"
            
            section += ">\n"
        
        return section
    
    def _generate_footer(self) -> str:
        """Generate features section footer."""
        return """> ^features

---"""
    
    def _create_state_key(self, name: str) -> str:
        """Create a state key from a name for UI components."""
        return name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace(',', '')
    
    def format_feats_only(self, character_data: Dict[str, Any]) -> str:
        """
        Format only the feats section.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Feats section only
        """
        if not self.validate_input(character_data):
            raise ValueError("Invalid character data for feats formatting")
        
        return self._generate_feats_section(character_data)
    
    def format_class_features_only(self, character_data: Dict[str, Any]) -> str:
        """
        Format only the class features section.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Class features section only
        """
        if not self.validate_input(character_data):
            raise ValueError("Invalid character data for class features formatting")
        
        return self._generate_class_features_section(character_data)
    
    def get_features_summary(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key features information for summary purposes.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Dictionary containing key features information
        """
        # Get features from v6.0.0 structure first, then fallback
        features_data = character_data.get('features', {})
        feats = features_data.get('feats', character_data.get('feats', []))
        class_features = features_data.get('class_features', character_data.get('class_features', []))
        character_info = self.get_character_info(character_data)
        character_level = character_info.get('level', 1)
        
        # Count available features
        available_features = [
            feature for feature in class_features
            if isinstance(feature, dict) and feature.get('level_required', 1) <= character_level
        ]
        
        # Count limited use features
        limited_use_features = [
            feature for feature in available_features
            if feature.get('limited_use') and isinstance(feature.get('limited_use'), dict)
        ]
        
        return {
            'feat_count': len(feats),
            'feat_names': [feat.get('name', 'Unknown') for feat in feats if isinstance(feat, dict)],
            'class_feature_count': len(available_features),
            'limited_use_feature_count': len(limited_use_features),
            'subclass_feature_count': len([f for f in available_features if f.get('is_subclass_feature', False)])
        }
    
    def get_consumable_features(self, character_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract features with limited uses for consumable tracking.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            List of features with limited uses
        """
        # Get class features from v6.0.0 structure first, then fallback
        features_data = character_data.get('features', {})
        class_features = features_data.get('class_features', character_data.get('class_features', []))
        character_info = self.get_character_info(character_data)
        character_level = character_info.get('level', 1)
        character_name = character_info.get('name', 'Unknown Character')
        
        consumable_features = []
        
        for feature in class_features:
            if isinstance(feature, dict):
                name = feature.get('name', 'Unknown Feature')
                level_required = feature.get('level_required', 1)
                limited_use = feature.get('limited_use')
                
                # Skip features above current level
                if level_required > character_level:
                    continue
                
                # Check for limited use
                if limited_use and isinstance(limited_use, dict):
                    uses = limited_use.get('uses', 0) or limited_use.get('maxUses', 0)
                    if uses > 0:
                        char_key = self._create_state_key(character_name)
                        feature_key = self._create_state_key(name)
                        
                        consumable_features.append({
                            'name': name,
                            'uses': uses,
                            'state_key': f"{char_key}_{feature_key}",
                            'level_required': level_required,
                            'is_subclass': feature.get('is_subclass_feature', False)
                        })
        
        return consumable_features
    
    def has_features(self, character_data: Dict[str, Any]) -> bool:
        """
        Check if the character has any features to display.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            True if character has features, False otherwise
        """
        # Get features from v6.0.0 structure first, then fallback
        features_data = character_data.get('features', {})
        feats = features_data.get('feats', character_data.get('feats', []))
        class_features = features_data.get('class_features', character_data.get('class_features', []))
        character_info = self.get_character_info(character_data)
        character_level = character_info.get('level', 1)
        
        # Check feats
        if feats:
            return True
        
        # Check class features
        if class_features:
            available_features = [
                feature for feature in class_features
                if isinstance(feature, dict) and feature.get('level_required', 1) <= character_level
            ]
            return len(available_features) > 0
        
        return False