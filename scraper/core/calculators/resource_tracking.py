"""
Resource Tracking Extractor

Extracts resource pools and usage tracking from D&D Beyond API data.
"""

from typing import Dict, Any, List, Optional
import logging

from shared.models.character import ResourcePool
from .base import RuleAwareCalculator

logger = logging.getLogger(__name__)


class ResourceTrackingExtractor(RuleAwareCalculator):
    """
    Extracts resource pools and usage tracking from D&D Beyond character data.
    
    Processes spell slots, class feature uses, and other limited-use resources
    with their current state and recovery mechanics.
    """
    
    def extract_resource_pools(self, raw_data: Dict[str, Any]) -> List[ResourcePool]:
        """
        Extract all resource pools from character data.
        
        Args:
            raw_data: Raw D&D Beyond character data
            
        Returns:
            List of ResourcePool objects with current state
        """
        try:
            logger.debug("Starting resource tracking extraction")
            resource_pools = []
            
            # Extract spell slots
            spell_slot_pools = self._extract_spell_slots(raw_data)
            resource_pools.extend(spell_slot_pools)
            
            # Extract pact magic slots
            pact_magic_pools = self._extract_pact_magic(raw_data)
            resource_pools.extend(pact_magic_pools)
            
            # Extract hit dice
            hit_dice_pools = self._extract_hit_dice(raw_data)
            resource_pools.extend(hit_dice_pools)
            
            # Extract class feature uses
            feature_use_pools = self._extract_feature_uses(raw_data)
            resource_pools.extend(feature_use_pools)
            
            logger.info(f"Extracted {len(resource_pools)} resource pools")
            return resource_pools
            
        except Exception as e:
            logger.error(f"Error extracting resource pools: {e}")
            return []
    
    def _extract_spell_slots(self, raw_data: Dict[str, Any]) -> List[ResourcePool]:
        """Extract spell slot resources."""
        pools = []
        
        try:
            spell_slots = raw_data.get('spellSlots', [])
            
            for slot_data in spell_slots:
                level = slot_data.get('level', 1)
                available = slot_data.get('available', 0)
                used = slot_data.get('used', 0)
                
                if available > 0:  # Only create pools for levels with slots
                    pool = ResourcePool(
                        name=f"Spell Slots (Level {level})",
                        resource_type="spell_slot",
                        level=level,
                        maximum=available,
                        current=available - used,
                        used=used,
                        recovery_type="long_rest",
                        source_type="class"
                    )
                    pools.append(pool)
                    logger.debug(f"Added spell slot pool: Level {level} ({available - used}/{available})")
            
        except Exception as e:
            logger.warning(f"Error extracting spell slots: {e}")
        
        return pools
    
    def _extract_pact_magic(self, raw_data: Dict[str, Any]) -> List[ResourcePool]:
        """Extract pact magic slot resources."""
        pools = []
        
        try:
            pact_magic = raw_data.get('pactMagic', [])
            
            for pact_data in pact_magic:
                level = pact_data.get('level', 1)
                available = pact_data.get('available', 0)
                used = pact_data.get('used', 0)
                
                if available > 0:
                    pool = ResourcePool(
                        name=f"Pact Magic Slots (Level {level})",
                        resource_type="pact_slot",
                        level=level,
                        maximum=available,
                        current=available - used,
                        used=used,
                        recovery_type="short_rest",
                        source_class="Warlock",
                        source_type="class"
                    )
                    pools.append(pool)
                    logger.debug(f"Added pact magic pool: Level {level} ({available - used}/{available})")
            
        except Exception as e:
            logger.warning(f"Error extracting pact magic: {e}")
        
        return pools
    
    def _extract_hit_dice(self, raw_data: Dict[str, Any]) -> List[ResourcePool]:
        """Extract hit dice resources."""
        pools = []
        
        try:
            classes = raw_data.get('classes', [])
            
            for class_data in classes:
                class_name = class_data.get('definition', {}).get('name', 'Unknown')
                class_level = class_data.get('level', 1)
                hit_dice_used = class_data.get('hitDiceUsed', 0)
                hit_die_type = class_data.get('definition', {}).get('hitDie', 8)
                
                available = class_level
                current = available - hit_dice_used
                
                pool = ResourcePool(
                    name=f"Hit Dice (d{hit_die_type})",
                    resource_type="hit_dice",
                    maximum=available,
                    current=current,
                    used=hit_dice_used,
                    recovery_type="long_rest",
                    recovery_amount=available // 2,  # Recover half on long rest (minimum 1)
                    source_class=class_name,
                    source_type="class"
                )
                pools.append(pool)
                logger.debug(f"Added hit dice pool for {class_name}: d{hit_die_type} ({current}/{available})")
            
        except Exception as e:
            logger.warning(f"Error extracting hit dice: {e}")
        
        return pools
    
    def _extract_feature_uses(self, raw_data: Dict[str, Any]) -> List[ResourcePool]:
        """Extract class feature usage resources."""
        pools = []
        
        try:
            # Look for limited use features in class features
            classes = raw_data.get('classes', [])
            
            for class_data in classes:
                class_name = class_data.get('definition', {}).get('name', 'Unknown')
                class_features = class_data.get('classFeatures', [])
                
                for feature_data in class_features:
                    definition = feature_data.get('definition', {})
                    limited_use = definition.get('limitedUse')
                    
                    if limited_use:
                        feature_name = definition.get('name', 'Unknown Feature')
                        pool = self._create_feature_use_pool(feature_name, limited_use, class_name)
                        if pool:
                            pools.append(pool)
                
                # Check subclass features
                subclass_definition = class_data.get('subclassDefinition', {})
                subclass_features = subclass_definition.get('classFeatures', [])
                subclass_name = subclass_definition.get('name', 'Unknown')
                
                for feature_data in subclass_features:
                    definition = feature_data.get('definition', {})
                    limited_use = definition.get('limitedUse')
                    
                    if limited_use:
                        feature_name = definition.get('name', 'Unknown Feature')
                        pool = self._create_feature_use_pool(feature_name, limited_use, subclass_name)
                        if pool:
                            pools.append(pool)
            
            # Look for racial feature uses
            race = raw_data.get('race', {})
            if race:
                racial_traits = race.get('racialTraits', [])
                
                for trait_data in racial_traits:
                    if trait_data:  # Check if trait_data is not None
                        definition = trait_data.get('definition', {})
                        limited_use = definition.get('limitedUse')
                        
                        if limited_use:
                            trait_name = definition.get('name', 'Unknown Trait')
                            pool = self._create_feature_use_pool(trait_name, limited_use, 'Racial Trait')
                            if pool:
                                pools.append(pool)
            
        except Exception as e:
            logger.warning(f"Error extracting feature uses: {e}")
        
        return pools
    
    def _create_feature_use_pool(self, feature_name: str, limited_use: Dict[str, Any], source: str) -> Optional[ResourcePool]:
        """Create a ResourcePool from limited use data."""
        try:
            # Handle case where limited_use might be a list
            if isinstance(limited_use, list):
                if not limited_use:
                    return None
                limited_use = limited_use[0]  # Take first item
            
            if not isinstance(limited_use, dict):
                return None
                
            max_uses = limited_use.get('maxUses', 0)
            number_used = limited_use.get('numberUsed', 0)
            reset_type = limited_use.get('resetType', 'long_rest')
            
            if max_uses <= 0:
                return None
            
            # Map reset types to recovery types
            recovery_type_map = {
                'short_rest': 'short_rest',
                'long_rest': 'long_rest',
                'dawn': 'dawn',
                'manual': 'manual'
            }
            
            recovery_type = recovery_type_map.get(reset_type, 'long_rest')
            
            pool = ResourcePool(
                name=feature_name,
                resource_type="feature_use",
                maximum=max_uses,
                current=max_uses - number_used,
                used=number_used,
                recovery_type=recovery_type,
                source_feature=feature_name,
                source_class=source,
                source_type="class" if source not in ['Racial Trait'] else "race"
            )
            
            logger.debug(f"Added feature use pool: {feature_name} ({max_uses - number_used}/{max_uses})")
            return pool
            
        except Exception as e:
            logger.warning(f"Error creating feature use pool for {feature_name}: {e}")
            return None
    
    def get_pools_by_type(self, pools: List[ResourcePool], resource_type: str) -> List[ResourcePool]:
        """Get resource pools by type."""
        return [pool for pool in pools if pool.resource_type == resource_type]
    
    def get_pools_by_recovery_type(self, pools: List[ResourcePool], recovery_type: str) -> List[ResourcePool]:
        """Get resource pools by recovery type."""
        return [pool for pool in pools if pool.recovery_type == recovery_type]
    
    def get_depleted_pools(self, pools: List[ResourcePool]) -> List[ResourcePool]:
        """Get resource pools that are completely used up."""
        return [pool for pool in pools if pool.current <= 0]
    
    def get_available_pools(self, pools: List[ResourcePool]) -> List[ResourcePool]:
        """Get resource pools that have uses remaining."""
        return [pool for pool in pools if pool.current > 0]
    
    def calculate(self, raw_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Calculate method required by RuleAwareCalculator base class.
        
        Returns resource pools as a dictionary for JSON serialization.
        """
        pools = self.extract_resource_pools(raw_data)
        
        return {
            'resource_pools': [pool.model_dump() for pool in pools],
            'total_pools': len(pools),
            'spell_slot_pools': len(self.get_pools_by_type(pools, 'spell_slot')),
            'feature_use_pools': len(self.get_pools_by_type(pools, 'feature_use')),
            'hit_dice_pools': len(self.get_pools_by_type(pools, 'hit_dice')),
            'depleted_pools': len(self.get_depleted_pools(pools)),
            'available_pools': len(self.get_available_pools(pools))
        }