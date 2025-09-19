"""
Character Appearance Extractor

Extracts character appearance and visual details from D&D Beyond API data.
"""

from typing import Dict, Any, Optional
import logging

from shared.models.character import CharacterAppearance
from .base import RuleAwareCalculator

logger = logging.getLogger(__name__)


class CharacterAppearanceExtractor(RuleAwareCalculator):
    """
    Extracts character appearance and visual details from D&D Beyond character data.
    
    Processes physical descriptions, avatar URLs, and appearance customization details.
    """
    
    def extract_character_appearance(self, raw_data: Dict[str, Any]) -> Optional[CharacterAppearance]:
        """
        Extract character appearance from character data.
        
        Args:
            raw_data: Raw D&D Beyond character data
            
        Returns:
            CharacterAppearance object with visual details, or None if minimal data
        """
        try:
            logger.debug("Starting character appearance extraction")
            
            # Extract basic physical description
            gender = raw_data.get('gender')
            age = raw_data.get('age')
            height = raw_data.get('height')
            # Convert weight to string if it's a number
            weight = raw_data.get('weight')
            if isinstance(weight, (int, float)):
                weight = str(weight)
            hair = raw_data.get('hair')
            eyes = raw_data.get('eyes')
            skin = raw_data.get('skin')
            
            # Extract narrative appearance description from traits
            appearance_description = None
            traits = raw_data.get('traits', {})
            if isinstance(traits, dict):
                appearance_description = traits.get('appearance')
            
            # Extract decorations (avatar and imagery)
            decorations = raw_data.get('decorations', {})
            
            # Extract avatar URLs
            avatar_url = decorations.get('avatarUrl')
            portrait_avatar_url = self._get_portrait_avatar_url(raw_data)
            frame_avatar_url = decorations.get('frameAvatarUrl')
            backdrop_avatar_url = decorations.get('backdropAvatarUrl')
            small_backdrop_avatar_url = decorations.get('smallBackdropAvatarUrl')
            large_backdrop_avatar_url = decorations.get('largeBackdropAvatarUrl')
            thumbnail_backdrop_avatar_url = decorations.get('thumbnailBackdropAvatarUrl')
            
            # Extract avatar IDs and decoration keys
            avatar_id = decorations.get('avatarId')
            portrait_decoration_key = decorations.get('portraitDecorationKey')
            frame_avatar_decoration_key = decorations.get('frameAvatarDecorationKey')
            backdrop_avatar_decoration_key = decorations.get('backdropAvatarDecorationKey')
            # Extract theme_color - handle both string and dict formats
            theme_color = decorations.get('themeColor')
            if isinstance(theme_color, dict):
                theme_color = theme_color.get('decorationKey')  # Extract the key from the dict
            
            # Extract default backdrop information
            default_backdrop = decorations.get('defaultBackdrop')
            
            # Check if we have any meaningful appearance data
            has_appearance_data = any([
                gender, age, height, weight, hair, eyes, skin,
                appearance_description, avatar_url, portrait_avatar_url, 
                frame_avatar_url, backdrop_avatar_url, avatar_id, theme_color
            ])
            
            if not has_appearance_data:
                logger.debug("No significant appearance data found")
                return None
            
            # Create CharacterAppearance object
            appearance = CharacterAppearance(
                gender=gender,
                age=age,
                height=height,
                weight=weight,
                hair=hair,
                eyes=eyes,
                skin=skin,
                appearance_description=appearance_description,
                avatar_url=avatar_url,
                portrait_avatar_url=portrait_avatar_url,
                frame_avatar_url=frame_avatar_url,
                backdrop_avatar_url=backdrop_avatar_url,
                small_backdrop_avatar_url=small_backdrop_avatar_url,
                large_backdrop_avatar_url=large_backdrop_avatar_url,
                thumbnail_backdrop_avatar_url=thumbnail_backdrop_avatar_url,
                avatar_id=avatar_id,
                portrait_decoration_key=portrait_decoration_key,
                frame_avatar_decoration_key=frame_avatar_decoration_key,
                backdrop_avatar_decoration_key=backdrop_avatar_decoration_key,
                theme_color=theme_color,
                default_backdrop=default_backdrop
            )
            
            logger.info("Successfully extracted character appearance")
            return appearance
            
        except Exception as e:
            logger.error(f"Error extracting character appearance: {e}")
            return None
    
    def _get_portrait_avatar_url(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """
        Get portrait avatar URL from various possible locations.
        
        Portrait avatars may be in decorations or race definition.
        """
        try:
            # Check decorations first
            decorations = raw_data.get('decorations', {})
            if 'portraitAvatarUrl' in decorations:
                return decorations['portraitAvatarUrl']
            
            # Check race definition
            race = raw_data.get('race', {})
            if 'portraitAvatarUrl' in race:
                return race['portraitAvatarUrl']
            
            # Check if there's a portrait URL in the race definition
            race_definition = race.get('definition', {}) if isinstance(race, dict) else {}
            if 'portraitAvatarUrl' in race_definition:
                return race_definition['portraitAvatarUrl']
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting portrait avatar URL: {e}")
            return None
    
    def has_custom_appearance(self, appearance: Optional[CharacterAppearance]) -> bool:
        """Check if character has custom appearance details."""
        if not appearance:
            return False
        
        # Check for custom physical descriptions
        physical_details = [
            appearance.hair, appearance.eyes, appearance.skin,
            appearance.height, appearance.weight
        ]
        
        return any(detail for detail in physical_details)
    
    def has_custom_avatar(self, appearance: Optional[CharacterAppearance]) -> bool:
        """Check if character has custom avatar."""
        if not appearance:
            return False
        
        return appearance.avatar_url is not None
    
    def get_best_avatar_url(self, appearance: Optional[CharacterAppearance]) -> Optional[str]:
        """Get the best available avatar URL."""
        if not appearance:
            return None
        
        # Prefer custom avatar, then portrait, then race default
        avatar_urls = [
            appearance.avatar_url,
            appearance.portrait_avatar_url,
            appearance.large_backdrop_avatar_url,
            appearance.backdrop_avatar_url
        ]
        
        return next((url for url in avatar_urls if url), None)
    
    def get_physical_description_summary(self, appearance: Optional[CharacterAppearance]) -> str:
        """Get a formatted physical description summary."""
        if not appearance:
            return "No physical description available."
        
        parts = []
        
        if appearance.gender:
            parts.append(f"Gender: {appearance.gender}")
        
        if appearance.age:
            parts.append(f"Age: {appearance.age}")
        
        if appearance.height:
            parts.append(f"Height: {appearance.height}")
        
        if appearance.weight:
            parts.append(f"Weight: {appearance.weight}")
        
        if appearance.hair:
            parts.append(f"Hair: {appearance.hair}")
        
        if appearance.eyes:
            parts.append(f"Eyes: {appearance.eyes}")
        
        if appearance.skin:
            parts.append(f"Skin: {appearance.skin}")
        
        if not parts:
            return "No physical description available."
        
        return "; ".join(parts)
    
    def calculate(self, raw_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Calculate method required by RuleAwareCalculator base class.
        
        Returns character appearance as a dictionary for JSON serialization.
        """
        appearance = self.extract_character_appearance(raw_data)
        
        result = {
            'appearance': appearance.model_dump() if appearance else None,
            'has_custom_appearance': self.has_custom_appearance(appearance),
            'has_custom_avatar': self.has_custom_avatar(appearance),
            'best_avatar_url': self.get_best_avatar_url(appearance),
            'physical_description': self.get_physical_description_summary(appearance)
        }
        
        return result