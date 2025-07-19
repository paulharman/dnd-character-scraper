"""
Change analysis interfaces for the DnD character tracking system.

This module defines the core interfaces for analyzing detected changes,
including priority assessment, impact analysis, and change categorization.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

# Import from the detection module
from ..change_detection.interfaces import FieldChange, ChangeContext, ChangePriority, ChangeCategory


class AnalysisType(Enum):
    """Types of analysis that can be performed on changes."""
    PRIORITY = "priority"
    IMPACT = "impact"
    SIGNIFICANCE = "significance"
    TREND = "trend"
    CORRELATION = "correlation"
    RISK = "risk"
    GAMEPLAY_EFFECT = "gameplay_effect"


class ImpactLevel(Enum):
    """Levels of impact for changes."""
    MINIMAL = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    CRITICAL = 5


class SignificanceLevel(Enum):
    """Levels of significance for changes."""
    TRIVIAL = 1
    MINOR = 2
    MODERATE = 3
    MAJOR = 4
    CRITICAL = 5


class TrendDirection(Enum):
    """Direction of trends in changes."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


@dataclass
class AnalysisResult:
    """Result of change analysis with confidence scoring."""
    analyzer_name: str
    analysis_type: AnalysisType
    confidence: float
    priority: int
    significance: float
    reasoning: str
    recommendations: List[str]
    metadata: Dict[str, Any] = None
    analysis_timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.analysis_timestamp is None:
            self.analysis_timestamp = datetime.now()


