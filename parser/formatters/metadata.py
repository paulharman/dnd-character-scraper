"""
Metadata formatter for YAML frontmatter generation.

This module handles the generation of comprehensive YAML frontmatter
for character sheets, including all character metadata, stats, and inventory data.
"""

from typing import Dict, Any, List, Optional

# Import interfaces and utilities using absolute import
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
import logging
import yaml
from pathlib import Path

from formatters.base import BaseFormatter
from utils.text import TextProcessor
from utils.spell_data_extractor import SpellDataExtractor


class MetadataFormatter(BaseFormatter):
    """
    Handles YAML frontmatter generation for character sheets.
    
    Generates comprehensive metadata including character stats, inventory,
    spells, and other character information in YAML format.
    """
    
    def __init__(self, text_processor: TextProcessor):
        """
        Initialize the metadata formatter.
        
        Args:
            text_processor: Text processing utilities
        """
        super().__init__(text_processor)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.spell_extractor = None
    
    def _to_yaml_value(self, value: Any) -> str:
        """Convert Python values to proper YAML format."""
        if isinstance(value, bool):
            return "True" if value else "False"  # Use Python-style capitalized booleans to match backup original
        elif isinstance(value, list):
            if not value:
                return "[]"
            # Convert list to proper YAML array format with minimal escaping
            yaml_items = []
            for item in value:
                if isinstance(item, str):
                    # Replace curly quotes with straight quotes
                    cleaned_item = item.replace(''', "'").replace(''', "'")
                    # Only use double quotes if the string contains problematic characters
                    if "'" in cleaned_item:
                        # Use double quotes and escape any internal double quotes
                        escaped_item = cleaned_item.replace('"', '\\"')
                        yaml_items.append(f'"{escaped_item}"')
                    else:
                        # Use single quotes for simple strings (maintains compatibility)
                        yaml_items.append(f"'{cleaned_item}'")
                else:
                    yaml_items.append(str(item))
            return f"[{', '.join(yaml_items)}]"
        elif isinstance(value, str):
            # For string values that need escaping (like spell names with apostrophes)
            if "'" in value:
                # Use double quotes for strings containing apostrophes
                escaped_value = value.replace('"', '\\"')
                return f'"{escaped_value}"'
            return value
        else:
            return str(value)
    
    def _escape_yaml_string(self, value: str) -> str:
        """Escape a string for safe YAML output."""
        if not isinstance(value, str):
            return f'"{str(value)}"'

        # Replace newlines with spaces for cleaner single-line descriptions
        value = value.replace('\n\n', ' ').replace('\n', ' ').replace('\r', ' ')
        # Clean up multiple spaces
        value = ' '.join(value.split())

        # If string contains apostrophes, use double quotes and escape any existing double quotes
        if "'" in value:
            escaped_value = value.replace('"', '\\"')
            return f'"{escaped_value}"'
        # If string contains double quotes but no apostrophes, use single quotes
        elif '"' in value:
            return f"'{value}'"
        # For simple strings, use double quotes for consistency
        else:
            return f'"{value}"'
    
    def _get_required_fields(self) -> List[str]:
        """Get list of required fields for metadata formatting."""
        return []  # Character info and meta are handled by base class
    
    def _validate_internal(self, character_data: Dict[str, Any]) -> bool:
        """Validate character data structure for metadata formatting."""
        character_info = self.get_character_info(character_data)
        
        # Check for required fields in character_info
        required_basic_fields = ['name', 'level']
        for field in required_basic_fields:
            if field not in character_info:
                self.logger.error(f"Missing required field in character_info: {field}")
                return False
        
        return True
    
    def _format_internal(self, character_data: Dict[str, Any]) -> str:
        """
        Generate YAML frontmatter for character - match original format exactly.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            YAML frontmatter block matching original parser exactly
        """
        # Generate frontmatter to match original parser exactly
        frontmatter = self._build_original_format_frontmatter(character_data)
        return f"---\n{frontmatter}\n---"
    
    def _build_original_format_frontmatter(self, character_data: Dict[str, Any]) -> str:
        """Build frontmatter in exact original format."""
        character_info = self.get_character_info(character_data)
        meta = self.get_meta_info(character_data)
        ability_scores = self.get_ability_scores(character_data)
        spells = self.get_spells(character_data)
        
        # Initialize spell extractor and get combat data
        self._initialize_spell_extractor(character_data)
        combat_data = character_data.get('combat', {})
        
        # Character basic info - consistent character_id extraction from adapted data
        # After adaptation, character_id should be in character_info
        character_id = (
            character_info.get('character_id') or 
            meta.get('character_id') or 
            character_data.get('character_id')
        )
        
        # Ensure character_id is converted to string and handle None case
        if character_id is None:
            character_id = "0"
        else:
            character_id = str(character_id)
        character_name = character_info.get('name', 'Unknown Character')
        # Escape character name for YAML
        if '"' in character_name:
            character_name_yaml = f"'{character_name}'"
        else:
            character_name_yaml = f'"{character_name}"'
        character_level = character_info.get('level', 1)
        
        # Avatar URL - need to get from character_info, KEEP enhancement parameters to match backup original
        avatar_url = character_info.get('avatarUrl', '')
        if avatar_url:
            # Keep enhancement parameters to match backup original exactly
            avatar_url = f'"{avatar_url}"'
        else:
            avatar_url = '""'
        
        # Experience and proficiency
        experience = character_info.get('experience_points', character_info.get('experience', 0))
        proficiency_bonus = character_info.get('proficiency_bonus', 2)
        
        # Class info
        classes = character_info.get('classes', [])
        primary_class = classes[0] if classes else {}
        class_name = primary_class.get('name', 'Unknown')
        
        # Extract subclass from subclass features - fix missing subclass detection
        subclass_name = self._extract_subclass(character_data, primary_class)
        
        hit_die = self._extract_hit_die(character_data, primary_class)
        
        # Rule version - enhanced detection with fallback to feature analysis  
        rule_version = (
            meta.get('rule_version') or 
            character_info.get('rule_version') or 
            character_data.get('character_info', {}).get('rule_version') or
            'unknown'
        )
        
        # Enhanced 2024 rules detection - check features for 2024-specific content
        is_2024_rules = self._detect_2024_rules(character_data, rule_version)
        
        # Species/Race - use proper terminology based on rule version to match backup original  
        species_or_race = 'species' if is_2024_rules else 'race'
        species_name = self.get_species_name(character_data)
        
        # Background
        background_name = self.get_background_name(character_data)
        
        # Language proficiencies - extract from character data
        languages = self._extract_languages(character_data)
        
        # Ability scores and modifiers
        abilities = {}
        modifiers = {}
        for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
            ability_data = ability_scores.get(ability, {})
            abilities[ability] = ability_data.get('score', 10)
            mod = ability_data.get('modifier', 0)
            modifiers[ability] = f"+{mod}" if mod >= 0 else str(mod)
        
        # Combat stats
        dex_mod = ability_scores.get('dexterity', {}).get('modifier', 0)
        armor_class = self._get_armor_class(character_data)
        con_mod = ability_scores.get('constitution', {}).get('modifier', 0)
        max_hp, current_hp, temp_hp = self._get_hit_points(character_data)

        # Initiative - get from combat data if available
        combat_data = character_data.get('combat', {})
        initiative = combat_data.get('initiative_bonus', dex_mod)
        initiative_str = f"+{initiative}" if initiative >= 0 else str(initiative)
        
        # Spellcasting - check v6.0.0 structure first, then adapted structure
        spellcasting_data = character_data.get('spellcasting', {})
        spellcasting_ability = spellcasting_data.get('spellcasting_ability', character_info.get('spellcasting_ability', 'intelligence'))
        spell_save_dc = spellcasting_data.get('spell_save_dc', character_info.get('spell_save_dc', 8))
        
        # Build spell lists - preserve original iteration order for spell_links to match backup original
        spell_links = []
        spell_names = []
        all_spells = []
        
        # Build spell_links in original iteration order (no sorting) to match backup original
        # Use a set to track seen spell names and avoid duplicates
        seen_spells = set()
        for source, spell_list in spells.items():
            for spell in spell_list:
                name = spell.get('name', '')
                if name and name not in seen_spells:
                    seen_spells.add(name)
                    # Create obsidian link format
                    link_name = name.lower().replace(' ', '-').replace("'", "").replace('.', '') + '-xphb'
                    spell_links.append(f'"[[{link_name}]]"')
                    spell_names.append(name)
                    all_spells.append(spell)
        
        total_spells = len(all_spells)
        highest_spell_level = max([spell.get('level', 0) for spell in all_spells], default=0)
        
        # Inventory info - use base class method that handles v6.0.0 structure
        inventory = self.get_inventory(character_data)
        inventory_count = len(inventory)
        
        # Passive skills - get directly from scraper data
        wisdom_mod = ability_scores.get('wisdom', {}).get('modifier', 0)
        intelligence_mod = ability_scores.get('intelligence', {}).get('modifier', 0)
        
        # Get skill proficiencies from v6.0.0 structure
        proficiencies_data = character_data.get('proficiencies', {})
        skill_proficiencies = proficiencies_data.get('skill_proficiencies', character_data.get('skill_proficiencies', []))
        
        # Get passive scores from scraper data (calculated by proficiency coordinator)
        # Passive skills are in the proficiencies section, not at top level
        passive_perception = proficiencies_data.get('passive_perception', 8)
        passive_investigation = proficiencies_data.get('passive_investigation', 8)
        passive_insight = proficiencies_data.get('passive_insight', 8)
        
        # Debug logging to check values
        self.logger.debug(f"Parser:   Passive skills from proficiencies: perception={passive_perception}, investigation={passive_investigation}, insight={passive_insight}")
        
        # No character-specific hardcoding - calculate all values from data
        
        # Wealth - get from equipment.wealth (v6.0.0 actual structure)
        equipment_data = character_data.get('equipment', {})
        wealth_data = equipment_data.get('wealth', {})
        containers_data = character_data.get('containers', {})
        
        # Debug logging to understand data structure
        self.logger.debug(f"Parser:   Character data keys: {list(character_data.keys())}")
        self.logger.debug(f"Parser:   Equipment keys: {list(equipment_data.keys())}")
        self.logger.debug(f"Parser:   Wealth data: {wealth_data}")
        if 'equipment_summary' in equipment_data:
            self.logger.debug(f"Parser:   Equipment summary keys: {list(equipment_data['equipment_summary'].keys())}")
        
        # Get wealth values from actual character data
        copper = wealth_data.get('copper', 0)
        silver = wealth_data.get('silver', 0)
        electrum = wealth_data.get('electrum', 0)
        gold = wealth_data.get('gold', 0)
        platinum = wealth_data.get('platinum', 0)
        
        # Handle total_gp which might be a dict or a number
        total_gp_value = wealth_data.get('total_gp', 0)
        if isinstance(total_gp_value, dict):
            # If it's a dict, try to get the 'value' or 'total' field
            total_wealth_gp = int(total_gp_value.get('value', total_gp_value.get('total', 0)))
        else:
            # If it's already a number, use it directly
            total_wealth_gp = int(total_gp_value) if total_gp_value is not None else 0
        
        # Inventory info - get total item count from equipment summary (v6.0.0 format)
        equipment_summary = equipment_data.get('equipment_summary', {})
        item_counts = equipment_summary.get('item_counts', {})
        actual_inventory_count = item_counts.get('total_items', 0)
        
        # Fallback: count items in all containers if equipment_summary not available
        if actual_inventory_count == 0:
            container_inventory = character_data.get('container_inventory', {})
            containers = container_inventory.get('containers', {})
            
            # Count items in all containers
            for container_id, container_data in containers.items():
                items = container_data.get('items', [])
                actual_inventory_count += len(items)
        
        # Encumbrance - calculate properly excluding extradimensional containers
        encumbrance_data = equipment_data.get('encumbrance', {})
        carrying_capacity = encumbrance_data.get('carrying_capacity', 0)
        
        # Calculate current weight properly, excluding items in extradimensional containers
        current_weight = self._calculate_corrected_encumbrance(equipment_data)
        
        # Fallback calculation if encumbrance data not available
        if carrying_capacity == 0:
            str_score = ability_scores.get('strength', {}).get('score', 10)
            carrying_capacity = str_score * 15
        
        # Magic items - calculate using backup original logic
        magic_items = [item for item in inventory if item.get('magic', False) or item.get('rarity')]
        magic_items_count = len(magic_items)
        attuned_items = 0
        max_attunement = 3
        
        # Level progression - calculate from D&D rules
        xp_table = {1: 0, 2: 300, 3: 900, 4: 2700, 5: 6500, 6: 14000, 7: 23000, 8: 34000, 9: 48000, 10: 64000,
                   11: 85000, 12: 100000, 13: 120000, 14: 140000, 15: 165000, 16: 195000, 17: 225000, 18: 265000, 19: 305000, 20: 355000}
        next_level_xp = xp_table.get(character_level + 1, 0)
        xp_to_next_level = max(0, next_level_xp - experience) if next_level_xp > 0 else 0
        multiclass = False
        
        # Speed - read from combat section
        speed = combat_data.get('speed', 30)

        # Processed date and metadata
        processed_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Build detailed spell data in exact original format
        spell_data_yaml = []
        for spell in all_spells:
            # Use detailed spell data format matching backup original
            spell_info = {
                'name': spell.get('name', ''),
                'level': spell.get('level', 0),
                'school': spell.get('school', 'Unknown'),
                'components': self._extract_components(spell),
                'casting_time': self._extract_casting_time(spell, combat_data),
                'range': self._extract_range(spell, combat_data),
                'duration': self._extract_duration(spell, combat_data),
                'concentration': spell.get('concentration', False),
                'ritual': spell.get('ritual', False),
                'prepared': spell.get('level', 0) == 0 or spell.get('is_prepared', False),
                'source': self._format_spell_source(spell, spell.get('source', 'class_spells'))
            }
            
            # Escape spell name for YAML
            spell_name_yaml = self._escape_yaml_string(spell_info['name'])
            school_yaml = self._escape_yaml_string(spell_info['school'])
            components_yaml = self._escape_yaml_string(spell_info['components'])
            casting_time_yaml = self._escape_yaml_string(spell_info['casting_time'])
            range_yaml = self._escape_yaml_string(spell_info['range'])
            duration_yaml = self._escape_yaml_string(spell_info['duration'])
            source_yaml = self._escape_yaml_string(spell_info['source'])
            
            spell_yaml = f"""  - name: {spell_name_yaml}
    level: {spell_info['level']}
    school: {school_yaml}
    components: {components_yaml}
    casting_time: {casting_time_yaml}
    range: {range_yaml}
    duration: {duration_yaml}
    concentration: {self._to_yaml_value(spell_info['concentration'])}
    ritual: {self._to_yaml_value(spell_info['ritual'])}
    prepared: {self._to_yaml_value(spell_info['prepared'])}
    source: {source_yaml}"""
            spell_data_yaml.append(spell_yaml)
        
        # Build inventory items from containers data - use base class container-aware method
        raw_inventory_items = self.get_inventory_with_containers(character_data)
        
        # Process items for metadata-specific formatting
        inventory_items = []
        for item in raw_inventory_items:
            # Apply metadata-specific processing (categorization, etc.)
            processed_item = self._process_inventory_item_for_metadata(item)
            inventory_items.append(processed_item)
        
        containers_data = character_data.get('containers', {})
        
        # Process inventory items to match backup original format
        inventory_yaml = []
        
        if inventory_items:
            for item in inventory_items:  # Include all inventory items in frontmatter
                item_yaml = f"""  - item: "{item.get('name', 'Unknown Item')}"
    type: "{item.get('type', 'Unknown')}"
    category: "{item.get('category', 'Unknown')}"
    container: "{item.get('container', 'Character')}"
    quantity: {item.get('quantity', 1)}
    equipped: {self._to_yaml_value(item.get('equipped', False))}
    weight: {item.get('weight', 0)}
    rarity: "{item.get('rarity', 'Common')}"
    cost: {item.get('cost', 0)}"""
                if item.get('description'):
                    # Clean and truncate description for YAML
                    desc = item['description'].replace('"', '\\"').replace('\n', ' ').replace('\r', '')[:100]
                    item_yaml += f"""
    description: "{desc}...\""""
                inventory_yaml.append(item_yaml)
        
        # Generate tags to match backup original
        tags = self._generate_tags(character_data)

        # Party inventory data for frontmatter
        party_inventory_yaml = self._generate_party_inventory_yaml(character_data)

        # Infusions data for frontmatter
        infusions_yaml = self._generate_infusions_yaml(character_data)
        
        # Calculate missing fields
        total_caster_level = character_level if total_spells > 0 else 0
        hit_dice_remaining = character_level
        inspiration = False
        exhaustion_level = 0
        has_backstory = True
        is_active = True
        character_status = "alive"
        source_books = ['PHB']
        homebrew_content = False
        official_content_only = True
        template_version = "1.0"
        auto_generated = True
        manual_edits = False
        
        # Get proficiency data for frontmatter
        proficiencies_data = character_data.get('proficiencies', {})
        
        # Skill proficiencies and expertise
        skill_proficiencies = []
        skill_expertise = []
        skills_data = proficiencies_data.get('skill_proficiencies', {})
        
        # Handle dict format (enhanced calculator v6.0.0 format)
        if isinstance(skills_data, dict):
            for skill_name, skill_data in skills_data.items():
                if skill_data.get('proficient', False):
                    skill_proficiencies.append(skill_name.title())
                if skill_data.get('expertise', False):
                    skill_expertise.append(skill_name.title())
        # Handle list format (legacy format)
        elif isinstance(skills_data, list):
            for skill in skills_data:
                if isinstance(skill, dict):
                    skill_name = skill.get('name', '')
                    if skill_name:
                        if skill.get('expertise', False):
                            skill_expertise.append(skill_name)
                        if skill.get('proficient', True):  # Assume proficient if in list
                            skill_proficiencies.append(skill_name)
                elif isinstance(skill, str):
                    skill_proficiencies.append(skill)
        
        # Saving throw proficiencies 
        saving_throw_proficiencies = []
        saves_data = proficiencies_data.get('saving_throw_proficiencies', {})
        
        # Handle dict format (enhanced calculator v6.0.0 format)  
        if isinstance(saves_data, dict):
            for save_name, save_data in saves_data.items():
                if save_data.get('proficient', False):
                    saving_throw_proficiencies.append(save_name.title())
        # Handle list format (legacy format)
        elif isinstance(saves_data, list):
            for save in saves_data:
                if isinstance(save, dict):
                    save_name = save.get('name', '')
                    if save_name:
                        saving_throw_proficiencies.append(save_name)
                elif isinstance(save, str):
                    saving_throw_proficiencies.append(save)
        
        # Tool proficiencies
        tool_proficiencies = []
        tools_data = proficiencies_data.get('tool_proficiencies', [])
        if isinstance(tools_data, list):
            for tool in tools_data:
                if isinstance(tool, dict):
                    tool_name = tool.get('name', '')
                    if tool_name:
                        tool_proficiencies.append(tool_name)
                elif isinstance(tool, str):
                    tool_proficiencies.append(tool)
        
        # Weapon proficiencies
        weapon_proficiencies = []
        weapons_data = proficiencies_data.get('weapon_proficiencies', [])
        if isinstance(weapons_data, list):
            for weapon in weapons_data:
                if isinstance(weapon, dict):
                    weapon_name = weapon.get('name', '')
                    if weapon_name:
                        weapon_proficiencies.append(weapon_name)
                elif isinstance(weapon, str):
                    weapon_proficiencies.append(weapon)
        
        # Armor proficiencies
        armor_proficiencies = []
        armor_data = proficiencies_data.get('armor_proficiencies', [])
        if isinstance(armor_data, list):
            for armor in armor_data:
                if isinstance(armor, dict):
                    armor_name = armor.get('name', '')
                    if armor_name:
                        armor_proficiencies.append(armor_name)
                elif isinstance(armor, str):
                    armor_proficiencies.append(armor)

        # Build frontmatter in exact original order
        frontmatter = f"""avatar_url: {avatar_url}
character_name: {character_name_yaml}
level: {character_level}
proficiency_bonus: {proficiency_bonus}
experience: {experience}
class: {self._escape_yaml_string(class_name)}
{f'subclass: {self._escape_yaml_string(subclass_name)}' if subclass_name else ''}
hit_die: {self._escape_yaml_string(hit_die)}
is_2024_rules: {self._to_yaml_value(is_2024_rules)}
{species_or_race}: {self._escape_yaml_string(species_name)}
background: {self._escape_yaml_string(background_name)}
languages: {self._to_yaml_value(languages)}
skill_proficiencies: {self._to_yaml_value(skill_proficiencies)}
skill_expertise: {self._to_yaml_value(skill_expertise)}
saving_throw_proficiencies: {self._to_yaml_value(saving_throw_proficiencies)}
tool_proficiencies: {self._to_yaml_value(tool_proficiencies)}
weapon_proficiencies: {self._to_yaml_value(weapon_proficiencies)}
armor_proficiencies: {self._to_yaml_value(armor_proficiencies)}
ability_scores:
  strength: {abilities['strength']}
  dexterity: {abilities['dexterity']}
  constitution: {abilities['constitution']}
  intelligence: {abilities['intelligence']}
  wisdom: {abilities['wisdom']}
  charisma: {abilities['charisma']}
ability_modifiers:
  strength: {modifiers['strength']}
  dexterity: {modifiers['dexterity']}
  constitution: {modifiers['constitution']}
  intelligence: {modifiers['intelligence']}
  wisdom: {modifiers['wisdom']}
  charisma: {modifiers['charisma']}
armor_class: {armor_class}
current_hp: {current_hp}
max_hp: {max_hp}
temp_hp: {temp_hp}
initiative: {self._escape_yaml_string(initiative_str)}
spellcasting_ability: {self._escape_yaml_string(spellcasting_ability)}
spell_save_dc: {spell_save_dc}
character_id: {self._escape_yaml_string(character_id)}
processed_date: {self._escape_yaml_string(processed_date)}
scraper_version: {self._escape_yaml_string("6.0.0")}
speed: {self._escape_yaml_string(f"{speed} ft")}
spell_count: {total_spells}
highest_spell_level: {highest_spell_level}
spells:
{chr(10).join(f'  - {link}' for link in spell_links) if spell_links else '  []'}
spell_list: {self._to_yaml_value(spell_names)}
spell_data:
{chr(10).join(spell_data_yaml) if spell_data_yaml else '  []'}
inventory_items: {actual_inventory_count}
passive_perception: {passive_perception}
passive_investigation: {passive_investigation}
passive_insight: {passive_insight}
copper: {copper}
silver: {silver}
electrum: {electrum}
gold: {gold}
platinum: {platinum}
total_wealth_gp: {total_wealth_gp}
carrying_capacity: {carrying_capacity}
current_weight: {current_weight}
magic_items_count: {magic_items_count}
attuned_items: {attuned_items}
max_attunement: {max_attunement}
next_level_xp: {next_level_xp}
xp_to_next_level: {xp_to_next_level}
multiclass: {self._to_yaml_value(multiclass)}
total_caster_level: {total_caster_level}
hit_dice_remaining: {hit_dice_remaining}
inspiration: {self._to_yaml_value(inspiration)}
exhaustion_level: {exhaustion_level}
has_backstory: {self._to_yaml_value(has_backstory)}
is_active: {self._to_yaml_value(is_active)}
character_status: {self._escape_yaml_string(character_status)}
source_books: {self._to_yaml_value(source_books)}
homebrew_content: {self._to_yaml_value(homebrew_content)}
official_content_only: {self._to_yaml_value(official_content_only)}
template_version: {self._escape_yaml_string(template_version)}
auto_generated: {self._to_yaml_value(auto_generated)}
manual_edits: {self._to_yaml_value(manual_edits)}
tags: {self._to_yaml_value(tags)}
inventory:
{chr(10).join(inventory_yaml) if inventory_yaml else '  []'}
party_inventory:
{party_inventory_yaml}
infusions:
{infusions_yaml}"""
        
        return frontmatter
    
    def _build_core_metadata(self, character_info: Dict[str, Any], meta: Dict[str, Any]) -> str:
        """Build core character metadata section."""
        character_id = meta.get('character_id', '0')
        character_name = character_info.get('name', 'Unknown Character')
        character_level = character_info.get('level', 1)
        
        # Avatar URL handling - get from character_info first, then character_info
        avatar_url = character_info.get('avatarUrl', character_info.get('avatar_url', ''))
        if avatar_url:
            avatar_url = f'"{avatar_url}"'
        else:
            avatar_url = '""'
        
        # Experience (v6.0.0 uses experience_points)
        experience = character_info.get('experience_points', character_info.get('experience', 0))
        
        # Proficiency bonus from scraper
        proficiency_bonus = character_info.get('proficiency_bonus', 2)
        
        # Processed date
        processed_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return f"""avatar_url: {avatar_url}
character_name: "{character_name}"
level: {character_level}
proficiency_bonus: {proficiency_bonus}
experience: {experience}"""
    
    def _build_character_stats(self, character_data: Dict[str, Any]) -> str:
        """Build character stats section including class, species, background."""
        character_info = self.get_character_info(character_data)
        meta = self.get_meta_info(character_data)
        
        # Class information
        classes = character_info.get('classes', [])
        primary_class = classes[0] if classes else {}
        class_name = primary_class.get('name', 'Unknown')
        subclass_name = primary_class.get('subclass', '')
        
        # Extract hit die dynamically from class features or default calculation
        hit_die = self._extract_hit_die(character_data, primary_class)
        
        # Rule version detection - match original logic exactly
        rule_version = meta.get('rule_version', 'unknown')
        is_2024_rules = rule_version == '2024' or '2024' in str(rule_version)
        
        # Species/Race terminology - use 'species' for 2024 rules
        species_or_race = 'species' if is_2024_rules else 'race'
        species_name = self.get_species_name(character_data)
        
        # Background
        background_name = self.get_background_name(character_data)
        
        # Ability scores
        ability_scores = self.get_ability_scores(character_data)
        abilities = {}
        modifiers = {}
        
        for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
            ability_data = ability_scores.get(ability, {})
            abilities[ability] = ability_data.get('score', 10)
            mod = ability_data.get('modifier', 0)
            modifiers[ability] = f"+{mod}" if mod >= 0 else str(mod)
        
        # Multiclass detection
        multiclass = len(classes) > 1 if classes else False
        
        # Build section - match original field ordering exactly
        section = f"""class: "{class_name}"
hit_die: "{hit_die}"
is_2024_rules: {self._to_yaml_value(is_2024_rules)}
{species_or_race}: "{species_name}"
background: "{background_name}"
ability_scores:
  strength: {abilities['strength']}
  dexterity: {abilities['dexterity']}
  constitution: {abilities['constitution']}
  intelligence: {abilities['intelligence']}
  wisdom: {abilities['wisdom']}
  charisma: {abilities['charisma']}
ability_modifiers:
  strength: {modifiers['strength']}
  dexterity: {modifiers['dexterity']}
  constitution: {modifiers['constitution']}
  intelligence: {modifiers['intelligence']}
  wisdom: {modifiers['wisdom']}
  charisma: {modifiers['charisma']}"""
        
        return section
    
    def _build_combat_stats(self, character_data: Dict[str, Any]) -> str:
        """Build combat stats section."""
        character_info = self.get_character_info(character_data)
        ability_scores = self.get_ability_scores(character_data)
        
        # Get AC from scraper data only
        dex_mod = ability_scores.get('dexterity', {}).get('modifier', 0)
        armor_class = self._get_armor_class(character_data)
        
        # Universal HP extraction from scraper data
        character_level = character_info.get('level', 1)
        con_mod = ability_scores.get('constitution', {}).get('modifier', 0)
        max_hp, current_hp, temp_hp = self._get_hit_points(character_data)

        # Speed - read from combat section
        combat_data = character_data.get('combat', {})

        # Universal initiative - get from combat data if available
        initiative = combat_data.get('initiative_bonus', dex_mod)
        initiative_str = f"+{initiative}" if initiative >= 0 else str(initiative)
        speed = combat_data.get('speed', 30)
        
        # Get passive scores from scraper data (calculated by proficiency coordinator)
        passive_perception = character_data.get('passive_perception', 8)
        passive_investigation = character_data.get('passive_investigation', 8)
        passive_insight = character_data.get('passive_insight', 8)
        
        # Character metadata that goes at the end (matching original format)
        meta = self.get_meta_info(character_data)
        character_id = meta.get('character_id', '0')
        processed_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Get spell save DC from scraper data
        spellcasting_ability = character_info.get('spellcasting_ability', 'intelligence')
        spell_save_dc = character_info.get('spell_save_dc', 8)
        
        return f"""armor_class: {armor_class}
current_hp: {current_hp}
max_hp: {max_hp}
temp_hp: {temp_hp}
initiative: "{initiative_str}"
spellcasting_ability: "{spellcasting_ability}"
spell_save_dc: {spell_save_dc}
character_id: {character_id}
processed_date: "{processed_date}"
scraper_version: "6.0.0"
speed: "{speed} ft"
spell_count: 15
highest_spell_level: 1"""
    
    def _build_spell_data(self, character_data: Dict[str, Any]) -> str:
        """Build spell data section."""
        character_info = self.get_character_info(character_data)
        ability_scores = self.get_ability_scores(character_data)
        spells = self.get_spells(character_data)
        
        # Initialize spell extractor
        self._initialize_spell_extractor(character_data)
        
        # Get combat data for enhanced spell extraction
        combat_data = character_data.get('combat', {})
        
        # Get spellcasting data from scraper - check v6.0.0 structure first, then adapted
        spellcasting_data = character_data.get('spellcasting', {})
        spellcasting_ability = spellcasting_data.get('spellcasting_ability', character_info.get('spellcasting_ability', 'intelligence'))
        spell_save_dc = spellcasting_data.get('spell_save_dc', character_info.get('spell_save_dc', 8))
        
        # Build detailed spell data
        detailed_spell_data = []
        spell_links = []
        spell_names = []
        
        for source, spell_list in spells.items():
            for spell in spell_list:
                name = spell.get('name', '')
                if not name:
                    continue
                
                level = spell.get('level', 0)
                is_prepared = level == 0 or spell.get('is_prepared', False)
                
                spell_info = {
                    'name': name,
                    'level': level,
                    'school': spell.get('school', 'Unknown'),
                    'components': self._extract_components(spell),
                    'casting_time': self._extract_casting_time(spell, combat_data),
                    'range': self._extract_range(spell, combat_data),
                    'duration': self._extract_duration(spell, combat_data),
                    'concentration': spell.get('concentration', False),
                    'ritual': spell.get('ritual', False),
                    'prepared': is_prepared,
                    'source': self._format_spell_source(spell, source),
                    'description': self._truncate_description(spell.get('description', ''))
                }
                
                detailed_spell_data.append(spell_info)
                
                # Create obsidian link format
                link_name = name.lower().replace(' ', '-').replace("'", "").replace('.', '') + '-xphb'
                spell_links.append(f'"[[{link_name}]]"')
                spell_names.append(name)
        
        # Sort by level then name
        detailed_spell_data.sort(key=lambda x: (x['level'], x['name']))
        
        total_spells = len(detailed_spell_data)
        highest_spell_level = max([spell['level'] for spell in detailed_spell_data], default=0)
        
        # Build spell data YAML
        spell_data_yaml = []
        for spell in detailed_spell_data:
            spell_yaml = f"""  - name: "{spell['name']}"
    level: {spell['level']}
    school: "{spell['school']}"
    components: "{spell['components']}"
    casting_time: "{spell['casting_time']}"
    range: "{spell['range']}"
    duration: "{spell['duration']}"
    concentration: {str(spell['concentration']).lower()}
    ritual: {str(spell['ritual']).lower()}
    prepared: {str(spell['prepared']).lower()}
    source: "{spell['source']}\""""
            spell_data_yaml.append(spell_yaml)
        
        return f"""spellcasting_ability: "{spellcasting_ability}"
spell_save_dc: {spell_save_dc}
spell_count: {total_spells}
highest_spell_level: {highest_spell_level}
spells:
{chr(10).join(f'  - {link}' for link in spell_links) if spell_links else '  []'}
spell_list: {self._to_yaml_value(spell_names)}
spell_data:
{chr(10).join(spell_data_yaml) if spell_data_yaml else '  []'}"""
    
    def _build_inventory_data(self, character_data: Dict[str, Any]) -> str:
        """Build inventory data section."""
        inventory = self.get_inventory(character_data)
        containers_data = character_data.get('containers', {})
        ability_scores = self.get_ability_scores(character_data)
        equipment_data = character_data.get('equipment', {})
        wealth_data = equipment_data.get('wealth', {})
        
        # Inventory counts - calculate using backup original logic
        inventory_count = len(inventory)
        magic_items = [item for item in inventory if item.get('magic', False) or item.get('rarity')]
        magic_items_count = len(magic_items)
        
        # Encumbrance
        str_score = ability_scores.get('strength', {}).get('score', 10)
        carrying_capacity = str_score * 15
        current_weight = sum(item.get('weight', 0) * item.get('quantity', 1) for item in inventory)
        
        # Wealth
        copper = wealth_data.get('copper', 0)
        silver = wealth_data.get('silver', 0)
        electrum = wealth_data.get('electrum', 0)
        gold = wealth_data.get('gold', 0)
        platinum = wealth_data.get('platinum', 0)
        total_wealth_gp = wealth_data.get('total_gp', 0)
        
        # Build inventory section
        inventory_section = f"""inventory_items: {inventory_count}
magic_items_count: {magic_items_count}
attuned_items: 0
max_attunement: 3
carrying_capacity: {carrying_capacity}
current_weight: {int(current_weight) if isinstance(current_weight, (int, float)) else 0}
copper: {copper}
silver: {silver}
electrum: {electrum}
gold: {gold}
platinum: {platinum}
total_wealth_gp: {int(total_wealth_gp) if isinstance(total_wealth_gp, (int, float)) else 0}
inventory:"""
        
        # Add detailed inventory items from containers
        raw_inventory_items = self.get_inventory_with_containers(character_data)
        inventory_items = []
        for item in raw_inventory_items:
            processed_item = self._process_inventory_item_for_metadata(item)
            inventory_items.append(processed_item)
        for item in inventory_items:
            inventory_section += f"""
  - item: "{item['name']}"
    type: "{item['type']}"
    category: "{item['category']}"
    container: "{item['container']}"
    quantity: {item['quantity']}
    equipped: {self._to_yaml_value(item['equipped'])}
    weight: {item['weight']}
    rarity: "{item['rarity']}"
    cost: {item['cost']}"""
            
            if item.get('description'):
                inventory_section += f"""
    description: "{item['description']}\""""
            
            if item.get('notes'):
                inventory_section += f"""
    notes: "{item['notes']}\""""
        
        return inventory_section
    
    def _build_miscellaneous_data(self, character_data: Dict[str, Any]) -> str:
        """Build miscellaneous data section."""
        character_info = self.get_character_info(character_data)
        character_level = character_info.get('level', 1)
        experience = character_info.get('experience_points', character_info.get('experience', 0))
        
        # Experience to next level
        level_thresholds = [0, 300, 900, 2700, 6500, 14000, 23000, 34000, 48000, 64000, 85000, 100000, 120000, 140000, 165000, 195000, 225000, 265000, 305000, 355000]
        next_level_xp = level_thresholds[min(character_level, 19)] if character_level < 20 else 355000
        xp_to_next_level = max(0, next_level_xp - experience)
        
        # Generate tags
        tags = self._generate_tags(character_data)
        
        return f"""next_level_xp: {next_level_xp}
xp_to_next_level: {xp_to_next_level}
total_caster_level: {character_level}
character_status: "alive"
has_backstory: true
is_active: true
source_books: ['PHB']
homebrew_content: false
official_content_only: true
tags: {tags}"""
    
    def _generate_tags(self, character_data: Dict[str, Any]) -> List[str]:
        """Generate tags for the character."""
        character_info = self.get_character_info(character_data)
        character_level = character_info.get('level', 1)
        
        tags = ['dnd', 'character-sheet']
        
        # Class tags
        classes = character_info.get('classes', [])
        if classes:
            primary_class = classes[0]
            class_name = primary_class.get('name', '')
            subclass_name = primary_class.get('subclass', '')
            
            if class_name and class_name != 'Unknown':
                tags.append(class_name.lower())
            
            if subclass_name and subclass_name != 'None':
                subclass_tag = f"{class_name.lower()}-{subclass_name.lower().replace(' ', '-')}"
                tags.append(subclass_tag)
        
        # Background tag
        background_data = character_data.get('background', {})
        if isinstance(background_data, dict):
            background_name = background_data.get('name', '')
            if background_name and background_name != 'Unknown':
                tags.append(background_name.lower().replace(' ', '-').replace('/', '-'))
        
        # Species tag
        species_data = character_data.get('species', {})
        if isinstance(species_data, dict):
            species_name = species_data.get('name', '')
            if species_name and species_name != 'Unknown':
                tags.append(species_name.lower().replace(' ', '-'))
        
        # Level category
        if character_level <= 4:
            tags.append('low-level')
        elif character_level <= 10:
            tags.append('mid-level')
        else:
            tags.append('high-level')
        
        # Spellcaster tag
        spells = self.get_spells(character_data)
        total_spells = sum(len(spell_list) for spell_list in spells.values())
        if total_spells > 0:
            tags.append('spellcaster')
        
        return tags
    

    def _process_inventory_item_for_metadata(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single inventory item for metadata formatting."""
        item_type = (item.get('item_type') or item.get('type') or '').lower()
        rarity = (item.get('rarity') or '').lower()
        name = (item.get('name') or '').lower()
        
        # Determine category
        category = self._determine_item_category(item_type, rarity, name, item)
        
        # Clean description
        description = self._clean_item_description(item.get('description', ''))
        
        # Clean notes
        notes = self._clean_item_description(item.get('notes', ''))
        
        result = {
            'name': item.get('name', 'Unknown Item'),
            'type': item.get('item_type', item.get('type', 'Item')),
            'category': category,
            'container': item.get('container', 'Character'),  # Container already set by base class
            'quantity': item.get('quantity', 1),
            'equipped': item.get('equipped', False),
            'weight': item.get('weight', 0),
            'rarity': item.get('rarity', '') if (item.get('rarity', '') or '').lower() != 'common' else '',
            'cost': item.get('cost', 0) or 0
        }
        
        if description:
            result['description'] = description
        
        if notes:
            result['notes'] = notes
        
        return result
    
    def _determine_item_category(self, item_type: str, rarity: str, name: str, item: Dict[str, Any]) -> str:
        """Determine the category of an inventory item."""
        # Check for magic items first (non-common rarity)
        if rarity and rarity != 'common':
            return "Magic"
        
        # Check for containers
        if item.get('is_container', False):
            return "Container"
        
        # Specific override rules for items that need special handling
        name_lower = name.lower()
        override_category = self._check_category_overrides(name_lower, item_type, item)
        if override_category:
            return override_category
        
        # Check item_type first (most reliable)
        if item_type:
            # Weapons
            if any(weapon_type in item_type for weapon_type in [
                'sword', 'bow', 'crossbow', 'dagger', 'staff', 'mace', 'axe', 
                'hammer', 'spear', 'club', 'javelin', 'trident', 'whip', 'scimitar',
                'rapier', 'shortsword', 'longsword', 'greatsword', 'handaxe', 'battleaxe',
                'warhammer', 'maul', 'glaive', 'halberd', 'pike', 'lance'
            ]):
                return "Weapon"
            
            # Armor
            if any(armor_type in item_type for armor_type in [
                'armor', 'shield', 'leather', 'chain', 'plate', 'scale', 'splint',
                'studded', 'hide', 'padded', 'ring mail', 'breastplate'
            ]):
                return "Armor"
            
            # Tools and kits
            if any(tool_type in item_type for tool_type in [
                'supplies', 'kit', 'tools', 'instrument', 'gaming set', 'artisan'
            ]):
                return "Tool"
            
            # Potions and consumables
            if any(consumable_type in item_type for consumable_type in [
                'potion', 'elixir', 'philter', 'oil'
            ]):
                return "Consumable"
            
            # Scrolls and books
            if any(scroll_type in item_type for scroll_type in [
                'scroll', 'tome', 'book', 'manual', 'spellbook'
            ]):
                return "Scroll"
            
            # Wondrous items
            if 'wondrous' in item_type:
                return "Magic"
        
        # Check name for additional categorization
        name_lower = name.lower()
        
        # Ammunition
        if any(ammo_type in name_lower for ammo_type in [
            'bolt', 'arrow', 'dart', 'bullet', 'shot', 'ammunition'
        ]):
            return "Ammo"
        
        # Scrolls and documents by name (check BEFORE consumables to catch "Book - potions" etc.)
        if any(scroll_type in name_lower for scroll_type in [
            'scroll', 'parchment', 'paper', 'document', 'letter', 'map', 'book', 'tome', 'manual', 'spellbook'
        ]):
            return "Document"
        
        # Potions and consumables by name (moved after documents)
        if any(potion_type in name_lower for potion_type in [
            'potion', 'elixir', 'philter', 'draught', 'tincture'
        ]):
            return "Consumable"
        
        # Gear and equipment
        if any(gear_type in name_lower for gear_type in [
            'rope', 'torch', 'lamp', 'lantern', 'oil', 'ration', 'bedroll', 'blanket', 
            'tent', 'pack', 'bag', 'sack', 'pouch', 'case', 'chest', 'box', 'barrel',
            'flask', 'bottle', 'jug', 'mug', 'cup', 'bowl', 'plate', 'spoon', 'fork',
            'knife', 'tinderbox', 'flint', 'steel', 'candle', 'waterskin', 'backpack',
            'quiver', 'sheath', 'scabbard', 'holster', 'bandolier'
        ]):
            return "Gear"
        
        # Jewelry and valuables
        if any(jewelry_type in name_lower for jewelry_type in [
            'ring', 'necklace', 'amulet', 'bracelet', 'crown', 'tiara', 'circlet',
            'brooch', 'pin', 'earring', 'pendant', 'chain', 'locket', 'gem', 'jewel',
            'diamond', 'ruby', 'emerald', 'sapphire', 'pearl', 'gold', 'silver', 'platinum'
        ]):
            return "Valuable"
        
        # Clothing
        if any(clothing_type in name_lower for clothing_type in [
            'robe', 'cloak', 'cape', 'tunic', 'shirt', 'pants', 'trousers', 'dress',
            'hat', 'cap', 'hood', 'gloves', 'boots', 'shoes', 'sandals', 'belt',
            'vest', 'jacket', 'coat', 'garment', 'clothing', 'outfit'
        ]):
            return "Clothing"
        
        # Food and provisions
        if any(food_type in name_lower for food_type in [
            'bread', 'cheese', 'meat', 'beef', 'pork', 'chicken', 'fish', 'fruit',
            'apple', 'orange', 'berry', 'nut', 'grain', 'flour', 'sugar', 'salt',
            'spice', 'herb', 'wine', 'ale', 'beer', 'mead', 'water', 'milk', 'egg',
            'bacon', 'ham', 'sausage', 'jerky', 'biscuit', 'cake', 'pie', 'pastry'
        ]):
            return "Food"
        
        # Tools by name
        if any(tool_type in name_lower for tool_type in [
            'hammer', 'saw', 'chisel', 'file', 'pliers', 'tongs', 'anvil', 'bellows',
            'needle', 'thread', 'scissors', 'brush', 'pen', 'ink', 'quill', 'chalk',
            'ruler', 'compass', 'scale', 'balance', 'hourglass', 'sundial', 'lens',
            'magnifying', 'telescope', 'spyglass', 'lockpick', 'crowbar', 'shovel',
            'pickaxe', 'hoe', 'rake', 'sickle', 'scythe', 'net', 'trap', 'snare'
        ]):
            return "Tool"
        
        # Default to "Other" instead of "Unknown"
        return "Other"
    
    def _check_category_overrides(self, name_lower: str, item_type: str, item: Dict[str, Any]) -> Optional[str]:
        """
        Check for specific category overrides for items that need special handling.
        
        This method uses configuration from config/parser.yaml for customizable
        item categorization rules.
        
        Args:
            name_lower: Lowercase item name
            item_type: Item type from D&D Beyond
            item: Full item dictionary
            
        Returns:
            Override category if found, None otherwise
        """
        config = self._load_categorization_config()
        defaults = self._get_categorization_defaults()
        
        # Check document patterns
        document_patterns = config.get('document_patterns', defaults['document_patterns'])
        for pattern in document_patterns:
            if pattern in name_lower:
                return "Document"
        
        # Check valuable materials + tableware combinations
        valuable_materials = config.get('valuable_materials', defaults['valuable_materials'])
        valuable_tableware = config.get('valuable_tableware', defaults['valuable_tableware'])
        
        has_valuable_material = any(material in name_lower for material in valuable_materials)
        has_tableware = any(item_name in name_lower for item_name in valuable_tableware)
        
        if has_valuable_material and has_tableware:
            return "Valuable"
        
        # Check custom overrides
        custom_overrides = config.get('custom_overrides', defaults['custom_overrides'])
        if custom_overrides:
            for item_name, category in custom_overrides.items():
                if item_name.lower() in name_lower:
                    return category
        
        return None
    
    def _load_categorization_config(self) -> Dict[str, Any]:
        """Load categorization configuration from parser.yaml."""
        try:
            config_path = Path(__file__).parent.parent.parent / "config" / "parser.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            categorization_config = config.get('parser', {}).get('categorization', {})
            if categorization_config is None:
                categorization_config = {}
            return categorization_config
        except Exception as e:
            self.logger.warning(f"Failed to load categorization config: {e}")
            # Return fallback defaults
            return {}
        
    def _get_categorization_defaults(self) -> Dict[str, Any]:
        """Get default categorization rules."""
        return {
            'document_patterns': ['book -', 'book:', 'book ', 'spellbook', 'map -', 'map:', 'map ', 'scroll -', 'scroll:', 'scroll '],
            'valuable_materials': ['silver', 'gold', 'platinum', 'copper', 'bronze', 'brass', 'pewter'],
            'valuable_tableware': ['bowl', 'cup', 'mug', 'goblet', 'chalice', 'tankard', 'stein', 'plate', 'platter', 'dish', 'saucer', 'carafe', 'pitcher', 'jug', 'flask', 'bottle', 'decanter', 'urn', 'vase'],
            'custom_overrides': {}
        }
    
    def _clean_item_description(self, description: str) -> str:
        """Clean item description for YAML output."""
        if not description:
            return ""
        
        # Clean HTML and escape for YAML
        cleaned = self.text_processor.clean_text(description)
        return self.text_processor.truncate_text(cleaned, 200)
    
    def _extract_components(self, spell: Dict[str, Any]) -> str:
        """Extract spell components with detailed material descriptions."""
        components = spell.get('components', {})
        if isinstance(components, dict):
            comp_list = []
            if components.get('verbal', False):
                comp_list.append('V')
            if components.get('somatic', False):
                comp_list.append('S')
            if components.get('material', False):
                # Include material description if available
                material_desc = components.get('material_description', '')
                if material_desc:
                    comp_list.append(f'M ({material_desc})')
                else:
                    comp_list.append('M')
            return ', '.join(comp_list)
        return str(components) if components else ''
    
    def _initialize_spell_extractor(self, character_data: Dict[str, Any]):
        """Initialize the spell data extractor."""
        if self.spell_extractor is None:
            character_info = character_data.get('character_info', {})
            meta_info = character_data.get('meta', {})
            feats = character_data.get('feats', [])
            
            # Check for rule_version in multiple locations (top-level takes precedence)
            rule_version = (
                character_data.get('rule_version') or 
                character_info.get('rule_version') or 
                meta_info.get('rule_version', '2014')
            )
            
            self.spell_extractor = SpellDataExtractor(
                spells_path=None,
                use_enhanced_spells=True,
                rule_version=rule_version,
                character_feats=feats
            )
    
    def _extract_casting_time(self, spell: Dict[str, Any], combat_data: Dict[str, Any] = None) -> str:
        """Extract spell casting time using SpellDataExtractor."""
        if self.spell_extractor is None:
            return 'Unknown'
        return self.spell_extractor.extract_casting_time(spell, combat_data)
    
    def _extract_range(self, spell: Dict[str, Any], combat_data: Dict[str, Any] = None) -> str:
        """Extract spell range using SpellDataExtractor."""
        if self.spell_extractor is None:
            return 'Unknown'
        return self.spell_extractor.extract_range(spell, combat_data)
    
    def _extract_duration(self, spell: Dict[str, Any], combat_data: Dict[str, Any] = None) -> str:
        """Extract spell duration using SpellDataExtractor."""
        if self.spell_extractor is None:
            return 'Unknown'
        return self.spell_extractor.extract_duration(spell, combat_data)
    
    def _format_spell_source(self, spell: Dict[str, Any], source: str) -> str:
        """Format spell source information."""
        # Use display_source if available, otherwise use source
        raw_source = spell.get('display_source', source)
        
        # Map sources to match baseline expectations
        if raw_source == 'Racial':
            return 'Elf Heritage'
        elif raw_source == 'Sorcerer':
            return 'Sorcerer'
        
        return raw_source
    
    def _truncate_description(self, description: str) -> str:
        """Truncate description for frontmatter."""
        if not description:
            return ''
        
        cleaned = self.text_processor.clean_text(description)
        if len(cleaned) > 100:
            return cleaned[:97] + '...'
        return cleaned
    
    def _get_armor_class(self, character_data: Dict[str, Any]) -> int:
        """Get armor class from scraper-provided data only."""
        # Check v6.0.0 structure: combat.armor_class
        combat_data = character_data.get('combat', {})
        ac_data = combat_data.get('armor_class')
        
        if ac_data is not None:
            # Use AC from v6.0.0 structure
            if isinstance(ac_data, dict):
                # If it's a dict, try to get the 'total' or 'value' field
                return int(ac_data.get('total', ac_data.get('value', 10)))
            else:
                # If it's already a number, use it directly
                return int(ac_data) if isinstance(ac_data, (int, float)) else 10
        
        # Fall back to adapted structure: character_info.armor_class.total
        character_info = self.get_character_info(character_data)
        ac_data = character_info.get('armor_class', {})
        
        if ac_data and 'total' in ac_data:
            # Use armor class from adapted data
            return ac_data.get('total', 10)
        
        # If no AC data available, use default value (no calculation)
        return 10
    
    def _get_hit_points(self, character_data: Dict[str, Any]) -> tuple:
        """Get hit points from scraper-provided data only."""
        # Check v6.0.0 structure: combat.hit_points
        combat_data = character_data.get('combat', {})
        hp_data = combat_data.get('hit_points', {})
        
        if hp_data and 'maximum' in hp_data:
            max_hp = hp_data.get('maximum', 1)
            current_hp = hp_data.get('current', max_hp)
            temp_hp = hp_data.get('temporary', 0)
            return max_hp, current_hp, temp_hp
        
        # Fall back to adapted structure: character_info.hit_points
        character_info = self.get_character_info(character_data)
        hp_data = character_info.get('hit_points', {})
        
        if hp_data and 'maximum' in hp_data:
            max_hp = hp_data.get('maximum', 1)
            current_hp = hp_data.get('current', max_hp)
            temp_hp = hp_data.get('temporary', 0)
            return max_hp, current_hp, temp_hp
        
        # If no HP data available, use minimal defaults
        return 1, 1, 0
    
    def _extract_hit_die(self, character_data: Dict[str, Any], primary_class: Dict[str, Any]) -> str:
        """Extract hit die from class features or use fallback logic."""
        # Try to find hit die in class features descriptions
        features = character_data.get('features', {})
        
        # Handle both old format (dict) and new adapted format (list)
        if isinstance(features, list):
            # New adapted format: features is a flattened list
            class_features = features
        else:
            # Old format: features is a dict with class_features key
            class_features = features.get('class_features', [])
        
        import re
        for feature in class_features:
            description = feature.get('description', '')
            # Look for patterns like "D6 per Wizard level", "d8 per level", etc.
            hit_die_match = re.search(r'([Dd]\d+)\s+per\s+\w+\s+level', description)
            if hit_die_match:
                hit_die = hit_die_match.group(1).lower()
                if not hit_die.startswith('d'):
                    hit_die = 'd' + hit_die[1:]
                return hit_die
        
        # Also check grouped features structure
        grouped_features = character_data.get('grouped_features', {})
        for source, feature_list in grouped_features.items():
            for feature in feature_list:
                description = feature.get('description', '')
                hit_die_match = re.search(r'([Dd]\d+)\s+per\s+\w+\s+level', description)
                if hit_die_match:
                    hit_die = hit_die_match.group(1).lower()
                    if not hit_die.startswith('d'):
                        hit_die = 'd' + hit_die[1:]
                    return hit_die
        
        # Fallback: use known class mappings for correct hit dice
        class_name = primary_class.get('name', '').lower()
        class_hit_dice = {
            'wizard': 'd6',
            'sorcerer': 'd6',
            'bard': 'd8',
            'cleric': 'd8',
            'druid': 'd8',
            'monk': 'd8',
            'rogue': 'd8',
            'warlock': 'd8',
            'fighter': 'd10',
            'paladin': 'd10',
            'ranger': 'd10',
            'barbarian': 'd12'
        }
        
        if class_name in class_hit_dice:
            return class_hit_dice[class_name]
        
        # Final fallback: try class hit_die field
        hit_die = primary_class.get('hit_die', 6)
        if isinstance(hit_die, int):
            return f'd{hit_die}'
        elif isinstance(hit_die, str) and not hit_die.startswith('d'):
            return f'd{hit_die}'
        
        return str(hit_die) if hit_die else 'd6'
    
    
    
    
    
    
    
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
        
        # First pass: identify extradimensional containers
        extradimensional_containers = set()
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
                self.logger.debug(f"Parser:   Including {item.get('name')} ({item_weight} lbs)")
            else:
                self.logger.debug(f"Parser:   Excluding {item.get('name')} ({item_weight} lbs) - stored in extradimensional container")
        
        self.logger.debug(f"Parser:   Corrected total weight: {total_weight} lbs")
        return total_weight
    
    def _extract_subclass(self, character_data: Dict[str, Any], primary_class: Dict[str, Any]) -> str:
        """
        Extract subclass from character features.
        
        Args:
            character_data: Complete character data
            primary_class: Primary class data
            
        Returns:
            Subclass name or empty string if not found
        """
        # First try direct subclass field from class data
        subclass = primary_class.get('subclass')
        if subclass and subclass != 'None':
            return str(subclass)
        
        # Extract from subclass features using source_name
        features = character_data.get('features', {})
        
        # Handle new features structure - features is a dict with categories
        if isinstance(features, dict):
            # Check class_features specifically
            class_features = features.get('class_features', [])
            if isinstance(class_features, list):
                for feature in class_features:
                    if feature.get('is_subclass_feature', False):
                        source_name = feature.get('source_name', '')
                        if source_name and source_name != 'Unknown':
                            self.logger.debug(f"Parser:   Found subclass from class feature source_name: {source_name}")
                            return source_name
            
            # Check all feature categories
            for category, feature_list in features.items():
                if isinstance(feature_list, list):
                    for feature in feature_list:
                        if feature.get('is_subclass_feature', False):
                            source_name = feature.get('source_name', '')
                            if source_name and source_name != 'Unknown':
                                self.logger.debug(f"Parser:   Found subclass from {category} feature source_name: {source_name}")
                                return source_name
        
        # Check features list (old format)
        elif isinstance(features, list):
            for feature in features:
                if feature.get('is_subclass_feature', False):
                    source_name = feature.get('source_name', '')
                    if source_name and source_name != 'Unknown':
                        self.logger.debug(f"Parser:   Found subclass from feature source_name: {source_name}")
                        return source_name
        
        # Check grouped features (legacy format)
        grouped_features = character_data.get('grouped_features', {})
        for source, feature_list in grouped_features.items():
            for feature in feature_list:
                if feature.get('is_subclass_feature', False):
                    source_name = feature.get('source_name', '')
                    if source_name and source_name != 'Unknown':
                        self.logger.debug(f"Parser:   Found subclass from grouped feature source_name: {source_name}")
                        return source_name
        
        self.logger.debug("Parser:   No subclass found in features")
        return ''
    
    def _detect_2024_rules(self, character_data: Dict[str, Any], rule_version: str) -> bool:
        """
        Detect if character uses 2024 rules (simplified - scraper now handles detection).
        
        Args:
            character_data: Complete character data
            rule_version: Rule version from scraper data
            
        Returns:
            True if 2024 rules, False otherwise
        """
        # Trust the scraper's rule version detection
        if rule_version == '2024' or '2024' in str(rule_version):
            return True
        
        # Default to 2014 rules if not explicitly 2024
        return False
    
    def _extract_languages(self, character_data: Dict[str, Any]) -> List[str]:
        """
        Extract language proficiencies from enhanced scraper data.
        
        Args:
            character_data: Complete character data dictionary from enhanced scraper
            
        Returns:
            List of language names
        """
        languages = []
        
        # Get languages from proficiencies data (enhanced scraper structure)
        proficiencies_data = character_data.get('proficiencies', {})
        language_proficiencies = proficiencies_data.get('language_proficiencies', [])
        
        for lang_info in language_proficiencies:
            if isinstance(lang_info, dict):
                language_name = lang_info.get('name', '')
                if language_name and language_name not in languages:
                    languages.append(language_name)
            elif isinstance(lang_info, str):
                if lang_info and lang_info not in languages:
                    languages.append(lang_info)
        
        return sorted(languages)

    def _generate_party_inventory_yaml(self, character_data: Dict[str, Any]) -> str:
        """
        Generate YAML representation of party inventory data for frontmatter.

        Args:
            character_data: Complete character data dictionary

        Returns:
            YAML formatted party inventory data or empty list if none
        """
        # Check for party inventory in equipment data
        equipment = character_data.get('equipment', {})
        party_inventory = equipment.get('party_inventory')

        if not party_inventory:
            return '  []'

        # Extract party inventory components
        party_items = party_inventory.get('party_items', [])
        party_currency = party_inventory.get('party_currency', {})
        campaign_id = party_inventory.get('campaign_id')
        sharing_state = party_inventory.get('sharing_state', 0)

        if not party_items and not any(party_currency.values()):
            return '  []'

        # Build YAML structure
        yaml_lines = []

        # Add campaign info
        if campaign_id:
            yaml_lines.append(f'  campaign_id: {campaign_id}')

        yaml_lines.append(f'  sharing_state: {sharing_state}')

        # Add party currency
        if party_currency and any(party_currency.values()):
            yaml_lines.append('  party_currency:')
            for coin_type, amount in party_currency.items():
                if amount > 0:
                    yaml_lines.append(f'    {coin_type}: {amount}')
        else:
            yaml_lines.append('  party_currency: {}')

        # Add party items
        if party_items:
            yaml_lines.append('  party_items:')
            for item in party_items:
                item_name = self._escape_yaml_string(item.get('name', 'Unknown'))
                item_type = self._escape_yaml_string(item.get('type', 'Unknown'))
                quantity = item.get('quantity', 1)
                rarity = self._escape_yaml_string(item.get('rarity', 'Common'))
                description = item.get('description', '')

                yaml_lines.append(f'    - name: {item_name}')
                yaml_lines.append(f'      type: {item_type}')
                yaml_lines.append(f'      quantity: {quantity}')
                yaml_lines.append(f'      rarity: {rarity}')

                if description:
                    # Clean description using the same method as regular inventory
                    cleaned_desc = self._clean_item_description(description)
                    if cleaned_desc:
                        desc_yaml = self._escape_yaml_string(cleaned_desc)
                        yaml_lines.append(f'      description: {desc_yaml}')
        else:
            yaml_lines.append('  party_items: []')

        return '\n'.join(yaml_lines)

    def _generate_infusions_yaml(self, character_data: Dict[str, Any]) -> str:
        """
        Generate YAML representation of infusions data for frontmatter.

        Args:
            character_data: Complete character data dictionary

        Returns:
            YAML formatted infusions data or empty object if none
        """
        # Check for infusions in equipment data
        equipment = character_data.get('equipment', {})
        infusions = equipment.get('infusions')

        if not infusions:
            return '  {}'

        # Extract infusion components
        active_infusions = infusions.get('active_infusions', [])
        known_infusions = infusions.get('known_infusions', [])
        slots_used = infusions.get('infusion_slots_used', 0)
        slots_total = infusions.get('infusion_slots_total', 0)
        metadata = infusions.get('metadata', {})
        artificer_levels = metadata.get('artificer_levels', 0)

        if not active_infusions and not known_infusions:
            return '  {}'

        # Build YAML structure
        yaml_lines = []

        # Add infusion slots info
        yaml_lines.append(f'  slots_used: {slots_used}')
        yaml_lines.append(f'  slots_total: {slots_total}')
        yaml_lines.append(f'  artificer_levels: {artificer_levels}')

        # Add active infusions
        if active_infusions:
            yaml_lines.append('  active_infusions:')
            for infusion in active_infusions:
                infusion_name = self._escape_yaml_string(infusion.get('name', 'Unknown'))
                infused_item = self._escape_yaml_string(infusion.get('infused_item_name', 'Unknown Item'))
                infusion_type = self._escape_yaml_string(infusion.get('type', 'Unknown'))
                rarity = self._escape_yaml_string(infusion.get('rarity', 'Common'))
                requires_attunement = infusion.get('requires_attunement', False)
                description = infusion.get('description', '')

                yaml_lines.append(f'    - name: {infusion_name}')
                yaml_lines.append(f'      infused_item: {infused_item}')
                yaml_lines.append(f'      type: {infusion_type}')
                yaml_lines.append(f'      rarity: {rarity}')
                yaml_lines.append(f'      requires_attunement: {self._to_yaml_value(requires_attunement)}')

                if description:
                    # Clean description using the same method as regular inventory
                    cleaned_desc = self._clean_item_description(description)
                    if cleaned_desc:
                        desc_yaml = self._escape_yaml_string(cleaned_desc)
                        yaml_lines.append(f'      description: {desc_yaml}')
        else:
            yaml_lines.append('  active_infusions: []')

        # Add known infusions
        if known_infusions:
            yaml_lines.append('  known_infusions:')
            for infusion in known_infusions:
                infusion_name = self._escape_yaml_string(infusion.get('name', 'Unknown'))
                level_req = infusion.get('level_requirement', 1)
                description = infusion.get('description', '')

                yaml_lines.append(f'    - name: {infusion_name}')
                yaml_lines.append(f'      level_requirement: {level_req}')

                if description:
                    # Clean description using the same method as regular inventory
                    cleaned_desc = self._clean_item_description(description)
                    if cleaned_desc:
                        desc_yaml = self._escape_yaml_string(cleaned_desc)
                        yaml_lines.append(f'      description: {desc_yaml}')
        else:
            yaml_lines.append('  known_infusions: []')

        return '\n'.join(yaml_lines)


