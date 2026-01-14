"""
Action Attack Extractor for D&D Beyond Actions.

Extracts attack actions from D&D Beyond's actions system, including:
- Monk unarmed strikes and martial arts
- Racial attacks (e.g., Tabaxi claws)
- Class feature attacks
- Item-granted attacks
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ActionAttack:
    """Represents an attack action from D&D Beyond."""
    name: str
    description: str
    attack_type: str  # 'melee' or 'ranged'
    activation_type: str  # 'action', 'bonus_action', 'reaction'
    attack_bonus: int
    damage_dice: str
    damage_bonus: int
    damage_type: str
    range_normal: Optional[int] = None
    range_long: Optional[int] = None
    uses_martial_arts: bool = False
    source: str = 'class'  # 'class', 'race', 'feat', 'item'


class ActionAttackExtractor:
    """Extracts attack actions from D&D Beyond character data."""

    # Activation type mappings
    ACTIVATION_TYPES = {
        1: 'action',
        2: 'no_action',
        3: 'bonus_action',
        4: 'reaction',
        5: 'minute',
        6: 'hour',
        7: 'special',
        8: 'legendary_action',
        9: 'mythic_action',
        10: 'lair_action'
    }

    # Attack type range mappings
    ATTACK_RANGES = {
        1: 'melee',
        2: 'ranged',
        3: 'melee_or_ranged'
    }

    # Damage type mappings (common ones)
    DAMAGE_TYPES = {
        1: 'bludgeoning',
        2: 'piercing',
        3: 'slashing',
        4: 'necrotic',
        5: 'acid',
        6: 'cold',
        7: 'fire',
        8: 'lightning',
        9: 'thunder',
        10: 'poison',
        11: 'psychic',
        12: 'radiant',
        13: 'force'
    }

    def __init__(self):
        """Initialize the action attack extractor."""
        self.logger = logging.getLogger(__name__)

    def extract_attacks(self, raw_data: Dict[str, Any], calculated_ability_scores: Dict[str, int]) -> List[ActionAttack]:
        """
        Extract attack actions from raw D&D Beyond character data.

        Args:
            raw_data: Raw character data from D&D Beyond API
            calculated_ability_scores: Pre-calculated ability scores (including all bonuses from items, feats, etc.)

        Returns:
            List of ActionAttack objects
        """
        attacks = []

        # Get character stats for attack calculation
        ability_scores = calculated_ability_scores
        prof_bonus = self._get_proficiency_bonus(raw_data)
        martial_arts_die = self._get_martial_arts_die(raw_data)

        # Extract actions from each source
        actions_data = raw_data.get('actions', {})

        for source_type in ['race', 'class', 'feat', 'item']:
            action_list = actions_data.get(source_type, [])
            if not isinstance(action_list, list):
                continue

            for action in action_list:
                # Check if this is an attack action
                if not self._is_attack_action(action):
                    continue

                try:
                    attack = self._create_attack_from_action(
                        action=action,
                        source=source_type,
                        ability_scores=ability_scores,
                        prof_bonus=prof_bonus,
                        martial_arts_die=martial_arts_die,
                        raw_data=raw_data
                    )
                    if attack:
                        attacks.append(attack)
                        self.logger.debug(f"Extracted {source_type} attack: {attack.name}")
                except Exception as e:
                    self.logger.warning(f"Failed to extract attack '{action.get('name')}': {e}")

        return attacks

    def _is_attack_action(self, action: Dict[str, Any]) -> bool:
        """Check if an action is an attack."""
        # Check displayAsAttack flag
        if action.get('displayAsAttack'):
            return True

        # Check if it has attack type range
        if action.get('attackTypeRange'):
            return True

        # Check if explicitly marked as attack
        if action.get('isAttack'):
            return True

        return False

    def _create_attack_from_action(
        self,
        action: Dict[str, Any],
        source: str,
        ability_scores: Dict[str, int],
        prof_bonus: int,
        martial_arts_die: Optional[str],
        raw_data: Dict[str, Any]
    ) -> Optional[ActionAttack]:
        """Create an ActionAttack from a D&D Beyond action."""

        name = action.get('name', 'Unknown Attack')
        snippet = action.get('snippet', '')
        description = action.get('description', snippet)

        # Get attack type (melee/ranged)
        attack_type_id = action.get('attackTypeRange', 1)
        attack_type = self.ATTACK_RANGES.get(attack_type_id, 'melee')

        # Get activation type
        activation = action.get('activation', {})
        activation_type_id = activation.get('activationType', 1)
        activation_type = self.ACTIVATION_TYPES.get(activation_type_id, 'action')

        # Get damage type
        damage_type_id = action.get('damageTypeId', 1)
        damage_type = self.DAMAGE_TYPES.get(damage_type_id, 'bludgeoning')

        # Check if this uses martial arts
        uses_martial_arts = action.get('isMartialArts', False)

        # Determine ability modifier
        ability_mod_stat_id = action.get('abilityModifierStatId')
        if ability_mod_stat_id:
            # Map stat ID to ability (1=STR, 2=DEX, etc.)
            ability_map = {1: 'strength', 2: 'dexterity', 3: 'constitution',
                          4: 'intelligence', 5: 'wisdom', 6: 'charisma'}
            ability_name = ability_map.get(ability_mod_stat_id, 'strength')
            ability_mod = self._get_ability_modifier(ability_scores.get(ability_name, 10))
        else:
            # For monk attacks, can use DEX or STR (use higher)
            str_mod = self._get_ability_modifier(ability_scores.get('strength', 10))
            dex_mod = self._get_ability_modifier(ability_scores.get('dexterity', 10))
            ability_mod = max(str_mod, dex_mod)

        # Calculate attack bonus
        fixed_to_hit = action.get('fixedToHit')
        if fixed_to_hit is not None:
            attack_bonus = fixed_to_hit
        else:
            is_proficient = action.get('isProficient', False)
            attack_bonus = ability_mod
            if is_proficient:
                attack_bonus += prof_bonus

        # Check for item bonuses to unarmed attacks
        unarmed_attack_bonus, unarmed_damage_bonus = self._get_unarmed_attack_bonuses(raw_data, name)

        # Add unarmed attack item bonus to attack roll
        attack_bonus += unarmed_attack_bonus

        # Determine damage dice and bonus
        dice = action.get('dice')

        # Check if this uses martial arts die (monk feature)
        if uses_martial_arts and martial_arts_die:
            # Monks can use martial arts die instead of normal damage
            damage_dice = martial_arts_die
            damage_bonus = ability_mod + unarmed_damage_bonus
        elif dice:
            # Action has explicit dice defined (e.g., weapon attacks, racial attacks)
            dice_count = dice.get('diceCount', 1)
            dice_value = dice.get('diceValue', 6)
            dice_multiplier = dice.get('diceMultiplier')

            if dice_multiplier:
                damage_dice = f"{dice_count}d{dice_value}×{dice_multiplier}"
            else:
                damage_dice = f"{dice_count}d{dice_value}"

            value = action.get('value', 0)
            damage_bonus = ability_mod + (value if value else 0) + unarmed_damage_bonus
        else:
            # Default unarmed strike: 1 + STR modifier
            # All characters can make unarmed strikes
            damage_dice = "1"
            damage_bonus = ability_mod + unarmed_damage_bonus

        # Get range if applicable
        range_info = action.get('range', {})
        range_normal = range_info.get('range') if range_info else None
        range_long = range_info.get('longRange') if range_info else None

        # For melee attacks, default to 5 ft reach
        if attack_type == 'melee' and not range_normal:
            range_normal = 5

        return ActionAttack(
            name=name,
            description=snippet or description[:200],
            attack_type=attack_type,
            activation_type=activation_type,
            attack_bonus=attack_bonus,
            damage_dice=damage_dice,
            damage_bonus=damage_bonus,
            damage_type=damage_type,
            range_normal=range_normal,
            range_long=range_long,
            uses_martial_arts=uses_martial_arts,
            source=source
        )

    def _get_proficiency_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Calculate proficiency bonus from character level."""
        classes = raw_data.get('classes', [])
        total_level = sum(c.get('level', 0) for c in classes)
        return 2 + ((max(1, total_level) - 1) // 4)

    def _get_martial_arts_die(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """Get the martial arts die for monk characters."""
        classes = raw_data.get('classes', [])

        for class_data in classes:
            class_name = class_data.get('definition', {}).get('name', '').lower()
            if 'monk' in class_name:
                level = class_data.get('level', 1)
                # Martial arts die progression
                if level >= 17:
                    return '1d12'
                elif level >= 11:
                    return '1d10'
                elif level >= 5:
                    return '1d8'
                else:
                    return '1d6'

        return None

    def _get_ability_modifier(self, score: int) -> int:
        """Calculate ability modifier from score."""
        return (score - 10) // 2

    def _get_unarmed_attack_bonuses(self, raw_data: Dict[str, Any], attack_name: str) -> tuple[int, int]:
        """
        Get item bonuses that apply to unarmed attacks.

        Args:
            raw_data: Raw character data from D&D Beyond API
            attack_name: Name of the attack being processed

        Returns:
            Tuple of (attack_bonus, damage_bonus)
        """
        attack_bonus = 0
        damage_bonus = 0

        # Check for item modifiers that grant bonuses to unarmed attacks
        modifiers = raw_data.get('modifiers', {})
        item_modifiers = modifiers.get('item', [])

        if not isinstance(item_modifiers, list):
            return (attack_bonus, damage_bonus)

        # Get equipped items
        inventory = raw_data.get('inventory', [])
        equipped_item_ids = set()
        for item in inventory:
            if item.get('equipped', False):
                item_id = item.get('definition', {}).get('id')
                if item_id:
                    equipped_item_ids.add(item_id)

        for modifier in item_modifiers:
            # Only process modifiers that grant bonuses to unarmed attacks
            if modifier.get('subType') != 'unarmed-attacks':
                continue

            # Check if the item is equipped
            component_id = modifier.get('componentId')
            if component_id and component_id not in equipped_item_ids:
                continue  # Skip unequipped items

            # Check if modifier is granted
            if not modifier.get('isGranted', False):
                continue

            modifier_type = modifier.get('type')

            # Attack roll bonus
            if modifier_type == 'bonus':
                bonus_value = modifier.get('fixedValue') or modifier.get('value', 0)
                attack_bonus += bonus_value
                self.logger.debug(f"Found unarmed attack bonus: +{bonus_value} from item {component_id}")

            # Damage bonus
            elif modifier_type == 'damage':
                bonus_value = modifier.get('fixedValue') or modifier.get('value', 0)
                damage_bonus += bonus_value
                self.logger.debug(f"Found unarmed damage bonus: +{bonus_value} from item {component_id}")

        return (attack_bonus, damage_bonus)
