from .base_agent import BaseAgent
from .prompts import IMAGE_SYSTEM, IMAGE_USER
from ..models import SlideContent
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ImageAgent(BaseAgent):
    """Agent specialized in finding and managing images for slides."""
    
    def get_temperature(self) -> float:
        return 0.5  # Balanced creativity
    
    def get_max_tokens(self) -> int:
        return 1000
    
    def get_system_prompt(self) -> str:
        return IMAGE_SYSTEM
    
    def get_user_prompt_template(self) -> str:
        return IMAGE_USER
    
    def get_fallback_result(self, **kwargs) -> Dict[str, Any]:
        return {
            "image_suggestions": []
        }
    
    async def suggest_images(self, slides: List[SlideContent], presentation_title: str, template: str) -> List[SlideContent]:
        """
        Analyze slides and suggest image URLs from Unsplash API or describe images to be generated.
        For now, we generate image search queries that can be used with Unsplash API.
        """
        # Process slides that need images
        slides_needing_images = []
        indices = []
        
        for i, slide in enumerate(slides):
            # Skip title slides and slides that already have images
            if slide.slideType == "title" or slide.image_url:
                continue
            
            # Slides with image_description need actual images
            # Also consider narrative slides that could benefit from visuals
            if slide.image_description or slide.slideType in ["image", "narrative"]:
                slides_needing_images.append({
                    "slide_index": i,
                    "title": slide.title,
                    "content_type": slide.slideType,
                    "description": slide.image_description or slide.paragraph or ", ".join(slide.content[:2])
                })
                indices.append(i)
        
        if not slides_needing_images:
            return slides
        
        # Ask LLM to generate Unsplash search queries
        result = await self.process(
            presentation_title=presentation_title,
            template=template,
            slides_info=str(slides_needing_images)
        )
        
        # Apply suggestions
        suggestions = result.get("image_suggestions", [])
        for suggestion in suggestions:
            idx = suggestion.get("slide_index")
            if idx is not None and idx < len(slides):
                search_query = suggestion.get("search_query", "")
                # For now, we construct Unsplash URL
                # In production, you'd call Unsplash API to get actual image
                if search_query:
                    # Unsplash Source API for demo purposes
                    # Format: https://source.unsplash.com/1600x900/?{query}
                    slides[idx].image_url = f"https://source.unsplash.com/1600x900/?{search_query.replace(' ', ',')}"
                    logger.info(f"Suggested image for slide {idx}: {search_query}")
        
        return slides
    
    async def suggest_background(self, template: str, presentation_title: str) -> str:
        """
        Suggest a background image URL based on template and presentation theme.
        Returns an Unsplash URL or empty string.
        """
        result = await self.process(
            presentation_title=presentation_title,
            template=template,
            slides_info="Background image request"
        )
        
        bg_query = result.get("background_query", "")
        if bg_query:
            # Return subtle background image
            return f"https://source.unsplash.com/1920x1080/?{bg_query.replace(' ', ',')},subtle,minimal"
        
        return ""
