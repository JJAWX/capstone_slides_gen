from .base_agent import BaseAgent
from ..models import SlideContent, DeckOutline
from typing import List, Dict, Any

class ContentAgent(BaseAgent):
    """Agent specialized in creating detailed slide content."""
    
    def get_temperature(self) -> float:
        return 0.8  # More creative for content
    
    def get_max_tokens(self) -> int:
        return 1500
    
    def get_system_prompt(self) -> str:
        return """You are a master content strategist for presentations.
Create engaging, concise bullet points that capture attention and deliver value.
Focus on actionable insights, compelling data, and memorable messaging."""
    
    def get_user_prompt_template(self) -> str:
        return """Create detailed content for this slide.

Slide Title: {slide_title}
Presentation Context: {presentation_title}
Current Outline: {current_content}
Audience: {audience}
Template Style: {template}

Requirements:
- 3-5 bullet points
- Each point max 15 words
- Focus on key insights and value propositions
- Use active language and strong verbs
- Consider audience's perspective and pain points

Return format:
{{
  "points": [
    "Bullet point 1",
    "Bullet point 2",
    "Bullet point 3"
  ]
}}"""
    
    def get_fallback_result(self, **kwargs) -> Dict[str, Any]:
        return {
            "points": [
                "Key insight 1",
                "Key insight 2", 
                "Key insight 3"
            ]
        }
    
    async def enhance_slide_content(self, slide: SlideContent, context: Dict) -> SlideContent:
        if slide.slideType == "title":
            return slide
        
        result = await self.process(
            slide_title=slide.title,
            presentation_title=context["title"],
            current_content=", ".join(slide.content),
            audience=context["audience"],
            template=context["template"]
        )
        
        return SlideContent(
            title=slide.title,
            content=result.get("points", slide.content),
            slideType=slide.slideType
        )
    
    async def generate_all_content(self, outline: DeckOutline, request) -> List[SlideContent]:
        context = {
            "title": outline.title,
            "audience": request.audience,
            "template": request.template
        }
        
        enhanced_slides = []
        for slide in outline.slides:
            enhanced = await self.enhance_slide_content(slide, context)
            enhanced_slides.append(enhanced)
        
        return enhanced_slides
