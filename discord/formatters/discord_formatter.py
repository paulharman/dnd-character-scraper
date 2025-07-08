#!/usr/bin/env python3
"""
Discord message formatter for character change notifications.

Converts character changes into rich Discord embeds with emojis,
colors, and structured formatting.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

# Handle imports with fallback for different execution contexts
try:
    from services.change_detection_service import CharacterChangeSet, FieldChange, ChangeType, ChangePriority
    from services.discord_service import (
        DiscordEmbed, DiscordMessage, EmbedColor,
        DISCORD_EMBED_DESC_LIMIT, DISCORD_EMBED_FIELD_LIMIT, DISCORD_EMBED_FIELD_COUNT_LIMIT
    )
except ImportError:
    # Fallback for when running from different contexts
    import sys
    import os
    discord_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if discord_dir not in sys.path:
        sys.path.insert(0, discord_dir)
    from services.change_detection_service import CharacterChangeSet, FieldChange, ChangeType, ChangePriority
    from services.discord_service import (
        DiscordEmbed, DiscordMessage, EmbedColor,
        DISCORD_EMBED_DESC_LIMIT, DISCORD_EMBED_FIELD_LIMIT, DISCORD_EMBED_FIELD_COUNT_LIMIT
    )

logger = logging.getLogger(__name__)


class FormatType(Enum):
    """Format types for Discord notifications."""
    COMPACT = "compact"
    DETAILED = "detailed" 
    JSON = "json"


class DiscordFormatter:
    """
    Formatter for Discord character change notifications.
    
    Features:
    - Multiple format types (compact, detailed, JSON)
    - Rich emoji and color coding
    - Field grouping and prioritization
    - Configurable change limits per message
    - Support for multiple characters
    """
    
    def __init__(self, format_type: FormatType = FormatType.DETAILED):
        self.format_type = format_type
        
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
            'inventory': '🎒',
            'equipment': '⚔️',
            'currency': '💰',
            'skills': '🎨',
            'proficiencies': '🔧',
            'feats': '🏆',
            'classes': '📚'
        }
        
        logger.info(f"Discord formatter initialized with format type: {format_type.value}")
    
    def format_character_changes(
        self,
        change_set: CharacterChangeSet,
        max_changes: int = 200,  # Increased default, will split based on Discord limits
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
        if self.format_type == FormatType.COMPACT:
            return [self._format_compact(change_set, max_changes, avatar_url)]
        elif self.format_type == FormatType.DETAILED:
            return self._format_detailed_with_splitting(change_set, max_changes, avatar_url)
        elif self.format_type == FormatType.JSON:
            return [self._format_json(change_set, max_changes, avatar_url)]
        else:
            raise ValueError(f"Unknown format type: {self.format_type}")
    
    def _format_compact(
        self,
        change_set: CharacterChangeSet,
        max_changes: int,
        avatar_url: Optional[str]
    ) -> DiscordMessage:
        """Format changes in compact style."""
        embed_color = self._get_embed_color(change_set)
        
        # Group changes by priority
        high_changes = change_set.get_changes_by_priority(ChangePriority.HIGH)
        medium_changes = change_set.get_changes_by_priority(ChangePriority.MEDIUM)
        
        # Build description
        description_parts = []
        
        if high_changes:
            description_parts.append(f"**{len(high_changes)} important changes**")
            for change in high_changes[:5]:  # Show first 5 high priority
                emoji = self.change_emojis.get(change.change_type, "🔄")
                description_parts.append(f"{emoji} {change.description}")
        
        if medium_changes and len(description_parts) < max_changes:
            remaining = max_changes - len(description_parts)
            description_parts.append(f"**{len(medium_changes)} other changes**")
            for change in medium_changes[:remaining-1]:
                emoji = self.change_emojis.get(change.change_type, "🔄")
                description_parts.append(f"{emoji} {change.description}")
        
        total_changes = len(change_set.changes)
        shown_changes = min(len(description_parts), max_changes)
        
        if total_changes > shown_changes:
            description_parts.append(f"*... and {total_changes - shown_changes} more changes*")
        
        embed = DiscordEmbed(
            title=f"🎲 {change_set.character_name} Updated",
            description="\n".join(description_parts),
            color=embed_color.value,
            timestamp=change_set.timestamp.isoformat(),
            footer={
                'text': f"v{change_set.from_version} → v{change_set.to_version} • {total_changes} total changes"
            },
            thumbnail={'url': avatar_url} if avatar_url else None
        )
        
        return DiscordMessage(embeds=[embed])
    
    def _format_detailed(
        self,
        change_set: CharacterChangeSet,
        max_changes: int,
        avatar_url: Optional[str]
    ) -> DiscordMessage:
        """Format changes in detailed style with grouped fields."""
        embed_color = self._get_embed_color(change_set) 
        
        # Group changes by category
        grouped_changes = self._group_changes_by_category(change_set.changes)
        
        # Create main embed
        embed = DiscordEmbed(
            title=f"🎲 {change_set.character_name} Character Update",
            description=f"**{len(change_set.changes)} changes detected**\n{change_set.summary}",
            color=embed_color.value,
            timestamp=change_set.timestamp.isoformat(),
            thumbnail={'url': avatar_url} if avatar_url else None,
            footer={
                'text': f"Version {change_set.from_version} → {change_set.to_version}"
            }
        )
        
        # Add fields for each category
        fields = []
        changes_shown = 0
        
        # Priority order for categories
        category_priority = [
            'level', 'experience', 'hit_points', 'armor_class', 'classes',
            'spells', 'spell_slots', 'inventory', 'equipment', 'ability_scores',
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
            
            # Format changes for this category
            change_lines = []
            for change in changes:
                if changes_shown >= max_changes:
                    break
                    
                emoji = self.change_emojis.get(change.change_type, "🔄")
                
                # Allow longer descriptions for better readability
                desc = change.description
                if len(desc) > 120:
                    desc = desc[:117] + "..."
                
                change_lines.append(f"{emoji} {desc}")
                changes_shown += 1
            
            if change_lines:
                field_value = "\n".join(change_lines)
                if len(change_lines) < len(changes):
                    field_value += f"\n*... {len(changes) - len(change_lines)} more*"
                
                fields.append({
                    'name': f"{category_emoji} {category_title} ({len(changes)})",
                    'value': field_value,
                    'inline': False  # Always full width for better readability
                })
        
        embed.fields = fields
        
        # Add avatar thumbnail if available
        if avatar_url:
            embed.thumbnail = {"url": avatar_url}
        
        return DiscordMessage(embeds=[embed])
    
    def _format_detailed_with_splitting(
        self,
        change_set: CharacterChangeSet,
        max_changes: int,
        avatar_url: Optional[str]
    ) -> List[DiscordMessage]:
        """Format changes with intelligent message splitting based on Discord limits."""
        embed_color = self._get_embed_color(change_set)
        
        # Sort changes by priority (critical first) with defensive handling
        try:
            sorted_changes = sorted(
                change_set.changes[:max_changes],
                key=lambda c: (c.priority.value if hasattr(c.priority, 'value') else 0, str(c.field_path)),
                reverse=True
            )
        except (TypeError, AttributeError) as e:
            logger.warning(f"Error sorting changes, using original order: {e}")
            sorted_changes = change_set.changes[:max_changes]
        
        # Group changes by category
        grouped_changes = self._group_changes_by_category(sorted_changes)
        
        messages = []
        current_message_changes = []
        current_message_size = 0
        message_number = 1
        
        # Base embed size calculation (title, description, footer, etc.)
        base_embed_size = len(f"🎲 {change_set.character_name} Updated (Part {message_number})") + 200
        
        category_priority = [
            'level', 'experience', 'hit_points', 'armor_class', 'feats', 'classes',
            'spells', 'spell_slots', 'inventory', 'equipment', 'ability_scores',
            'skills', 'currency', 'other'
        ]
        
        for category in category_priority:
            if category not in grouped_changes:
                continue
                
            changes = grouped_changes[category]
            if not changes:
                continue
            
            # Calculate size needed for this category
            category_title = f"{self.field_emojis.get(category, '📋')} {category.replace('_', ' ').title()} ({len(changes)})"
            category_size = len(category_title) + 50  # field overhead
            
            change_lines = []
            for change in changes:
                emoji = self.change_emojis.get(change.change_type, "🔄")
                
                # Format change line with consistent 120-character limit
                desc = change.description
                if len(desc) > 120:
                    desc = desc[:117] + "..."
                
                change_line = f"{emoji} {desc}"
                change_line_size = len(change_line) + 1  # +1 for newline
                
                # Check if adding this change would exceed limits
                if (current_message_size + category_size + len("\n".join(change_lines)) + change_line_size > DISCORD_EMBED_DESC_LIMIT or 
                    len(current_message_changes) >= DISCORD_EMBED_FIELD_COUNT_LIMIT):
                    
                    # Create message with current changes
                    if current_message_changes:
                        message = self._create_split_message(
                            change_set, current_message_changes, embed_color, 
                            avatar_url, message_number, len(sorted_changes)
                        )
                        messages.append(message)
                        
                        # Reset for next message
                        current_message_changes = []
                        current_message_size = base_embed_size
                        message_number += 1
                        
                        # IMPORTANT: Also reset category state for new message
                        change_lines = []
                        category_size = 0
                
                change_lines.append(change_line)
                category_size += change_line_size
            
            # Add this category to current message
            if change_lines:
                field_value = "\n".join(change_lines)
                category_field = {
                    'name': category_title,
                    'value': field_value[:DISCORD_EMBED_FIELD_LIMIT],  # Ensure field limit
                    'inline': False  # Always full width for better readability
                }
                
                current_message_changes.append(category_field)
                current_message_size += category_size
        
        # Create final message if there are remaining changes
        if current_message_changes:
            message = self._create_split_message(
                change_set, current_message_changes, embed_color,
                avatar_url, message_number, len(sorted_changes)
            )
            messages.append(message)
        
        # Log splitting info
        if len(messages) > 1:
            logger.info(f"Split character changes into {len(messages)} Discord messages due to size limits")
        
        return messages if messages else [self._format_detailed(change_set, max_changes, avatar_url)]
    
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
        
        # Count changes in this message
        changes_in_message = sum(field['value'].count('\n') + 1 for field in fields)
        
        description = f"{total_changes} total changes"
        if part_number > 1:
            description += f" • Showing {changes_in_message} changes in this message"
        
        embed = DiscordEmbed(
            title=title,
            description=description,
            color=embed_color.value,
            timestamp=change_set.timestamp.isoformat(),
            fields=fields,
            footer={
                "text": f"Version {change_set.from_version} → {change_set.to_version}"
            }
        )
        
        if avatar_url:
            embed.thumbnail = {"url": avatar_url}
        
        return DiscordMessage(embeds=[embed])
    
    def _format_json(
        self,
        change_set: CharacterChangeSet,
        max_changes: int,
        avatar_url: Optional[str]
    ) -> DiscordMessage:
        """Format changes as JSON for debugging."""
        import json
        
        # Convert changes to serializable format
        changes_data = []
        for change in change_set.changes[:max_changes]:
            changes_data.append({
                'field': change.field_path,
                'type': change.change_type.value,
                'priority': change.priority.name,
                'old_value': str(change.old_value),
                'new_value': str(change.new_value),
                'description': change.description
            })
        
        # Create JSON content
        data = {
            'character_id': change_set.character_id,
            'character_name': change_set.character_name,
            'from_version': change_set.from_version,
            'to_version': change_set.to_version,
            'timestamp': change_set.timestamp.isoformat(),
            'total_changes': len(change_set.changes),
            'changes_shown': len(changes_data),
            'changes': changes_data
        }
        
        json_content = json.dumps(data, indent=2)
        
        # Discord has a 2000 character limit for messages
        if len(json_content) > 1900:
            json_content = json_content[:1900] + "\n... (truncated)"
        
        embed = DiscordEmbed(
            title=f"🎲 {change_set.character_name} - Change Data",
            description=f"```json\n{json_content}\n```",
            color=EmbedColor.INFO.value,
            timestamp=change_set.timestamp.isoformat(),
            footer={'text': f"JSON Debug Format"}
        )
        
        return DiscordMessage(embeds=[embed])
    
    def _get_embed_color(self, change_set: CharacterChangeSet) -> EmbedColor:
        """Determine embed color based on change types."""
        # Check for specific high-impact changes
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
        
        # Default based on priority
        if change_set.has_high_priority_changes():
            return EmbedColor.WARNING
        else:
            return EmbedColor.INFO
    
    def _group_changes_by_category(self, changes: List[FieldChange]) -> Dict[str, List[FieldChange]]:
        """Group changes by field category."""
        groups = {}
        
        for change in changes:
            category = self._categorize_field(change.field_path)
            if category not in groups:
                groups[category] = []
            groups[category].append(change)
        
        return groups
    
    def _categorize_field(self, field_path: str) -> str:
        """Categorize a field path into a logical group."""
        path_lower = field_path.lower()
        
        # Check each category pattern
        category_patterns = {
            'level': ['basic_info.level'],
            'experience': ['experience', 'xp'],
            'hit_points': ['hit_points', 'hp'],
            'armor_class': ['armor_class', 'ac'],
            'classes': ['classes', 'class'],
            'ability_scores': ['ability_scores', 'ability_modifiers'],
            'spells': ['spells.'],
            'spell_slots': ['spell_slots'],
            'inventory': ['inventory'],
            'equipment': ['equipment'],
            'currency': ['currency', 'gold', 'silver', 'copper'],
            'skills': ['skills'],
            'proficiencies': ['proficiencies'],
            'feats': ['feats']
        }
        
        for category, patterns in category_patterns.items():
            if any(pattern in path_lower for pattern in patterns):
                return category
        
        return 'other'
    
    def format_multiple_characters(
        self,
        change_sets: List[CharacterChangeSet],
        max_changes_per_character: int = 10
    ) -> List[DiscordMessage]:
        """
        Format changes for multiple characters.
        
        Args:
            change_sets: List of character change sets
            max_changes_per_character: Max changes to show per character
            
        Returns:
            List of Discord messages (one per character)
        """
        messages = []
        
        for change_set in change_sets:
            if change_set.changes:  # Only send if there are changes
                message = self.format_character_changes(
                    change_set, 
                    max_changes_per_character
                )
                messages.append(message)
        
        logger.info(f"Formatted {len(messages)} Discord messages for {len(change_sets)} characters")
        return messages
    
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