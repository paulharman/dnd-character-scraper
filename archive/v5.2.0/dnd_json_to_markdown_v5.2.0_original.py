#!/usr/bin/env python3
"""
DnD Character Scraper to Obsidian Markdown Converter
Converts enhanced_dnd_scraper.py output to DnD UI Toolkit format for Obsidian

This script replaces the PowerShell run_scraper.ps1 with Python equivalent
that works with the new enhanced JSON output format.

Configuration Variables:
"""

# ==========================================
# CONFIGURATION VARIABLES
# ==========================================

# Spell data enhancement settings
SPELLS_FOLDER_PATH = "/mnt/c/Users/alc_u/Documents/DnD/CharacterScraper/spells"  # Path to local spell markdown files
USE_ENHANCED_SPELL_DATA = True  # Whether to use local spell files for enhanced data
SPELL_FILE_SUFFIX = "-xphb.md"   # Suffix pattern for spell files

# Scraper settings
ENHANCED_SCRAPER_PATH = "/mnt/c/Users/alc_u/Documents/DnD/CharacterScraper/archive/v5.2.0/enhanced_dnd_scraper_v5.2.0_original.py"  # Path to enhanced scraper
DEFAULT_TIMEOUT = 300  # Timeout for scraper execution

# Output settings
VERBOSE_OUTPUT = False

# ==========================================