@dataclass
class ImpactAnalysis:
    """Analysis of change impact on character capabilities."""
    impact_level: ImpactLevel
    affected_systems: List[str]
    gameplay_effects: List[str]
    numerical_impact: Dict[str, float]
    mitigation_suggestions: List[str]
    confidence: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TrendAnalysis:
    """Analysis of trends in character changes over time."""
    trend_direction: TrendDirection
    trend_strength: float
    data_points: List[Dict[str, Any]]
    predictions: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    confidence: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CorrelationAnalysis:
    """Analysis of correlations between different changes."""
    correlated_changes: List[Tuple[str, str, float]]
    correlation_strength: float
    causal_relationships: List[Dict[str, Any]]
    pattern_matches: List[str]
    confidence: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class IChangeAnalyzer(ABC):
    """
    Base interface for change analyzers.
    
    Change analyzers examine detected changes to provide additional
    insights, priorities, and context.
    """
    
    @property
    @abstractmethod
    def analyzer_name(self) -> str:
        """Get the unique analyzer name."""
        pass
    
    @property
    @abstractmethod
    def analysis_type(self) -> AnalysisType:
        """Get the type of analysis this analyzer performs."""
        pass
    
    @property
    @abstractmethod
    def supported_categories(self) -> List[ChangeCategory]:
        """Get the change categories this analyzer supports."""
        pass
    
    @abstractmethod
    def analyze_change(self, change: FieldChange, context: ChangeContext) -> AnalysisResult:
        """
        Analyze a single change and return assessment.
        
        Args:
            change: The change to analyze
            context: Change detection context
            
        Returns:
            Analysis result with insights and recommendations
        """
        pass
    
    @abstractmethod
    def analyze_changes(self, changes: List[FieldChange], 
                       context: ChangeContext) -> List[AnalysisResult]:
        """
        Analyze multiple changes for patterns and relationships.
        
        Args:
            changes: List of changes to analyze
            context: Change detection context
            
        Returns:
            List of analysis results
        """
        pass
    
    @abstractmethod
    def validate_change(self, change: FieldChange) -> bool:
        """
        Validate that a change is suitable for analysis.
        
        Args:
            change: The change to validate
            
        Returns:
            True if change can be analyzed
        """
        pass
    
    @abstractmethod
    def get_confidence_score(self, analysis: AnalysisResult) -> float:
        """
        Get confidence score for analysis result.
        
        Args:
            analysis: Analysis result to score
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        pass


class IPriorityAnalyzer(ABC):
    """
    Interface for analyzing change priorities.
    
    Determines the relative importance of changes based on
    game rules, character state, and context.
    """
    
    @abstractmethod
    def analyze_priority(self, change: FieldChange, 
                        context: ChangeContext) -> ChangePriority:
        """
        Analyze the priority of a change.
        
        Args:
            change: The change to analyze
            context: Change detection context
            
        Returns:
            Priority level for the change
        """
        pass
    
    @abstractmethod
    def compare_priorities(self, change1: FieldChange, 
                          change2: FieldChange, 
                          context: ChangeContext) -> int:
        """
        Compare the priorities of two changes.
        
        Args:
            change1: First change to compare
            change2: Second change to compare
            context: Change detection context
            
        Returns:
            -1 if change1 has lower priority, 0 if equal, 1 if higher
        """
        pass
    
    @abstractmethod
    def get_priority_factors(self, change: FieldChange, 
                           context: ChangeContext) -> Dict[str, float]:
        """
        Get the factors that influence priority calculation.
        
        Args:
            change: The change to analyze
            context: Change detection context
            
        Returns:
            Dictionary of priority factors and their weights
        """
        pass
    
    @abstractmethod
    def set_priority_weights(self, weights: Dict[str, float]) -> None:
        """
        Set the weights for priority factors.
        
        Args:
            weights: Dictionary of factor weights
        """
        pass


class IImpactAnalyzer(ABC):
    """
    Interface for analyzing change impact.
    
    Assesses how changes affect character capabilities,
    gameplay, and mechanical interactions.
    """
    
    @abstractmethod
    def analyze_impact(self, change: FieldChange, 
                      context: ChangeContext) -> ImpactAnalysis:
        """
        Analyze the impact of a change.
        
        Args:
            change: The change to analyze
            context: Change detection context
            
        Returns:
            Impact analysis result
        """
        pass
    
    @abstractmethod
    def analyze_cumulative_impact(self, changes: List[FieldChange], 
                                 context: ChangeContext) -> ImpactAnalysis:
        """
        Analyze the cumulative impact of multiple changes.
        
        Args:
            changes: List of changes to analyze
            context: Change detection context
            
        Returns:
            Cumulative impact analysis
        """
        pass
    
    @abstractmethod
    def get_affected_systems(self, change: FieldChange) -> List[str]:
        """
        Get the game systems affected by a change.
        
        Args:
            change: The change to analyze
            
        Returns:
            List of affected system names
        """
        pass
    
    @abstractmethod
    def calculate_numerical_impact(self, change: FieldChange, 
                                  context: ChangeContext) -> Dict[str, float]:
        """
        Calculate numerical impact of a change.
        
        Args:
            change: The change to analyze
            context: Change detection context
            
        Returns:
            Dictionary of numerical impact values
        """
        pass


class ISignificanceAnalyzer(ABC):
    """
    Interface for analyzing change significance.
    
    Determines how meaningful changes are in the context
    of character development and game progression.
    """
    
    @abstractmethod
    def analyze_significance(self, change: FieldChange, 
                           context: ChangeContext) -> SignificanceLevel:
        """
        Analyze the significance of a change.
        
        Args:
            change: The change to analyze
            context: Change detection context
            
        Returns:
            Significance level for the change
        """
        pass
    
    @abstractmethod
    def get_significance_factors(self, change: FieldChange, 
                               context: ChangeContext) -> Dict[str, float]:
        """
        Get factors that influence significance calculation.
        
        Args:
            change: The change to analyze
            context: Change detection context
            
        Returns:
            Dictionary of significance factors
        """
        pass
    
    @abstractmethod
    def analyze_character_progression(self, changes: List[FieldChange], 
                                    context: ChangeContext) -> Dict[str, Any]:
        """
        Analyze how changes relate to character progression.
        
        Args:
            changes: List of changes to analyze
            context: Change detection context
            
        Returns:
            Character progression analysis
        """
        pass
    
    @abstractmethod
    def identify_milestones(self, changes: List[FieldChange], 
                           context: ChangeContext) -> List[Dict[str, Any]]:
        """
        Identify significant milestones in character development.
        
        Args:
            changes: List of changes to analyze
            context: Change detection context
            
        Returns:
            List of milestone events
        """
        pass


class ITrendAnalyzer(ABC):
    """
    Interface for analyzing trends in character changes.
    
    Identifies patterns and trends in character development
    over time for predictive analysis.
    """
    
    @abstractmethod
    def analyze_trend(self, field_path: str, 
                     historical_data: List[Dict[str, Any]], 
                     context: ChangeContext) -> TrendAnalysis:
        """
        Analyze trends for a specific field.
        
        Args:
            field_path: Path to the field to analyze
            historical_data: Historical change data
            context: Change detection context
            
        Returns:
            Trend analysis result
        """
        pass
    
    @abstractmethod
    def detect_patterns(self, changes: List[FieldChange], 
                       context: ChangeContext) -> List[Dict[str, Any]]:
        """
        Detect patterns in a set of changes.
        
        Args:
            changes: List of changes to analyze
            context: Change detection context
            
        Returns:
            List of detected patterns
        """
        pass
    
    @abstractmethod
    def predict_future_changes(self, historical_data: List[Dict[str, Any]], 
                              context: ChangeContext) -> List[Dict[str, Any]]:
        """
        Predict future changes based on historical data.
        
        Args:
            historical_data: Historical change data
            context: Change detection context
            
        Returns:
            List of predicted changes
        """
        pass
    
    @abstractmethod
    def identify_anomalies(self, changes: List[FieldChange], 
                          context: ChangeContext) -> List[Dict[str, Any]]:
        """
        Identify anomalous changes that don't fit patterns.
        
        Args:
            changes: List of changes to analyze
            context: Change detection context
            
        Returns:
            List of anomalous changes
        """
        pass


class ICorrelationAnalyzer(ABC):
    """
    Interface for analyzing correlations between changes.
    
    Identifies relationships and dependencies between
    different types of character changes.
    """
    
    @abstractmethod
    def analyze_correlations(self, changes: List[FieldChange], 
                           context: ChangeContext) -> CorrelationAnalysis:
        """
        Analyze correlations between changes.
        
        Args:
            changes: List of changes to analyze
            context: Change detection context
            
        Returns:
            Correlation analysis result
        """
        pass
    
    @abstractmethod
    def find_causal_relationships(self, changes: List[FieldChange], 
                                 context: ChangeContext) -> List[Dict[str, Any]]:
        """
        Find causal relationships between changes.
        
        Args:
            changes: List of changes to analyze
            context: Change detection context
            
        Returns:
            List of causal relationships
        """
        pass
    
    @abstractmethod
    def calculate_correlation_strength(self, change1: FieldChange, 
                                     change2: FieldChange, 
                                     context: ChangeContext) -> float:
        """
        Calculate correlation strength between two changes.
        
        Args:
            change1: First change
            change2: Second change
            context: Change detection context
            
        Returns:
            Correlation strength (-1.0 to 1.0)
        """
        pass
    
    @abstractmethod
    def identify_change_clusters(self, changes: List[FieldChange], 
                               context: ChangeContext) -> List[List[FieldChange]]:
        """
        Identify clusters of related changes.
        
        Args:
            changes: List of changes to analyze
            context: Change detection context
            
        Returns:
            List of change clusters
        """
        pass


class IValidationAnalyzer(ABC):
    """
    Interface for analyzing change validity and consistency.
    
    Validates that changes are logically consistent and
    comply with game rules and character constraints.
    """
    
    @abstractmethod
    def validate_change_consistency(self, change: FieldChange, 
                                  context: ChangeContext) -> bool:
        """
        Validate that a change is internally consistent.
        
        Args:
            change: The change to validate
            context: Change detection context
            
        Returns:
            True if change is consistent
        """
        pass
    
    @abstractmethod
    def validate_rule_compliance(self, change: FieldChange, 
                               context: ChangeContext) -> bool:
        """
        Validate that a change complies with game rules.
        
        Args:
            change: The change to validate
            context: Change detection context
            
        Returns:
            True if change complies with rules
        """
        pass
    
    @abstractmethod
    def validate_character_constraints(self, changes: List[FieldChange], 
                                     context: ChangeContext) -> List[str]:
        """
        Validate that changes don't violate character constraints.
        
        Args:
            changes: List of changes to validate
            context: Change detection context
            
        Returns:
            List of validation errors (empty if valid)
        """
        pass
    
    @abstractmethod
    def suggest_corrections(self, change: FieldChange, 
                           context: ChangeContext) -> List[Dict[str, Any]]:
        """
        Suggest corrections for invalid changes.
        
        Args:
            change: The change to correct
            context: Change detection context
            
        Returns:
            List of suggested corrections
        """
        pass


class IChangeAnalyzerFactory(ABC):
    """
    Interface for creating change analyzers.
    
    Provides factory methods for creating and configuring
    change analyzers with proper dependencies.
    """
    
    @abstractmethod
    def create_analyzer(self, analyzer_type: str, config: Dict[str, Any]) -> IChangeAnalyzer:
        """
        Create a change analyzer of the specified type.
        
        Args:
            analyzer_type: Type of analyzer to create
            config: Configuration for the analyzer
            
        Returns:
            Configured change analyzer
        """
        pass
    
    @abstractmethod
    def create_priority_analyzer(self, config: Dict[str, Any]) -> IPriorityAnalyzer:
        """
        Create a priority analyzer.
        
        Args:
            config: Configuration for the analyzer
            
        Returns:
            Configured priority analyzer
        """
        pass
    
    @abstractmethod
    def create_impact_analyzer(self, config: Dict[str, Any]) -> IImpactAnalyzer:
        """
        Create an impact analyzer.
        
        Args:
            config: Configuration for the analyzer
            
        Returns:
            Configured impact analyzer
        """
        pass
    
    @abstractmethod
    def create_trend_analyzer(self, config: Dict[str, Any]) -> ITrendAnalyzer:
        """
        Create a trend analyzer.
        
        Args:
            config: Configuration for the analyzer
            
        Returns:
            Configured trend analyzer
        """
        pass
    
    @abstractmethod
    def get_available_analyzers(self) -> List[str]:
        """
        Get list of available analyzer types.
        
        Returns:
            List of analyzer type names
        """
        pass


class IAnalysisAggregator(ABC):
    """
    Interface for aggregating analysis results.
    
    Combines results from multiple analyzers to provide
    comprehensive analysis summaries.
    """
    
    @abstractmethod
    def aggregate_results(self, results: List[AnalysisResult], 
                         context: ChangeContext) -> Dict[str, Any]:
        """
        Aggregate multiple analysis results.
        
        Args:
            results: List of analysis results to aggregate
            context: Change detection context
            
        Returns:
            Aggregated analysis summary
        """
        pass
    
    @abstractmethod
    def generate_summary(self, results: List[AnalysisResult], 
                        context: ChangeContext) -> str:
        """
        Generate a human-readable summary of analysis results.
        
        Args:
            results: List of analysis results
            context: Change detection context
            
        Returns:
            Summary text
        """
        pass
    
    @abstractmethod
    def rank_changes_by_importance(self, changes: List[FieldChange], 
                                  results: List[AnalysisResult], 
                                  context: ChangeContext) -> List[FieldChange]:
        """
        Rank changes by importance based on analysis results.
        
        Args:
            changes: List of changes to rank
            results: Analysis results for the changes
            context: Change detection context
            
        Returns:
            Changes ranked by importance
        """
        pass
    
    @abstractmethod
    def identify_key_insights(self, results: List[AnalysisResult], 
                            context: ChangeContext) -> List[Dict[str, Any]]:
        """
        Identify key insights from analysis results.
        
        Args:
            results: List of analysis results
            context: Change detection context
            
        Returns:
            List of key insights
        """
        pass