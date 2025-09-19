"""
Calculator service interfaces for the DnD character system.

This module defines the core interfaces for calculation services that
coordinate between different calculators to produce final character data.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class CalculationPriority(Enum):
    """Priority levels for calculation services."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class CalculationStatus(Enum):
    """Status of calculation operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class CalculationContext:
    """Context information for calculation operations."""
    character_id: Optional[str] = None
    rule_version: str = "2014"
    calculation_mode: str = "standard"
    performance_mode: bool = False
    validation_enabled: bool = True
    debug_enabled: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CalculationResult:
    """Result of a calculation operation."""
    service_name: str
    status: CalculationStatus
    data: Dict[str, Any]
    errors: List[str] = None
    warnings: List[str] = None
    execution_time: float = 0.0
    dependencies_met: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ServiceDependency:
    """Represents a dependency between calculation services."""
    service_name: str
    required_data: List[str]
    optional_data: List[str] = None
    priority: CalculationPriority = CalculationPriority.MEDIUM
    
    def __post_init__(self):
        if self.optional_data is None:
            self.optional_data = []


class ICalculationService(ABC):
    """
    Base interface for all calculation services.
    
    Calculation services coordinate between multiple calculators to produce
    specific aspects of character data (abilities, combat, spells, etc.).
    """
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """Get the unique service name."""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> CalculationPriority:
        """Get the service execution priority."""
        pass
    
    @property
    @abstractmethod
    def dependencies(self) -> List[ServiceDependency]:
        """Get the service dependencies."""
        pass
    
    @abstractmethod
    def calculate(self, character_data: Dict[str, Any], context: CalculationContext) -> CalculationResult:
        """
        Perform the calculation using the provided character data.
        
        Args:
            character_data: Raw character data from D&D Beyond
            context: Calculation context and configuration
            
        Returns:
            CalculationResult with computed data and status
        """
        pass
    
    @abstractmethod
    def validate_input(self, character_data: Dict[str, Any]) -> bool:
        """
        Validate that the input data is suitable for this service.
        
        Args:
            character_data: Character data to validate
            
        Returns:
            True if data is valid for this service
        """
        pass
    
    @abstractmethod
    def can_execute(self, available_data: Dict[str, Any]) -> bool:
        """
        Check if this service can execute with the available data.
        
        Args:
            available_data: Currently available calculated data
            
        Returns:
            True if service can execute with available data
        """
        pass
    
    @abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        """
        Get the schema for data this service produces.
        
        Returns:
            Schema describing the output data structure
        """
        pass


class ICalculationOrchestrator(ABC):
    """
    Interface for orchestrating multiple calculation services.
    
    The orchestrator manages the execution order and data flow between
    different calculation services.
    """
    
    @abstractmethod
    def register_service(self, service: ICalculationService) -> None:
        """
        Register a calculation service with the orchestrator.
        
        Args:
            service: The calculation service to register
        """
        pass
    
    @abstractmethod
    def unregister_service(self, service_name: str) -> None:
        """
        Unregister a calculation service.
        
        Args:
            service_name: Name of the service to unregister
        """
        pass
    
    @abstractmethod
    def calculate_character(self, character_data: Dict[str, Any], context: CalculationContext) -> Dict[str, Any]:
        """
        Calculate complete character data using all registered services.
        
        Args:
            character_data: Raw character data from D&D Beyond
            context: Calculation context and configuration
            
        Returns:
            Complete calculated character data
        """
        pass
    
    @abstractmethod
    def get_execution_order(self) -> List[str]:
        """
        Get the execution order of services based on dependencies.
        
        Returns:
            List of service names in execution order
        """
        pass
    
    @abstractmethod
    def validate_dependencies(self) -> bool:
        """
        Validate that all service dependencies can be satisfied.
        
        Returns:
            True if all dependencies are valid
        """
        pass


class ICalculationCache(ABC):
    """
    Interface for caching calculation results.
    
    Provides caching capabilities to avoid redundant calculations
    and improve performance.
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Get cached calculation result.
        
        Args:
            key: Cache key
            
        Returns:
            Cached result or None if not found
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set cached calculation result.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
        """
        pass
    
    @abstractmethod
    def invalidate(self, key: str) -> None:
        """
        Invalidate cached result.
        
        Args:
            key: Cache key to invalidate
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cached results."""
        pass
    
    @abstractmethod
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache hit/miss stats
        """
        pass


