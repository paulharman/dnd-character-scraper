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
            self.logger.debug("Parser:   Character level not found in character_info")
        
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
        
        # Sort feats by name for consistent display
        sorted_feats = sorted(feats, key=lambda f: f.get('name', '')) if feats else []
        
        for feat in sorted_feats:
            if isinstance(feat, dict):
                name = feat.get('name', 'Unknown Feat')
                description = feat.get('description', '')
                
                # Determine feat source and type
                feat_source = self._determine_feat_source(feat)
                
                section += f"\n>### {name} ({feat_source})\n>\n"
                
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
        
        # Sort class features by type, then name, then level for better grouping
        def get_feature_type_priority(feature):
            # Prioritize subclass features after class features
            is_subclass = feature.get('is_subclass_feature', False)
            return 1 if is_subclass else 0
        
        sorted_features = sorted(class_features, key=lambda f: (
            get_feature_type_priority(f),  # Class features first, then subclass
            f.get('name', ''),             # Then by name (groups progressions)  
            f.get('level_required', 1)     # Then by level (shows progression order)
        )) if class_features else []
        
        for feature in sorted_features:
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
                
                section += f"\n>### {name}\n"
                
                # Add source and level information
                feature_type = "Subclass" if is_subclass else "Class"
                source_name = feature.get('source_name', 'Unknown')
                section += f"> *{feature_type} Feature (Level {level_required})*\n"
                if source_name and source_name != 'Unknown':
                    section += f"> *Source: {source_name}*\n"
                section += ">\n"
                
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
                class_name = resource.get('class', 'Unknown Class')  # Fixed: use 'class' not 'class_name'
                if class_name not in resources_by_class:
                    resources_by_class[class_name] = []
                resources_by_class[class_name].append(resource)
        
        # Format resources by class
        for class_name, class_resource_list in resources_by_class.items():
            section += f"> **{class_name}:**\n"
            
            for resource in class_resource_list:
                resource_name = resource.get('name', 'Unknown Resource')  # Fixed: use 'name' not 'resource_name'
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
    
    def _determine_feat_source(self, feat: Dict[str, Any]) -> str:
        """
        Determine the source description for a feat.
        
        Args:
            feat: Feat dictionary
            
        Returns:
            Source description string
        """
        # Check for feat type from prerequisites or description
        description = feat.get('description', '')
        
        # Check for Origin Feat
        if 'Origin Feat' in description:
            return 'Origin Feat'
        
        # Check for General Feat
        if 'General Feat' in description:
            return 'General Feat'
        
        # Check for Fighting Style Feat
        if 'Fighting Style Feat' in description:
            return 'Fighting Style Feat'
        
        # Check for Epic Boon
        if 'Epic Boon' in description:
            return 'Epic Boon'
        
        # Default to just "Feat"
        return 'Feat'