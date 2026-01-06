from .base_agent import BaseAgent
from ..models import DeckOutline, SlideContent
from typing import Dict, Any

class OutlineAgent(BaseAgent):
    """Agent specialized in creating presentation outlines."""
    
    def get_temperature(self) -> float:
        return 0.7  # Creative but structured
    
    def get_max_tokens(self) -> int:
        return 2000
    
    def get_system_prompt(self) -> str:
        return """You are an expert presentation architect.
Create compelling, well-structured presentation outlines that engage the target audience.
Consider storytelling flow, logical progression, and audience attention span.
Return a JSON object with title and slides array."""
    
    def get_user_prompt_template(self) -> str:
        return """Create a {slide_count}-slide presentation outline.

Topic: {prompt}
Audience: {audience}
Template: {template}

Requirements:
- First slide must be title slide
- Include mix of content types: title, content, comparison, data
- Ensure logical flow and compelling narrative
- Keep titles concise and impactful

Return format:
{{
  "title": "Presentation Title",
  "slides": [
    {{
      "title": "Slide Title",
      "content": ["Key point 1", "Key point 2"],
      "slideType": "title|content|comparison|data"
    }}
  ]
}}"""
    
    def get_fallback_result(self, **kwargs) -> Dict[str, Any]:
        return {
            "title": kwargs.get("prompt", "Presentation"),
            "slides": [
                {
                    "title": kwargs.get("prompt", "Presentation"),
                    "content": ["Professional Presentation"],
                    "slideType": "title"
                }
            ]
        }
    
    async def generate_outline(self, request) -> DeckOutline:
        result = await self.process(
            prompt=request.prompt,
            slide_count=request.slideCount,
            audience=request.audience,
            template=request.template
        )
        
        # Verify slides is a list
        raw_slides = result.get("slides", [])
        if not isinstance(raw_slides, list):
            raw_slides = []

        slides = []
        for slide in raw_slides:
            try:
                # Ensure content is a list of strings
                content = slide.get("content", [])
                if isinstance(content, str):
                    content = [content]
                elif not isinstance(content, list):
                    content = []
                    
                slides.append(SlideContent(
                    title=slide.get("title", "Slide"),
                    content=content,
                    slideType=slide.get("slideType", "content")
                ))
            except Exception:
                continue

        return DeckOutline(title=result.get("title", request.prompt), slides=slides)
