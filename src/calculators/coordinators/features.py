"""
Features Coordinator

Coordinates the extraction and processing of class features, traits, and abilities
with comprehensive support for both class and subclass features.
"""

from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass

from ..interfaces.coordination import ICoordinator
from ..utils.performance import monitor_performance
from ..services.interfaces import CalculationContext, CalculationResult, CalculationStatus

logger = logging.getLogger(__name__)


@dataclass
class FeaturesData:
    """Data class for features calculation results."""
    class_features: List[Dict[str, Any]]
    racial_traits: List[Dict[str, Any]]
    feats: List[Dict[str, Any]]
    background_features: List[Dict[str, Any]]
    total_features: int
    features_by_level: Dict[int, List[Dict[str, Any]]]
    limited_use_features: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class FeaturesCoordinator(ICoordinator):
    """
    Coordinates features and traits calculations with comprehensive support.
    
    This coordinator handles:
    - Class features from all classes
    - Subclass features with level requirements
    - Racial traits and abilities
    - Background features
    - Feats and character options
    - Limited use features tracking
    - Feature scaling and level progression
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize the features coordinator.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @property
    def coordinator_name(self) -> str:
        """Get the coordinator name."""
        return "features"
    
    @property
    def dependencies(self) -> List[str]:
        """Get the list of dependencies."""
        return ["character_info"]  # Depends on character level and class info
    
    @property
    def priority(self) -> int:
        """Get the execution priority (lower = higher priority)."""
        return 50  # Medium priority - depends on character info
    
    @monitor_performance("features_coordinate")
    def coordinate(self, raw_data: Dict[str, Any], context: CalculationContext) -> CalculationResult:
        """
        Coordinate the calculation of features and traits.
        
        Args:
            raw_data: Raw character data from D&D Beyond
            context: Calculation context
            
        Returns:
            CalculationResult with features data
        """
        self.logger.info(f"Coordinating features calculation for character {raw_data.get('id', 'unknown')}")
        
        try:
            # Extract class features
            class_features = self._extract_class_features(raw_data)
            
            # Extract racial traits
            racial_traits = self._extract_racial_traits(raw_data)
            
            # Extract feats
            feats = self._extract_feats(raw_data)
            
            # Extract background features
            background_features = self._extract_background_features(raw_data)
            
            # Process features by level
            features_by_level = self._organize_features_by_level(class_features)
            
            # Identify limited use features
            limited_use_features = self._identify_limited_use_features(
                class_features + racial_traits + feats + background_features
            )
            
            # Calculate totals
            total_features = len(class_features) + len(racial_traits) + len(feats) + len(background_features)
            
            # Create result data
            result_data = {
                'class_features': class_features,
                'racial_traits': racial_traits,
                'feats': feats,
                'background_features': background_features,
                'total_features': total_features,
                'features_by_level': features_by_level,
                'limited_use_features': limited_use_features,
                'metadata': {
                    'class_feature_count': len(class_features),
                    'racial_trait_count': len(racial_traits),
                    'feat_count': len(feats),
                    'background_feature_count': len(background_features),
                    'limited_use_count': len(limited_use_features),
                    'highest_level_features': max(features_by_level.keys()) if features_by_level else 0,
                    'has_subclass_features': any(f.get('is_subclass_feature', False) for f in class_features)
                }
            }
            
            self.logger.info(f"Successfully calculated features. Total: {total_features}")
            
            return CalculationResult(
                service_name=self.coordinator_name,
                status=CalculationStatus.COMPLETED,
                data=result_data,
                errors=[],
                warnings=[]
            )
            
        except Exception as e:
            self.logger.error(f"Error coordinating features calculation: {str(e)}")
            return CalculationResult(
                service_name=self.coordinator_name,
                status=CalculationStatus.FAILED,
                data={},
                errors=[f"Features calculation failed: {str(e)}"]
            )
    
    def _extract_class_features(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract class features from character data."""
        features = []
        classes = raw_data.get('classes', [])
        
        for class_data in classes:
            class_name = class_data.get('definition', {}).get('name', 'Unknown')
            class_level = class_data.get('level', 1)
            
            # Extract class features
            class_features = class_data.get('classFeatures', [])
            for feature_data in class_features:
                feature = self._process_feature_data(feature_data, class_name, False)
                if feature and feature.get('level_required', 1) <= class_level:
                    features.append(feature)
            
            # Extract subclass features
            subclass_data = class_data.get('subclassDefinition')
            if subclass_data:
                subclass_name = subclass_data.get('name', 'Unknown')
                subclass_features = subclass_data.get('classFeatures', [])
                for feature_data in subclass_features:
                    feature = self._process_feature_data(feature_data, subclass_name, True)
                    if feature and feature.get('level_required', 1) <= class_level:
                        features.append(feature)
        
        return features
    
    def _extract_racial_traits(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract racial traits from character data."""
        traits = []
        
        # Extract from race data
        race_data = raw_data.get('race', {})
        if race_data:
            race_name = race_data.get('fullName', race_data.get('baseName', 'Unknown'))
            
            # Extract racial traits
            racial_traits = race_data.get('racialTraits', [])
            for trait_data in racial_traits:
                trait = self._process_trait_data(trait_data, race_name, 'racial')
                if trait:
                    traits.append(trait)
        
        # Extract from optional class features that might be racial
        optional_features = raw_data.get('optionalClassFeatures', [])
        for feature_data in optional_features:
            # Check if this is a racial variant
            if self._is_racial_variant(feature_data):
                trait = self._process_trait_data(feature_data, 'Racial Variant', 'racial')
                if trait:
                    traits.append(trait)
        
        return traits
    
    def _extract_feats(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract feats from character data."""
        feats = []
        
        # Extract from feats array
        feats_data = raw_data.get('feats', [])
        for feat_data in feats_data:
            feat = self._process_feat_data(feat_data)
            if feat:
                feats.append(feat)
        
        return feats
    
    def _extract_background_features(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract background features from character data."""
        features = []
        
        # Extract from background data
        background_data = raw_data.get('background', {})
        if background_data:
            background_name = background_data.get('definition', {}).get('name', 'Unknown')
            
            # Extract background features
            background_features = background_data.get('backgroundFeatures', [])
            for feature_data in background_features:
                feature = self._process_trait_data(feature_data, background_name, 'background')
                if feature:
                    features.append(feature)
        
        return features
    
    def _process_feature_data(self, feature_data: Dict[str, Any], source_name: str, is_subclass: bool) -> Optional[Dict[str, Any]]:
        """Process individual feature data."""
        try:
            # Handle both wrapped (definition) and unwrapped feature data
            definition = feature_data.get('definition', {})
            if not definition:
                if 'id' in feature_data and 'name' in feature_data:
                    definition = feature_data
                else:
                    return None
            
            # Extract basic information
            feature_id = definition.get('id')
            name = definition.get('name', 'Unknown Feature')
            description = definition.get('description', '')
            snippet = definition.get('snippet', '')
            level_required = definition.get('requiredLevel', 1)
            
            # Extract metadata
            feature_type = definition.get('featureType')
            if isinstance(feature_type, int):
                feature_type = str(feature_type)
            
            # Extract usage limitations
            limited_use = definition.get('limitedUse')
            if isinstance(limited_use, list):
                limited_use = limited_use[0] if limited_use and isinstance(limited_use[0], dict) else None
            elif not isinstance(limited_use, dict):
                limited_use = None
            
            # Extract level scaling
            level_scales = definition.get('levelScales', [])
            if not level_scales and 'levelScale' in feature_data:
                level_scales = [feature_data['levelScale']]
            
            return {
                'id': feature_id,
                'name': name,
                'description': description,
                'snippet': snippet,
                'level_required': level_required,
                'is_subclass_feature': is_subclass,
                'feature_type': feature_type,
                'source_name': source_name,
                'limited_use': limited_use,
                'level_scales': level_scales,
                'activation': definition.get('activation'),
                'hide_in_builder': definition.get('hideInBuilder', False),
                'hide_in_sheet': definition.get('hideInSheet', False),
                'display_order': definition.get('displayOrder'),
                'source_id': definition.get('sourceId'),
                'source_page_number': definition.get('sourcePageNumber'),
                'definition_key': definition.get('definitionKey'),
                'spell_list_ids': definition.get('spellListIds', []),
                'creature_rules': definition.get('creatureRules', [])
            }
            
        except Exception as e:
            self.logger.warning(f"Error processing feature data: {e}")
            return None
    
    def _process_trait_data(self, trait_data: Dict[str, Any], source_name: str, trait_type: str) -> Optional[Dict[str, Any]]:
        """Process racial trait or background feature data."""
        try:
            # Handle both wrapped and unwrapped data
            definition = trait_data.get('definition', trait_data)
            
            trait_id = definition.get('id')
            name = definition.get('name', 'Unknown Trait')
            description = definition.get('description', '')
            snippet = definition.get('snippet', '')
            
            return {
                'id': trait_id,
                'name': name,
                'description': description,
                'snippet': snippet,
                'trait_type': trait_type,
                'source_name': source_name,
                'level_required': 1,  # Traits are usually available from level 1
                'is_subclass_feature': False,
                'limited_use': definition.get('limitedUse'),
                'activation': definition.get('activation'),
                'source_id': definition.get('sourceId'),
                'source_page_number': definition.get('sourcePageNumber')
            }
            
        except Exception as e:
            self.logger.warning(f"Error processing trait data: {e}")
            return None
    
    def _process_feat_data(self, feat_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process feat data."""
        try:
            definition = feat_data.get('definition', feat_data)
            
            feat_id = definition.get('id')
            name = definition.get('name', 'Unknown Feat')
            description = definition.get('description', '')
            snippet = definition.get('snippet', '')
            
            return {
                'id': feat_id,
                'name': name,
                'description': description,
                'snippet': snippet,
                'trait_type': 'feat',
                'source_name': 'Feat',
                'level_required': 1,
                'is_subclass_feature': False,
                'limited_use': definition.get('limitedUse'),
                'activation': definition.get('activation'),
                'source_id': definition.get('sourceId'),
                'source_page_number': definition.get('sourcePageNumber'),
                'prerequisites': definition.get('prerequisites', [])
            }
            
        except Exception as e:
            self.logger.warning(f"Error processing feat data: {e}")
            return None
    
    def _organize_features_by_level(self, class_features: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
        """Organize class features by level requirement."""
        features_by_level = {}
        
        for feature in class_features:
            level = feature.get('level_required', 1)
            if level not in features_by_level:
                features_by_level[level] = []
            features_by_level[level].append(feature)
        
        return features_by_level
    
    def _identify_limited_use_features(self, all_features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify features that have usage limitations."""
        limited_use_features = []
        
        for feature in all_features:
            if feature.get('limited_use'):
                limited_use_features.append(feature)
        
        return limited_use_features
    
    def _is_racial_variant(self, feature_data: Dict[str, Any]) -> bool:
        """Check if a feature is a racial variant."""
        # This is a heuristic check - you might need to adjust based on actual data
        definition = feature_data.get('definition', {})
        name = definition.get('name', '').lower()
        
        # Common racial variant keywords
        racial_keywords = ['variant', 'racial', 'heritage', 'lineage', 'subrace']
        
        return any(keyword in name for keyword in racial_keywords)
    
    def _get_character_level(self, raw_data: Dict[str, Any], context: CalculationContext) -> int:
        """Get character level from context or calculate from raw data."""
        # Try to get from context first
        if context and hasattr(context, 'metadata') and context.metadata:
            character_info = context.metadata.get('character_info', {})
            if 'level' in character_info:
                return character_info['level']
        
        # Fallback: calculate from classes
        classes = raw_data.get('classes', [])
        return sum(cls.get('level', 0) for cls in classes)
    
    def validate_input(self, raw_data: Dict[str, Any]) -> bool:
        """
        Validate that the input data is suitable for this coordinator.
        
        Args:
            raw_data: Raw character data to validate
            
        Returns:
            True if data is valid for this coordinator
        """
        # Features calculation can work with minimal data
        if not isinstance(raw_data, dict):
            return False
        
        # We can extract features from various sources, so very permissive validation
        return True
    
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
        return {
            "type": "object",
            "properties": {
                "class_features": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": ["integer", "null"]},
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "snippet": {"type": "string"},
                            "level_required": {"type": "integer", "minimum": 1},
                            "is_subclass_feature": {"type": "boolean"},
                            "feature_type": {"type": ["string", "null"]},
                            "source_name": {"type": "string"},
                            "limited_use": {"type": ["object", "null"]},
                            "level_scales": {"type": "array"},
                            "activation": {"type": ["object", "null"]}
                        },
                        "required": ["name", "level_required", "is_subclass_feature"]
                    }
                },
                "racial_traits": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": ["integer", "null"]},
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "trait_type": {"type": "string"},
                            "source_name": {"type": "string"}
                        },
                        "required": ["name", "trait_type"]
                    }
                },
                "feats": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": ["integer", "null"]},
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "prerequisites": {"type": "array"}
                        },
                        "required": ["name"]
                    }
                },
                "background_features": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": ["integer", "null"]},
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "trait_type": {"type": "string"}
                        },
                        "required": ["name", "trait_type"]
                    }
                },
                "total_features": {"type": "integer", "minimum": 0},
                "features_by_level": {
                    "type": "object",
                    "patternProperties": {
                        "^[0-9]+$": {
                            "type": "array",
                            "items": {"type": "object"}
                        }
                    }
                },
                "limited_use_features": {
                    "type": "array",
                    "items": {"type": "object"}
                },
                "metadata": {"type": "object"}
            },
            "required": [
                "class_features", "racial_traits", "feats", "background_features", 
                "total_features", "features_by_level", "limited_use_features"
            ]
        }