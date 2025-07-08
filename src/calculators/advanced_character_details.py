"""
Advanced Character Details Extractor

Extracts comprehensive character metadata, notes, and campaign information from D&D Beyond API data.
"""

from typing import Dict, Any, Optional
import logging

from src.models.character import AdvancedCharacterDetails
from .base import RuleAwareCalculator

logger = logging.getLogger(__name__)


class AdvancedCharacterDetailsExtractor(RuleAwareCalculator):
    """
    Extracts advanced character details and metadata from D&D Beyond character data.
    
    Processes character notes, backstory, relationships, campaign information,
    and various character metadata fields.
    """
    
    def extract_advanced_details(self, raw_data: Dict[str, Any]) -> Optional[AdvancedCharacterDetails]:
        """
        Extract advanced character details from character data.
        
        Args:
            raw_data: Raw D&D Beyond character data
            
        Returns:
            AdvancedCharacterDetails object, or None if no significant data
        """
        try:
            logger.debug("Starting advanced character details extraction")
            
            # Extract character notes and backstory
            notes = raw_data.get('notes', {})
            backstory = notes.get('backstory')
            allies = notes.get('allies')
            enemies = notes.get('enemies') 
            organizations = notes.get('organizations')
            personal_possessions = notes.get('personalPossessions')
            other_holdings = notes.get('otherHoldings')
            other_notes = notes.get('otherNotes')
            
            # Extract personality traits, ideals, bonds, flaws from background
            personality_traits = self._extract_personality_traits(raw_data)
            ideals = self._extract_ideals(raw_data)
            bonds = self._extract_bonds(raw_data)
            flaws = self._extract_flaws(raw_data)
            
            # Extract campaign information
            campaign = raw_data.get('campaign', {})
            campaign_name = campaign.get('name') if campaign else None
            campaign_id = campaign.get('id') if campaign else None
            dm_name = campaign.get('dmName') if campaign else None
            
            # Extract character status
            inspiration = raw_data.get('inspiration', False)
            lifestyle = raw_data.get('lifestyle')
            alignment_id = raw_data.get('alignmentId')
            faith = raw_data.get('faith')
            current_xp = raw_data.get('currentXp', 0)
            
            # Extract meta information
            username = raw_data.get('username')
            is_assigned_to_player = raw_data.get('isAssignedToPlayer', True)
            readonly_url = raw_data.get('readonlyUrl')
            can_edit = raw_data.get('canEdit', True)
            date_modified = raw_data.get('dateModified')
            
            # Check if we have any meaningful details to preserve
            has_details = any([
                backstory, personality_traits, ideals, bonds, flaws,
                allies, enemies, organizations, personal_possessions,
                other_holdings, other_notes, campaign_name, faith,
                current_xp, username
            ])
            
            if not has_details:
                logger.debug("No significant advanced details found")
                return None
            
            # Create AdvancedCharacterDetails object
            details = AdvancedCharacterDetails(
                backstory=backstory,
                personality_traits=personality_traits,
                ideals=ideals,
                bonds=bonds,
                flaws=flaws,
                allies=allies,
                enemies=enemies,
                organizations=organizations,
                personal_possessions=personal_possessions,
                other_holdings=other_holdings,
                other_notes=other_notes,
                campaign_name=campaign_name,
                campaign_id=campaign_id,
                dm_name=dm_name,
                inspiration=inspiration,
                lifestyle=lifestyle,
                alignment_id=alignment_id,
                faith=faith,
                current_xp=current_xp,
                username=username,
                is_assigned_to_player=is_assigned_to_player,
                readonly_url=readonly_url,
                can_edit=can_edit,
                date_modified=date_modified
            )
            
            logger.info("Successfully extracted advanced character details")
            return details
            
        except Exception as e:
            logger.error(f"Error extracting advanced character details: {e}")
            return None
    
    def _extract_personality_traits(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """Extract personality traits from background data."""
        try:
            # Check traits field first
            traits = raw_data.get('traits', {})
            if traits and 'personalityTraits' in traits:
                return traits['personalityTraits']
            
            # Check background definition
            background = raw_data.get('background', {})
            background_def = background.get('definition', {}) if background else {}
            
            # Look for selected personality traits
            personality_traits = background_def.get('personalityTraits', [])
            if personality_traits:
                # Find the selected trait (may have a selection or dice roll)
                for trait in personality_traits:
                    if trait.get('selected') or trait.get('diceRoll'):
                        return trait.get('description')
                
                # If no selection, return first trait
                if personality_traits:
                    return personality_traits[0].get('description')
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting personality traits: {e}")
            return None
    
    def _extract_ideals(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """Extract ideals from background data."""
        try:
            # Check traits field first
            traits = raw_data.get('traits', {})
            if traits and 'ideals' in traits:
                return traits['ideals']
            
            # Check background definition
            background = raw_data.get('background', {})
            background_def = background.get('definition', {}) if background else {}
            
            ideals = background_def.get('ideals', [])
            if ideals:
                for ideal in ideals:
                    if ideal.get('selected') or ideal.get('diceRoll'):
                        return ideal.get('description')
                
                if ideals:
                    return ideals[0].get('description')
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting ideals: {e}")
            return None
    
    def _extract_bonds(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """Extract bonds from background data."""
        try:
            # Check traits field first
            traits = raw_data.get('traits', {})
            if traits and 'bonds' in traits:
                return traits['bonds']
            
            # Check background definition
            background = raw_data.get('background', {})
            background_def = background.get('definition', {}) if background else {}
            
            bonds = background_def.get('bonds', [])
            if bonds:
                for bond in bonds:
                    if bond.get('selected') or bond.get('diceRoll'):
                        return bond.get('description')
                
                if bonds:
                    return bonds[0].get('description')
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting bonds: {e}")
            return None
    
    def _extract_flaws(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """Extract flaws from background data."""
        try:
            # Check traits field first
            traits = raw_data.get('traits', {})
            if traits and 'flaws' in traits:
                return traits['flaws']
            
            # Check background definition
            background = raw_data.get('background', {})
            background_def = background.get('definition', {}) if background else {}
            
            flaws = background_def.get('flaws', [])
            if flaws:
                for flaw in flaws:
                    if flaw.get('selected') or flaw.get('diceRoll'):
                        return flaw.get('description')
                
                if flaws:
                    return flaws[0].get('description')
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting flaws: {e}")
            return None
    
    def has_backstory(self, details: Optional[AdvancedCharacterDetails]) -> bool:
        """Check if character has backstory information."""
        return details is not None and bool(details.backstory)
    
    def has_personality_info(self, details: Optional[AdvancedCharacterDetails]) -> bool:
        """Check if character has personality information."""
        if not details:
            return False
        
        return any([
            details.personality_traits,
            details.ideals,
            details.bonds,
            details.flaws
        ])
    
    def has_relationships(self, details: Optional[AdvancedCharacterDetails]) -> bool:
        """Check if character has relationship information."""
        if not details:
            return False
        
        return any([
            details.allies,
            details.enemies,
            details.organizations
        ])
    
    def has_campaign_info(self, details: Optional[AdvancedCharacterDetails]) -> bool:
        """Check if character has campaign information."""
        if not details:
            return False
        
        return any([
            details.campaign_name,
            details.dm_name
        ])
    
    def get_backstory_summary(self, details: Optional[AdvancedCharacterDetails], max_length: int = 200) -> str:
        """Get a truncated backstory summary."""
        if not details or not details.backstory:
            return "No backstory available."
        
        backstory = details.backstory.strip()
        if len(backstory) <= max_length:
            return backstory
        
        # Truncate and add ellipsis
        truncated = backstory[:max_length].rsplit(' ', 1)[0]
        return f"{truncated}..."
    
    def calculate(self, raw_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Calculate method required by RuleAwareCalculator base class.
        
        Returns advanced character details as a dictionary for JSON serialization.
        """
        details = self.extract_advanced_details(raw_data)
        
        return {
            'character_details': details.model_dump() if details else None,
            'has_backstory': self.has_backstory(details),
            'has_personality_info': self.has_personality_info(details),
            'has_relationships': self.has_relationships(details),
            'has_campaign_info': self.has_campaign_info(details),
            'backstory_summary': self.get_backstory_summary(details, 100) if details else None
        }