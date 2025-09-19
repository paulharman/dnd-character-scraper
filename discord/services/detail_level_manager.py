#!/usr/bin/env python3
"""
Detail Level Manager for Discord vs Change Log formatting.

Manages different levels of detail between Discord notifications and comprehensive change logs,
providing appropriate formatting for each context.
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum

# Use consolidated enhanced change detection system
from shared.models.change_detection import FieldChange, ChangeType, ChangePriority

# Import change log models
try:
    from discord.core.models.change_log import ChangeAttribution, ChangeCausation
except ImportError:
    # Fallback for when running from different contexts
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from discord.core.models.change_log import ChangeAttribution, ChangeCausation

logger = logging.getLogger(__name__)


class DetailLevel(Enum):
    """Detail levels for different contexts."""
    DISCORD_BRIEF = "discord_brief"
    DISCORD_DETAILED = "discord_detailed"
    CHANGE_LOG_COMPREHENSIVE = "change_log_comprehensive"


class DetailLevelManager:
    """
    Manages different detail levels for Discord notifications vs change logs.
    
    Features:
    - Context-appropriate formatting
    - Attribution integration
    - Causation explanation
    - Length management for Discord limits
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Maximum lengths for different contexts
        self.max_lengths = {
            DetailLevel.DISCORD_BRIEF: 80,
            DetailLevel.DISCORD_DETAILED: 150,
            DetailLevel.CHANGE_LOG_COMPREHENSIVE: 500
        }
        
        # Attribution templates for different detail levels
        self.attribution_templates = {
            DetailLevel.DISCORD_BRIEF: {
                'feat_selection': "({source_name})",
                'level_progression': "(level {level})",
                'equipment_change': "({source_name})",
                'ability_improvement': "({source_name})",
                'class_feature': "({source_name})",
                'racial_trait': "({source_name})",
                'feat': "({source_name})",
                'magic_item': "({source_name})",
                'race': "({source_name})",
                'equipment': "({source_name})",
                'ability_score': "({source_name})",
                'unknown': "(unknown)",
                'default': "({source_name})"
            },
            DetailLevel.DISCORD_DETAILED: {
                'feat_selection': "from {source_name} feat",
                'level_progression': "from level {level} progression",
                'equipment_change': "from equipping {source_name}",
                'ability_improvement': "from {source_name}",
                'class_feature': "from {source_name} class feature",
                'racial_trait': "from {source_name} racial trait",
                'feat': "from {source_name} feat",
                'magic_item': "from {source_name} magic item",
                'race': "from {source_name} racial trait",
                'equipment': "from {source_name} equipment",
                'ability_score': "from {source_name} change",
                'unknown': "from unknown source",
                'default': "from {source_name}"
            },
            DetailLevel.CHANGE_LOG_COMPREHENSIVE: {
                'feat_selection': "This change was caused by selecting the {source_name} feat. {impact_summary}",
                'level_progression': "This change occurred due to level {level} progression in {class_name}. {impact_summary}",
                'equipment_change': "This change resulted from equipping {source_name}. {impact_summary}",
                'ability_improvement': "This change was caused by {source_name}. {impact_summary}",
                'class_feature': "This change was granted by the {source_name} class feature. {impact_summary}",
                'racial_trait': "This change comes from the {source_name} racial trait. {impact_summary}",
                'feat': "This change was caused by selecting the {source_name} feat. {impact_summary}",
                'magic_item': "This change resulted from the {source_name} magic item. {impact_summary}",
                'race': "This change comes from the {source_name} racial trait. {impact_summary}",
                'equipment': "This change resulted from {source_name} equipment. {impact_summary}",
                'ability_score': "This change was caused by {source_name} ability score modification. {impact_summary}",
                'unknown': "This change occurred from an unknown source. {impact_summary}",
                'default': "This change was caused by {source_name}. {impact_summary}"
            }
        }
        
        self.logger.info("Detail level manager initialized")
    
    def format_change_for_discord(self, change: FieldChange, attribution: Optional[ChangeAttribution] = None,
                                causation: Optional[ChangeCausation] = None, 
                                detail_level: DetailLevel = DetailLevel.DISCORD_DETAILED) -> str:
        """
        Format a change for Discord notification with appropriate detail level.
        
        Args:
            change: The field change to format
            attribution: Attribution information
            causation: Causation information
            detail_level: Level of detail to include
            
        Returns:
            Formatted description for Discord
        """
        try:
            # Start with base description
            base_desc = change.description or f"{change.field_path} changed"
            
            # Add attribution if available
            if attribution and attribution.source_name:
                attribution_text = self._format_attribution(attribution, causation, detail_level)
                if attribution_text:
                    if detail_level == DetailLevel.DISCORD_BRIEF:
                        base_desc = f"{base_desc} {attribution_text}"
                    else:
                        base_desc = f"{base_desc} {attribution_text}"
            
            # Ensure length limits
            max_length = self.max_lengths.get(detail_level, 150)
            if len(base_desc) > max_length:
                base_desc = base_desc[:max_length - 3] + "..."
            
            return base_desc
            
        except Exception as e:
            self.logger.error(f"Error formatting change for Discord: {e}", exc_info=True)
            return change.description or f"{change.field_path} changed"
    
    def format_change_for_log(self, change: FieldChange, attribution: Optional[ChangeAttribution] = None,
                            causation: Optional[ChangeCausation] = None) -> str:
        """
        Format a change for comprehensive change log with full details.
        
        Args:
            change: The field change to format
            attribution: Attribution information
            causation: Causation information
            
        Returns:
            Comprehensive description for change log
        """
        try:
            # Start with detailed base description
            base_desc = change.description or f"{change.field_path} changed"
            
            # Add comprehensive attribution and causation
            if attribution:
                attribution_text = self._format_attribution(
                    attribution, causation, DetailLevel.CHANGE_LOG_COMPREHENSIVE
                )
                if attribution_text:
                    base_desc = f"{base_desc}. {attribution_text}"
            
            # Add causation chain if available
            if causation and causation.related_changes:
                related_desc = self._format_causation_chain(causation)
                if related_desc:
                    base_desc = f"{base_desc} {related_desc}"
            
            # Add mechanical impact if available
            if attribution and attribution.impact_summary:
                base_desc = f"{base_desc} Impact: {attribution.impact_summary}"
            
            return base_desc
            
        except Exception as e:
            self.logger.error(f"Error formatting change for log: {e}", exc_info=True)
            return change.description or f"{change.field_path} changed"
    
    def should_include_in_discord(self, change: FieldChange, attribution: Optional[ChangeAttribution] = None,
                                config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine if a change should be included in Discord notifications.
        
        Args:
            change: The field change to evaluate
            attribution: Attribution information
            config: Configuration settings
            
        Returns:
            True if change should be included in Discord
        """
        try:
            # DEBUG: Start evaluation
            debug_info = {
                'field_path': change.field_path,
                'description': change.description,
                'priority': f"{change.priority.name} ({change.priority.value})",
                'attribution_source_type': attribution.source_type if attribution else None,
                'attribution_source': attribution.source if attribution else None,
                'attribution_source_name': attribution.source_name if attribution else None
            }
            self.logger.info(f"🔍 DISCORD FILTER DEBUG - Evaluating change: {debug_info}")
            
            # No hardcoded overrides - all filtering should respect user configuration
            
            # Check for real container moves that should be included
            if change.description and change.field_path:
                # Real container moves should be included (Bag of Holding, backpack, etc.)
                if 'moved' in change.description.lower():
                    # Include moves to/from actual containers (not internal categorization)
                    real_containers = ['bag of holding', 'backpack', 'pouch', 'container', 'pack', 'satchel', 'bag']
                    container_check = any(container in change.description.lower() for container in real_containers)
                    self.logger.info(f"🎒 CONTAINER MOVE CHECK - Has real container: {container_check}")
                    if container_check:
                        self.logger.info(f"✅ INCLUDED - Real container move")
                        return True
            
            # Always include high priority changes
            high_priority_check = change.priority.value >= ChangePriority.HIGH.value
            self.logger.info(f"⭐ HIGH PRIORITY CHECK - Priority {change.priority.value} >= {ChangePriority.HIGH.value}: {high_priority_check}")
            if high_priority_check:
                self.logger.info(f"✅ INCLUDED - High priority change")
                return True
            
            # Check configuration settings
            if config:
                self.logger.info(f"⚙️ CONFIG PRESENT - {config}")
                # Skip low priority if configured
                only_high_priority = config.get('discord_only_high_priority', False)
                if only_high_priority and change.priority.value < ChangePriority.HIGH.value:
                    self.logger.info(f"❌ EXCLUDED - Config requires high priority only")
                    return False
                
                # Include medium priority unless explicitly disabled
                medium_priority_check = change.priority.value >= ChangePriority.MEDIUM.value
                exclude_medium = config.get('discord_exclude_medium_priority', False)
                self.logger.info(f"🔶 MEDIUM PRIORITY CHECK - Priority {change.priority.value} >= {ChangePriority.MEDIUM.value}: {medium_priority_check}, Excluded: {exclude_medium}")
                if medium_priority_check and not exclude_medium:
                    self.logger.info(f"✅ INCLUDED - Medium priority allowed")
                    return True
                
                # Include low priority if explicitly enabled
                low_priority_check = change.priority.value >= ChangePriority.LOW.value
                include_low = config.get('discord_include_low_priority', False)
                self.logger.info(f"🔷 LOW PRIORITY CHECK - Priority {change.priority.value} >= {ChangePriority.LOW.value}: {low_priority_check}, Included: {include_low}")
                if low_priority_check and include_low:
                    self.logger.info(f"✅ INCLUDED - Low priority explicitly enabled")
                    return True
            else:
                self.logger.info(f"⚙️ NO CONFIG - Using default behavior")
                # Default behavior: include medium and high priority
                medium_or_high = change.priority.value >= ChangePriority.MEDIUM.value
                self.logger.info(f"🔶 DEFAULT MEDIUM+ CHECK - Priority {change.priority.value} >= {ChangePriority.MEDIUM.value}: {medium_or_high}")
                if medium_or_high:
                    self.logger.info(f"✅ INCLUDED - Default medium+ priority")
                    return True
            
            # Special cases based on attribution
            if attribution:
                self.logger.info(f"🏷️ ATTRIBUTION CHECKS - source_type: {attribution.source_type}, source: {attribution.source}")
                
                # Always include feat-related changes
                feat_check = attribution.source_type in ['feat', 'feat_selection']
                if feat_check:
                    self.logger.info(f"✅ INCLUDED - Feat attribution")
                    return True
                
                # Always include level progression changes
                level_check = attribution.source in ['level_progression'] or attribution.source_type == 'class_feature'
                if level_check:
                    self.logger.info(f"✅ INCLUDED - Level progression attribution")
                    return True
                
                # Include equipment changes that affect combat stats
                equipment_check = attribution.source_type in ['equipment', 'magic_item', 'equipment_change']
                combat_stat_check = any(keyword in change.field_path.lower() 
                                      for keyword in ['armor_class', 'attack', 'damage', 'hit_points', 'spell_attack', 'spell_save'])
                self.logger.info(f"⚔️ EQUIPMENT COMBAT CHECK - Is equipment: {equipment_check}, Affects combat: {combat_stat_check}")
                if equipment_check and combat_stat_check:
                    self.logger.info(f"✅ INCLUDED - Equipment affecting combat stats")
                    return True
                
                # Include racial trait changes
                race_check = attribution.source_type in ['race', 'racial_trait']
                if race_check:
                    self.logger.info(f"✅ INCLUDED - Racial trait attribution")
                    return True
                
                # No hardcoded ability score overrides - respect user configuration
            else:
                self.logger.info(f"🏷️ NO ATTRIBUTION")
            
            # Filter out equipped/unequipped changes from Discord (but keep in change log)
            if change.description and ('equipped ' in change.description.lower() or 'unequipped ' in change.description.lower()):
                # Only exclude simple equip/unequip - keep other equipment changes
                other_equipment_keywords = any(keyword in change.description.lower() 
                                             for keyword in ['added', 'removed', 'gained', 'lost', 'moved', 'reordered', 'quantity'])
                self.logger.info(f"👕 EQUIP/UNEQUIP CHECK - Has other keywords: {other_equipment_keywords}")
                if not other_equipment_keywords:
                    self.logger.info(f"❌ EXCLUDED - Simple equip/unequip change")
                    return False
            
            # Filter out internal equipment categorization moves (basic ↔ enhanced equipment)
            if change.description and 'moved' in change.description.lower():
                description = change.description.lower()
                # Check for internal scraper categorization moves
                internal_moves = [
                    'from basic equipment to enhanced equipment',
                    'from enhanced equipment to basic equipment',
                    'basic equipment' in description and 'enhanced equipment' in description
                ]
                internal_move_check = any(internal_moves)
                self.logger.info(f"🔄 INTERNAL MOVE CHECK - Is internal move: {internal_move_check}")
                if internal_move_check:
                    self.logger.info(f"❌ EXCLUDED - Internal equipment categorization move")
                    return False
            
            self.logger.info(f"❌ EXCLUDED - No inclusion criteria met")
            return False
            
        except Exception as e:
            self.logger.error(f"Error determining Discord inclusion: {e}", exc_info=True)
            return True  # Default to including on error
    
    def should_include_in_change_log(self, change: FieldChange, attribution: Optional[ChangeAttribution] = None,
                                   config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine if a change should be included in change logs.
        
        Args:
            change: The field change to evaluate
            attribution: Attribution information
            config: Configuration settings
            
        Returns:
            True if change should be included in change log
        """
        try:
            # Change logs are more comprehensive - include almost everything
            if config and not config.get('enable_change_logging', True):
                return False
            
            # Skip very low confidence changes if available
            if hasattr(change, 'confidence') and change.confidence < 0.3:
                return False
            
            # Skip metadata-only changes if configured
            if (config and config.get('change_log_skip_metadata', False) and 
                change.category.name == 'METADATA'):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error determining change log inclusion: {e}", exc_info=True)
            return True  # Default to including on error
    
    def get_priority_for_discord(self, change: FieldChange, attribution: Optional[ChangeAttribution] = None) -> ChangePriority:
        """
        Determine effective priority for Discord notifications, potentially boosting based on attribution.
        
        Args:
            change: The field change
            attribution: Attribution information
            
        Returns:
            Effective priority for Discord
        """
        try:
            base_priority = change.priority
            
            # Boost priority for certain attribution types
            if attribution:
                if attribution.source_type in ['feat', 'feat_selection']:
                    # Feat changes are always important
                    return max(base_priority, ChangePriority.HIGH, key=lambda p: p.value)
                
                if attribution.source in ['level_progression'] or attribution.source_type == 'class_feature':
                    # Level progression changes are important
                    return max(base_priority, ChangePriority.HIGH, key=lambda p: p.value)
                
                if attribution.source_type in ['equipment', 'magic_item', 'equipment_change']:
                    # Equipment affecting combat stats is medium priority
                    if any(keyword in change.field_path.lower() 
                           for keyword in ['armor_class', 'attack', 'damage', 'hit_points', 'spell_attack', 'spell_save']):
                        return max(base_priority, ChangePriority.MEDIUM, key=lambda p: p.value)
                    else:
                        # Other equipment changes get slight boost
                        return max(base_priority, ChangePriority.MEDIUM, key=lambda p: p.value)
                
                if attribution.source_type in ['race', 'racial_trait']:
                    # Racial trait changes are medium priority
                    return max(base_priority, ChangePriority.MEDIUM, key=lambda p: p.value)
                
                if attribution.source_type == 'ability_score':
                    # Ability score changes affecting multiple stats are medium priority
                    if any(keyword in change.field_path.lower() 
                           for keyword in ['modifier', 'saving_throw', 'skill', 'spell_attack', 'spell_save']):
                        return max(base_priority, ChangePriority.MEDIUM, key=lambda p: p.value)
                    else:
                        # Other ability score changes get slight boost
                        return max(base_priority, ChangePriority.MEDIUM, key=lambda p: p.value)
            
            return base_priority
            
        except Exception as e:
            self.logger.error(f"Error determining Discord priority: {e}", exc_info=True)
            return change.priority
    
    def create_discord_summary(self, changes: List[FieldChange], attributions: Dict[str, ChangeAttribution] = None) -> str:
        """
        Create a summary description for Discord when there are many changes.
        
        Args:
            changes: List of changes
            attributions: Dictionary mapping field paths to attributions
            
        Returns:
            Summary description
        """
        try:
            if not changes:
                return "No changes detected"
            
            # Group changes by attribution source
            source_groups = {}
            unattributed_count = 0
            
            for change in changes:
                attribution = attributions.get(change.field_path) if attributions else None
                if attribution and attribution.source_name:
                    source_key = f"{attribution.source_type}:{attribution.source_name}"
                    if source_key not in source_groups:
                        source_groups[source_key] = []
                    source_groups[source_key].append(change)
                else:
                    unattributed_count += 1
            
            # Create summary parts
            summary_parts = []
            
            # Add attributed changes
            for source_key, source_changes in source_groups.items():
                source_type, source_name = source_key.split(':', 1)
                if source_type in ['feat', 'feat_selection']:
                    summary_parts.append(f"{source_name} feat ({len(source_changes)} changes)")
                elif source_type in ['level_progression', 'class_feature']:
                    summary_parts.append(f"Level up ({len(source_changes)} changes)")
                elif source_type in ['equipment', 'equipment_change']:
                    summary_parts.append(f"{source_name} equipment ({len(source_changes)} changes)")
                elif source_type == 'magic_item':
                    summary_parts.append(f"{source_name} magic item ({len(source_changes)} changes)")
                elif source_type in ['race', 'racial_trait']:
                    summary_parts.append(f"{source_name} racial trait ({len(source_changes)} changes)")
                elif source_type == 'ability_score':
                    summary_parts.append(f"{source_name} ({len(source_changes)} changes)")
                else:
                    summary_parts.append(f"{source_name} ({len(source_changes)} changes)")
            
            # Add unattributed changes
            if unattributed_count > 0:
                summary_parts.append(f"Other changes ({unattributed_count})")
            
            # Combine into summary
            if len(summary_parts) == 1:
                return f"Changes from {summary_parts[0]}"
            elif len(summary_parts) <= 3:
                return f"Changes from {', '.join(summary_parts[:-1])} and {summary_parts[-1]}"
            else:
                return f"Changes from {summary_parts[0]}, {summary_parts[1]} and {len(summary_parts) - 2} other sources"
            
        except Exception as e:
            self.logger.error(f"Error creating Discord summary: {e}", exc_info=True)
            return f"{len(changes)} changes detected"
    
    def _format_attribution(self, attribution: ChangeAttribution, causation: Optional[ChangeCausation],
                          detail_level: DetailLevel) -> str:
        """Format attribution information for the given detail level."""
        try:
            templates = self.attribution_templates.get(detail_level, {})
            # Try source_type first (more specific), then source, then default
            template = (templates.get(attribution.source_type) or 
                       templates.get(attribution.source) or 
                       templates.get('default', ''))
            
            if not template:
                return ""
            
            # Prepare template variables
            template_vars = {
                'source_name': attribution.source_name,
                'source_type': attribution.source_type,
                'impact_summary': attribution.impact_summary
            }
            
            # Add causation-specific variables
            if causation and causation.trigger_details:
                template_vars.update(causation.trigger_details)
            
            # Format template
            try:
                return template.format(**template_vars)
            except KeyError as e:
                # Handle missing template variables gracefully
                self.logger.debug(f"Missing template variable {e}, using fallback")
                # Use source_type specific fallback
                if detail_level == DetailLevel.DISCORD_BRIEF:
                    return f"({attribution.source_name})"
                elif detail_level == DetailLevel.DISCORD_DETAILED:
                    return f"from {attribution.source_name}"
                else:
                    return f"This change was caused by {attribution.source_name}. {attribution.impact_summary}"
            
        except Exception as e:
            self.logger.error(f"Error formatting attribution: {e}", exc_info=True)
            return ""
    
    def _format_causation_chain(self, causation: ChangeCausation) -> str:
        """Format causation chain information."""
        try:
            if not causation.related_changes:
                return ""
            
            if len(causation.related_changes) == 1:
                return f"This also affected {causation.related_changes[0]}."
            elif len(causation.related_changes) <= 3:
                return f"This also affected {', '.join(causation.related_changes[:-1])} and {causation.related_changes[-1]}."
            else:
                return f"This also affected {causation.related_changes[0]}, {causation.related_changes[1]} and {len(causation.related_changes) - 2} other stats."
            
        except Exception as e:
            self.logger.error(f"Error formatting causation chain: {e}", exc_info=True)
            return ""
    
    def get_detail_level_for_context(self, context: str, change_count: int = 1) -> DetailLevel:
        """
        Determine appropriate detail level based on context and change count.
        
        Args:
            context: Context ('discord', 'change_log')
            change_count: Number of changes being formatted
            
        Returns:
            Appropriate detail level
        """
        try:
            if context == 'change_log':
                return DetailLevel.CHANGE_LOG_COMPREHENSIVE
            elif context == 'discord':
                if change_count <= 5:
                    return DetailLevel.DISCORD_DETAILED
                else:
                    return DetailLevel.DISCORD_BRIEF
            else:
                return DetailLevel.DISCORD_DETAILED
                
        except Exception as e:
            self.logger.error(f"Error determining detail level: {e}", exc_info=True)
            return DetailLevel.DISCORD_DETAILED
    
    def filter_changes_for_context(self, changes: List[FieldChange], 
                                 attributions: Dict[str, ChangeAttribution] = None,
                                 context: str = 'discord',
                                 config: Optional[Dict[str, Any]] = None) -> List[FieldChange]:
        """
        Filter changes based on context and configuration.
        
        Args:
            changes: List of changes to filter
            attributions: Dictionary mapping field paths to attributions
            context: Context ('discord', 'change_log')
            config: Configuration settings
            
        Returns:
            Filtered list of changes appropriate for the context
        """
        try:
            self.logger.info(f"🔄 FILTER START - Context: {context}, Input changes: {len(changes)}")
            
            # Group changes by priority for debug info
            priority_counts = {}
            for change in changes:
                priority_name = change.priority.name
                priority_counts[priority_name] = priority_counts.get(priority_name, 0) + 1
            
            self.logger.info(f"📊 INPUT PRIORITY BREAKDOWN - {priority_counts}")
            
            filtered_changes = []
            excluded_changes = []
            
            for i, change in enumerate(changes):
                attribution = attributions.get(change.field_path) if attributions else None
                
                self.logger.info(f"🔍 EVALUATING CHANGE {i+1}/{len(changes)}")
                
                if context == 'discord':
                    if self.should_include_in_discord(change, attribution, config):
                        filtered_changes.append(change)
                    else:
                        excluded_changes.append({
                            'field_path': change.field_path,
                            'description': change.description,
                            'priority': change.priority.name
                        })
                elif context == 'change_log':
                    if self.should_include_in_change_log(change, attribution, config):
                        filtered_changes.append(change)
                    else:
                        excluded_changes.append({
                            'field_path': change.field_path,
                            'description': change.description,
                            'priority': change.priority.name
                        })
                else:
                    # Default to including all changes
                    filtered_changes.append(change)
            
            # Log summary
            self.logger.info(f"✅ FILTER COMPLETE - {context}: {len(filtered_changes)}/{len(changes)} changes included")
            
            if excluded_changes:
                self.logger.info(f"❌ EXCLUDED CHANGES ({len(excluded_changes)}):")
                for i, excluded in enumerate(excluded_changes, 1):
                    self.logger.info(f"   {i}. {excluded['field_path']}: {excluded['description']} (Priority: {excluded['priority']})")
            
            # Group filtered changes by priority for debug info
            filtered_priority_counts = {}
            for change in filtered_changes:
                priority_name = change.priority.name
                filtered_priority_counts[priority_name] = filtered_priority_counts.get(priority_name, 0) + 1
            
            self.logger.info(f"📊 OUTPUT PRIORITY BREAKDOWN - {filtered_priority_counts}")
            
            return filtered_changes
            
        except Exception as e:
            self.logger.error(f"Error filtering changes for context: {e}", exc_info=True)
            return changes  # Return all changes on error
    
    def get_change_importance_score(self, change: FieldChange, 
                                  attribution: Optional[ChangeAttribution] = None) -> int:
        """
        Calculate an importance score for a change to help with prioritization.
        
        Args:
            change: The field change to score
            attribution: Attribution information
            
        Returns:
            Importance score (higher = more important)
        """
        try:
            score = 0
            
            # Base score from priority
            if change.priority == ChangePriority.HIGH:
                score += 100
            elif change.priority == ChangePriority.MEDIUM:
                score += 50
            elif change.priority == ChangePriority.LOW:
                score += 25
            elif change.priority == ChangePriority.CRITICAL:
                score += 150
            
            # Boost score based on attribution
            if attribution:
                if attribution.source_type in ['feat', 'feat_selection']:
                    score += 75  # Feats are very important
                elif attribution.source_type == 'class_feature':
                    score += 60  # Class features are important
                elif attribution.source_type in ['magic_item', 'equipment']:
                    score += 40  # Equipment changes are moderately important
                elif attribution.source_type in ['race', 'racial_trait']:
                    score += 30  # Racial traits are moderately important
                elif attribution.source_type == 'ability_score':
                    score += 20  # Ability score changes are somewhat important
            
            # Boost score for combat-related changes
            if any(keyword in change.field_path.lower() 
                   for keyword in ['armor_class', 'attack', 'damage', 'hit_points', 'spell_attack', 'spell_save']):
                score += 25
            
            # Boost score for character progression changes
            if any(keyword in change.field_path.lower() 
                   for keyword in ['level', 'class', 'feat', 'spell', 'proficiency']):
                score += 15
            
            # Additional boost for feat-related field paths
            if 'feat' in change.field_path.lower():
                score += 25
            
            return score
            
        except Exception as e:
            self.logger.error(f"Error calculating change importance: {e}", exc_info=True)
            return 0


def create_detail_level_manager() -> DetailLevelManager:
    """Factory function to create a detail level manager."""
    return DetailLevelManager()