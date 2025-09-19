"""
Calculation Service

High-level service for orchestrating character calculations through coordinators.
This service manages the overall calculation workflow, dependency resolution,
and result aggregation for character data processing.
"""

from typing import Dict, Any, List, Optional, Set
import logging
from dataclasses import dataclass, field
from datetime import datetime
import time

from ..interfaces.coordination import ICoordinator
from ..coordinators.character_info import CharacterInfoCoordinator
from ..coordinators.abilities import AbilitiesCoordinator
from ..coordinators.combat import CombatCoordinator
from ..coordinators.spellcasting import SpellcastingCoordinator
from ..coordinators.features import FeaturesCoordinator
from ..coordinators.equipment import EquipmentCoordinator
from ..utils.performance import monitor_performance
from ..utils.validation import validate_character_data
from .interfaces import CalculationContext, CalculationResult, CalculationStatus

logger = logging.getLogger(__name__)


@dataclass
class CalculationSession:
    """Represents a calculation session with all coordinators."""
    session_id: str
    character_id: str
    rule_version: str
    coordinators: List[ICoordinator] = field(default_factory=list)
    context: Optional[CalculationContext] = None
    results: Dict[str, CalculationResult] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    status: CalculationStatus = CalculationStatus.PENDING
    
    def mark_started(self):
        """Mark session as started."""
        self.start_time = datetime.now()
        self.status = CalculationStatus.IN_PROGRESS
    
    def mark_completed(self):
        """Mark session as completed."""
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
        self.status = CalculationStatus.COMPLETED
    
    def mark_failed(self):
        """Mark session as failed."""
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
        self.status = CalculationStatus.FAILED


