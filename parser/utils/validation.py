"""
Validation utilities for character data parsing.

This module provides validation services for character data structures
to ensure data integrity and proper formatting.
"""

from typing import Dict, Any, List, Optional, Union
import logging

# Import interface using absolute import
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.interfaces import IValidationService


class ValidationService(IValidationService):
    """
    Validation service for character data structures.
    
    Provides comprehensive validation for character data to ensure
    proper structure and required fields are present.
    """
    
    def __init__(self):
        """Initialize the validation service."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.validation_errors: List[str] = []
        self.current_context = ""
    
    def validate_character_data(self, character_data: Dict[str, Any]) -> bool:
        """
        Validate complete character data structure.
        
        Args:
            character_data: Character data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        self.validation_errors.clear()
        self.current_context = "character_data"
        
        if not isinstance(character_data, dict):
            self._add_error("Character data must be a dictionary")
            return False
        
        # Validate required top-level sections (v6.0.0 format)
        # Check for either basic_info (v6.0.0 actual format) or character_info (legacy)
        if 'basic_info' not in character_data and 'character_info' not in character_data:
            self._add_error("Missing required section: basic_info or character_info")
            return False
        
        # Validate sections - use basic_info if available, fallback to character_info
        character_info_data = character_data.get('basic_info') or character_data.get('character_info', {})
        validation_results = [
            self._validate_character_info(character_info_data),
            self._validate_optional_sections(character_data)
        ]
        
        return all(validation_results)
    
    def validate_section(self, section_name: str, section_data: Any) -> bool:
        """
        Validate a specific section of character data.
        
        Args:
            section_name: Name of the section to validate
            section_data: Data for the section
            
        Returns:
            True if section is valid, False otherwise
        """
        self.validation_errors.clear()
        self.current_context = section_name
        
        validation_map = {
            'basic_info': self._validate_character_info,  # v6.0.0 actual format
            'character_info': self._validate_character_info,  # legacy format
            'spells': self._validate_spells_section,
            'inventory': self._validate_inventory_section,
            'containers': self._validate_containers_section,
            'feats': self._validate_feats_section,
            'classes': self._validate_classes_section,
            'species': self._validate_species_section,
            'background': self._validate_background_section
        }
        
        validator = validation_map.get(section_name)
        if validator:
            return validator(section_data)
        else:
            self._add_error(f"Unknown section: {section_name}")
            return False
    
    def get_validation_errors(self) -> List[str]:
        """
        Get list of validation errors from last validation.
        
        Returns:
            List of error messages
        """
        return self.validation_errors.copy()
    
    def _add_error(self, error_message: str) -> None:
        """Add an error message to the validation errors list."""
        full_message = f"[{self.current_context}] {error_message}"
        self.validation_errors.append(full_message)
        self.logger.error(full_message)
    
    def _validate_section_exists(self, data: Dict[str, Any], section_name: str) -> bool:
        """Check if a required section exists in the data."""
        if section_name not in data:
            self._add_error(f"Missing required section: {section_name}")
            return False
        return True
    
    def _validate_basic_info(self, basic_info: Dict[str, Any]) -> bool:
        """Validate basic_info section."""
        if not isinstance(basic_info, dict):
            self._add_error("basic_info must be a dictionary")
            return False
        
        # Required fields in basic_info
        required_fields = ['name', 'level']
        for field in required_fields:
            if field not in basic_info:
                self._add_error(f"Missing required field in basic_info: {field}")
                return False
        
        # Validate field types
        if not isinstance(basic_info.get('name'), str):
            self._add_error("basic_info.name must be a string")
            return False
        
        if not isinstance(basic_info.get('level'), int):
            self._add_error("basic_info.level must be an integer")
            return False
        
        if basic_info.get('level', 0) < 1:
            self._add_error("basic_info.level must be at least 1")
            return False
        
        # Validate optional classes field
        if 'classes' in basic_info:
            if not isinstance(basic_info['classes'], list):
                self._add_error("basic_info.classes must be a list")
                return False
            
            for i, cls in enumerate(basic_info['classes']):
                if not self._validate_class_entry(cls, f"basic_info.classes[{i}]"):
                    return False
        
        return True
    
    def _validate_character_info(self, character_info: Dict[str, Any]) -> bool:
        """Validate character_info/basic_info section (v6.0.0 format)."""
        if not isinstance(character_info, dict):
            self._add_error("character info must be a dictionary")
            return False
        
        # Required fields in character info
        required_fields = ['name', 'level']
        for field in required_fields:
            if field not in character_info:
                self._add_error(f"Missing required field: {field}")
                return False
        
        # Validate field types
        if not isinstance(character_info.get('name'), str):
            self._add_error("name must be a string")
            return False
        
        if not isinstance(character_info.get('level'), int):
            self._add_error("level must be an integer")
            return False
        
        if character_info.get('level', 0) < 1:
            self._add_error("level must be at least 1")
            return False
        
        # Validate optional classes field
        if 'classes' in character_info:
            if not isinstance(character_info['classes'], list):
                self._add_error("classes must be a list")
                return False
            
            for i, cls in enumerate(character_info['classes']):
                if not self._validate_class_entry(cls, f"classes[{i}]"):
                    return False
        
        return True
    
    def _validate_meta_info(self, meta_info: Dict[str, Any]) -> bool:
        """Validate meta section."""
        if not isinstance(meta_info, dict):
            self._add_error("meta must be a dictionary")
            return False
        
        # Optional but important fields
        if 'character_id' in meta_info:
            if not isinstance(meta_info['character_id'], (str, int)):
                self._add_error("meta.character_id must be a string or integer")
                return False
        
        if 'rule_version' in meta_info:
            if not isinstance(meta_info['rule_version'], str):
                self._add_error("meta.rule_version must be a string")
                return False
        
        return True
    
    def _validate_optional_sections(self, character_data: Dict[str, Any]) -> bool:
        """Validate optional sections if they exist."""
        optional_sections = {
            'spells': self._validate_spells_section,
            'inventory': self._validate_inventory_section,
            'containers': self._validate_containers_section,
            'feats': self._validate_feats_section,
            'species': self._validate_species_section,
            'background': self._validate_background_section
        }
        
        for section_name, validator in optional_sections.items():
            if section_name in character_data:
                if not validator(character_data[section_name]):
                    return False
        
        return True
    
    def _validate_spells_section(self, spells_data: Dict[str, Any]) -> bool:
        """Validate spells section."""
        if not isinstance(spells_data, dict):
            self._add_error("spells must be a dictionary")
            return False
        
        # Validate spell levels
        for level, spell_list in spells_data.items():
            if not isinstance(spell_list, list):
                self._add_error(f"spells.{level} must be a list")
                return False
            
            for i, spell in enumerate(spell_list):
                if not isinstance(spell, dict):
                    self._add_error(f"spells.{level}[{i}] must be a dictionary")
                    return False
                
                if 'name' not in spell:
                    self._add_error(f"spells.{level}[{i}] must have a 'name' field")
                    return False
        
        return True
    
    def _validate_inventory_section(self, inventory_data: List[Dict[str, Any]]) -> bool:
        """Validate inventory section."""
        if not isinstance(inventory_data, list):
            self._add_error("inventory must be a list")
            return False
        
        for i, item in enumerate(inventory_data):
            if not isinstance(item, dict):
                self._add_error(f"inventory[{i}] must be a dictionary")
                return False
            
            if 'name' not in item:
                self._add_error(f"inventory[{i}] must have a 'name' field")
                return False
        
        return True
    
    def _validate_containers_section(self, containers_data: Dict[str, Any]) -> bool:
        """Validate containers section."""
        if not isinstance(containers_data, dict):
            self._add_error("containers must be a dictionary")
            return False
        
        # Validate inventory_items if present
        if 'inventory_items' in containers_data:
            if not isinstance(containers_data['inventory_items'], list):
                self._add_error("containers.inventory_items must be a list")
                return False
        
        # Validate containers mapping if present
        if 'containers' in containers_data:
            containers_map = containers_data['containers']
            if not isinstance(containers_map, dict):
                self._add_error("containers.containers must be a dictionary")
                return False
            
            for container_id, container_info in containers_map.items():
                if not isinstance(container_info, dict):
                    self._add_error(f"containers.containers[{container_id}] must be a dictionary")
                    return False
                
                if 'name' not in container_info:
                    self._add_error(f"containers.containers[{container_id}] must have a 'name' field")
                    return False
        
        return True
    
    def _validate_feats_section(self, feats_data: List[Dict[str, Any]]) -> bool:
        """Validate feats section."""
        if not isinstance(feats_data, list):
            self._add_error("feats must be a list")
            return False
        
        for i, feat in enumerate(feats_data):
            if not isinstance(feat, dict):
                self._add_error(f"feats[{i}] must be a dictionary")
                return False
            
            if 'name' not in feat:
                self._add_error(f"feats[{i}] must have a 'name' field")
                return False
        
        return True
    
    def _validate_classes_section(self, classes_data: List[Dict[str, Any]]) -> bool:
        """Validate classes section."""
        if not isinstance(classes_data, list):
            self._add_error("classes must be a list")
            return False
        
        for i, cls in enumerate(classes_data):
            if not self._validate_class_entry(cls, f"classes[{i}]"):
                return False
        
        return True
    
    def _validate_class_entry(self, cls: Dict[str, Any], context: str) -> bool:
        """Validate a single class entry."""
        if not isinstance(cls, dict):
            self._add_error(f"{context} must be a dictionary")
            return False
        
        required_fields = ['name', 'level']
        for field in required_fields:
            if field not in cls:
                self._add_error(f"{context} must have a '{field}' field")
                return False
        
        if not isinstance(cls.get('name'), str):
            self._add_error(f"{context}.name must be a string")
            return False
        
        if not isinstance(cls.get('level'), int):
            self._add_error(f"{context}.level must be an integer")
            return False
        
        if cls.get('level', 0) < 1:
            self._add_error(f"{context}.level must be at least 1")
            return False
        
        return True
    
    def _validate_species_section(self, species_data: Dict[str, Any]) -> bool:
        """Validate species section."""
        if not isinstance(species_data, dict):
            self._add_error("species must be a dictionary")
            return False
        
        if 'name' not in species_data:
            self._add_error("species must have a 'name' field")
            return False
        
        if not isinstance(species_data.get('name'), str):
            self._add_error("species.name must be a string")
            return False
        
        return True
    
    def _validate_background_section(self, background_data: Dict[str, Any]) -> bool:
        """Validate background section."""
        if not isinstance(background_data, dict):
            self._add_error("background must be a dictionary")
            return False
        
        if 'name' not in background_data:
            self._add_error("background must have a 'name' field")
            return False
        
        if not isinstance(background_data.get('name'), str):
            self._add_error("background.name must be a string")
            return False
        
        return True