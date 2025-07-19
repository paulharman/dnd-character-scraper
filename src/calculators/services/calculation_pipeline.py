"""
Calculation Pipeline

Manages calculation execution with dependency resolution and orchestration.
Provides a high-level interface for executing coordinators in the correct
order while handling dependencies and error recovery.
"""

from typing import Dict, Any, List, Optional, Set
import logging
from dataclasses import dataclass, field
from datetime import datetime
import time

from ..interfaces.coordination import ICoordinator
from ..utils.performance import monitor_performance
from .interfaces import CalculationContext, CalculationResult, CalculationStatus

logger = logging.getLogger(__name__)


@dataclass
class PipelineStage:
    """Represents a stage in the calculation pipeline."""
    name: str
    coordinator: ICoordinator
    dependencies: List[str] = field(default_factory=list)
    executed: bool = False
    result: Optional[CalculationResult] = None
    execution_time: Optional[float] = None
    error: Optional[str] = None


class CalculationPipeline:
    """
    Manages calculation execution with dependency resolution.
    
    This pipeline orchestrates the execution of multiple coordinators
    in the correct order based on their dependencies. It provides
    error handling, performance monitoring, and result aggregation.
    """
    
    def __init__(self):
        """Initialize the calculation pipeline."""
        self.stages: Dict[str, PipelineStage] = {}
        self.execution_order: List[str] = []
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Pipeline state
        self.is_executing = False
        self.execution_results: Dict[str, Any] = {}
        self.execution_context: Optional[CalculationContext] = None
        
        # Performance tracking
        self.execution_times: List[float] = []
        self.total_executions = 0
        self.successful_executions = 0
    
    def register_stage(self, name: str, coordinator: ICoordinator, dependencies: List[str] = None):
        """
        Register a calculation stage with dependencies.
        
        Args:
            name: Unique name for the stage
            coordinator: Coordinator to execute for this stage
            dependencies: List of stage names this stage depends on
        """
        dependencies = dependencies or []
        
        stage = PipelineStage(
            name=name,
            coordinator=coordinator,
            dependencies=dependencies
        )
        
        self.stages[name] = stage
        self.logger.info(f"Registered pipeline stage: {name} (dependencies: {dependencies})")
        
        # Rebuild execution order
        self._rebuild_execution_order()
    
    def unregister_stage(self, name: str):
        """
        Unregister a calculation stage.
        
        Args:
            name: Name of the stage to unregister
        """
        if name in self.stages:
            del self.stages[name]
            self.logger.info(f"Unregistered pipeline stage: {name}")
            
            # Rebuild execution order
            self._rebuild_execution_order()
    
    def _rebuild_execution_order(self):
        """Rebuild execution order based on dependencies using topological sort."""
        if not self.stages:
            self.execution_order = []
            return
        
        # Topological sort to resolve dependencies
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(stage_name: str):
            if stage_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving stage '{stage_name}'")
            
            if stage_name in visited:
                return
            
            if stage_name not in self.stages:
                # Dependency not found - this will be handled during execution
                return
            
            temp_visited.add(stage_name)
            
            # Visit dependencies first
            stage = self.stages[stage_name]
            for dep in stage.dependencies:
                if dep in self.stages:
                    visit(dep)
            
            temp_visited.remove(stage_name)
            visited.add(stage_name)
            order.append(stage_name)
        
        # Sort stages by coordinator priority first, then apply topological sort
        sorted_stages = sorted(
            self.stages.keys(),
            key=lambda name: self.stages[name].coordinator.priority
        )
        
        for stage_name in sorted_stages:
            if stage_name not in visited:
                visit(stage_name)
        
        self.execution_order = order
        self.logger.debug(f"Pipeline execution order: {self.execution_order}")
    
    @monitor_performance("calculation_pipeline_execute")
    def execute(self, raw_data: Dict[str, Any], context: CalculationContext = None) -> Dict[str, Any]:
        """
        Execute the calculation pipeline.
        
        Args:
            raw_data: Raw character data to process
            context: Optional calculation context
            
        Returns:
            Dictionary containing results from all stages
        """
        if self.is_executing:
            raise RuntimeError("Pipeline is already executing")
        
        start_time = time.time()
        self.is_executing = True
        self.execution_context = context
        self.execution_results = {}
        
        try:
            # Reset stage execution state
            for stage in self.stages.values():
                stage.executed = False
                stage.result = None
                stage.execution_time = None
                stage.error = None
            
            # Validate dependencies before execution
            self._validate_dependencies()
            
            # Execute stages in dependency order
            for stage_name in self.execution_order:
                if stage_name not in self.stages:
                    self.logger.warning(f"Stage '{stage_name}' not found in pipeline")
                    continue
                
                stage = self.stages[stage_name]
                
                # Check if dependencies are satisfied
                if not self._are_dependencies_satisfied(stage):
                    error_msg = f"Dependencies not satisfied for stage '{stage_name}'"
                    self.logger.error(error_msg)
                    stage.error = error_msg
                    continue
                
                # Execute stage
                self._execute_stage(stage, raw_data, context)
            
            # Aggregate results
            self._aggregate_results()
            
            # Update performance metrics
            execution_time = time.time() - start_time
            self.execution_times.append(execution_time)
            self.total_executions += 1
            
            # Check if execution was successful
            failed_stages = [name for name, stage in self.stages.items() if stage.error]
            if not failed_stages:
                self.successful_executions += 1
                self.logger.info(f"Pipeline execution completed successfully in {execution_time:.3f}s")
            else:
                self.logger.error(f"Pipeline execution completed with {len(failed_stages)} failed stages: {failed_stages}")
            
            return self.execution_results
            
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {str(e)}")
            raise
        
        finally:
            self.is_executing = False
            self.execution_context = None
    
    def _execute_stage(self, stage: PipelineStage, raw_data: Dict[str, Any], context: CalculationContext):
        """Execute a single pipeline stage."""
        stage_start_time = time.time()
        
        try:
            self.logger.debug(f"Executing stage: {stage.name}")
            
            # Check if coordinator can handle the data
            if not stage.coordinator.can_coordinate(raw_data):
                self.logger.warning(f"Coordinator for stage '{stage.name}' cannot handle input data")
                stage.error = "Coordinator cannot handle input data"
                return
            
            # Execute coordinator
            result = stage.coordinator.coordinate(raw_data, context or CalculationContext())
            
            # Store result
            stage.result = result
            stage.execution_time = time.time() - stage_start_time
            stage.executed = True
            
            # Handle result
            if result.status == CalculationStatus.COMPLETED:
                self.execution_results[stage.name] = result.data
                
                # Add result to context for dependent stages
                if context and hasattr(context, 'metadata'):
                    if not context.metadata:
                        context.metadata = {}
                    context.metadata[stage.name] = result.data
                
                self.logger.debug(f"Stage '{stage.name}' completed successfully")
            else:
                error_msg = f"Stage '{stage.name}' failed: {'; '.join(result.errors)}"
                stage.error = error_msg
                self.logger.error(error_msg)
            
        except Exception as e:
            stage.error = f"Stage execution error: {str(e)}"
            stage.execution_time = time.time() - stage_start_time
            self.logger.error(f"Error executing stage '{stage.name}': {str(e)}")
    
    def _are_dependencies_satisfied(self, stage: PipelineStage) -> bool:
        """Check if all dependencies for a stage are satisfied."""
        for dep_name in stage.dependencies:
            if dep_name not in self.stages:
                self.logger.error(f"Dependency '{dep_name}' not found for stage '{stage.name}'")
                return False
            
            dep_stage = self.stages[dep_name]
            if not dep_stage.executed or dep_stage.error:
                return False
        
        return True
    
    def _validate_dependencies(self):
        """Validate that all dependencies are resolvable."""
        missing_deps = {}
        
        for stage_name, stage in self.stages.items():
            for dep_name in stage.dependencies:
                if dep_name not in self.stages:
                    if stage_name not in missing_deps:
                        missing_deps[stage_name] = []
                    missing_deps[stage_name].append(dep_name)
        
        if missing_deps:
            error_msg = f"Missing dependencies: {missing_deps}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _aggregate_results(self):
        """Aggregate results from all executed stages."""
        # Results are already being stored in execution_results during stage execution
        # This method can be extended for custom aggregation logic
        
        # Add metadata about pipeline execution
        self.execution_results['_pipeline_metadata'] = {
            'total_stages': len(self.stages),
            'executed_stages': len([s for s in self.stages.values() if s.executed]),
            'failed_stages': len([s for s in self.stages.values() if s.error]),
            'execution_order': self.execution_order,
            'stage_times': {
                name: stage.execution_time 
                for name, stage in self.stages.items() 
                if stage.execution_time is not None
            }
        }
    
    def get_stage_result(self, stage_name: str) -> Optional[CalculationResult]:
        """
        Get the result of a specific stage.
        
        Args:
            stage_name: Name of the stage
            
        Returns:
            Stage result or None if not found/executed
        """
        if stage_name in self.stages:
            return self.stages[stage_name].result
        return None
    
    def get_stage_status(self, stage_name: str) -> Dict[str, Any]:
        """
        Get the status of a specific stage.
        
        Args:
            stage_name: Name of the stage
            
        Returns:
            Dictionary containing stage status information
        """
        if stage_name not in self.stages:
            return {'status': 'not_found'}
        
        stage = self.stages[stage_name]
        return {
            'status': 'completed' if stage.executed and not stage.error else 'failed' if stage.error else 'pending',
            'executed': stage.executed,
            'execution_time': stage.execution_time,
            'error': stage.error,
            'dependencies': stage.dependencies,
            'dependencies_satisfied': self._are_dependencies_satisfied(stage) if not stage.executed else True
        }
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current/last pipeline execution.
        
        Returns:
            Dictionary containing execution summary
        """
        stage_statuses = {}
        for stage_name in self.stages:
            stage_statuses[stage_name] = self.get_stage_status(stage_name)
        
        return {
            'total_stages': len(self.stages),
            'execution_order': self.execution_order,
            'stages': stage_statuses,
            'is_executing': self.is_executing,
            'performance': {
                'total_executions': self.total_executions,
                'successful_executions': self.successful_executions,
                'success_rate': (self.successful_executions / max(1, self.total_executions)) * 100,
                'average_execution_time': sum(self.execution_times) / max(1, len(self.execution_times)) if self.execution_times else 0
            }
        }
    
    def list_stages(self) -> List[str]:
        """
        List all registered stage names.
        
        Returns:
            List of stage names
        """
        return list(self.stages.keys())
    
    def clear_results(self):
        """Clear all execution results and reset stage state."""
        self.execution_results = {}
        for stage in self.stages.values():
            stage.executed = False
            stage.result = None
            stage.execution_time = None
            stage.error = None
        
        self.logger.debug("Pipeline results cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of the pipeline.
        
        Returns:
            Health check results
        """
        health = {
            'status': 'healthy',
            'stages_registered': len(self.stages),
            'execution_order_valid': True,
            'dependencies_satisfied': True,
            'is_executing': self.is_executing
        }
        
        # Check for dependency issues
        try:
            self._validate_dependencies()
        except ValueError as e:
            health['status'] = 'degraded'
            health['dependencies_satisfied'] = False
            health['dependency_errors'] = str(e)
        
        # Check execution order
        try:
            self._rebuild_execution_order()
        except ValueError as e:
            health['status'] = 'degraded'
            health['execution_order_valid'] = False
            health['execution_order_errors'] = str(e)
        
        # Add performance metrics
        if self.total_executions > 0:
            success_rate = (self.successful_executions / self.total_executions) * 100
            if success_rate < 80:  # Less than 80% success rate
                health['status'] = 'degraded'
            
            health['performance'] = {
                'success_rate': success_rate,
                'total_executions': self.total_executions,
                'average_execution_time': sum(self.execution_times) / len(self.execution_times) if self.execution_times else 0
            }
        
        return health