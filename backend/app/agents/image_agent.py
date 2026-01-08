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
            
            # AGGRESSIVE Strategy: Add images to MOST slides for engaging PPT
            # Skip only pure outline slides occasionally
            needs_image = True  # Default: give most slides images
            
            if slide.content_role == "outline":
                # Outline slides: add image every other one
                needs_image = (i % 2 == 0)
            
            if needs_image:
                slides_needing_images.append({
                    "slide_index": i,
                    "title": slide.title,
                    "content_type": slide.slideType,
                    "content_role": slide.content_role,
                    "description": slide.image_description or slide.paragraph or ", ".join(slide.content[:2]) if slide.content else slide.title
                })
                indices.append(i)
        
        if not slides_needing_images:
            logger.info("No slides need images")
            return slides
        
        logger.info(f"Requesting images for {len(slides_needing_images)} slides")
        
        # Ask LLM to generate image search queries
        result = await self.process(
            presentation_title=presentation_title,
            template=template,
            slides_info=str(slides_needing_images)
        )
        
        # Apply suggestions from LLM
        suggestions = result.get("image_suggestions", [])
        logger.info(f"Received {len(suggestions)} image suggestions from LLM")
        
        # Track which slides got images
        slides_with_images = set()
        
        for suggestion in suggestions:
            idx = suggestion.get("slide_index")
            if idx is not None and idx < len(slides):
                search_query = suggestion.get("search_query", "")
                if search_query:
                    # Use Lorem Picsum for reliable placeholder images
                    seed = f"{presentation_title[:10]}_{idx}_{search_query[:10]}".replace(" ", "_")
                    slides[idx].image_url = f"https://picsum.photos/seed/{seed}/1600/900"
                    slides_with_images.add(idx)
                    logger.info(f"Added image URL for slide {idx}: {search_query}")
        
        # FALLBACK: If LLM didn't return enough suggestions, add images anyway
        for slide_info in slides_needing_images:
            idx = slide_info["slide_index"]
            if idx not in slides_with_images and idx < len(slides):
                # Use slide title as seed for deterministic but varied images
                seed = f"{presentation_title[:8]}_{slide_info['title'][:12]}_{idx}".replace(" ", "_")
                slides[idx].image_url = f"https://picsum.photos/seed/{seed}/1600/900"
                logger.info(f"Added fallback image URL for slide {idx}")
        
        # Add background images to title slides and section dividers
        suggestions = result.get("image_suggestions", [])
        logger.info(f"Received {len(suggestions)} image suggestions")
        
        for suggestion in suggestions:
            idx = suggestion.get("slide_index")
            if idx is not None and idx < len(slides):
                search_query = suggestion.get("search_query", "")
                if search_query:
                    # Use Lorem Picsum for reliable placeholder images
                    # Each slide gets a unique random image based on slide index
                    # Format: https://picsum.photos/seed/{seed}/1600/900
                    seed = f"{presentation_title[:10]}_{idx}_{search_query[:10]}".replace(" ", "_")
                    slides[idx].image_url = f"https://picsum.photos/seed/{seed}/1600/900"
                    logger.info(f"Added image URL for slide {idx}: {search_query} -> seed={seed}")
        
        # Add background images ONLY to the first title slide
        background_query = result.get("background_query", "")
        if background_query:
            for i, slide in enumerate(slides):
                # ⚠️ 背景图片只能添加到主标题页 (slideType == "title" 且是第一张)
                if slide.slideType == "title" and i == 0:
                    bg_seed = f"bg_{presentation_title[:10]}_{i}".replace(" ", "_")
                    bg_url = f"https://picsum.photos/seed/{bg_seed}/1920/1080"
                    slides[i].background_image_url = bg_url
                    logger.info(f"Added background URL for title slide {i}")
                    break  # 只给第一张标题页添加背景
        
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
