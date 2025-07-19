"""
Calculator Factory

Factory for creating calculator components with dependency injection.
Provides centralized configuration and wiring of all calculator services,
coordinators, and utilities.
"""

from typing import Dict, Any, Optional, List
import logging

from ..services.calculation_service import CalculationService
from ..services.character_builder import CharacterBuilder
from ..services.validation_service import ValidationService
from ..services.performance_service import PerformanceService
from ..coordinators.character_info import CharacterInfoCoordinator
from ..coordinators.abilities import AbilitiesCoordinator
from ..coordinators.proficiencies import ProficienciesCoordinator
from ..coordinators.combat import CombatCoordinator
from ..coordinators.spellcasting import SpellcastingCoordinator
from ..coordinators.features import FeaturesCoordinator
from ..coordinators.equipment import EquipmentCoordinator
from ..coordinators.resources import ResourcesCoordinator
from ..interfaces.coordination import ICoordinator

logger = logging.getLogger(__name__)


class CalculatorFactory:
    """
    Factory for creating calculator components with dependency injection.
    
    This factory provides centralized creation and configuration of all
    calculator components, ensuring proper dependency injection and
    consistent configuration across the system.
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize the calculator factory.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Component caches for singleton behavior
        self._validation_service = None
        self._performance_service = None
        self._character_builder = None
        self._coordinators: Dict[str, ICoordinator] = {}
    
    def create_calculation_service(self, config_manager=None) -> CalculationService:
        """
        Create a fully configured CalculationService with all coordinators.
        
        Args:
            config_manager: Optional configuration manager override
            
        Returns:
            Configured CalculationService instance
        """
        config = config_manager or self.config_manager
        
        # Create calculation service
        calculation_service = CalculationService(config)
        
        # Create and register all coordinators
        coordinators = self.create_all_coordinators(config)
        for coordinator in coordinators:
            calculation_service.register_coordinator(coordinator)
        
        self.logger.info(f"Created CalculationService with {len(coordinators)} coordinators")
        return calculation_service
    
    def create_all_coordinators(self, config_manager=None) -> List[ICoordinator]:
        """
        Create all standard coordinators with proper configuration.
        
        Args:
            config_manager: Optional configuration manager override
            
        Returns:
            List of configured coordinator instances
        """
        config = config_manager or self.config_manager
        
        # Create coordinators in dependency order
        coordinators = [
            self.create_character_info_coordinator(config),
            self.create_abilities_coordinator(config),
            self.create_proficiencies_coordinator(config),
            self.create_combat_coordinator(config),
            self.create_resources_coordinator(config),
            self.create_spellcasting_coordinator(config),
            self.create_features_coordinator(config),
            self.create_equipment_coordinator(config)
        ]
        
        self.logger.info(f"Created {len(coordinators)} coordinators")
        return coordinators
    
    def create_character_info_coordinator(self, config_manager=None) -> CharacterInfoCoordinator:
        """Create CharacterInfoCoordinator with dependencies."""
        if 'character_info' not in self._coordinators:
            config = config_manager or self.config_manager
            self._coordinators['character_info'] = CharacterInfoCoordinator(config)
            self.logger.debug("Created CharacterInfoCoordinator")
        
        return self._coordinators['character_info']
    
    def create_abilities_coordinator(self, config_manager=None) -> AbilitiesCoordinator:
        """Create AbilitiesCoordinator with dependencies."""
        if 'abilities' not in self._coordinators:
            config = config_manager or self.config_manager
            self._coordinators['abilities'] = AbilitiesCoordinator(config)
            self.logger.debug("Created AbilitiesCoordinator")
        
        return self._coordinators['abilities']
    
    def create_proficiencies_coordinator(self, config_manager=None) -> ProficienciesCoordinator:
        """Create ProficienciesCoordinator with dependencies."""
        if 'proficiencies' not in self._coordinators:
            config = config_manager or self.config_manager
            self._coordinators['proficiencies'] = ProficienciesCoordinator(config)
            self.logger.debug("Created ProficienciesCoordinator")
        
        return self._coordinators['proficiencies']
    
    def create_combat_coordinator(self, config_manager=None) -> CombatCoordinator:
        """Create CombatCoordinator with dependencies."""
        if 'combat' not in self._coordinators:
            config = config_manager or self.config_manager
            self._coordinators['combat'] = CombatCoordinator(config)
            self.logger.debug("Created CombatCoordinator")
        
        return self._coordinators['combat']
    
    def create_spellcasting_coordinator(self, config_manager=None) -> SpellcastingCoordinator:
        """Create SpellcastingCoordinator with dependencies."""
        if 'spellcasting' not in self._coordinators:
            config = config_manager or self.config_manager
            self._coordinators['spellcasting'] = SpellcastingCoordinator(config)
            self.logger.debug("Created SpellcastingCoordinator")
        
        return self._coordinators['spellcasting']
    
    def create_features_coordinator(self, config_manager=None) -> FeaturesCoordinator:
        """Create FeaturesCoordinator with dependencies."""
        if 'features' not in self._coordinators:
            config = config_manager or self.config_manager
            self._coordinators['features'] = FeaturesCoordinator(config)
            self.logger.debug("Created FeaturesCoordinator")
        
        return self._coordinators['features']
    
    def create_equipment_coordinator(self, config_manager=None) -> EquipmentCoordinator:
        """Create EquipmentCoordinator with dependencies."""
        if 'equipment' not in self._coordinators:
            config = config_manager or self.config_manager
            self._coordinators['equipment'] = EquipmentCoordinator(config)
            self.logger.debug("Created EquipmentCoordinator")
        
        return self._coordinators['equipment']
    
    def create_resources_coordinator(self, config_manager=None) -> ResourcesCoordinator:
        """Create ResourcesCoordinator with dependencies."""
        if 'resources' not in self._coordinators:
            config = config_manager or self.config_manager
            self._coordinators['resources'] = ResourcesCoordinator(config)
            self.logger.debug("Created ResourcesCoordinator")
        
        return self._coordinators['resources']
    
    def create_character_builder(self, config_manager=None) -> CharacterBuilder:
        """
        Create CharacterBuilder with dependencies.
        
        Args:
            config_manager: Optional configuration manager override
            
        Returns:
            Configured CharacterBuilder instance
        """
        if self._character_builder is None:
            config = config_manager or self.config_manager
            
            # Create character builder (validation service is internal)
            self._character_builder = CharacterBuilder(config_manager=config)
            
            self.logger.debug("Created CharacterBuilder")
        
        return self._character_builder
    
    def create_validation_service(self, config_manager=None) -> ValidationService:
        """
        Create ValidationService with configuration.
        
        Args:
            config_manager: Optional configuration manager override
            
        Returns:
            Configured ValidationService instance
        """
        if self._validation_service is None:
            config = config_manager or self.config_manager
            self._validation_service = ValidationService(config)
            self.logger.debug("Created ValidationService")
        
        return self._validation_service
    
    def create_performance_service(self, config_manager=None) -> PerformanceService:
        """
        Create PerformanceService with configuration.
        
        Args:
            config_manager: Optional configuration manager override
            
        Returns:
            Configured PerformanceService instance
        """
        if self._performance_service is None:
            config = config_manager or self.config_manager
            self._performance_service = PerformanceService(config)
            self.logger.debug("Created PerformanceService")
        
        return self._performance_service
    
    def create_full_calculator_stack(self, config_manager=None) -> Dict[str, Any]:
        """
        Create complete calculator stack with all components.
        
        Args:
            config_manager: Optional configuration manager override
            
        Returns:
            Dictionary containing all calculator components
        """
        config = config_manager or self.config_manager
        
        # Create all services
        calculation_service = self.create_calculation_service(config)
        character_builder = self.create_character_builder(config)
        validation_service = self.create_validation_service(config)
        performance_service = self.create_performance_service(config)
        
        stack = {
            'calculation_service': calculation_service,
            'character_builder': character_builder,
            'validation_service': validation_service,
            'performance_service': performance_service,
            'coordinators': {
                name: coordinator for name, coordinator in self._coordinators.items()
            }
        }
        
        self.logger.info("Created complete calculator stack")
        return stack
    
    def get_coordinator(self, coordinator_name: str) -> Optional[ICoordinator]:
        """
        Get a coordinator by name.
        
        Args:
            coordinator_name: Name of the coordinator
            
        Returns:
            Coordinator instance or None if not found
        """
        return self._coordinators.get(coordinator_name)
    
    def list_coordinators(self) -> List[str]:
        """
        List all created coordinator names.
        
        Returns:
            List of coordinator names
        """
        return list(self._coordinators.keys())
    
    def clear_cache(self):
        """Clear all cached components (for testing)."""
        self._validation_service = None
        self._performance_service = None
        self._character_builder = None
        self._coordinators.clear()
        self.logger.debug("Cleared factory cache")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of the factory.
        
        Returns:
            Health check results
        """
        return {
            'status': 'healthy',
            'coordinators_created': len(self._coordinators),
            'services_cached': {
                'validation_service': self._validation_service is not None,
                'performance_service': self._performance_service is not None,
                'character_builder': self._character_builder is not None
            },
            'available_coordinators': list(self._coordinators.keys())
        }