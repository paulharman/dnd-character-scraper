# Container Inventory Tracking System

The v6.0.0 D&D Beyond Character Scraper includes a comprehensive container inventory tracking system that organizes character equipment within containers, tracks weight distribution, and maintains proper hierarchical relationships.

## Overview

The container tracking system extracts and processes container data from the D&D Beyond API to provide:

- **Nested Container Support**: Proper handling of containers within containers
- **Weight Distribution**: Accurate weight calculations across container hierarchy  
- **Equipment Integration**: Links between equipment and storage locations
- **Container Organization**: Structured organization of items by container
- **API Data Extraction**: Comprehensive container data from D&D Beyond API

## System Architecture

### Core Component

The `ContainerInventoryCalculator` (`src/calculators/container_inventory.py`) handles all container-related processing:

```python
from src.calculators.container_inventory import ContainerInventoryCalculator

calculator = ContainerInventoryCalculator(rule_version)
result = calculator.calculate(raw_data)
```

### Data Models

Container data is represented using these key models:

#### Container Model
```python
class Container:
    container_id: int
    name: str
    capacity_weight: Optional[float]
    capacity_volume: Optional[str]
    items: List[int]  # Item IDs stored in this container
    total_weight: float
    parent_container_id: Optional[int]
```

#### InventoryItem Model
```python
class InventoryItem:
    item_id: int
    name: str
    quantity: int
    weight: float
    container_id: Optional[int]
    equipped: bool
    attuned: bool
```

## API Data Structure

The D&D Beyond API provides container information in the character data:

### Container Definition
```json
{
  "inventory": [
    {
      "id": 12345,
      "definition": {
        "name": "Backpack",
        "type": "Adventuring Gear",
        "capacity": "30 pounds",
        "weight": 5
      },
      "quantity": 1,
      "containerEntityId": null,
      "containerEntityTypeId": null
    }
  ]
}
```

### Item with Container Reference
```json
{
  "inventory": [
    {
      "id": 67890,
      "definition": {
        "name": "Rope, hempen (50 feet)",
        "weight": 10
      },
      "quantity": 1,
      "containerEntityId": 12345,
      "containerEntityTypeId": 1958004211
    }
  ]
}
```

## Container Processing Logic

### 1. Container Identification

The system identifies containers by analyzing item definitions:

```python
def _is_container(self, item_data: Dict[str, Any]) -> bool:
    """Determine if an item is a container based on definition."""
    definition = item_data.get('definition', {})
    
    # Check for explicit container properties
    if definition.get('capacity'):
        return True
    
    # Check container-like names
    container_names = ['bag', 'backpack', 'pouch', 'chest', 'case']
    name = definition.get('name', '').lower()
    
    return any(container_name in name for container_name in container_names)
```

### 2. Container Hierarchy Building

The system builds hierarchical relationships between containers:

```python
def _build_containers(self, inventory_items: List[InventoryItem], 
                     character_id: str) -> Dict[int, Container]:
    """Build container hierarchy from inventory items."""
    containers = {}
    
    for item in inventory_items:
        if self._is_container_item(item):
            container = Container(
                container_id=item.item_id,
                name=item.name,
                capacity_weight=self._extract_weight_capacity(item),
                capacity_volume=self._extract_volume_capacity(item),
                items=[],
                total_weight=item.weight,
                parent_container_id=item.container_id
            )
            containers[item.item_id] = container
    
    return containers
```

### 3. Item Organization

Items are organized by their container relationships:

```python
def _organize_items_by_container(self, inventory_items: List[InventoryItem], 
                               containers: Dict[int, Container]) -> Dict[str, Any]:
    """Organize inventory items by container."""
    organization = {
        'uncontained': [],
        'containers': {}
    }
    
    for item in inventory_items:
        if item.container_id and item.container_id in containers:
            # Item is in a container
            container_id = str(item.container_id)
            if container_id not in organization['containers']:
                organization['containers'][container_id] = []
            organization['containers'][container_id].append(item)
        else:
            # Item is not in a container
            organization['uncontained'].append(item)
    
    return organization
```

### 4. Weight Distribution

The system calculates weight distribution across the container hierarchy:

```python
def _calculate_weight_breakdown(self, containers: Dict[int, Container], 
                              organization: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate weight distribution across containers."""
    weight_breakdown = {
        'total_weight': 0.0,
        'uncontained_weight': 0.0,
        'container_weights': {}
    }
    
    # Calculate uncontained item weights
    for item in organization['uncontained']:
        weight_breakdown['uncontained_weight'] += item.weight * item.quantity
    
    # Calculate container weights (including contents)
    for container_id, container in containers.items():
        container_weight = container.total_weight
        
        # Add weight of items in container
        container_items = organization['containers'].get(str(container_id), [])
        for item in container_items:
            container_weight += item.weight * item.quantity
        
        weight_breakdown['container_weights'][str(container_id)] = {
            'container_name': container.name,
            'container_base_weight': container.total_weight,
            'contents_weight': container_weight - container.total_weight,
            'total_weight': container_weight
        }
    
    # Calculate total weight
    weight_breakdown['total_weight'] = (
        weight_breakdown['uncontained_weight'] + 
        sum(cw['total_weight'] for cw in weight_breakdown['container_weights'].values())
    )
    
    return weight_breakdown
```

## Output Format

The container system produces structured output in the character JSON:

### Container Data Section
```json
{
  "containers": {
    "12345": {
      "container_id": 12345,
      "name": "Backpack",
      "capacity_weight": 30.0,
      "capacity_volume": "1 cubic foot",
      "items": [67890, 54321],
      "total_weight": 25.0,
      "parent_container_id": null
    }
  }
}
```

