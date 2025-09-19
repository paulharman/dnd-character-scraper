#!/usr/bin/env python3
"""
Enhanced Spell Processor

This module provides enhanced spell processing logic to fix the spell detection
and deduplication issues identified in the investigation.

Key fixes:
1. Proper feat spell detection (Magic Initiate, etc.)
2. Per-source deduplication while preserving cross-source duplicates
3. Comprehensive logging for debugging
"""

import logging
import json
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class EnhancedSpellInfo:
    """Enhanced spell information with detailed metadata."""
    id: int
    name: str
    level: int
    school: str
    source: str
    description: str
    is_legacy: bool
    
    # Availability flags
    counts_as_known: bool
    is_always_prepared: bool
    is_prepared: bool
    uses_spell_slot: bool
    limited_use: Optional[Dict[str, Any]]
    
    # Source metadata
    component_id: Optional[int]
    component_type_id: Optional[int]
    
    # Calculated flags
    is_available: bool  # Whether this spell should be included in output
    availability_reason: str  # Why this spell is available
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'level': self.level,
            'school': self.school,
            'source': self.source,
            'description': self.description,
            'isLegacy': self.is_legacy,
            'is_prepared': self.is_prepared or self.is_always_prepared,
            'always_prepared': self.is_always_prepared,
            'ritual': False,  # Will be enhanced later if needed
            'concentration': False,  # Will be enhanced later if needed
            # Enhanced metadata
            'counts_as_known': self.counts_as_known,
            'uses_spell_slot': self.uses_spell_slot,
            'limited_use': self.limited_use,
            'component_id': self.component_id,
            'component_type_id': self.component_type_id,
            'is_available': self.is_available,
            'availability_reason': self.availability_reason
        }


