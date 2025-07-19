"""
Core calculator interfaces for the DnD character system.

This module defines the fundamental interfaces that all calculators must implement,
providing a consistent API for character data calculation and validation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum

from ..services.interfaces import CalculationContext, CalculationResult


class CalculatorType(Enum):
    """Types of calculators in the system."""
    ABILITY_SCORE = "ability_score"
    ARMOR_CLASS = "armor_class"
    HIT_POINTS = "hit_points"
    SPEED = "speed"
    SPELLCASTING = "spellcasting"
    ENCUMBRANCE = "encumbrance"
    PROFICIENCY = "proficiency"
    ATTACK = "attack"
    WEALTH = "wealth"
    FEATURES = "features"
    CONTAINER = "container"


class CalculationError(Exception):
    """Base exception for calculation errors."""
    
    def __init__(self, message: str, calculator_type: CalculatorType = None, context: Dict[str, Any] = None):
        super().__init__(message)
        self.calculator_type = calculator_type
        self.context = context or {}


class ValidationError(CalculationError):
    """Exception raised when input validation fails."""
    pass


class DependencyError(CalculationError):
    """Exception raised when required dependencies are missing."""
    pass


@dataclass
class CalculationMetrics:
    """Metrics for calculator performance monitoring."""
    execution_time: float
    memory_usage: int
    cache_hits: int
    cache_misses: int
    validation_time: float
    calculation_time: float
    
    def __post_init__(self):
        if self.execution_time < 0:
            raise ValueError("Execution time cannot be negative")


@dataclass
class CalculatorConfig:
    """Configuration for calculator behavior."""
    enable_caching: bool = True
    enable_validation: bool = True
    enable_profiling: bool = False
    rule_version: str = "2014"
    strict_mode: bool = False
    debug_mode: bool = False
    performance_mode: bool = False
    cache_ttl: int = 3600  # 1 hour
    timeout: int = 30  # 30 seconds
    max_retries: int = 3
    
    def __post_init__(self):
        if self.cache_ttl < 0:
            raise ValueError("Cache TTL cannot be negative")
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")


class ICalculator(ABC):
    """
    Core interface for all calculators.
    
    This interface defines the fundamental contract that all calculators
    must implement, providing consistency across the calculation system.
    """
    
    @property
    @abstractmethod
    def calculator_type(self) -> CalculatorType:
        """Get the type of this calculator."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the human-readable name of this calculator."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Get the version of this calculator."""
        pass
    
    @property
    @abstractmethod
    def dependencies(self) -> List[CalculatorType]:
        """Get the list of calculator types this calculator depends on."""
        pass
    
    @abstractmethod
    def calculate(self, character_data: Dict[str, Any], context: CalculationContext) -> CalculationResult:
        """
        Perform the calculation using the provided character data.
        
        Args:
            character_data: Raw character data from D&D Beyond
            context: Calculation context and configuration
            
        Returns:
            CalculationResult with computed data and metadata
            
        Raises:
            CalculationError: If calculation fails
            ValidationError: If input validation fails
            DependencyError: If required dependencies are missing
        """
        pass
    
    @abstractmethod
    def validate_input(self, character_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that the input data is suitable for this calculator.
        
        Args:
            character_data: Character data to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        pass
    
    @abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        """
        Get the schema for data this calculator produces.
        
        Returns:
            JSONSchema describing the output data structure
        """
        pass
    
    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """
        Get the list of required fields in the input data.
        
        Returns:
            List of required field names
        """
        pass
    
    @abstractmethod
    def get_optional_fields(self) -> List[str]:
        """
        Get the list of optional fields in the input data.
        
        Returns:
            List of optional field names
        """
        pass
    
    @abstractmethod
    def supports_rule_version(self, rule_version: str) -> bool:
        """
        Check if this calculator supports the specified rule version.
        
        Args:
            rule_version: Rule version to check (e.g., "2014", "2024")
            
        Returns:
            True if rule version is supported
        """
        pass
    
    @abstractmethod
    def get_cache_key(self, character_data: Dict[str, Any], context: CalculationContext) -> str:
        """
        Generate a cache key for the given inputs.
        
        Args:
            character_data: Character data
            context: Calculation context
            
        Returns:
            Cache key string
        """
        pass
    
    def can_calculate(self, character_data: Dict[str, Any], context: CalculationContext) -> bool:
        """
        Check if this calculator can process the given data.
        
        Args:
            character_data: Character data to check
            context: Calculation context
            
        Returns:
            True if calculator can process this data
        """
        is_valid, _ = self.validate_input(character_data)
        return is_valid and self.supports_rule_version(context.rule_version)
    
    def get_metrics(self) -> Optional[CalculationMetrics]:
        """
        Get performance metrics for this calculator.
        
        Returns:
            CalculationMetrics if profiling is enabled, None otherwise
        """
        return None
    
    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        pass
    
    def configure(self, config: CalculatorConfig) -> None:
        """
        Configure calculator behavior.
        
        Args:
            config: Configuration settings
        """
        pass
    
    def get_configuration(self) -> CalculatorConfig:
        """
        Get current calculator configuration.
        
        Returns:
            Current configuration
        """
        return CalculatorConfig()


class IRuleAwareCalculator(ICalculator):
    """
    Interface for calculators that need rule version awareness.
    
    Extends the base calculator interface with rule-specific functionality.
    """
    
    @abstractmethod
    def set_rule_version(self, rule_version: str) -> None:
        """
        Set the rule version for calculations.
        
        Args:
            rule_version: Rule version to use (e.g., "2014", "2024")
        """
        pass
    
    @abstractmethod
    def get_rule_version(self) -> str:
        """
        Get the current rule version.
        
        Returns:
            Current rule version
        """
        pass
    
    @abstractmethod
    def get_supported_rule_versions(self) -> List[str]:
        """
        Get all supported rule versions.
        
        Returns:
            List of supported rule versions
        """
        pass
    
    @abstractmethod
    def calculate_for_rule_version(self, character_data: Dict[str, Any], 
                                  rule_version: str, context: CalculationContext) -> CalculationResult:
        """
        Calculate using a specific rule version.
        
        Args:
            character_data: Character data
            rule_version: Rule version to use
            context: Calculation context
            
        Returns:
            CalculationResult with rule-specific data
        """
        pass


class ICachedCalculator(ICalculator):
    """
    Interface for calculators that support caching.
    
    Extends the base calculator interface with caching capabilities.
    """
    
    @abstractmethod
    def get_from_cache(self, cache_key: str) -> Optional[CalculationResult]:
        """
        Get calculation result from cache.
        
        Args:
            cache_key: Cache key to look up
            
        Returns:
            Cached result or None if not found
        """
        pass
    
    @abstractmethod
    def store_in_cache(self, cache_key: str, result: CalculationResult, ttl: Optional[int] = None) -> None:
        """
        Store calculation result in cache.
        
        Args:
            cache_key: Cache key
            result: Result to cache
            ttl: Time to live in seconds
        """
        pass
    
    @abstractmethod
    def invalidate_cache(self, cache_key: str) -> None:
        """
        Invalidate cached result.
        
        Args:
            cache_key: Cache key to invalidate
        """
        pass
    
    @abstractmethod
    def clear_cache(self) -> None:
        """Clear all cached results for this calculator."""
        pass
    
    @abstractmethod
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache hit/miss stats
        """
        pass


