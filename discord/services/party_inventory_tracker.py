#!/usr/bin/env python3
"""
Party Inventory Tracker for Discord Notifications

Treats party inventory as a virtual character to leverage existing Discord
change detection and notification infrastructure.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass

from .change_detection.models import CharacterSnapshot, FieldChange, ChangeType, ChangePriority, ChangeCategory

logger = logging.getLogger(__name__)


@dataclass
class PartyInventorySnapshot:
    """Represents a party inventory snapshot for change detection."""
    campaign_id: str
    timestamp: datetime
    party_items: List[Dict[str, Any]]
    party_currency: Dict[str, int]
    sharing_state: int
    associated_characters: List[int]
    metadata: Dict[str, Any]

    def to_character_snapshot(self) -> CharacterSnapshot:
        """Convert to CharacterSnapshot format for existing Discord infrastructure."""
        # Create virtual character ID for party inventory
        virtual_character_id = f"party_{self.campaign_id}"

        # Get campaign name from metadata or fall back to campaign ID
        campaign_name = self.metadata.get('campaign_name')
        display_name = f"Party Inventory ({campaign_name})" if campaign_name else f"Party Inventory (Campaign {self.campaign_id})"

        # Transform party inventory data into character-like structure
        character_data = {
            "basic_info": {
                "name": display_name,
                "campaign_id": self.campaign_id,
                "type": "party_inventory"
            },
            "party_inventory": {
                "party_items": self.party_items,
                "party_currency": self.party_currency,
                "sharing_state": self.sharing_state,
                "associated_characters": self.associated_characters
            },
            "metadata": {
                **self.metadata,
                "is_party_inventory": True,
                "snapshot_timestamp": self.timestamp.isoformat()
            }
        }

        return CharacterSnapshot(
            character_id=hash(virtual_character_id),  # Generate numeric ID from string
            character_name=display_name,
            version=int(self.timestamp.timestamp()),
            timestamp=self.timestamp,
            character_data=character_data,
            metadata={
                "is_party_inventory": True,
                "campaign_id": self.campaign_id,
                "campaign_name": campaign_name,
                "virtual_character_id": virtual_character_id
            }
        )


class PartyInventoryTracker:
    """
    Tracks party inventory changes by treating them as virtual character changes.

    Integrates with existing Discord notification infrastructure by converting
    party inventory data into CharacterSnapshot format.
    """

    def __init__(self, storage_dir: str):
        self.storage_dir = Path(storage_dir)
        self.snapshots_dir = self.storage_dir / "party_snapshots"
        self.snapshots_dir.mkdir(exist_ok=True, parents=True)

        logger.info(f"Party inventory tracker initialized with storage: {self.snapshots_dir}")

    def extract_party_inventory_from_character(self, character_data: Dict[str, Any]) -> Optional[PartyInventorySnapshot]:
        """
        Extract party inventory data from a character's data.

        Args:
            character_data: Character data containing party inventory

        Returns:
            PartyInventorySnapshot if party inventory exists, None otherwise
        """
        try:
            # Extract party inventory from equipment section
            equipment = character_data.get('equipment', {})
            party_inventory = equipment.get('party_inventory')

            if not party_inventory:
                logger.debug("No party inventory found in character data")
                return None

            campaign_id = party_inventory.get('campaign_id')
            if not campaign_id:
                logger.warning("Party inventory found but no campaign_id")
                return None

            # Extract party data
            party_items = party_inventory.get('party_items', [])
            party_currency = party_inventory.get('party_currency', {})
            sharing_state = party_inventory.get('sharing_state', 0)

            # Get character info for metadata
            character_info = character_data.get('character_info', {})
            character_id = character_info.get('id')

            # Extract campaign name from character details
            character_details = character_data.get('character_details', {})
            campaign_name = character_details.get('campaign_name') if character_details else None

            return PartyInventorySnapshot(
                campaign_id=str(campaign_id),
                timestamp=datetime.now(),
                party_items=party_items,
                party_currency=party_currency,
                sharing_state=sharing_state,
                associated_characters=[character_id] if character_id else [],
                metadata={
                    "source_character": character_info.get('name', 'Unknown'),
                    "source_character_id": character_id,
                    "campaign_name": campaign_name,
                    "items_count": len(party_items),
                    "currency_total_gp": self._calculate_total_currency_gp(party_currency)
                }
            )

        except Exception as e:
            logger.error(f"Error extracting party inventory: {e}")
            return None

    def _calculate_total_currency_gp(self, currency: Dict[str, int]) -> float:
        """Calculate total currency value in gold pieces."""
        multipliers = {'cp': 0.01, 'sp': 0.1, 'ep': 0.5, 'gp': 1, 'pp': 10}
        return sum(amount * multipliers.get(coin_type, 1) for coin_type, amount in currency.items())

    def save_party_snapshot(self, snapshot: PartyInventorySnapshot) -> str:
        """
        Save party inventory snapshot to storage.

        Args:
            snapshot: PartyInventorySnapshot to save

        Returns:
            Path to saved snapshot file
        """
        timestamp_str = snapshot.timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"party_inventory_{snapshot.campaign_id}_{timestamp_str}.json"
        filepath = self.snapshots_dir / filename

        # Convert to character snapshot for consistent storage format
        character_snapshot = snapshot.to_character_snapshot()

        snapshot_data = {
            "campaign_id": snapshot.campaign_id,
            "timestamp": snapshot.timestamp.isoformat(),
            "party_items": snapshot.party_items,
            "party_currency": snapshot.party_currency,
            "sharing_state": snapshot.sharing_state,
            "associated_characters": snapshot.associated_characters,
            "metadata": snapshot.metadata,
            "character_snapshot": character_snapshot.to_dict() if hasattr(character_snapshot, 'to_dict') else {
                "character_id": character_snapshot.character_id,
                "character_name": character_snapshot.character_name,
                "version": character_snapshot.version,
                "timestamp": character_snapshot.timestamp.isoformat(),
                "character_data": character_snapshot.character_data,
                "metadata": character_snapshot.metadata
            }
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Saved party inventory snapshot to: {filepath}")
        return str(filepath)

    def load_latest_party_snapshot(self, campaign_id: str) -> Optional[PartyInventorySnapshot]:
        """
        Load the most recent party inventory snapshot for a campaign.

        Args:
            campaign_id: Campaign ID to load snapshot for

        Returns:
            Latest PartyInventorySnapshot or None if not found
        """
        try:
            # Find all snapshots for this campaign
            pattern = f"party_inventory_{campaign_id}_*.json"
            snapshot_files = list(self.snapshots_dir.glob(pattern))

            if not snapshot_files:
                logger.debug(f"No party inventory snapshots found for campaign {campaign_id}")
                return None

            # Get the most recent file
            latest_file = max(snapshot_files, key=lambda f: f.stat().st_mtime)

            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return PartyInventorySnapshot(
                campaign_id=data['campaign_id'],
                timestamp=datetime.fromisoformat(data['timestamp']),
                party_items=data['party_items'],
                party_currency=data['party_currency'],
                sharing_state=data['sharing_state'],
                associated_characters=data['associated_characters'],
                metadata=data['metadata']
            )

        except Exception as e:
            logger.error(f"Error loading party snapshot for campaign {campaign_id}: {e}")
            return None

    def detect_party_changes(self, old_snapshot: PartyInventorySnapshot,
                           new_snapshot: PartyInventorySnapshot) -> List[FieldChange]:
        """
        Detect changes between two party inventory snapshots.

        Args:
            old_snapshot: Previous snapshot
            new_snapshot: Current snapshot

        Returns:
            List of FieldChange objects representing the differences
        """
        changes = []

        try:
            # Check currency changes
            currency_changes = self._detect_currency_changes(
                old_snapshot.party_currency,
                new_snapshot.party_currency
            )
            changes.extend(currency_changes)

            # Check item changes
            item_changes = self._detect_item_changes(
                old_snapshot.party_items,
                new_snapshot.party_items
            )
            changes.extend(item_changes)

            # Check container organization changes (optional, for detailed tracking)
            container_changes = self._detect_container_organization_changes(
                old_snapshot.party_items,
                new_snapshot.party_items
            )
            changes.extend(container_changes)

            # Check sharing state changes
            if old_snapshot.sharing_state != new_snapshot.sharing_state:
                sharing_change = FieldChange(
                    field_path="party_inventory.sharing_state",
                    old_value=old_snapshot.sharing_state,
                    new_value=new_snapshot.sharing_state,
                    change_type=ChangeType.MODIFIED,
                    priority=ChangePriority.MEDIUM,
                    category=ChangeCategory.INVENTORY,
                    description=f"Sharing {'enabled' if new_snapshot.sharing_state > 0 else 'disabled'}"
                )
                changes.append(sharing_change)

            if changes:
                logger.info(f"Detected {len(changes)} party inventory changes for campaign {new_snapshot.campaign_id}")
            else:
                logger.debug(f"No party inventory changes detected for campaign {new_snapshot.campaign_id}")

        except Exception as e:
            logger.error(f"Error detecting party changes: {e}")

        return changes

    def _detect_currency_changes(self, old_currency: Dict[str, int],
                               new_currency: Dict[str, int]) -> List[FieldChange]:
        """Detect changes in party currency."""
        changes = []

        # Get all currency types from both snapshots
        all_currency_types = set(old_currency.keys()) | set(new_currency.keys())

        for currency_type in all_currency_types:
            old_amount = old_currency.get(currency_type, 0)
            new_amount = new_currency.get(currency_type, 0)

            if old_amount != new_amount:
                delta = new_amount - old_amount
                change_type = ChangeType.INCREMENTED if delta > 0 else ChangeType.DECREMENTED
                priority = ChangePriority.MEDIUM if abs(delta) > 100 else ChangePriority.LOW

                change = FieldChange(
                    field_path=f"party_inventory.party_currency.{currency_type}",
                    old_value=old_amount,
                    new_value=new_amount,
                    change_type=change_type,
                    priority=priority,
                    category=ChangeCategory.INVENTORY,
                    description=f"{currency_type.upper()} {'+' if delta > 0 else ''}{delta}",
                    metadata={"delta": delta, "currency_type": currency_type}
                )
                changes.append(change)

        return changes

    def _detect_item_changes(self, old_items: List[Dict[str, Any]],
                           new_items: List[Dict[str, Any]]) -> List[FieldChange]:
        """Detect changes in party items, including container moves."""
        changes = []

        # Create lookup dictionaries by item name for comparison
        old_items_dict = {item.get('name', ''): item for item in old_items}
        new_items_dict = {item.get('name', ''): item for item in new_items}

        # Find added items
        for item_name, item_data in new_items_dict.items():
            if item_name not in old_items_dict:
                container = item_data.get('container')
                container_name = self._get_container_name(container)
                container_emoji = self._get_container_emoji(container)
                quantity = item_data.get('quantity', 1)

                if container:
                    container_info = f" to {container_emoji} {container_name}"
                else:
                    container_info = ""

                change = FieldChange(
                    field_path=f"party_inventory.party_items.{item_name}",
                    old_value=None,
                    new_value=item_data,
                    change_type=ChangeType.ADDED,
                    priority=ChangePriority.HIGH,
                    category=ChangeCategory.INVENTORY,
                    description=f"Added {quantity}x {item_name}{container_info}",
                    metadata={
                        "item_type": item_data.get('type'),
                        "container": container,
                        "container_name": container_name,
                        "container_emoji": container_emoji,
                        "rarity": item_data.get('rarity'),
                        "cost": item_data.get('cost')
                    }
                )
                changes.append(change)

        # Find removed items
        for item_name, item_data in old_items_dict.items():
            if item_name not in new_items_dict:
                container = item_data.get('container')
                container_name = self._get_container_name(container)
                container_emoji = self._get_container_emoji(container)
                quantity = item_data.get('quantity', 1)

                if container:
                    container_info = f" from {container_emoji} {container_name}"
                else:
                    container_info = ""

                change = FieldChange(
                    field_path=f"party_inventory.party_items.{item_name}",
                    old_value=item_data,
                    new_value=None,
                    change_type=ChangeType.REMOVED,
                    priority=ChangePriority.HIGH,
                    category=ChangeCategory.INVENTORY,
                    description=f"Removed {quantity}x {item_name}{container_info}",
                    metadata={
                        "item_type": item_data.get('type'),
                        "container": container,
                        "container_name": container_name,
                        "container_emoji": container_emoji,
                        "rarity": item_data.get('rarity'),
                        "cost": item_data.get('cost')
                    }
                )
                changes.append(change)

        # Find modified items (quantity changes and container moves)
        for item_name in old_items_dict:
            if item_name in new_items_dict:
                old_item = old_items_dict[item_name]
                new_item = new_items_dict[item_name]

                # Check for quantity changes
                old_qty = old_item.get('quantity', 1)
                new_qty = new_item.get('quantity', 1)

                if old_qty != new_qty:
                    delta = new_qty - old_qty
                    change_type = ChangeType.INCREMENTED if delta > 0 else ChangeType.DECREMENTED
                    container_info = self._get_container_description(new_item.get('container'))

                    change = FieldChange(
                        field_path=f"party_inventory.party_items.{item_name}.quantity",
                        old_value=old_qty,
                        new_value=new_qty,
                        change_type=change_type,
                        priority=ChangePriority.MEDIUM,
                        category=ChangeCategory.INVENTORY,
                        description=f"{item_name} quantity {'+' if delta > 0 else ''}{delta} ({old_qty} → {new_qty}){container_info}",
                        metadata={
                            "delta": delta,
                            "item_type": new_item.get('type'),
                            "container": new_item.get('container')
                        }
                    )
                    changes.append(change)

                # Check for container moves
                old_container = old_item.get('container', '')
                new_container = new_item.get('container', '')

                if old_container != new_container:
                    old_container_desc = self._get_container_name(old_container)
                    new_container_desc = self._get_container_name(new_container)
                    old_emoji = self._get_container_emoji(old_container)
                    new_emoji = self._get_container_emoji(new_container)

                    # Create more descriptive move message
                    quantity = new_item.get('quantity', 1)
                    quantity_text = f"{quantity}x " if quantity > 1 else ""

                    change = FieldChange(
                        field_path=f"party_inventory.party_items.{item_name}.container",
                        old_value=old_container,
                        new_value=new_container,
                        change_type=ChangeType.MOVED,
                        priority=ChangePriority.MEDIUM,
                        category=ChangeCategory.INVENTORY,
                        description=f"📦➡️ Moved {quantity_text}{item_name} from {old_emoji} {old_container_desc} to {new_emoji} {new_container_desc}",
                        metadata={
                            "item_type": new_item.get('type'),
                            "old_container": old_container,
                            "new_container": new_container,
                            "quantity": quantity,
                            "old_container_emoji": old_emoji,
                            "new_container_emoji": new_emoji
                        }
                    )
                    changes.append(change)

        return changes

    def _get_container_description(self, container: Optional[str]) -> str:
        """Get a human-readable description of where an item is stored."""
        if not container:
            return ""

        container_name = self._get_container_name(container)
        return f" (in {container_name})"

    def _get_container_name(self, container: Optional[str]) -> str:
        """Get a human-readable container name with smart detection."""
        if not container:
            return "party inventory"

        # Clean up container names for better readability
        container = str(container).strip()

        # Handle common container patterns
        if container.lower() in ['', 'none', 'null']:
            return "party inventory"

        # Handle numbered containers (e.g., "Container 1" -> "Container 1")
        if container.isdigit():
            return f"Container {container}"

        # Smart detection for known container types
        container_lower = container.lower()

        # Magical containers
        if 'bag of holding' in container_lower:
            return "Bag of Holding"
        elif 'handy haversack' in container_lower or "heward's handy haversack" in container_lower:
            return "Handy Haversack"
        elif 'portable hole' in container_lower:
            return "Portable Hole"
        elif 'efficient quiver' in container_lower:
            return "Efficient Quiver"
        elif 'alchemy jug' in container_lower:
            return "Alchemy Jug"
        elif 'decanter of endless water' in container_lower:
            return "Decanter of Endless Water"

        # Common mundane containers
        elif 'backpack' in container_lower:
            return "Backpack"
        elif 'sack' in container_lower or 'bag' in container_lower:
            return "Bag/Sack"
        elif 'chest' in container_lower:
            return "Chest"
        elif 'pouch' in container_lower:
            return "Pouch"
        elif 'belt' in container_lower:
            return "Belt/Bandolier"
        elif 'quiver' in container_lower:
            return "Quiver"
        elif 'case' in container_lower:
            return "Case"
        elif 'barrel' in container_lower or 'cask' in container_lower:
            return "Barrel/Cask"
        elif 'cart' in container_lower or 'wagon' in container_lower:
            return "Cart/Wagon"

        # Handle very long container names
        if len(container) > 50:
            return f"{container[:47]}..."

        # Return original name if no smart detection matches
        return container

    def _get_container_emoji(self, container: Optional[str]) -> str:
        """Get an appropriate emoji for a container type."""
        if not container:
            return "📦"

        container_lower = str(container).lower()

        # Magical containers
        if 'bag of holding' in container_lower:
            return "🎒✨"
        elif 'handy haversack' in container_lower:
            return "🎒"
        elif 'portable hole' in container_lower:
            return "🕳️✨"
        elif 'efficient quiver' in container_lower:
            return "🏹"
        elif 'alchemy jug' in container_lower:
            return "🧪"
        elif 'decanter' in container_lower:
            return "🍺"

        # Common containers
        elif 'backpack' in container_lower:
            return "🎒"
        elif 'sack' in container_lower or 'bag' in container_lower:
            return "👜"
        elif 'chest' in container_lower:
            return "📦"
        elif 'pouch' in container_lower:
            return "👛"
        elif 'belt' in container_lower:
            return "🔗"
        elif 'quiver' in container_lower:
            return "🏹"
        elif 'case' in container_lower:
            return "💼"
        elif 'barrel' in container_lower or 'cask' in container_lower:
            return "🛢️"
        elif 'cart' in container_lower or 'wagon' in container_lower:
            return "🛒"

        return "📦"  # Default container emoji

    def _detect_container_organization_changes(self, old_items: List[Dict[str, Any]],
                                             new_items: List[Dict[str, Any]]) -> List[FieldChange]:
        """
        Detect changes in how items are organized across containers.

        This provides insights into party inventory organization patterns.
        """
        changes = []

        try:
            # Analyze container usage patterns
            old_containers = self._analyze_container_usage(old_items)
            new_containers = self._analyze_container_usage(new_items)

            # Detect new containers being used
            for container in new_containers:
                if container not in old_containers and container:
                    item_count = len(new_containers[container]['items'])
                    change = FieldChange(
                        field_path=f"party_inventory.containers.{container}",
                        old_value=None,
                        new_value=new_containers[container],
                        change_type=ChangeType.ADDED,
                        priority=ChangePriority.LOW,
                        category=ChangeCategory.INVENTORY,
                        description=f"Started using {self._get_container_name(container)} ({item_count} items)",
                        metadata={
                            "container_name": container,
                            "item_count": item_count,
                            "items": new_containers[container]['items']
                        }
                    )
                    changes.append(change)

            # Detect containers no longer being used
            for container in old_containers:
                if container not in new_containers and container:
                    item_count = len(old_containers[container]['items'])
                    change = FieldChange(
                        field_path=f"party_inventory.containers.{container}",
                        old_value=old_containers[container],
                        new_value=None,
                        change_type=ChangeType.REMOVED,
                        priority=ChangePriority.LOW,
                        category=ChangeCategory.INVENTORY,
                        description=f"No longer using {self._get_container_name(container)} (was {item_count} items)",
                        metadata={
                            "container_name": container,
                            "item_count": item_count,
                            "items": old_containers[container]['items']
                        }
                    )
                    changes.append(change)

        except Exception as e:
            logger.warning(f"Error detecting container organization changes: {e}")

        return changes

    def _analyze_container_usage(self, items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze how containers are being used."""
        containers = {}

        for item in items:
            container = item.get('container', '')
            if container not in containers:
                containers[container] = {
                    'items': [],
                    'total_quantity': 0,
                    'item_types': set()
                }

            containers[container]['items'].append(item.get('name', 'Unknown'))
            containers[container]['total_quantity'] += item.get('quantity', 1)
            if item.get('type'):
                containers[container]['item_types'].add(item.get('type'))

        # Convert sets to lists for serialization
        for container_data in containers.values():
            container_data['item_types'] = list(container_data['item_types'])

        return containers

    def process_character_for_party_changes(self, character_data: Dict[str, Any]) -> Optional[List[FieldChange]]:
        """
        Process a character's data for party inventory changes.

        This is the main entry point for integrating with existing Discord monitoring.

        Args:
            character_data: Character data that may contain party inventory

        Returns:
            List of FieldChange objects if party changes detected, None otherwise
        """
        try:
            # Extract current party inventory
            current_snapshot = self.extract_party_inventory_from_character(character_data)
            if not current_snapshot:
                return None

            # Load previous snapshot
            previous_snapshot = self.load_latest_party_snapshot(current_snapshot.campaign_id)

            # Save current snapshot
            self.save_party_snapshot(current_snapshot)

            # If no previous snapshot, this is the first time - create a "new party found" change
            if not previous_snapshot:
                logger.info(f"First party inventory snapshot for campaign {current_snapshot.campaign_id}")

                # Get campaign name for better message
                campaign_name = current_snapshot.metadata.get('campaign_name')
                campaign_display = campaign_name if campaign_name else f"Campaign {current_snapshot.campaign_id}"

                # Create a special "new party found" change for first-time detection
                new_party_change = FieldChange(
                    field_path="party_inventory.discovery",
                    old_value=None,
                    new_value="discovered",
                    change_type=ChangeType.ADDED,
                    priority=ChangePriority.HIGH,
                    category=ChangeCategory.EQUIPMENT,
                    description=f"🎒 New party inventory discovered for {campaign_display}! Now monitoring for changes.",
                    metadata={
                        "is_new_party": True,
                        "campaign_id": current_snapshot.campaign_id,
                        "campaign_name": campaign_name,
                        "item_count": len(current_snapshot.party_items),
                        "total_currency_gp": sum(current_snapshot.party_currency.get(k, 0) * v for k, v in {
                            'copper': 0.01, 'silver': 0.1, 'electrum': 0.5, 'gold': 1.0, 'platinum': 10.0
                        }.items())
                    }
                )

                return [new_party_change]

            # Detect changes
            changes = self.detect_party_changes(previous_snapshot, current_snapshot)

            if changes:
                logger.info(f"Detected {len(changes)} party inventory changes for campaign {current_snapshot.campaign_id}")
                return changes
            else:
                logger.debug(f"No party inventory changes detected for campaign {current_snapshot.campaign_id}")
                return None

        except Exception as e:
            logger.error(f"Error processing character for party changes: {e}")
            return None

    def get_virtual_character_id(self, campaign_id: str) -> int:
        """Get consistent virtual character ID for a campaign's party inventory."""
        return hash(f"party_inventory_{campaign_id}")

    def create_virtual_character_snapshot(self, campaign_id: str) -> Optional[CharacterSnapshot]:
        """
        Create a CharacterSnapshot for party inventory to integrate with Discord infrastructure.

        Args:
            campaign_id: Campaign ID to create snapshot for

        Returns:
            CharacterSnapshot representing party inventory as virtual character
        """
        latest_snapshot = self.load_latest_party_snapshot(campaign_id)
        if not latest_snapshot:
            return None

        return latest_snapshot.to_character_snapshot()


