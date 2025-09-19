"""
Equipment Details Extractor

Extracts comprehensive equipment information with detailed properties from D&D Beyond API data.
"""

from typing import Dict, Any, List, Optional
import logging

from shared.models.character import EnhancedEquipment, WeaponProperty
from .base import RuleAwareCalculator

logger = logging.getLogger(__name__)


class EquipmentDetailsExtractor(RuleAwareCalculator):
    """
    Extracts equipment with detailed properties from D&D Beyond character data.
    
    Processes all equipment including weapons, armor, and magic items with
    comprehensive property details, descriptions, and special abilities.
    """
    
    def extract_equipment_details(self, raw_data: Dict[str, Any]) -> List[EnhancedEquipment]:
        """
        Extract all equipment with enhanced details from character data.
        
        Args:
            raw_data: Raw D&D Beyond character data
            
        Returns:
            List of EnhancedEquipment objects with full details
        """
        try:
            logger.debug("Starting equipment details extraction")
            equipment_list = []
            
            # Extract from inventory
            inventory = raw_data.get('inventory', [])
            for item_data in inventory:
                try:
                    enhanced_item = self._process_inventory_item(item_data)
                    if enhanced_item:
                        equipment_list.append(enhanced_item)
                except Exception as e:
                    logger.warning(f"Error processing inventory item: {e}")
                    continue
            
            # Extract from custom items if any
            custom_items = raw_data.get('customItems', [])
            for item_data in custom_items:
                try:
                    enhanced_item = self._process_custom_item(item_data)
                    if enhanced_item:
                        equipment_list.append(enhanced_item)
                except Exception as e:
                    logger.warning(f"Error processing custom item: {e}")
                    continue
            
            logger.info(f"Extracted {len(equipment_list)} enhanced equipment items")
            return equipment_list
            
        except Exception as e:
            logger.error(f"Error extracting equipment details: {e}")
            return []
    
    def _process_inventory_item(self, item_data: Dict[str, Any]) -> Optional[EnhancedEquipment]:
        """Process individual inventory item into EnhancedEquipment model."""
        try:
            # Handle both wrapped (definition) and unwrapped item data
            definition = item_data.get('definition', {})
            if not definition:
                # Try using item_data directly if no definition wrapper
                if 'id' in item_data and 'name' in item_data:
                    definition = item_data
                    logger.debug(f"Processing unwrapped item data for: {item_data.get('name')}")
                else:
                    logger.warning(f"Item data missing both definition and direct fields: {item_data}")
                    return None
            
            # Basic item information
            item_id = item_data.get('id')
            name = definition.get('name', 'Unknown Item')
            item_type = definition.get('type', 'Unknown')
            subtype = definition.get('subType')
            
            # Quantities and state
            quantity = item_data.get('quantity', 1)
            weight = definition.get('weight', 0.0)
            cost = definition.get('cost')
            rarity = definition.get('rarity', 'common')
            
            # Equipment state
            equipped = item_data.get('equipped', False)
            attuned = item_data.get('isAttuned', False)
            requires_attunement = definition.get('canAttune', False)
            charges_used = item_data.get('chargesUsed', 0)
            
            # Descriptions
            description = definition.get('description', '')
            snippet = definition.get('snippet', '')
            
            # Magic item properties
            is_magic = definition.get('magic', False)
            attunement_description = definition.get('attunementDescription')
            
            # Container relationships
            container_entity_id = item_data.get('containerEntityId')
            container_entity_type_id = item_data.get('containerEntityTypeId')
            
            # Extract weapon properties
            weapon_properties = self._extract_weapon_properties(definition)
            damage_dice = definition.get('damage', {}).get('diceString') if definition.get('damage') else None
            damage_type = definition.get('damageType')
            weapon_category = self._determine_weapon_category(definition)
            
            # Handle attack_type with type conversion
            attack_type = definition.get('attackType')
            if isinstance(attack_type, int):
                # Map attack type IDs to strings
                attack_type_map = {1: "melee", 2: "ranged"}
                attack_type = attack_type_map.get(attack_type, "unknown")
            
            range_normal = definition.get('range')
            range_long = definition.get('longRange')
            is_monk_weapon = definition.get('isMonkWeapon', False)
            
            # Extract armor properties
            armor_class = definition.get('armorClass')
            strength_requirement = definition.get('strengthRequirement')
            stealth_disadvantage = definition.get('stealthCheck') == 1  # 1 means disadvantage
            armor_type = self._determine_armor_type(definition)
            
            # Extract granted modifiers
            granted_modifiers = definition.get('grantedModifiers', [])
            
            # Source information
            source_id = definition.get('sourceId')
            source_page_number = definition.get('sourcePageNumber')
            definition_key = definition.get('definitionKey')
            
            # D&D Beyond metadata
            entity_type_id = item_data.get('entityTypeId')
            definition_id = item_data.get('definitionId')
            equipped_entity_id = item_data.get('equippedEntityId')
            equipped_entity_type_id = item_data.get('equippedEntityTypeId')
            
            # Create EnhancedEquipment object
            equipment = EnhancedEquipment(
                id=item_id,
                name=name,
                item_type=item_type,
                subtype=subtype,
                quantity=quantity,
                weight=weight,
                cost=cost,
                rarity=rarity,
                equipped=equipped,
                attuned=attuned,
                requires_attunement=requires_attunement,
                charges_used=charges_used,
                description=description,
                snippet=snippet,
                is_magic=is_magic,
                attunement_description=attunement_description,
                container_entity_id=container_entity_id,
                container_entity_type_id=container_entity_type_id,
                weapon_properties=weapon_properties,
                damage_dice=damage_dice,
                damage_type=damage_type,
                weapon_category=weapon_category,
                attack_type=attack_type,
                range_normal=range_normal,
                range_long=range_long,
                is_monk_weapon=is_monk_weapon,
                armor_class=armor_class,
                strength_requirement=strength_requirement,
                stealth_disadvantage=stealth_disadvantage,
                armor_type=armor_type,
                granted_modifiers=granted_modifiers,
                source_id=source_id,
                source_page_number=source_page_number,
                definition_key=definition_key,
                entity_type_id=entity_type_id,
                definition_id=definition_id,
                equipped_entity_id=equipped_entity_id,
                equipped_entity_type_id=equipped_entity_type_id,
                is_custom=False
            )
            
            logger.debug(f"Processed equipment: {name} ({item_type})")
            return equipment
            
        except Exception as e:
            logger.error(f"Error processing inventory item: {e}")
            return None
    
    def _process_custom_item(self, item_data: Dict[str, Any]) -> Optional[EnhancedEquipment]:
        """Process custom item data."""
        try:
            # Custom items have a simpler structure
            name = item_data.get('name', 'Custom Item')
            item_type = item_data.get('type', 'Custom')
            description = item_data.get('description', '')
            quantity = item_data.get('quantity', 1)
            weight = item_data.get('weight', 0.0)
            cost = item_data.get('cost')
            
            equipment = EnhancedEquipment(
                name=name,
                item_type=item_type,
                quantity=quantity,
                weight=weight,
                cost=cost,
                description=description,
                is_custom=True
            )
            
            logger.debug(f"Processed custom equipment: {name}")
            return equipment
            
        except Exception as e:
            logger.error(f"Error processing custom item: {e}")
            return None
    
    def _extract_weapon_properties(self, definition: Dict[str, Any]) -> List[WeaponProperty]:
        """Extract weapon properties from definition."""
        properties = []
        
        weapon_properties = definition.get('properties', [])
        if not weapon_properties:
            return properties
            
        for prop_data in weapon_properties:
            try:
                prop_id = prop_data.get('id')
                prop_name = prop_data.get('name', 'Unknown Property')
                prop_description = prop_data.get('description')
                
                # Extract property-specific values
                damage_value = None
                range_normal = None
                range_long = None
                
                # Handle specific property types
                if 'versatile' in prop_name.lower() and 'damage' in prop_data:
                    damage_value = prop_data.get('damage', {}).get('diceString')
                elif 'range' in prop_name.lower():
                    range_normal = prop_data.get('range')
                    range_long = prop_data.get('longRange')
                
                weapon_prop = WeaponProperty(
                    id=prop_id,
                    name=prop_name,
                    description=prop_description,
                    damage_value=damage_value,
                    range_normal=range_normal,
                    range_long=range_long
                )
                
                properties.append(weapon_prop)
                
            except Exception as e:
                logger.warning(f"Error processing weapon property: {e}")
                continue
        
        return properties
    
    def _determine_weapon_category(self, definition: Dict[str, Any]) -> Optional[str]:
        """Determine weapon category (simple/martial) from definition."""
        category_id = definition.get('categoryId')
        if not category_id:
            return None
        
        # Common D&D Beyond category mappings
        if category_id == 1:  # Simple melee weapons
            return "simple"
        elif category_id == 2:  # Simple ranged weapons
            return "simple"
        elif category_id == 3:  # Martial melee weapons
            return "martial"
        elif category_id == 4:  # Martial ranged weapons
            return "martial"
        else:
            return None
    
    def _determine_armor_type(self, definition: Dict[str, Any]) -> Optional[str]:
        """Determine armor type from definition."""
        armor_type_id = definition.get('armorTypeId')
        if not armor_type_id:
            return None
        
        # Common D&D Beyond armor type mappings
        armor_type_map = {
            1: "light",
            2: "medium", 
            3: "heavy",
            4: "shield"
        }
        
        return armor_type_map.get(armor_type_id)
    
    def get_equipped_items(self, equipment: List[EnhancedEquipment]) -> List[EnhancedEquipment]:
        """Get only equipped items."""
        return [item for item in equipment if item.equipped]
    
    def get_attuned_items(self, equipment: List[EnhancedEquipment]) -> List[EnhancedEquipment]:
        """Get only attuned magic items."""
        return [item for item in equipment if item.attuned]
    
    def get_magic_items(self, equipment: List[EnhancedEquipment]) -> List[EnhancedEquipment]:
        """Get only magic items."""
        return [item for item in equipment if item.is_magic]
    
    def get_weapons(self, equipment: List[EnhancedEquipment]) -> List[EnhancedEquipment]:
        """Get weapon items."""
        weapon_types = ['weapon', 'simple weapon', 'martial weapon']
        return [item for item in equipment if any(wt in item.item_type.lower() for wt in weapon_types)]
    
    def get_armor(self, equipment: List[EnhancedEquipment]) -> List[EnhancedEquipment]:
        """Get armor items."""
        armor_types = ['armor', 'light armor', 'medium armor', 'heavy armor', 'shield']
        return [item for item in equipment if any(at in item.item_type.lower() for at in armor_types)]
    
    def calculate(self, raw_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Calculate method required by RuleAwareCalculator base class.
        
        Returns enhanced equipment as a dictionary for JSON serialization.
        """
        equipment = self.extract_equipment_details(raw_data)
        
        return {
            'enhanced_equipment': [item.model_dump() for item in equipment],
            'equipment_count': len(equipment),
            'equipped_count': len(self.get_equipped_items(equipment)),
            'magic_item_count': len(self.get_magic_items(equipment)),
            'weapon_count': len(self.get_weapons(equipment)),
            'armor_count': len(self.get_armor(equipment))
        }