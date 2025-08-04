#!/usr/bin/env python3
"""
Discord message formatter for character change notifications.

Converts character changes into rich Discord embeds with emojis,
colors, and structured formatting.
"""

import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

# Use consolidated enhanced change detection system
from discord.services.change_detection.models import CharacterChangeSet
from src.models.change_detection import FieldChange, ChangeType, ChangePriority
from discord.services.discord_service import (
    DiscordEmbed, DiscordMessage, EmbedColor,
    DISCORD_EMBED_DESC_LIMIT, DISCORD_EMBED_FIELD_LIMIT, DISCORD_EMBED_FIELD_COUNT_LIMIT,
    DISCORD_EMBEDS_PER_MESSAGE
)

logger = logging.getLogger(__name__)


class DiscordFormatter:
    """
    Formatter for Discord character change notifications.
    
    Features:
    - Rich emoji and color coding
    - Field grouping and prioritization
    - Configurable change limits per message
    - Support for multiple characters
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Discord formatter.
        
        Args:
            config: Discord configuration dictionary
        """
        self.config = config or {}
        
        # Emoji mappings for different types of changes
        self.change_emojis = {
            ChangeType.ADDED: "➕",
            ChangeType.REMOVED: "➖", 
            ChangeType.MODIFIED: "🔄",
            ChangeType.INCREMENTED: "⬆️",
            ChangeType.DECREMENTED: "⬇️"
        }
        
        # Priority emojis
        self.priority_emojis = {
            ChangePriority.LOW: "🔵",
            ChangePriority.MEDIUM: "🟡", 
            ChangePriority.HIGH: "🟠",
            ChangePriority.CRITICAL: "🔴"
        }
        
        # Field category emojis
        self.field_emojis = {
            'level': '🎯',
            'experience': '⭐',
            'hit_points': '❤️',
            'armor_class': '🛡️',
            'ability_scores': '💪',
            'spells': '✨',
            'spell_slots': '🎱',
            'subclass': '🎓',
            'inventory': '🎒',
            'equipment': '⚔️',
            'currency': '💰',
            'skills': '🎨',
            'proficiencies': '🔧',
            'feats': '🏆',
            'classes': '📚'
        }
        
        logger.info("Discord formatter initialized")
    
    def format_character_changes(
        self,
        change_set: CharacterChangeSet,
        max_changes: int = 200,
        avatar_url: Optional[str] = None
    ) -> List[DiscordMessage]:
        """
        Format character changes into Discord messages (may split into multiple).
        
        Args:
            change_set: Set of character changes
            max_changes: Maximum changes to consider (high value, splits based on Discord limits)
            avatar_url: Character avatar URL
            
        Returns:
            List of formatted Discord messages (split if needed)
        """
        # For single message with few changes, use detailed format
        if len(change_set.changes) <= 10:
            return [self._format_detailed(change_set, max_changes, avatar_url)]
        else:
            return self._format_detailed_with_splitting(change_set, max_changes, avatar_url)
    
    def _format_detailed(
        self,
        change_set: CharacterChangeSet,
        max_changes: int,
        avatar_url: Optional[str]
    ) -> DiscordMessage:
        """Format changes in detailed style with everything in description."""
        embed_color = self._get_embed_color(change_set) 
        
        # Group changes by category (if enabled)
        grouped_changes = self._group_changes_conditionally(change_set.changes)
        
        # Build description with all changes
        description_parts = [f"**{len(change_set.changes)} total changes**"]
        changes_shown = 0
        
        # Priority order for categories
        category_priority = [
            'level', 'experience', 'hit_points', 'armor_class', 'feats', 'classes',
            'subclass', 'spells', 'spell_slots', 'inventory', 'equipment', 'ability_scores',
            'skills', 'currency', 'other'
        ]
        
        for category in category_priority:
            if category not in grouped_changes or changes_shown >= max_changes:
                continue
                
            changes = grouped_changes[category]
            if not changes:
                continue
            
            # Get category emoji and title
            category_emoji = self.field_emojis.get(category, "📋")
            category_title = category.replace('_', ' ').title()
            
            # Add category header
            description_parts.append(f"{category_emoji} {category_title} ({len(changes)})")
            
            # Add individual changes
            for change in changes:
                if changes_shown >= max_changes:
                    break
                    
                emoji = self.change_emojis.get(change.change_type, "🔄")
                
                # Use full description without truncation - let Discord handle the limits
                desc = change.description
                description_parts.append(f"{emoji} {desc}")
                changes_shown += 1
        
        # Join description and check if it exceeds Discord limits
        full_description = "\n".join(description_parts)
        
        # If description is too long, fall back to detailed splitting
        if len(full_description) > DISCORD_EMBED_DESC_LIMIT:
            logger.info(f"Description too long ({len(full_description)} chars), falling back to field-based splitting")
            return self._format_detailed_with_splitting(change_set, max_changes, avatar_url)[0]
        
        # Create main embed with everything in description
        embed = DiscordEmbed(
            title=f"🎲 {change_set.character_name} Updated",
            description=full_description,
            color=embed_color.value,
            timestamp=change_set.timestamp.isoformat(),
            thumbnail={'url': avatar_url} if avatar_url else None,
            footer={
                'text': f"Version {change_set.from_version} → {change_set.to_version}"
            }
        )
        
        return DiscordMessage(embeds=[embed])
    
    def _format_detailed_with_splitting(
        self,
        change_set: CharacterChangeSet,
        max_changes: int,
        avatar_url: Optional[str]
    ) -> List[DiscordMessage]:
        """Format changes with intelligent embed/message splitting based on Discord limits."""
        embed_color = self._get_embed_color(change_set)
        
        # Sort changes by priority (critical first), then by change type, then by field path
        # This groups related operations together (e.g., all "Unequipped" before "Reorganized")
        try:
            sorted_changes = sorted(
                change_set.changes[:max_changes],
                key=lambda c: (
                    c.priority.value if hasattr(c.priority, 'value') else 0,
                    c.change_type.value if hasattr(c.change_type, 'value') else 0,
                    str(c.field_path)
                ),
                reverse=True
            )
        except (TypeError, AttributeError) as e:
            logger.warning(f"Error sorting changes, using original order: {e}")
            sorted_changes = change_set.changes[:max_changes]
        
        # Group changes by category (if enabled)
        grouped_changes = self._group_changes_conditionally(sorted_changes)
        
        # Create embeds with multiple categories per embed when possible
        embeds = []
        current_embed_fields = []
        current_embed_size = 0
        embed_number = 1
        
        # Discord limits - less conservative to pack more content
        MAX_EMBED_SIZE = 5900  # Less conservative (Discord limit is 6000)
        MAX_FIELD_SIZE = 1000  # Less conservative (Discord limit is 1024)
        MAX_FIELDS = 24        # Less conservative (Discord limit is 25)
        
        # Base embed overhead (title, description, footer, etc.)
        base_embed_overhead = 250  # Less conservative estimate
        
        category_priority = [
            'level', 'experience', 'hit_points', 'armor_class', 'feats', 'classes',
            'subclass', 'spells', 'spell_slots', 'inventory', 'equipment', 'ability_scores',
            'skills', 'currency', 'other'
        ]
        
        for category in category_priority:
            if category not in grouped_changes:
                continue
                
            changes = grouped_changes[category]
            if not changes:
                continue
            
            # Build category field with all changes
            category_title = f"{self.field_emojis.get(category, '📋')} {category.replace('_', ' ').title()} ({len(changes)})"
            
            # Build all change lines
            change_lines = []
            for change in changes:
                emoji = self.change_emojis.get(change.change_type, "🔄")
                
                # Use full description - chunking will handle Discord limits
                desc = change.description
                change_line = f"{emoji} {desc}"
                change_lines.append(change_line)
            
            field_value = "\n".join(change_lines)
            
            # Debug logging to see what's happening  
            logger.debug(f"Category '{category}': {len(changes)} changes, field_value length: {len(field_value)}, MAX_FIELD_SIZE: {MAX_FIELD_SIZE}")
            logger.debug(f"Current embed size: {current_embed_size}, field_size: {len(category_title) + len(field_value) + 20}")
            logger.debug(f"Field value length: {len(field_value)}, MAX_FIELD_SIZE: {MAX_FIELD_SIZE}, exceeds limit: {len(field_value) > MAX_FIELD_SIZE}")
            
            # Check if this field would fit in the current embed
            field_size = len(category_title) + len(field_value) + 20
            would_fit_in_current_embed = (
                current_embed_size + field_size + base_embed_overhead <= MAX_EMBED_SIZE and
                len(current_embed_fields) < MAX_FIELDS and
                len(field_value) <= MAX_FIELD_SIZE
            )
            
            if would_fit_in_current_embed:
                # Field fits as-is in current embed - no chunking needed
                logger.debug(f"Field '{category}' fits in current embed - no chunking")
                field = {
                    'name': category_title,
                    'value': field_value,
                    'inline': False,
                    'category': category,
                    'chunk_idx': 0,
                    'total_chunks': 1
                }
                
                current_embed_fields.append(field)
                current_embed_size += field_size
                
            else:
                # Field is too large - split across multiple fields/embeds with continuation
                logger.debug(f"Field '{category}' too large - splitting with continuation")
                
                # Calculate field size for chunking (without title for continuation fields)
                available_field_size = MAX_FIELD_SIZE - 20  # Some overhead
                change_chunks = self._chunk_changes_for_field(changes, available_field_size)
                
                for chunk_idx, change_chunk in enumerate(change_chunks):
                    # Build field value for this chunk
                    chunk_lines = []
                    for change in change_chunk:
                        emoji = self.change_emojis.get(change.change_type, "🔄")
                        desc = change.description
                        chunk_lines.append(f"{emoji} {desc}")
                    
                    chunk_field_value = "\n".join(chunk_lines)
                    
                    # First chunk gets the category title, subsequent chunks are continuation
                    if chunk_idx == 0:
                        chunk_field_name = category_title
                    else:
                        chunk_field_name = "\u200b"  # Zero-width space for continuation
                    
                    chunk_field_size = len(chunk_field_name) + len(chunk_field_value) + 20
                    
                    # Check if we need a new embed for this chunk
                    if (current_embed_size + chunk_field_size + base_embed_overhead > MAX_EMBED_SIZE or
                        len(current_embed_fields) >= MAX_FIELDS) and current_embed_fields:
                        
                        # Create embed with current fields
                        embed = self._create_embed_from_fields(
                            change_set, current_embed_fields, embed_color, 
                            avatar_url, embed_number, len(sorted_changes)
                        )
                        embeds.append(embed)
                        
                        # Reset for next embed
                        current_embed_fields = []
                        current_embed_size = 0
                        embed_number += 1
                    
                    # Add chunk field to current embed
                    field = {
                        'name': chunk_field_name,
                        'value': chunk_field_value,
                        'inline': False,
                        'category': category
                    }
                    
                    current_embed_fields.append(field)
                    current_embed_size += chunk_field_size
        
        # Create final embed if there are remaining fields
        if current_embed_fields:
            embed = self._create_embed_from_fields(
                change_set, current_embed_fields, embed_color,
                avatar_url, embed_number, len(sorted_changes)
            )
            embeds.append(embed)
        
        # Group embeds into messages (max 10 embeds per message)
        messages = []
        for i in range(0, len(embeds), DISCORD_EMBEDS_PER_MESSAGE):
            embed_batch = embeds[i:i + DISCORD_EMBEDS_PER_MESSAGE]
            message = DiscordMessage(embeds=embed_batch)
            messages.append(message)
        
        # Log splitting info
        if len(embeds) > 1:
            logger.info(f"Split {len(sorted_changes)} character changes into {len(embeds)} embeds across {len(messages)} Discord messages")
            for i, msg in enumerate(messages, 1):
                logger.debug(f"Message {i}: {len(msg.embeds)} embeds")
        
        return messages if messages else [self._create_empty_message(change_set, embed_color, avatar_url)]
    
    def _fix_part_numbers_for_embed(self, fields: List[Dict[str, Any]]) -> None:
        """Fix part numbers for fields in an embed - only add part numbers if category is split across embeds."""
        # Group fields by category
        category_fields = {}
        for field in fields:
            if 'category' in field:
                category = field['category']
                if category not in category_fields:
                    category_fields[category] = []
                category_fields[category].append(field)
        
        # For each category, determine if we need part numbers
        for category, cat_fields in category_fields.items():
            if len(cat_fields) <= 1:
                # Single field for this category - no part numbers needed
                continue
                
            # Multiple fields for this category in this embed
            # Check if all chunks of this category are in this embed
            chunk_indices = [f['chunk_idx'] for f in cat_fields]
            total_chunks = cat_fields[0]['total_chunks']
            
            # If we have all chunks of this category in this embed, don't use part numbers
            if len(chunk_indices) == total_chunks and set(chunk_indices) == set(range(total_chunks)):
                # All chunks are in this embed - no part numbers needed
                continue
            else:
                # Category is split - add part numbers
                for field in cat_fields:
                    if field['total_chunks'] > 1:
                        field['name'] += f" (Part {field['chunk_idx'] + 1})"
    
    def _chunk_changes_for_field(self, changes: List[FieldChange], max_field_content_size: int) -> List[List[FieldChange]]:
        """Split changes into chunks that fit within Discord field limits."""
        chunks = []
        current_chunk = []
        current_size = 0
        
        # Log the chunking parameters for debugging
        logger.debug(f"Chunking {len(changes)} changes with max field size: {max_field_content_size}")
        
        for change in changes:
            # Estimate size of this change line more accurately
            emoji = self.change_emojis.get(change.change_type, "🔄")
            desc = change.description
            
            # Instead of truncating individual descriptions, preserve full content
            # and let the chunking handle the splitting
            change_line = f"{emoji} {desc}"
            change_size = len(change_line) + 1  # +1 for newline
            
            # If a single change is too large for a field, we need to split the description
            if change_size > max_field_content_size:
                # Split this single change into multiple chunks
                split_chunks = self._split_large_change_description(change, emoji, max_field_content_size)
                for split_chunk in split_chunks:
                    if current_chunk and current_size + len(split_chunk) + 1 > max_field_content_size:
                        # Start new chunk
                        chunks.append(current_chunk)
                        current_chunk = []
                        current_size = 0
                    
                    # Create a pseudo-change for this split
                    split_change = type('SplitChange', (), {
                        'description': split_chunk.replace(emoji + " ", ""),
                        'change_type': change.change_type,
                        'field_path': change.field_path
                    })()
                    
                    current_chunk.append(split_change)
                    current_size += len(split_chunk) + 1
                continue
            
            # Normal chunking logic
            if current_size + change_size > max_field_content_size and current_chunk:
                logger.debug(f"Creating chunk with {len(current_chunk)} changes, size: {current_size}")
                chunks.append(current_chunk)
                current_chunk = []
                current_size = 0
            
            current_chunk.append(change)
            current_size += change_size
        
        # Add remaining changes
        if current_chunk:
            logger.debug(f"Final chunk with {len(current_chunk)} changes, size: {current_size}")
            chunks.append(current_chunk)
        
        logger.debug(f"Created {len(chunks)} chunks total")
        return chunks
    
    def _split_large_change_description(self, change: FieldChange, emoji: str, max_size: int) -> List[str]:
        """Split a large change description into multiple parts that fit in Discord fields."""
        desc = change.description
        max_desc_length = max_size - len(emoji) - 10  # Account for emoji and some padding
        
        if len(desc) <= max_desc_length:
            return [f"{emoji} {desc}"]
        
        # Split the description into parts
        parts = []
        remaining = desc
        part_num = 1
        
        while remaining:
            if len(remaining) <= max_desc_length:
                # Last part
                if part_num == 1:
                    parts.append(f"{emoji} {remaining}")
                else:
                    parts.append(f"{emoji} {remaining}")
                break
            else:
                # Find a good break point (prefer word boundaries)
                break_point = max_desc_length
                
                # Look for word boundary within last 50 characters
                for i in range(max_desc_length - 50, max_desc_length):
                    if i < len(remaining) and remaining[i] in ' \t\n-.,;:':
                        break_point = i
                        break
                
                part_text = remaining[:break_point].rstrip()
                if part_num == 1:
                    parts.append(f"{emoji} {part_text}...")
                else:
                    parts.append(f"{emoji} ...{part_text}...")
                
                remaining = remaining[break_point:].lstrip()
                part_num += 1
        
        logger.debug(f"Split large description into {len(parts)} parts")
        return parts
    
    def _create_empty_message(self, change_set: CharacterChangeSet, embed_color: EmbedColor, avatar_url: Optional[str]) -> DiscordMessage:
        """Create a message when no changes to display."""
        embed = DiscordEmbed(
            title=f"🎲 {change_set.character_name} Updated",
            description="No displayable changes found.",
            color=embed_color.value,
            timestamp=change_set.timestamp.isoformat(),
            thumbnail={'url': avatar_url} if avatar_url else None,
            footer={
                'text': f"Version {change_set.from_version} → {change_set.to_version}"
            }
        )
        
        return DiscordMessage(embeds=[embed])
    
    def _create_embed_from_fields(
        self,
        change_set: CharacterChangeSet,
        fields: List[Dict[str, Any]],
        embed_color: EmbedColor,
        avatar_url: Optional[str],
        embed_number: int,
        total_changes: int
    ) -> DiscordEmbed:
        """Create an embed from a list of fields."""
        embed_title = f"🎲 {change_set.character_name} Updated"
        if embed_number > 1:
            embed_title += f" (Part {embed_number})"
        
        # Ensure title doesn't exceed Discord limits
        if len(embed_title) > 256:
            embed_title = embed_title[:253] + "..."
        
        # Count changes in this embed
        changes_in_embed = sum(field['value'].count('\n') + 1 for field in fields)
        
        description = f"**{total_changes} total changes**"
        if embed_number > 1:
            description += f"\n*Showing {changes_in_embed} changes in this embed*"
        
        # Ensure description doesn't exceed Discord limits
        if len(description) > DISCORD_EMBED_DESC_LIMIT:
            description = description[:DISCORD_EMBED_DESC_LIMIT-3] + "..."
        
        # Ensure all fields are within limits
        safe_fields = []
        for field in fields:
            safe_field = {
                'name': field['name'][:256] if len(field['name']) > 256 else field['name'],
                'value': field['value'][:DISCORD_EMBED_FIELD_LIMIT-3] + "..." if len(field['value']) > DISCORD_EMBED_FIELD_LIMIT else field['value'],
                'inline': field.get('inline', False)
            }
            safe_fields.append(safe_field)
        
        # Limit number of fields
        if len(safe_fields) > DISCORD_EMBED_FIELD_COUNT_LIMIT:
            safe_fields = safe_fields[:DISCORD_EMBED_FIELD_COUNT_LIMIT]
            logger.warning(f"Truncated fields to Discord limit of {DISCORD_EMBED_FIELD_COUNT_LIMIT}")
        
        embed = DiscordEmbed(
            title=embed_title,
            description=description,
            color=embed_color.value,
            timestamp=change_set.timestamp.isoformat(),
            fields=safe_fields,
            footer={
                "text": f"Version {change_set.from_version} → {change_set.to_version}"
            }
        )
        
        if avatar_url and embed_number == 1:  # Only add avatar to first embed
            embed.thumbnail = {"url": avatar_url}
        
        return embed
    
    def _create_split_message(
        self,
        change_set: CharacterChangeSet,
        fields: List[Dict[str, Any]],
        embed_color: EmbedColor,
        avatar_url: Optional[str],
        part_number: int,
        total_changes: int
    ) -> DiscordMessage:
        """Create a split message with the given fields."""
        title = f"🎲 {change_set.character_name} Updated"
        if part_number > 1:
            title += f" (Part {part_number})"
        
        # Ensure title doesn't exceed Discord limits
        if len(title) > 256:
            title = title[:253] + "..."
        
        # Count changes in this message
        changes_in_message = sum(field['value'].count('\n') + 1 for field in fields)
        
        description = f"**{total_changes} total changes**"
        if part_number > 1:
            description += f"\n*Showing {changes_in_message} changes in this message*"
        
        # Ensure description doesn't exceed Discord limits
        if len(description) > DISCORD_EMBED_DESC_LIMIT:
            description = description[:DISCORD_EMBED_DESC_LIMIT-3] + "..."
        
        # Ensure all fields are within limits
        safe_fields = []
        for field in fields:
            safe_field = {
                'name': field['name'][:256] if len(field['name']) > 256 else field['name'],
                'value': field['value'][:DISCORD_EMBED_FIELD_LIMIT-3] + "..." if len(field['value']) > DISCORD_EMBED_FIELD_LIMIT else field['value'],
                'inline': field.get('inline', False)
            }
            safe_fields.append(safe_field)
        
        # Limit number of fields
        if len(safe_fields) > DISCORD_EMBED_FIELD_COUNT_LIMIT:
            safe_fields = safe_fields[:DISCORD_EMBED_FIELD_COUNT_LIMIT]
            logger.warning(f"Truncated fields to Discord limit of {DISCORD_EMBED_FIELD_COUNT_LIMIT}")
        
        embed = DiscordEmbed(
            title=title,
            description=description,
            color=embed_color.value,
            timestamp=change_set.timestamp.isoformat(),
            fields=safe_fields,
            footer={
                "text": f"Version {change_set.from_version} → {change_set.to_version}"
            }
        )
        
        if avatar_url:
            embed.thumbnail = {"url": avatar_url}
        
        return DiscordMessage(embeds=[embed])
    
    def _get_embed_color(self, change_set: CharacterChangeSet) -> EmbedColor:
        """Determine embed color based on change types and priority."""
        
        # Check if priority-based coloring is enabled
        discord_config = self.config.get('discord', {})
        use_priority_colors = discord_config.get('color_code_by_priority', False)
        
        if use_priority_colors:
            # Use priority-based coloring
            highest_priority = self._get_highest_priority(change_set.changes)
            
            if highest_priority == ChangePriority.CRITICAL:
                return EmbedColor.PRIORITY_CRITICAL
            elif highest_priority == ChangePriority.HIGH:
                return EmbedColor.PRIORITY_HIGH
            elif highest_priority == ChangePriority.MEDIUM:
                return EmbedColor.PRIORITY_MEDIUM
            else:  # LOW priority
                return EmbedColor.PRIORITY_LOW
        
        # Legacy behavior: Check for specific high-impact changes
        for change in change_set.changes:
            if change.field_path.lower() == 'basic_info.level':
                return EmbedColor.LEVEL_UP
            elif any(keyword in change.field_path.lower() 
                    for keyword in ['inventory', 'equipment', 'currency']):
                return EmbedColor.INVENTORY
            elif any(keyword in change.field_path.lower() 
                    for keyword in ['hit_points', 'armor_class', 'saving_throws']):
                return EmbedColor.COMBAT
            elif any(keyword in change.field_path.lower() 
                    for keyword in ['spells', 'spell_slots']):
                return EmbedColor.SPELLS
        
        # Default based on priority (legacy)
        if change_set.has_high_priority_changes():
            return EmbedColor.WARNING
        else:
            return EmbedColor.INFO
    
    def _get_highest_priority(self, changes: List[FieldChange]) -> ChangePriority:
        """Get the highest priority from a list of changes."""
        if not changes:
            return ChangePriority.LOW
        
        # Priority order: CRITICAL > HIGH > MEDIUM > LOW
        priority_values = {
            ChangePriority.CRITICAL: 4,
            ChangePriority.HIGH: 3,
            ChangePriority.MEDIUM: 2,
            ChangePriority.LOW: 1
        }
        
        highest_value = 0
        highest_priority = ChangePriority.LOW
        
        for change in changes:
            change_value = priority_values.get(change.priority, 1)
            if change_value > highest_value:
                highest_value = change_value
                highest_priority = change.priority
        
        return highest_priority
    
    def _group_changes_conditionally(self, changes: List[FieldChange]) -> Dict[str, List[FieldChange]]:
        """Group changes by category if grouping is enabled, otherwise create individual groups."""
        discord_config = self.config.get('discord', {})
        group_related_changes = discord_config.get('group_related_changes', True)
        
        if group_related_changes:
            # Use normal category-based grouping
            return self._group_changes_by_category(changes)
        else:
            # Create individual groups (one change per group)
            individual_groups = {}
            for i, change in enumerate(changes):
                # Create unique group name for each change
                group_name = f"change_{i}_{change.field_path.split('.')[-1]}"
                individual_groups[group_name] = [change]
            return individual_groups
    
    def _group_changes_by_category(self, changes: List[FieldChange]) -> Dict[str, List[FieldChange]]:
        """Group changes by field category."""
        groups = {}
        
        for change in changes:
            category = self._categorize_field(change.field_path)
            if category not in groups:
                groups[category] = []
            groups[category].append(change)
        
        # Sort changes within each group with category-specific logic
        for category in groups:
            if category == 'spells':
                groups[category].sort(key=self._spell_sort_key)
            elif category == 'equipment':
                groups[category].sort(key=self._equipment_sort_key)
            elif category == 'ability_scores':
                groups[category].sort(key=self._ability_score_sort_key)
            elif category == 'skills':
                groups[category].sort(key=self._skills_sort_key)
            else:
                groups[category].sort(key=lambda c: c.field_path)
        
        return groups
    
    def _categorize_field(self, field_path: str) -> str:
        """Categorize a field path into a logical group."""
        path_lower = field_path.lower()
        
        # Test specific cases first
        if 'spells.race.' in path_lower or 'spells.' in path_lower:
            logger.debug(f"Field path '{field_path}' explicitly matched spells category")
            return 'spells'
        
        # Check each category pattern (order matters - more specific patterns first)
        category_patterns = {
            'level': ['character_info.level', 'basic_info.level'],
            'experience': ['character_info.experience', 'experience_points', 'experience', 'xp'],
            'hit_points': ['hit_points', 'hp', 'character.hit_points'],  # Enhanced detector paths
            'spell_slots': ['spell_slots'],  # Must come before armor_class to avoid 'ac' match
            'subclass': ['.subclass', 'character.classes.'],  # Enhanced detector paths
            'armor_class': ['armor_class', 'ac'],
            'classes': ['character_info.classes', 'classes', 'class'],
            'ability_scores': ['ability_scores', 'ability_modifiers', 'character.ability_scores'],
            'spells': ['spells.', 'learned spell', 'forgot spell', 'character.spells'],
            'inventory': ['inventory', 'character.inventory'],
            'equipment': ['equipment', 'item_counts', 'weight_distribution', 'container_summary'],
            'currency': ['currency', 'gold', 'silver', 'copper'],
            'skills': ['skills', 'character.skills'],
            'proficiencies': ['proficiencies', 'character.proficiencies'],
            'feats': ['feats', 'character.feats']
        }
        
        for category, patterns in category_patterns.items():
            for pattern in patterns:
                if pattern in path_lower:
                    logger.debug(f"Field path '{field_path}' matched category '{category}' via pattern '{pattern}'")
                    return category
        
        # Add debug logging for uncategorized fields
        logger.debug(f"Uncategorized field path: {field_path}")
        return 'other'
    
    def _spell_sort_key(self, change: FieldChange) -> tuple:
        """
        Custom sorting key for spells: Forgot first, then Learned, both sorted by level then alphabetically.
        
        Returns:
            Tuple for sorting: (change_type_priority, spell_level, spell_name)
        """
        try:
            # Extract spell information from the description
            description = change.description.lower()
            
            # Determine change type priority: Forgot (0) comes before Learned (1)
            if "forgot" in description:
                change_type_priority = 0
            elif "learned" in description:
                change_type_priority = 1
            else:
                change_type_priority = 2  # Other spell changes last
            
            # Extract spell level from description
            spell_level = 999  # Default for unknown levels
            if "cantrip" in description:
                spell_level = 0
            else:
                # Look for "level X" pattern
                level_match = re.search(r'level (\d+)', description)
                if level_match:
                    spell_level = int(level_match.group(1))
            
            # Extract spell name for alphabetical sorting
            # Pattern: "Forgot/Learned [level X/cantrip] spell: SpellName (from source)"
            spell_name = ""
            name_match = re.search(r'spell: ([^(]+)', description)
            if name_match:
                spell_name = name_match.group(1).strip().lower()
            
            return (change_type_priority, spell_level, spell_name)
            
        except Exception as e:
            logger.warning(f"Error parsing spell change for sorting: {e}")
            # Fallback to basic field path sorting
            return (999, 999, change.field_path)
    
    def _equipment_sort_key(self, change: FieldChange) -> tuple:
        """
        Custom sorting key for equipment: Moved, Reordered, Added, Removed, Quantity changes.
        Note: Equipped/Unequipped and internal categorization moves are filtered out of Discord notifications.
        
        Returns:
            Tuple for sorting: (change_type_priority, item_name)
        """
        try:
            description = change.description.lower()
            
            # Determine change type priority (equipped/unequipped filtered out for Discord)
            if "moved" in description and ("container" in description or "equipment" in description):
                change_type_priority = 0  # Inventory organization first
            elif "reordered" in description:
                change_type_priority = 1  # Inventory organization
            elif "added" in description or "gained" in description:
                change_type_priority = 2  # New acquisitions
            elif "removed" in description or "lost" in description:
                change_type_priority = 3  # Losses
            elif "quantity" in description or "changed from" in description:
                change_type_priority = 4  # Quantity changes
            else:
                change_type_priority = 5  # Other changes
            
            # Extract item name for alphabetical sorting within each type
            item_name = ""
            # Try to extract item name from various description patterns
            if "moved" in description:
                # "Moved rope from backpack to bag of holding"
                match = re.search(r'moved\s+(.+?)\s+from', description)
                if match:
                    item_name = match.group(1).strip()
            elif "reordered" in description:
                # "Reordered Crossbow Bolts within basic equipment"
                match = re.search(r'reordered\s+(.+?)\s+within', description)
                if match:
                    item_name = match.group(1).strip()
            
            return (change_type_priority, item_name.lower())
            
        except Exception as e:
            logger.warning(f"Error parsing equipment change for sorting: {e}")
            return (999, change.field_path)
    
    def _ability_score_sort_key(self, change: FieldChange) -> tuple:
        """
        Custom sorting key for ability scores: D&D standard order (STR, DEX, CON, INT, WIS, CHA).
        
        Returns:
            Tuple for sorting: (ability_priority, change_direction, description)
        """
        try:
            description = change.description.lower()
            
            # D&D standard ability score order
            ability_order = {
                'strength': 0, 'str': 0,
                'dexterity': 1, 'dex': 1, 
                'constitution': 2, 'con': 2,
                'intelligence': 3, 'int': 3,
                'wisdom': 4, 'wis': 4,
                'charisma': 5, 'cha': 5
            }
            
            # Find which ability this change affects
            ability_priority = 999
            for ability, priority in ability_order.items():
                if ability in description:
                    ability_priority = priority
                    break
            
            # Determine if this is an increase or decrease (decreases first for visibility)
            change_direction = 0  # Default
            if "decreased" in description or "reduced" in description:
                change_direction = 0  # Decreases first (problems are more visible)
            elif "increased" in description or "improved" in description:
                change_direction = 1  # Increases second
            
            return (ability_priority, change_direction, description)
            
        except Exception as e:
            logger.warning(f"Error parsing ability score change for sorting: {e}")
            return (999, 0, change.field_path)
    
    def _skills_sort_key(self, change: FieldChange) -> tuple:
        """
        Custom sorting key for skills: Expertise gained, Proficiency gained, Lost changes, Bonus changes.
        
        Returns:
            Tuple for sorting: (change_type_priority, skill_name)
        """
        try:
            description = change.description.lower()
            
            # Determine change type priority
            if "gained expertise" in description or "expertise in" in description:
                change_type_priority = 0  # Expertise gains (highest impact)
            elif "gained proficiency" in description or "proficiency in" in description:
                change_type_priority = 1  # Proficiency gains
            elif "lost proficiency" in description:
                change_type_priority = 2  # Proficiency losses
            elif "lost expertise" in description:
                change_type_priority = 3  # Expertise losses (rare but significant)
            elif "bonus" in description and ("increased" in description or "decreased" in description):
                change_type_priority = 4  # Bonus changes
            else:
                change_type_priority = 5  # Other skill changes
            
            # Extract skill name for alphabetical sorting
            skill_name = ""
            if "proficiency in" in description:
                match = re.search(r'proficiency in\s+(.+?)(?:\s+\(|$)', description)
                if match:
                    skill_name = match.group(1).strip()
            elif "expertise in" in description:
                match = re.search(r'expertise in\s+(.+?)(?:\s+\(|$)', description)
                if match:
                    skill_name = match.group(1).strip()
            
            return (change_type_priority, skill_name.lower())
            
        except Exception as e:
            logger.warning(f"Error parsing skill change for sorting: {e}")
            return (999, change.field_path)
    
    def create_summary_message(self, change_sets: List[CharacterChangeSet]) -> DiscordMessage:
        """
        Create a summary message for multiple character updates.
        
        Args:
            change_sets: List of character change sets
            
        Returns:
            Summary Discord message
        """
        if not change_sets:
            return DiscordMessage(
                content="No character changes detected in this update cycle."
            )
        
        total_changes = sum(len(cs.changes) for cs in change_sets)
        characters_with_changes = len([cs for cs in change_sets if cs.changes])
        
        # Create summary embed
        embed = DiscordEmbed(
            title="🎲 Campaign Update Summary",
            description=f"**{characters_with_changes} characters updated**\n**{total_changes} total changes detected**",
            color=EmbedColor.INFO.value,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Add field for each character
        fields = []
        for change_set in change_sets:
            if not change_set.changes:
                continue
                
            high_priority = len(change_set.get_changes_by_priority(ChangePriority.HIGH))
            
            status_emoji = "🔴" if high_priority > 0 else "🟡"
            fields.append({
                'name': f"{status_emoji} {change_set.character_name}",
                'value': f"{len(change_set.changes)} changes\nv{change_set.from_version} → v{change_set.to_version}",
                'inline': True
            })
        
        embed.fields = fields
        embed.footer = {'text': f"Individual character updates will follow"}
        
        return DiscordMessage(embeds=[embed])