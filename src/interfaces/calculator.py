"""
Calculator Interfaces

Defines contracts for character calculation modules.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.character import Character


class CalculatorInterface(ABC):
    """Base interface for all character calculators."""
    
    @abstractmethod
    def calculate(self, character: "Character", raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform calculation and return results.
        
        Args:
            character: Character data model
            raw_data: Raw D&D Beyond API data
            
        Returns:
            Dictionary with calculated values
        """
        pass
    
    @abstractmethod
    def validate_inputs(self, character: "Character", raw_data: Dict[str, Any]) -> bool:
        """
        Validate that inputs are sufficient for calculation.
        
        Args:
            character: Character data model
            raw_data: Raw D&D Beyond API data
            
        Returns:
            True if inputs are valid
        """
        pass


class AbilityScoreCalculatorInterface(CalculatorInterface):
    """Interface for ability score calculations."""
    
    @abstractmethod
    def calculate_base_scores(self, raw_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate base ability scores from character creation."""
        pass
    
    @abstractmethod
    def calculate_racial_bonuses(self, raw_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate ability score bonuses from species/race."""
        pass
    
    @abstractmethod
    def calculate_feat_bonuses(self, raw_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate ability score bonuses from feats."""
        pass
    
    @abstractmethod
    def calculate_final_scores(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate final ability scores with full breakdown."""
        pass


class HitPointCalculatorInterface(CalculatorInterface):
    """Interface for hit point calculations."""
    
    @abstractmethod
    def calculate_max_hp(self, character: "Character", raw_data: Dict[str, Any]) -> int:
        """Calculate maximum hit points."""
        pass
    
    @abstractmethod
    def get_hp_breakdown(self, character: "Character", raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed hit point calculation breakdown."""
        pass
    
    @abstractmethod
    def calculate_hit_die(self, character: "Character", raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate hit dice information."""
        pass


class ArmorClassCalculatorInterface(CalculatorInterface):
    """Interface for armor class calculations."""
    
    @abstractmethod
    def calculate_ac(self, character: "Character", raw_data: Dict[str, Any]) -> int:
        """Calculate armor class."""
        pass
    
    @abstractmethod
    def get_ac_breakdown(self, character: "Character", raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed AC calculation breakdown."""
        pass
    
    @abstractmethod
    def detect_ac_calculation_method(self, raw_data: Dict[str, Any]) -> str:
        """Detect which AC calculation method is being used."""
        pass


class SpellcastingCalculatorInterface(CalculatorInterface):
    """Interface for spellcasting calculations."""
    
    @abstractmethod
    def calculate_spell_slots(self, character: "Character", raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate spell slots by level."""
        pass
    
    @abstractmethod
    def calculate_spell_save_dc(self, character: "Character", raw_data: Dict[str, Any]) -> Optional[int]:
        """Calculate spell save DC."""
        pass
    
    @abstractmethod
    def calculate_spell_attack_bonus(self, character: "Character", raw_data: Dict[str, Any]) -> Optional[int]:
        """Calculate spell attack bonus."""
        pass
    
    @abstractmethod
    def detect_spellcasting_ability(self, character: "Character", raw_data: Dict[str, Any]) -> Optional[str]:
        """Detect primary spellcasting ability."""
        pass


class ProficiencyCalculatorInterface(CalculatorInterface):
    """Interface for proficiency calculations."""
    
    @abstractmethod
    def calculate_proficiency_bonus(self, character: "Character") -> int:
        """Calculate proficiency bonus based on character level."""
        pass
    
    @abstractmethod
    def get_skill_proficiencies(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get skill proficiencies with sources."""
        pass
    
    @abstractmethod
    def get_saving_throw_proficiencies(self, raw_data: Dict[str, Any]) -> List[str]:
        """Get saving throw proficiencies."""
        pass