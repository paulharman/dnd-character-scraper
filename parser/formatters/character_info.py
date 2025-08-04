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

# Configure Windows-1252 encoding for console output compatibility
os.environ['PYTHONIOENCODING'] = 'windows-1252'
os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '1'

# Reconfigure current process stdio for immediate effects
try:
    sys.stdout.reconfigure(encoding='windows-1252', errors='replace')
    sys.stderr.reconfigure(encoding='windows-1252', errors='replace')
except AttributeError:
    # Fallback for older Python versions
    pass

cmd = ['python', 'parser/dnd_json_to_markdown.py', '{character_id}', full_path]
result = subprocess.run(cmd, capture_output=True, text=True, encoding='windows-1252', errors='replace')

# Capture and display Discord changes if present
if result.returncode == 0:
    if result.stdout and ('DISCORD CHANGES DETECTED:' in result.stdout or 'DISCORD STATUS:' in result.stdout):
        # Extract and display Discord content
        lines = result.stdout.split('\\n')
        discord_started = False
        for line in lines:
            if 'DISCORD CHANGES DETECTED:' in line or 'DISCORD STATUS:' in line:
                discord_started = True
                print(line)
                continue
            elif discord_started:
                # Print all content until we reach the end or another section
                if line.startswith('====') or line.startswith('SUCCESS:'):
                    break
                else:
                    print(line)
    
    print('SUCCESS: Character refreshed!')
    print('Reload file to see changes.')
else:
    print(f'ERROR: {{result.stderr}}')
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
        
        # Class information
        classes = character_info.get('classes', [])
        primary_class = classes[0] if classes else {}
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
        meta = character_data.get('meta', {})
        character_id = meta.get('character_id', '0')
        
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
        
        # Class information
        classes = character_info.get('classes', [])
        primary_class = classes[0] if classes else {}
        class_name = primary_class.get('name', 'Unknown')
        subclass_name = primary_class.get('subclass', 'None')
        
        # If subclass is empty, try to derive from features
        if not subclass_name or subclass_name == 'None':
            derived_subclass = self._derive_subclass_from_features(character_data, class_name)
            if derived_subclass:
                subclass_name = derived_subclass
        
        # Combat stats - get from v6.0.0 structure first, then fallback
        combat_data = character_data.get('combat', {})
        
        # Initiative: use Dex modifier (initiative = dex mod)
        ability_scores = self.get_ability_scores(character_data)
        dex_mod = ability_scores.get('dexterity', {}).get('modifier', 0)
        initiative = dex_mod
        initiative_str = f"+{initiative}" if initiative >= 0 else str(initiative)
        
        # Speed from species data
        species_data = character_data.get('character_info', {}).get('species', {})
        speed = species_data.get('speed', 30)
        
        # AC from combat section (scraper provides complete calculation)
        ac_data = combat_data.get('armor_class', {})
        if isinstance(ac_data, dict) and 'total' in ac_data:
            armor_class = ac_data['total']  # Use scraper's calculated value directly
            
            # Use enhanced AC breakdown from scraper
            if 'breakdown' in ac_data:
                # Extract method and details from breakdown
                breakdown = ac_data['breakdown']
                if ac_data.get('has_armor', False):
                    # Armored character
                    armor_type = ac_data.get('armor_type', 'unknown').title()
                    if ac_data.get('has_shield', False):
                        ac_method = f'{armor_type} + Shield'
                    else:
                        ac_method = f'{armor_type} Armor'
                    # Use the detailed breakdown as details
                    ac_details = f'({breakdown.split(": ", 1)[-1]})'
                else:
                    # Unarmored character - check for unarmored defense
                    if 'Barbarian' in breakdown:
                        ac_method = 'Unarmored Defense (Barbarian)'  
                        ac_details = '(10 + Dex + Con)'
                    elif 'Monk' in breakdown:
                        ac_method = 'Unarmored Defense (Monk)'
                        ac_details = '(10 + Dex + Wis)'
                    else:
                        ac_method = 'Unarmored'
                        ac_details = '(10 + Dex)'
            else:
                # Fallback if no breakdown available
                ac_method = 'Unarmored'
                ac_details = '(10 + Dex)'
        else:
            # Fallback only if scraper data is missing
            armor_class = 10 + dex_mod
            ac_method = 'Unarmored'
            ac_details = '(10 + Dex)'
        
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
    value: '{initiative_str}'
  - label: Speed
    value: '{speed} ft'
  - label: Armor Class
    sublabel: {ac_method} {ac_details}
    value: {armor_class}

grid:
  columns: 3
```

<BR>

```healthpoints
state_key: {state_key}_health
health: {max_hp}
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
        
        # Class information
        classes = character_info.get('classes', [])
        primary_class = classes[0] if classes else {}
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