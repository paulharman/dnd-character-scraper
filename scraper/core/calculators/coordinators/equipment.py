"""
Equipment Coordinator

Coordinates the calculation of equipment, inventory, containers, wealth, and encumbrance
with comprehensive support for all equipment-related aspects of a character.
"""

from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass, asdict

from ..interfaces.coordination import ICoordinator
from ..utils.performance import monitor_performance
from ..services.interfaces import CalculationContext, CalculationResult, CalculationStatus
from ..encumbrance import EnhancedEncumbranceCalculator
from ..utils.data_transformer import EnhancedCalculatorDataTransformer

logger = logging.getLogger(__name__)


@dataclass
class PartyInventoryData:
    """Data class for party inventory results."""
    party_items: List[Dict[str, Any]]
    party_currency: Dict[str, int]
    sharing_state: int
    modifiers: Dict[str, Any]
    spells: Dict[str, Any]
    party_values: List[Any]
    party_infusions: List[Any]
    party_restrictions: List[Any]
    campaign_id: Optional[int] = None


@dataclass
class InfusionsData:
    """Data class for infusion results."""
    active_infusions: List[Dict[str, Any]]
    known_infusions: List[Dict[str, Any]]
    infusion_slots_used: int
    infusion_slots_total: int
    metadata: Dict[str, Any]


@dataclass
class EquipmentData:
    """Data class for equipment calculation results."""
    basic_equipment: List[Dict[str, Any]]
    enhanced_equipment: List[Dict[str, Any]]
    container_inventory: Dict[str, Any]
    wealth: Dict[str, Any]
    encumbrance: Dict[str, Any]
    equipment_summary: Dict[str, Any]
    party_inventory: Optional[PartyInventoryData]
    infusions: Optional[InfusionsData]
    metadata: Dict[str, Any]


