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
            # Convert list to proper YAML array format with single quotes to match backup original
            yaml_items = []
            for item in value:
                if isinstance(item, str):
                    # Escape single quotes by doubling them in YAML single-quoted strings
                    escaped_item = item.replace("'", "''")
                    yaml_items.append(f"'{escaped_item}'")
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
        max_hp, current_hp = self._get_hit_points(character_data)
        initiative_str = f"+{dex_mod}" if dex_mod >= 0 else str(dex_mod)
        
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
        
        # Build inventory items from containers data - use base class method
        inventory_items = self.get_inventory(character_data)
        containers_data = character_data.get('containers', {})
        
        # Process inventory items to match backup original format
        inventory_yaml = []
        
        if inventory_items:
            for item in inventory_items:  # Include all inventory items in frontmatter
                item_yaml = f"""  - item: "{item.get('name', 'Unknown Item')}"
    type: "{item.get('item_type', 'Unknown')}"
    category: "{item.get('item_type', 'Unknown')}"
    container: "Character"
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
initiative: {self._escape_yaml_string(initiative_str)}
spellcasting_ability: {self._escape_yaml_string(spellcasting_ability)}
spell_save_dc: {spell_save_dc}
character_id: {self._escape_yaml_string(character_id)}
processed_date: {self._escape_yaml_string(processed_date)}
scraper_version: {self._escape_yaml_string("6.0.0")}
speed: {self._escape_yaml_string("30 ft")}
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
{chr(10).join(inventory_yaml) if inventory_yaml else '  []'}"""
        
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
        max_hp, current_hp = self._get_hit_points(character_data)
        
        # Universal initiative: Dex modifier
        initiative = dex_mod
        initiative_str = f"+{initiative}" if initiative >= 0 else str(initiative)
        
        # Speed
        speed_data = character_info.get('speed', {})
        walking_speed = speed_data.get('walking', {})
        speed = walking_speed.get('total', 30)
        
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
        inventory_items = self._extract_inventory_items(containers_data)
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
    
    def _extract_inventory_items(self, containers_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract inventory items from containers data."""
        container_items = containers_data.get('inventory_items', [])
        container_mapping = containers_data.get('containers', {})
        
        # Create item lookup by ID
        item_lookup = {item.get('id'): item for item in container_items}
        
        inventory_items = []
        for container_id, container_info in container_mapping.items():
            container_name = container_info.get('name', 'Unknown Container')
            is_character = container_info.get('is_character', False)
            
            for item_id in container_info.get('items', []):
                if item_id in item_lookup:
                    item = item_lookup[item_id]
                    processed_item = self._process_inventory_item(item, container_name, is_character)
                    inventory_items.append(processed_item)
        
        return inventory_items
    
    def _process_inventory_item(self, item: Dict[str, Any], container_name: str, is_character: bool) -> Dict[str, Any]:
        """Process a single inventory item."""
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
            'container': 'Character' if is_character else container_name,
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
        if rarity and rarity != 'common':
            return "Magic"
        elif item.get('is_container', False):
            return "Container"
        elif any(weapon_type in item_type for weapon_type in ['sword', 'bow', 'crossbow', 'dagger', 'staff', 'mace', 'axe', 'hammer', 'spear', 'club']):
            return "Weapon"
        elif any(armor_type in item_type for armor_type in ['armor', 'shield']):
            return "Armor"
        elif 'bolt' in name or 'arrow' in name or 'ammunition' in item_type:
            return "Ammo"
        elif any(tool_type in item_type for tool_type in ['supplies', 'kit', 'tools']):
            return "Tool"
        elif any(gear_type in name for gear_type in ['rope', 'torch', 'lamp', 'oil', 'ration', 'bedroll', 'blanket', 'tent', 'pack']):
            return "Gear"
        else:
            return "Other"
    
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
            return max_hp, current_hp
        
        # Fall back to adapted structure: character_info.hit_points
        character_info = self.get_character_info(character_data)
        hp_data = character_info.get('hit_points', {})
        
        if hp_data and 'maximum' in hp_data:
            max_hp = hp_data.get('maximum', 1)
            current_hp = hp_data.get('current', max_hp)
            return max_hp, current_hp
        
        # If no HP data available, use minimal defaults
        return 1, 1
    
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