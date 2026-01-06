from .base_agent import BaseAgent
from .prompts import REVIEW_SYSTEM, REVIEW_USER
from ..models import SlideContent
from typing import List, Dict, Any

class ReviewAgent(BaseAgent):
    """Agent specialized in reviewing and polishing the presentation."""
    
    def get_temperature(self) -> float:
        return 0.3  # Precise and critical
    
    def get_max_tokens(self) -> int:
        return 2000
    
    def get_system_prompt(self) -> str:
        return REVIEW_SYSTEM
    
    def get_user_prompt_template(self) -> str:
        return REVIEW_USER
    
    def get_fallback_result(self, **kwargs) -> Dict[str, Any]:
        # Fallback: return original slides structure (reconstructed from input logic if complex, 
        # but here we might just return empty or catch it upper level)
        return {"slides": []}
    
    async def review_slides(self, slides: List[SlideContent], title: str, audience: str) -> List[SlideContent]:
        # Prepare text representation for the LLM
        slides_text = ""
        for i, s in enumerate(slides):
            slides_text += f"\n--- Slide {i+1}: {s.title} ---\n"
            slides_text += "\n".join(f"- {p}" for p in s.content)
            
        result = await self.process(
            title=title,
            audience=audience,
            slides_text=slides_text
        )
        
        # Parse result back to objects
        reviewed_slides = []
        raw_slides = result.get("slides", [])
        
        # If review fails or returns partial, we might need a robust merge strategy.
        # For now, if the count matches, we use reviewed. If not, we might trust the LLM or fallback.
        if len(raw_slides) > 0:
            for s in raw_slides:
                reviewed_slides.append(SlideContent(
                    title=s.get("title", "Untitled"),
                    content=s.get("content", []),
                    slideType=s.get("slideType", "content")
                ))
            return reviewed_slides
        else:
            return slides