class CalculationService:
    """
    Service for orchestrating character calculations through coordinators.
    
    This service manages the overall calculation workflow including:
    - Coordinator registration and dependency resolution
    - Input validation and preprocessing
    - Calculation orchestration and result aggregation
    - Performance monitoring and error handling
    - Context management and result caching
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize the calculation service.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Coordinator registry
        self.coordinators: Dict[str, ICoordinator] = {}
        self.coordinator_dependencies: Dict[str, Set[str]] = {}
        
        # Session management
        self.active_sessions: Dict[str, CalculationSession] = {}
        
        # Performance tracking
        self.performance_metrics = {
            'calculation_times': [],
            'coordinator_times': {},
            'error_counts': 0,
            'success_counts': 0
        }
        
        # Register default coordinators
        self._register_default_coordinators()
    
    def _register_default_coordinators(self):
        """Register default coordinators."""
        default_coordinators = [
            CharacterInfoCoordinator(),
            AbilitiesCoordinator(),
            CombatCoordinator(),
            SpellcastingCoordinator(),
            FeaturesCoordinator(),
            EquipmentCoordinator()
        ]
        
        for coordinator in default_coordinators:
            self.register_coordinator(coordinator)
    
    def register_coordinator(self, coordinator: ICoordinator):
        """
        Register a coordinator with the service.
        
        Args:
            coordinator: The coordinator to register
        """
        name = coordinator.coordinator_name
        self.coordinators[name] = coordinator
        self.coordinator_dependencies[name] = set(coordinator.dependencies)
        
        # Initialize performance tracking for this coordinator
        if name not in self.performance_metrics['coordinator_times']:
            self.performance_metrics['coordinator_times'][name] = []
        
        self.logger.info(f"Registered coordinator: {name} (priority: {coordinator.priority})")
    
    def unregister_coordinator(self, coordinator_name: str):
        """
        Unregister a coordinator from the service.
        
        Args:
            coordinator_name: Name of the coordinator to unregister
        """
        if coordinator_name in self.coordinators:
            del self.coordinators[coordinator_name]
            del self.coordinator_dependencies[coordinator_name]
            self.logger.info(f"Unregistered coordinator: {coordinator_name}")
    
    def get_coordinator(self, coordinator_name: str) -> Optional[ICoordinator]:
        """
        Get a registered coordinator by name.
        
        Args:
            coordinator_name: Name of the coordinator
            
        Returns:
            The coordinator instance or None if not found
        """
        return self.coordinators.get(coordinator_name)
    
    def list_coordinators(self) -> List[str]:
        """
        List all registered coordinator names.
        
        Returns:
            List of coordinator names
        """
        return list(self.coordinators.keys())
    
    @monitor_performance("calculation_service_calculate")
    def calculate(self, raw_data: Dict[str, Any], context: CalculationContext) -> CalculationResult:
        """
        Calculate character data using all registered coordinators.
        
        Args:
            raw_data: Raw character data from D&D Beyond
            context: Calculation context
            
        Returns:
            Aggregated calculation result
        """
        session_id = f"{context.character_id}_{int(time.time())}"
        
        # Create calculation session
        session = CalculationSession(
            session_id=session_id,
            character_id=context.character_id,
            rule_version=context.rule_version,
            coordinators=list(self.coordinators.values()),
            context=context
        )
        
        self.active_sessions[session_id] = session
        session.mark_started()
        
        try:
            # Basic input validation - only check for critical issues
            if not isinstance(raw_data, dict):
                session.mark_failed()
                return CalculationResult(
                    service_name="calculation_service",
                    status=CalculationStatus.FAILED,
                    data={},
                    errors=["Input data must be a dictionary"]
                )
            
            # Check for basic required fields that would prevent any coordinator from working
            if not raw_data.get('id') and not raw_data.get('name'):
                session.mark_failed()
                return CalculationResult(
                    service_name="calculation_service",
                    status=CalculationStatus.FAILED,
                    data={},
                    errors=["Input data must contain either character ID or name"]
                )
            
            # Calculate execution order based on dependencies
            execution_order = self._calculate_execution_order()
            
            # Execute coordinators in dependency order
            aggregated_data = {}
            all_warnings = []
            
            for coordinator_name in execution_order:
                coordinator = self.coordinators[coordinator_name]
                
                # Check if coordinator can handle this data
                if not coordinator.can_coordinate(raw_data):
                    self.logger.warning(f"Coordinator {coordinator_name} cannot handle input data")
                    continue
                
                # Execute coordinator
                start_time = time.time()
                result = coordinator.coordinate(raw_data, context)
                duration = time.time() - start_time
                
                # Track performance
                self.performance_metrics['coordinator_times'][coordinator_name].append(duration)
                
                # Store result
                session.results[coordinator_name] = result
                
                # Handle result
                if result.status == CalculationStatus.COMPLETED:
                    aggregated_data[coordinator_name] = result.data
                    all_warnings.extend(result.warnings)
                    
                    # Add result to context for dependent coordinators
                    if not hasattr(context, 'metadata'):
                        context.metadata = {}
                    context.metadata[coordinator_name] = result.data
                    
                    self.logger.info(f"Coordinator {coordinator_name} completed successfully")
                else:
                    self.logger.error(f"Coordinator {coordinator_name} failed: {result.errors}")
                    session.mark_failed()
                    return CalculationResult(
                        service_name="calculation_service",
                        status=CalculationStatus.FAILED,
                        data=aggregated_data,
                        errors=[f"Coordinator {coordinator_name} failed: {'; '.join(result.errors)}"]
                    )
            
            # Create final result
            final_result = CalculationResult(
                service_name="calculation_service",
                status=CalculationStatus.COMPLETED,
                data=aggregated_data,
                errors=[],
                warnings=all_warnings
            )
            
            session.mark_completed()
            self.performance_metrics['success_counts'] += 1
            
            self.logger.info(f"Calculation completed successfully for character {context.character_id}")
            return final_result
            
        except Exception as e:
            session.mark_failed()
            self.performance_metrics['error_counts'] += 1
            self.logger.error(f"Calculation failed for character {context.character_id}: {str(e)}")
            
            return CalculationResult(
                service_name="calculation_service",
                status=CalculationStatus.FAILED,
                data={},
                errors=[f"Calculation service error: {str(e)}"]
            )
        
        finally:
            # Clean up session
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
    
    def _calculate_execution_order(self) -> List[str]:
        """
        Calculate the execution order for coordinators based on dependencies.
        
        Returns:
            List of coordinator names in execution order
        """
        # Topological sort to resolve dependencies
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(coordinator_name: str):
            if coordinator_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {coordinator_name}")
            
            if coordinator_name in visited:
                return
            
            temp_visited.add(coordinator_name)
            
            # Visit dependencies first
            for dep in self.coordinator_dependencies.get(coordinator_name, set()):
                if dep in self.coordinators:
                    visit(dep)
            
            temp_visited.remove(coordinator_name)
            visited.add(coordinator_name)
            order.append(coordinator_name)
        
        # Sort coordinators by priority first, then apply topological sort
        sorted_coordinators = sorted(
            self.coordinators.keys(),
            key=lambda name: self.coordinators[name].priority
        )
        
        for coordinator_name in sorted_coordinators:
            if coordinator_name not in visited:
                visit(coordinator_name)
        
        return order
    
    def validate_dependencies(self) -> Dict[str, List[str]]:
        """
        Validate that all coordinator dependencies are satisfied.
        
        Returns:
            Dictionary of unresolved dependencies per coordinator
        """
        unresolved = {}
        
        for coordinator_name, dependencies in self.coordinator_dependencies.items():
            missing_deps = []
            
            for dep in dependencies:
                if dep not in self.coordinators:
                    missing_deps.append(dep)
            
            if missing_deps:
                unresolved[coordinator_name] = missing_deps
        
        return unresolved
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the calculation service.
        
        Returns:
            Dictionary of performance metrics
        """
        metrics = {
            'total_calculations': self.performance_metrics['success_counts'] + self.performance_metrics['error_counts'],
            'success_rate': 0.0,
            'error_rate': 0.0,
            'average_calculation_time': 0.0,
            'coordinator_performance': {}
        }
        
        total_calcs = metrics['total_calculations']
        if total_calcs > 0:
            metrics['success_rate'] = (self.performance_metrics['success_counts'] / total_calcs) * 100
            metrics['error_rate'] = (self.performance_metrics['error_counts'] / total_calcs) * 100
        
        # Calculate average times for each coordinator
        for coordinator_name, times in self.performance_metrics['coordinator_times'].items():
            if times:
                metrics['coordinator_performance'][coordinator_name] = {
                    'average_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'execution_count': len(times)
                }
        
        return metrics
    
    def get_active_sessions(self) -> Dict[str, CalculationSession]:
        """
        Get all active calculation sessions.
        
        Returns:
            Dictionary of active sessions
        """
        return self.active_sessions.copy()
    
    def get_session_history(self, character_id: str) -> List[CalculationSession]:
        """
        Get calculation session history for a character.
        
        Args:
            character_id: Character ID to get history for
            
        Returns:
            List of calculation sessions
        """
        # This would typically be implemented with persistent storage
        # For now, return empty list since we don't persist sessions
        return []
    
    def clear_performance_metrics(self):
        """Clear all performance metrics."""
        self.performance_metrics = {
            'calculation_times': [],
            'coordinator_times': {name: [] for name in self.coordinators.keys()},
            'error_counts': 0,
            'success_counts': 0
        }
        self.logger.info("Performance metrics cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the calculation service.
        
        Returns:
            Health check results
        """
        health = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'coordinators': {
                'registered': len(self.coordinators),
                'active': len(self.active_sessions),
                'dependencies_satisfied': len(self.validate_dependencies()) == 0
            },
            'performance': {
                'success_rate': 0.0,
                'error_rate': 0.0,
                'average_response_time': 0.0
            }
        }
        
        # Calculate performance metrics
        metrics = self.get_performance_metrics()
        health['performance'].update({
            'success_rate': metrics['success_rate'],
            'error_rate': metrics['error_rate']
        })
        
        # Check for issues
        issues = []
        unresolved_deps = self.validate_dependencies()
        if unresolved_deps:
            issues.append(f"Unresolved dependencies: {unresolved_deps}")
            health['status'] = 'degraded'
        
        if metrics['error_rate'] > 10:  # More than 10% error rate
            issues.append(f"High error rate: {metrics['error_rate']:.1f}%")
            health['status'] = 'degraded'
        
        if len(self.active_sessions) > 100:  # Too many active sessions
            issues.append(f"High number of active sessions: {len(self.active_sessions)}")
            health['status'] = 'degraded'
        
        health['issues'] = issues
        
        return health