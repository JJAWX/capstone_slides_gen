from .base_agent import BaseAgent
from ..models import SlideContent
from typing import List, Dict, Any, Optional
import logging
import os
import requests
import re

logger = logging.getLogger(__name__)

IMAGE_SEARCH_SYSTEM = """You are an expert at analyzing slide content and generating precise image search queries.
Your goal is to find the most relevant images for slides that lack visual content.

For each slide, you will:
1. Extract key concepts and themes from the title and content
2. Generate a specific search query that matches the slide's topic
3. Ensure the query is concrete and descriptive

Guidelines:
- Focus on the main subject matter of the slide
- Use specific nouns and adjectives
- Avoid abstract or generic terms
- Consider the professional context of presentations
- Generate 3-5 keyword phrases for optimal search results

You MUST respond with a valid JSON object."""

IMAGE_SEARCH_USER = """Analyze these slides and generate relevant image search queries.

Slides to analyze:
{slides_info}

For each slide, generate a specific image search query based on its content.
Return format:
{{
  "image_queries": [
    {{
      "slide_index": 0,
      "keywords": ["keyword1", "keyword2", "keyword3"],
      "search_query": "specific descriptive search query",
      "reasoning": "Why this image matches the slide content"
    }}
  ]
}}"""


class ImageSearchAgent(BaseAgent):
    """
    Agent specialized in finding relevant images for slides without backgrounds.
    Focuses on slides with less than 100 characters of text content.
    """
    
    def __init__(self):
        super().__init__()
        self.unsplash_access_key = os.getenv("UNSPLASH_ACCESS_KEY", "")
    
    def get_temperature(self) -> float:
        return 0.4  # Focused on precision
    
    def get_max_tokens(self) -> int:
        return 1500
    
    def get_system_prompt(self) -> str:
        return IMAGE_SEARCH_SYSTEM
    
    def get_user_prompt_template(self) -> str:
        return IMAGE_SEARCH_USER
    
    def get_fallback_result(self, **kwargs) -> Dict[str, Any]:
        return {"image_queries": []}
    
    def _count_text_length(self, slide: SlideContent) -> int:
        """Count total text length in a slide."""
        total = 0
        if slide.title:
            total += len(slide.title)
        if slide.content:
            total += sum(len(c) for c in slide.content)
        if slide.paragraph:
            total += len(slide.paragraph)
        return total
    
    def _extract_keywords_from_slide(self, slide: SlideContent) -> List[str]:
        """Extract meaningful keywords from slide content."""
        text = ""
        if slide.title:
            text += slide.title + " "
        if slide.content:
            text += " ".join(slide.content) + " "
        if slide.paragraph:
            text += slide.paragraph
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
            'it', 'its', 'they', 'them', 'their', 'we', 'our', 'you', 'your'
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        
        # Count frequency and return top keywords
        from collections import Counter
        word_counts = Counter(keywords)
        return [word for word, _ in word_counts.most_common(5)]
    
    async def search_unsplash(self, query: str) -> Optional[str]:
        """Search Unsplash API for an image matching the query."""
        if not self.unsplash_access_key:
            logger.warning("No Unsplash API key configured, using picsum fallback")
            return None
        
        try:
            url = f"https://api.unsplash.com/search/photos"
            params = {
                "query": query,
                "per_page": 1,
                "orientation": "landscape"
            }
            headers = {
                "Authorization": f"Client-ID {self.unsplash_access_key}"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get("results"):
                return data["results"][0]["urls"]["regular"]
            
        except Exception as e:
            logger.error(f"Unsplash search failed: {e}")
        
        return None
    
    def _generate_picsum_url(self, seed: str, width: int = 1600, height: int = 900) -> str:
        """Generate a deterministic picsum URL based on seed."""
        clean_seed = re.sub(r'[^a-zA-Z0-9_]', '', seed.replace(" ", "_"))
        return f"https://picsum.photos/seed/{clean_seed}/{width}/{height}"
    
    async def find_images_for_sparse_slides(
        self,
        slides: List[SlideContent],
        presentation_title: str,
        max_text_length: int = 100
    ) -> List[SlideContent]:
        """
        Find and add images to slides that:
        1. Don't have a background image
        2. Have less than max_text_length characters of text
        
        This makes sparse slides more visually appealing.
        """
        slides_to_enhance = []
        
        for i, slide in enumerate(slides):
            # Skip slides with background images
            if slide.background_image_url:
                continue
            
            # Skip slides that already have content images
            if slide.image_url:
                continue
            
            # Check text length
            text_length = self._count_text_length(slide)
            if text_length < max_text_length:
                keywords = self._extract_keywords_from_slide(slide)
                slides_to_enhance.append({
                    "slide_index": i,
                    "title": slide.title,
                    "keywords": keywords,
                    "text_length": text_length,
                    "content_snippet": (slide.content[0] if slide.content else "")[:50]
                })
        
        if not slides_to_enhance:
            logger.info("No sparse slides found that need images")
            return slides
        
        logger.info(f"Found {len(slides_to_enhance)} sparse slides to enhance with images")
        
        # Ask LLM for precise search queries
        result = await self.process(slides_info=str(slides_to_enhance))
        
        image_queries = result.get("image_queries", [])
        
        for query_info in image_queries:
            idx = query_info.get("slide_index")
            if idx is None or idx >= len(slides):
                continue
            
            search_query = query_info.get("search_query", "")
            keywords = query_info.get("keywords", [])
            
            if not search_query and keywords:
                search_query = " ".join(keywords[:3])
            
            if search_query:
                # Try Unsplash first
                image_url = await self.search_unsplash(search_query)
                
                if not image_url:
                    # Fall back to picsum with keyword-based seed
                    seed = f"{presentation_title}_{search_query}_{idx}"
                    image_url = self._generate_picsum_url(seed)
                
                slides[idx].image_url = image_url
                logger.info(f"Added image to sparse slide {idx}: {search_query}")
        
        # Fallback for slides that didn't get images from LLM
        for slide_info in slides_to_enhance:
            idx = slide_info["slide_index"]
            if not slides[idx].image_url:
                keywords = slide_info.get("keywords", [])
                if keywords:
                    seed = f"{presentation_title}_{keywords[0]}_{idx}"
                    slides[idx].image_url = self._generate_picsum_url(seed)
                    logger.info(f"Added fallback image to slide {idx}")
        
        return slides