def integrate_party_tracking_with_discord_monitor():
    """
    Integration instructions for adding party inventory tracking to Discord monitor.

    This function shows how to modify the discord_monitor.py to include party tracking.
    """
    integration_code = """
    # In discord_monitor.py DiscordMonitor class:

    def __init__(self, config_path: str, use_party_mode: bool = False, character_id_override: str = None):
        # ... existing initialization ...

        # Add party inventory tracker
        self.party_tracker = PartyInventoryTracker(str(self.storage_dir))

    async def scrape_character(self, character_id: int) -> bool:
        # ... existing scraping logic ...

        # After successful character scraping, check for party inventory changes
        if character_data:  # If scraping was successful
            party_changes = self.party_tracker.process_character_for_party_changes(character_data)
            if party_changes:
                # Create virtual character changeset for party inventory
                campaign_id = character_data.get('equipment', {}).get('party_inventory', {}).get('campaign_id')
                if campaign_id:
                    virtual_character_id = self.party_tracker.get_virtual_character_id(str(campaign_id))

                    # Add virtual character to monitoring list for notifications
                    # This allows existing notification system to handle party changes
                    await self.notification_manager.handle_party_inventory_changes(
                        virtual_character_id,
                        f"Party Inventory (Campaign {campaign_id})",
                        party_changes
                    )

        return True  # existing return logic
    """

    return integration_code