class EquipmentCoordinator(ICoordinator):
    """
    Coordinates equipment and inventory calculations with comprehensive support.
    
    This coordinator handles:
    - Basic equipment extraction and processing
    - Enhanced equipment details with properties
    - Container inventory organization
    - Wealth calculation and currency management
    - Encumbrance tracking based on weight and capacity
    - Equipment categorization and filtering
    - Magic item and attunement tracking
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize the equipment coordinator.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize enhanced calculator and data transformer
        self.enhanced_encumbrance_calculator = EnhancedEncumbranceCalculator()
        self.data_transformer = EnhancedCalculatorDataTransformer()
        
        # Currency conversion rates to gold pieces
        self.currency_to_gp = {
            'pp': 10.0,   # 1 platinum = 10 gold
            'gp': 1.0,    # 1 gold = 1 gold
            'ep': 0.5,    # 1 electrum = 0.5 gold
            'sp': 0.1,    # 1 silver = 0.1 gold
            'cp': 0.01    # 1 copper = 0.01 gold
        }
    
    @property
    def coordinator_name(self) -> str:
        """Get the coordinator name."""
        return "equipment"
    
    @property
    def dependencies(self) -> List[str]:
        """Get the list of dependencies."""
        return ["character_info", "abilities"]  # Depends on character info and abilities for encumbrance
    
    @property
    def priority(self) -> int:
        """Get the execution priority (lower = higher priority)."""
        return 60  # Low priority - depends on character info and abilities
    
    @monitor_performance("equipment_coordinate")
    def coordinate(self, raw_data: Dict[str, Any], context: CalculationContext) -> CalculationResult:
        """
        Coordinate the calculation of equipment and inventory.
        
        Args:
            raw_data: Raw character data from D&D Beyond
            context: Calculation context
            
        Returns:
            CalculationResult with equipment data
        """
        self.logger.info(f"Coordinating equipment calculation for character {raw_data.get('id', 'unknown')}")
        
        try:
            # Extract basic equipment
            basic_equipment = self._extract_basic_equipment(raw_data)
            
            # Extract enhanced equipment with detailed properties
            enhanced_equipment = self._extract_enhanced_equipment(raw_data)
            
            # Calculate container inventory organization
            container_inventory = self._calculate_container_inventory(raw_data)
            
            # Calculate wealth
            wealth = self._calculate_wealth(raw_data)
            
            # Calculate encumbrance
            encumbrance = self._calculate_encumbrance(raw_data, context)
            
            # Fetch party inventory if available
            party_inventory = self._process_party_inventory(raw_data)

            # Process infusions if available
            infusions = self._process_infusions(raw_data)

            # Generate equipment summary
            equipment_summary = self._generate_equipment_summary(
                basic_equipment, enhanced_equipment, container_inventory, wealth, encumbrance, party_inventory, infusions
            )

            # Create result data
            result_data = {
                'basic_equipment': basic_equipment,
                'enhanced_equipment': enhanced_equipment,
                'container_inventory': container_inventory,
                'wealth': wealth,
                'encumbrance': encumbrance,
                'equipment_summary': equipment_summary,
                'party_inventory': asdict(party_inventory) if party_inventory else None,
                'infusions': asdict(infusions) if infusions else None,
                'metadata': {
                    'total_items': len(basic_equipment),
                    'equipped_items': len([e for e in enhanced_equipment if e.get('equipped', False)]),
                    'magic_items': len([e for e in enhanced_equipment if e.get('is_magic', False)]),
                    'attuned_items': len([e for e in enhanced_equipment if e.get('attuned', False)]),
                    'containers': len(container_inventory.get('containers', {})),
                    'total_weight': encumbrance.get('total_weight', 0),
                    'encumbrance_level': encumbrance.get('encumbrance_level', 0),
                    'total_wealth_gp': wealth.get('total_gp', 0),
                    'has_containers': len(container_inventory.get('containers', {})) > 1,
                    'has_infusions': infusions is not None and (len(infusions.active_infusions) > 0 or len(infusions.known_infusions) > 0) if infusions else False
                }
            }
            
            self.logger.info(f"Successfully calculated equipment. Items: {len(basic_equipment)}, Weight: {encumbrance.get('total_weight', 0)}")
            
            return CalculationResult(
                service_name=self.coordinator_name,
                status=CalculationStatus.COMPLETED,
                data=result_data,
                errors=[],
                warnings=[]
            )
            
        except Exception as e:
            self.logger.error(f"Error coordinating equipment calculation: {str(e)}")
            return CalculationResult(
                service_name=self.coordinator_name,
                status=CalculationStatus.FAILED,
                data={},
                errors=[f"Equipment calculation failed: {str(e)}"]
            )

    def _process_party_inventory(self, raw_data: Dict[str, Any]) -> Optional[PartyInventoryData]:
        """Process party inventory data if available."""
        party_data = raw_data.get('party_inventory')
        if not party_data:
            return None

        try:
            # Extract campaign ID from raw data
            campaign_id = raw_data.get('campaign', {}).get('id')

            # Process party items
            party_items = []
            for item in party_data.get('partyItems', []):
                processed_item = {
                    'id': item.get('id'),
                    'name': item.get('definition', {}).get('name', 'Unknown'),
                    'type': item.get('definition', {}).get('type', 'Unknown'),
                    'quantity': item.get('quantity', 1),
                    'weight': item.get('definition', {}).get('weight', 0),
                    'description': item.get('definition', {}).get('description', ''),
                    'is_magic': item.get('definition', {}).get('magic', False),
                    'rarity': item.get('definition', {}).get('rarity'),
                    'cost': item.get('definition', {}).get('cost'),
                    'definition': item.get('definition', {})
                }
                party_items.append(processed_item)

            # Create PartyInventoryData object
            party_inventory = PartyInventoryData(
                party_items=party_items,
                party_currency=party_data.get('currency', {}),
                sharing_state=party_data.get('sharingState', 0),
                modifiers=party_data.get('modifiers', {}),
                spells=party_data.get('spells', {}),
                party_values=party_data.get('partyValues', []),
                party_infusions=party_data.get('partyInfusions', []),
                party_restrictions=party_data.get('partyRestrictions', []),
                campaign_id=campaign_id
            )

            self.logger.info(f"Processed party inventory: {len(party_items)} items, {party_inventory.party_currency} currency")
            return party_inventory

        except Exception as e:
            self.logger.error(f"Error processing party inventory: {str(e)}")
            return None

    def _process_infusions(self, raw_data: Dict[str, Any]) -> Optional[InfusionsData]:
        """Process infusion data if available."""
        infusions_data = raw_data.get('infusions')
        known_infusions_data = raw_data.get('known_infusions')

        # If no infusion data available, return None
        if not infusions_data and not known_infusions_data:
            return None

        try:
            # Process active infusions
            active_infusions = []
            infusion_slots_used = 0

            if infusions_data:
                for item in infusions_data.get('items', []):
                    processed_infusion = {
                        'id': item.get('id'),
                        'name': item.get('definition', {}).get('name', 'Unknown'),
                        'type': item.get('definition', {}).get('type', 'Unknown'),
                        'rarity': item.get('definition', {}).get('rarity'),
                        'infused_item_name': item.get('infusedItem', {}).get('definition', {}).get('name', 'Unknown'),
                        'infused_item_id': item.get('infusedItem', {}).get('id'),
                        'description': item.get('definition', {}).get('description', ''),
                        'is_magic': item.get('definition', {}).get('magic', True),  # Infusions are typically magical
                        'requires_attunement': item.get('definition', {}).get('canAttune', False),
                        'definition': item.get('definition', {})
                    }
                    active_infusions.append(processed_infusion)
                    infusion_slots_used += 1

            # Process known infusions
            known_infusions = []
            if known_infusions_data:
                for infusion in known_infusions_data.get('infusions', []):
                    processed_known = {
                        'id': infusion.get('id'),
                        'name': infusion.get('definition', {}).get('name', 'Unknown'),
                        'description': infusion.get('definition', {}).get('description', ''),
                        'level_requirement': infusion.get('definition', {}).get('levelRequirement', 1),
                        'source': infusion.get('definition', {}).get('sources', []),
                        'definition': infusion.get('definition', {})
                    }
                    known_infusions.append(processed_known)

            # Calculate total infusion slots based on Artificer levels
            character_classes = raw_data.get('classes', [])
            artificer_levels = 0

            for cls in character_classes:
                class_name = cls.get('definition', {}).get('name', '')
                subclass_name = cls.get('subclassDefinition', {}).get('name', '')

                # Check for Artificer main class
                if class_name == 'Artificer':
                    artificer_levels += cls.get('level', 0)
                # Check for subclasses that grant infusions
                elif any(keyword in subclass_name.lower() for keyword in ['artificer', 'infusion']):
                    artificer_levels += cls.get('level', 0)

            # Artificer infusion slots by level (simplified)
            if artificer_levels >= 18:
                infusion_slots_total = 6
            elif artificer_levels >= 14:
                infusion_slots_total = 5
            elif artificer_levels >= 10:
                infusion_slots_total = 4
            elif artificer_levels >= 6:
                infusion_slots_total = 3
            elif artificer_levels >= 2:
                infusion_slots_total = 2
            else:
                infusion_slots_total = 0

            # Create InfusionsData object
            infusions = InfusionsData(
                active_infusions=active_infusions,
                known_infusions=known_infusions,
                infusion_slots_used=infusion_slots_used,
                infusion_slots_total=infusion_slots_total,
                metadata={
                    'artificer_levels': artificer_levels,
                    'total_active': len(active_infusions),
                    'total_known': len(known_infusions),
                    'slots_available': infusion_slots_total - infusion_slots_used
                }
            )

            self.logger.info(f"Processed infusions: {len(active_infusions)} active, {len(known_infusions)} known")
            return infusions

        except Exception as e:
            self.logger.error(f"Error processing infusions: {str(e)}")
            return None

    def _extract_basic_equipment(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract basic equipment information."""
        equipment = []
        
        # Extract from inventory (preferred) or container_inventory (fallback)
        inventory = raw_data.get('inventory', [])
        
        # Ensure inventory is not None
        if inventory is None:
            inventory = []
        
        # If no basic inventory, try to extract from container_inventory
        if not inventory:
            container_inventory = raw_data.get('container_inventory', {})
            inventory = self._extract_inventory_from_containers(container_inventory)
        
        # Ensure inventory is iterable
        if inventory is None:
            inventory = []
        
        for item_data in inventory:
            try:
                definition = item_data.get('definition', {})
                
                item = {
                    'id': item_data.get('id'),
                    'name': definition.get('name', 'Unknown Item'),
                    'item_type': definition.get('type', 'Unknown'),
                    'quantity': item_data.get('quantity', 1),
                    'weight': definition.get('weight', 0.0) or 0.0,
                    'cost': definition.get('cost'),
                    'rarity': definition.get('rarity', 'common'),
                    'equipped': item_data.get('equipped', False),
                    'description': definition.get('description', ''),
                    'is_magic': definition.get('magic', False),
                    'requires_attunement': definition.get('canAttune', False),
                    'attuned': item_data.get('isAttuned', False),
                    'container_entity_id': item_data.get('containerEntityId'),
                    'total_weight': (definition.get('weight', 0.0) or 0.0) * item_data.get('quantity', 1)
                }
                
                equipment.append(item)
                
            except Exception as e:
                self.logger.warning(f"Error processing equipment item: {e}")
                continue
        
        return equipment
    
    def _extract_inventory_from_containers(self, container_inventory: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract inventory items from container_inventory structure."""
        inventory = []
        
        try:
            # Get container organization which has the detailed item information
            container_organization = container_inventory.get('container_organization', {})
            containers = container_inventory.get('containers', {})
            
            # Process items from each container
            for container_name, items in container_organization.items():
                # Ensure items is not None
                if items is None:
                    continue
                
                # Determine container ID for this container
                container_id = None
                if container_name != 'character':
                    # Find the container ID by matching name
                    for cid, container_data in containers.items():
                        if (container_data.get('name') or '').lower().replace(' ', '_') == container_name:
                            container_id = cid
                            break
                
                # Process each item in this container
                for item_data in items:
                    inventory_item = {
                        'id': item_data.get('id'),
                        'containerEntityId': container_id,
                        'equipped': item_data.get('equipped', False),
                        'quantity': item_data.get('quantity', 1),
                        'definition': {
                            'name': item_data.get('name', 'Unknown Item'),
                            'type': item_data.get('type', 'Unknown'),
                            'weight': item_data.get('weight', 0.0),
                            'description': item_data.get('description', ''),
                            'rarity': item_data.get('rarity', 'common'),
                            'cost': item_data.get('cost'),
                            'magic': item_data.get('is_magic', False),
                            'canAttune': item_data.get('requires_attunement', False)
                        }
                    }
                    
                    # Add attunement status if applicable
                    if item_data.get('requires_attunement', False):
                        inventory_item['isAttuned'] = item_data.get('attuned', False)
                    
                    inventory.append(inventory_item)
            
            self.logger.info(f"Extracted {len(inventory)} items from container_inventory structure")
            
        except Exception as e:
            self.logger.warning(f"Error extracting inventory from containers: {e}")
        
        return inventory
    
    def _extract_enhanced_equipment(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract enhanced equipment with detailed properties."""
        enhanced_equipment = []
        
        # Extract from inventory (preferred) or container_inventory (fallback)
        inventory = raw_data.get('inventory', [])
        
        # Ensure inventory is not None
        if inventory is None:
            inventory = []
        
        # If no basic inventory, try to extract from container_inventory
        if not inventory:
            container_inventory = raw_data.get('container_inventory', {})
            inventory = self._extract_inventory_from_containers(container_inventory)
        
        # Ensure inventory is iterable
        if inventory is None:
            inventory = []
        
        for item_data in inventory:
            try:
                definition = item_data.get('definition', {})
                
                # Basic information
                item = {
                    'id': item_data.get('id'),
                    'name': definition.get('name', 'Unknown Item'),
                    'item_type': definition.get('type', 'Unknown'),
                    'subtype': definition.get('subType'),
                    'quantity': item_data.get('quantity', 1),
                    'weight': definition.get('weight', 0.0) or 0.0,
                    'cost': definition.get('cost'),
                    'rarity': definition.get('rarity', 'common'),
                    'equipped': item_data.get('equipped', False),
                    'attuned': item_data.get('isAttuned', False),
                    'requires_attunement': definition.get('canAttune', False),
                    'description': definition.get('description', ''),
                    'snippet': definition.get('snippet', ''),
                    'is_magic': definition.get('magic', False),
                    'is_custom': definition.get('isCustomItem', False),
                    
                    # Container information
                    'container_entity_id': item_data.get('containerEntityId'),
                    'is_container': definition.get('isContainer', False),
                    'capacity_weight': definition.get('capacityWeight', 0.0) or 0.0,
                    
                    # Weapon properties
                    'weapon_properties': self._extract_weapon_properties(definition),
                    'damage_dice': definition.get('damage', {}).get('diceString') if definition.get('damage') else None,
                    'damage_type': definition.get('damageType'),
                    'attack_type': self._convert_attack_type(definition.get('attackType')),
                    'weapon_category': self._determine_weapon_category(definition.get('categoryId')),
                    'range_normal': definition.get('range'),
                    'range_long': definition.get('longRange'),
                    'is_monk_weapon': definition.get('isMonkWeapon', False),
                    
                    # Armor properties
                    'armor_class': definition.get('armorClass'),
                    'armor_type': self._determine_armor_type(definition.get('armorTypeId')),
                    'strength_requirement': definition.get('strengthRequirement'),
                    'stealth_disadvantage': definition.get('stealthCheck') == 1,
                    
                    # Modifiers and enhancements
                    'granted_modifiers': definition.get('grantedModifiers', []),
                    'charges_used': item_data.get('chargesUsed', 0),
                    
                    # Source information
                    'source_id': definition.get('sourceId'),
                    'source_page_number': definition.get('sourcePageNumber'),
                    'definition_key': definition.get('definitionKey')
                }
                
                enhanced_equipment.append(item)
                
            except Exception as e:
                self.logger.warning(f"Error processing enhanced equipment item: {e}")
                continue
        
        return enhanced_equipment
    
    def _calculate_container_inventory(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate container inventory organization."""
        try:
            # Create containers map
            containers = {}
            character_id = raw_data.get('id', 0)
            
            # Character container (default)
            containers[character_id] = {
                'id': character_id,
                'name': 'Character',
                'capacity_weight': 0.0,
                'current_weight': 0.0,
                'is_character': True,
                'items': []
            }
            
            # Find container items
            inventory = raw_data.get('inventory', [])
            # Ensure inventory is not None
            if inventory is None:
                inventory = []
            
            for item_data in inventory:
                definition = item_data.get('definition', {})
                if definition.get('isContainer', False):
                    containers[item_data.get('id')] = {
                        'id': item_data.get('id'),
                        'name': definition.get('name', 'Container'),
                        'capacity_weight': definition.get('capacityWeight', 0.0) or 0.0,
                        'current_weight': 0.0,
                        'is_character': False,
                        'items': []
                    }
            
            # Organize items by container
            container_organization = {}
            # Ensure inventory is still not None for second iteration
            if inventory is None:
                inventory = []
            
            for item_data in inventory:
                definition = item_data.get('definition', {})
                item_weight = (definition.get('weight', 0.0) or 0.0) * item_data.get('quantity', 1)
                
                container_id = item_data.get('containerEntityId', character_id)
                if container_id not in containers:
                    container_id = character_id
                
                container = containers[container_id]
                container['current_weight'] += item_weight
                container['items'].append(item_data.get('id'))
                
                container_name = (container['name'] or 'unknown').lower().replace(' ', '_')
                if container_name not in container_organization:
                    container_organization[container_name] = []
                
                container_organization[container_name].append({
                    'id': item_data.get('id'),
                    'name': definition.get('name', 'Unknown Item'),
                    'quantity': item_data.get('quantity', 1),
                    'weight': definition.get('weight', 0.0) or 0.0,
                    'total_weight': item_weight,
                    'equipped': item_data.get('equipped', False)
                })
            
            # Calculate weight breakdown
            weight_breakdown = {
                'total_weight': 0.0,
                'containers': {},
                'uncontained_weight': 0.0
            }
            
            for container_id, container in containers.items():
                weight_breakdown['total_weight'] += container['current_weight']
                container_name = (container['name'] or 'unknown').lower().replace(' ', '_')
                
                utilization_percentage = 0.0
                if container['capacity_weight'] > 0:
                    utilization_percentage = (container['current_weight'] / container['capacity_weight']) * 100
                
                weight_breakdown['containers'][container_name] = {
                    'weight': container['current_weight'],
                    'capacity': container['capacity_weight'],
                    'utilization_percentage': round(utilization_percentage, 1),
                    'is_character': container['is_character']
                }
            
            return {
                'containers': containers,
                'container_organization': container_organization,
                'weight_breakdown': weight_breakdown
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating container inventory: {e}")
            return {
                'containers': {},
                'container_organization': {},
                'weight_breakdown': {'total_weight': 0.0, 'containers': {}, 'uncontained_weight': 0.0}
            }
    
    def _calculate_wealth(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate character wealth."""
        try:
            currencies = raw_data.get('currencies', {})
            
            wealth = {
                'copper': currencies.get('cp', 0),
                'silver': currencies.get('sp', 0),
                'electrum': currencies.get('ep', 0),
                'gold': currencies.get('gp', 0),
                'platinum': currencies.get('pp', 0)
            }
            
            # Calculate total wealth in gold pieces
            total_gp = 0.0
            for currency_code, conversion_rate in self.currency_to_gp.items():
                amount = currencies.get(currency_code, 0)
                total_gp += amount * conversion_rate
            
            wealth['total_gp'] = round(total_gp, 2)
            
            return wealth
            
        except Exception as e:
            self.logger.error(f"Error calculating wealth: {e}")
            return {
                'copper': 0, 'silver': 0, 'electrum': 0, 'gold': 0, 'platinum': 0, 'total_gp': 0.0
            }
    
    def _calculate_encumbrance(self, raw_data: Dict[str, Any], context: CalculationContext) -> Dict[str, Any]:
        """Calculate encumbrance using enhanced calculator with comprehensive fallback."""
        # Try enhanced calculator first
        try:
            self.logger.debug("Using enhanced encumbrance calculator")
            transformed_data = self.data_transformer.transform_for_enhanced_calculators(raw_data)
            enhanced_result = self.enhanced_encumbrance_calculator.calculate(transformed_data, context)
            
            if enhanced_result.status == CalculationStatus.COMPLETED:
                self.logger.info("Successfully used enhanced encumbrance calculator")
                enhanced_data = enhanced_result.data
                return {
                    'total_weight': enhanced_data.get('current_weight', 0.0),
                    'carrying_capacity': enhanced_data.get('carrying_capacity', 150.0),
                    'encumbered_threshold': enhanced_data.get('encumbered_threshold', 50.0),
                    'heavily_encumbered_threshold': enhanced_data.get('heavily_encumbered_threshold', 100.0),
                    'encumbrance_level': enhanced_data.get('encumbrance_level', 0),
                    'speed_reduction': enhanced_data.get('speed_penalty', 0),
                    'strength_score': enhanced_data.get('strength_score', 10),
                    'calculation_method': 'enhanced'
                }
            else:
                self.logger.debug(f"Enhanced calculator needs additional data: {enhanced_result.errors}")
                
        except Exception as e:
            self.logger.debug(f"Enhanced calculator unavailable, using comprehensive calculation: {str(e)}")
        
        # Comprehensive encumbrance calculation
        self.logger.debug("Using comprehensive encumbrance calculation")
        
        try:
            # Get strength score from context or raw data
            strength_score = self._get_strength_score(raw_data, context)
            
            # Calculate carrying capacity thresholds
            carrying_capacity = strength_score * 15
            encumbered_threshold = strength_score * 5
            heavily_encumbered_threshold = strength_score * 10
            
            # Calculate total weight from inventory
            total_weight = 0.0
            inventory = raw_data.get('inventory', [])
            # Ensure inventory is not None
            if inventory is None:
                inventory = []
            
            for item_data in inventory:
                definition = item_data.get('definition', {})
                item_weight = (definition.get('weight', 0.0) or 0.0) * item_data.get('quantity', 1)
                total_weight += item_weight
            
            # Determine encumbrance level
            if total_weight <= encumbered_threshold:
                encumbrance_level = 0  # Unencumbered
                speed_reduction = 0
            elif total_weight <= heavily_encumbered_threshold:
                encumbrance_level = 1  # Encumbered
                speed_reduction = 10
            elif total_weight <= carrying_capacity:
                encumbrance_level = 2  # Heavily encumbered
                speed_reduction = 20
            else:
                encumbrance_level = 3  # Over capacity
                speed_reduction = 999
            
            return {
                'total_weight': round(total_weight, 2),
                'carrying_capacity': carrying_capacity,
                'encumbered_threshold': encumbered_threshold,
                'heavily_encumbered_threshold': heavily_encumbered_threshold,
                'encumbrance_level': encumbrance_level,
                'speed_reduction': speed_reduction,
                'strength_score': strength_score
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating encumbrance: {e}")
            return {
                'total_weight': 0.0, 'carrying_capacity': 150, 'encumbered_threshold': 50,
                'heavily_encumbered_threshold': 100, 'encumbrance_level': 0, 'speed_reduction': 0,
                'strength_score': 10
            }
    
    def _generate_equipment_summary(self, basic_equipment: List[Dict[str, Any]],
                                   enhanced_equipment: List[Dict[str, Any]],
                                   container_inventory: Dict[str, Any],
                                   wealth: Dict[str, Any],
                                   encumbrance: Dict[str, Any],
                                   party_inventory: Optional[PartyInventoryData] = None,
                                   infusions: Optional[InfusionsData] = None) -> Dict[str, Any]:
        """Generate equipment summary statistics."""
        try:
            # Equipment categorization
            weapons = [e for e in enhanced_equipment if self._is_weapon(e)]
            armor = [e for e in enhanced_equipment if self._is_armor(e)]
            magic_items = [e for e in enhanced_equipment if e.get('is_magic', False)]
            equipped_items = [e for e in enhanced_equipment if e.get('equipped', False)]
            attuned_items = [e for e in enhanced_equipment if e.get('attuned', False)]
            
            # Weight distribution
            equipped_weight = sum(e.get('weight', 0) * e.get('quantity', 1) for e in equipped_items)
            unequipped_weight = encumbrance.get('total_weight', 0) - equipped_weight
            
            return {
                'item_counts': {
                    'total_items': len(basic_equipment),
                    'weapons': len(weapons),
                    'armor': len(armor),
                    'magic_items': len(magic_items),
                    'equipped_items': len(equipped_items),
                    'attuned_items': len(attuned_items)
                },
                'weight_distribution': {
                    'total_weight': encumbrance.get('total_weight', 0),
                    'equipped_weight': round(equipped_weight, 2),
                    'unequipped_weight': round(unequipped_weight, 2),
                    'encumbrance_level': encumbrance.get('encumbrance_level', 0)
                },
                'wealth_summary': {
                    'total_gp': wealth.get('total_gp', 0),
                    'currency_count': sum(1 for v in wealth.values() if isinstance(v, int) and v > 0)
                },
                'container_summary': {
                    'total_containers': len(container_inventory.get('containers', {})),
                    'containers_with_items': len([c for c in container_inventory.get('containers', {}).values() 
                                                if c.get('items', [])]),
                    'organization': container_inventory.get('container_organization', {})
                },
                'notable_items': {
                    'high_value_items': [e for e in enhanced_equipment
                                       if e.get('cost') and e.get('cost') > 100],
                    'rare_items': [e for e in enhanced_equipment
                                 if (e.get('rarity') or 'common').lower() in ['rare', 'very rare', 'legendary']],
                    'requires_attunement': [e for e in enhanced_equipment
                                          if e.get('requires_attunement', False)]
                },
                'party_inventory_summary': self._get_party_inventory_summary(party_inventory) if party_inventory else None,
                'infusions_summary': self._get_infusions_summary(infusions) if infusions else None
            }
            
        except Exception as e:
            self.logger.error(f"Error generating equipment summary: {e}")
            return {}

    def _get_party_inventory_summary(self, party_inventory: PartyInventoryData) -> Dict[str, Any]:
        """Generate summary for party inventory."""
        try:
            return {
                'campaign_id': party_inventory.campaign_id,
                'item_count': len(party_inventory.party_items),
                'total_party_currency_gp': (
                    party_inventory.party_currency.get('gp', 0) +
                    party_inventory.party_currency.get('sp', 0) / 10 +
                    party_inventory.party_currency.get('cp', 0) / 100 +
                    party_inventory.party_currency.get('ep', 0) * 0.5 +
                    party_inventory.party_currency.get('pp', 0) * 10
                ),
                'sharing_enabled': party_inventory.sharing_state > 0,
                'party_items_by_type': self._categorize_party_items(party_inventory.party_items),
                'has_party_modifiers': len(party_inventory.modifiers.get('item', [])) > 0,
                'has_party_spells': len(party_inventory.spells.get('item', [])) > 0
            }
        except Exception as e:
            self.logger.error(f"Error generating party inventory summary: {e}")
            return {}

    def _categorize_party_items(self, party_items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize party items by type."""
        categories = {}
        for item in party_items:
            item_type = item.get('type', 'Unknown')
            categories[item_type] = categories.get(item_type, 0) + 1
        return categories

    def _get_infusions_summary(self, infusions: InfusionsData) -> Dict[str, Any]:
        """Generate summary for infusions."""
        try:
            # Categorize active infusions by type
            active_by_type = {}
            for infusion in infusions.active_infusions:
                infusion_type = infusion.get('type', 'Unknown')
                active_by_type[infusion_type] = active_by_type.get(infusion_type, 0) + 1

            # Find rare/unique infusions
            rare_infusions = [inf for inf in infusions.active_infusions
                            if (inf.get('rarity') or 'common').lower() in ['rare', 'very rare', 'legendary']]

            return {
                'active_count': len(infusions.active_infusions),
                'known_count': len(infusions.known_infusions),
                'slots_used': infusions.infusion_slots_used,
                'slots_total': infusions.infusion_slots_total,
                'slots_available': infusions.infusion_slots_total - infusions.infusion_slots_used,
                'artificer_levels': infusions.metadata.get('artificer_levels', 0),
                'active_by_type': active_by_type,
                'has_rare_infusions': len(rare_infusions) > 0,
                'attunement_required': len([inf for inf in infusions.active_infusions
                                          if inf.get('requires_attunement', False)])
            }
        except Exception as e:
            self.logger.error(f"Error generating infusions summary: {e}")
            return {}

    def _extract_weapon_properties(self, definition: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract weapon properties from definition."""
        properties = []
        
        weapon_properties = definition.get('properties', [])
        # Ensure weapon_properties is not None
        if weapon_properties is None:
            weapon_properties = []
        
        for prop_data in weapon_properties:
            try:
                prop = {
                    'id': prop_data.get('id'),
                    'name': prop_data.get('name', 'Unknown Property'),
                    'description': prop_data.get('description'),
                    'damage_value': None,
                    'range_normal': None,
                    'range_long': None
                }
                
                # Handle specific property types
                if 'versatile' in (prop['name'] or '').lower() and 'damage' in prop_data:
                    prop['damage_value'] = prop_data.get('damage', {}).get('diceString')
                elif 'range' in (prop['name'] or '').lower():
                    prop['range_normal'] = prop_data.get('range')
                    prop['range_long'] = prop_data.get('longRange')
                
                properties.append(prop)
                
            except Exception as e:
                self.logger.warning(f"Error processing weapon property: {e}")
                continue
        
        return properties
    
    def _convert_attack_type(self, attack_type: Any) -> Optional[str]:
        """Convert attack type ID to string."""
        if isinstance(attack_type, int):
            attack_type_map = {1: "melee", 2: "ranged"}
            return attack_type_map.get(attack_type, "unknown")
        return attack_type
    
    def _determine_weapon_category(self, category_id: Optional[int]) -> Optional[str]:
        """Determine weapon category from category ID."""
        if not category_id:
            return None
        
        category_map = {
            1: "simple",  # Simple melee
            2: "simple",  # Simple ranged
            3: "martial", # Martial melee
            4: "martial"  # Martial ranged
        }
        
        return category_map.get(category_id)
    
    def _determine_armor_type(self, armor_type_id: Optional[int]) -> Optional[str]:
        """Determine armor type from armor type ID."""
        if not armor_type_id:
            return None
        
        armor_type_map = {
            1: "light",
            2: "medium",
            3: "heavy",
            4: "shield"
        }
        
        return armor_type_map.get(armor_type_id)
    
    def _is_weapon(self, item: Dict[str, Any]) -> bool:
        """Check if an item is a weapon."""
        item_type = (item.get('item_type') or '').lower()
        weapon_types = ['weapon', 'simple weapon', 'martial weapon']
        return any(wt in item_type for wt in weapon_types)
    
    def _is_armor(self, item: Dict[str, Any]) -> bool:
        """Check if an item is armor."""
        item_type = (item.get('item_type') or '').lower()
        armor_types = ['armor', 'light armor', 'medium armor', 'heavy armor', 'shield']
        return any(at in item_type for at in armor_types)
    
    def _get_strength_score(self, raw_data: Dict[str, Any], context: CalculationContext) -> int:
        """Get strength score from context or raw data."""
        # Try to get from context first
        if context and hasattr(context, 'metadata') and context.metadata:
            abilities_data = context.metadata.get('abilities', {})
            if 'ability_scores' in abilities_data:
                strength_data = abilities_data['ability_scores'].get('strength', {})
                if isinstance(strength_data, dict):
                    return strength_data.get('score', 10)
                elif isinstance(strength_data, int):
                    return strength_data
        
        # Fallback: calculate from raw data
        stats = raw_data.get('stats', [])
        # Ensure stats is not None
        if stats is None:
            stats = []
        
        for stat in stats:
            if stat.get('id') == 1:  # Strength ID is 1
                return stat.get('value', 10)
        
        return 10
    
    def validate_input(self, raw_data: Dict[str, Any]) -> bool:
        """
        Validate that the input data is suitable for this coordinator.
        
        Args:
            raw_data: Raw character data to validate
            
        Returns:
            True if data is valid for this coordinator
        """
        # Equipment calculation can work with minimal data
        if not isinstance(raw_data, dict):
            return False
        
        # Basic validation - we need character data
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
                "basic_equipment": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": ["integer", "null"]},
                            "name": {"type": "string"},
                            "item_type": {"type": "string"},
                            "quantity": {"type": "integer", "minimum": 1},
                            "weight": {"type": "number", "minimum": 0},
                            "equipped": {"type": "boolean"},
                            "total_weight": {"type": "number", "minimum": 0}
                        },
                        "required": ["name", "item_type", "quantity", "weight", "equipped"]
                    }
                },
                "enhanced_equipment": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": ["integer", "null"]},
                            "name": {"type": "string"},
                            "item_type": {"type": "string"},
                            "quantity": {"type": "integer", "minimum": 1},
                            "weight": {"type": "number", "minimum": 0},
                            "equipped": {"type": "boolean"},
                            "is_magic": {"type": "boolean"},
                            "attuned": {"type": "boolean"},
                            "requires_attunement": {"type": "boolean"},
                            "weapon_properties": {"type": "array"},
                            "armor_type": {"type": ["string", "null"]}
                        },
                        "required": ["name", "item_type", "quantity", "weight", "equipped"]
                    }
                },
                "container_inventory": {
                    "type": "object",
                    "properties": {
                        "containers": {"type": "object"},
                        "container_organization": {"type": "object"},
                        "weight_breakdown": {"type": "object"}
                    },
                    "required": ["containers", "container_organization", "weight_breakdown"]
                },
                "wealth": {
                    "type": "object",
                    "properties": {
                        "copper": {"type": "integer", "minimum": 0},
                        "silver": {"type": "integer", "minimum": 0},
                        "electrum": {"type": "integer", "minimum": 0},
                        "gold": {"type": "integer", "minimum": 0},
                        "platinum": {"type": "integer", "minimum": 0},
                        "total_gp": {"type": "number", "minimum": 0}
                    },
                    "required": ["copper", "silver", "electrum", "gold", "platinum", "total_gp"]
                },
                "encumbrance": {
                    "type": "object",
                    "properties": {
                        "total_weight": {"type": "number", "minimum": 0},
                        "carrying_capacity": {"type": "number", "minimum": 0},
                        "encumbrance_level": {"type": "integer", "minimum": 0, "maximum": 3},
                        "speed_reduction": {"type": "integer", "minimum": 0},
                        "strength_score": {"type": "integer", "minimum": 1}
                    },
                    "required": ["total_weight", "carrying_capacity", "encumbrance_level", "speed_reduction"]
                },
                "equipment_summary": {"type": "object"},
                "metadata": {"type": "object"}
            },
            "required": [
                "basic_equipment", "enhanced_equipment", "container_inventory", 
                "wealth", "encumbrance", "equipment_summary"
            ]
        }