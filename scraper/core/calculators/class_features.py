"""
Class Feature Extractor

Extracts comprehensive class feature information from D&D Beyond API data.
"""

from typing import Dict, Any, List, Optional
import logging

from shared.models.character import ClassFeature
from .base import RuleAwareCalculator

logger = logging.getLogger(__name__)


class ClassFeatureExtractor(RuleAwareCalculator):
    """
    Extracts class features with rich details from D&D Beyond character data.
    
    Processes all class features including subclass features, scaling features,
    and usage limitations. Maintains compatibility with both 2014 and 2024 rules.
    """
    
    def extract_class_features(self, raw_data: Dict[str, Any]) -> List[ClassFeature]:
        """
        Extract all class features from character data.
        
        Args:
            raw_data: Raw D&D Beyond character data
            
        Returns:
            List of ClassFeature objects with full details
        """
        try:
            logger.debug("Starting class feature extraction")
            features = []
            
            # Extract features from each class
            classes = raw_data.get('classes', [])
            for class_data in classes:
                class_name = class_data.get('definition', {}).get('name', 'Unknown')
                logger.debug(f"Processing class features for {class_name}")
                
                # Extract class features
                class_features = self._extract_features_from_class(class_data, class_name)
                features.extend(class_features)
                
                # Extract subclass features if available
                subclass_data = class_data.get('subclassDefinition')
                logger.debug(f"DEBUG: Looking for subclass in class_data keys: {list(class_data.keys())}")
                logger.debug(f"DEBUG: subclass_data found: {subclass_data is not None}")
                if subclass_data:
                    subclass_name = subclass_data.get('name', 'Unknown')
                    logger.debug(f"Processing subclass features for {subclass_name}")
                    subclass_features = self._extract_subclass_features(class_data, subclass_name)
                    features.extend(subclass_features)
                else:
                    logger.debug(f"DEBUG: No subclassDefinition found at class level")
            
            logger.info(f"Extracted {len(features)} class features total")
            return features
            
        except Exception as e:
            logger.error(f"Error extracting class features: {e}")
            return []
    
    def _extract_features_from_class(self, class_data: Dict[str, Any], class_name: str) -> List[ClassFeature]:
        """Extract features from a specific class."""
        features = []
        class_features = class_data.get('classFeatures', [])
        class_level = class_data.get('level', 1)
        
        for feature_data in class_features:
            try:
                feature = self._process_feature_data(feature_data, class_name, False)
                if feature and feature.level_required <= class_level:
                    features.append(feature)
            except Exception as e:
                logger.warning(f"Error processing class feature: {e}")
                continue
        
        return features
    
    def _extract_subclass_features(self, class_data: Dict[str, Any], subclass_name: str) -> List[ClassFeature]:
        """Extract features from subclass definition."""
        features = []
        subclass_definition = class_data.get('subclassDefinition', {})
        class_features = subclass_definition.get('classFeatures', [])
        class_level = class_data.get('level', 1)
        
        for feature_data in class_features:
            try:
                feature = self._process_feature_data(feature_data, subclass_name, True)
                if feature and feature.level_required <= class_level:
                    features.append(feature)
            except Exception as e:
                logger.warning(f"Error processing subclass feature: {e}")
                continue
        
        return features
    
    def _process_feature_data(self, feature_data: Dict[str, Any], source_name: str, is_subclass: bool) -> Optional[ClassFeature]:
        """Process individual feature data into ClassFeature model."""
        try:
            # Handle both wrapped (definition) and unwrapped feature data
            definition = feature_data.get('definition', {})
            if not definition:
                # Try using feature_data directly if no definition wrapper
                if 'id' in feature_data and 'name' in feature_data:
                    definition = feature_data
                    logger.debug(f"Processing unwrapped feature data for: {feature_data.get('name')}")
                else:
                    logger.warning(f"Feature data missing both definition and direct fields: {feature_data}")
                    return None
            
            # Extract basic feature information
            feature_id = definition.get('id')
            name = definition.get('name', 'Unknown Feature')
            description = definition.get('description', '')
            snippet = definition.get('snippet', '')
            
            # Extract level requirement
            level_required = definition.get('requiredLevel', 1)
            
            # Extract feature metadata with type conversion
            feature_type = definition.get('featureType')
            if isinstance(feature_type, int):
                feature_type = str(feature_type)
                
            display_order = definition.get('displayOrder')
            hide_in_builder = definition.get('hideInBuilder', False)
            hide_in_sheet = definition.get('hideInSheet', False)
            
            # Extract source information
            source_id = definition.get('sourceId')
            source_page_number = definition.get('sourcePageNumber')
            definition_key = definition.get('definitionKey')
            
            # Extract usage limitations with type checking
            limited_use = definition.get('limitedUse')
            # Convert list to dict if needed or set to None
            if isinstance(limited_use, list):
                if limited_use and isinstance(limited_use[0], dict):
                    # Take first item if it's a list of dicts
                    limited_use = limited_use[0]
                else:
                    limited_use = None
            elif not isinstance(limited_use, dict):
                limited_use = None
                
            activation = definition.get('activation')
            
            # Extract level scaling information
            level_scales = []
            if 'levelScales' in definition:
                level_scales = definition['levelScales']
            elif 'levelScale' in feature_data:
                # Some features have levelScale at the feature level
                level_scales = [feature_data['levelScale']]
            
            # Extract spell lists and creature rules
            spell_list_ids = definition.get('spellListIds', [])
            creature_rules = definition.get('creatureRules', [])
            
            # Create ClassFeature object
            feature = ClassFeature(
                id=feature_id,
                name=name,
                description=description,
                snippet=snippet,
                level_required=level_required,
                is_subclass_feature=is_subclass,
                feature_type=feature_type,
                limited_use=limited_use,
                activation=activation,
                hide_in_builder=hide_in_builder,
                hide_in_sheet=hide_in_sheet,
                display_order=display_order,
                source_id=source_id,
                source_page_number=source_page_number,
                definition_key=definition_key,
                level_scales=level_scales,
                spell_list_ids=spell_list_ids,
                creature_rules=creature_rules
            )
            
            logger.debug(f"Processed feature: {name} (Level {level_required}, Subclass: {is_subclass})")
            return feature
            
        except Exception as e:
            logger.error(f"Error processing feature data: {e}")
            return None
    
    def get_features_by_level(self, features: List[ClassFeature], level: int) -> List[ClassFeature]:
        """Get all features available at or before a specific level."""
        return [f for f in features if f.level_required <= level]
    
    def get_features_by_type(self, features: List[ClassFeature], feature_type: str) -> List[ClassFeature]:
        """Get features by type (e.g., 'feature', 'cantrip', etc.)."""
        return [f for f in features if f.feature_type == feature_type]
    
    def get_subclass_features(self, features: List[ClassFeature]) -> List[ClassFeature]:
        """Get only subclass features."""
        return [f for f in features if f.is_subclass_feature]
    
    def get_features_with_limited_use(self, features: List[ClassFeature]) -> List[ClassFeature]:
        """Get features that have usage limitations."""
        return [f for f in features if f.limited_use is not None]
    
    def calculate(self, character, raw_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Calculate method required by RuleAwareCalculator base class.
        
        Args:
            character: Character model (may be minimal)
            raw_data: Raw D&D Beyond character data
            **kwargs: Additional parameters
        
        Returns class features as a dictionary for JSON serialization.
        """
        features = self.extract_class_features(raw_data)
        
        return {
            'class_features': [feature.model_dump() for feature in features],
            'feature_count': len(features),
            'subclass_feature_count': len(self.get_subclass_features(features)),
            'limited_use_feature_count': len(self.get_features_with_limited_use(features))
        }