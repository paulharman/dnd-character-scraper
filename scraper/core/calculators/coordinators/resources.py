"""
Resources Coordinator

Coordinates the calculation of class-specific resources like Ki points, Sorcery points,
Bardic Inspiration, Rage uses, and other class features with usage tracking.
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass

from ..interfaces.coordination import ICoordinator
from ..utils.performance import monitor_performance
from ..services.interfaces import CalculationContext, CalculationResult, CalculationStatus
from ..class_resource_calculator import ClassResourceCalculator, RestType

logger = logging.getLogger(__name__)


@dataclass
class ResourcesData:
    """Data class for resources calculation results."""
    class_resources: List[Dict[str, Any]]
    resources_by_class: Dict[str, List[Dict[str, Any]]]
    resources_by_rest_type: Dict[str, List[Dict[str, Any]]]
    total_resources: int
    depleted_resources: List[str]
    metadata: Dict[str, Any]


class ResourcesCoordinator(ICoordinator):
    """
    Coordinates class resource calculations with comprehensive tracking.
    
    This coordinator handles:
    - Class-specific resources (Ki, Sorcery Points, Bardic Inspiration, etc.)
    - Usage tracking and depletion detection
    - Rest type categorization (short rest vs long rest resources)
    - Multiclass resource interactions
    - Resource restoration simulation
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize the resources coordinator.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        self.resource_calculator = ClassResourceCalculator(config_manager)
        
        # Coordinator metadata
        self.name = "resources"
        self._priority = 35  # After combat (30) but before equipment (40)
        self._dependencies = ["character_info", "abilities"]
        self.version = "1.0.0"
        
        self.logger.debug(f"Initialized {self.__class__.__name__}")
    
    @property
    def coordinator_name(self) -> str:
        """Get the coordinator name."""
        return self.name
    
    @property
    def dependencies(self) -> List[str]:
        """Get the list of dependencies."""
        return self._dependencies.copy()
    
    @property
    def priority(self) -> int:
        """Get the execution priority (lower = higher priority)."""
        return self._priority
    
    @monitor_performance("resources_coordinate")
    def coordinate(self, raw_data: Dict[str, Any], context: CalculationContext) -> CalculationResult:
        """
        Coordinate the calculation of class resources.
        
        Args:
            raw_data: Raw character data from D&D Beyond
            context: Calculation context with character data and metadata
            
        Returns:
            CalculationResult with resource data
        """
        try:
            # Extract character id and classes from raw data
            character_id = raw_data.get('id', 'unknown')
            
            self.logger.info(f"Calculating class resources for character {character_id}")
            
            # Transform raw data to format expected by resource calculator
            character_data = self._transform_raw_data_for_calculator(raw_data, context)
            
            # Calculate class resources using the resource calculator
            result = self.resource_calculator.calculate(character_data)
            class_resources_data = result.get('class_resources', [])
            
            # Transform ClassResource objects to dictionary format for compatibility
            class_resources = []
            for resource in class_resources_data:
                resource_dict = {
                    'name': resource.resource_name,
                    'class': resource.class_name,
                    'maximum': resource.maximum,
                    'current': resource.current,
                    'used': resource.used,
                    'remaining': resource.remaining,
                    'recharge_on': resource.recharge_on.value,
                    'level_based': resource.level_based,
                    'ability_based': resource.ability_based,
                    'ability_name': resource.ability_name,
                    'ability_modifier': resource.ability_modifier,
                    'usage_fraction': resource.usage_fraction,
                    'is_depleted': resource.is_depleted,
                    'description': resource.description,
                    'breakdown': resource.breakdown
                }
                class_resources.append(resource_dict)
            
            # Organize resources by class
            resources_by_class = self._organize_resources_by_class(class_resources)
            
            # Organize resources by rest type
            resources_by_rest_type = self._organize_resources_by_rest_type(class_resources)
            
            # Find depleted resources
            depleted_resources = [r['name'] for r in class_resources if r['is_depleted']]
            
            # Structure the data
            resources_data = ResourcesData(
                class_resources=class_resources,
                resources_by_class=resources_by_class,
                resources_by_rest_type=resources_by_rest_type,
                total_resources=len(class_resources),
                depleted_resources=depleted_resources,
                metadata={
                    "calculation_method": "class_resource_calculator",
                    "total_resources": len(class_resources),
                    "total_classes_with_resources": len(resources_by_class),
                    "depleted_count": len(depleted_resources),
                    "short_rest_resources": len(resources_by_rest_type.get('short_rest', [])),
                    "long_rest_resources": len(resources_by_rest_type.get('long_rest', [])),
                    "coordinator_version": self.version
                }
            )
            
            # Log summary
            self.logger.info(f"Successfully calculated class resources. Total: {len(class_resources)}")
            self.logger.info(f"  Classes with resources: {len(resources_by_class)}")
            self.logger.info(f"  Depleted resources: {len(depleted_resources)}")
            
            if class_resources:
                resource_names = [r['name'] for r in class_resources]
                self.logger.info(f"  Resource names: {resource_names}")
            
            if depleted_resources:
                self.logger.info(f"  Depleted: {depleted_resources}")
            
            return CalculationResult(
                service_name=self.coordinator_name,
                status=CalculationStatus.COMPLETED,
                data=self._format_output(resources_data),
                metadata=resources_data.metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating class resources: {e}")
            return CalculationResult(
                service_name=self.coordinator_name,
                status=CalculationStatus.FAILED,
                data={},
                errors=[str(e)],
                metadata={"error": str(e)}
            )
    
    def _transform_raw_data_for_calculator(self, raw_data: Dict[str, Any], context: CalculationContext) -> Dict[str, Any]:
        """Transform raw D&D Beyond data to format expected by resource calculator."""
        # Get ability scores from context
        ability_scores = {}
        if context and hasattr(context, 'metadata') and context.metadata:
            abilities_data = context.metadata.get('abilities', {})
            ability_scores = abilities_data.get('ability_scores', {})
        
        # Fallback to raw data if context doesn't have abilities
        if not ability_scores:
            stats = raw_data.get('stats', [])
            ability_id_map = {
                1: "strength", 2: "dexterity", 3: "constitution",
                4: "intelligence", 5: "wisdom", 6: "charisma"
            }
            
            for stat in stats:
                ability_id = stat.get('id')
                ability_score = stat.get('value', 10)
                
                if ability_id in ability_id_map:
                    ability_name = ability_id_map[ability_id]
                    modifier = (ability_score - 10) // 2
                    ability_scores[ability_name] = {
                        'score': ability_score,
                        'modifier': modifier
                    }
        
        # Get classes
        classes = []
        raw_classes = raw_data.get('classes', [])
        for class_data in raw_classes:
            class_def = class_data.get('definition', {})
            classes.append({
                'name': class_def.get('name', 'Unknown'),
                'level': class_data.get('level', 1)
            })
        
        # Get character level
        character_level = sum(cls.get('level', 0) for cls in raw_classes) or 1
        
        # Get resource usage (would come from character state)
        resource_usage = raw_data.get('resource_usage', {})
        
        return {
            'classes': classes,
            'abilities': {
                'ability_scores': ability_scores
            },
            'character_info': {
                'level': character_level
            },
            'resource_usage': resource_usage
        }
    
    def _organize_resources_by_class(self, class_resources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Organize resources by class name."""
        resources_by_class = {}
        
        for resource in class_resources:
            class_name = resource['class']
            if class_name not in resources_by_class:
                resources_by_class[class_name] = []
            resources_by_class[class_name].append(resource)
        
        return resources_by_class
    
    def _organize_resources_by_rest_type(self, class_resources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Organize resources by rest type."""
        resources_by_rest_type = {
            'short_rest': [],
            'long_rest': [],
            'none': []
        }
        
        for resource in class_resources:
            rest_type = resource['recharge_on']
            if rest_type in resources_by_rest_type:
                resources_by_rest_type[rest_type].append(resource)
        
        return resources_by_rest_type
    
    def _format_output(self, data: ResourcesData) -> Dict[str, Any]:
        """
        Format resources data for output.
        
        Args:
            data: ResourcesData instance
            
        Returns:
            Formatted resource data dictionary
        """
        return {
            "class_resources": data.class_resources,
            "resources_by_class": data.resources_by_class,
            "resources_by_rest_type": data.resources_by_rest_type,
            "total_resources": data.total_resources,
            "depleted_resources": data.depleted_resources,
            "resources_metadata": data.metadata,
            "has_resources": data.total_resources > 0,
            "has_depleted_resources": len(data.depleted_resources) > 0,
            "short_rest_count": len(data.resources_by_rest_type.get('short_rest', [])),
            "long_rest_count": len(data.resources_by_rest_type.get('long_rest', []))
        }
    
    def simulate_rest(self, raw_data: Dict[str, Any], context: CalculationContext, rest_type: str) -> Dict[str, Any]:
        """
        Simulate taking a rest and return restored resources.
        
        Args:
            raw_data: Raw character data
            context: Calculation context
            rest_type: Type of rest ('short_rest' or 'long_rest')
            
        Returns:
            Dictionary with rest simulation results
        """
        try:
            # Transform data for calculator
            character_data = self._transform_raw_data_for_calculator(raw_data, context)
            
            # Convert string to RestType enum
            if rest_type == 'short_rest':
                rest_enum = RestType.SHORT_REST
            elif rest_type == 'long_rest':
                rest_enum = RestType.LONG_REST
            else:
                raise ValueError(f"Invalid rest type: {rest_type}")
            
            # Simulate rest using resource calculator
            rest_result = self.resource_calculator.simulate_rest(character_data, rest_enum)
            
            return {
                'rest_type': rest_type,
                'restored_resources': rest_result.get('restored_resources', []),
                'class_resources': [
                    {
                        'name': resource.resource_name,
                        'class': resource.class_name,
                        'maximum': resource.maximum,
                        'current': resource.current,
                        'used': resource.used,
                        'remaining': resource.remaining,
                        'usage_fraction': resource.usage_fraction
                    }
                    for resource in rest_result.get('class_resources', [])
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error simulating rest: {e}")
            return {
                'rest_type': rest_type,
                'error': str(e),
                'restored_resources': [],
                'class_resources': []
            }
    
    def validate_input(self, raw_data: Dict[str, Any]) -> bool:
        """
        Validate that we have sufficient data for resource calculation.
        
        Args:
            raw_data: Raw character data to validate
            
        Returns:
            True if inputs are valid, False otherwise
        """
        try:
            if not raw_data:
                return False
            
            # Check for basic character data
            if not raw_data.get('classes'):
                return False
            
            # Resource calculation is robust - can work with minimal data
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating resource inputs: {e}")
            return False
    
    def get_dependencies(self) -> List[str]:
        """Get list of coordinator dependencies."""
        return self.dependencies.copy()
    
    def get_name(self) -> str:
        """Get coordinator name."""
        return self.name
    
    def get_priority(self) -> int:
        """Get coordinator priority."""
        return self.priority
    
    def get_version(self) -> str:
        """Get coordinator version."""
        return self.version
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of the coordinator.
        
        Returns:
            Health check results
        """
        try:
            # Test calculator initialization
            test_calculator = self.resource_calculator is not None
            
            return {
                "status": "healthy" if test_calculator else "degraded",
                "name": self.name,
                "version": self.version,
                "priority": self.priority,
                "dependencies": self.dependencies,
                "calculator_available": test_calculator,
                "config_manager": self.config_manager is not None
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "name": self.name,
                "version": self.version
            }