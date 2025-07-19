"""
Abilities formatter for ability scores and skills.

This module handles the generation of ability scores and skills sections
including ability scores, saving throws, skills, and passive scores.
"""

from typing import Dict, Any, List, Optional

# Import interfaces and utilities using absolute import
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging

from formatters.base import BaseFormatter
from utils.text import TextProcessor


class AbilitiesFormatter(BaseFormatter):
    """
    Handles abilities and skills section generation for character sheets.
    
    Generates comprehensive abilities and skills information including
    ability scores, saving throws, skill proficiencies, and passive scores.
    """
    
    def __init__(self, text_processor: TextProcessor):
        """
        Initialize the abilities formatter.
        
        Args:
            text_processor: Text processing utilities
        """
        super().__init__(text_processor)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _get_required_fields(self) -> List[str]:
        """Get list of required fields for abilities formatting."""
        return []
    
    def _validate_internal(self, character_data: Dict[str, Any]) -> bool:
        """Validate character data structure for abilities formatting."""
        ability_scores = self.get_ability_scores(character_data)
        
        # Check for required ability scores
        required_abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        for ability in required_abilities:
            if ability not in ability_scores:
                self.logger.warning(f"Missing ability score: {ability}")
                # Don't fail validation for missing abilities, just warn
        
        return True
    
    def _format_internal(self, character_data: Dict[str, Any]) -> str:
        """
        Generate comprehensive abilities and skills section.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Formatted abilities and skills section
        """
        sections = []
        
        # Header
        sections.append(self._generate_header())
        
        # Ability scores and saving throws
        sections.append(self._generate_ability_scores_section(character_data))
        
        # Passive scores
        sections.append(self._generate_passive_scores_section(character_data))
        
        # Skills
        sections.append(self._generate_skills_section(character_data))
        
        # Proficiency sources
        sections.append(self._generate_proficiency_sources_section(character_data))
        
        # Footer
        sections.append(self._generate_footer())
        
        return '\n'.join(section for section in sections if section)
    
    def _generate_header(self) -> str:
        """Generate abilities section header."""
        return "## Abilities & Skills"
    
    def _generate_ability_scores_section(self, character_data: Dict[str, Any]) -> str:
        """Generate ability scores and saving throws section."""
        ability_scores = self.get_ability_scores(character_data)
        
        # Extract ability scores
        abilities = {}
        for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
            ability_data = ability_scores.get(ability, {})
            if isinstance(ability_data, dict):
                abilities[ability] = ability_data.get('score', 10)
            else:
                abilities[ability] = ability_data
        
        # Get saving throw proficiencies from v6.0.0 structure
        proficiencies_data = character_data.get('proficiencies', {})
        saving_throw_proficiencies = proficiencies_data.get('saving_throw_proficiencies', [])
        saving_throw_profs = []
        
        # Extract saving throw names from v6.0.0 structure
        for save_prof in saving_throw_proficiencies:
            if isinstance(save_prof, dict):
                save_name = save_prof.get('name', '').lower()
                if save_name in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
                    saving_throw_profs.append(save_name)
        
        # Fallback to legacy format if v6.0.0 data not found
        if not saving_throw_profs:
            # Try combat structure
            combat_data = character_data.get('combat', {})
            saving_throws = combat_data.get('saving_throws', {})
            for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
                if saving_throws.get(ability, {}).get('proficient', False):
                    saving_throw_profs.append(ability)
            
            # Final fallback to legacy structure
            if not saving_throw_profs:
                saving_throw_profs = character_data.get('saving_throw_proficiencies', [])
        
        # Build ability scores section
        section = f"""```ability
abilities:
  strength: {abilities['strength']}
  dexterity: {abilities['dexterity']}
  constitution: {abilities['constitution']}
  intelligence: {abilities['intelligence']}
  wisdom: {abilities['wisdom']}
  charisma: {abilities['charisma']}

proficiencies:
{chr(10).join(f'  - {prof}' for prof in saving_throw_profs) if saving_throw_profs else ''}
```"""
        
        return section
    
    def _generate_passive_scores_section(self, character_data: Dict[str, Any]) -> str:
        """Generate passive scores section."""
        ability_scores = self.get_ability_scores(character_data)
        character_info = self.get_character_info(character_data)
        
        # Get ability modifiers
        wisdom_mod = ability_scores.get('wisdom', {}).get('modifier', 0)
        intel_mod = ability_scores.get('intelligence', {}).get('modifier', 0)
        
        # Get proficiency bonus from character_info
        proficiency_bonus = character_info.get('proficiency_bonus', 2)
        
        # Get passive scores from scraper data (calculated by proficiency coordinator)
        # They are stored under the proficiencies object
        proficiencies_data = character_data.get('proficiencies', {})
        passive_perception = proficiencies_data.get('passive_perception', 10)
        passive_investigation = proficiencies_data.get('passive_investigation', 10)
        passive_insight = proficiencies_data.get('passive_insight', 10)
        
        section = f"""<BR>

```badges
items:
  - label: Passive Perception
    value: {passive_perception}
  - label: Passive Investigation
    value: {passive_investigation}
  - label: Passive Insight
    value: {passive_insight}
```"""
        
        return section
    
    def _generate_skills_section(self, character_data: Dict[str, Any]) -> str:
        """Generate skills proficiencies section."""
        # Get skill proficiencies from v6.0.0 structure
        proficiencies_data = character_data.get('proficiencies', {})
        skill_proficiencies = proficiencies_data.get('skill_proficiencies', [])
        
        # Fallback to legacy structure if v6.0.0 data not found
        if not skill_proficiencies:
            skill_proficiencies = character_data.get('skill_proficiencies', [])
        ability_scores = self.get_ability_scores(character_data)
        character_info = self.get_character_info(character_data)
        
        # Get proficiency bonus from character_info
        proficiency_bonus = character_info.get('proficiency_bonus', 2)
        
        # Categorize skills
        proficient_skills = []
        expertise_skills = []
        
        # Check if we have skills data in the v6.0.0 format
        # (skills may be stored differently or not present for characters without proficiencies)
        if skill_proficiencies:
            for skill in skill_proficiencies:
                if isinstance(skill, dict) and skill.get('proficient', False):
                    skill_name = skill.get('name', '').lower()
                    
                    # Get expertise directly from scraper data - no detection logic
                    has_expertise = skill.get('expertise', False)
                    
                    if has_expertise:
                        expertise_skills.append(skill_name)
                    else:
                        proficient_skills.append(skill_name)
        
        # Build skills section - handle case where no skills are found
        if not proficient_skills and not expertise_skills:
            # Character has no skill proficiencies
            section = f"""<BR>

```skills
proficiencies:

```"""
        else:
            section = f"""<BR>

```skills
proficiencies:
{chr(10).join(f'  - {skill}' for skill in proficient_skills)}

{f'expertise:{chr(10)}{chr(10).join(f"  - {skill}" for skill in expertise_skills)}' if expertise_skills else ''}
```"""
        
        return section
    
    def _generate_proficiency_sources_section(self, character_data: Dict[str, Any]) -> str:
        """Generate proficiency sources section."""
        sources = self._generate_proficiency_sources(character_data)
        if sources:
            return f"\n{sources}"
        return ""
    
    def _generate_footer(self) -> str:
        """Generate abilities section footer."""
        return """
^abilities-skills

---"""
    
    
    
    
    
    
    
    
    
    def _generate_proficiency_sources(self, character_data: Dict[str, Any]) -> str:
        """Generate detailed proficiency sources breakdown matching backup original format."""
        # Get skill proficiencies from v6.0.0 structure
        proficiencies_data = character_data.get('proficiencies', {})
        skill_proficiencies = proficiencies_data.get('skill_proficiencies', [])
        
        # Fallback to legacy structure if v6.0.0 data not found
        if not skill_proficiencies:
            skill_proficiencies = character_data.get('skill_proficiencies', [])
        
        # Get saving throw proficiencies from v6.0.0 structure
        saving_throw_proficiencies = proficiencies_data.get('saving_throw_proficiencies', [])
        saving_throw_profs = []
        
        # Extract saving throw names from v6.0.0 structure
        for save_prof in saving_throw_proficiencies:
            if isinstance(save_prof, dict):
                save_name = save_prof.get('name', '').lower()
                if save_name in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
                    saving_throw_profs.append(save_name)
        
        # Fallback to legacy format if v6.0.0 data not found
        if not saving_throw_profs:
            # Try combat structure
            combat_data = character_data.get('combat', {})
            saving_throws = combat_data.get('saving_throws', {})
            for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
                if saving_throws.get(ability, {}).get('proficient', False):
                    saving_throw_profs.append(ability)
            
            # Final fallback to legacy structure
            if not saving_throw_profs:
                saving_throw_profs = character_data.get('saving_throw_proficiencies', [])
        
        if not skill_proficiencies and not saving_throw_profs:
            return ""
        
        # Get basic character info using proper accessor
        character_info = self.get_character_info(character_data)
        classes = character_info.get('classes', [])
        primary_class = classes[0] if classes else {}
        class_name = primary_class.get('name', 'Unknown')
        
        # Get background and species info from v6.0.0 structure
        background_data = character_info.get('background', character_data.get('background', {}))
        background_name = background_data.get('name', 'Unknown') if isinstance(background_data, dict) else 'Unknown'
        
        species_data = character_info.get('species', character_data.get('species', {}))
        species_name = species_data.get('name', 'Unknown') if isinstance(species_data, dict) else 'Unknown'
        
        # Determine species/race label based on rule version - check multiple indicators
        rule_version = character_info.get('rule_version', 'unknown')
        is_2024_rules = (
            rule_version == '2024' or 
            '2024' in str(rule_version) or
            character_info.get('classes', [{}])[0].get('is_2024', False) if character_info.get('classes') else False
        )
        species_or_race_label = 'Species' if is_2024_rules else 'Race'
        
        # Get ability modifiers and proficiency bonus for saving throw calculations
        ability_scores = self.get_ability_scores(character_data)
        proficiency_bonus = character_info.get('proficiency_bonus', 2)
        
        # Build skill bonuses list with proper source formatting
        skill_bonuses = []
        for skill in skill_proficiencies:
            if isinstance(skill, dict) and skill.get('proficient', False):
                name = skill.get('name', 'Unknown')
                source = skill.get('source', 'Unknown')
                
                # Map source names to match backup original format
                if source.lower() == 'class':
                    source = f'Class: {class_name}'
                elif source.lower() == 'background':
                    source = f'Background: {background_name}'
                elif source.lower() in ['species', 'race', 'species/race']:
                    source = f'{species_or_race_label}: {species_name}'
                
                skill_bonuses.append(f"- **{name}** ({source})")
        
        # Saving throw bonuses with actual bonus values
        save_bonuses = []
        for save in saving_throw_profs:
            if isinstance(save, str):
                ability_data = ability_scores.get(save.lower(), {})
                ability_mod = ability_data.get('modifier', 0)
                save_bonus = ability_mod + proficiency_bonus
                save_name = save.capitalize()
                save_bonuses.append(f"- **{save_name}** +{save_bonus} (Class: {class_name})")
        
        section = f"""### Proficiency Sources
> **Skill Bonuses:**
{chr(10).join(f'> {bonus}' for bonus in skill_bonuses) if skill_bonuses else '> *None*'}
>
> **Saving Throw Bonuses:**
{chr(10).join(f'> {bonus}' for bonus in save_bonuses) if save_bonuses else '> *None*'}
>
> ^proficiency-sources"""
        
        return section
    
    def format_ability_scores_only(self, character_data: Dict[str, Any]) -> str:
        """
        Format only the ability scores section.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Ability scores section only
        """
        if not self.validate_input(character_data):
            raise ValueError("Invalid character data for ability scores formatting")
        
        return self._generate_ability_scores_section(character_data)
    
    def format_skills_only(self, character_data: Dict[str, Any]) -> str:
        """
        Format only the skills section.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Skills section only
        """
        if not self.validate_input(character_data):
            raise ValueError("Invalid character data for skills formatting")
        
        return self._generate_skills_section(character_data)
    
    def get_ability_summary(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract ability scores and modifiers for summary purposes.
        
        Args:
            character_data: Complete character data dictionary
            
        Returns:
            Dictionary containing ability scores and modifiers
        """
        ability_scores = self.get_ability_scores(character_data)
        
        summary = {}
        for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
            ability_data = ability_scores.get(ability, {})
            if isinstance(ability_data, dict):
                summary[ability] = {
                    'score': ability_data.get('score', 10),
                    'modifier': ability_data.get('modifier', 0)
                }
            else:
                # Handle case where ability_data is just the score
                score = ability_data if isinstance(ability_data, int) else 10
                modifier = (score - 10) // 2
                summary[ability] = {
                    'score': score,
                    'modifier': modifier
                }
        
        return summary