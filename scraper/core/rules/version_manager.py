"""
D&D Beyond Character Scraper - Rule Version Manager

Handles detection and management of 2014 vs 2024 D&D rule differences.
Uses a conservative detection approach with multiple validation methods.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class RuleVersion(Enum):
    """D&D 5e rule version enumeration."""
    RULES_2014 = "2014"
    RULES_2024 = "2024"


@dataclass
class DetectionResult:
    """Result of rule version detection analysis."""
    version: RuleVersion
    confidence: float  # 0.0 to 1.0
    detection_method: str
    evidence: List[str]
    warnings: List[str]


class RuleVersionManager:
    """
    Centralized manager for detecting and handling D&D rule version differences.
    
    Detection Strategy (in order of priority):
    1. User override flags (--force-2014/--force-2024)
    2. Primary class analysis (official content only)
    3. Source book ID detection
    4. Species/Race terminology analysis
    5. Default to 2024 rules with info message
    
    Homebrew content is ignored for detection purposes.
    """
    
    def __init__(self):
        self.version_cache: Dict[int, DetectionResult] = {}
        self.force_version: Optional[RuleVersion] = None
        
        # 2024 Source Book IDs (official D&D Beyond sources)
        self.SOURCE_2024_IDS = {142, 143, 144, 145, 146, 147, 148, 149, 150}  # 2024 D&D content sources
        
        # Known homebrew/unofficial source patterns (to ignore)
        self.HOMEBREW_INDICATORS = {
            'homebrew', 'custom', 'unofficial', 'ua', 'unearthed'
        }
    
    def set_force_version(self, version: Optional[RuleVersion]) -> None:
        """Set forced rule version from command line arguments."""
        self.force_version = version
        if version:
            logger.info(f"Rule version forced to {version.value}")
    
    def detect_rule_version(self, character_data: Dict[str, Any], character_id: int = None) -> DetectionResult:
        """
        Detect the rule version for a character using multiple methods.
        
        Args:
            character_data: Raw D&D Beyond character data
            character_id: Optional character ID for caching
            
        Returns:
            DetectionResult with version, confidence, and evidence
        """
        # Check cache first
        if character_id and character_id in self.version_cache:
            return self.version_cache[character_id]
        
        # Check for forced version
        if self.force_version:
            result = DetectionResult(
                version=self.force_version,
                confidence=1.0,
                detection_method="user_override",
                evidence=[f"User forced version to {self.force_version.value}"],
                warnings=[]
            )
            if character_id:
                self.version_cache[character_id] = result
            return result
        
        # Run detection methods (in order of priority)
        detection_methods = [
            self._detect_by_features,
            self._detect_by_primary_class,
            self._detect_by_source_ids,
            self._detect_by_terminology,
            self._detect_by_species_structure
        ]
        
        results = []
        for method in detection_methods:
            try:
                method_result = method(character_data)
                if method_result:
                    results.append(method_result)
            except Exception as e:
                logger.warning(f"Detection method {method.__name__} failed: {e}")
        
        # Analyze results and make final determination
        final_result = self._analyze_detection_results(results, character_data)
        
        # Cache result
        if character_id:
            self.version_cache[character_id] = final_result
        
        return final_result
    
    def _detect_by_features(self, character_data: Dict[str, Any]) -> Optional[DetectionResult]:
        """Detect rule version based on feature descriptions with 2024-specific patterns."""
        evidence = []
        
        # Check features for 2024-specific content patterns
        features = character_data.get('features', {})
        
        # Handle features structure - features is a dict with categories (v6.0.0 format)
        if isinstance(features, dict):
            for category, feature_list in features.items():
                if isinstance(feature_list, list):
                    for feature in feature_list:
                        if not isinstance(feature, dict):
                            continue
                            
                        description = feature.get('description', '').lower()
                        feature_name = feature.get('name', 'Unknown Feature')
                        
                        # Look for 2024-specific language patterns
                        patterns_2024 = [
                            'you gain a wizard subclass of your choice',  # 2024 wizard language
                            'specialization that grants you features',     # 2024 subclass language
                            'for the rest of your career',                # 2024 feature language
                            'expertise in two skills',                    # 2024 rogue feature
                            'channel divinity',                           # 2024 cleric changes
                        ]
                        
                        for pattern in patterns_2024:
                            if pattern in description:
                                evidence.append(f"Found 2024-specific pattern '{pattern}' in {category} feature '{feature_name}'")
                                return DetectionResult(
                                    version=RuleVersion.RULES_2024,
                                    confidence=0.9,
                                    detection_method="feature_analysis",
                                    evidence=evidence,
                                    warnings=[]
                                )
        
        # Handle features list (legacy format)
        elif isinstance(features, list):
            for feature in features:
                if not isinstance(feature, dict):
                    continue
                    
                description = feature.get('description', '').lower()
                feature_name = feature.get('name', 'Unknown Feature')
                
                # Look for 2024-specific language patterns
                patterns_2024 = [
                    'you gain a wizard subclass of your choice',  # 2024 wizard language
                    'specialization that grants you features',     # 2024 subclass language
                    'for the rest of your career',                # 2024 feature language
                ]
                
                for pattern in patterns_2024:
                    if pattern in description:
                        evidence.append(f"Found 2024-specific pattern '{pattern}' in feature '{feature_name}'")
                        return DetectionResult(
                            version=RuleVersion.RULES_2024,
                            confidence=0.9,
                            detection_method="feature_analysis",
                            evidence=evidence,
                            warnings=[]
                        )
        
        return None
    
    def _detect_by_primary_class(self, character_data: Dict[str, Any]) -> Optional[DetectionResult]:
        """Detect rule version based on primary class source."""
        classes = character_data.get('classes', [])
        if not classes:
            return None
        
        # Filter out None values and classes without level data
        valid_classes = [c for c in classes if c is not None and isinstance(c, dict) and 'level' in c]
        if not valid_classes:
            return None
        
        # Get primary class (highest level, or first if tied)
        primary_class = max(valid_classes, key=lambda c: c.get('level', 0))
        
        class_source_id = None
        subclass_source_id = None

        # Check class definition source
        if 'definition' in primary_class and primary_class['definition'] is not None:
            class_def = primary_class['definition']
            # Try direct sourceId first (old format)
            class_source_id = class_def.get('sourceId')

            # If not found, check sources array (new format)
            if not class_source_id and 'sources' in class_def:
                sources = class_def.get('sources', [])
                if sources and isinstance(sources, list) and len(sources) > 0:
                    class_source_id = sources[0].get('sourceId')

        # Check subclass definition source
        if 'subclassDefinition' in primary_class and primary_class['subclassDefinition'] is not None:
            subclass_def = primary_class['subclassDefinition']
            # Try direct sourceId first (old format)
            subclass_source_id = subclass_def.get('sourceId')

            # If not found, check sources array (new format)
            if not subclass_source_id and 'sources' in subclass_def:
                sources = subclass_def.get('sources', [])
                if sources and isinstance(sources, list) and len(sources) > 0:
                    subclass_source_id = sources[0].get('sourceId')
        
        evidence = []
        version = None
        confidence = 0.0
        
        # Analyze class source
        if class_source_id in self.SOURCE_2024_IDS:
            version = RuleVersion.RULES_2024
            confidence = 0.9
            evidence.append(f"Primary class source ID {class_source_id} indicates 2024 rules")
        elif class_source_id and class_source_id not in self.SOURCE_2024_IDS:
            version = RuleVersion.RULES_2014
            confidence = 0.8
            evidence.append(f"Primary class source ID {class_source_id} indicates 2014 rules")
        
        # Analyze subclass source (can override if different)
        if subclass_source_id:
            if subclass_source_id in self.SOURCE_2024_IDS:
                if version == RuleVersion.RULES_2014:
                    # Mixed content - conservative approach
                    evidence.append(f"Mixed content: 2014 class with 2024 subclass (ID {subclass_source_id})")
                    evidence.append("Using 2014 rules due to mixed content")
                else:
                    version = RuleVersion.RULES_2024
                    confidence = max(confidence, 0.9)
                    evidence.append(f"Subclass source ID {subclass_source_id} confirms 2024 rules")
            elif subclass_source_id not in self.SOURCE_2024_IDS:
                # 2014 subclass
                if version == RuleVersion.RULES_2024:
                    version = RuleVersion.RULES_2014  # Conservative: any 2014 content = 2014 rules
                    confidence = 0.8
                    evidence.append(f"Mixed content: 2024 class with 2014 subclass (ID {subclass_source_id})")
                    evidence.append("Using 2014 rules due to mixed content")
        
        if version:
            return DetectionResult(
                version=version,
                confidence=confidence,
                detection_method="primary_class",
                evidence=evidence,
                warnings=[]
            )
        
        return None
    
    def _detect_by_source_ids(self, character_data: Dict[str, Any]) -> Optional[DetectionResult]:
        """Detect rule version based on source book IDs across character data."""
        source_ids = set()
        evidence = []
        
        # Collect source IDs from various character components
        components_to_check = [
            ('race', character_data.get('race', {})),
            ('background', character_data.get('background', {})),
            ('feats', character_data.get('feats', [])),
            ('items', character_data.get('inventory', []))
        ]
        
        for component_name, component_data in components_to_check:
            if isinstance(component_data, dict):
                # Check definition.sourceId (old format)
                if 'definition' in component_data:
                    source_id = component_data['definition'].get('sourceId')
                    if source_id:
                        source_ids.add(source_id)
                        evidence.append(f"{component_name} source ID: {source_id}")
                
                # Check sources array (new format)
                if 'sources' in component_data:
                    for source in component_data['sources']:
                        if isinstance(source, dict):
                            source_id = source.get('sourceId')
                            if source_id:
                                source_ids.add(source_id)
                                evidence.append(f"{component_name} sources source ID: {source_id}")
                                
            elif isinstance(component_data, list):
                for item in component_data:
                    if isinstance(item, dict):
                        # Check definition.sourceId
                        if 'definition' in item:
                            source_id = item['definition'].get('sourceId')
                            if source_id:
                                source_ids.add(source_id)
                                evidence.append(f"{component_name} item source ID: {source_id}")
                        
                        # Check sources array
                        if 'sources' in item:
                            for source in item['sources']:
                                if isinstance(source, dict):
                                    source_id = source.get('sourceId')
                                    if source_id:
                                        source_ids.add(source_id)
                                        evidence.append(f"{component_name} item sources source ID: {source_id}")
        
        # Analyze source IDs
        has_2024_sources = bool(source_ids & self.SOURCE_2024_IDS)
        has_2014_sources = bool(source_ids - self.SOURCE_2024_IDS)
        
        if has_2024_sources and not has_2014_sources:
            return DetectionResult(
                version=RuleVersion.RULES_2024,
                confidence=0.8,
                detection_method="source_ids",
                evidence=evidence + ["All source IDs indicate 2024 rules"],
                warnings=[]
            )
        elif has_2014_sources and not has_2024_sources:
            return DetectionResult(
                version=RuleVersion.RULES_2014,
                confidence=0.8,
                detection_method="source_ids",
                evidence=evidence + ["All source IDs indicate 2014 rules"],
                warnings=[]
            )
        elif has_2024_sources and has_2014_sources:
            return DetectionResult(
                version=RuleVersion.RULES_2014,
                confidence=0.7,
                detection_method="source_ids",
                evidence=evidence + ["Mixed source IDs detected - using 2014 rules (conservative)"],
                warnings=["Character contains mixed 2014/2024 content"]
            )
        
        return None
    
    def _detect_by_terminology(self, character_data: Dict[str, Any]) -> Optional[DetectionResult]:
        """Detect rule version based on terminology (species vs race)."""
        evidence = []
        
        # Check for 2024 terminology
        if 'species' in character_data:
            evidence.append("Uses 'species' terminology (2024)")
            return DetectionResult(
                version=RuleVersion.RULES_2024,
                confidence=0.6,
                detection_method="terminology",
                evidence=evidence,
                warnings=[]
            )
        
        # Check for 2014 terminology
        if 'race' in character_data:
            evidence.append("Uses 'race' terminology (2014)")
            return DetectionResult(
                version=RuleVersion.RULES_2014,
                confidence=0.6,
                detection_method="terminology",
                evidence=evidence,
                warnings=[]
            )
        
        return None
    
    def _detect_by_species_structure(self, character_data: Dict[str, Any]) -> Optional[DetectionResult]:
        """Detect rule version based on species/race data structure."""
        race_data = character_data.get('race', {})
        if not race_data:
            return None
        
        evidence = []
        
        # Check for 2024-specific structural patterns
        # (This would need to be expanded based on actual API differences)
        if 'definition' in race_data:
            definition = race_data['definition']
            
            # Look for 2024-specific fields or structures
            # Note: This is a placeholder - would need actual API analysis
            if definition.get('isLegacy') is False:
                evidence.append("Species marked as non-legacy (potential 2024)")
                return DetectionResult(
                    version=RuleVersion.RULES_2024,
                    confidence=0.5,
                    detection_method="species_structure",
                    evidence=evidence,
                    warnings=[]
                )
        
        return None
    
    def _analyze_detection_results(self, results: List[DetectionResult], character_data: Dict[str, Any]) -> DetectionResult:
        """Analyze multiple detection results and determine final rule version."""
        if not results:
            # No detection results - default to 2024 with info message
            return DetectionResult(
                version=RuleVersion.RULES_2024,
                confidence=0.5,
                detection_method="default",
                evidence=["No clear rule version indicators found"],
                warnings=["Defaulting to 2024 rules - use --force-2014 if incorrect"]
            )
        
        # Sort by confidence
        results.sort(key=lambda r: r.confidence, reverse=True)
        best_result = results[0]
        
        # Check for conflicting high-confidence results
        conflicting_results = [
            r for r in results
            if r.version != best_result.version and r.confidence > 0.7
        ]

        if conflicting_results:
            # High-confidence conflict - prioritize class-based detection over race/items
            # Class mechanics are more important for determining rule version
            class_based_results = [
                r for r in results
                if r.detection_method in ['primary_class', 'feature_analysis']
            ]

            if class_based_results:
                # Use class-based detection when available (mixed content scenario)
                class_result = max(class_based_results, key=lambda r: r.confidence)
                all_evidence = []
                all_warnings = ["Mixed content detected (2024 class with 2014 race/items or vice versa)"]

                for result in results:
                    all_evidence.extend(result.evidence)
                    all_warnings.extend(result.warnings)

                return DetectionResult(
                    version=class_result.version,
                    confidence=0.85,
                    detection_method="mixed_content_class_priority",
                    evidence=all_evidence,
                    warnings=all_warnings + [f"Prioritizing class-based detection: {class_result.version.value} rules"]
                )

            # No class-based detection available - be conservative (2014)
            all_evidence = []
            all_warnings = ["Conflicting rule version indicators detected"]

            for result in results:
                all_evidence.extend(result.evidence)
                all_warnings.extend(result.warnings)

            return DetectionResult(
                version=RuleVersion.RULES_2014,
                confidence=0.6,
                detection_method="conflict_resolution",
                evidence=all_evidence,
                warnings=all_warnings + ["Using 2014 rules due to conflicts (conservative approach)"]
            )
        
        # Aggregate evidence and warnings from all results
        all_evidence = []
        all_warnings = []
        for result in results:
            all_evidence.extend(result.evidence)
            all_warnings.extend(result.warnings)
        
        return DetectionResult(
            version=best_result.version,
            confidence=best_result.confidence,
            detection_method=best_result.detection_method,
            evidence=all_evidence,
            warnings=all_warnings
        )
    
    def get_detection_summary(self, result: DetectionResult) -> str:
        """Generate a human-readable summary of rule detection."""
        summary_lines = [
            f"Rule Version Detected: {result.version.value}",
            f"Confidence: {result.confidence:.1%}",
            f"Detection Method: {result.detection_method}"
        ]
        
        if result.evidence:
            summary_lines.append("Evidence:")
            for evidence in result.evidence:
                summary_lines.append(f"  - {evidence}")
        
        if result.warnings:
            summary_lines.append("Warnings:")
            for warning in result.warnings:
                summary_lines.append(f"  ! {warning}")
        
        return "\n".join(summary_lines)