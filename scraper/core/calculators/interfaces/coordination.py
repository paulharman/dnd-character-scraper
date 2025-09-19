"""
Coordination interfaces for the calculator system.

This module defines the core interfaces for coordinators that handle
specific calculation domains with dependency management.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ..services.interfaces import CalculationContext, CalculationResult


class ICoordinator(ABC):
    """Base interface for all coordinators."""
    
    @property
    @abstractmethod
    def coordinator_name(self) -> str:
        """Get the coordinator name."""
        pass
    
    @property
    @abstractmethod
    def dependencies(self) -> List[str]:
        """Get the list of dependencies."""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """Get the execution priority (lower = higher priority)."""
        pass
    
    @abstractmethod
    def coordinate(self, raw_data: Dict[str, Any], context: CalculationContext) -> CalculationResult:
        """
        Coordinate calculations for this domain.
        
        Args:
            raw_data: Raw character data from D&D Beyond
            context: Calculation context with shared data
            
        Returns:
            CalculationResult with calculated data
        """
        pass
    
    @abstractmethod
    def validate_input(self, raw_data: Dict[str, Any]) -> bool:
        """
        Validate that the input data is suitable for this coordinator.
        
        Args:
            raw_data: Raw character data to validate
            
        Returns:
            True if data is valid for this coordinator
        """
        pass
    
    def can_coordinate(self, raw_data: Dict[str, Any]) -> bool:
        """
        Check if this coordinator can handle the given data.
        
        Args:
            raw_data: Raw character data
            
        Returns:
            True if coordinator can handle this data
        """
        return self.validate_input(raw_data)
    
    def get_output_schema(self) -> Dict[str, Any]:
        """
        Get the schema for data this coordinator produces.
        
        Returns:
            Schema describing the output data structure
        """
        return {"type": "object"}


class IRuleAwareCoordinator(ICoordinator):
    """Interface for coordinators that need rule version awareness."""
    
    @abstractmethod
    def set_rule_version(self, rule_version: str) -> None:
        """Set the rule version for calculations."""
        pass
    
    @abstractmethod
    def get_rule_version(self) -> str:
        """Get the current rule version."""
        pass


class ICalculationContext(ABC):
    """Interface for calculation context management."""
    
    @abstractmethod
    def get_shared_data(self, key: str) -> Any:
        """Get shared data by key."""
        pass
    
    @abstractmethod
    def set_shared_data(self, key: str, value: Any) -> None:
        """Set shared data by key."""
        pass
    
    @abstractmethod
    def has_shared_data(self, key: str) -> bool:
        """Check if shared data exists for key."""
        pass
    
    @abstractmethod
    def clear_shared_data(self) -> None:
        """Clear all shared data."""
        pass