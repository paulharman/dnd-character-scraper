"""
Spellcasting formatter for comprehensive spell information.

This module handles the generation of spellcasting sections including
spell statistics, spell slots, spell lists, and detailed spell descriptions.
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import re

# Import interfaces and utilities using absolute import
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging

from formatters.base import BaseFormatter
from utils.text import TextProcessor
from utils.spell_data_extractor import SpellDataExtractor

# Import EnhancedSpellInfo for type checking
try:
    from scraper.core.calculators.services.spell_processor import EnhancedSpellInfo
except ImportError:
    # Fallback if import fails
    EnhancedSpellInfo = None


class SpellcastingFormatter(BaseFormatter):
    """
    Handles spellcasting section generation for character sheets.
    
    Generates comprehensive spellcasting information including spell stats,
    spell slots, spell lists, and detailed spell descriptions.
    """
    
    def __init__(self, text_processor: TextProcessor, config_manager=None):
        """
        Initialize the spellcasting formatter.
        
        Args:
            text_processor: Text processing utilities
            config_manager: Configuration manager for template settings
        """
        super().__init__(text_processor)
        self.config_manager = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        self.spell_extractor = None  # Will be initialized when needed
        self.combat_data = {}  # Initialize combat data storage

    def _convert_spell_to_dict(self, spell) -> Dict[str, Any]:
        """
        Convert EnhancedSpellInfo object to dictionary format for compatibility.
        
        Args:
            spell: Either EnhancedSpellInfo object or dictionary
            
        Returns:
            Dictionary representation of the spell
        """
        # If it's already a dictionary, return as-is
        if isinstance(spell, dict):
            return spell
            
        # If it's an EnhancedSpellInfo object, convert it
        if EnhancedSpellInfo and isinstance(spell, EnhancedSpellInfo):
            return {
                'name': spell.name,
                'level': spell.level,
                'school': spell.school,
                'source': spell.source,
                'description': spell.description,
                'isLegacy': spell.is_legacy,
                'is_prepared': spell.is_prepared or spell.is_always_prepared,
                'always_prepared': spell.is_always_prepared,
                'ritual': False,  # Will be filled by spell extractor if needed
                'concentration': False,  # Will be filled by spell extractor if needed
                # Additional metadata for enhanced features
                'counts_as_known': spell.counts_as_known,
                'uses_spell_slot': spell.uses_spell_slot,
                'limited_use': spell.limited_use,
                'component_id': spell.component_id,
                'component_type_id': spell.component_type_id,
                'is_available': spell.is_available,
                'availability_reason': spell.availability_reason
            }
        
        # Fallback for unknown types
        self.logger.warning(f"Unknown spell type: {type(spell)}")
        return {}
    
    def _get_required_fields(self) -> List[str]:
        """Get list of required fields for spellcasting formatting."""
        return []
    
    def _validate_internal(self, character_data: Dict[str, Any]) -> bool:
        """Validate character data structure for spellcasting formatting."""
        spells = self.get_spells(character_data)
        
        # Check if character has spells
        if not spells:
            self.logger.info("Parser:   No spells found for character")
            return False
        
        # Validate spell structure
        for source, spell_list in spells.items():
            if not isinstance(spell_list, list):
                self.logger.error(f"Spell list for {source} is not a list")
                return False
            
            for spell in spell_list:
                # Convert spell to dict format for validation
                spell_dict = self._convert_spell_to_dict(spell)
                if not spell_dict:
                    self.logger.error(f"Could not convert spell in {source} to dictionary format")
                    return False
                
                if 'name' not in spell_dict:
                    self.logger.error(f"Spell in {source} missing name field")
                    return False
        
        return True
    
    
    def _generate_header(self) -> str:
        """Generate spellcasting section header."""
        return """## Spellcasting

