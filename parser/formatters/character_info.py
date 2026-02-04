"""
Character information formatter for character infobox and statistics.

This module handles the generation of character information sections including
the character infobox, quick links, and character statistics.
"""

from typing import Dict, Any, List, Optional

# Import interfaces and utilities using absolute import
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging

from formatters.base import BaseFormatter
from utils.text import TextProcessor


class CharacterInfoFormatter(BaseFormatter):
    """
    Handles character information formatting for character sheets.
    
    Generates character infobox, quick links navigation, and character
    statistics sections with proper DnD UI Toolkit formatting.
    """
    
    def __init__(self, text_processor: TextProcessor):
        """
        Initialize the character info formatter.
        
        Args:
            text_processor: Text processing utilities
        """
        super().__init__(text_processor)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _get_required_fields(self) -> List[str]:
        """Get list of required fields for character info formatting."""
        return []
    
    def _validate_internal(self, character_data: Dict[str, Any]) -> bool:
        """Validate character data structure for character info formatting."""
        character_info = self.get_character_info(character_data)
        
        # Check for required fields
        required_fields = ['name', 'level']
        for field in required_fields:
            if field not in character_info:
                self.logger.error(f"Missing required field in character_info: {field}")
                return False
        
        return True
    
    def _format_internal(self, character_data: Dict[str, Any]) -> str:
        """
        Generate character information sections.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Combined character information sections
        """
        sections = []
        
        # Python refresh block (matching backup original)
        python_refresh = self._generate_python_refresh_block(character_data)
        sections.append(python_refresh)
        
        # Generate character infobox
        infobox = self._generate_character_infobox(character_data)
        sections.append(infobox)
        
        # Generate quick links
        quick_links = self._generate_quick_links(character_data)
        sections.append(quick_links)
        
        # Generate character statistics
        char_stats = self._generate_character_statistics(character_data)
        sections.append(char_stats)
        
        return '\n\n'.join(section for section in sections if section)
    
    def _generate_python_refresh_block(self, character_data: Dict[str, Any]) -> str:
        """Generate Python refresh block for Obsidian integration matching backup original."""
        # Check v6.0.0 structure first, then fall back to meta
        character_info = character_data.get('character_info', {})
        character_id = character_info.get('character_id')
        if not character_id:
            meta = character_data.get('meta', {})
            character_id = meta.get('character_id', '0')
        character_id = str(character_id)
        
        
        # Get the project root directory at generation time
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        return f"""```run-python
import os, sys, subprocess

# Set to project root (hardcoded at generation time)
os.chdir(r'{project_root}')

# Get paths from Obsidian context
vault_path = @vault_path
note_path = @note_path
full_path = os.path.join(vault_path, note_path)

# Configure UTF-8 encoding for proper Unicode support (accented characters in names, etc.)
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Reconfigure current process stdio for immediate effects
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    # Fallback for older Python versions
    pass

cmd = ['python', 'parser/dnd_json_to_markdown.py', '{character_id}', full_path]
print('Refreshing...')
sys.stdout.flush()
try:
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
    if result.returncode == 0:
        if result.stdout:
            for line in result.stdout.split('\\n'):
                stripped = line.strip()
                if stripped:
                    print(stripped)
        else:
            print('Character refreshed!')
            print('Reload file to see changes.')
    else:
        err = result.stderr.strip() if result.stderr else 'Unknown error'
        print(f'ERROR: {{err}}')
except subprocess.TimeoutExpired:
    print('ERROR: Parser timed out. Try again.')
except Exception as e:
    print(f'ERROR: {{e}}')
```


---"""
    
    def _generate_character_infobox(self, character_data: Dict[str, Any]) -> str:
        """Generate character infobox with avatar and quick details."""
        character_info = self.get_character_info(character_data)
        meta = character_data.get('meta', {})
        
        # Character basic info
        character_name = character_info.get('name', 'Unknown Character')
        character_level = character_info.get('level', 1)
        
        # Avatar URL
        avatar_url = character_info.get('avatarUrl', '')
        
        # Class information - handle multiclassing
        classes = character_info.get('classes', [])
        primary_class = classes[0] if classes else {}
        
        # Check for multiclassing
        if len(classes) > 1:
            # Format as "Class1 X/Class2 Y"
            class_parts = []
            for class_data in classes:
                class_parts.append(f"{class_data.get('name', 'Unknown')} {class_data.get('level', 1)}")
            class_name = " / ".join(class_parts)
            # For subclass, use primary class's subclass
            subclass_name = primary_class.get('subclass', '')
        else:
            class_name = primary_class.get('name', 'Unknown')
            subclass_name = primary_class.get('subclass', '')
        
        # If subclass is empty, try to derive from features
        if not subclass_name:
            subclass_name = self._derive_subclass_from_features(character_data, class_name)
        
        # Species/Race terminology based on rule version
        rule_version = character_info.get('rule_version', meta.get('rule_version', 'unknown'))
        
        # Check multiple indicators for 2024 rules
        is_2024_rules = (
            rule_version == '2024' or 
            '2024' in str(rule_version) or
            character_info.get('classes', [{}])[0].get('is_2024', False) if character_info.get('classes') else False
        )
        species_or_race_label = 'Species' if is_2024_rules else 'Race'
        
        # Get species and background data from v6.0.0 structure
        species_data = character_info.get('species', character_data.get('species', {}))
        species_name = species_data.get('name', 'Unknown') if isinstance(species_data, dict) else 'Unknown'
        
        background_data = character_info.get('background', character_data.get('background', {}))
        background_name = background_data.get('name', 'Unknown') if isinstance(background_data, dict) else 'Unknown'
        
        # Combat stats - check v6.0.0 structure first
        combat_data = character_data.get('combat', {})
        hp_data = combat_data.get('hit_points', character_info.get('hit_points', {}))
        max_hp = hp_data.get('maximum', 1)
        current_hp = hp_data.get('current', max_hp)
        
        # AC from combat data (scraper provides complete calculation)
        ac_data = combat_data.get('armor_class', {})
        if isinstance(ac_data, dict) and 'total' in ac_data:
            armor_class = ac_data['total']  # Use scraper's calculated value directly
        else:
            # Fallback only if scraper data is missing
            armor_class = 10
        
        # Proficiency bonus from scraper
        proficiency_bonus = character_info.get('proficiency_bonus', 2)
        
        # Ability scores for display
        ability_scores = self.get_ability_scores(character_data)
        abilities = {}
        for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
            ability_data = ability_scores.get(ability, {})
            score = ability_data.get('score', 10)
            mod = ability_data.get('modifier', 0)
            mod_str = f"+{mod}" if mod >= 0 else str(mod)
            abilities[ability] = f"{score} ({mod_str})"
        
        # HP calculation method (simplified for now)
        hp_calc = "Manual"  # Could be enhanced to detect fixed vs manual
        
        # Build infobox
        infobox = f"""> [!infobox]+ ^character-info
> # {character_name}
{f'> ![Character Avatar|200]({avatar_url})' if avatar_url else ''}
> ###### Character Details
> |  |  |
> | --- | --- |
> | **Class** | {class_name} |{f'''
> | **Subclass** | {subclass_name} |''' if subclass_name else ''}
> | **{species_or_race_label}** | {species_name} |
> | **Background** | {background_name} |
> | **Level** | {character_level} |
> | **Hit Points** | {current_hp}/{max_hp} |
> | **HP Calc** | {hp_calc} |
> | **Armor Class** | {armor_class} |
> | **Proficiency** | +{proficiency_bonus} |
> 
> ###### Ability Scores
> |  |  |  |
> | --- | --- | --- |
> | **Str** {abilities['strength']} | **Dex** {abilities['dexterity']} | **Con** {abilities['constitution']} |
> | **Int** {abilities['intelligence']} | **Wis** {abilities['wisdom']} | **Cha** {abilities['charisma']} |"""
        
        return infobox
    
    def _generate_quick_links(self, character_data: Dict[str, Any]) -> str:
        """Generate quick links navigation table."""
        # Get character_id using fallback chain (same as metadata formatter)
        character_info = self.get_character_info(character_data)
        meta = self.get_meta_info(character_data)
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
        
        # Check if character has spells to include spellcasting link
        spells = character_data.get('spells', {})
        has_spells = bool(spells)
        
        # Build quick links table
        links = [
            "[[#Character Statistics]]",
            "[[#Abilities & Skills]]",
            "[[#Appearance]]"
        ]
        
        if has_spells:
            links.append("[[#Spellcasting]]")
        
        links.extend([
            "[[#Features]]",
            "[[#Racial Traits]]",
            "[[#Attacks]]",
            "[[#Proficiencies]]",
            "[[#Background]]",
            "[[#Backstory]]",
            "[[#Inventory]]",
            "&nbsp;",
            f"[D&D Beyond](https://www.dndbeyond.com/characters/{character_id})"
        ])
        
        quick_links = "## Quick Links\n\n| Section |\n| --- |\n"
        for link in links:
            quick_links += f"| {link} |\n"
        
        quick_links += "\n---"
        
        return quick_links
    
    def _generate_character_statistics(self, character_data: Dict[str, Any]) -> str:
        """Generate character statistics section with DnD UI Toolkit formatting."""
        character_info = self.get_character_info(character_data)
        
        # Character basic info
        character_name = character_info.get('name', 'Unknown Character')
        character_level = character_info.get('level', 1)
        
        # Class information - handle multiclassing
        classes = character_info.get('classes', [])
        primary_class = classes[0] if classes else {}
        
        # Check for multiclassing
        if len(classes) > 1:
            # Format as "Class1 X/Class2 Y"
            class_parts = []
            for class_data in classes:
                class_parts.append(f"{class_data.get('name', 'Unknown')} {class_data.get('level', 1)}")
            class_name = " / ".join(class_parts)
            # For subclass, use primary class's subclass
            subclass_name = primary_class.get('subclass', 'None')
        else:
            class_name = primary_class.get('name', 'Unknown')
            subclass_name = primary_class.get('subclass', 'None')
        
        # If subclass is empty, try to derive from features
        if not subclass_name or subclass_name == 'None':
            derived_subclass = self._derive_subclass_from_features(character_data, class_name)
            if derived_subclass:
                subclass_name = derived_subclass
        
        # Combat stats - get from v6.0.0 structure first, then fallback
        combat_data = character_data.get('combat', {})

        # Initiative: get from combat data if available (includes all bonuses)
        ability_scores = self.get_ability_scores(character_data)
        dex_mod = ability_scores.get('dexterity', {}).get('modifier', 0)
        initiative = combat_data.get('initiative_bonus', dex_mod)
        initiative_str = f"+{initiative}" if initiative >= 0 else str(initiative)

        # Get initiative breakdown if available
        initiative_breakdown = combat_data.get('initiative_breakdown', '')
        if not initiative_breakdown:
            initiative_breakdown = f"Dex {dex_mod:+d}"

        # Speed from combat data (includes class bonuses like Monk Unarmored Movement)
        # Check for new movement format first, fallback to legacy speed
        movement_data = combat_data.get('movement', {})
        if isinstance(movement_data, dict):
            walking_speed = movement_data.get('walking_speed', 30)
            climbing_speed = movement_data.get('climbing_speed', 0)
            swimming_speed = movement_data.get('swimming_speed', 0)
            flying_speed = movement_data.get('flying_speed', 0)
        else:
            # Legacy format - just walking speed
            walking_speed = combat_data.get('speed', 30)
            climbing_speed = 0
            swimming_speed = 0
            flying_speed = 0

        # AC from combat section (scraper provides complete calculation)
        ac_data = combat_data.get('armor_class', {})
        if isinstance(ac_data, dict) and 'total' in ac_data:
            armor_class = ac_data['total']  # Use scraper's calculated value directly

            # Build clean AC sublabel
            if 'breakdown' in ac_data:
                breakdown = ac_data['breakdown']
                # Parse breakdown string: "AC: 12 (armor) + 4 (dex)" or
                # "Unarmored Defense (Monk): 10 (base) + 3 (dex) + 3 (wis) + 1 (magic) = 17"
                # Extract the calculation part after ": "
                calc_part = breakdown.split(": ", 1)[-1] if ':' in breakdown else breakdown
                # Remove trailing "= N" if present
                if '=' in calc_part:
                    calc_part = calc_part.split('=')[0].strip()

                # Convert "12 (armor) + 4 (dex)" to "Armor +12, Dex +4"
                import re
                parts = re.findall(r'(\d+)\s*\((\w+)\)', calc_part)
                if parts:
                    ac_breakdown_parts = [f"{label.title()} +{value}" for value, label in parts]

                    # Add shield if present
                    if ac_data.get('has_shield', False) and not any('shield' in p.lower() for p in ac_breakdown_parts):
                        ac_breakdown_parts.append("Shield +2")

                    ac_sublabel = ", ".join(ac_breakdown_parts)
                else:
                    # Couldn't parse, use raw breakdown
                    ac_sublabel = calc_part
            else:
                ac_sublabel = "Base 10, Dex " + (f"+{dex_mod}" if dex_mod >= 0 else str(dex_mod))
        else:
            # Fallback only if scraper data is missing
            armor_class = 10 + dex_mod
            ac_sublabel = "Base 10, Dex " + (f"+{dex_mod}" if dex_mod >= 0 else str(dex_mod))
        
        # Hit points and hit dice
        hp_data = combat_data.get('hit_points', {})
        if not hp_data:
            # Fallback to character_info
            hp_data = character_info.get('hit_points', {})
        max_hp = hp_data.get('maximum', 1)
        hit_die = primary_class.get('hit_die', 6)
        
        # Ensure proper d notation for hit die
        if hit_die:
            hit_die_str = str(hit_die)
            if not hit_die_str.startswith('d'):
                hit_die = f'd{hit_die_str}'
            else:
                hit_die = hit_die_str
        
        # Create character name for state key
        state_key = self._create_state_key(character_name)

        # Build speed entry with all movement types
        speed_sublabels = []
        if climbing_speed > 0:
            speed_sublabels.append(f"Climbing speed - {climbing_speed} ft")
        if swimming_speed > 0:
            speed_sublabels.append(f"Swimming speed - {swimming_speed} ft")
        if flying_speed > 0:
            speed_sublabels.append(f"Flying speed - {flying_speed} ft")

        speed_entry = f"""  - label: Walking speed
    value: '{walking_speed} ft'"""
        if speed_sublabels:
            speed_entry += f"\n    sublabel: {', '.join(speed_sublabels)}"

        section = f"""## Character Statistics

```stats
items:
  - label: Level
    value: '{character_level}'
  - label: Class
    value: '{class_name}'
  - label: Subclass
    value: '{subclass_name}'
  - label: Initiative
    sublabel: {initiative_breakdown}
    value: '{initiative_str}'
{speed_entry}
  - label: Armor Class
    sublabel: {ac_sublabel}
    value: {armor_class}

grid:
  columns: 3
```

<BR>

```healthpoints
state_key: {state_key}_health
health: '{{{{ frontmatter.max_hp }}}}'
hitdice:
  dice: {hit_die}
  value: {character_level}
```

^character-statistics

---"""
        
        return section
    
    def _create_state_key(self, character_name: str) -> str:
        """Create a state key from character name for UI components."""
        return character_name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace(',', '')
    
    def _derive_subclass_from_features(self, character_data: Dict[str, Any], class_name: str) -> str:
        """
        Derive subclass name from features when not directly available.
        
        Args:
            character_data: Complete character data dictionary
            class_name: Primary class name
            
        Returns:
            Subclass name if found, empty string otherwise
        """
        features_data = character_data.get('features', {})
        class_features = features_data.get('class_features', [])
        
        # Look for subclass features with source_name
        for feature in class_features:
            if isinstance(feature, dict):
                if feature.get('is_subclass_feature', False):
                    source_name = feature.get('source_name', '')
                    # Make sure it's not the main class name
                    if source_name and source_name != class_name:
                        return source_name
        
        return ''
    
    def format_infobox_only(self, character_data: Dict[str, Any]) -> str:
        """
        Format only the character infobox section.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Character infobox section only
        """
        if not self.validate_input(character_data):
            raise ValueError("Invalid character data for infobox formatting")
        
        return self._generate_character_infobox(character_data)
    
    def format_quick_links_only(self, character_data: Dict[str, Any]) -> str:
        """
        Format only the quick links section.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Quick links section only
        """
        if not self.validate_input(character_data):
            raise ValueError("Invalid character data for quick links formatting")
        
        return self._generate_quick_links(character_data)
    
    def format_statistics_only(self, character_data: Dict[str, Any]) -> str:
        """
        Format only the character statistics section.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Character statistics section only
        """
        if not self.validate_input(character_data):
            raise ValueError("Invalid character data for statistics formatting")
        
        return self._generate_character_statistics(character_data)
    
    def get_character_summary(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key character information for summary purposes.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Dictionary containing key character information
        """
        character_info = self.get_character_info(character_data)
        meta = character_data.get('meta', {})
        
        # Character basic info
        character_name = character_info.get('name', 'Unknown Character')
        character_level = character_info.get('level', 1)
        
        # Class information - handle multiclassing  
        classes = character_info.get('classes', [])
        primary_class = classes[0] if classes else {}
        
        # Check for multiclassing
        if len(classes) > 1:
            # Format as "Class1 X/Class2 Y"
            class_parts = []
            for class_data in classes:
                class_parts.append(f"{class_data.get('name', 'Unknown')} {class_data.get('level', 1)}")
            class_name = " / ".join(class_parts)
            # For subclass, use primary class's subclass
            subclass_name = primary_class.get('subclass', '')
        else:
            class_name = primary_class.get('name', 'Unknown')
            subclass_name = primary_class.get('subclass', '')
        
        # Species/Race and background
        rule_version = character_info.get('rule_version', meta.get('rule_version', 'unknown'))
        is_2024_rules = rule_version == '2024' or '2024' in str(rule_version)
        
        # Get species and background data from v6.0.0 structure
        species_data = character_info.get('species', character_data.get('species', {}))
        species_name = species_data.get('name', 'Unknown') if isinstance(species_data, dict) else 'Unknown'
        
        background_data = character_info.get('background', character_data.get('background', {}))
        background_name = background_data.get('name', 'Unknown') if isinstance(background_data, dict) else 'Unknown'
        
        # Combat stats
        hp_data = character_info.get('hit_points', {})
        max_hp = hp_data.get('maximum', 1)
        current_hp = hp_data.get('current', max_hp)
        
        ac_data = character_info.get('armor_class', {})
        armor_class = ac_data.get('total', 10)
        
        return {
            'name': character_name,
            'level': character_level,
            'class': class_name,
            'subclass': subclass_name,
            'species': species_name,
            'background': background_name,
            'hp': {'current': current_hp, 'maximum': max_hp},
            'armor_class': armor_class,
            'is_2024_rules': is_2024_rules,
            'character_id': meta.get('character_id', '0')
        }