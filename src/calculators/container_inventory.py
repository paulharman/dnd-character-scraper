"""
Container Inventory Calculator

Handles container relationships and organization for character inventory.
Supports nested containers and proper weight distribution.
"""

from typing import Dict, Any, Optional, List, Tuple
import logging

from .base import RuleAwareCalculator
from src.models.character import InventoryItem, Container

logger = logging.getLogger(__name__)


class ContainerInventoryCalculator(RuleAwareCalculator):
    """
    Calculator for container-based inventory organization.
    
    Extracts container relationships from D&D Beyond API data and organizes
    items by storage location with proper weight tracking.
    """
    
    def calculate(self, raw_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Calculate container inventory organization from raw D&D Beyond data.
        
        Args:
            raw_data: Raw character data from D&D Beyond API
            **kwargs: Additional parameters
                
        Returns:
            Dictionary containing:
                - inventory_items: List of InventoryItem objects
                - containers: Dictionary of Container objects by ID
                - container_organization: Items organized by container
                - weight_breakdown: Weight distribution across containers
        """
        character_id = raw_data.get('id', 'unknown')
        logger.debug(f"Calculating container inventory for character {character_id}")
        
        # Extract inventory items with container data
        inventory_items = self._extract_inventory_items(raw_data)
        
        # Build container hierarchy
        containers = self._build_containers(inventory_items, character_id)
        
        # Organize items by container
        container_organization = self._organize_items_by_container(inventory_items, containers)
        
        # Calculate weight breakdown
        weight_breakdown = self._calculate_weight_breakdown(inventory_items, containers)
        
        result = {
            'inventory_items': [item.model_dump() for item in inventory_items],
            'containers': {str(k): v.model_dump() for k, v in containers.items()},
            'container_organization': container_organization,
            'weight_breakdown': weight_breakdown
        }
        
        logger.debug(f"Character {character_id} has {len(inventory_items)} items in {len(containers)} containers")
        
        return result
    
    def _extract_inventory_items(self, raw_data: Dict[str, Any]) -> List[InventoryItem]:
        """
        Extract inventory items from raw data with container information.
        
        Args:
            raw_data: Raw character data
            
        Returns:
            List of InventoryItem objects with container relationships
        """
        items = []
        
        # Create a mapping of custom items for notes lookup
        # Use multiple fields to create a unique key to handle potential duplicate names
        custom_items_map = {}
        if 'customItems' in raw_data:
            for custom_item in raw_data['customItems']:
                name = custom_item.get('name', '').strip()
                quantity = custom_item.get('quantity', 1)
                weight = custom_item.get('weight')
                cost = custom_item.get('cost')
                
                # Create a composite key using name + quantity + weight + cost
                # This should handle most cases of duplicate names
                key = (name, quantity, weight, cost)
                custom_items_map[key] = custom_item
                
                # Also keep a simple name-based lookup as fallback
                if name and name not in custom_items_map:
                    custom_items_map[name] = custom_item
        
        # Process standard inventory items
        inventory_data = raw_data.get('inventory', [])
        for item_data in inventory_data:
            try:
                # Extract item definition
                definition = item_data.get('definition', {})
                
                # Check if this is a custom item
                is_custom_item = definition.get('isCustomItem', False)
                item_name = definition.get('name', 'Unknown Item')
                
                # Get notes from custom items if this is a custom item
                notes = None
                if is_custom_item:
                    # Try composite key matching first (more precise)
                    item_quantity = item_data.get('quantity', 1)
                    item_weight = definition.get('weight')
                    item_cost = definition.get('cost')
                    composite_key = (item_name.strip(), item_quantity, item_weight, item_cost)
                    
                    if composite_key in custom_items_map:
                        custom_item_data = custom_items_map[composite_key]
                        notes = custom_item_data.get('notes')
                    elif item_name.strip() in custom_items_map:
                        # Fallback to name-only matching
                        custom_item_data = custom_items_map[item_name.strip()]
                        notes = custom_item_data.get('notes')
                
                # Create inventory item
                item = InventoryItem(
                    id=item_data.get('id'),
                    name=item_name,
                    quantity=item_data.get('quantity', 1),
                    weight=definition.get('weight', 0.0) or 0.0,
                    equipped=item_data.get('equipped', False),
                    attuned=item_data.get('isAttuned', False),
                    requires_attunement=definition.get('canAttune', False),
                    
                    # Container relationships (now properly available for custom items)
                    container_entity_id=item_data.get('containerEntityId'),
                    container_entity_type_id=item_data.get('containerEntityTypeId'),
                    container_definition_key=item_data.get('containerDefinitionKey'),
                    
                    # Container metadata (if this item is a container)
                    is_container=definition.get('isContainer', False),
                    capacity_weight=definition.get('capacityWeight', 0.0) or 0.0,
                    capacity_volume=definition.get('capacity'),
                    
                    # Additional properties (handle custom vs regular items)
                    description=definition.get('description', ''),
                    notes=notes,
                    item_type='Custom' if is_custom_item else definition.get('type', 'Item'),
                    rarity=definition.get('rarity', 'Common'),
                    cost=definition.get('cost'),
                    
                    # D&D Beyond specific fields
                    definition_id=definition.get('id'),
                    entity_type_id=item_data.get('entityTypeId'),
                    equipped_entity_id=item_data.get('equippedEntityId'),
                    equipped_entity_type_id=item_data.get('equippedEntityTypeId')
                )
                
                items.append(item)
                
            except Exception as e:
                logger.warning(f"Failed to extract item data: {e}")
                logger.debug(f"Item data: {item_data}")
                continue
        
        # Custom items are now included in the main inventory array with includeCustomItems=true
        # No separate processing needed - they have proper container relationships
        
        return items
    
    def _build_containers(self, items: List[InventoryItem], character_id: int) -> Dict[int, Container]:
        """
        Build container hierarchy from inventory items.
        
        Args:
            items: List of inventory items
            character_id: Character ID for default container
            
        Returns:
            Dictionary of containers by ID
        """
        containers = {}
        
        # Create character container (default storage)
        character_container = Container(
            id=character_id,
            name="Character",
            capacity_weight=0.0,  # Will be calculated by encumbrance calculator
            capacity_volume=None,
            is_character=True
        )
        containers[character_id] = character_container
        
        # Create containers for container items
        for item in items:
            if item.is_container and item.id:
                container = Container(
                    id=item.id,
                    name=item.name,
                    capacity_weight=item.capacity_weight,
                    capacity_volume=item.capacity_volume,
                    is_character=False
                )
                containers[item.id] = container
        
        return containers
    
    def _organize_items_by_container(self, items: List[InventoryItem], 
                                   containers: Dict[int, Container]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Organize items by their container location.
        
        Args:
            items: List of inventory items
            containers: Dictionary of containers
            
        Returns:
            Dictionary organizing items by container name
        """
        organization = {}
        
        for item in items:
            # Determine which container this item belongs to
            container_id = item.container_entity_id
            if container_id is None:
                # Item is on character directly
                container_id = next(iter(containers.keys()))  # Character container
            
            # Find container name
            container_name = "character"
            if container_id in containers:
                container = containers[container_id]
                container_name = container.name.lower().replace(" ", "_")
                
                # Add item to container's item list
                if item.id and item.id not in container.items:
                    container.items.append(item.id)
            
            # Add to organization
            if container_name not in organization:
                organization[container_name] = []
            
            # Create item summary for organization
            item_summary = {
                'id': item.id,
                'name': item.name,
                'quantity': item.quantity,
                'weight': item.weight,
                'equipped': item.equipped,
                'total_weight': item.weight * item.quantity
            }
            
            organization[container_name].append(item_summary)
        
        return organization
    
    def _calculate_weight_breakdown(self, items: List[InventoryItem], 
                                  containers: Dict[int, Container]) -> Dict[str, Any]:
        """
        Calculate weight distribution across containers.
        
        Args:
            items: List of inventory items
            containers: Dictionary of containers
            
        Returns:
            Weight breakdown with container utilization
        """
        breakdown = {
            'total_weight': 0.0,
            'containers': {},
            'uncontained_weight': 0.0
        }
        
        # Calculate weight by container
        for item in items:
            item_weight = item.weight * item.quantity
            breakdown['total_weight'] += item_weight
            
            # Determine container
            container_id = item.container_entity_id
            if container_id is None:
                container_id = next(iter(containers.keys()))  # Character container
            
            if container_id in containers:
                container = containers[container_id]
                container_name = container.name.lower().replace(" ", "_")
                
                # Update container current weight
                container.current_weight += item_weight
                
                # Add to breakdown
                if container_name not in breakdown['containers']:
                    breakdown['containers'][container_name] = {
                        'weight': 0.0,
                        'capacity': container.capacity_weight,
                        'utilization': container.get_utilization_text(),
                        'utilization_percentage': 0.0,
                        'is_character': container.is_character
                    }
                
                breakdown['containers'][container_name]['weight'] += item_weight
                breakdown['containers'][container_name]['utilization_percentage'] = \
                    container.get_utilization_percentage()
            else:
                breakdown['uncontained_weight'] += item_weight
        
        return breakdown
    
    def get_container_contents(self, container_id: int, items: List[InventoryItem]) -> List[InventoryItem]:
        """
        Get all items in a specific container.
        
        Args:
            container_id: Container ID to search
            items: List of all inventory items
            
        Returns:
            List of items in the container
        """
        return [item for item in items if item.container_entity_id == container_id]
    
    def get_item_location(self, item_id: int, containers: Dict[int, Container]) -> Optional[Container]:
        """
        Find which container an item is stored in.
        
        Args:
            item_id: Item ID to search for
            containers: Dictionary of containers
            
        Returns:
            Container containing the item, or None if not found
        """
        for container in containers.values():
            if item_id in container.items:
                return container
        return None