class ICalculationValidator(ABC):
    """
    Interface for validating calculation results.
    
    Provides validation capabilities to ensure calculation results
    are accurate and consistent.
    """
    
    @abstractmethod
    def validate_result(self, result: CalculationResult, context: CalculationContext) -> bool:
        """
        Validate a calculation result.
        
        Args:
            result: The calculation result to validate
            context: Calculation context
            
        Returns:
            True if result is valid
        """
        pass
    
    @abstractmethod
    def validate_character_data(self, character_data: Dict[str, Any], context: CalculationContext) -> bool:
        """
        Validate complete character data.
        
        Args:
            character_data: Complete character data to validate
            context: Calculation context
            
        Returns:
            True if character data is valid
        """
        pass
    
    @abstractmethod
    def get_validation_errors(self) -> List[str]:
        """
        Get validation errors from the last validation.
        
        Returns:
            List of validation error messages
        """
        pass
    
    @abstractmethod
    def get_validation_warnings(self) -> List[str]:
        """
        Get validation warnings from the last validation.
        
        Returns:
            List of validation warning messages
        """
        pass


class ICalculationProfiler(ABC):
    """
    Interface for profiling calculation performance.
    
    Provides performance monitoring and profiling capabilities
    for calculation services.
    """
    
    @abstractmethod
    def start_profiling(self, service_name: str) -> None:
        """
        Start profiling a calculation service.
        
        Args:
            service_name: Name of the service to profile
        """
        pass
    
    @abstractmethod
    def stop_profiling(self, service_name: str) -> Dict[str, Any]:
        """
        Stop profiling and get performance metrics.
        
        Args:
            service_name: Name of the service being profiled
            
        Returns:
            Performance metrics for the service
        """
        pass
    
    @abstractmethod
    def get_profile_report(self) -> Dict[str, Any]:
        """
        Get a comprehensive profiling report.
        
        Returns:
            Profiling report with performance metrics
        """
        pass
    
    @abstractmethod
    def reset_profiles(self) -> None:
        """Reset all profiling data."""
        pass


class ICalculationEventHandler(ABC):
    """
    Interface for handling calculation events.
    
    Provides event handling capabilities for calculation lifecycle events.
    """
    
    @abstractmethod
    def on_calculation_start(self, service_name: str, context: CalculationContext) -> None:
        """
        Handle calculation start event.
        
        Args:
            service_name: Name of the service starting calculation
            context: Calculation context
        """
        pass
    
    @abstractmethod
    def on_calculation_complete(self, service_name: str, result: CalculationResult) -> None:
        """
        Handle calculation completion event.
        
        Args:
            service_name: Name of the service that completed
            result: Calculation result
        """
        pass
    
    @abstractmethod
    def on_calculation_error(self, service_name: str, error: Exception, context: CalculationContext) -> None:
        """
        Handle calculation error event.
        
        Args:
            service_name: Name of the service that errored
            error: The error that occurred
            context: Calculation context
        """
        pass
    
    @abstractmethod
    def on_dependency_missing(self, service_name: str, missing_dependency: str, context: CalculationContext) -> None:
        """
        Handle missing dependency event.
        
        Args:
            service_name: Name of the service with missing dependency
            missing_dependency: Name of the missing dependency
            context: Calculation context
        """
        pass


class ICalculationServiceFactory(ABC):
    """
    Interface for creating calculation services.
    
    Provides factory methods for creating and configuring
    calculation services with proper dependencies.
    """
    
    @abstractmethod
    def create_service(self, service_type: str, config: Dict[str, Any]) -> ICalculationService:
        """
        Create a calculation service of the specified type.
        
        Args:
            service_type: Type of service to create
            config: Configuration for the service
            
        Returns:
            Configured calculation service
        """
        pass
    
    @abstractmethod
    def get_available_services(self) -> List[str]:
        """
        Get list of available service types.
        
        Returns:
            List of available service type names
        """
        pass
    
    @abstractmethod
    def register_service_type(self, service_type: str, service_class: type) -> None:
        """
        Register a new service type.
        
        Args:
            service_type: Name of the service type
            service_class: Class that implements the service
        """
        pass
    
    @abstractmethod
    def create_orchestrator(self, services: List[ICalculationService], config: Dict[str, Any]) -> ICalculationOrchestrator:
        """
        Create a calculation orchestrator with the given services.
        
        Args:
            services: List of calculation services
            config: Configuration for the orchestrator
            
        Returns:
            Configured calculation orchestrator
        """
        pass