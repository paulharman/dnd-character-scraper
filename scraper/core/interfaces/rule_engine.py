"""
Rule Engine Interface

Defines contract for handling 2014 vs 2024 rule differences.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum


class RuleVersion(Enum):
    """D&D rule version enumeration."""
    RULES_2014 = "2014"
    RULES_2024 = "2024"
    UNKNOWN = "unknown"


class RuleEngineInterface(ABC):
    """Interface for rule version detection and handling."""
    
    @abstractmethod
    def detect_rule_version(self, raw_data: Dict[str, Any]) -> RuleVersion:
        """
        Detect which rule version a character uses.
        
        Args:
            raw_data: Raw character data from D&D Beyond
            
        Returns:
            RuleVersion enum indicating 2014, 2024, or unknown
        """
        pass
    
    @abstractmethod
    def get_spell_progression(self, class_name: str, rule_version: RuleVersion) -> Dict[int, List[int]]:
        """
        Get spell slot progression for a class based on rule version.
        
        Args:
            class_name: Name of the character class
            rule_version: Rule version to use
            
        Returns:
            Dictionary mapping level to spell slots array
        """
        pass
    
    @abstractmethod
    def get_species_terminology(self, rule_version: RuleVersion) -> str:
        """
        Get the correct terminology for species/race based on rule version.
        
        Args:
            rule_version: Rule version to use
            
        Returns:
            "species" for 2024, "race" for 2014
        """
        pass
    
    @abstractmethod
    def apply_rule_specific_logic(self, 
                                 calculation_type: str, 
                                 raw_data: Dict[str, Any], 
                                 rule_version: RuleVersion) -> Dict[str, Any]:
        """
        Apply rule-specific calculation logic.
        
        Args:
            calculation_type: Type of calculation (e.g., "ability_scores", "spells")
            raw_data: Raw character data
            rule_version: Rule version to apply
            
        Returns:
            Modified calculation results based on rule version
        """
        pass