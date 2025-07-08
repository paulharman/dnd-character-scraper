"""
YAML frontmatter formatter for D&D character sheets.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from .base import BaseFormatter

logger = logging.getLogger(__name__)


class YAMLFormatter(BaseFormatter):
    """Formatter for YAML frontmatter in character sheets."""
    
    def format(self) -> str:
        """Format character data as YAML frontmatter."""
        lines = ["---"]
        
        # Basic character info
        lines.extend(self._format_basic_info())
        
        # Ability scores and modifiers
        lines.extend(self._format_abilities())
        
        # Combat stats
        lines.extend(self._format_combat_stats())
        
        # Spellcasting info
        lines.extend(self._format_spellcasting())
        
        # Spells
        lines.extend(self._format_spells())
        
        # Inventory summary
        lines.extend(self._format_inventory_summary())
        
        # Features and passives
        lines.extend(self._format_features())
        
        # Meta information
        lines.extend(self._format_meta())
        
        lines.append("---")
        return "\n".join(lines)
    
    def _format_basic_info(self) -> List[str]:
        """Format basic character information."""
        lines = []
        
        # Character portrait
        appearance = self.character_data.get('appearance', {})
        avatar_url = appearance.get('avatar_url', '')
        if avatar_url:
            lines.append(f'avatar_url: "{avatar_url}"')
        
        # Basic info
        lines.append(f'character_name: "{self.character_name}"')
        lines.append(f'level: {self.character_level}')
        
        # Class info
        classes = self.character_data.get('classes', [])
        if classes:
            primary_class = classes[0]
            lines.append(f'class: "{primary_class.get("name", "Unknown")}"')
            lines.append(f'hit_die: "d{self._get_hit_die(primary_class.get("name", ""))}"')
        
        # Rule version
        is_2024 = self.rule_version == "2024"
        lines.append(f'is_2024_rules: {str(is_2024).lower()}')
        
        # Species/Background
        species = self.character_data.get('species', {})
        background = self.character_data.get('background', {})
        lines.append(f'species: "{species.get("name", "Unknown")}"')
        lines.append(f'background: "{background.get("name", "Unknown")}"')
        
        # Experience
        proficiency_bonus = self.character_data.get('proficiency_bonus', 2)
        experience = self.character_data.get('experience_points', 0)
        lines.append(f'proficiency_bonus: {proficiency_bonus}')
        lines.append(f'experience: {experience}')
        
        return lines
    
    def _format_abilities(self) -> List[str]:
        """Format ability scores and modifiers."""
        lines = []
        
        ability_scores = self.character_data.get('ability_scores', {})
        ability_modifiers = self.character_data.get('ability_modifiers', {})
        
        # Ability scores
        lines.append('ability_scores:')
        for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
            score = ability_scores.get(ability, 10)
            lines.append(f'  {ability}: {score}')
        
        # Ability modifiers
        lines.append('ability_modifiers:')
        for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
            modifier = ability_modifiers.get(ability, 0)
            lines.append(f'  {ability}: {self.format_modifier(modifier)}')
        
        return lines
    
    def _format_combat_stats(self) -> List[str]:
        """Format combat-related statistics."""
        lines = []
        
        # Combat stats
        armor_class = self.character_data.get('armor_class', 10)
        current_hp = self.character_data.get('current_hp', 1)
        max_hp = self.character_data.get('max_hp', 1)
        initiative = self.character_data.get('initiative_bonus', 0)
        
        lines.append(f'armor_class: {armor_class}')
        lines.append(f'current_hp: {current_hp}')
        lines.append(f'max_hp: {max_hp}')
        lines.append(f'initiative: "{self.format_modifier(initiative)}"')
        
        return lines
    
    def _format_spellcasting(self) -> List[str]:
        """Format spellcasting information."""
        lines = []
        
        is_spellcaster = self.character_data.get('is_spellcaster', False)
        if not is_spellcaster:
            return lines
        
        spellcasting_ability = self.character_data.get('spellcasting_ability', 'intelligence')
        spell_save_dc = self.character_data.get('spell_save_dc', 8)
        spell_attack_bonus = self.character_data.get('spell_attack_bonus', 0)
        
        # Get ability modifier for spellcasting
        ability_modifiers = self.character_data.get('ability_modifiers', {})
        ability_mod = ability_modifiers.get(spellcasting_ability, 0)
        
        lines.append(f'spellcasting_ability: "{spellcasting_ability}"')
        lines.append(f'spell_save_dc: {spell_save_dc}')
        lines.append(f'spell_attack_bonus: {self.format_modifier(spell_attack_bonus)}')
        lines.append(f'spellcasting_modifier: {self.format_modifier(ability_mod)}')
        
        # Spell count and highest level
        spells = self.character_data.get('spells', {})
        total_spells = sum(len(spell_list) for spell_list in spells.values())
        highest_level = 0
        
        for spell_list in spells.values():
            for spell in spell_list:
                spell_level = spell.get('level', 0)
                if spell_level > highest_level:
                    highest_level = spell_level
        
        lines.append(f'spell_count: {total_spells}')
        lines.append(f'highest_spell_level: {highest_level}')
        
        return lines
    
    def _format_spells(self) -> List[str]:
        """Format spell lists."""
        lines = []
        
        spells = self.character_data.get('spells', {})
        if not spells:
            return lines
        
        # Obsidian-style spell links
        lines.append('spells:')
        for source, spell_list in spells.items():
            if spell_list:
                lines.append(f'  {source}:')
                for spell in spell_list:
                    spell_name = spell.get('name', 'Unknown Spell')
                    lines.append(f'    - "[[{spell_name}]]"')
        
        # Plain spell list
        lines.append('spell_list:')
        for source, spell_list in spells.items():
            if spell_list:
                lines.append(f'  {source}:')
                for spell in spell_list:
                    spell_name = spell.get('name', 'Unknown Spell')
                    lines.append(f'    - "{spell_name}"')
        
        return lines
    
    def _format_inventory_summary(self) -> List[str]:
        """Format inventory summary."""
        lines = []
        
        inventory = self.character_data.get('inventory', [])
        item_count = len(inventory)
        
        lines.append(f'inventory_items: {item_count}')
        
        # Wealth breakdown
        wealth_data = self.character_data.get('wealth', {})
        lines.append('wealth:')
        lines.append(f'  copper: {wealth_data.get("copper", 0)}')
        lines.append(f'  silver: {wealth_data.get("silver", 0)}')
        lines.append(f'  electrum: {wealth_data.get("electrum", 0)}')
        lines.append(f'  gold: {wealth_data.get("gold", 0)}')
        lines.append(f'  platinum: {wealth_data.get("platinum", 0)}')
        lines.append(f'  total_gp: {wealth_data.get("total_gp", 0)}')
        
        # Encumbrance information
        encumbrance_data = self.character_data.get('encumbrance', {})
        encumbrance_level = encumbrance_data.get('encumbrance_level', 0)
        lines.append(f'encumbrance: {encumbrance_level}')
        lines.append(f'carrying_capacity: {encumbrance_data.get("carrying_capacity", 0)}')
        lines.append(f'total_weight: {encumbrance_data.get("total_weight", 0)}')
        
        return lines
    
    def _format_features(self) -> List[str]:
        """Format character features and passives."""
        lines = []
        
        # Passive scores (calculated from skills)
        skills = self.character_data.get('skills', {})
        passive_perception = 10 + skills.get('Perception', 0)
        passive_investigation = 10 + skills.get('Investigation', 0)
        passive_insight = 10 + skills.get('Insight', 0)
        
        lines.append(f'passive_perception: {passive_perception}')
        lines.append(f'passive_investigation: {passive_investigation}')
        lines.append(f'passive_insight: {passive_insight}')
        
        # Feats
        feats = self.character_data.get('feats', [])
        lines.append(f'feats_count: {len(feats)}')
        if feats:
            lines.append('feat_list:')
            for feat in feats:
                feat_name = feat.get('name', 'Unknown Feat')
                lines.append(f'  - "{feat_name}"')
        
        # Check for backstory
        notes = self.character_data.get('notes', {})
        has_backstory = bool(notes.get('backstory', '').strip())
        lines.append(f'has_backstory: {str(has_backstory).lower()}')
        
        return lines
    
    def _format_meta(self) -> List[str]:
        """Format metadata."""
        lines = []
        
        # Processing info
        processed_date = datetime.now().strftime('%Y-%m-%d')
        lines.append(f'processed_date: "{processed_date}"')
        
        scraper_version = self.character_data.get('scraper_version', '6.0.0')
        lines.append(f'scraper_version: "{scraper_version}"')
        
        character_id = self.character_data.get('character_id', 0)
        lines.append(f'character_id: {character_id}')
        
        # Tags for organization
        lines.append('tags:')
        lines.append('  - "dnd"')
        lines.append('  - "character"')
        lines.append(f'  - "level-{self.character_level}"')
        lines.append(f'  - "{self.rule_version}-rules"')
        
        return lines
    
    def _get_hit_die(self, class_name: str) -> int:
        """Get hit die size for class."""
        hit_dice = {
            'artificer': 8, 'bard': 8, 'cleric': 8, 'druid': 8, 'monk': 8,
            'rogue': 8, 'warlock': 8, 'wizard': 6, 'fighter': 10, 'paladin': 10,
            'ranger': 10, 'barbarian': 12, 'sorcerer': 6
        }
        return hit_dice.get(class_name.lower(), 8)