import argparse
import json
import logging
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class CharacterMarkdownGenerator:
    """Converts enhanced DnD scraper JSON to Obsidian markdown with DnD UI Toolkit format."""
    
    def __init__(self, character_data: Dict[str, Any]):
        self.data = character_data
        self.basic_info = character_data.get("basic_info", {})
        self.appearance = character_data.get("appearance", {})
        self.background = character_data.get("background", {})
        self.species = character_data.get("species", {})
        self.ability_scores = character_data.get("ability_scores", {})
        self.skills = character_data.get("skills", {})
        self.saving_throws = character_data.get("saving_throws", {})
        self.proficiencies = character_data.get("proficiencies", {})
        self.proficiency_sources = character_data.get("proficiency_sources", {})
        self.spells = character_data.get("spells", {})
        self.spell_slots = character_data.get("spell_slots", {})
        self.feats = character_data.get("feats", [])
        self.actions = character_data.get("actions", [])
        self.inventory = character_data.get("inventory", [])
        self.meta = character_data.get("meta", {})
        
        self.character_name = self.basic_info.get("name", "Unknown Character")
        self.level = self.basic_info.get("level", 1)
        self.classes = self.basic_info.get("classes", [])
        
    def get_proficiency_bonus(self) -> int:
        """Get proficiency bonus from scraper calculation."""
        # Use calculated value from scraper if available
        if "proficiency_bonus" in self.meta:
            return self.meta["proficiency_bonus"]
        # Fallback calculation if not available
        return 2 + ((self.level - 1) // 4)
    
    def get_primary_spellcasting_ability(self) -> str:
        """Get primary spellcasting ability from meta or infer from classes."""
        # First try to get from meta (new enhanced scraper feature)
        if "primary_spellcasting_ability" in self.meta and self.meta["primary_spellcasting_ability"]:
            return self.meta["primary_spellcasting_ability"]
        
        # Try to get from class spellcasting_ability field
        for cls in self.classes:
            spellcasting_ability = cls.get("spellcasting_ability", "").strip()
            if spellcasting_ability:
                return spellcasting_ability
        
        # Fallback: infer from classes
        for cls in self.classes:
            class_name = cls.get("name", "").lower()
            if class_name in ["wizard", "artificer"]:
                return "intelligence"
            elif class_name in ["cleric", "druid", "ranger"]:
                return "wisdom"
            elif class_name in ["bard", "sorcerer", "warlock", "paladin"]:
                return "charisma"
        
        return "intelligence"  # Default fallback
    
    def get_spell_save_dc(self) -> int:
        """Get spell save DC from spell data or calculate as fallback."""
        # Try to get from spell data first (scraper calculates this per spell)
        for spell_group in self.spells.values():
            for spell in spell_group:
                if spell.get("save_dc"):
                    return spell["save_dc"]
        
        # Fallback calculation if not available from scraper
        spellcasting_ability = self.get_primary_spellcasting_ability()
        spellcasting_mod = self.ability_scores.get(spellcasting_ability, {}).get("modifier", 0)
        return 8 + self.get_proficiency_bonus() + spellcasting_mod
    
    def has_spell_slots(self) -> bool:
        """Check if character has any spell slots (not just racial/item spells)."""
        # Check if spell_slots exists and has non-zero caster_level
        spell_slots = self.spell_slots
        if not spell_slots:
            return False
        
        # Check if caster level > 0
        caster_level = spell_slots.get("caster_level", 0)
        if caster_level > 0:
            return True
        
        # Check if has any regular or pact slots
        regular_slots = spell_slots.get("regular_slots", {})
        pact_slots = spell_slots.get("pact_slots", {})
        
        has_regular = any(slots > 0 for slots in regular_slots.values() if isinstance(slots, int))
        has_pact = bool(pact_slots.get("slots", 0) > 0)
        
        return has_regular or has_pact
    
    def get_initiative_modifier(self) -> int:
        """Get initiative modifier including bonuses from class features, feats, etc."""
        # Try to get initiative from enhanced scraper data first
        if "initiative" in self.basic_info and isinstance(self.basic_info["initiative"], dict):
            return self.basic_info["initiative"].get("total", 0)
        
        # Fallback to just dexterity modifier
        return self.ability_scores.get("dexterity", {}).get("modifier", 0)
    
    def get_armor_class(self) -> int:
        """Get AC from enhanced scraper data or calculate from inventory."""
        # Try to get AC from enhanced scraper first (check both locations)
        if "armor_class" in self.basic_info and self.basic_info["armor_class"].get("total"):
            return self.basic_info["armor_class"]["total"]
        elif "armor_class" in self.data and self.data["armor_class"].get("total"):
            return self.data["armor_class"]["total"]
        
        # Fallback to manual calculation
        return self.get_armor_class_from_inventory()
    
    def get_hit_dice_type(self) -> str:
        """Determine hit dice type based on primary class."""
        if not self.classes:
            return "6"
        
        primary_class = self.classes[0].get("name", "").lower()
        hit_die_map = {
            "barbarian": "12",
            "fighter": "10", "paladin": "10", "ranger": "10",
            "artificer": "8", "bard": "8", "cleric": "8", "druid": "8", 
            "monk": "8", "rogue": "8", "warlock": "8",
            "sorcerer": "6", "wizard": "6"
        }
        
        # Check if hit_die is available in the class data (new enhanced format)
        if self.classes[0].get("hit_die"):
            return str(self.classes[0]["hit_die"])
        
        return hit_die_map.get(primary_class, "6")
    
    def get_safe_state_key(self, name: str, suffix: str = "") -> str:
        """Generate a safe state key for DnD UI Toolkit."""
        if not name or not name.strip():
            name = "unknown"
        
        safe_name = name.lower().replace(' ', '_').replace("'", '').replace('-', '_')
        safe_name = re.sub(r'[^a-z0-9_]', '', safe_name)
        
        # Ensure doesn't start with number or underscore
        if safe_name and (safe_name[0].isdigit() or safe_name[0] == '_'):
            safe_name = f"item_{safe_name}"
        
        # Handle empty result after sanitization
        if not safe_name or safe_name == '_':
            safe_name = "unknown"
        
        # Clean up multiple underscores
        safe_name = re.sub(r'_+', '_', safe_name).strip('_')
        
        if suffix:
            safe_name += f"_{suffix}"
        
        return safe_name
    
    def format_modifier(self, value: int) -> str:
        """Format a modifier with proper +/- sign."""
        return f"+{value}" if value >= 0 else str(value)
    
    def extract_spell_components(self, spell: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Extract spell components from spell data. Uses D&D Beyond API data extracted by enhanced scraper."""
        
        # Check if spell data already has component fields from enhanced scraper
        components = {}
        if spell.get("casting_time"):
            components["casting_time"] = spell["casting_time"]
        if spell.get("range"):
            components["range"] = spell["range"]
        if spell.get("components"):
            components["components"] = spell["components"]
        if spell.get("duration"):
            components["duration"] = spell["duration"]
        
        if len(components) >= 3:  # If we have structured data, use it
            return components
        
        # Fallback: return None if no component data found
        # Note: Enhanced scraper should now provide component data from D&D Beyond API
        return None
    
    def load_enhanced_spell_data(self, spell_name: str) -> Dict[str, Any]:
        """Load enhanced spell data from local markdown files (parser only).
        Only use enhanced files for 2024 rules characters since enhanced files are 2024 rules."""
        if not USE_ENHANCED_SPELL_DATA:
            return {}
        
        # Check if character is using 2024 rules - only use enhanced files for 2024 characters
        is_2024_character = False
        if self.classes and len(self.classes) > 0:
            is_2024_character = self.classes[0].get("is_2024", False)
        
        # Enhanced spell files are 2024 rules only - don't use for 2014 characters
        if not is_2024_character:
            logger.debug(f"Skipping enhanced spell data for {spell_name} - character uses 2014 rules, enhanced files are 2024")
            return {}
        
        try:
            # Convert spell name to filename format
            filename = spell_name.lower().replace(' ', '-').replace("'", "")
            filename = re.sub(r'[^\w\-]', '', filename)  # Remove special characters
            spell_file_path = Path(SPELLS_FOLDER_PATH) / f"{filename}{SPELL_FILE_SUFFIX}"
            
            if not spell_file_path.exists():
                return {}
            
            with open(spell_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            enhanced_data = {}
            
            # Parse frontmatter and extract content
            if content.startswith('---'):
                try:
                    frontmatter_end = content.find('---', 3)
                    if frontmatter_end != -1:
                        frontmatter = content[3:frontmatter_end]
                        
                        # Extract the spell description content after frontmatter
                        spell_description = content[frontmatter_end + 3:].strip()
                        if spell_description:
                            # Clean up the spell description
                            cleaned_description = self._clean_enhanced_spell_description(spell_description)
                            enhanced_data['description'] = cleaned_description
                        
                        for line in frontmatter.split('\n'):
                            line = line.strip()
                            if ':' in line and not line.startswith('- '):
                                key, value = line.split(':', 1)
                                key = key.strip()
                                value = value.strip().strip('"').strip("'")
                                
                                if key == 'levelInt':  # Parse levelInt from enhanced files
                                    enhanced_data['level'] = int(value) if value.isdigit() else 0
                                elif key == 'ritual':
                                    enhanced_data['ritual'] = value.lower() == 'true'
                                elif key == 'school':
                                    enhanced_data['school'] = value
                
                except Exception as e:
                    logger.error(f"Error parsing frontmatter for {spell_name}: {e}")
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Error loading enhanced spell data for {spell_name}: {e}")
            return {}
    
    def _clean_enhanced_spell_description(self, description: str) -> str:
        """Clean up enhanced spell description by removing unwanted sections."""
        import re
        
        lines = description.split('\n')
        cleaned_lines = []
        skip_until_content = True
        in_summary_section = False
        
        for line in lines:
            # Skip until we find the actual spell content (after the duplicate header)
            if skip_until_content:
                # Look for the start of actual spell content (usually starts with "You" or a description)
                # Skip lines that are headers, images, or component lists
                if (line.startswith('# ') or 
                    line.startswith('*') or 
                    line.startswith('![') or
                    line.startswith('- **Casting time:**') or
                    line.startswith('- **Range:**') or
                    line.startswith('- **Components:**') or
                    line.startswith('- **Duration:**') or
                    line.strip() == ''):
                    continue
                else:
                    # Found actual content, stop skipping
                    skip_until_content = False
            
            # Remove image references
            if '![' in line and '/img/' in line:
                continue
                
            # Check for Summary section or Classes/Source sections to remove
            if line.startswith('## Summary') or line.startswith('**Classes**:'):
                in_summary_section = True
                continue
            
            # Check for Source line (appears after Classes)
            if in_summary_section and line.startswith('*Source:'):
                continue
                
            # If we're in summary section and hit another ## header, we're done with summary
            if in_summary_section and line.startswith('## ') and not line.startswith('## Summary'):
                in_summary_section = False
            
            # Skip lines that are part of the summary section
            if in_summary_section:
                continue
                
            # Add the line if we're not skipping
            if not skip_until_content:
                cleaned_lines.append(line)
        
        # Join back together and clean up extra whitespace
        cleaned_content = '\n'.join(cleaned_lines).strip()
        
        # Change ## headers to ##### headers within spell descriptions
        cleaned_content = re.sub(r'^## ', '##### ', cleaned_content, flags=re.MULTILINE)
        
        # Remove any trailing Classes/Source information that might not be in Summary section
        # Look for **Classes**: pattern and remove everything from there to the end
        classes_pattern = r'\n\*\*Classes\*\*:.*$'
        cleaned_content = re.sub(classes_pattern, '', cleaned_content, flags=re.DOTALL)
        
        # Remove Source lines that appear at the end
        source_pattern = r'\n\*Source:.*$'
        cleaned_content = re.sub(source_pattern, '', cleaned_content, flags=re.DOTALL)
        
        return cleaned_content.strip()
    
    def _wrap_in_callout(self, content: List[str], block_id: str) -> List[str]:
        """Wrap content in a callout block for proper embedding."""
        if not content:
            return []
        
        callout_content = []
        in_quote_block = False
        last_was_br = False  # Track if last element was a BR tag
        
        for i, line in enumerate(content):
            if line.strip():
                # Check if line is <BR> - keep these outside blockquotes
                if line.strip() == "<BR>":
                    # Close current blockquote if needed
                    if in_quote_block:
                        in_quote_block = False
                    # Add BR outside quote block
                    callout_content.append(line)
                    last_was_br = True
                # Check if line is a heading (starts with #) - keep headings outside blockquotes
                elif line.strip().startswith("#"):
                    # Close current blockquote if needed
                    if in_quote_block:
                        in_quote_block = False
                    # Add spacing before heading if not first item
                    if callout_content:
                        # Use blank line for #### headings (spell names - for links to work)
                        # Use > line for ##### headings (spell subsections)
                        if line.strip().startswith("####") and not line.strip().startswith("#####"):
                            callout_content.append("")
                        else:
                            callout_content.append(">")
                    
                    # #### headings (spell names) go outside quote blocks for linking
                    # ##### headings (spell subsections) go inside quote blocks
                    if line.strip().startswith("####") and not line.strip().startswith("#####"):
                        callout_content.append(line)  # No > prefix for spell names
                    else:
                        callout_content.append(f">{line}")  # > prefix for subsections
                    last_was_br = False
                else:
                    # Start quote block if not already in one
                    if not in_quote_block:
                        # Only add spacing line if there's previous content AND last wasn't a BR
                        if callout_content and not last_was_br:
                            callout_content.append(">")
                        in_quote_block = True
                    callout_content.append(f"> {line}")
                    last_was_br = False
            else:
                # For empty lines, only add them if we're in a quote block and need spacing
                if in_quote_block:
                    # Look ahead to see if next line is a heading or BR tag
                    next_line_is_heading = (i + 1 < len(content) and 
                                          content[i + 1].strip() and 
                                          content[i + 1].strip().startswith("#"))
                    next_line_is_br = (i + 1 < len(content) and 
                                     content[i + 1].strip() == "<BR>")
                    
                    if next_line_is_heading:
                        # End quote block before heading
                        in_quote_block = False
                    elif next_line_is_br:
                        # End quote block before BR tag and add a blank line
                        in_quote_block = False
                        callout_content.append("")  # Add blank line before BR
                    else:
                        # Add empty quote line for spacing within content
                        callout_content.append(">")
                last_was_br = False
        
        # Close quote block and add block ID
        if in_quote_block:
            callout_content.append(">")
        
        callout_content.append(f"> ^{block_id}")
        
        return callout_content
    
    def _format_background_description(self, description: str) -> List[str]:
        """Format background description with proper structure and line breaks."""
        if not description:
            return []
        
        lines = []
        
        # Parse the structured background information
        # Look for common patterns like **Ability Scores:**, **Feat:**, etc.
        import re
        
        # Split on major sections while preserving the section headers
        sections = re.split(r'(\*\*[^*]+:\*\*)', description)
        
        current_section = None
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
                
            # Check if this is a section header (like **Ability Scores:**)
            if section.startswith('**') and section.endswith(':**'):
                current_section = section.replace('**', '').replace(':', '')
                # Don't add the header yet - wait for content
            else:
                # This is content for the current section
                if current_section:
                    # Clean up the text and add proper formatting
                    content = section.strip()
                    
                    # Add section header inline with content
                    if current_section in ["Ability Scores", "Skill Proficiencies", "Tool Proficiency", "Feat"]:
                        lines.extend(["", f"**{current_section}:** {content}"])
                    elif current_section == "Equipment":
                        # Equipment section often has both rules and flavor text
                        # Try to separate the equipment choice from the background description
                        import re
                        equipment_match = re.match(r'(.*?)(\s+You\s+.+)', content, re.DOTALL)
                        if equipment_match:
                            equipment_info = equipment_match.group(1).strip()
                            background_description = equipment_match.group(2).strip()
                            lines.extend(["", f"**{current_section}:** {equipment_info}"])
                            lines.extend(["", background_description])
                        else:
                            lines.extend(["", f"**{current_section}:** {content}"])
                    else:
                        # This is likely the main description text
                        lines.extend(["", f"**{current_section}:** {content}"])
                    
                    current_section = None  # Reset after processing
                else:
                    # Content without a header - likely main description
                    # Look for flavor text that should be separate
                    if section.strip():
                        lines.extend(["", section])
        
        # Clean up empty lines and return
        cleaned_lines = []
        for line in lines:
            if line.strip() or (cleaned_lines and cleaned_lines[-1].strip()):
                cleaned_lines.append(line)
        
        return cleaned_lines
    
    def generate_frontmatter(self) -> List[str]:
        """Generate comprehensive YAML frontmatter with character metadata."""
        frontmatter = ["---"]
        
        # Avatar image if available
        avatar_url = self.basic_info.get("avatarUrl") or self.data.get("avatarUrl")
        if avatar_url:
            # Remove query parameters for cleaner URL
            clean_avatar_url = avatar_url.split('?')[0]
            frontmatter.append(f"avatar_url: \"{clean_avatar_url}\"")
        
        # Basic character info
        frontmatter.append(f"character_name: \"{self.character_name}\"")
        frontmatter.append(f"level: {self.level}")
        frontmatter.append(f"proficiency_bonus: {self.get_proficiency_bonus()}")
        
        # Experience if available
        experience = self.basic_info.get("experience")
        if experience is not None:
            frontmatter.append(f"experience: {experience}")
        
        # Class and subclass info
        if self.classes:
            primary_class = self.classes[0]
            frontmatter.append(f"class: \"{primary_class.get('name', 'Unknown')}\"")
            subclass = primary_class.get('subclass', '')
            if subclass:
                frontmatter.append(f"subclass: \"{subclass}\"")
            frontmatter.append(f"hit_die: \"d{primary_class.get('hit_die', 6)}\"")
            frontmatter.append(f"is_2024_rules: {primary_class.get('is_2024', False)}")
        
        # Species/Race info
        species_name = self.data.get("species", {}).get("name", "Unknown")
        if species_name and species_name != "Unknown":
            # Use race for 2014 rules, species for 2024 rules
            is_2024_rules = self.classes and self.classes[0].get("is_2024", False)
            species_key = "species" if is_2024_rules else "race"
            frontmatter.append(f"{species_key}: \"{species_name}\"")
        
        # Background info
        background_name = self.data.get("background", {}).get("name", "")
        if background_name:
            frontmatter.append(f"background: \"{background_name}\"")
        
        # Ability scores and modifiers
        frontmatter.append("ability_scores:")
        for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            score = self.ability_scores.get(ability, {}).get("score", 10)
            frontmatter.append(f"  {ability}: {score}")
        
        frontmatter.append("ability_modifiers:")
        for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            modifier = self.ability_scores.get(ability, {}).get("modifier", 0)
            frontmatter.append(f"  {ability}: {self.format_modifier(modifier)}")
        
        # Combat stats
        frontmatter.append(f"armor_class: {self.get_armor_class()}")
        
        hp_info = self.basic_info.get("hit_points", {})
        if hp_info:
            frontmatter.append(f"current_hp: {hp_info.get('current', 0)}")
            frontmatter.append(f"max_hp: {hp_info.get('maximum', 0)}")
            if hp_info.get('temporary', 0) > 0:
                frontmatter.append(f"temp_hp: {hp_info.get('temporary', 0)}")
        
        frontmatter.append(f"initiative: \"{self.format_modifier(self.get_initiative_modifier())}\"")
        
        # Spellcasting info if applicable (only for characters with spell slots)
        if self.spells and self.has_spell_slots():
            frontmatter.append(f"spellcasting_ability: \"{self.get_primary_spellcasting_ability()}\"")
            frontmatter.append(f"spell_save_dc: {self.get_spell_save_dc()}")
        
        # Character ID and metadata
        character_id = self.meta.get("character_id")
        if character_id:
            frontmatter.append(f"character_id: {character_id}")
        
        processed_timestamp = self.meta.get("processed_timestamp")
        if processed_timestamp:
            import datetime
            dt = datetime.datetime.fromtimestamp(processed_timestamp)
            frontmatter.append(f"processed_date: \"{dt.strftime('%Y-%m-%d %H:%M:%S')}\"")
        
        scraper_version = self.meta.get("scraper_version")
        if scraper_version:
            frontmatter.append(f"scraper_version: \"{scraper_version}\"")
        
        # Speed if available (from inventory or default)
        speed = "30 ft"  # Default
        frontmatter.append(f"speed: \"{speed}\"")
        
        # Proficiency information
        proficiencies = self.proficiencies
        if proficiencies:
            saving_throw_profs = []
            for ability, data in self.saving_throws.items():
                if isinstance(data, dict) and data.get("proficient", False):
                    saving_throw_profs.append(ability)
            if saving_throw_profs:
                frontmatter.append(f"saving_throw_proficiencies: {saving_throw_profs}")
        
        # Skill proficiencies count
        skill_profs = []
        for skill, data in self.skills.items():
            if isinstance(data, dict) and data.get("proficient", False):
                skill_profs.append(skill)
        if skill_profs:
            frontmatter.append(f"skill_count: {len(skill_profs)}")
        
        # Spell count if spellcaster
        if self.spells:
            total_spells = sum(len(spell_list) for spell_list in self.spells.values())
            frontmatter.append(f"spell_count: {total_spells}")
            
            # Spell levels known
            spell_levels = set()
            all_spell_names = []
            for spell_list in self.spells.values():
                for spell in spell_list:
                    spell_levels.add(spell.get("level", 0))
                    spell_name = spell.get("name", "")
                    if spell_name:
                        all_spell_names.append(spell_name)
            
            frontmatter.append(f"highest_spell_level: {max(spell_levels) if spell_levels else 0}")
            
            # Add spells for Obsidian linking and filtering
            if all_spell_names:
                unique_spells = sorted(set(all_spell_names))
                # Obsidian-style links for automatic linking to spell notes
                frontmatter.append("spells:")
                for spell_name in unique_spells:
                    # Convert spell name to filename format: "Acid Splash" -> "acid-splash-xphb"
                    spell_filename = spell_name.lower().replace(' ', '-').replace("'", '') + "-xphb"
                    frontmatter.append(f"  - \"[[{spell_filename}]]\"")
                # Simple list for queries and dataview
                frontmatter.append(f"spell_list: {unique_spells}")
        
        # Equipment count
        inventory_count = len(self.inventory) if self.inventory else 0
        frontmatter.append(f"inventory_items: {inventory_count}")
        
        # Passive scores (very useful for DMs and gameplay)
        # Try to get from enhanced scraper first
        passive_senses = None
        if "passive_senses" in self.meta:
            passive_senses = self.meta["passive_senses"]
        elif "passive_senses" in self.data:
            passive_senses = self.data["passive_senses"]
        
        if passive_senses:
            frontmatter.append(f"passive_perception: {passive_senses.get('perception', 10)}")
            frontmatter.append(f"passive_investigation: {passive_senses.get('investigation', 10)}")
            frontmatter.append(f"passive_insight: {passive_senses.get('insight', 10)}")
        else:
            # Fallback calculation
            wis_mod = self.ability_scores.get("wisdom", {}).get("modifier", 0)
            int_mod = self.ability_scores.get("intelligence", {}).get("modifier", 0)
            
            # Calculate passive perception (10 + WIS mod + proficiency if proficient)
            passive_perception = 10 + wis_mod
            if "perception" in [skill.lower().replace(' ', '-') for skill in self.proficiencies.get("skills", [])]:
                passive_perception += self.get_proficiency_bonus()
            frontmatter.append(f"passive_perception: {passive_perception}")
            
            # Calculate passive investigation (10 + INT mod + proficiency if proficient)
            passive_investigation = 10 + int_mod
            if "investigation" in [skill.lower().replace(' ', '-') for skill in self.proficiencies.get("skills", [])]:
                passive_investigation += self.get_proficiency_bonus()
            frontmatter.append(f"passive_investigation: {passive_investigation}")
            
            # Calculate passive insight (10 + WIS mod + proficiency if proficient)
            passive_insight = 10 + wis_mod
            if "insight" in [skill.lower().replace(' ', '-') for skill in self.proficiencies.get("skills", [])]:
                passive_insight += self.get_proficiency_bonus()
            frontmatter.append(f"passive_insight: {passive_insight}")
        
        # Wealth tracking - use individual currencies from scraper meta section
        individual_currencies = self.meta.get("individual_currencies", {})
        copper = individual_currencies.get("copper", 0)
        silver = individual_currencies.get("silver", 0)
        electrum = individual_currencies.get("electrum", 0)
        gold = individual_currencies.get("gold", 0)
        platinum = individual_currencies.get("platinum", 0)
        
        # Use calculated value from scraper
        total_wealth = self.meta.get("total_wealth_gp", 0)
        
        frontmatter.append(f"copper: {copper}")
        frontmatter.append(f"silver: {silver}")
        frontmatter.append(f"electrum: {electrum}")
        frontmatter.append(f"gold: {gold}")
        frontmatter.append(f"platinum: {platinum}")
        frontmatter.append(f"total_wealth_gp: {total_wealth}")
        
        # Carrying capacity from scraper calculation
        carrying_capacity = self.meta.get("carrying_capacity", self.ability_scores.get("strength", {}).get("score", 10) * 15)
        
        # Calculate current weight from inventory
        current_weight = 0
        for item in self.inventory:
            if item.get("equipped", False) or item.get("quantity", 1) > 0:
                item_weight = item.get("weight", 0) or 0
                quantity = item.get("quantity", 1)
                current_weight += item_weight * quantity
        
        frontmatter.append(f"carrying_capacity: {carrying_capacity}")
        frontmatter.append(f"current_weight: {int(current_weight)}")
        
        # Magic items and attunement
        magic_items = [item for item in self.inventory if item.get("rarity") and item["rarity"] != "Common"]
        attuned_items = [item for item in self.inventory if item.get("attuned", False)]
        
        frontmatter.append(f"magic_items_count: {len(magic_items)}")
        frontmatter.append(f"attuned_items: {len(attuned_items)}")
        frontmatter.append(f"max_attunement: 3")  # Standard D&D rule
        
        # Character progression
        experience = self.basic_info.get("experience", 0)
        
        # D&D 5e XP thresholds
        xp_thresholds = [0, 300, 900, 2700, 6500, 14000, 23000, 34000, 48000, 64000, 85000, 100000, 120000, 140000, 165000, 195000, 225000, 265000, 305000, 355000]
        
        next_level_xp = 0
        if self.level < 20:
            next_level_xp = xp_thresholds[self.level] if self.level < len(xp_thresholds) else 355000
        
        xp_to_next = max(0, next_level_xp - experience) if next_level_xp > 0 else 0
        
        frontmatter.append(f"next_level_xp: {next_level_xp}")
        frontmatter.append(f"xp_to_next_level: {xp_to_next}")
        
        # Multiclassing detection
        is_multiclass = len(self.classes) > 1
        frontmatter.append(f"multiclass: {is_multiclass}")
        
        # Total caster level from scraper calculation
        total_caster_level = self.meta.get("total_caster_level", 0)
        if total_caster_level > 0:
            frontmatter.append(f"total_caster_level: {total_caster_level}")
        
        # Resource tracking
        frontmatter.append(f"hit_dice_remaining: {self.level}")  # Assume full hit dice
        frontmatter.append(f"inspiration: false")  # Default to no inspiration
        frontmatter.append(f"exhaustion_level: 0")  # Default to no exhaustion
        
        # Feat tracking
        feat_count = len(self.feats) if self.feats else 0
        if feat_count > 0:
            frontmatter.append(f"feats_count: {feat_count}")
            feat_names = [feat.get("name", "") for feat in self.feats if feat.get("name")]
            if feat_names:
                frontmatter.append(f"feat_list: {feat_names}")
        
        # Character notes availability
        notes = self.data.get("notes", {}) or {}
        has_backstory = bool((notes.get("backstory") or "").strip())
        has_personality = any((notes.get(trait) or "").strip() for trait in ["personal_traits", "ideals", "bonds", "flaws"])
        if has_backstory:
            frontmatter.append("has_backstory: true")
        if has_personality:
            frontmatter.append("has_personality_traits: true")
        
        # Count personality elements
        personality_counts = {}
        for trait_type in ["personal_traits", "ideals", "bonds", "flaws"]:
            content = notes.get(trait_type, "")
            if content and content.strip():
                # Simple count by counting numbered items or line breaks
                count = len([line for line in content.split('\n') if line.strip()]) or 1
                personality_counts[trait_type] = count
        
        if personality_counts:
            frontmatter.append(f"personality_traits_count: {personality_counts.get('personal_traits', 0)}")
            frontmatter.append(f"ideals_count: {personality_counts.get('ideals', 0)}")
            frontmatter.append(f"bonds_count: {personality_counts.get('bonds', 0)}")
            frontmatter.append(f"flaws_count: {personality_counts.get('flaws', 0)}")
        
        # Campaign integration fields
        frontmatter.append(f"is_active: true")
        frontmatter.append(f"character_status: \"alive\"")
        
        # Source books detection (basic detection from classes and spells)
        source_books = set(["PHB"])  # Always include PHB
        
        # Detect source books from class names and subclasses
        for cls in self.classes:
            subclass = cls.get("subclass", "")
            if "Xanathar" in subclass or "XGE" in subclass:
                source_books.add("XGE")
            elif "Tasha" in subclass or "TCE" in subclass:
                source_books.add("TCE")
            elif "Sword Coast" in subclass or "SCAG" in subclass:
                source_books.add("SCAG")
        
        frontmatter.append(f"source_books: {sorted(list(source_books))}")
        frontmatter.append(f"homebrew_content: false")  # Assume official content
        frontmatter.append(f"official_content_only: true")
        
        # Template metadata
        frontmatter.append(f"template_version: \"1.0\"")
        frontmatter.append(f"auto_generated: true")
        frontmatter.append(f"manual_edits: false")
        
        # Tags for organization
        tags = ["dnd", "character-sheet"]
        if self.classes:
            class_name = self.classes[0].get('name', '').lower()
            tags.append(class_name)
            subclass = self.classes[0].get('subclass', '')
            if subclass:
                tags.append(f"{class_name}-{subclass.lower().replace(' ', '-').replace('the-', '')}")
        if background_name:
            tags.append(background_name.lower().replace(' ', '-'))
        if species_name and species_name != "Unknown":
            tags.append(species_name.lower().replace(' ', '-'))
        
        # Level-based tags
        if self.level >= 17:
            tags.append("high-level")
        elif self.level >= 11:
            tags.append("mid-high-level")
        elif self.level >= 5:
            tags.append("mid-level")
        else:
            tags.append("low-level")
        
        # Spellcaster tag (only for characters with spell slots)
        if self.spells and self.has_spell_slots():
            tags.append("spellcaster")
        
        frontmatter.append(f"tags: {tags}")
        
        frontmatter.append("---")
        return frontmatter
    
    def generate_stats_block(self) -> List[str]:
        """Generate stats block for key character information."""
        initiative = self.format_modifier(self.get_initiative_modifier())
        ac = self.get_armor_class()
        
        # Get AC sublabel from equipped armor
        ac_sublabel = self.get_ac_sublabel()
        
        block = [
            "```stats",
            "items:",
            f"  - label: Level",
            f"    value: '{self.level}'",
            f"  - label: Initiative",
            f"    value: '{initiative}'"
        ]
        
        # Add AC with sublabel if available
        if ac_sublabel:
            block.extend([
                f"  - label: Armor Class",
                f"    sublabel: {ac_sublabel}",
                f"    value: {ac}"
            ])
        else:
            block.extend([
                f"  - label: Armor Class",
                f"    value: {ac}"
            ])
        
        block.extend([
            "",
            "grid:",
            "  columns: 3",
            "```"
        ])
        
        return block
    
    def generate_secondary_stats_block(self) -> List[str]:
        """Generate secondary stats block for additional character info."""
        prof_bonus = self.get_proficiency_bonus()
        
        # Calculate speed (default 30 for most races)
        speed = 30  # Could be enhanced to read from character data
        
        # Get primary class and subclass
        primary_class = "Unknown"
        subclass = ""
        if self.classes:
            primary_class = self.classes[0].get("name", "Unknown")
            subclass = self.classes[0].get("subclass", "")
        
        class_display = primary_class
        if subclass:
            class_display = f"{primary_class} ({subclass})"
        
        block = [
            "",
            "```stats",
            "items:",
            f"  - label: Proficiency Bonus",
            f"    value: '+{prof_bonus}'",
            f"  - label: Speed",
            f"    value: '{speed} ft'",
            f"  - label: Class",
            f"    value: '{primary_class}'",
            f"  - label: Subclass",
            f"    value: '{subclass if subclass else ''}'"
        ]
        
        # Add hit dice info
        hit_dice_type = self.get_hit_dice_type()
        block.extend([
            f"  - label: Hit Dice",
            f"    value: 'd{hit_dice_type}'",
            "",
            "grid:",
            "  columns: 5",
            "```"
        ])
        
        return block
    
    def get_ac_sublabel(self) -> str:
        """Get AC sublabel describing armor source."""
        # Try to get AC calculation from enhanced scraper first (check both locations)
        if "armor_class" in self.basic_info and self.basic_info["armor_class"].get("calculation"):
            return self.basic_info["armor_class"]["calculation"]
        elif "armor_class" in self.data and self.data["armor_class"].get("calculation"):
            return self.data["armor_class"]["calculation"]
        
        # Fallback to manual inventory check
        for item in self.inventory:
            if item.get("equipped", False):
                item_name = item.get("name", "").lower()
                if "scale mail" in item_name:
                    return "Scale Mail (14 + Dex)"
                elif "leather armor" in item_name:
                    return "Leather Armor (11 + Dex)"
                elif "studded leather" in item_name:
                    return "Studded Leather (12 + Dex)"
                elif "chain mail" in item_name:
                    return "Chain Mail (16)"
                elif "chain shirt" in item_name:
                    return "Chain Shirt (13 + Dex)"
        
        return "Unarmored (10 + Dex)"
    
    def generate_health_block(self) -> List[str]:
        """Generate health points block."""
        hp_info = self.basic_info.get("hit_points", {})
        current_hp = hp_info.get("current", 1)
        max_hp = hp_info.get("maximum", 1)
        hit_dice_type = self.get_hit_dice_type()
        state_key = self.get_safe_state_key(self.character_name, "health")
        
        return [
            "```healthpoints",
            f"state_key: {state_key}",
            f"health: {max_hp}",
            f"hitdice:",
            f"  dice: d{hit_dice_type}",
            f"  value: {self.level}",
            "```"
        ]
    
    def generate_ability_block(self) -> List[str]:
        """Generate abilities block with proficiencies."""
        block = [
            "## Abilities",
            "",
            "```ability",
            "abilities:"
        ]
        
        # Add ability scores
        for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            score = self.ability_scores.get(ability, {}).get("score", 10)
            block.append(f"  {ability}: {score}")
        
        # Add saving throw proficiencies
        saving_throw_profs = []
        proficiency_bonus = self.get_proficiency_bonus()
        
        for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            ability_mod = self.ability_scores.get(ability, {}).get("modifier", 0)
            save_bonus = self.ability_scores.get(ability, {}).get("save_bonus", ability_mod)
            
            # If save bonus is higher than ability modifier, character has proficiency
            if save_bonus > ability_mod:
                saving_throw_profs.append(f"  - {ability}")
        
        if saving_throw_profs:
            block.append("")
            block.append("proficiencies:")
            block.extend(saving_throw_profs)
        
        block.append("```")
        
        return block
    
    def calculate_passive_scores(self) -> dict:
        """Get passive scores from scraper calculation."""
        # Use calculated values from scraper if available
        passive_senses = None
        if "passive_senses" in self.meta:
            passive_senses = self.meta["passive_senses"]
        elif "passive_senses" in self.data:
            passive_senses = self.data["passive_senses"]
        
        if passive_senses:
            return {
                'perception': passive_senses.get('perception', 10),
                'investigation': passive_senses.get('investigation', 10),
                'insight': passive_senses.get('insight', 10)
            }
        else:
            # Fallback calculation if scraper values not available
            wis_mod = self.ability_scores.get("wisdom", {}).get("modifier", 0)
            int_mod = self.ability_scores.get("intelligence", {}).get("modifier", 0)
            
            # Calculate passive perception (10 + WIS mod + proficiency if proficient)
            passive_perception = 10 + wis_mod
            if "perception" in [skill.lower().replace(' ', '-') for skill in self.proficiencies.get("skills", [])]:
                passive_perception += self.get_proficiency_bonus()
            
            # Calculate passive investigation (10 + INT mod + proficiency if proficient)
            passive_investigation = 10 + int_mod
            if "investigation" in [skill.lower().replace(' ', '-') for skill in self.proficiencies.get("skills", [])]:
                passive_investigation += self.get_proficiency_bonus()
            
            # Calculate passive insight (10 + WIS mod + proficiency if proficient)
            passive_insight = 10 + wis_mod
            if "insight" in [skill.lower().replace(' ', '-') for skill in self.proficiencies.get("skills", [])]:
                passive_insight += self.get_proficiency_bonus()
            
            return {
                'perception': passive_perception,
                'investigation': passive_investigation,
                'insight': passive_insight
            }
    
    def generate_passive_badges(self) -> List[str]:
        """Generate passive scores as badges."""
        passives = self.calculate_passive_scores()
        
        return [
            "```badges",
            "items:",
            f"  - label: Passive Perception",
            f"    value: {passives['perception']}",
            f"  - label: Passive Investigation",
            f"    value: {passives['investigation']}",
            f"  - label: Passive Insight",
            f"    value: {passives['insight']}",
            "```"
        ]
    
    def generate_skills_block(self) -> List[str]:
        """Generate skills block with expertise detection."""
        block = [
            "## Skills",
            "",
            "```skills",
            "proficiencies:"
        ]
        
        # Get skill proficiencies from proficiencies data
        skill_proficiencies = self.proficiencies.get("skills", [])
        proficiency_bonus = self.get_proficiency_bonus()
        
        # Convert to valid skill names for DnD UI Toolkit
        valid_skills = [
            "acrobatics", "animal_handling", "arcana", "athletics", "deception", "history", "insight",
            "intimidation", "investigation", "medicine", "nature", "perception", "performance",
            "persuasion", "religion", "sleight_of_hand", "stealth", "survival"
        ]
        
        # Map skill names to their corresponding abilities
        skill_ability_map = {
            "acrobatics": "dexterity", "animal_handling": "wisdom", "arcana": "intelligence",
            "athletics": "strength", "deception": "charisma", "history": "intelligence",
            "insight": "wisdom", "intimidation": "charisma", "investigation": "intelligence",
            "medicine": "wisdom", "nature": "intelligence", "perception": "wisdom",
            "performance": "charisma", "persuasion": "charisma", "religion": "intelligence",
            "sleight_of_hand": "dexterity", "stealth": "dexterity", "survival": "wisdom"
        }
        
        expertise_skills = []
        regular_skills = []
        
        for skill in skill_proficiencies:
            skill_name = skill.lower().replace(' ', '_').replace('-', '_')
            if skill_name in valid_skills:
                # Check if this skill has expertise (double proficiency)
                skill_key = skill.lower().replace(' ', '-')
                if skill_key in self.skills:
                    skill_bonus = self.skills[skill_key]
                    ability_name = skill_ability_map.get(skill_name, "dexterity")
                    ability_modifier = self.ability_scores.get(ability_name, {}).get("modifier", 0)
                    
                    # Expected bonus with proficiency: ability_mod + proficiency_bonus
                    # Expected bonus with expertise: ability_mod + (2 * proficiency_bonus)
                    expected_prof = ability_modifier + proficiency_bonus
                    expected_expertise = ability_modifier + (2 * proficiency_bonus)
                    
                    if skill_bonus == expected_expertise:
                        expertise_skills.append(skill_name)
                    else:
                        regular_skills.append(skill_name)
                else:
                    regular_skills.append(skill_name)
        
        # Add regular proficiencies
        for skill in regular_skills:
            block.append(f"  - {skill}")
        
        # Add expertise section if there are any
        if expertise_skills:
            block.append("")
            block.append("expertise:")
            for skill in expertise_skills:
                block.append(f"  - {skill}")
        
        # Add skill bonuses if any unusual modifiers are detected
        skill_bonuses = []
        for skill in skill_proficiencies:
            skill_name = skill.lower().replace(' ', '_').replace('-', '_')
            if skill_name in valid_skills:
                skill_key = skill.lower().replace(' ', '-')
                if skill_key in self.skills:
                    skill_bonus = self.skills[skill_key]
                    ability_name = skill_ability_map.get(skill_name, "dexterity")
                    ability_modifier = self.ability_scores.get(ability_name, {}).get("modifier", 0)
                    
                    # Calculate expected values
                    expected_prof = ability_modifier + proficiency_bonus
                    expected_expertise = ability_modifier + (2 * proficiency_bonus)
                    
                    # If the bonus doesn't match standard proficiency or expertise, it's a custom bonus
                    if skill_bonus != ability_modifier and skill_bonus != expected_prof and skill_bonus != expected_expertise:
                        bonus_value = skill_bonus - ability_modifier
                        if skill_name not in expertise_skills:  # Don't double-count expertise skills
                            skill_bonuses.append({"name": skill_name, "value": bonus_value})
        
        # Add bonuses section if there are any custom modifiers
        if skill_bonuses:
            block.append("")
            block.append("bonuses:")
            for bonus in skill_bonuses:
                block.extend([
                    f"  - name: {bonus['name'].replace('_', ' ').title()}",
                    f"    target: {bonus['name']}",
                    f"    value: {bonus['value']}"
                ])
        
        block.append("```")
        
        return block
    
    def _get_skill_proficiency_sources(self) -> List[str]:
        """Get skill proficiency sources with detailed attribution."""
        skill_sources = []
        skill_proficiencies = self.proficiencies.get("skills", [])
        
        # Parse background skill proficiencies
        background_skills = []
        if self.background and self.background.get("description"):
            description = self.background["description"]
            # Look for "Skill Proficiencies:" pattern
            import re
            skill_match = re.search(r'Skill Proficiencies:\*\*\s*([^*]+)', description)
            if skill_match:
                skills_text = skill_match.group(1).strip()
                # Parse "Arcana and History" format
                background_skills = [s.strip() for s in re.split(r'\s+and\s+|,\s*', skills_text)]
        
        # Parse species/racial skill proficiencies
        species_skills = []
        if self.species and self.species.get("traits"):
            for trait in self.species["traits"]:
                trait_name = trait.get("name", "")
                trait_description = trait.get("description", "")
                if "skill" in trait_name.lower() or "proficiency" in trait_name.lower():
                    # Extract skill names from trait description
                    if any(skill.lower() in trait_description.lower() for skill in skill_proficiencies):
                        for skill in skill_proficiencies:
                            if skill.lower() in trait_description.lower():
                                species_skills.append(skill)
        
        # Generate source attributions
        for skill in skill_proficiencies:
            # Use proficiency sources from scraper if available
            if skill in self.proficiency_sources:
                source_text = self.proficiency_sources[skill]
                skill_sources.append(f"**{skill}** ({source_text})")
            else:
                # Fallback to pattern matching for backward compatibility
                sources = []
                
                if skill in background_skills:
                    background_name = self.background.get("name", "Background")
                    sources.append(f"Background: {background_name}")
                
                if skill in species_skills:
                    species_name = self.species.get("name", "Species")
                    sources.append(f"Species: {species_name}")
                
                # Check for class-granted skills (common for some classes)
                for class_info in self.classes:
                    class_name = class_info.get("name", "")
                    if class_name.lower() == "wizard" and skill in ["Investigation"]:
                        sources.append(f"Class: {class_name}")
                    elif class_name.lower() == "rogue" and skill in ["Perception", "Investigation"]:
                        sources.append(f"Class: {class_name}")
                
                # If no specific source found, try to infer from common patterns
                if not sources:
                    if skill in ["Insight", "Perception"]:
                        # These might be from species traits
                        if self.species:
                            species_name = self.species.get("name", "Species")
                            sources.append(f"Species: {species_name} (Inferred)")
                    else:
                        sources.append("Unknown Source")
                
                if sources:
                    source_text = ", ".join(sources)
                    skill_sources.append(f"**{skill}** ({source_text})")
        
        return skill_sources
    
    def _get_saving_throw_sources(self) -> List[str]:
        """Get saving throw proficiency sources with detailed attribution."""
        save_sources = []
        proficiency_bonus = self.get_proficiency_bonus()
        
        # Determine which saves have proficiency
        proficient_saves = []
        for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            ability_mod = self.ability_scores.get(ability, {}).get("modifier", 0)
            save_bonus = self.ability_scores.get(ability, {}).get("save_bonus", ability_mod)
            
            # If save bonus is higher than ability modifier, character has proficiency
            if save_bonus > ability_mod:
                proficient_saves.append(ability)
        
        # Determine sources for each proficient save
        for save in proficient_saves:
            sources = []
            
            # Check class-based saving throw proficiencies
            for class_info in self.classes:
                class_name = class_info.get("name", "").lower()
                
                # Common class saving throw proficiencies
                if class_name == "wizard" and save in ["intelligence", "wisdom"]:
                    sources.append(f"Class: Wizard")
                elif class_name == "fighter" and save in ["strength", "constitution"]:
                    sources.append(f"Class: Fighter")
                elif class_name == "rogue" and save in ["dexterity", "intelligence"]:
                    sources.append(f"Class: Rogue")
                elif class_name == "cleric" and save in ["wisdom", "charisma"]:
                    sources.append(f"Class: Cleric")
                elif class_name == "barbarian" and save in ["strength", "constitution"]:
                    sources.append(f"Class: Barbarian")
                elif class_name == "bard" and save in ["dexterity", "charisma"]:
                    sources.append(f"Class: Bard")
                elif class_name == "druid" and save in ["intelligence", "wisdom"]:
                    sources.append(f"Class: Druid")
                elif class_name == "monk" and save in ["strength", "dexterity"]:
                    sources.append(f"Class: Monk")
                elif class_name == "paladin" and save in ["wisdom", "charisma"]:
                    sources.append(f"Class: Paladin")
                elif class_name == "ranger" and save in ["strength", "dexterity"]:
                    sources.append(f"Class: Ranger")
                elif class_name == "sorcerer" and save in ["constitution", "charisma"]:
                    sources.append(f"Class: Sorcerer")
                elif class_name == "warlock" and save in ["wisdom", "charisma"]:
                    sources.append(f"Class: Warlock")
                elif class_name == "artificer" and save in ["constitution", "intelligence"]:
                    sources.append(f"Class: Artificer")
            
            # Check for feat-based proficiencies
            for feat in self.feats:
                feat_name = feat.get("name", "").lower()
                if "resilient" in feat_name and save in feat_name:
                    sources.append(f"Feat: Resilient ({save.title()})")
                elif "war caster" in feat_name and save == "constitution":
                    sources.append("Feat: War Caster")
            
            # Check for species/racial proficiencies (rare but possible)
            if self.species and self.species.get("traits"):
                for trait in self.species["traits"]:
                    trait_name = trait.get("name", "").lower()
                    trait_description = trait.get("description", "").lower()
                    if ("saving throw" in trait_description or "save" in trait_description) and save in trait_description:
                        species_name = self.species.get("name", "Species")
                        sources.append(f"Species: {species_name}")
            
            # If no source found, indicate it's likely class-based
            if not sources:
                # Try to infer from level and class
                primary_class = self.classes[0].get("name", "Unknown") if self.classes else "Unknown"
                sources.append(f"Class: {primary_class} (Inferred)")
            
            if sources:
                source_text = ", ".join(sources)
                save_sources.append(f"**{save.title()}** ({source_text})")
        
        return save_sources
    
    def generate_proficiency_sources_block(self) -> List[str]:
        """Generate combined proficiency sources (skills + saves) in single callout."""
        skill_sources = self._get_skill_proficiency_sources()
        save_sources = self._get_saving_throw_sources()
        
        if not skill_sources and not save_sources:
            return []
        
        block = ["", "### Proficiency Sources"]
        sources_content = [""]
        
        if skill_sources:
            sources_content.append("**Skill Bonuses:**")
            for skill_info in skill_sources:
                sources_content.append(f"- {skill_info}")
            
        if save_sources:
            if skill_sources:
                sources_content.append("")  # Add spacing between sections
            sources_content.append("**Saving Throw Bonuses:**")
            for save_info in save_sources:
                sources_content.append(f"- {save_info}")
        
        # Wrap combined content in callout
        callout_content = self._wrap_in_callout(sources_content, "proficiency-sources")
        block.extend(callout_content)
        
        return block
    
    def _process_species_traits(self) -> List[str]:
        """Process species traits with enhanced descriptions and proper trait combinations."""
        if not self.species or not self.species.get("traits"):
            return []
        
        traits_block = []
        species_name = self.species.get("name", "Species")
        
        # Group traits by semantic category to reduce duplication
        trait_categories = {
            "senses": [],
            "proficiencies": [],
            "bonuses": [],
            "resistances": [],
            "immunities": [],
            "advantages": [],
            "languages": [],
            "special_abilities": []
        }
        
        # Categorize traits semantically
        for trait in self.species["traits"]:
            trait_type = trait.get("type", "unknown")
            trait_name = trait.get("name", "Unknown Trait")
            trait_description = trait.get("description", "")
            
            if trait_type == "sense":
                trait_categories["senses"].append(trait)
            elif trait_type == "proficiency" or "proficiency" in trait_name.lower():
                trait_categories["proficiencies"].append(trait)
            elif trait_type == "bonus" or trait_name == "Bonus":
                trait_categories["bonuses"].append(trait)
            elif trait_type == "resistance":
                trait_categories["resistances"].append(trait)
            elif trait_type == "immunity":
                trait_categories["immunities"].append(trait)
            elif trait_type == "advantage":
                trait_categories["advantages"].append(trait)
            elif trait_type == "language" or "language" in trait_name.lower():
                trait_categories["languages"].append(trait)
            elif trait_type in ["set", "ignore", "disadvantage", "expertise"] or trait_name in ["Set", "Ignore", "Disadvantage", "Expertise"]:
                # Skip technical/mechanical traits that aren't player-facing
                continue
            else:
                trait_categories["special_abilities"].append(trait)
        
        # Process each category
        processed_traits = []
        
        # Handle Fey Ancestry special case (advantage + immunity combination)
        fey_ancestry_processed = False
        if trait_categories["advantages"] and trait_categories["immunities"]:
            for adv_trait in trait_categories["advantages"]:
                if "saving throws" in adv_trait.get("description", "").lower():
                    for imm_trait in trait_categories["immunities"]:
                        if "magical sleep" in imm_trait.get("description", "").lower():
                            processed_traits.append({
                                "name": "Fey Ancestry",
                                "description": "You have advantage on saving throws against being charmed, and magic can't put you to sleep.",
                                "category": "Special Abilities"
                            })
                            fey_ancestry_processed = True
                            break
                    if fey_ancestry_processed:
                        break
        
        # Process senses
        if trait_categories["senses"]:
            sense_descriptions = []
            for trait in trait_categories["senses"]:
                sense_type = trait.get("sense_type", "unknown")
                if sense_type == "darkvision":
                    range_val = trait.get("range", 60)
                    sense_descriptions.append(f"**Darkvision {range_val} ft.** You can see in dim light within {range_val} feet as if it were bright light, and in darkness as if it were dim light. You discern colors in that darkness only as shades of gray.")
                else:
                    sense_descriptions.append(f"**{sense_type.title()}:** {trait.get('description', '')}")
            
            if sense_descriptions:
                processed_traits.append({
                    "name": "Senses",
                    "description": "\n\n".join(sense_descriptions),
                    "category": "Senses"
                })
        
        # Process proficiencies (combined)
        if trait_categories["proficiencies"]:
            prof_descriptions = []
            for trait in trait_categories["proficiencies"]:
                prof_type = trait.get("proficiency_type", "")
                description = trait.get("description", "")
                if prof_type:
                    prof_descriptions.append(f"**{prof_type.title()}:** {description}")
                else:
                    prof_descriptions.append(description)
            
            if prof_descriptions:
                processed_traits.append({
                    "name": "Proficiencies",
                    "description": "\n\n".join(prof_descriptions),
                    "category": "Proficiencies"
                })
        
        # Process bonuses (combined and deduplicated)
        if trait_categories["bonuses"]:
            bonus_descriptions = []
            seen_bonuses = set()
            for trait in trait_categories["bonuses"]:
                description = trait.get("description", "")
                if description:
                    # Clean up bonus descriptions
                    if description.startswith("Bonus: "):
                        description = description[7:]  # Remove "Bonus: " prefix
                    
                    # Avoid duplicates
                    if description not in seen_bonuses:
                        seen_bonuses.add(description)
                        bonus_descriptions.append(description)
            
            if bonus_descriptions:
                processed_traits.append({
                    "name": "Ability Score Increases",
                    "description": "\n\n".join(bonus_descriptions),
                    "category": "Bonuses"
                })
        
        # Process languages (combined)
        if trait_categories["languages"]:
            lang_descriptions = []
            for trait in trait_categories["languages"]:
                description = trait.get("description", "")
                if description:
                    lang_descriptions.append(description)
            
            if lang_descriptions:
                processed_traits.append({
                    "name": "Languages",
                    "description": "\n\n".join(lang_descriptions),
                    "category": "Languages"
                })
        
        # Process advantages (except Fey Ancestry)
        if trait_categories["advantages"] and not fey_ancestry_processed:
            for trait in trait_categories["advantages"]:
                description = trait.get("description", "")
                if "saving throws" not in description.lower():  # Skip if it's Fey Ancestry
                    processed_traits.append({
                        "name": trait.get("name", "Advantage"),
                        "description": description,
                        "category": "Special Abilities"
                    })
        
        # Process immunities (except Fey Ancestry)
        if trait_categories["immunities"] and not fey_ancestry_processed:
            for trait in trait_categories["immunities"]:
                description = trait.get("description", "")
                if "magical sleep" not in description.lower():  # Skip if it's Fey Ancestry
                    processed_traits.append({
                        "name": trait.get("name", "Immunity"),
                        "description": description,
                        "category": "Special Abilities"
                    })
        
        # Process resistances
        if trait_categories["resistances"]:
            for trait in trait_categories["resistances"]:
                processed_traits.append({
                    "name": trait.get("name", "Resistance"),
                    "description": trait.get("description", ""),
                    "category": "Special Abilities"
                })
        
        # Process other special abilities
        if trait_categories["special_abilities"]:
            for trait in trait_categories["special_abilities"]:
                processed_traits.append({
                    "name": trait.get("name", "Special Ability"),
                    "description": trait.get("description", ""),
                    "category": "Special Abilities"
                })
        
        # Generate the traits block
        if processed_traits:
            traits_block.extend(["", f"### {species_name} Traits"])
            for trait in processed_traits:
                # Only add trait if it has meaningful content
                description = trait.get('description', '').strip()
                if description:
                    traits_block.extend([
                        "",
                        f"#### {trait['name']}",
                        "",
                        description
                    ])
                else:
                    # Add header only for traits without descriptions
                    traits_block.extend([
                        "",
                        f"#### {trait['name']}"
                    ])
        
        return traits_block
    
    def generate_wealth_encumbrance_block(self) -> List[str]:
        """Generate wealth and encumbrance details."""
        block = ["", "### Wealth & Encumbrance"]
        
        # Wealth breakdown
        if "individual_currencies" in self.meta:
            currencies = self.meta["individual_currencies"]
            total_wealth = self.meta.get("total_wealth_gp", 0)
            
            wealth_parts = []
            if currencies.get("platinum", 0) > 0:
                wealth_parts.append(f"{currencies['platinum']} pp")
            if currencies.get("gold", 0) > 0:
                wealth_parts.append(f"{currencies['gold']} gp") 
            if currencies.get("electrum", 0) > 0:
                wealth_parts.append(f"{currencies['electrum']} ep")
            if currencies.get("silver", 0) > 0:
                wealth_parts.append(f"{currencies['silver']} sp")
            if currencies.get("copper", 0) > 0:
                wealth_parts.append(f"{currencies['copper']} cp")
                
            if wealth_parts:
                block.append(f"**Wealth:** {', '.join(wealth_parts)} *(Total: {total_wealth} gp)*")
            else:
                block.append(f"**Wealth:** {total_wealth} gp")
        
        # Encumbrance tracking
        carrying_capacity = self.meta.get("carrying_capacity", 0)
        if carrying_capacity > 0:
            # Calculate current weight from inventory
            current_weight = 0
            if self.inventory:
                for item in self.inventory:
                    item_weight = item.get("weight", 0)
                    quantity = item.get("quantity", 1)
                    current_weight += item_weight * quantity
            
            encumbrance_percent = (current_weight / carrying_capacity) * 100 if carrying_capacity > 0 else 0
            
            # Determine encumbrance status
            if encumbrance_percent < 50:
                status = "Light"
            elif encumbrance_percent < 100:
                status = "Heavy"
            else:
                status = "Overloaded"
            
            block.append(f"**Encumbrance:** {current_weight:.1f}/{carrying_capacity} lbs ({encumbrance_percent:.0f}% - {status})")
        
        return block
    
    def _sort_actions_by_type(self, actions_list: List[str]) -> List[str]:
        """Sort actions by type: physical/martial first (alphabetically), then magical by spell level (alphabetically within level)."""
        import re
        
        # Common D&D cantrip names for detection
        common_cantrips = {
            "acid splash", "blade ward", "booming blade", "chill touch", "control flames",
            "create bonfire", "dancing lights", "druidcraft", "eldritch blast", "fire bolt",
            "friends", "frostbite", "green-flame blade", "guidance", "gust", "infestation",
            "light", "mage hand", "magic stone", "mending", "message", "minor illusion",
            "mold earth", "poison spray", "prestidigitation", "produce flame", "ray of frost",
            "resistance", "sacred flame", "shape water", "shocking grasp", "spare the dying",
            "sword burst", "thaumaturgy", "thorn whip", "thunderclap", "toll the dead",
            "true strike", "vicious mockery", "word of radiance"
        }
        
        physical = []
        magical_by_level = {}
        
        for action in actions_list:
            action_lower = action.lower()
            
            # Check if this is a spell with level notation
            if "(" in action and "level)" in action:
                # Extract spell level for sorting
                level_match = re.search(r'\(([^)]+) level\)', action)
                if level_match:
                    level_text = level_match.group(1).lower()
                    
                    # Convert level text to sorting order
                    if level_text == "cantrip":
                        level_order = 0
                    else:
                        level_order = {
                            "1st": 1, "2nd": 2, "3rd": 3, "4th": 4, "5th": 5,
                            "6th": 6, "7th": 7, "8th": 8, "9th": 9
                        }.get(level_text, 99)
                    
                    if level_order not in magical_by_level:
                        magical_by_level[level_order] = []
                    magical_by_level[level_order].append(action)
                else:
                    # Has parentheses but not spell level - treat as physical
                    physical.append(action)
            elif action_lower in common_cantrips:
                # This is a cantrip without level notation - treat as level 0 spell
                if 0 not in magical_by_level:
                    magical_by_level[0] = []
                magical_by_level[0].append(action)
            else:
                # No level notation and not a known cantrip - treat as physical/martial
                physical.append(action)
        
        # Build sorted result
        result = []
        
        # Add physical actions first (alphabetically)
        result.extend(sorted(physical))
        
        # Add magical actions by spell level, then alphabetically within each level
        for level in sorted(magical_by_level.keys()):
            result.extend(sorted(magical_by_level[level]))
        
        return result

    def _spell_provides_ongoing_bonus_action(self, description: str) -> bool:
        """Check if spell description indicates ongoing bonus action abilities."""
        import re
        
        # More specific patterns that indicate ongoing bonus action abilities
        bonus_action_patterns = [
            r'as a bonus action.*you can.*command',
            r'as a bonus action.*you can.*attack',
            r'as a bonus action.*you can.*move',
            r'bonus action.*you can.*command',
            r'bonus action.*mentally command',
            r'on each of your turns.*bonus action.*you can',
            r'on your turn.*bonus action.*you can',
            r'bonus action.*cause.*to (attack|move|act)',
            r'subsequent turns.*bonus action'
        ]
        
        for pattern in bonus_action_patterns:
            if re.search(pattern, description):
                return True
        return False

    def _spell_provides_ongoing_reaction(self, description: str) -> bool:
        """Check if spell description indicates ongoing reaction abilities for the caster."""
        import re
        
        # Very specific patterns that indicate the caster gains ongoing reaction abilities
        reaction_patterns = [
            r'as a reaction.*you can',
            r'use your reaction.*to',
            r'when.*you can use your reaction',
            r'you may use your reaction',
            r'allows you.*reaction'
        ]
        
        # Exclude patterns that mention reactions in other contexts
        exclusion_patterns = [
            r"can't take reactions",
            r"cannot take reactions", 
            r"unable to take reactions",
            r"loses.*reaction",
            r"no reactions"
        ]
        
        # Check for exclusions first
        for exclusion in exclusion_patterns:
            if re.search(exclusion, description):
                return False
        
        # Then check for valid reaction patterns
        for pattern in reaction_patterns:
            if re.search(pattern, description):
                return True
        return False

    def _get_ongoing_ability_type(self, description: str, action_type: str = "bonus action") -> str:
        """Get the type of ongoing ability (Command, Attack, Move, etc.)."""
        import re
        
        if action_type == "bonus action":
            # Check for specific verbs in description to determine ability type
            if re.search(r'command|direct', description):
                return "Command"
            elif re.search(r'attack', description):
                return "Attack"
            elif re.search(r'move', description):
                return "Move"
            else:
                return "Control"
        
        elif action_type == "reaction":
            if re.search(r'trigger|activate', description):
                return "Trigger"
            elif re.search(r'counter|prevent', description):
                return "Counter"
            else:
                return "React"
        
        return "Use"

    def _is_bonus_action_feature(self, feature_name: str, description: str) -> bool:
        """Check if a feature uses a bonus action."""
        import re
        
        # Check feature name patterns
        bonus_action_names = [
            "innate sorcery", "metamagic", "font of magic.*create"
        ]
        
        feature_lower = feature_name.lower()
        for pattern in bonus_action_names:
            if re.search(pattern, feature_lower):
                return True
        
        # Check description patterns
        bonus_action_patterns = [
            r'as a bonus action',
            r'bonus action.*you can',
            r'use.*bonus action'
        ]
        
        for pattern in bonus_action_patterns:
            if re.search(pattern, description):
                return True
        
        return False

    def _is_reaction_feature(self, feature_name: str, description: str) -> bool:
        """Check if a feature uses a reaction."""
        import re
        
        reaction_patterns = [
            r'as a reaction',
            r'use your reaction',
            r'reaction.*you can'
        ]
        
        for pattern in reaction_patterns:
            if re.search(pattern, description):
                return True
        
        return False

    def _is_actionable_feature(self, feature_name: str, description: str) -> bool:
        """Check if a feature is actually an action (vs passive/resource)."""
        import re
        
        # Features that are resources or passive abilities, not actions
        non_action_patterns = [
            r'sorcery points?$',
            r'convert spell slots?$',
            r'spell slots?.*level',
            r'no action required',
            r'passive',
            r'permanent'
        ]
        
        feature_lower = feature_name.lower()
        for pattern in non_action_patterns:
            if re.search(pattern, feature_lower):
                return False
        
        for pattern in non_action_patterns:
            if re.search(pattern, description):
                return False
        
        return True

    def _get_sorcery_points(self) -> int:
        """Calculate sorcery points for sorcerer levels."""
        sorcerer_level = 0
        
        # Find sorcerer levels
        for cls in self.classes:
            if cls.get("name", "").lower() == "sorcerer":
                sorcerer_level = cls.get("level", 0)
                break
        
        # Sorcery points = sorcerer level
        return sorcerer_level

    def _process_font_of_magic_feature(self, feature_name: str, feature: Dict[str, Any], source_info: str) -> List[str]:
        """Special processing for Font of Magic features with improved formatting."""
        # Enhanced header with source
        if source_info:
            feature_block = ["", f"### {feature_name} ({source_info})"]
        else:
            feature_block = ["", f"### {feature_name}"]
        
        # Remove consumables for Font of Magic features as requested
        # Instead provide clean description with improved table formatting
        
        if "sorcery points" in feature_name.lower():
            # Main sorcery points feature with improved table
            feature_block.extend([
                "",
                "You can tap into the wellspring of magic within yourself. This wellspring is represented by Sorcery Points, which allow you to create a variety of magical effects.",
                "",
                f"You have {self._get_sorcery_points()} Sorcery Points, and you regain all expended Sorcery Points when you finish a Long Rest.",
                "",
                "**Converting Spell Slots to Sorcery Points:** You can expend a spell slot to gain a number of Sorcery Points equal to the slot's level (no action required).",
                "",
                "**Creating Spell Slots:** As a Bonus Action, you can transform unexpended Sorcery Points into one spell slot according to the table below:",
                "",
                "| Spell Slot Level | Sorcery Point Cost | Min. Sorcerer Level |",
                "|:----------------:|:-----------------:|:-------------------:|",
                "| 1st              | 2                 | 2                   |",
                "| 2nd              | 3                 | 3                   |",
                "| 3rd              | 5                 | 5                   |",
                "| 4th              | 6                 | 7                   |",
                "| 5th              | 7                 | 9                   |",
                "",
                "*You can create a spell slot no higher than level 5. Any spell slot you create with this feature vanishes when you finish a Long Rest.*"
            ])
        elif "convert spell slots" in feature_name.lower():
            # Simplified convert spell slots feature
            feature_block.extend([
                "",
                "You can expend a spell slot to gain a number of Sorcery Points equal to the slot's level (no action required).",
                "",
                "*See Font of Magic: Sorcery Points for the full conversion table.*"
            ])
        elif "create spell slot" in feature_name.lower():
            # Simplified create spell slot feature
            feature_block.extend([
                "",
                "As a Bonus Action, you can transform unexpended Sorcery Points into one spell slot.",
                "",
                "*See Font of Magic: Sorcery Points for the full conversion table.*"
            ])
        else:
            # Fallback for other Font of Magic features
            description = feature.get("description", "")
            if description:
                feature_block.extend(["", description])
        
        return feature_block

    def generate_action_economy_block(self) -> List[str]:
        """Generate action economy quick reference."""
        block = ["", "### Action Economy"]
        
        # Add note about spell preparation for wizards
        is_wizard = any(cls.get("name", "").lower() == "wizard" for cls in self.classes)
        if is_wizard:
            block.append("*Note: Shows cantrips (always available), prepared spells, ritual spells (can be cast unprepared), and always-prepared spells.*")
            block.append("")
        
        # Analyze available actions
        actions = []
        bonus_actions = []
        reactions = []
        
        # Separate lists for ongoing spell abilities
        ongoing_bonus_actions = []
        ongoing_reactions = []
        
        # Check spells for action types
        all_spells = []
        if self.spells:
            for spell_list in self.spells.values():
                if isinstance(spell_list, list):
                    all_spells.extend(spell_list)
        
        # Categorize spells by casting time (only include always prepared or cantrips)
        for spell in all_spells:
            casting_time = spell.get("casting_time", "").lower()
            spell_name = spell.get("name", "Unknown")
            level = spell.get("level", 0)
            always_prepared = spell.get("always_prepared", False)
            preparation_type = spell.get("preparation_type", "")
            description = spell.get("description", "").lower()
            
            # Only include spells that are:
            # 1. Always prepared (racial/feat spells)
            # 2. Cantrips (always available)
            # 3. Actually prepared or effectively prepared (includes rituals)
            # 4. Known spells for non-prepared casters
            effective_prepared = spell.get("effective_prepared", False)
            spell_available = (
                always_prepared or 
                level == 0 or  # Cantrips
                effective_prepared or  # Actually prepared (includes rituals for wizards)
                preparation_type in ["known", "always_known"]  # Non-wizard casters
            )
            
            if not spell_available:
                continue  # Skip unprepared wizard spells
            
            # Check for ongoing abilities that provide different action types
            ongoing_bonus_action = self._spell_provides_ongoing_bonus_action(description)
            ongoing_reaction = self._spell_provides_ongoing_reaction(description)
            
            spell_display = f"{spell_name} ({level}{'st' if level == 1 else 'nd' if level == 2 else 'rd' if level == 3 else 'th'} level)" if level > 0 else spell_name
            
            # Primary casting time categorization
            if "bonus action" in casting_time:
                bonus_actions.append(spell_display)
            elif "reaction" in casting_time:
                reactions.append(spell_display)
            elif "action" in casting_time:
                actions.append(spell_display)
            
            # Add ongoing abilities to separate lists
            if ongoing_bonus_action:
                ability_type = self._get_ongoing_ability_type(description)
                ongoing_entry = f"{spell_name} - {ability_type}"
                if ongoing_entry not in ongoing_bonus_actions:
                    ongoing_bonus_actions.append(ongoing_entry)
            
            if ongoing_reaction:
                ability_type = self._get_ongoing_ability_type(description, action_type="reaction")
                ongoing_entry = f"{spell_name} - {ability_type}"
                if ongoing_entry not in ongoing_reactions:
                    ongoing_reactions.append(ongoing_entry)
        
        # Add class features and actions (with proper action type detection)
        for action in self.actions:
            action_name = action.get("name", "")
            action_description = (action.get("description") or "").lower()
            
            if action_name:
                # Check if this feature should be classified as a bonus action
                if self._is_bonus_action_feature(action_name, action_description):
                    bonus_actions.append(action_name)
                # Check if this feature should be classified as a reaction
                elif self._is_reaction_feature(action_name, action_description):
                    reactions.append(action_name)
                # Check if this is not an action at all (resource/passive)
                elif not self._is_actionable_feature(action_name, action_description):
                    continue  # Skip non-actionable features
                else:
                    actions.append(action_name)
        
        # Add basic combat actions (universal)
        actions.extend(["Attack", "Cast a Spell", "Dash", "Disengage", "Dodge", "Help", "Hide", "Ready", "Search", "Use Object"])
        
        # Add character-specific bonus actions and reactions
        has_two_weapon_fighting = False
        has_offhand_weapon = False
        
        # Check for two-weapon fighting capability
        if self.inventory:
            light_weapons = 0
            for item in self.inventory:
                if item.get("equipped", False):
                    item_type = (item.get("type") or "").lower()
                    item_name = (item.get("name") or "").lower()
                    if "dagger" in item_name or ("light" in item_type and "weapon" in item_type):
                        light_weapons += 1
            
            if light_weapons >= 2:
                has_offhand_weapon = True
        
        # Check for fighting style or features that enable two-weapon fighting
        for feat in self.feats:
            feat_name = feat.get("name", "").lower()
            if "two weapon" in feat_name or "dual wield" in feat_name:
                has_two_weapon_fighting = True
        
        # Only add two-weapon options if character actually has the capability
        if has_offhand_weapon or has_two_weapon_fighting:
            bonus_actions.append("Off-hand Attack")
            if has_two_weapon_fighting:
                bonus_actions.append("Two-Weapon Fighting")
        
        # Universal reactions
        reactions.extend(["Opportunity Attack", "Ready Action Trigger"])
        
        # Add spell-specific reactions (with same availability check)
        for spell in all_spells:
            if "reaction" in spell.get("casting_time", "").lower():
                level = spell.get("level", 0)
                always_prepared = spell.get("always_prepared", False)
                preparation_type = spell.get("preparation_type", "")
                
                # Apply same availability check as above
                effective_prepared = spell.get("effective_prepared", False)
                spell_available = (
                    always_prepared or 
                    level == 0 or  # Cantrips
                    effective_prepared or  # Actually prepared (includes rituals for wizards)
                    preparation_type in ["known", "always_known"]  # Non-wizard casters
                )
                
                if spell_available:
                    spell_name = spell.get("name", "Unknown")
                    if spell_name not in reactions:
                        reactions.append(spell_name)
        
        # Display categorized actions
        if actions:
            block.append("**Action:**")
            
            # Separate spell/class actions from standard actions
            spell_class_actions = []
            standard_actions = ["Attack", "Cast a Spell", "Dash", "Disengage", "Dodge", "Help", "Hide", "Ready", "Search", "Use Object"]
            
            for action in actions:
                if action not in standard_actions:
                    spell_class_actions.append(action)
            
            # Sort spell/class actions using new sorting scheme
            sorted_actions = self._sort_actions_by_type(spell_class_actions)
            
            # Show sorted spell/class actions first
            for action in sorted_actions:
                block.append(f"- {action}")
            
            # Show standard actions in a group
            if any(action in actions for action in standard_actions):
                block.append("- **Standard Actions:** Attack, Cast a Spell, Dash, Disengage, Dodge, Help, Hide, Ready, Search, Use Object")
        
        if bonus_actions or ongoing_bonus_actions:
            block.append("")
            block.append("**Bonus Action:**")
            
            # Show regular bonus actions first
            if bonus_actions:
                sorted_bonus_actions = self._sort_actions_by_type(bonus_actions)
                for bonus_action in sorted_bonus_actions:
                    block.append(f"- {bonus_action}")
            
            # Show ongoing spell abilities under "If cast:" section
            if ongoing_bonus_actions:
                if bonus_actions:  # Add spacing if there were regular bonus actions
                    block.append("")
                block.append("")
                block.append("If cast:")
                sorted_ongoing_bonus = sorted(ongoing_bonus_actions)
                for ongoing_action in sorted_ongoing_bonus:
                    block.append(f"- {ongoing_action}")
        
        if reactions or ongoing_reactions:
            block.append("")
            block.append("**Reaction:**")
            
            # Show regular reactions first
            if reactions:
                sorted_reactions = self._sort_actions_by_type(reactions)
                for reaction in sorted_reactions:
                    block.append(f"- {reaction}")
            
            # Show ongoing spell abilities under "If cast:" section
            if ongoing_reactions:
                if reactions:  # Add spacing if there were regular reactions
                    block.append("")
                block.append("")
                block.append("If cast:")
                sorted_ongoing_reactions = sorted(ongoing_reactions)
                for ongoing_reaction in sorted_ongoing_reactions:
                    block.append(f"- {ongoing_reaction}")
        
        return block
    
    def _get_item_granted_modifiers(self) -> List[str]:
        """Get modifiers granted by equipped items with detailed source information."""
        item_modifiers = []
        
        if not self.inventory:
            return item_modifiers
        
        for item in self.inventory:
            item_name = item.get("name", "Unknown Item")
            equipped = item.get("equipped", False)
            
            # Only process equipped items
            if not equipped:
                continue
            
            # Check for item modifiers (this would need to be expanded based on available data)
            # For now, we'll look for common item types that grant modifiers
            item_type = (item.get("type") or "").lower()
            
            # Check for armor class bonuses
            if "armor" in item_type and item.get("armor_class"):
                ac_bonus = item.get("armor_class", {}).get("base", 0)
                if ac_bonus > 0:
                    item_modifiers.append(f"**{item_name}**: +{ac_bonus} AC (Armor)")
            
            # Check for weapon bonuses
            if "weapon" in item_type:
                weapon_data = item.get("damage", {})
                if weapon_data:
                    damage_bonus = weapon_data.get("bonus", 0)
                    if damage_bonus > 0:
                        item_modifiers.append(f"**{item_name}**: +{damage_bonus} Attack/Damage (Weapon)")
            
            # Check for shield bonuses
            if "shield" in item_type:
                shield_ac = item.get("armor_class", {}).get("base", 0)
                if shield_ac > 0:
                    item_modifiers.append(f"**{item_name}**: +{shield_ac} AC (Shield)")
            
            # Check for magical item properties
            if item.get("magical", False):
                # This would need more detailed parsing based on item properties
                properties = item.get("properties", [])
                for prop in properties:
                    if prop.get("description"):
                        item_modifiers.append(f"**{item_name}**: {prop.get('description')} (Magical Property)")
        
        return item_modifiers
    
    def generate_spell_quick_reference(self) -> List[str]:
        """Generate spell quick reference with components and resources."""
        if not self.spells:
            return []
            
        block = ["", "### Spell Quick Reference"]
        
        # Collect all spells with enhanced information
        all_spells = []
        if self.spells:
            for spell_source, spell_list in self.spells.items():
                if isinstance(spell_list, list):
                    for spell in spell_list:
                        spell_info = {
                            "name": spell.get("name", "Unknown"),
                            "level": spell.get("level", 0),
                            "casting_time": spell.get("casting_time", ""),
                            "range": spell.get("range", ""),
                            "components": spell.get("components", ""),
                            "duration": spell.get("duration", ""),
                            "concentration": spell.get("concentration", False),
                            "ritual": spell.get("ritual", False),
                            "source": spell_source
                        }
                        all_spells.append(spell_info)
        
        # Group by level
        spells_by_level = {}
        for spell in all_spells:
            level = spell["level"]
            if level not in spells_by_level:
                spells_by_level[level] = []
            spells_by_level[level].append(spell)
        
        # Display organized spell info
        for level in sorted(spells_by_level.keys()):
            level_name = "Cantrips" if level == 0 else f"Level {level}"
            block.append(f"**{level_name}:**")
            
            for spell in spells_by_level[level]:
                spell_line = f"- **{spell['name']}**"
                
                # Add key info inline
                info_parts = []
                if spell["concentration"]:
                    info_parts.append("Concentration")
                if spell["ritual"]:
                    info_parts.append("Ritual")
                if spell["casting_time"] and "action" not in spell["casting_time"].lower():
                    info_parts.append(spell["casting_time"])
                if spell["range"] and spell["range"].lower() not in ["special", "self"]:
                    info_parts.append(spell["range"])
                
                if info_parts:
                    spell_line += f" *({', '.join(info_parts)})*"
                
                block.append(spell_line)
                
                # Add component info
                if spell["components"]:
                    components = spell["components"]
                    # Highlight expensive components
                    if " gp" in components.lower() or "worth" in components.lower():
                        block.append(f"  💰 {components}")
                    else:
                        block.append(f"  🔹 {components}")
            
            block.append("")  # Space between levels
        
        return block
    
    def generate_concentration_tracker(self) -> List[str]:
        """Generate concentration spell tracker."""
        if not self.spells:
            return []
            
        # Find concentration spells
        concentration_spells = []
        if self.spells:
            for spell_source, spell_list in self.spells.items():
                if isinstance(spell_list, list):
                    for spell in spell_list:
                        if spell.get("concentration", False):
                            concentration_spells.append({
                                "name": spell.get("name", "Unknown"),
                                "level": spell.get("level", 0),
                                "duration": spell.get("duration", ""),
                                "source": spell_source
                            })
        
        if not concentration_spells:
            return []
            
        block = ["", "### Concentration Spells"]
        block.append("*Remember: Only one concentration spell at a time!*")
        block.append("")
        
        for spell in concentration_spells:
            level_text = f"Level {spell['level']}" if spell['level'] > 0 else "Cantrip"
            duration_text = f" ({spell['duration']})" if spell['duration'] else ""
            block.append(f"- **{spell['name']}** ({level_text}){duration_text}")
        
        return block
    
    def _get_feature_source_info(self, feature: Dict[str, Any]) -> str:
        """Get detailed source information for a feature (feat, action, or class feature)."""
        feature_name = feature.get("name", "").lower()
        feature_source = feature.get("source", "")
        
        # Parse source IDs to determine feature origin
        if "feat:" in feature_source:
            # Regular feat
            return "Feat"
        elif "background_feat:" in feature_source:
            # Background-granted feat
            if self.background:
                background_name = self.background.get("name", "Background")
                return f"Background: {background_name}"
            return "Background Feat"
        elif "class_feature:" in feature_source:
            # Class feature
            return "Class Feature"
        
        # Infer source from feature name patterns
        if any(keyword in feature_name for keyword in ["magic initiate", "initiate"]):
            if self.background:
                background_name = self.background.get("name", "Background")
                return f"Background: {background_name}"
            return "Feat"
        
        # Check if it's a known class feature
        class_features = {
            "spellcasting": "Class Feature",
            "signature spells": "Class Feature", 
            "arcane recovery": "Class Feature",
            "spell mastery": "Class Feature",
            "ritual casting": "Class Feature",
            "action surge": "Class Feature",
            "second wind": "Class Feature",
            "fighting style": "Class Feature",
            "cunning action": "Class Feature",
            "sneak attack": "Class Feature",
            "rage": "Class Feature",
            "unarmored defense": "Class Feature",
            "wild shape": "Class Feature",
            "channel divinity": "Class Feature",
            "divine smite": "Class Feature",
            "lay on hands": "Class Feature"
        }
        
        for class_feature, source_type in class_features.items():
            if class_feature in feature_name:
                if self.classes:
                    class_name = self.classes[0].get("name", "Class")
                    return f"{source_type}: {class_name}"
                return source_type
        
        # Check if it's species-related
        if self.species:
            species_name = self.species.get("name", "").lower()
            if any(keyword in feature_name for keyword in ["elven", "dwarven", "halfling", "elf", "dwarf"]):
                return f"Species: {self.species.get('name', 'Species')}"
        
        # Default to unknown source
        return ""
    
    def generate_spell_slots_block(self) -> List[str]:
        """Generate spell slots consumable block."""
        if not self.spells or not self.has_spell_slots():
            return []
        
        block = [
            "",
            "### Spell Slots",
            "",
            "```consumable",
            "items:"
        ]
        
        # Use spell slots from enhanced scraper if available
        regular_slots = self.spell_slots.get("regular_slots", {})
        state_key_base = self.get_safe_state_key(self.character_name)
        
        # Add sorcery points for sorcerers FIRST (above regular spell slots as requested)
        sorcery_points = self._get_sorcery_points()
        if sorcery_points > 0:
            block.extend([
                f"  - label: 'Sorcery Points'",
                f"    state_key: {state_key_base}_sorcery_points",
                f"    uses: {sorcery_points}"
            ])
        
        # Process regular spell slots
        for slot_level, count in regular_slots.items():
            if count > 0:
                level_num = slot_level.replace("level_", "")
                block.extend([
                    f"  - label: 'Level {level_num}'",
                    f"    state_key: {state_key_base}_spells_{level_num}",
                    f"    uses: {count}"
                ])
        
        # Handle pact magic slots if present
        pact_slots = self.spell_slots.get("pact_slots", {})
        if pact_slots and "slots" in pact_slots:
            pact_count = pact_slots["slots"]
            pact_level = pact_slots.get("level", 1)
            block.extend([
                f"  - label: 'Pact Magic (Level {pact_level})'",
                f"    state_key: {state_key_base}_pact_magic",
                f"    uses: {pact_count}"
            ])
        
        # Add free spell casts from features
        free_casts = self._get_free_spell_casts()
        for cast_info in free_casts:
            block.extend([
                f"  - label: '{cast_info['label']}'",
                f"    state_key: {state_key_base}_{cast_info['key']}",
                f"    uses: {cast_info['uses']}"
            ])
        
        block.append("```")
        return block
    
    def _get_free_spell_casts(self) -> List[Dict[str, Any]]:
        """Identify spells with limited free casts from features."""
        free_casts = []
        
        # Check all spells for limited usage
        for source, spell_list in self.spells.items():
            if not isinstance(spell_list, list):
                continue
                
            for spell in spell_list:
                usage_type = spell.get("usage_type", "")
                if usage_type == "per-rest":  # Only show limited-use spells, not at-will cantrips
                    spell_name = spell.get("name", "Unknown")
                    level = spell.get("level", 0)
                    source_info = spell.get("source_info", {})
                    
                    # Format the label based on source
                    if source_info.get("feature") == "Feat Grant":
                        # Look for the specific feat name
                        feat_names = [feat.get("name", "") for feat in self.feats if "Magic Initiate" in feat.get("name", "")]
                        if feat_names:
                            label = f"{spell_name} ({feat_names[0]})"
                        else:
                            label = f"{spell_name} (Feat)"
                    elif source_info.get("feature") == "Racial Trait":
                        species_name = self.species.get("name", "Species")
                        label = f"{spell_name} ({species_name})"
                    elif source_info.get("feature") == "Background Spell":
                        background_name = self.background.get("name", "Background")
                        label = f"{spell_name} ({background_name})"
                    else:
                        label = f"{spell_name} (Free Cast)"
                    
                    # Create safe state key
                    safe_spell_name = self.get_safe_state_key(spell_name)
                    safe_source = self.get_safe_state_key(source_info.get("feature", "free"))
                    
                    free_casts.append({
                        "label": label,
                        "key": f"{safe_spell_name}_{safe_source}",
                        "uses": 1  # Most free casts are once per long rest
                    })
        
        return free_casts
    
    def generate_features_block(self) -> List[str]:
        """Generate features block from feats and actions."""
        block = ["## Features"]
        
        # Passive features that shouldn't have consumable uses
        passive_features = {
            "spellcasting", "elven lineage", "elven lineage spells", 
            "magic initiate (wizard)", "signature spells", "darkvision",
            "fey ancestry", "trance"
        }
        
        # Process feats
        for feat in self.feats:
            if feat.get("name") and feat.get("description"):
                block.extend(self._process_feature(feat, passive_features))
        
        # Process actions
        for action in self.actions:
            if action.get("name") and action.get("description"):
                block.extend(self._process_feature(action, passive_features))
        
        # Process species traits with enhanced descriptions
        if self.species and self.species.get("traits"):
            species_traits = self._process_species_traits()
            if species_traits:
                block.extend(species_traits)
        
        # Add item-granted modifiers
        item_modifiers = self._get_item_granted_modifiers()
        if item_modifiers:
            block.extend(["", "### Item-Granted Modifiers"])
            for modifier in item_modifiers:
                block.append(f"- {modifier}")
        
        # Concentration info is now integrated into the spell table
        
        # Add action economy reference
        action_economy = self.generate_action_economy_block()
        if action_economy:
            block.extend(action_economy)
        
        
        return block
    
    def _process_feature(self, feature: Dict[str, Any], passive_features: set) -> List[str]:
        """Process a single feature (feat or action) with enhanced source information."""
        feature_name = feature.get("name") or "Unknown Feature"
        
        # Determine source information
        source_info = self._get_feature_source_info(feature)
        
        # Enhanced header with source
        if source_info:
            feature_block = ["", f"### {feature_name} ({source_info})"]
        else:
            feature_block = ["", f"### {feature_name}"]
        
        # Check if feature should have consumable uses
        feature_name_lower = (feature.get("name") or "").lower()
        description_lower = (feature.get("description") or "").lower()
        
        # Special handling for Font of Magic features
        if "font of magic" in feature_name_lower:
            return self._process_font_of_magic_feature(feature_name, feature, source_info)
        
        has_uses = False
        uses_count = 1
        
        if feature_name_lower not in passive_features:
            # Check for usage patterns in description
            usage_patterns = [
                r"once.*long rest", r"once.*short rest", r"\d+.*per day", 
                r"regain.*on.*rest", r"spend.*spell slot", r"expend.*use",
                r"you can cast.*once", r"ability to cast.*way.*long rest"
            ]
            
            for pattern in usage_patterns:
                if re.search(pattern, description_lower):
                    has_uses = True
                    break
            
            # Try to extract specific number of uses (be more specific to avoid level requirements)
            uses_match = re.search(r"(\d+)\s*times.*per\s*day", description_lower)
            if not uses_match:
                uses_match = re.search(r"(\d+)\s*times.*per.*rest", description_lower)
            if not uses_match:
                # Check for proficiency bonus usage
                if re.search(r"equal to.*proficiency bonus", description_lower) or re.search(r"proficiency bonus.*per", description_lower):
                    uses_count = self.get_proficiency_bonus()
                    uses_match = True  # Set flag to indicate we found it
            if not uses_match:
                # Look for "X uses per rest" or "X per rest" but exclude if it follows "level"
                potential_matches = re.finditer(r"(\d+)(?:\s+uses?)?\s*per.*rest", description_lower)
                for match in potential_matches:
                    # Check if this number is part of a level requirement
                    preceding_text = description_lower[:match.start()].split()[-3:]
                    if not any("level" in word for word in preceding_text):
                        uses_match = match
                        break
            
            if uses_match:
                # Only extract group if uses_match is a match object, not a boolean
                if hasattr(uses_match, 'group'):
                    uses_count = int(uses_match.group(1))
        
        # Add consumable block if has uses
        if has_uses:
            state_key = self.get_safe_state_key(self.character_name, 
                                               feature_name.lower().replace(' ', '_').replace("'", '').replace('-', '_'))
            feature_block.extend([
                "```consumable",
                'label: ""',
                f"state_key: {state_key}",
                f"uses: {uses_count}",
                "```"
            ])
        
        # Format the description with better paragraph breaks and table formatting
        description = feature["description"]
        formatted_description = self._format_feature_description(description)
        feature_block.extend(formatted_description)
        return feature_block
    
    def _format_feature_description(self, description: str) -> List[str]:
        """Format feature descriptions with better paragraph breaks only."""
        # Keep it simple - just improve paragraph breaks and let the content drive itself
        return self._split_into_paragraphs(description)
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into well-formatted paragraphs."""
        lines = []
        
        # Clean up text and split by double newlines or major sentence breaks
        text = text.strip()
        
        # Split on major breaks
        paragraphs = re.split(r'\n\s*\n|(?<=\.)\s+(?=[A-Z])', text)
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Add spacing between paragraphs
            if lines:
                lines.append("")
            
            lines.append(paragraph)
        
        return lines
    
    def generate_spellcasting_section(self) -> List[str]:
        """Generate complete spellcasting section with multiple block IDs."""
        if not self.spells:
            return []
        
        all_blocks = []
        
        # Add spell-related stats first
        spell_save_dc = self.get_spell_save_dc()
        spellcasting_ability = self.get_primary_spellcasting_ability().title()
        
        # Calculate spell attack modifier
        spellcasting_ability_name = self.get_primary_spellcasting_ability()
        spellcasting_mod = self.ability_scores.get(spellcasting_ability_name, {}).get("modifier", 0)
        spell_attack_bonus = self.get_proficiency_bonus() + spellcasting_mod
        
        # Spellcasting stats in callout
        spell_stats_content = [
            "```stats",
            "items:",
            f"  - label: Spell Save DC",
            f"    value: {spell_save_dc}",
            f"  - label: Spell Attack Bonus",
            f"    value: '{self.format_modifier(spell_attack_bonus)}'",
            f"  - label: Spellcasting Ability",
            f"    value: '{spellcasting_ability}'",
            f"  - label: Spellcasting Modifier",
            f"    value: '{self.format_modifier(spellcasting_mod)}'",
            "",
            "grid:",
            "  columns: 4",
            "```"
        ]
        
        wrapped_spell_stats = self._wrap_in_callout(spell_stats_content, "spellstats")
        all_blocks.extend(["", "## Spellcasting", "", "<span class=\"right-link\">[[#Character Statistics|Top]]</span>"])
        all_blocks.extend(wrapped_spell_stats)
        
        # Add spell slots in callout
        spell_slots = self.generate_spell_slots_block()
        if spell_slots:
            # Remove header from spell slots and wrap in callout
            spell_slots_content = spell_slots[2:]  # Skip "", "### Spell Slots"
            wrapped_spell_slots = self._wrap_in_callout(spell_slots_content, "spellslots")
            all_blocks.extend(["", "### Spell Slots"])
            all_blocks.extend(wrapped_spell_slots)
        
        # Add spell table in callout
        spell_table = self.generate_spell_table_with_internal_links()
        if spell_table:
            # Remove header from spell table and wrap in callout
            spell_table_content = spell_table[2:]  # Skip "", "### Spell List"
            wrapped_spell_table = self._wrap_in_callout(spell_table_content, "spelltable")
            all_blocks.extend(["", "### Spell List"])
            all_blocks.extend(wrapped_spell_table)
        
        # Add spell dictionary in callout
        spell_dictionary = self.generate_spell_dictionary()
        if spell_dictionary:
            # Add header and wrap spell dictionary content in callout
            wrapped_spell_dictionary = self._wrap_in_callout(spell_dictionary, "spells")
            all_blocks.extend(["", "### Spell Details"])
            all_blocks.extend(wrapped_spell_dictionary)
        
        return all_blocks
    
    def generate_spell_table_with_internal_links(self) -> List[str]:
        """Generate spell table with internal document links."""
        # Collect all spells and sort by level then name
        all_spells = []
        for source, spell_list in self.spells.items():
            for spell in spell_list:
                all_spells.append(spell)
        
        # Sort by level (0 for cantrips), then by name
        all_spells.sort(key=lambda s: (s.get("level", 0), s.get("name", "")))
        
        if not all_spells:
            return []
        
        # Check if character has any preparation-based classes
        preparation_classes = ["wizard", "cleric", "druid", "paladin", "artificer"]
        has_preparation_class = any(
            cls.get("name", "").lower() in preparation_classes 
            for cls in self.classes
        )
        
        # Create spell table with internal heading links
        if has_preparation_class:
            block = [
                "",
                "### Spell List",
                "",
                "| Level | Spell | School | Components | Casting Time | Concentration | Prepared | Source |",
                "|-------|-------|--------|------------|--------------|---------------|----------|--------|"
            ]
        else:
            block = [
                "",
                "### Spell List",
                "",
                "| Level | Spell | School | Components | Casting Time | Concentration | Source |",
                "|-------|-------|--------|------------|--------------|---------------|--------|"
            ]
        
        for spell in all_spells:
            level = spell.get("level", 0)
            level_display = "Cantrip" if level == 0 else str(level)
            spell_name = spell['name']
            school = spell.get("school", "")
            
            spell_components = self.extract_spell_components(spell)
            components = spell_components.get("components", "—") if spell_components else "—"
            casting_time = spell_components.get("casting_time", "—") if spell_components else "—"
            
            # Check for concentration
            concentration = "Yes" if spell.get("concentration", False) else ""
            
            # Get source information
            source_info = spell.get("source_info", {})
            sources = spell.get("sources", [])
            
            # Format source display
            if source_info.get("feature") == "Feat Grant":
                # Look for Magic Initiate feat specifically
                feat_names = [feat.get("name", "") for feat in self.feats if "Magic Initiate" in feat.get("name", "")]
                if feat_names:
                    source_display = feat_names[0]
                else:
                    source_display = "Feat"
            elif source_info.get("feature") == "Racial Trait":
                species_name = self.species.get("name", "Species")
                source_display = f"{species_name} Heritage"
            elif source_info.get("feature") == "Background Spell":
                background_name = self.background.get("name", "Background")
                source_display = f"{background_name} Background"
            elif source_info.get("class") and source_info.get("class") != "Unknown Class":
                source_display = source_info.get("class")
            elif sources:
                source_display = sources[0]  # Use first source as fallback
            else:
                source_display = "Unknown"
            
            # Create internal heading links for spell descriptions below
            if has_preparation_class:
                # Check preparation status only for preparation-based classes
                always_prepared = spell.get("always_prepared", False)
                preparation_type = spell.get("preparation_type", "")
                is_prepared = spell.get("is_prepared", False)  # Raw preparation status from scraper
                effective_prepared = spell.get("effective_prepared", False)  # Includes ritual logic
                is_ritual = spell.get("ritual", False)
                
                if always_prepared:
                    prepared = "Always"
                elif level == 0:  # Cantrips
                    prepared = "Always"
                elif effective_prepared:  # Check effective preparation (includes rituals for wizards)
                    if is_ritual and not is_prepared:
                        prepared = "Ritual"  # Wizard ritual that's not prepared but can be cast
                    else:
                        prepared = "Yes"  # Actually prepared spell
                elif preparation_type == "prepared_from_book":
                    prepared = "No"  # Wizard spells that need to be prepared
                elif preparation_type in ["known", "always_known"]:
                    prepared = "Known"  # Non-wizard casters
                else:
                    prepared = "—"
                
                block.append(f"| {level_display} | [[#{spell_name}]] | {school} | {components} | {casting_time} | {concentration} | {prepared} | {source_display} |")
            else:
                # No preparation column for classes that don't use preparation
                block.append(f"| {level_display} | [[#{spell_name}]] | {school} | {components} | {casting_time} | {concentration} | {source_display} |")
        
        return block
    
    
    def generate_spell_dictionary(self) -> List[str]:
        """Generate spell dictionary with full descriptions."""
        # Collect all spells and sort by level then name
        all_spells = []
        for source, spell_list in self.spells.items():
            for spell in spell_list:
                all_spells.append(spell)
        
        # Sort by level (0 for cantrips), then by name
        all_spells.sort(key=lambda s: (s.get("level", 0), s.get("name", "")))
        
        if not all_spells:
            return []
        
        block = []
        
        # List all spells with full details
        for spell in all_spells:
            level = spell.get("level", 0)
            spell_name = spell['name']
            
            # Load enhanced spell data if available (parser only)
            enhanced_data = self.load_enhanced_spell_data(spell_name)
            
            # Use enhanced data to override API data where available
            if enhanced_data:
                level = enhanced_data.get("level", level)  # Override level from enhanced file
                school = enhanced_data.get("school", spell.get("school", "")).title()
                ritual = enhanced_data.get("ritual", spell.get("ritual", False))
            else:
                school = spell.get("school", "").title()  # Capitalize school name
                ritual = spell.get("ritual", False)
            
            level_text = "Cantrip" if level == 0 else f"Level {level}"
            
            # Add spell heading with proper capitalization
            block.extend([
                "",
                f"#### {spell_name}"
            ])
            
            # Add badges block for level, school, ritual, and data source
            # Show "F" if enhanced data was used to override level/school/ritual, otherwise use API source
            data_source = "F" if enhanced_data else spell.get("data_source", "A")
            
            # Create separate badges: Level, School, Ritual (if applicable), Blank, Source
            badges = [
                f"  - label: {level_text}",
                f"  - label: {school}"
            ]
            
            # Add ritual badge if it's a ritual spell
            if ritual:
                badges.append("  - label: Ritual")
            
            # Always add a blank badge for spacing before data source
            badges.append("  - label:")
            
            # Add data source badge
            badges.append(f"  - label: {data_source}")
            
            block.extend([
                "",
                "```badges",
                "items:"
            ] + badges + [
                "```"
            ])
            
            # Add spacing
            block.append("")
            
            # Extract spell components
            spell_components = self.extract_spell_components(spell)
            
            if spell_components:
                block.extend(["```spell-components"])
                for key, value in spell_components.items():
                    block.append(f"{key}: {value}")
                block.append("```")
            else:
                # Fallback for spells without component data
                block.extend([
                    "```spell-components",
                    "casting_time: Unknown",
                    "range: Unknown", 
                    "components: Unknown",
                    "```"
                ])
            
            # Add description - use enhanced description if available, otherwise API description
            description = enhanced_data.get("description") if enhanced_data else spell.get("description")
            if description:
                # Split multi-line descriptions into individual lines for proper callout formatting
                description_lines = description.split('\n')
                block.append("")  # Empty line before description
                block.extend(description_lines)
            
            # Add spacing between spells with BR
            block.extend(["", "<BR>", "", ""])
        
        return block
    
    
    def generate_proficiencies_block(self) -> List[str]:
        """Generate comprehensive proficiencies block."""
        if not self.proficiencies:
            return []
        
        block = ["", "## Proficiencies"]
        
        # Armor proficiencies
        armor_profs = self.proficiencies.get("armor", [])
        if armor_profs:
            block.extend(["", "### Armor"])
            for armor in armor_profs:
                source_info = self._get_proficiency_source_info(armor, "armor")
                if source_info:
                    block.append(f"- {armor} ({source_info})")
                else:
                    block.append(f"- {armor}")
        
        # Weapon proficiencies
        weapon_profs = self.proficiencies.get("weapons", [])
        if weapon_profs:
            block.extend(["", "### Weapons"])
            for weapon in weapon_profs:
                source_info = self._get_proficiency_source_info(weapon, "weapons")
                if source_info:
                    block.append(f"- {weapon} ({source_info})")
                else:
                    block.append(f"- {weapon}")
        
        # Tool proficiencies
        tool_profs = self.proficiencies.get("tools", [])
        if tool_profs:
            block.extend(["", "### Tools"])
            for tool in tool_profs:
                source_info = self._get_proficiency_source_info(tool, "tools")
                if source_info:
                    block.append(f"- {tool} ({source_info})")
                else:
                    block.append(f"- {tool}")
        
        # Languages
        languages = self.proficiencies.get("languages", [])
        if languages:
            block.extend(["", "### Languages"])
            for language in languages:
                source_info = self._get_proficiency_source_info(language, "languages")
                if source_info:
                    block.append(f"- {language} ({source_info})")
                else:
                    block.append(f"- {language}")
        
        # Add detailed ability score bonuses with source information
        ability_bonuses = self._get_ability_score_bonuses_with_sources()
        if ability_bonuses:
            block.extend(["", "### Ability Score Bonuses"])
            for bonus_info in ability_bonuses:
                block.append(f"- {bonus_info}")
        
        # Add resistances from species traits
        resistances = self._get_resistances_from_traits()
        if resistances:
            block.extend(["", "### Resistances"])
            for resistance in resistances:
                block.append(f"- {resistance}")
        
        return block
    
    def _get_ability_score_bonuses_with_sources(self) -> List[str]:
        """Get ability score bonuses with detailed source information."""
        bonuses = []
        
        # Create feat lookup by source ID
        feat_lookup = {}
        for feat in self.feats:
            source = feat.get("source", "")
            feat_lookup[source] = feat.get("name", "Unknown Feat")
        
        # Check each ability score for source breakdown
        for ability_name, ability_data in self.ability_scores.items():
            source_breakdown = ability_data.get("source_breakdown", {})
            total_score = ability_data.get("score", 0)
            
            # Build bonus description
            bonus_parts = []
            base_score = source_breakdown.get("base", 0)
            if base_score > 0:
                bonus_parts.append(f"Base {base_score}")
            
            # Add feat bonuses with feat names
            feat_bonus = source_breakdown.get("feat", 0)
            if feat_bonus > 0:
                feat_sources = []
                # Try to identify which feat(s) provided the bonus
                for feat in self.feats:
                    feat_source = feat.get("source", "")
                    feat_name = feat.get("name", "")
                    # Match feats that likely provide ability score improvements
                    if ("ability score" in feat_name.lower() or 
                        "improvement" in feat_name.lower() or
                        "sage" in feat_name.lower()):
                        # Avoid duplicating "Ability Scores" from background feat
                        if feat_name not in ["Ability Scores"]:
                            feat_sources.append(feat_name)
                
                if feat_sources:
                    # Remove duplicates while preserving order
                    seen = set()
                    unique_feats = []
                    for feat in feat_sources:
                        if feat not in seen:
                            seen.add(feat)
                            unique_feats.append(feat)
                    feat_source_text = ", ".join(unique_feats)
                    bonus_parts.append(f"Feat +{feat_bonus} ({feat_source_text})")
                else:
                    bonus_parts.append(f"Feat +{feat_bonus}")
            
            # Add other source types if they exist
            for source_type, value in source_breakdown.items():
                if source_type not in ["base", "feat"] and value > 0:
                    bonus_parts.append(f"{source_type.title()} +{value}")
            
            if len(bonus_parts) > 1:  # Only show if there are bonuses beyond base
                ability_title = ability_name.title()
                bonus_description = " + ".join(bonus_parts)
                bonuses.append(f"**{ability_title}** {total_score} ({bonus_description})")
        
        # Also add any species trait bonuses
        if self.species and self.species.get("traits"):
            for trait in self.species["traits"]:
                trait_name = trait.get("name", "")
                trait_description = trait.get("description", "")
                
                if trait_name == "Bonus":
                    if ":" in trait_description:
                        bonus_info = trait_description.split(":", 1)[1].strip()
                        bonuses.append(f"**Species Trait:** {bonus_info}")
                    else:
                        bonuses.append(f"**Species Trait:** {trait_description}")
        
        return bonuses
    
    def _get_resistances_from_traits(self) -> List[str]:
        """Get resistances from species traits."""
        resistances = []
        
        if self.species and self.species.get("traits"):
            for trait in self.species["traits"]:
                trait_name = trait.get("name", "")
                trait_description = trait.get("description", "")
                
                if trait_name == "Resistance":
                    resistances.append(trait_description)
        
        return resistances
    
    def _get_proficiency_source_info(self, proficiency_name: str, proficiency_type: str) -> str:
        """Get source information for a specific proficiency."""
        sources = []
        
        # Check background for proficiency sources
        if self.background:
            background_name = self.background.get("name", "")
            if background_name:
                # Common background proficiencies
                if proficiency_type == "languages":
                    if proficiency_name == "Draconic" and "sage" in background_name.lower():
                        sources.append("Background: Sage")
                    elif proficiency_name == "Common":
                        sources.append("Species")
                elif proficiency_type == "tools":
                    if "supplies" in proficiency_name.lower() and "sage" in background_name.lower():
                        sources.append("Background: Sage")
        
        # Check class for proficiency sources
        for class_info in self.classes:
            class_name = class_info.get("name", "")
            if class_name:
                if proficiency_type == "weapons":
                    if class_name.lower() == "wizard" and proficiency_name == "Simple Weapons":
                        sources.append(f"Class: {class_name}")
        
        # Check species for proficiency sources
        if self.species:
            species_name = self.species.get("name", "")
            if species_name and proficiency_type == "languages":
                if proficiency_name == "Common":
                    sources.append("Species")
                elif "dragonborn" in species_name.lower() and proficiency_name == "Draconic":
                    sources.append(f"Species: {species_name}")
        
        # Check feats for proficiency sources
        for feat in self.feats:
            feat_name = feat.get("name", "")
            if "magic initiate" in feat_name.lower() and proficiency_type == "languages":
                # Magic Initiate might grant language proficiencies
                continue
        
        if sources:
            # Remove duplicates while preserving order
            seen = set()
            unique_sources = []
            for source in sources:
                if source not in seen:
                    seen.add(source)
                    unique_sources.append(source)
            return ", ".join(unique_sources)
        return ""
    
    def generate_appearance_block(self) -> List[str]:
        """Generate character appearance section with consistent fields."""
        # Always create appearance section with standard fields
        block = ["", "## Appearance", ""]
        
        # Standard appearance fields - show all, leave blank if no data
        def get_appearance_value(key, default=''):
            if not self.appearance:
                return default
            value = self.appearance.get(key, default)
            return value if value is not None else default
        
        appearance_items = [
            f"**Gender:** {get_appearance_value('gender')}",
            f"**Age:** {get_appearance_value('age')}",
            f"**Height:** {get_appearance_value('height')}",
            f"**Weight:** {get_appearance_value('weight')}{' lbs' if get_appearance_value('weight') else ''}",
            f"**Hair:** {get_appearance_value('hair')}",
            f"**Eyes:** {get_appearance_value('eyes')}",
            f"**Skin:** {get_appearance_value('skin')}",
            f"**Size:** {get_appearance_value('size_name', 'Medium')}"
        ]
        
        block.extend(appearance_items)
            
        # Appearance traits/description if available
        if self.appearance:
            has_physical_traits = (self.appearance.get("traits") or "").strip()
            if has_physical_traits:
                block.extend(["", "### Physical Description", ""])
                # Split multi-line descriptions properly
                block.extend(has_physical_traits.split('\n'))
            
        return block
    
    def generate_lifestyle_info(self) -> List[str]:
        """Generate lifestyle information if available."""
        lifestyle_id = self.basic_info.get("lifestyleId")
        
        if lifestyle_id is None:
            return []
        
        # Map lifestyle IDs to names (based on D&D 5e lifestyles + D&D Beyond extensions)
        lifestyle_names = {
            0: "Wretched", 1: "Squalid", 2: "Poor", 3: "Modest", 
            4: "Comfortable", 5: "Wealthy", 6: "Aristocratic", 7: "Aristocratic", 8: "Aristocratic"
        }
        
        lifestyle_name = lifestyle_names.get(lifestyle_id, f"Unknown (ID: {lifestyle_id})")
        return [f"**Lifestyle:** {lifestyle_name}"]
    
    def _get_base_trait_type(self, trait_name: str) -> str:
        """Determine the base trait type for grouping similar traits."""
        trait_name_lower = trait_name.lower()
        
        # Define patterns for grouping similar traits
        trait_patterns = {
            'Proficiencies': ['proficiency', 'proficiencies'],
            'Skills': ['skill', 'skills'],
            'Sets': ['set', 'sets'],
            'Breath Weapon': ['breath weapon', 'breath'],
            'Resistance': ['resistance', 'resistances', 'damage resistance'],
            'Immunity': ['immunity', 'immunities', 'damage immunity'],
            'Senses': ['sense', 'senses', 'darkvision', 'blindsight', 'tremorsense'],
            'Movement': ['speed', 'movement', 'fly', 'swim', 'climb'],
            'Spellcasting': ['spellcasting', 'cantrip', 'spell', 'magic'],
            'Ancestry': ['ancestry', 'heritage', 'lineage'],
            'Languages': ['language', 'languages'],
        }
        
        # Check for pattern matches
        for base_type, patterns in trait_patterns.items():
            for pattern in patterns:
                if pattern in trait_name_lower:
                    return base_type
        
        # If no pattern matches, return the original trait name
        return trait_name
    
    def generate_racial_traits_block(self) -> List[str]:
        """Generate racial traits section, excluding Language/Bonus/Resistance (handled in Proficiencies)."""
        block = []
        
        if not self.species or not self.species.get("traits"):
            return block
            
        block.extend(["", "## Racial Traits"])
        
        # Group traits by their base type to avoid duplicate headers
        trait_groups = {}
        
        # Filter out traits that are better handled in Proficiencies section
        for trait in self.species["traits"]:
            trait_name = trait.get("name", "Unknown Trait")
            trait_description = trait.get("description", "")
            
            # Skip Language, Bonus, and Resistance traits (handled in Proficiencies)
            if trait_name in ["Language", "Bonus", "Resistance"]:
                continue
            
            # Determine the base trait type for grouping
            base_trait_type = self._get_base_trait_type(trait_name)
            
            # Group traits with the same base type
            if base_trait_type not in trait_groups:
                trait_groups[base_trait_type] = []
            
            trait_groups[base_trait_type].append({
                'name': trait_name,
                'description': trait_description
            })
        
        # Generate sections for each trait group
        for base_type, traits in trait_groups.items():
            if len(traits) == 1:
                # Single trait - use its specific name
                trait = traits[0]
                description = trait.get('description', '').strip()
                if description:
                    block.extend(["", f"### {trait['name']}", "", description])
                else:
                    block.extend(["", f"### {trait['name']}"])
            else:
                # Multiple traits of same type - group under base type header
                block.extend(["", f"### {base_type}"])
                for trait in traits:
                    description = trait.get('description', '').strip()
                    if trait['name'] != base_type:  # Avoid redundant subheading if name matches base type
                        if description:
                            block.extend(["", f"**{trait['name']}**", "", description])
                        else:
                            block.extend(["", f"**{trait['name']}**"])
                    else:
                        if description:
                            block.extend(["", description])
                    
                    # Add spacing between multiple traits except for the last one
                    if trait != traits[-1] and description:
                        block.append("")
                
        return block

    def generate_background_species_block(self) -> List[str]:
        """Generate enhanced background and species information."""
        block = []
        
        # Background section with enhanced details
        if self.background.get("name") and self.background["name"] != "Unknown":
            block.extend(["", "## Background", "", f"### {self.background['name']}"])
            if self.background.get("description"):
                # Parse and format the background description
                formatted_description = self._format_background_description(self.background["description"])
                block.extend(formatted_description)
                
            # Add enhanced background details
            background_details = []
            if self.background.get("personal_possessions"):
                background_details.extend(["", "### Personal Possessions", "", self.background["personal_possessions"]])
            if self.background.get("organizations"):
                background_details.extend(["", "### Organizations", "", self.background["organizations"]])
            if self.background.get("enemies"):
                background_details.extend(["", "### Enemies", "", self.background["enemies"]])
            if self.background.get("ideals"):
                background_details.extend(["", "### Ideals", "", self.background["ideals"]])
            if self.background.get("bonds"):
                background_details.extend(["", "### Bonds", "", self.background["bonds"]])
            if self.background.get("flaws"):
                background_details.extend(["", "### Flaws", "", self.background["flaws"]])
            if self.background.get("personality_traits"):
                background_details.extend(["", "### Personality Traits", "", self.background["personality_traits"]])
            if self.background.get("other_holdings"):
                background_details.extend(["", "### Other Holdings", "", self.background["other_holdings"]])
            
            # Add lifestyle information if available
            lifestyle_info = self.generate_lifestyle_info()
            if lifestyle_info:
                background_details.extend(["", "### Lifestyle", ""] + lifestyle_info)
                
            block.extend(background_details)
        
        # Species information is already covered in the infobox and racial traits
        # No need for a separate Species section
        
        return block
    
    def generate_attacks_block(self) -> List[str]:
        """Generate attacks block from weapon inventory and actions."""
        block = ["", "## Attacks", "", "<span class=\"right-link\">[[#Character Statistics|Top]]</span>"]
        
        # Get equipped weapons from inventory
        def is_weapon(item):
            item_type = (item.get("type") or "").lower()
            item_name = (item.get("name") or "").lower()
            
            # Common D&D weapon types
            weapon_types = [
                "crossbow", "dagger", "quarterstaff", "handaxe", "shortsword", "longsword",
                "warhammer", "mace", "club", "javelin", "spear", "bow", "sword", "axe",
                "scimitar", "rapier", "trident", "glaive", "halberd", "pike", "whip"
            ]
            
            # Check if type contains any weapon keywords
            for weapon_type in weapon_types:
                if weapon_type in item_type or weapon_type in item_name:
                    return True
            
            return False
        
        weapons = [item for item in self.inventory if item.get("equipped", False) and is_weapon(item)]
        
        if weapons:
            # Add all weapons in a callout block for proper embedding
            block.extend(["", ">"])
            for i, weapon in enumerate(weapons):
                    weapon_name = weapon.get("name", "Unknown Weapon")
                    
                    # Add weapon header
                    if i > 0:
                        block.append("> ")  # Empty line between weapons
                    block.append(f"> ### {weapon_name}")
                    
                    # Basic weapon info
                    weapon_type = weapon.get("type", "Weapon")
                    if weapon_type:
                        block.append(f"> **Type:** {weapon_type}")
                    
                    # Calculate attack bonus (simplified)
                    str_mod = self.ability_scores.get("strength", {}).get("modifier", 0)
                    dex_mod = self.ability_scores.get("dexterity", {}).get("modifier", 0)
                    prof_bonus = self.get_proficiency_bonus()
                    
                    # Use DEX for finesse/ranged weapons, STR for others
                    weapon_lower = weapon_name.lower()
                    is_finesse_or_ranged = any(keyword in weapon_lower for keyword in 
                                             ["crossbow", "dagger", "bow", "sling", "dart", "rapier", "scimitar", "shortsword"])
                    
                    if is_finesse_or_ranged:
                        attack_mod = dex_mod + prof_bonus
                        damage_mod = dex_mod
                    else:
                        attack_mod = str_mod + prof_bonus
                        damage_mod = str_mod
                    
                    block.append(f"> **Attack Bonus:** {self.format_modifier(attack_mod)}")
                    
                    # Add damage information
                    damage_die, damage_type = self.get_weapon_damage(weapon_name)
                    if damage_die:
                        total_damage = f"{damage_die} + {damage_mod}" if damage_mod != 0 else damage_die
                        block.append(f"> **Damage:** {total_damage} {damage_type}")
                    
                    if weapon.get("weight"):
                        block.append(f"> **Weight:** {weapon['weight']} lbs")
            
            # Add the block ID inside the callout
            block.extend(["> ", "> ^attacks"])
        
        return block
    
    def get_weapon_damage(self, weapon_name: str) -> Tuple[str, str]:
        """Get weapon damage die and type based on weapon name."""
        weapon_lower = weapon_name.lower()
        
        # Common D&D weapon damage mapping
        weapon_damages = {
            "crossbow": ("1d8", "piercing"),
            "light crossbow": ("1d8", "piercing"),
            "heavy crossbow": ("1d10", "piercing"),
            "dagger": ("1d4", "piercing"),
            "quarterstaff": ("1d6", "bludgeoning"),  # versatile: 1d8 two-handed
            "handaxe": ("1d6", "slashing"),
            "shortsword": ("1d6", "piercing"),
            "longsword": ("1d8", "slashing"),  # versatile: 1d10 two-handed
            "rapier": ("1d8", "piercing"),
            "scimitar": ("1d6", "slashing"),
            "mace": ("1d6", "bludgeoning"),
            "club": ("1d4", "bludgeoning"),
            "javelin": ("1d6", "piercing"),
            "spear": ("1d6", "piercing"),  # versatile: 1d8 two-handed
            "shortbow": ("1d6", "piercing"),
            "longbow": ("1d8", "piercing"),
            "warhammer": ("1d8", "bludgeoning"),  # versatile: 1d10 two-handed
        }
        
        # Check for weapon type matches
        for weapon_type, (damage_die, damage_type) in weapon_damages.items():
            if weapon_type in weapon_lower:
                return damage_die, damage_type
        
        # Default fallback
        return "1d6", "bludgeoning"
    
    def get_armor_class_from_inventory(self) -> int:
        """Calculate AC based on equipped armor and dexterity."""
        base_ac = 10
        dex_mod = self.ability_scores.get("dexterity", {}).get("modifier", 0)
        
        # Look for equipped armor
        for item in self.inventory:
            if item.get("equipped", False):
                item_name = item.get("name", "").lower()
                if "scale mail" in item_name:
                    # Scale mail: 14 + Dex modifier (max 2)
                    return 14 + min(dex_mod, 2)
                elif "leather" in item_name:
                    # Leather armor: 11 + Dex modifier
                    return 11 + dex_mod
                elif "studded leather" in item_name:
                    # Studded leather: 12 + Dex modifier
                    return 12 + dex_mod
                elif "chain mail" in item_name:
                    # Chain mail: 16 (no dex bonus)
                    return 16
                elif "chain shirt" in item_name:
                    # Chain shirt: 13 + Dex modifier (max 2)
                    return 13 + min(dex_mod, 2)
        
        # No armor found, return unarmored AC
        return base_ac + dex_mod
    
    def generate_inventory_block(self) -> List[str]:
        """Generate inventory block."""
        if not self.inventory:
            return []
        
        block = ["", "## Inventory"]
        
        # Add wealth and encumbrance at the start
        wealth_encumbrance = self.generate_wealth_encumbrance_block()
        if wealth_encumbrance:
            # Remove the header since we're integrating it
            wealth_content = [line for line in wealth_encumbrance if not line.startswith("### Wealth")]
            block.extend(wealth_content)
            block.append("")  # Add spacing before items
        
        for item in self.inventory:
            item_name = item.get("name", "Unknown")
            if item_name == "Unknown":
                continue
            
            block.extend([
                "",
                f"### {item_name}",
                f"**Type:** {item.get('type', 'Unknown')}",
                f"**Quantity:** {item.get('quantity', 1)}",
                f"**Equipped:** {'Yes' if item.get('equipped', False) else 'No'}"
            ])
            
            if item.get("weight"):
                block.append(f"**Weight:** {item['weight']} lbs")
            
            if item.get("rarity") and item["rarity"] != "Common":
                block.append(f"**Rarity:** {item['rarity']}")
            
            if item.get("attuned"):
                block.append(f"**Attuned:** Yes")
        
        return block
    
    def generate_character_notes_block(self) -> List[str]:
        """Generate character notes, backstory, and personality traits."""
        notes = self.data.get("notes", {}) or {}
        block = []
        
        # Backstory
        backstory = (notes.get("backstory") or "").strip()
        if backstory:
            # Split multi-line backstory into individual lines for proper callout formatting
            backstory_lines = backstory.split('\n')
            block.extend([
                "## Backstory",
                ""
            ])
            block.extend(backstory_lines)
            block.append("")
        
        # Character notes
        character_notes = (notes.get("character_notes") or "").strip()
        if character_notes:
            # Split multi-line notes into individual lines for proper callout formatting
            notes_lines = character_notes.split('\n')
            block.extend([
                "### Character Notes",
                ""
            ])
            block.extend(notes_lines)
            block.append("")
        
        # Allies & Contacts
        allies = (notes.get("allies") or "").strip()
        if allies:
            # Split multi-line allies content into individual lines for proper callout formatting
            allies_lines = allies.split('\n')
            block.extend([
                "### Allies & Contacts",
                ""
            ])
            block.extend(allies_lines)
            block.append("")
        
        # Personality traits section
        personality_traits = []
        trait_sections = {
            "Personal Traits": notes.get("personal_traits"),
            "Ideals": notes.get("ideals"), 
            "Bonds": notes.get("bonds"),
            "Flaws": notes.get("flaws")
        }
        
        for section_name, content in trait_sections.items():
            if content and content.strip():
                # Split multi-line trait content into individual lines for proper callout formatting
                content_lines = content.strip().split('\n')
                personality_traits.extend([
                    f"### {section_name}",
                    ""
                ])
                personality_traits.extend(content_lines)
                personality_traits.append("")
        
        if personality_traits:
            block.extend(["### Personality"] + personality_traits)
        
        return block
    
    def generate_markdown(self) -> str:
        """Generate complete markdown document."""
        # Configuration - parameterized script locations
        PYTHON_SCRIPT_PATH = "C:/Users/alc_u/Documents/DnD/CharacterScraper/dnd_json_to_markdown.py"
        
        all_blocks = []
        
        # Frontmatter
        all_blocks.extend(self.generate_frontmatter())
        all_blocks.append("")
        
        # Execute Code plugin refresh button
        character_id = self.meta.get("character_id", "")
        if character_id:
            # Get just the filename for the output
            import os
            script_filename = os.path.basename(PYTHON_SCRIPT_PATH)
            script_dir = os.path.dirname(PYTHON_SCRIPT_PATH)
            
            all_blocks.extend([
                "```run-python",
                "import os, sys, subprocess",
                f"os.chdir(r'{script_dir}')",
                "vault_path = @vault_path",
                "note_path = @note_path", 
                "full_path = os.path.join(vault_path, note_path)",
                f"cmd = ['python', 'dnd_json_to_markdown.py', '{character_id}', full_path]",
                "result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')",
                "print('\\n\\n')",  # Push output below visible area
                "print('SUCCESS: Character refreshed!' if result.returncode == 0 else f'ERROR: {result.stderr}')",
                "print('Reload file to see changes.' if result.returncode == 0 else '')",
                "```",
                "",
                "",
                "---",
                ""
            ])
        
        # Character infobox
        avatar_url = self.basic_info.get("avatarUrl") or self.data.get("avatarUrl")
        clean_avatar_url = avatar_url.split('?')[0] if avatar_url else ""
        
        # Get key character info for infobox
        primary_class = self.classes[0] if self.classes else {}
        class_name = primary_class.get("name", "Unknown")
        subclass_name = primary_class.get("subclass", "")
        
        # Try multiple paths for species/race name
        species_name = "Unknown"
        
        # Check for species data (enhanced scraper processes race into species field)
        species_data = self.data.get("species", {})
        if species_data.get("name"):
            species_name = species_data["name"]
            
        # Determine if 2024 rules for proper terminology
        is_2024_rules = False
        if self.classes:
            is_2024_rules = self.classes[0].get("is_2024", False)
        
        # Use appropriate terminology
        species_label = "Species" if is_2024_rules else "Race"
            
        background_name = self.data.get("background", {}).get("name", "Unknown")
        hp_info = self.basic_info.get("hit_points", {})
        current_hp = hp_info.get("current", 1)
        max_hp = hp_info.get("maximum", 1)
        
        infobox_lines = [
            "> [!infobox]+",
            f"> # {self.character_name}",
        ]
        
        if clean_avatar_url:
            infobox_lines.append(f"> ![Character Avatar|200]({clean_avatar_url})")
        
        infobox_lines.extend([
            "> ###### Character Details",
            "> |  |  |",
            "> | --- | --- |",
            f"> | **Class** | {class_name} |",
        ])
        
        if subclass_name:
            infobox_lines.append(f"> | **Subclass** | {subclass_name} |")
            
        # Get HP calculation method
        hp_info = self.basic_info.get("hit_points", {})
        hp_method = hp_info.get("hit_point_method", "Unknown")
        
        infobox_lines.extend([
            f"> | **{species_label}** | {species_name} |",
            f"> | **Background** | {background_name} |",
            f"> | **Level** | {self.level} |",
            f"> | **Hit Points** | {current_hp}/{max_hp} |",
            f"> | **HP Calc** | {hp_method} |",
            f"> | **Armor Class** | {self.get_armor_class()} |",
            f"> | **Proficiency** | +{self.get_proficiency_bonus()} |",
            "> ",
            "> ###### Ability Scores",
            "> |  |  |  |",
            "> | --- | --- | --- |",
        ])
        
        # Add ability scores in a compact format
        abilities = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        for i in range(0, len(abilities), 3):
            row_abilities = abilities[i:i+3]
            score_parts = []
            for ability in row_abilities:
                score = self.ability_scores.get(ability, {}).get("score", 10)
                modifier = self.ability_scores.get(ability, {}).get("modifier", 0)
                mod_str = f"+{modifier}" if modifier >= 0 else str(modifier)
                score_parts.append(f"**{ability.title()[:3]}** {score} ({mod_str})")
            
            while len(score_parts) < 3:
                score_parts.append("")
            
            infobox_lines.append(f"> | {score_parts[0]} | {score_parts[1]} | {score_parts[2]} |")
        
        # Add block ID to infobox (open by default)
        infobox_lines[0] = "> [!infobox]+ ^character-info"
        all_blocks.extend(infobox_lines)
        all_blocks.append("")
        
        # Quick Links section - use header text (anchors will be at end of sections)
        quick_links = [
            "## Quick Links",
            "",
            "| Section |",
            "| --- |",
            "| [[#Character Statistics]] |",
            "| [[#Abilities & Skills]] |",
            "| [[#Appearance]] |",
            "| [[#Spellcasting]] |",
            "| [[#Features]] |",
            "| [[#Racial Traits]] |",
            "| [[#Attacks]] |",
            "| [[#Proficiencies]] |",
            "| [[#Background]] |",
            "| [[#Backstory]] |",
            "| [[#Inventory]] |",
            "| &nbsp; |",
            f"| [D&D Beyond](https://www.dndbeyond.com/characters/{character_id}) |",
            "",
            "---",
            ""
        ]
        all_blocks.extend(quick_links)
        
        # Character Statistics section 
        all_blocks.extend(["## Character Statistics", ""])
        
        # Get character details for the stats
        primary_class = self.classes[0] if self.classes else {}
        class_name = primary_class.get("name", "Unknown")
        subclass_name = primary_class.get("subclass", "")
        
        # Generate character statistics
        combat_stats = [
            "```stats",
            "items:",
            f"  - label: Level",
            f"    value: '{self.level}'",
            f"  - label: Class", 
            f"    value: '{class_name}'",
        ]
        
        # Add subclass (always show, even if empty)
        combat_stats.extend([
            f"  - label: Subclass",
            f"    value: '{subclass_name if subclass_name else 'None'}'"
        ])
        
        # Add combat stats with passive senses
        ac_sublabel = self.get_ac_sublabel()
        combat_stats.extend([
            f"  - label: Initiative",
            f"    value: '{self.format_modifier(self.get_initiative_modifier())}'",
            f"  - label: Speed", 
            f"    value: '30 ft'",
            f"  - label: Armor Class",
            f"    sublabel: {ac_sublabel}",
            f"    value: {self.get_armor_class()}",
        ])
        
        # Passive senses moved to Abilities & Skills section as badges
            
        combat_stats.extend([
            "",
            "grid:",
            "  columns: 3",
            "```"
        ])
        all_blocks.extend(combat_stats)
        
        # Health section 
        all_blocks.extend(["", "<BR>", ""])
        all_blocks.extend(self.generate_health_block())
        
        # Inspiration removed - not useful as a consumable in this format
            
        all_blocks.extend(["", "^character-statistics", "", "---", ""])
        
        # Character Stats Section - abilities and skills grouped together  
        all_blocks.extend(["## Abilities & Skills", ""])
        
        # Abilities section (content only, no header)
        ability_content = self.generate_ability_block()
        # Skip the header lines and add content
        all_blocks.extend(ability_content[2:])  # Skip "## Abilities ^abilities" and empty line
        
        # Add passive scores as badges
        all_blocks.extend(["", "<BR>", ""])
        all_blocks.extend(self.generate_passive_badges())
        
        # Skills section (content only, no header) with line break
        all_blocks.extend(["", "<BR>", ""])
        skills_content = self.generate_skills_block()
        # Skip the header lines and add content  
        all_blocks.extend(skills_content[2:])  # Skip "## Skills ^skills" and empty line
        
        # Add proficiency sources block
        proficiency_sources_content = self.generate_proficiency_sources_block()
        if proficiency_sources_content:
            all_blocks.extend(proficiency_sources_content)
        
        all_blocks.extend(["", "^abilities-skills", "", "---", ""])  # Block ID at end of section
        
        # Appearance section
        appearance_content = self.generate_appearance_block()
        if appearance_content:
            # Remove the header and wrap content in callout
            content_without_header = appearance_content[3:]  # Skip "", "## Appearance", ""
            wrapped_appearance = self._wrap_in_callout(content_without_header, "appearance")
            all_blocks.extend(["", "## Appearance", "", "<span class=\"right-link\">[[#Character Statistics|Top]]</span>"])
            all_blocks.extend(wrapped_appearance)
        all_blocks.extend(["", "---", ""])  # Divider
        
        
        # Spellcasting section (complete with stats, slots, table, and descriptions)
        spellcasting_content = self.generate_spellcasting_section()
        if spellcasting_content:
            all_blocks.extend(spellcasting_content)
            all_blocks.extend(["", "^spellcasting"])  # Overall spellcasting block ID
        all_blocks.extend(["", "---", ""])  # Divider
        
        # Features section
        features_content = self.generate_features_block()
        if features_content:
            # Remove the header and wrap content in callout
            content_without_header = features_content[1:]  # Skip "## Features"
            wrapped_features = self._wrap_in_callout(content_without_header, "features")
            all_blocks.extend(["", "## Features", "", "<span class=\"right-link\">[[#Character Statistics|Top]]</span>"])
            all_blocks.extend(wrapped_features)
        all_blocks.extend(["", "---", ""])  # Divider
        
        # Racial Traits section
        racial_traits_content = self.generate_racial_traits_block()
        if racial_traits_content:
            # Remove the header and wrap content in callout
            content_without_header = racial_traits_content[2:]  # Skip "", "## Racial Traits"
            wrapped_racial_traits = self._wrap_in_callout(content_without_header, "racial-traits")
            all_blocks.extend(["", "## Racial Traits", "", "<span class=\"right-link\">[[#Character Statistics|Top]]</span>"])
            all_blocks.extend(wrapped_racial_traits)
        all_blocks.extend(["", "---", ""])  # Divider
        
        # Attacks section
        all_blocks.extend(self.generate_attacks_block())
        all_blocks.extend(["", "---", ""])  # No external anchor needed - it's in the callout
        
        # Proficiencies section
        proficiencies_content = self.generate_proficiencies_block()
        if proficiencies_content:
            # Remove the header and wrap content in callout
            content_without_header = proficiencies_content[2:]  # Skip "", "## Proficiencies"
            wrapped_proficiencies = self._wrap_in_callout(content_without_header, "proficiencies")
            all_blocks.extend(["", "## Proficiencies", "", "<span class=\"right-link\">[[#Character Statistics|Top]]</span>"])
            all_blocks.extend(wrapped_proficiencies)
        all_blocks.extend(["", "---", ""])  # Divider
        
        # Background section
        background_blocks = self.generate_background_species_block()
        if background_blocks:
            # Remove the header and wrap content in callout
            content_without_header = background_blocks[2:]  # Skip "", "## Background"
            wrapped_background = self._wrap_in_callout(content_without_header, "background")
            all_blocks.extend(["", "## Background", "", "<span class=\"right-link\">[[#Character Statistics|Top]]</span>"])
            all_blocks.extend(wrapped_background)
        all_blocks.extend(["", "---", ""])  # Divider
        
        # Character notes section (before inventory)
        notes_blocks = self.generate_character_notes_block()
        if notes_blocks:
            # Remove the header and wrap content in callout
            content_without_header = notes_blocks[1:]  # Skip "## Backstory"
            wrapped_notes = self._wrap_in_callout(content_without_header, "backstory")
            all_blocks.extend(["", "## Backstory", "", "<span class=\"right-link\">[[#Character Statistics|Top]]</span>"])
            all_blocks.extend(wrapped_notes)
        all_blocks.extend(["", "---", ""])  # Divider
        
        # Inventory section (moved to last)
        inventory_content = self.generate_inventory_block()
        if inventory_content:
            # Remove the header and wrap content in callout
            content_without_header = inventory_content[2:]  # Skip "", "## Inventory"
            wrapped_inventory = self._wrap_in_callout(content_without_header, "inventory")
            all_blocks.extend(["", "## Inventory", "", "<span class=\"right-link\">[[#Character Statistics|Top]]</span>"])
            all_blocks.extend(wrapped_inventory)
        
        return "\n".join(all_blocks)


def run_scraper(character_id: str, session_cookie: Optional[str] = None, 
                script_path: Optional[Path] = None) -> Dict[str, Any]:
    """Run the enhanced DnD scraper and return parsed JSON."""
    if script_path is None:
        script_path = Path(__file__).parent / "enhanced_dnd_scraper.py"
    
    if not script_path.exists():
        raise FileNotFoundError(f"Scraper script not found: {script_path}")
    
    # Build command
    cmd = [sys.executable, str(script_path), character_id, "--output", "temp_character.json"]
    if session_cookie:
        cmd.extend(["--session", session_cookie])
    
    # Note: Scraper always uses API only, parser handles enhanced spell files
    
    # Add verbose flag if enabled
    if VERBOSE_OUTPUT:
        cmd.append("--verbose")
    
    logger.info(f"Running scraper for character ID: {character_id}")
    
    try:
        # Run the scraper
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Scraper completed successfully")
        
        # Read the output file with proper resource management
        output_file = Path("temp_character.json")
        try:
            if not output_file.exists():
                raise FileNotFoundError("Scraper did not create output file")
            
            with open(output_file, 'r', encoding='utf-8') as f:
                character_data = json.load(f)
            
            return character_data
        finally:
            # Ensure temp file is always cleaned up
            if output_file.exists():
                output_file.unlink()
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Scraper failed: {e}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Error running scraper: {e}")
        raise


# Mojibake fix function removed - no longer needed with proper UTF-8 handling


def main():
    """Main entry point."""
    global USE_ENHANCED_SPELL_DATA, SPELLS_FOLDER_PATH, VERBOSE_OUTPUT, ENHANCED_SCRAPER_PATH
    
    parser = argparse.ArgumentParser(
        description="Convert DnD Beyond character to Obsidian markdown with DnD UI Toolkit format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dnd_json_to_markdown.py 145081718 "Character Sheet.md"
  python dnd_json_to_markdown.py 145081718 "/path/to/Ilarion Veles.md" --session "your_session"
  python dnd_json_to_markdown.py 145081718 "sheet.md" --scraper-path "./custom_scraper.py"
  python dnd_json_to_markdown.py 145081718 "sheet.md" --spells-path "./spells"
  python dnd_json_to_markdown.py 145081718 "sheet.md" --verbose
  python dnd_json_to_markdown.py 145081718 "sheet.md" --no-enhance-spells

Spell Enhancement:
  Enhanced spell data is ENABLED BY DEFAULT using local spell markdown files.
  Use --no-enhance-spells to disable enhanced spells and use API data only.
  Requires a spells folder with spell files in the format "spell-name-xphb.md".

This script converts enhanced_dnd_scraper.py JSON output to D&D UI Toolkit markdown format.
        """
    )
    
    parser.add_argument(
        "character_id",
        help="D&D Beyond character ID"
    )
    
    parser.add_argument(
        "output_path",
        help="Output markdown file path"
    )
    
    parser.add_argument(
        "--session",
        help="D&D Beyond session cookie for private characters"
    )
    
    parser.add_argument(
        "--scraper-path",
        type=Path,
        default=Path(ENHANCED_SCRAPER_PATH),
        help=f"Path to enhanced_dnd_scraper.py (default: {ENHANCED_SCRAPER_PATH})"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--no-enhance-spells",
        action="store_true",
        help="Disable enhanced spell data, use API only (default: False - enhanced spells enabled by default)"
    )
    
    parser.add_argument(
        "--spells-path",
        default=SPELLS_FOLDER_PATH,
        help=f"Path to spells folder (default: {SPELLS_FOLDER_PATH})"
    )
    
    
    # Mojibake fix argument removed - no longer needed
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Configure spell enhancement
    USE_ENHANCED_SPELL_DATA = not args.no_enhance_spells  # Enhanced spells enabled by default
    SPELLS_FOLDER_PATH = args.spells_path
    VERBOSE_OUTPUT = args.verbose
    
    if USE_ENHANCED_SPELL_DATA:
        logger.info(f"Enhanced spell data enabled, using folder: {SPELLS_FOLDER_PATH}")
        if not os.path.exists(SPELLS_FOLDER_PATH):
            logger.warning(f"Spells folder not found: {SPELLS_FOLDER_PATH}")
            logger.warning("Falling back to D&D Beyond spell data only")
            USE_ENHANCED_SPELL_DATA = False
    
    try:
        # Run the scraper
        character_data = run_scraper(
            args.character_id, 
            args.session, 
            args.scraper_path
        )
        
        # Generate markdown
        generator = CharacterMarkdownGenerator(character_data)
        markdown_content = generator.generate_markdown()
        
        # Write output file
        output_path = Path(args.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Mojibake fix removed - no longer needed with proper UTF-8 handling
        
        character_name = character_data.get("basic_info", {}).get("name", "Unknown")
        logger.info(f"DnD UI Toolkit formatted character sheet for {character_name} written to {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to process character: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()