"""
Inventory formatter for equipment and items.

This module handles the generation of inventory sections including
wealth calculation, encumbrance tracking, and interactive inventory components.
"""

from typing import Dict, Any, List, Optional

# Import interfaces and utilities using absolute import
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging

from formatters.base import BaseFormatter
from utils.text import TextProcessor


class InventoryFormatter(BaseFormatter):
    """
    Handles inventory section generation for character sheets.
    
    Generates comprehensive inventory information including wealth calculation,
    encumbrance tracking, and DataCore JSX interactive inventory components.
    """
    
    # Template configuration - values match parser.yaml settings
    # These can be overridden by subclasses or future config integration
    DEFAULT_JSX_DIR = "z_Templates"                 # jsx_components_dir from parser.yaml
    DEFAULT_INVENTORY_COMPONENT = "InventoryManager.jsx"  # inventory_component from parser.yaml
    
    def __init__(self, text_processor: TextProcessor):
        """
        Initialize the inventory formatter.
        
        Args:
            text_processor: Text processing utilities
        """
        super().__init__(text_processor)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _get_required_fields(self) -> List[str]:
        """Get list of required fields for inventory formatting."""
        return []
    
    def _validate_internal(self, character_data: Dict[str, Any]) -> bool:
        """Validate character data structure for inventory formatting."""
        # Use proper character info accessor like other formatters
        character_info = self.get_character_info(character_data)
        
        # Check for character name - this is informational, not a blocker
        if not character_info.get('name'):
            self.logger.debug("Parser:   Character name not found in character_info")
        
        return True
    
    def _get_template_settings(self) -> tuple:
        """
        Get template settings for JSX components.
        
        This method provides a clean interface for template configuration.
        Currently uses class constants that match parser.yaml settings.
        Can be easily enhanced to use a config manager when available.
        
        Returns:
            Tuple of (jsx_dir, inventory_component)
        """
        # TODO: When config manager is available, enhance to:
        # if hasattr(self, 'config_manager') and self.config_manager:
        #     jsx_dir = self.config_manager.get_template_setting("jsx_components_dir", self.DEFAULT_JSX_DIR)
        #     inventory_component = self.config_manager.get_template_setting("inventory_component", self.DEFAULT_INVENTORY_COMPONENT)
        #     return jsx_dir, inventory_component
        
        return self.DEFAULT_JSX_DIR, self.DEFAULT_INVENTORY_COMPONENT
    
    def _format_internal(self, character_data: Dict[str, Any]) -> str:
        """
        Generate comprehensive inventory section.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Formatted inventory section
        """
        sections = []
        
        # Header
        sections.append(self._generate_header())

        # Wealth information
        sections.append(self._generate_wealth_section(character_data))

        # Encumbrance information
        sections.append(self._generate_encumbrance_section(character_data))

        # Interactive inventory component (player inventory)
        sections.append(self._generate_interactive_inventory_section(character_data))

        # Party inventory (if available)
        party_inventory_section = self._generate_party_inventory_section(character_data)
        if party_inventory_section:
            sections.append(party_inventory_section)

        # Infusions (if available)
        infusions_section = self._generate_infusions_section(character_data)
        if infusions_section:
            sections.append(infusions_section)

        # Footer
        sections.append(self._generate_footer())
        
        return ''.join(section for section in sections if section)
    
    def _generate_header(self) -> str:
        """Generate inventory section header."""
        return """## Inventory

<span class="right-link">[[#Character Statistics|Top]]</span>

"""
    
    def _generate_wealth_section(self, character_data: Dict[str, Any]) -> str:
        """Generate wealth calculation section with v6.0.0 format support."""
        # In v6.0.0 format, wealth info is at the top level
        wealth = character_data.get('wealth', {})
        
        if wealth:
            # Extract values from wealth dict (v6.0.0 format)
            copper = wealth.get('copper', 0)
            silver = wealth.get('silver', 0)
            electrum = wealth.get('electrum', 0)
            gold = wealth.get('gold', 0)
            platinum = wealth.get('platinum', 0)
            total_gp = wealth.get('total_gp', 0)
            
            
            # Calculate total_gp if not provided
            if total_gp == 0:
                total_gp = (copper * 0.01) + (silver * 0.1) + (electrum * 0.5) + gold + (platinum * 10)
            
            # Use the actual currency breakdown from the wealth data
        else:
            # Fallback: extract from equipment section
            equipment = character_data.get('equipment', {})
            wealth = equipment.get('wealth', {})
            
            if wealth:
                # Extract values from equipment wealth dict
                copper = wealth.get('copper', 0)
                silver = wealth.get('silver', 0)
                electrum = wealth.get('electrum', 0)
                gold = wealth.get('gold', 0)
                platinum = wealth.get('platinum', 0)
                total_gp = wealth.get('total_gp', 0)
                
                # Calculate total_gp if not provided
                if total_gp == 0:
                    total_gp = (copper * 0.01) + (silver * 0.1) + (electrum * 0.5) + gold + (platinum * 10)
            else:
                # Last fallback: try equipment_summary
                equipment_summary = equipment.get('equipment_summary', {})
                wealth_summary = equipment_summary.get('wealth_summary', {})
                total_gp = wealth_summary.get('total_gp', 0)
                
                if total_gp > 0:
                    # Convert decimal gold to gold + silver breakdown
                    gold = int(total_gp) if isinstance(total_gp, (int, float)) else 0  # Integer part becomes gold pieces
                    silver_remainder = (total_gp - gold) * 10  # Decimal part * 10 becomes silver pieces
                    silver = int(silver_remainder) if isinstance(silver_remainder, (int, float)) else 0
                    copper = 0
                    electrum = 0
                    platinum = 0
                else:
                    copper = silver = electrum = gold = platinum = 0
        
        wealth_str = []
        if gold > 0:
            wealth_str.append(f"{gold} gp")
        if silver > 0:
            wealth_str.append(f"{silver} sp")
        if copper > 0:
            wealth_str.append(f"{copper} cp")
        if platinum > 0:
            wealth_str.append(f"{platinum} pp")
        
        # If no wealth components, show 0 gp
        if not wealth_str:
            wealth_str.append("0 gp")
        
        # Simple wealth display - styling is now handled in InventoryManager.jsx
        wealth_display = ' | '.join(wealth_str)
        total_display = f"Total: {int(total_gp) if isinstance(total_gp, (int, float)) else 0} gp"

        return f"**Personal Wealth:** {wealth_display} ({total_display})\n\n"

    def _generate_party_inventory_section(self, character_data: Dict[str, Any]) -> Optional[str]:
        """Generate party inventory section with interactive JSX component if available."""
        # Check for party inventory in equipment data
        equipment = character_data.get('equipment', {})
        party_inventory = equipment.get('party_inventory')

        if not party_inventory:
            return None

        # Extract party inventory data
        party_items = party_inventory.get('party_items', [])
        party_currency = party_inventory.get('party_currency', {})
        campaign_id = party_inventory.get('campaign_id')

        if not party_items and not any(party_currency.values()):
            return None

        # Get character name for the component
        character_info = self.get_character_info(character_data)
        character_name = character_info.get('name', 'Unknown Character')

        # Get template settings using proper configuration method
        jsx_dir, _ = self._get_template_settings()
        party_component = "PartyInventoryManager.jsx"

        # Generate the DataCore JSX component for party inventory
        section = f"### Party Inventory"
        if campaign_id:
            section += f" (Campaign {campaign_id})"
        section += "\n\n"

        section += "```datacorejsx\n"
        section += f"const {{ PartyInventoryQuery }} = await dc.require(\"{jsx_dir}/{party_component}\");\n"
        section += f"return <PartyInventoryQuery characterName=\"{character_name}\""
        if campaign_id:
            section += f" campaignId=\"{campaign_id}\""
        section += " />;\n"
        section += "```\n\n"

        return section

    def _generate_infusions_section(self, character_data: Dict[str, Any]) -> Optional[str]:
        """Generate infusions section if character has infusions."""
        # Check for infusions in equipment data
        equipment = character_data.get('equipment', {})
        infusions = equipment.get('infusions')

        if not infusions:
            return None

        # Extract infusion data
        active_infusions = infusions.get('active_infusions', [])
        known_infusions = infusions.get('known_infusions', [])
        slots_used = infusions.get('infusion_slots_used', 0)
        slots_total = infusions.get('infusion_slots_total', 0)
        artificer_levels = infusions.get('metadata', {}).get('artificer_levels', 0)

        # Only show section if there are infusions
        if not active_infusions and not known_infusions:
            return None

        # Get character name for the component
        character_info = self.get_character_info(character_data)
        character_name = character_info.get('name', 'Unknown Character')

        # Generate section header
        section = f"### Artificer Infusions"
        if artificer_levels > 0:
            section += f" (Level {artificer_levels} Artificer)"
        section += "\n\n"

        # Add infusion slots information
        if slots_total > 0:
            section += f"**Infusion Slots:** {slots_used}/{slots_total} used"
            if slots_total > slots_used:
                section += f" ({slots_total - slots_used} available)"
            section += "\n\n"

        # Add active infusions if any
        if active_infusions:
            section += f"**Active Infusions ({len(active_infusions)}):**\n"
            for infusion in active_infusions:
                infusion_name = infusion.get('name', 'Unknown')
                infused_item = infusion.get('infused_item_name', 'Unknown Item')
                section += f"- **{infusion_name}** (on {infused_item})\n"
            section += "\n"

        # Add known infusions count if any
        if known_infusions:
            section += f"**Known Infusions:** {len(known_infusions)} total\n\n"

        # Add interactive component for detailed infusion management
        jsx_dir = self.DEFAULT_JSX_DIR
        section += "```datacorejsx\n"
        section += f"const {{ InfusionsQuery }} = await dc.require(\"{jsx_dir}/InfusionsManager.jsx\");\n"
        section += f"return <InfusionsQuery characterName=\"{character_name}\" />;\n"
        section += "```\n\n"

        return section

    def _generate_encumbrance_section(self, character_data: Dict[str, Any]) -> str:
        """Generate encumbrance tracking section with v6.0.0 format support."""
        # Get encumbrance data - try top level first, then equipment section
        encumbrance = character_data.get('encumbrance', {})
        carrying_capacity = encumbrance.get('carrying_capacity', 0)
        encumbrance_level = encumbrance.get('encumbrance_level')
        
        # Calculate corrected total weight excluding extradimensional containers
        equipment = character_data.get('equipment', {})
        total_weight = self._calculate_corrected_encumbrance(equipment)
        
        # If no encumbrance at top level, try equipment section for carrying capacity
        if carrying_capacity == 0:
            encumbrance = equipment.get('encumbrance', {})
            
            if encumbrance:
                carrying_capacity = encumbrance.get('carrying_capacity', 0)
                encumbrance_level = encumbrance.get('encumbrance_level')
            else:
                # Fallback to equipment_summary for carrying capacity only
                equipment_summary = equipment.get('equipment_summary', {})
                weight_distribution = equipment_summary.get('weight_distribution', {})
                
                # Don't override total_weight - keep our corrected calculation
                # Only get encumbrance_level if not already set
                if encumbrance_level is None:
                    encumbrance_level = weight_distribution.get('encumbrance_level')
                
                # Calculate carrying capacity from abilities if not available
                # Carrying capacity = Strength score * 15
                abilities = character_data.get('abilities', {})
                ability_scores = abilities.get('ability_scores', {})
                strength_data = ability_scores.get('strength', {})
                strength_score = strength_data.get('score', 10)
                carrying_capacity = strength_score * 15
        
        # Calculate encumbrance percentage and status
        percentage = int((total_weight / carrying_capacity * 100)) if carrying_capacity > 0 and isinstance(total_weight, (int, float)) else 0
        
        # Use v6.0.0 encumbrance level if available, otherwise calculate
        if encumbrance_level is not None:
            # Convert to int if it's a string to handle type mismatches
            try:
                encumbrance_level_int = int(encumbrance_level) if isinstance(encumbrance_level, str) else encumbrance_level
            except (ValueError, TypeError):
                encumbrance_level_int = 0

            # v6.0.0 uses numeric levels: 0=Unencumbered, 1=Encumbered, 2=Heavily Encumbered, 3=Overloaded
            if encumbrance_level_int >= 3:
                encumbrance_status = "Overloaded"
            elif encumbrance_level_int >= 2:
                encumbrance_status = "Heavy"
            elif encumbrance_level_int >= 1:
                encumbrance_status = "Medium"
            else:
                encumbrance_status = "Light"
        else:
            # Fallback calculation
            encumbrance_status = "Heavy" if percentage > 66 else "Medium" if percentage > 33 else "Light"
        
        return f"**Encumbrance:** {total_weight:.1f}/{carrying_capacity} lbs ({percentage}% - {encumbrance_status})\n\n"
    
    def _generate_interactive_inventory_section(self, character_data: Dict[str, Any]) -> str:
        """Generate interactive inventory component section."""
        section = "### Personal Inventory\n\n"

        # Get character name for the component
        character_info = self.get_character_info(character_data)
        character_name = character_info.get('name', 'Unknown Character')

        # Get template settings using proper configuration method
        jsx_dir, inventory_component = self._get_template_settings()

        # Generate the DataCore JSX component
        section += "```datacorejsx\n"
        section += f"const {{ InventoryQuery }} = await dc.require(\"{jsx_dir}/{inventory_component}\");\n"
        section += f"return <InventoryQuery characterName=\"{character_name}\" />;\n"
        section += "```\n\n"

        return section
    
    def _generate_footer(self) -> str:
        """Generate inventory section footer."""
        return "^inventory"
    
    def format_wealth_only(self, character_data: Dict[str, Any]) -> str:
        """
        Format only the wealth section.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Wealth section only
        """
        if not self.validate_input(character_data):
            raise ValueError("Invalid character data for wealth formatting")
        
        return self._generate_wealth_section(character_data)
    
    def format_encumbrance_only(self, character_data: Dict[str, Any]) -> str:
        """
        Format only the encumbrance section.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Encumbrance section only
        """
        if not self.validate_input(character_data):
            raise ValueError("Invalid character data for encumbrance formatting")
        
        return self._generate_encumbrance_section(character_data)
    
    def get_inventory_summary(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key inventory information for summary purposes.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Dictionary containing key inventory information
        """
        wealth = character_data.get('wealth', {})
        encumbrance = character_data.get('encumbrance', {})
        
        # Get inventory items from v6.0.0 structure first, then fallback
        inventory = character_data.get('inventory', [])
        if not inventory:
            equipment = character_data.get('equipment', {})
            inventory = equipment.get('basic_equipment', [])
        
        # Calculate wealth summary
        total_gp = wealth.get('total_gp', 0)
        
        # Calculate encumbrance summary
        total_weight = encumbrance.get('total_weight', 0)
        carrying_capacity = encumbrance.get('carrying_capacity', 0)
        encumbrance_percentage = int((total_weight / carrying_capacity * 100)) if carrying_capacity > 0 and isinstance(total_weight, (int, float)) else 0
        encumbrance_status = "Heavy" if encumbrance_percentage > 66 else "Medium" if encumbrance_percentage > 33 else "Light"
        
        # Count inventory items
        total_items = len(inventory)
        equipped_items = len([item for item in inventory if item.get('equipped', False)])
        
        return {
            'total_wealth_gp': total_gp,
            'total_weight': total_weight,
            'carrying_capacity': carrying_capacity,
            'encumbrance_percentage': encumbrance_percentage,
            'encumbrance_status': encumbrance_status,
            'total_items': total_items,
            'equipped_items': equipped_items
        }
    
    def get_wealth_breakdown(self, character_data: Dict[str, Any]) -> Dict[str, int]:
        """
        Get detailed breakdown of wealth by currency type.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Dictionary with wealth breakdown by currency
        """
        wealth = character_data.get('wealth', {})
        
        return {
            'copper': wealth.get('copper', 0),
            'silver': wealth.get('silver', 0),
            'gold': wealth.get('gold', 0),
            'platinum': wealth.get('platinum', 0),
            'total_gp': wealth.get('total_gp', 0)
        }
    
    def has_inventory_data(self, character_data: Dict[str, Any]) -> bool:
        """
        Check if the character has any inventory data to display.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            True if character has inventory data, False otherwise
        """
        # Get inventory items from v6.0.0 structure first, then fallback
        inventory = character_data.get('inventory', [])
        if not inventory:
            equipment = character_data.get('equipment', {})
            inventory = equipment.get('basic_equipment', [])
        
        wealth = character_data.get('wealth', {})
        encumbrance = character_data.get('encumbrance', {})
        
        # Check if there's any meaningful inventory data
        has_items = len(inventory) > 0
        has_wealth = wealth.get('total_gp', 0) > 0
        has_encumbrance = encumbrance.get('total_weight', 0) > 0
        
        return has_items or has_wealth or has_encumbrance
    
    def format_with_config(self, character_data: Dict[str, Any], config: Optional[Any] = None) -> str:
        """
        Format inventory with configuration support for templates.
        
        Args:
            character_data: Complete character data dictionary
            config: Optional configuration object with template settings
            
        Returns:
            Formatted inventory section with config-based templates
        """
        # This is a placeholder for enhanced functionality that would use
        # the config system to get JSX template settings
        if config:
            # Would use config.get_template_setting() and config.get_datacorejsx_template()
            # For now, fall back to standard formatting
            pass
        
        return self.format(character_data)
    
    def _calculate_corrected_encumbrance(self, equipment_data: Dict[str, Any]) -> float:
        """
        Calculate encumbrance excluding items in extradimensional containers.
        
        Args:
            equipment_data: Equipment data from character
            
        Returns:
            Total weight excluding extradimensional container contents
        """
        basic_equipment = equipment_data.get('basic_equipment', [])
        total_weight = 0.0
        
        # Get container inventory structure if available
        container_inventory = equipment_data.get('container_inventory', {})
        containers = container_inventory.get('containers', {})
        
        # First pass: identify extradimensional containers using container structure
        extradimensional_containers = set()
        
        if containers:
            # Use container structure to identify extradimensional containers
            for container_id, container_info in containers.items():
                container_name = container_info.get('name', '').lower()
                
                # Check for known extradimensional containers
                if any(name in container_name for name in [
                    'bag of holding', 'heward\'s handy haversack', 'portable hole',
                    'handy haversack', 'efficient quiver'
                ]):
                    # Add both string and integer versions to handle type mismatches
                    extradimensional_containers.add(str(container_id))
                    try:
                        extradimensional_containers.add(int(container_id))
                    except (ValueError, TypeError):
                        # Handle cases where container_id can't be converted to int
                        pass
                    self.logger.debug(f"Parser:   Identified extradimensional container: {container_info.get('name')} (ID: {container_id})")
        else:
            # Fallback: identify extradimensional containers by item names in basic_equipment
            for item in basic_equipment:
                item_name = item.get('name', '').lower()
                
                # Check for known extradimensional containers
                if any(name in item_name for name in [
                    'bag of holding', 'heward\'s handy haversack', 'portable hole',
                    'handy haversack', 'efficient quiver'
                ]):
                    extradimensional_containers.add(item.get('id'))
                    self.logger.debug(f"Parser:   Identified extradimensional container: {item.get('name')} (ID: {item.get('id')})")
        
        # Second pass: calculate weight, excluding items in extradimensional containers
        for item in basic_equipment:
            item_weight = item.get('weight', 0.0) * item.get('quantity', 1)
            
            # Check if item is stored in an extradimensional container
            container_id = item.get('container_entity_id')
            is_in_extradimensional = container_id in extradimensional_containers
            
            # Only add to total weight if NOT in an extradimensional container
            if not is_in_extradimensional:
                total_weight += item_weight
            else:
                self.logger.debug(f"Parser:   Excluding {item.get('name')} ({item_weight} lbs) - stored in extradimensional container")
        
        return total_weight