class EnhancedSpellProcessor:
    """
    Enhanced spell processor that fixes detection and deduplication issues.
    
    This processor addresses the following issues:
    1. Missing feat spells (like Minor Illusion from Magic Initiate)
    2. Within-source spell duplication (like duplicate Detect Magic in Racial)
    3. Incorrect cross-source deduplication (preserving legitimate duplicates)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        # Enable debug logging for spell processing
        self.logger.setLevel(logging.DEBUG)
    
    def process_character_spells(self, raw_data: Dict[str, Any]) -> Dict[str, List[EnhancedSpellInfo]]:
        """
        Process all spells for a character with enhanced detection and deduplication.
        
        Args:
            raw_data: Raw D&D Beyond character data
            
        Returns:
            Dictionary mapping spell sources to lists of EnhancedSpellInfo objects
        """
        self.logger.info("Starting enhanced spell processing")
        
        # Step 1: Extract all spells from raw data with enhanced detection
        raw_spells_by_source = self._extract_all_spells(raw_data)
        
        # Step 2: Apply per-source deduplication
        deduplicated_spells = self._deduplicate_spells_by_source(raw_spells_by_source)
        
        # Step 3: Log processing results
        self._log_processing_results(raw_spells_by_source, deduplicated_spells)
        
        return deduplicated_spells
    
    def _extract_all_spells(self, raw_data: Dict[str, Any]) -> Dict[str, List[EnhancedSpellInfo]]:
        """Extract all spells from raw D&D Beyond data with enhanced detection."""
        self.logger.info("Extracting all spells from raw D&D Beyond data")
        
        spells_by_source = {}
        
        # Process spells by source type
        spells_data = raw_data.get('spells', {})
        if isinstance(spells_data, dict):
            for source_type, spell_list in spells_data.items():
                if isinstance(spell_list, list):
                    # For feat spells, try to get more specific source names
                    if source_type == 'feat':
                        feat_spells_by_source = self._process_feat_spells(spell_list, raw_data)
                        for feat_source, feat_spell_list in feat_spells_by_source.items():
                            if feat_spell_list:
                                spells_by_source[feat_source] = feat_spell_list
                    else:
                        source_name = self._get_friendly_source_name(source_type)
                        processed_spells = self._process_spell_list(spell_list, source_name, source_type)
                        if processed_spells:
                            spells_by_source[source_name] = processed_spells
        
        # Process class spells
        class_spells_data = raw_data.get('classSpells', [])
        if isinstance(class_spells_data, list):
            for class_spell_entry in class_spells_data:
                if isinstance(class_spell_entry, dict):
                    character_class_id = class_spell_entry.get('characterClassId')
                    spells = class_spell_entry.get('spells', [])
                    
                    if spells:
                        class_name = self._get_class_name_by_id(raw_data, character_class_id)
                        processed_spells = self._process_spell_list(spells, class_name, 'class')
                        if processed_spells:
                            spells_by_source[class_name] = processed_spells
        
        return spells_by_source
    
    def _process_spell_list(self, spell_list: List[Dict[str, Any]], source_name: str, source_type: str) -> List[EnhancedSpellInfo]:
        """Process a list of spells from a specific source."""
        processed_spells = []
        
        for spell_data in spell_list:
            if not isinstance(spell_data, dict):
                continue
            
            spell_info = self._create_enhanced_spell_info(spell_data, source_name, source_type)
            if spell_info:
                processed_spells.append(spell_info)
        
        self.logger.debug(f"Processed {len(processed_spells)} spells from source '{source_name}'")
        return processed_spells
    
    def _create_enhanced_spell_info(self, spell_data: Dict[str, Any], source_name: str, source_type: str) -> Optional[EnhancedSpellInfo]:
        """Create EnhancedSpellInfo from raw spell data with enhanced availability detection."""
        spell_def = spell_data.get('definition', {})
        print(f"ENHANCED_PROCESSOR: Processing {spell_def.get('name', 'Unknown')} from {source_type}")
        spell_def = spell_data.get('definition', {})
        if not spell_def:
            return None
        
        # Basic spell information
        spell_id = spell_def.get('id', 0)
        name = spell_def.get('name', 'Unknown Spell')
        level = spell_def.get('level', 0)
        
        # Handle school field (can be string or dict)
        school_data = spell_def.get('school', 'Unknown')
        if isinstance(school_data, dict):
            school = school_data.get('name', 'Unknown')
        else:
            school = str(school_data)
        
        description = spell_def.get('description', '')
        
        # Determine if spell is legacy based on spell definition ID
        # Since sourceId is null in spell definitions, use known legacy spell IDs
        spell_def_id = spell_def.get('id')
        source_id = spell_def.get('sourceId')
        
        # Known legacy spell definition IDs (pre-2024 spells)
        # These are spell IDs that are known to be from legacy sources
        KNOWN_LEGACY_SPELL_IDS = {
            2384,  # Ice Knife (legacy, sourceId 4)
            # Add other known legacy spell IDs as needed
        }
        
        # Try sourceId first, then fallback to known spell IDs
        SOURCE_2024_IDS = {142, 143, 144, 145, 146, 147, 148, 149, 150}
        if source_id is not None:
            is_legacy = source_id not in SOURCE_2024_IDS
        elif spell_def_id in KNOWN_LEGACY_SPELL_IDS:
            is_legacy = True
        else:
            # For spells with high definition IDs (2619xxx range), they are likely 2024
            # For spells with low definition IDs (under 1000000), they are likely legacy
            is_legacy = spell_def_id is not None and spell_def_id < 1000000
        
        # Debug logging for legacy spell detection
        if is_legacy:
            self.logger.debug(f"Detected legacy spell: {name} (id={spell_def_id}, sourceId={source_id})")
        
        # Availability flags from raw data
        counts_as_known = spell_data.get('countsAsKnownSpell', False)
        is_always_prepared = spell_data.get('alwaysPrepared', False)
        is_prepared = spell_data.get('prepared', False)
        uses_spell_slot = spell_data.get('usesSpellSlot', True)
        limited_use = spell_data.get('limitedUse')
        
        # Source metadata
        component_id = spell_data.get('componentId')
        
        # Fix D&D Beyond API bug: Detect feat-granted always-prepared spells
        if source_type == 'feat' and not is_always_prepared:
            detected_always_prepared = self._detect_feat_always_prepared_spell(
                spell_data, component_id, level, limited_use
            )
            if detected_always_prepared:
                is_always_prepared = True
                print(f"MAGIC_INITIATE_FIX: Fixed always_prepared for {name} (Level {level})")
                logger.info(f"Fixed always_prepared flag for feat spell: {name} (Level {level}) from component_id {component_id}")
        
        component_type_id = spell_data.get('componentTypeId')
        
        # Enhanced availability detection
        is_available, availability_reason = self._determine_spell_availability(
            spell_data, source_type, counts_as_known, is_always_prepared, 
            is_prepared, uses_spell_slot, limited_use
        )
        
        if is_available:
            self.logger.debug(f"Including spell '{name}' from '{source_name}': {availability_reason}")
        else:
            self.logger.debug(f"Excluding spell '{name}' from '{source_name}': {availability_reason}")
            return None  # Don't include unavailable spells
        
        return EnhancedSpellInfo(
            id=spell_id,
            name=name,
            level=level,
            school=school,
            source=source_name,
            description=description,
            is_legacy=is_legacy,
            counts_as_known=counts_as_known,
            is_always_prepared=is_always_prepared,
            is_prepared=is_prepared,
            uses_spell_slot=uses_spell_slot,
            limited_use=limited_use,
            component_id=component_id,
            component_type_id=component_type_id,
            is_available=is_available,
            availability_reason=availability_reason
        )
    
    def _determine_spell_availability(self, spell_data: Dict[str, Any], source_type: str, 
                                    counts_as_known: bool, is_always_prepared: bool, 
                                    is_prepared: bool, uses_spell_slot: bool, 
                                    limited_use: Optional[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Determine if a spell should be available with enhanced logic.
        
        This uses a more comprehensive approach that considers all the ways a spell
        can be available, rather than hardcoding specific source types.
        """
        
        # Primary availability indicators (strongest signals)
        if counts_as_known:
            return True, f"{source_type} spell - counts as known"
        
        if is_always_prepared:
            return True, f"{source_type} spell - always prepared"
        
        if is_prepared:
            return True, f"{source_type} spell - prepared"
        
        # Secondary availability indicators
        # Spells that don't use spell slots are typically available (cantrips, racial abilities, etc.)
        if not uses_spell_slot:
            return True, f"{source_type} spell - doesn't use spell slots"
        
        # Spells with limited use are typically available (racial spells, feat spells, etc.)
        if limited_use is not None:
            # Check if the spell has actual uses available
            max_uses = limited_use.get('maxUses', 0) if isinstance(limited_use, dict) else 0
            if max_uses > 0:
                return True, f"{source_type} spell - has limited use ({max_uses} uses)"
            else:
                return True, f"{source_type} spell - has limited use structure"
        
        # For class spells, if none of the above apply, they're typically not available
        # (this handles spells in spellbook that aren't prepared)
        if source_type == 'class':
            return False, f"{source_type} spell - not known, prepared, or always prepared"
        
        # For non-class sources, we're more permissive since they often represent
        # special abilities that should be available
        # This includes feat spells, racial spells, item spells, etc.
        if source_type in ['feat', 'race', 'background', 'item', 'subclass']:
            return True, f"{source_type} spell - available from non-class source"
        
        # For unknown source types, use conservative approach
        self.logger.warning(f"Unknown source type '{source_type}' for spell, using conservative logic")
        return False, f"Unknown source '{source_type}' - conservative exclusion"
    
    def _deduplicate_spells_by_source(self, spells_by_source: Dict[str, List[EnhancedSpellInfo]]) -> Dict[str, List[EnhancedSpellInfo]]:
        """
        Deduplicate spells within each source while preserving cross-source duplicates.
        
        This fixes the issue where Detect Magic appears twice in the Racial source.
        """
        self.logger.info("Applying per-source deduplication")
        
        deduplicated = {}
        
        for source, spell_list in spells_by_source.items():
            deduplicated_list = self._deduplicate_within_source(spell_list, source)
            if deduplicated_list:
                deduplicated[source] = deduplicated_list
        
        return deduplicated
    
    def _deduplicate_within_source(self, spell_list: List[EnhancedSpellInfo], source: str) -> List[EnhancedSpellInfo]:
        """Remove duplicate spells within a single source, keeping the first occurrence."""
        seen_spells: Set[Tuple[str, int]] = set()
        deduplicated_spells = []
        removed_count = 0
        
        for spell in spell_list:
            # Create a unique identifier for the spell (name + level)
            spell_key = (spell.name, spell.level)
            
            if spell_key not in seen_spells:
                seen_spells.add(spell_key)
                deduplicated_spells.append(spell)
            else:
                removed_count += 1
                self.logger.info(f"Removed duplicate spell '{spell.name}' (level {spell.level}) from source '{source}'")
        
        if removed_count > 0:
            self.logger.info(f"Removed {removed_count} duplicate spells from source '{source}'")
        
        return deduplicated_spells
    
    def _get_friendly_source_name(self, source_type: str) -> str:
        """Map API source type to friendly source name."""
        source_mapping = {
            'race': 'Racial',
            'feat': 'Feat',
            'item': 'Item',
            'background': 'Background',
            'class': 'Class',
            'subclass': 'Subclass'
        }
        return source_mapping.get(source_type, source_type.title())
    
    def _process_feat_spells(self, feat_spell_list: List[Dict[str, Any]], raw_data: Dict[str, Any]) -> Dict[str, List[EnhancedSpellInfo]]:
        """
        Process feat spells and group them by specific feat names when possible.
        
        This attempts to identify which specific feat granted each spell,
        rather than lumping all feat spells together.
        """
        feat_spells_by_source = {}
        
        # Try to group spells by their component IDs to identify specific feats
        spells_by_component = {}
        
        for spell_data in feat_spell_list:
            if not isinstance(spell_data, dict):
                continue
            
            component_id = spell_data.get('componentId')
            if component_id:
                if component_id not in spells_by_component:
                    spells_by_component[component_id] = []
                spells_by_component[component_id].append(spell_data)
            else:
                # Fallback for spells without component IDs
                if 'unknown_feat' not in spells_by_component:
                    spells_by_component['unknown_feat'] = []
                spells_by_component['unknown_feat'].append(spell_data)
        
        # Process each component group
        for component_id, spells in spells_by_component.items():
            if component_id == 'unknown_feat':
                source_name = 'Feat'
            else:
                # Try to identify the specific feat name
                feat_name = self._identify_feat_by_component_id(component_id, raw_data)
                if feat_name:
                    source_name = feat_name
                else:
                    source_name = 'Feat'
            
            processed_spells = self._process_spell_list(spells, source_name, 'feat')
            if processed_spells:
                feat_spells_by_source[source_name] = processed_spells
        
        return feat_spells_by_source
    
    def _identify_feat_by_component_id(self, component_id: int, raw_data: Dict[str, Any]) -> Optional[str]:
        """
        Try to identify a feat name by its component ID.
        
        This looks through various data structures to find the feat that
        corresponds to the given component ID.
        """
        # Check in choices data
        choices = raw_data.get('choices', [])
        for choice in choices:
            if isinstance(choice, dict):
                if choice.get('componentId') == component_id:
                    # Try to get the feat name from the choice
                    choice_type = choice.get('type')
                    if choice_type == 2:  # Feat choice type
                        option_value = choice.get('optionValue')
                        if option_value:
                            feat_name = self._get_feat_name_by_id(option_value, raw_data)
                            if feat_name:
                                return feat_name
        
        # Check in modifiers data
        modifiers = raw_data.get('modifiers', [])
        for modifier in modifiers:
            if isinstance(modifier, dict):
                if modifier.get('componentId') == component_id:
                    friendly_type_name = modifier.get('friendlyTypeName', '')
                    friendly_subtype_name = modifier.get('friendlySubtypeName', '')
                    
                    # Look for feat-related modifiers
                    if 'feat' in friendly_type_name.lower():
                        # Try to extract feat name from the friendly names
                        if friendly_subtype_name and friendly_subtype_name != friendly_type_name:
                            return friendly_subtype_name
                        elif friendly_type_name:
                            return friendly_type_name
        
        # Check in features data if available
        features = raw_data.get('features', [])
        for feature in features:
            if isinstance(feature, dict):
                if feature.get('componentId') == component_id:
                    feature_def = feature.get('definition', {})
                    feature_name = feature_def.get('name')
                    if feature_name:
                        return feature_name
        
        # Check in feats data if available
        feats = raw_data.get('feats', [])
        for feat in feats:
            if isinstance(feat, dict):
                if feat.get('componentId') == component_id:
                    feat_def = feat.get('definition', {})
                    feat_name = feat_def.get('name')
                    if feat_name:
                        return feat_name
        
        return None
    
    def _get_feat_name_by_id(self, feat_id: int, raw_data: Dict[str, Any]) -> Optional[str]:
        """Get feat name by feat ID."""
        feats = raw_data.get('feats', [])
        for feat in feats:
            if isinstance(feat, dict):
                feat_def = feat.get('definition', {})
                if feat_def.get('id') == feat_id:
                    return feat_def.get('name')
        return None
    
    def _get_class_name_by_id(self, raw_data: Dict[str, Any], character_class_id: int) -> str:
        """Get class name by character class ID."""
        classes = raw_data.get('classes', [])
        for class_data in classes:
            if class_data.get('id') == character_class_id:
                class_definition = class_data.get('definition', {})
                return class_definition.get('name', 'Unknown Class')
        return 'Unknown Class'
    
    def _log_processing_results(self, raw_spells: Dict[str, List[EnhancedSpellInfo]], 
                               deduplicated_spells: Dict[str, List[EnhancedSpellInfo]]) -> None:
        """Log the results of spell processing for debugging."""
        self.logger.info("=== SPELL PROCESSING RESULTS ===")
        
        total_raw = sum(len(spell_list) for spell_list in raw_spells.values())
        total_final = sum(len(spell_list) for spell_list in deduplicated_spells.values())
        
        self.logger.info(f"Total spells before processing: {total_raw}")
        self.logger.info(f"Total spells after processing: {total_final}")
        self.logger.info(f"Spells removed: {total_raw - total_final}")
        
        # Log by source
        for source in set(list(raw_spells.keys()) + list(deduplicated_spells.keys())):
            raw_count = len(raw_spells.get(source, []))
            final_count = len(deduplicated_spells.get(source, []))
            
            if raw_count != final_count:
                self.logger.info(f"Source '{source}': {raw_count} -> {final_count} spells")
            else:
                self.logger.info(f"Source '{source}': {final_count} spells (no change)")
        
        # Log specific target spells
        self._log_target_spells(deduplicated_spells)
    
    def _log_target_spells(self, spells_by_source: Dict[str, List[EnhancedSpellInfo]]) -> None:
        """Log information about target spells (Minor Illusion, Detect Magic) for debugging."""
        target_spells = ['Minor Illusion', 'Detect Magic']
        
        for target_spell in target_spells:
            found_instances = []
            
            for source, spell_list in spells_by_source.items():
                for spell in spell_list:
                    if target_spell in spell.name:
                        found_instances.append(f"{source}")
            
            if found_instances:
                self.logger.info(f"Target spell '{target_spell}' found in sources: {', '.join(found_instances)}")
            else:
                self.logger.warning(f"Target spell '{target_spell}' NOT FOUND in any source")
    
    
    def _detect_feat_always_prepared_spell(self, spell_data: Dict[str, Any], component_id: Optional[int], 
                                         spell_level: int, limited_use: Optional[Dict[str, Any]]) -> bool:
        """
        Detect spells that should be always prepared from feats.
        
        D&D Beyond's API incorrectly sets alwaysPrepared=false for feat-granted spells
        that should be always prepared according to the feat descriptions.
        """
        if not component_id:
            return False
            
        # Known feat component IDs that grant always-prepared spells
        FEAT_ALWAYS_PREPARED_IDS = {
            1789165: "Magic Initiate",      # Magic Initiate feat
            3026435: "Fey Touched",         # Fey Touched feat  
            3026436: "Shadow Touched",      # Shadow Touched feat
            2666608: "Aberrant Dragonmark" # Aberrant Dragonmark feat
        }
        
        if component_id not in FEAT_ALWAYS_PREPARED_IDS:
            return False
            
        feat_name = FEAT_ALWAYS_PREPARED_IDS[component_id]
        
        # Add debug output to see what we're checking
        print(f"DEBUG: Checking {feat_name} spell - level:{spell_level}, limitedUse:{limited_use}")
        
        # Magic Initiate: Level 1 spell with once-per-long-rest usage
        if feat_name == "Magic Initiate":
            if spell_level == 1:
                # Check if it has the right limited use pattern
                if limited_use and isinstance(limited_use, dict):
                    max_uses = limited_use.get('maxUses', 0)
                    reset_type = limited_use.get('resetType', 0)  # 2 = long rest
                    result = max_uses == 1 and reset_type == 2
                    print(f"DEBUG: Magic Initiate L1 spell - maxUses:{max_uses}, resetType:{reset_type}, result:{result}")
                    return result
                
        # Fey Touched: Both level 1 spells (Misty Step + chosen spell)
        elif feat_name == "Fey Touched":
            if spell_level == 1 and limited_use:
                max_uses = limited_use.get('maxUses', 0) 
                reset_type = limited_use.get('resetType', 0)
                return max_uses == 1 and reset_type == 2
                
        # Shadow Touched: Both level 1 spells (Invisibility + chosen spell)
        elif feat_name == "Shadow Touched":
            if spell_level == 1 and limited_use:
                max_uses = limited_use.get('maxUses', 0)
                reset_type = limited_use.get('resetType', 0) 
                return max_uses == 1 and reset_type == 2
                
        # Aberrant Dragonmark: Level 1 spell (cantrip is handled separately)
        elif feat_name == "Aberrant Dragonmark":
            if spell_level == 1 and limited_use:
                max_uses = limited_use.get('maxUses', 0)
                reset_type = limited_use.get('resetType', 0)
                return max_uses == 1 and reset_type == 2
        
        return False