class IAsyncCalculator(ICalculator):
    """
    Interface for calculators that support asynchronous operations.
    
    Extends the base calculator interface with async capabilities.
    """
    
    @abstractmethod
    async def calculate_async(self, character_data: Dict[str, Any], 
                             context: CalculationContext) -> CalculationResult:
        """
        Perform asynchronous calculation.
        
        Args:
            character_data: Character data
            context: Calculation context
            
        Returns:
            CalculationResult with computed data
        """
        pass
    
    @abstractmethod
    async def validate_input_async(self, character_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Perform asynchronous input validation.
        
        Args:
            character_data: Character data to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        pass
    
    @abstractmethod
    def is_async_supported(self) -> bool:
        """
        Check if this calculator supports async operations.
        
        Returns:
            True if async is supported
        """
        pass


class ICalculatorFactory(ABC):
    """
    Interface for creating calculator instances.
    
    Provides factory methods for creating and configuring calculators.
    """
    
    @abstractmethod
    def create_calculator(self, calculator_type: CalculatorType, 
                         config: CalculatorConfig) -> ICalculator:
        """
        Create a calculator of the specified type.
        
        Args:
            calculator_type: Type of calculator to create
            config: Configuration for the calculator
            
        Returns:
            Configured calculator instance
        """
        pass
    
    @abstractmethod
    def get_available_calculators(self) -> List[CalculatorType]:
        """
        Get list of available calculator types.
        
        Returns:
            List of available calculator types
        """
        pass
    
    @abstractmethod
    def register_calculator(self, calculator_type: CalculatorType, 
                           calculator_class: type) -> None:
        """
        Register a new calculator type.
        
        Args:
            calculator_type: Type of calculator
            calculator_class: Class that implements the calculator
        """
        pass
    
    @abstractmethod
    def create_calculator_chain(self, calculator_types: List[CalculatorType], 
                               config: CalculatorConfig) -> List[ICalculator]:
        """
        Create a chain of calculators with proper dependency order.
        
        Args:
            calculator_types: List of calculator types to create
            config: Configuration for all calculators
            
        Returns:
            List of calculators in dependency order
        """
        pass


class ICalculatorRegistry(ABC):
    """
    Interface for managing calculator registration and discovery.
    
    Provides registry functionality for calculator types and instances.
    """
    
    @abstractmethod
    def register(self, calculator: ICalculator) -> None:
        """
        Register a calculator instance.
        
        Args:
            calculator: Calculator to register
        """
        pass
    
    @abstractmethod
    def unregister(self, calculator_type: CalculatorType) -> None:
        """
        Unregister a calculator type.
        
        Args:
            calculator_type: Type of calculator to unregister
        """
        pass
    
    @abstractmethod
    def get_calculator(self, calculator_type: CalculatorType) -> Optional[ICalculator]:
        """
        Get a calculator by type.
        
        Args:
            calculator_type: Type of calculator to get
            
        Returns:
            Calculator instance or None if not found
        """
        pass
    
    @abstractmethod
    def get_all_calculators(self) -> Dict[CalculatorType, ICalculator]:
        """
        Get all registered calculators.
        
        Returns:
            Dictionary mapping calculator types to instances
        """
        pass
    
    @abstractmethod
    def get_dependencies(self, calculator_type: CalculatorType) -> List[CalculatorType]:
        """
        Get dependencies for a calculator type.
        
        Args:
            calculator_type: Type of calculator
            
        Returns:
            List of dependency types
        """
        pass
    
    @abstractmethod
    def resolve_dependencies(self, calculator_types: List[CalculatorType]) -> List[CalculatorType]:
        """
        Resolve dependencies and return calculators in execution order.
        
        Args:
            calculator_types: List of calculator types to resolve
            
        Returns:
            List of calculator types in dependency order
        """
        pass
    
    @abstractmethod
    def validate_dependencies(self) -> Tuple[bool, List[str]]:
        """
        Validate that all dependencies can be satisfied.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        pass