<span class="right-link">[[#Character Statistics|Top]]</span>"""
    
    def _generate_spell_statistics(self, character_data: Dict[str, Any]) -> str:
        """Generate spell statistics block."""
        # Get spellcasting stats from v6.0.0 structure first, then fallback
        spellcasting_data = character_data.get('spellcasting', {})
        character_info = self.get_character_info(character_data)
        
        # Try spellcasting section first (v6.0.0), then character_info, then top-level
        spell_save_dc = (
            spellcasting_data.get('spell_save_dc') or
            character_info.get('spell_save_dc') or
            character_data.get('spell_save_dc', 8)
        )
        
        spell_attack_bonus = (
            spellcasting_data.get('spell_attack_bonus') or
            character_info.get('spell_attack_bonus') or
            character_data.get('spell_attack_bonus', 0)
        )
        
        spellcasting_ability = (
            spellcasting_data.get('spellcasting_ability') or
            character_info.get('spellcasting_ability') or
            character_data.get('spellcasting_ability', 'intelligence')
        )
        
        # Get ability modifier for spellcasting
        ability_scores = self.get_ability_scores(character_data)
        ability_data = ability_scores.get(spellcasting_ability, {})
        ability_mod = ability_data.get('modifier', 0)
        
        # Calculate spell attack bonus if not provided (proficiency + ability mod)
        if spell_attack_bonus == 0:
            proficiency_bonus = character_info.get('proficiency_bonus', 2)
            spell_attack_bonus = proficiency_bonus + ability_mod
        
        # Calculate spell save DC if not provided (8 + proficiency + ability mod)
        if spell_save_dc == 8:
            proficiency_bonus = character_info.get('proficiency_bonus', 2)
            spell_save_dc = 8 + proficiency_bonus + ability_mod
        
        # Format modifier and attack bonus
        modifier_str = f"+{ability_mod}" if ability_mod >= 0 else str(ability_mod)
        attack_bonus_str = f"+{spell_attack_bonus}" if spell_attack_bonus >= 0 else str(spell_attack_bonus)
        
        # Build stats block
        stats_block = f"""> ```stats
> items:
>   - label: Spell Save DC
>     value: {spell_save_dc}
>   - label: Spell Attack Bonus
>     value: '{attack_bonus_str}'
>   - label: Spellcasting Ability
>     value: '{spellcasting_ability.capitalize() if spellcasting_ability else 'None'}'
>   - label: Spellcasting Modifier
>     value: '{modifier_str}'
>
> grid:
>   columns: 4
> ```
>
> ^spellstats"""
        
        return stats_block
    
    def _generate_spell_slots(self, character_data: Dict[str, Any]) -> str:
        """Generate spell slots section."""
        character_info = self.get_character_info(character_data)
        character_name = character_info.get('name', 'Unknown')
        classes = character_info.get('classes', [])
        
        # Create character key for state tracking
        char_key = character_name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace(',', '')
        
        section = "\n### Spell Slots\n> ```consumable\n> items:\n"
        
        # Check for sorcery points (sorcerer-specific)
        if any('Sorcerer' in cls.get('name', '') for cls in classes):
            character_level = character_info.get('level', 1)
            sorcery_points = max(1, character_level)  # Sorcerers get sorcery points equal to level
            section += f">   - label: 'Sorcery Points'\n"
            section += f">     state_key: {char_key}_sorcery_points\n"
            section += f">     uses: {sorcery_points}\n"
        
        # Regular spell slots - try v6.0.0 structure first, then fallback
        spellcasting_data = character_data.get('spellcasting', {})
        spell_slots = spellcasting_data.get('spell_slots', character_data.get('spell_slots', {}))
        regular_slots = self._normalize_spell_slots(spell_slots)
        
        for level in range(1, 10):
            slot_key = f'level_{level}'
            slots = regular_slots.get(slot_key, 0)
            if slots > 0:
                section += f">   - label: 'Level {level}'\n"
                section += f">     state_key: {char_key}_spells_{level}\n"
                section += f">     uses: {slots}\n"
        
        # Pact slots for warlocks - try v6.0.0 structure first
        pact_slots = spellcasting_data.get('pact_slots', character_data.get('pact_slots', 0))
        if pact_slots > 0:
            pact_level = spellcasting_data.get('pact_slot_level', character_data.get('pact_slot_level', 1))
            section += f">   - label: 'Pact Slots (Level {pact_level})'\n"
            section += f">     state_key: {char_key}_pact_slots\n"
            section += f">     uses: {pact_slots}\n"
        
        section += "> ```\n>\n> ^spellslots"
        
        return section
    
    def _normalize_spell_slots(self, spell_slots: Any) -> Dict[str, int]:
        """
        Normalize spell slots data to expected dictionary format.
        
        Handles both v6.0.0 list format [level1_slots, level2_slots, ...]
        and legacy dictionary format {"regular_slots": {"level_1": count, ...}}
        
        Args:
            spell_slots: Spell slots data in various formats
            
        Returns:
            Dictionary with level_N keys mapping to slot counts
        """
        # Handle list format (v6.0.0): [3, 1, 0, 0, 0, 0, 0, 0, 0]
        if isinstance(spell_slots, list):
            normalized = {}
            for i, slot_count in enumerate(spell_slots):
                if slot_count > 0:  # Only include levels with slots
                    level = i + 1  # List is 0-indexed, spell levels start at 1
                    if level <= 9:  # Only spell levels 1-9
                        normalized[f'level_{level}'] = slot_count
            return normalized
        
        # Handle dictionary format (legacy): {"regular_slots": {"level_1": 3, ...}}
        elif isinstance(spell_slots, dict):
            # Check if it's the nested legacy format
            if 'regular_slots' in spell_slots:
                regular_slots = spell_slots.get('regular_slots', {})
                if isinstance(regular_slots, dict):
                    return regular_slots
                else:
                    return {}
            else:
                # Assume it's already in the correct format
                return spell_slots
        
        # Fallback for unexpected format
        else:
            self.logger.warning(f"Unexpected spell_slots format: {type(spell_slots)}")
            return {}
    
    def _generate_free_cast_spells(self, character_data: Dict[str, Any]) -> str:
        """Generate Free Cast Spells section for spells that can be cast without spell slots."""
        character_info = self.get_character_info(character_data)
        character_name = character_info.get('name', 'Unknown')
        
        # Check both processed spells and raw data for free cast spells
        spells = self.get_spells(character_data)
        raw_spells = character_data.get('spells', {})
        
        char_key = character_name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace(',', '')
        free_cast_spells = []
        
        # First check processed spells
        for source, spell_list in spells.items():
            for spell in spell_list:
                spell_dict = self._convert_spell_to_dict(spell)
                spell_name = spell_dict.get('name', '')
                spell_level = spell_dict.get('level', 0)
                source_info = spell_dict.get('source_info', {})
                
                # Skip cantrips (they're always free, but handled separately)
                if spell_level == 0:
                    continue
                
                # Check for racial spells (usually once per long rest)
                if source.lower() == 'racial':
                    racial_source = self._determine_racial_spell_source(character_data, spell_name)
                    free_cast_spells.append({
                        'name': spell_name,
                        'source': racial_source,
                        'uses': 1,
                        'rest_type': 'Long Rest'
                    })
        
        # Also check raw spell data for limited use spells not in processed data
        if not free_cast_spells:
            for source_key, spell_list in raw_spells.items():
                if not isinstance(spell_list, list):
                    continue
                    
                for spell in spell_list:
                    if not isinstance(spell, dict):
                        continue
                        
                    definition = spell.get('definition', {})
                    spell_name = definition.get('name', '')
                    spell_level = definition.get('level', 0)
                    limited_use = spell.get('limitedUse')
                    uses_spell_slot = spell.get('usesSpellSlot', True)
                    
                    # Skip cantrips and spells that use spell slots
                    if spell_level == 0 or uses_spell_slot:
                        continue
                    
                    if limited_use:
                        max_uses = limited_use.get('maxUses', 1)
                        reset_type = limited_use.get('resetType', 2)
                        
                        # Map reset types: 1 = short rest, 2 = long rest, 3 = daily
                        if reset_type == 1:
                            rest_type = 'Short Rest'
                        elif reset_type == 2:
                            rest_type = 'Long Rest'
                        elif reset_type == 3:
                            rest_type = 'Daily'
                        else:
                            rest_type = 'Long Rest'  # Default
                        
                        # Determine source based on spell source
                        if source_key.lower() == 'race':
                            source_display = self._determine_racial_spell_source(character_data, spell_name)
                        elif source_key.lower() == 'feat':
                            source_display = self._determine_feat_spell_source(character_data, spell_name)
                        elif source_key.lower() == 'class':
                            source_display = self._determine_class_spell_source(character_data, spell_name)
                        elif source_key.lower() == 'item':
                            source_display = self._determine_item_spell_source(character_data, spell_name)
                        else:
                            source_display = source_key.title()
                        
                        free_cast_spells.append({
                            'name': spell_name,
                            'source': source_display,
                            'uses': max_uses,
                            'rest_type': rest_type
                        })
        
        # Check processed spells for other sources if no raw data found
        if not free_cast_spells:
            for source, spell_list in spells.items():
                for spell in spell_list:
                    spell_dict = self._convert_spell_to_dict(spell)
                    spell_name = spell_dict.get('name', '')
                    spell_level = spell_dict.get('level', 0)
                    source_info = spell_dict.get('source_info', {})
                    
                    # Skip cantrips (they're always free, but handled separately)
                    if spell_level == 0:
                        continue
                    
                    # Check for feat spells (usually once per long rest)
                    if source.lower() == 'feat':
                        # Extract feat name from source_info or use generic
                        feat_name = source_info.get('granted_by', 'Feat')
                        free_cast_spells.append({
                            'name': spell_name,
                            'source': feat_name,
                            'uses': 1,
                            'rest_type': 'Long Rest'
                        })
                    
                    # Check for class feature spells (varies by feature)
                    elif source.lower() == 'class':
                        class_source = self._determine_class_spell_source(character_data, spell_name)
                        free_cast_spells.append({
                            'name': spell_name,
                            'source': class_source,
                            'uses': 1,
                            'rest_type': 'Long Rest'
                        })
                    
                    # Check for magic item spells (varies by item)
                    elif source.lower() == 'item':
                        item_source = self._determine_item_spell_source(character_data, spell_name)
                        free_cast_spells.append({
                            'name': spell_name,
                            'source': item_source,
                            'uses': 1,
                            'rest_type': 'Long Rest'
                        })
        
        if not free_cast_spells:
            return ""
        
        section = "\n### Free Cast Spells\n> ```consumable\n> items:\n"
        
        for spell_data in free_cast_spells:
            spell_key = spell_data['name'].lower().replace(' ', '_').replace("'", "")
            uses_text = f"{spell_data['uses']}"
            if spell_data['uses'] > 1:
                uses_text += f" per {spell_data['rest_type']}"
            else:
                uses_text += f"/Long Rest" if spell_data['rest_type'] == 'Long Rest' else f"/{spell_data['rest_type']}"
            
            section += f">   - label: '{spell_data['name']} ({spell_data['source']}) - {uses_text}'\n"
            section += f">     state_key: {char_key}_{spell_key}_free\n"
            section += f">     uses: {spell_data['uses']}\n"
        
        section += "> ```\n>\n> ^freecasts"
        
        return section
    
    
    def _generate_spell_list_table(self, character_data: Dict[str, Any]) -> str:
        """Generate interactive spell list using datacorejsx component."""
        character_info = self.get_character_info(character_data)
        character_name = character_info.get('name', 'Unknown')

        # Sanitize character name for JSX
        # Replace double quotes with single quotes to match filename sanitization
        character_name_sanitized = character_name.replace('"', "'")

        # Get template settings from config if available
        jsx_components_dir = "z_Templates"
        spell_component = "SpellQuery.jsx"

        if self.config_manager:
            jsx_components_dir = self.config_manager.get_template_setting("jsx_components_dir", jsx_components_dir)
            spell_component = self.config_manager.get_template_setting("spell_component", spell_component)

        section = f"""
### Spell List

```datacorejsx
const {{ SpellQuery }} = await dc.require("{jsx_components_dir}/{spell_component}");
// Use character name approach as fallback since fileName is having datacore API issues
return <SpellQuery characterName="{character_name_sanitized}" />;
```

^spelltable"""

        return section
    
    def _generate_spell_details(self, character_data: Dict[str, Any]) -> str:
        """Generate detailed spell descriptions."""
        spells = self.get_spells(character_data)

        section = "\n### Spell Details\n"

        # Organize spells by name (alphabetically) since backup original doesn't group by level
        all_spells = []
        for source, spell_list in spells.items():
            for spell in spell_list:
                # Convert spell to dict and add source information for formatting
                spell_dict = self._convert_spell_to_dict(spell)
                spell_dict['display_source'] = source
                all_spells.append(spell_dict)

        # Sort spells by level first, then alphabetically by name
        all_spells.sort(key=lambda x: (x.get('level', 0), x.get('name', 'Unknown').lower()))

        # Generate details for each spell
        for spell in all_spells:
            spell_detail = self._generate_single_spell_detail(spell)
            section += spell_detail

        # Remove trailing <BR> tag and blank lines from the end of the section
        # This prevents extra spacing before the footer
        import re
        section = re.sub(r'\n*<BR>\n*$', '', section)
        section = section.rstrip()

        return section
    
    def _get_spell_source_indicator(self, spell: Dict[str, Any]) -> str:
        """
        Determine spell source indicator for badge.
        
        Returns:
            'F' if spell is enhanced from external spell files
            'A' if spell uses API data only (homebrew, custom, no file enhancement)
        """
        # Check if enhanced spell file exists for this spell
        if self._has_enhanced_spell_file(spell):
            return 'F'  # Enhanced from files
        else:
            return 'A'  # API only
    
    def _has_enhanced_spell_file(self, spell: Dict[str, Any]) -> bool:
        """Check if an enhanced spell file exists for this spell."""
        if not self.spell_extractor or not self.spell_extractor.spells_path:
            return False
            
        spell_name = spell.get('name', '').lower().replace(' ', '-').replace("'", "")
        spell_name = re.sub(r'[^\w\-]', '', spell_name)  # Remove special characters
        spell_file = Path(self.spell_extractor.spells_path) / f"{spell_name}-xphb.md"
        
        return spell_file.exists()
    
    def _is_homebrew_spell(self, spell: Dict[str, Any]) -> bool:
        """Check if this appears to be a homebrew/custom spell."""
        # Check if it's from an item source (often homebrew)
        source = spell.get('source', '')
        if source == 'Item':
            return True
            
        # Check for custom component indicators
        component_type_id = spell.get('component_type_id')
        if component_type_id and component_type_id > 100000000:  # High IDs often indicate custom content
            return True
            
        # Check if description suggests custom content
        description = spell.get('description', '')
        if 'homebrew' in description.lower() or 'custom' in description.lower():
            return True
            
        return False
    
    def _has_spell_file_enhancement(self, spell: Dict[str, Any]) -> bool:
        """Check if spell has enhancement from external spell files."""
        # This is a simplified check - in a full implementation, you'd check
        # if the spell exists in your spell files directory and if it was used
        # to enhance the description beyond what the API provides
        
        spell_name = spell.get('name', '').lower().replace(' ', '-').replace("'", "")
        
        # For now, return False to indicate most spells should show 'A'
        # until we have a proper spell file enhancement system
        return False

    def _generate_single_spell_detail(self, spell: Dict[str, Any]) -> str:
        """Generate detailed information for a single spell using restored extraction logic."""
        name = spell.get('name', 'Unknown Spell')
        level = spell.get('level', 0)
        school = spell.get('school', 'Unknown')
        
        # Initialize spell extractor if needed
        if self.spell_extractor is None:
            self._initialize_spell_extractor()
        
        # Use restored extraction logic with combat data
        casting_time = self.spell_extractor.extract_casting_time(spell, self.combat_data)
        range_text = self.spell_extractor.extract_range(spell, self.combat_data)
        components = self.spell_extractor.extract_components(spell, self.combat_data)
        duration = self.spell_extractor.extract_duration(spell, self.combat_data)
        
        # Build badges section
        level_label = "Cantrip" if level == 0 else f"Level {level}"
        
        # Determine data source indicator:
        # F = Enhanced from spell files
        # A = API only (homebrew, custom, or no external file enhancement)
        source_indicator = self._get_spell_source_indicator(spell)
        
        badges_section = f"""> ```badges
> items:
>   - label: {level_label}
>   - label: {school}
>   - label:
>   - label: {source_indicator}
> ```"""
        
        # Build spell-components section
        components_section = f"""> ```spell-components
> casting_time: {casting_time}
> range: {range_text}
> components: {components}
> duration: {duration}
> ```"""
        
        # Get description using spell extractor
        description = self.spell_extractor.get_spell_description(spell)
        
        # Clean HTML tags from description
        description = self.text_processor.format_spell_description(description)
        
        # Format description with proper indentation and blockquote
        description_lines = description.split('\n')
        formatted_description = ""
        for line in description_lines:
            if line.strip():
                formatted_description += f"> {line}\n"
            else:
                formatted_description += ">\n"
        
        # Build complete spell detail in backup original format
        spell_detail = f"""#### {name}
>
{badges_section}
>
{components_section}
>
{formatted_description}

<BR>

"""
        
        return spell_detail
    
    def _initialize_spell_extractor(self):
        """Initialize the spell data extractor with character data context."""
        # Get character context from current character data
        if hasattr(self, '_current_character_data'):
            character_data = self._current_character_data
        else:
            # Fallback for when character data is not set
            character_data = {}
        
        # Extract configuration
        character_info = character_data.get('character_info', {})
        meta_info = character_data.get('meta', {})
        feats = character_data.get('feats', [])
        
        # Fix rule_version detection by checking multiple sources (same as metadata.py fix)
        rule_version = (
            character_data.get('rule_version') or 
            character_info.get('rule_version') or 
            meta_info.get('rule_version', '2014')
        )
        
        # Get spells path from config if available
        spells_path = "obsidian/spells"  # Default fallback
        use_enhanced_spells = True
        if self.config_manager:
            # Try to get spells path from config
            try:
                paths = self.config_manager.resolve_paths()
                spells_path = str(paths.get("spells", "obsidian/spells"))
                use_enhanced_spells = self.config_manager.should_enhance_spells()
            except Exception as e:
                # If config access fails, use default path
                spells_path = "obsidian/spells"
        
        self.spell_extractor = SpellDataExtractor(
            spells_path=spells_path,
            use_enhanced_spells=use_enhanced_spells,
            rule_version=rule_version,
            character_feats=feats
        )
    
    def _format_internal(self, character_data: Dict[str, Any]) -> str:
        """
        Generate comprehensive spellcasting section.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Formatted spellcasting section
        """
        # Store character data for spell extractor initialization
        self._current_character_data = character_data
        
        spells = self.get_spells(character_data)
        
        if not spells:
            return ""
        
        sections = []
        
        # Header
        sections.append(self._generate_header())
        
        # Spell statistics
        sections.append(self._generate_spell_statistics(character_data))
        
        # Spell slots
        sections.append(self._generate_spell_slots(character_data))
        
        # Free cast spells
        free_cast_section = self._generate_free_cast_spells(character_data)
        if free_cast_section:
            sections.append(free_cast_section)
        
        # Spell list table
        sections.append(self._generate_spell_list_table(character_data))
        
        # Spell details
        sections.append(self._generate_spell_details(character_data))
        
        # Footer
        sections.append(self._generate_footer())
        
        return '\n'.join(section for section in sections if section)
    
    
    def _format_spell_source(self, spell: Dict[str, Any]) -> str:
        """Format spell source with proper names (deprecated - use spell extractor)."""
        # Initialize spell extractor if needed
        if self.spell_extractor is None:
            self._initialize_spell_extractor()
        
        return self.spell_extractor.format_spell_source(spell)
    
    
    
    def _determine_racial_spell_source(self, character_data: Dict[str, Any], spell_name: str) -> str:
        """Determine the specific racial spell source based on available feature data."""
        # Get character info to check species
        character_info = self.get_character_info(character_data)
        species_data = character_info.get('species', {})
        species_name = species_data.get('name', 'Unknown')
        
        # Look for racial traits that grant spells (v6.0.0 format)
        features_data = character_data.get('features', {})
        racial_traits = features_data.get('racial_traits', [])
        
        for trait in racial_traits:
            if isinstance(trait, dict):
                trait_name = trait.get('name', '')
                description = trait.get('description', '')
                
                # Look for traits that mention spells
                if 'spell' in trait_name.lower():
                    # Check if this trait mentions the specific spell
                    if spell_name.lower() in description.lower():
                        return trait_name
                    # Or if it's a general spell-granting trait
                    elif 'lineage' in trait_name.lower() or 'heritage' in trait_name.lower():
                        return trait_name
                elif 'magic' in trait_name.lower() and spell_name.lower() in description.lower():
                    return trait_name
        
        # If no specific trait found, use generic format
        return f'{species_name} Heritage'
    
    def _determine_feat_spell_source(self, character_data: Dict[str, Any], spell_name: str) -> str:
        """Determine the specific feat that grants a spell from processed data."""
        # Look in processed features for feats that grant spells (v6.0.0 format)
        features_data = character_data.get('features', {})
        feats = features_data.get('feats', [])
        
        for feat in feats:
            if isinstance(feat, dict):
                feat_name = feat.get('name', '')
                feat_description = feat.get('description', '')
                
                # Look for spells in feat description
                if spell_name.lower() in feat_description.lower():
                    return feat_name
                
                # Check for common spell-granting feat patterns
                if 'magic initiate' in feat_name.lower() and 'spell' in feat_description.lower():
                    return feat_name
                elif 'fey touched' in feat_name.lower() and spell_name.lower() in ['misty step', 'silvery barbs']:
                    return feat_name
                elif 'shadow touched' in feat_name.lower() and spell_name.lower() in ['invisibility']:
                    return feat_name
                elif 'telekinetic' in feat_name.lower() and spell_name.lower() in ['mage hand']:
                    return feat_name
        
        # If no specific feat found, use generic format
        return 'Feat'
    
    def _determine_class_spell_source(self, character_data: Dict[str, Any], spell_name: str) -> str:
        """Determine the specific class feature that grants a spell from processed data."""
        # Look in processed features for class features that grant spells (v6.0.0 format)
        features_data = character_data.get('features', {})
        class_features = features_data.get('class_features', [])
        
        for feature in class_features:
            if isinstance(feature, dict):
                feature_name = feature.get('name', '')
                feature_description = feature.get('description', '')
                
                # Look for spells in feature description
                if spell_name.lower() in feature_description.lower():
                    return feature_name
                
                # Check for common spell-granting class feature patterns
                if 'domain' in feature_name.lower() and 'spell' in feature_description.lower():
                    return feature_name
                elif 'magic' in feature_name.lower() and 'spell' in feature_description.lower():
                    return feature_name
                elif 'spells' in feature_name.lower():
                    return feature_name
        
        # If no specific feature found, use generic format
        return 'Class Feature'
    
    def _determine_item_spell_source(self, character_data: Dict[str, Any], spell_name: str) -> str:
        """Determine the specific magic item that grants a spell from processed data."""
        # Look in equipment for magic items that grant spells
        equipment_data = character_data.get('equipment', {})
        inventory = equipment_data.get('inventory', [])
        
        for item in inventory:
            if isinstance(item, dict):
                item_name = item.get('name', '')
                item_description = item.get('description', '')
                
                # Look for spells in item description
                if spell_name.lower() in item_description.lower():
                    return item_name
                
                # Check for common spell-granting item patterns
                if 'wand' in item_name.lower() and spell_name.lower() in item_description.lower():
                    return item_name
                elif 'staff' in item_name.lower() and spell_name.lower() in item_description.lower():
                    return item_name
                elif 'ring' in item_name.lower() and spell_name.lower() in item_description.lower():
                    return item_name
                elif 'cloak' in item_name.lower() and spell_name.lower() in item_description.lower():
                    return item_name
                elif 'boots' in item_name.lower() and spell_name.lower() in item_description.lower():
                    return item_name
        
        # If no specific item found, use generic format
        return 'Magic Item'
    
    def _generate_footer(self) -> str:
        """Generate spellcasting section footer."""
        return ">\n> ^spells\n\n^spellcasting\n\n---"