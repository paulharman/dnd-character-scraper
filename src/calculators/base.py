"""
Base Calculator with Rule Version Awareness

Provides a base class for all calculators that need to handle 2014 vs 2024 rule differences.
"""

from typing import Dict, Any, Optional
import logging
from abc import ABC, abstractmethod

from ..rules.version_manager import RuleVersionManager, RuleVersion, DetectionResult
from ..rules.constants import GameConstants

logger = logging.getLogger(__name__)


class RuleAwareCalculator(ABC):
    """
    Base class for calculators that need to handle 2014/2024 rule differences.
    
    Provides common functionality for rule version detection and rule-specific calculations.
    """
    
    def __init__(self, config_manager=None, rule_manager: Optional[RuleVersionManager] = None):
        """
        Initialize rule-aware calculator.
        
        Args:
            config_manager: Configuration manager instance
            rule_manager: Rule version manager instance (creates new if None)
        """
        self.config_manager = config_manager
        self.rule_manager = rule_manager or RuleVersionManager()
        self.constants = GameConstants()
        
    def get_rule_version(self, raw_data: Dict[str, Any], character_id: int = None) -> DetectionResult:
        """
        Get rule version for character data.
        
        Args:
            raw_data: Raw character data from D&D Beyond
            character_id: Optional character ID for caching
            
        Returns:
            DetectionResult with rule version and analysis
        """
        return self.rule_manager.detect_rule_version(raw_data, character_id)
    
    def log_rule_detection(self, detection_result: DetectionResult, character_id: int = None):
        """
        Log rule detection results for debugging.
        
        Args:
            detection_result: Rule detection result
            character_id: Optional character ID for context
        """
        prefix = f"Character {character_id}: " if character_id else ""
        logger.info(f"{prefix}Detected {detection_result.version.value} rules "
                   f"({detection_result.confidence:.1%} confidence)")
        
        if detection_result.warnings:
            for warning in detection_result.warnings:
                logger.warning(f"{prefix}{warning}")
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"{prefix}Detection method: {detection_result.detection_method}")
            for evidence in detection_result.evidence:
                logger.debug(f"{prefix}Evidence: {evidence}")
    
    @abstractmethod
    def calculate(self, raw_data: Dict[str, Any], **kwargs) -> Any:
        """
        Perform the calculation with rule version awareness.
        
        Args:
            raw_data: Raw character data from D&D Beyond
            **kwargs: Additional calculation parameters
            
        Returns:
            Calculated result (type varies by calculator)
        """
        pass
    
    def calculate_with_rule_version(self, raw_data: Dict[str, Any], rule_version: RuleVersion = None, **kwargs) -> Any:
        """
        Perform calculation with explicit rule version.
        
        Args:
            raw_data: Raw character data from D&D Beyond
            rule_version: Explicit rule version to use (overrides detection)
            **kwargs: Additional calculation parameters
            
        Returns:
            Calculated result (type varies by calculator)
        """
        # Set forced version if provided
        if rule_version:
            original_force = self.rule_manager.force_version
            self.rule_manager.set_force_version(rule_version)
            try:
                result = self.calculate(raw_data, **kwargs)
            finally:
                self.rule_manager.set_force_version(original_force)
            return result
        else:
            return self.calculate(raw_data, **kwargs)


class LegacyCalculatorAdapter(RuleAwareCalculator):
    """
    Adapter to make existing calculators rule-aware without breaking changes.
    
    Wraps existing calculator implementations and adds rule version detection.
    """
    
    def __init__(self, legacy_calculator, config_manager=None, rule_manager: Optional[RuleVersionManager] = None):
        """
        Initialize adapter for legacy calculator.
        
        Args:
            legacy_calculator: Existing calculator instance to wrap
            config_manager: Configuration manager instance
            rule_manager: Rule version manager instance
        """
        super().__init__(config_manager, rule_manager)
        self.legacy_calculator = legacy_calculator
    
    def calculate(self, raw_data: Dict[str, Any], **kwargs) -> Any:
        """
        Perform calculation using legacy calculator with rule detection.
        
        Args:
            raw_data: Raw character data from D&D Beyond
            **kwargs: Additional calculation parameters
            
        Returns:
            Result from legacy calculator
        """
        # Detect rule version
        character_id = kwargs.get('character_id')
        detection_result = self.get_rule_version(raw_data, character_id)
        
        # Log detection for debugging
        self.log_rule_detection(detection_result, character_id)
        
        # Call legacy calculator (most existing calculators work for both rule versions)
        if hasattr(self.legacy_calculator, 'calculate'):
            return self.legacy_calculator.calculate(raw_data, **kwargs)
        else:
            # Some calculators might have different method names
            raise NotImplementedError(f"Legacy calculator {type(self.legacy_calculator)} "
                                    f"doesn't have expected calculate method")


def make_rule_aware(calculator_class):
    """
    Decorator to make existing calculator classes rule-aware.
    
    Args:
        calculator_class: Existing calculator class to enhance
        
    Returns:
        Enhanced calculator class with rule version awareness
    """
    class RuleAwareWrapper(calculator_class, RuleAwareCalculator):
        def __init__(self, config_manager=None, rule_manager: Optional[RuleVersionManager] = None):
            calculator_class.__init__(self, config_manager)
            RuleAwareCalculator.__init__(self, config_manager, rule_manager)
    
    return RuleAwareWrapper