### Enhanced Inventory Section
```json
{
  "inventory": [
    {
      "item_id": 67890,
      "name": "Rope, hempen (50 feet)",
      "quantity": 1,
      "weight": 10.0,
      "container_id": 12345,
      "container_name": "Backpack",
      "equipped": false,
      "attuned": false
    }
  ]
}
```

### Weight Breakdown Section
```json
{
  "weight_breakdown": {
    "total_weight": 35.0,
    "uncontained_weight": 10.0,
    "container_weights": {
      "12345": {
        "container_name": "Backpack",
        "container_base_weight": 5.0,
        "contents_weight": 20.0,
        "total_weight": 25.0
      }
    }
  }
}
```

## Integration with Character Processing

The container system integrates seamlessly with other character processing components:

### Character Calculator Integration
```python
# In CharacterCalculator.calculate()
container_data = self.container_calculator.calculate(raw_data, rule_version=self.rule_version)

result.update({
    'containers': container_data['containers'],
    'inventory': container_data['inventory_items'],
    'container_organization': container_data['container_organization'],
    'weight_breakdown': container_data['weight_breakdown']
})
```

### Equipment Integration
The equipment details calculator works with container data to provide enhanced equipment organization:

```python
# Equipment can reference container locations
equipment_item = {
    'name': 'Studded Leather Armor',
    'equipped': True,
    'container_id': None,  # Not in a container when equipped
    'storage_location': 'Equipped'
}
```

## Usage Examples

### Basic Container Data Access
```python
# Access container information
containers = character_data['containers']
for container_id, container in containers.items():
    print(f"Container: {container['name']}")
    print(f"Capacity: {container['capacity_weight']} lbs")
    print(f"Items: {len(container['items'])}")
```

### Weight Analysis
```python
# Analyze weight distribution
weight_breakdown = character_data['weight_breakdown']
print(f"Total Weight: {weight_breakdown['total_weight']} lbs")

for container_id, weights in weight_breakdown['container_weights'].items():
    print(f"{weights['container_name']}: {weights['total_weight']} lbs")
```

### Item Location Lookup
```python
# Find items by container
inventory = character_data['inventory']
container_items = {}

for item in inventory:
    container_id = item.get('container_id')
    if container_id:
        if container_id not in container_items:
            container_items[container_id] = []
        container_items[container_id].append(item)
```

## Advanced Features

### Nested Container Support
The system handles containers within containers:

```json
{
  "containers": {
    "bag_of_holding": {
      "container_id": 1001,
      "name": "Bag of Holding",
      "parent_container_id": null,
      "items": [2001]
    },
    "component_pouch": {
      "container_id": 2001,
      "name": "Component Pouch", 
      "parent_container_id": 1001,
      "items": [3001, 3002]
    }
  }
}
```

### Capacity Tracking
The system tracks both weight and volume capacity where available:

```json
{
  "container_id": 12345,
  "name": "Backpack",
  "capacity_weight": 30.0,
  "capacity_volume": "1 cubic foot",
  "current_weight": 25.0,
  "weight_remaining": 5.0
}
```

### Container Type Detection
The system identifies different container types:

- **Bags**: Bag of Holding, component pouches, etc.
- **Backpacks**: Standard adventuring backpacks
- **Cases**: Scroll cases, map cases, etc.
- **Chests**: Storage chests and strongboxes
- **Pouches**: Belt pouches, coin purses, etc.

## Error Handling

The container system includes robust error handling:

### Missing Container References
When an item references a container that doesn't exist:
```python
logger.warning(f"Item {item_id} references unknown container {container_id}")
# Item is treated as uncontained
```

### Invalid Weight Data
When weight data is missing or invalid:
```python
if weight is None or weight < 0:
    logger.warning(f"Invalid weight for item {item_id}, defaulting to 0")
    weight = 0.0
```

### Circular Container References
The system detects and prevents circular container references:
```python
def _detect_circular_reference(self, container_id: int, parent_id: int, 
                              containers: Dict[int, Container]) -> bool:
    """Detect circular references in container hierarchy."""
    visited = set()
    current = parent_id
    
    while current and current not in visited:
        visited.add(current)
        current = containers.get(current, {}).get('parent_container_id')
        
        if current == container_id:
            return True  # Circular reference detected
    
    return False
```

## Performance Considerations

The container system is optimized for performance:

- **Lazy Loading**: Container data is calculated only when needed
- **Caching**: Container relationships are cached during processing
- **Efficient Lookups**: Uses dictionaries for O(1) container lookups
- **Minimal API Calls**: All data extracted from single character API call

## Testing

The container system includes comprehensive testing:

### Unit Tests
```python
def test_container_identification():
    """Test container identification logic."""
    # Test various container types
    
def test_weight_calculation():
    """Test weight distribution calculations."""
    # Test weight calculations with nested containers
    
def test_item_organization():
    """Test item organization by container."""
    # Test proper item-container relationships
```

### Integration Tests
```python
def test_full_container_processing():
    """Test complete container processing pipeline."""
    # Test with real character data
```

## Configuration

Container processing can be configured via YAML:

```yaml
container_processing:
  enabled: true
  track_weight: true
  track_volume: true
  detect_nested: true
  weight_precision: 2
  
container_detection:
  use_name_matching: true
  use_capacity_detection: true
  custom_container_names:
    - "bag"
    - "sack"
    - "case"
```

## Future Enhancements

Potential future enhancements to the container system:

- **Volume Calculations**: Enhanced volume tracking and calculations
- **Container Limits**: Enforcement of weight and volume limits
- **Visual Organization**: ASCII art representation of container contents
- **Export Formats**: Export container organization to various formats
- **Container Suggestions**: AI-powered organization suggestions

The container inventory tracking system provides comprehensive organization and tracking capabilities that enhance the character data extraction and processing experience while maintaining compatibility with existing D&D Beyond data structures.