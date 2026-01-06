from .base_agent import BaseAgent
from .prompts import CONTENT_SYSTEM, CONTENT_USER
from ..models import SlideContent, DeckRequest
from typing import List, Dict, Any

class ContentAgent(BaseAgent):
    """Agent specialized in creating detailed slide content."""
    
    def get_temperature(self) -> float:
        return 0.8  # More creative for content
    
    def get_max_tokens(self) -> int:
        return 1500
    
    def get_system_prompt(self) -> str:
        return CONTENT_SYSTEM
    
    def get_user_prompt_template(self) -> str:
        return CONTENT_USER
    
    def get_fallback_result(self, **kwargs) -> Dict[str, Any]:
        return {
            "points": [
                "Key insight 1",
                "Key insight 2", 
                "Key insight 3"
            ]
        }
    
    async def generate_all_content(self, slides: List[SlideContent], request: DeckRequest, deck_title: str) -> List[SlideContent]:
        context = {
            "title": deck_title,
            "audience": request.audience,
            "template": request.template
        }
        
        # Prepare batch inputs for non-title slides
        indices_to_process = []
        batch_inputs = []
        
        for i, slide in enumerate(slides):
            if slide.slideType == "title":
                continue
            
            indices_to_process.append(i)
            batch_inputs.append({
                "slide_title": slide.title,
                "presentation_title": context["title"],
                "current_content": ", ".join(slide.content) if slide.content else "",
                "audience": context["audience"],
                "template": context["template"]
            })
            
        # Execute batch if there are items
        if batch_inputs:
            results = await self.process_batch(batch_inputs)
            
            # Map results back to slides
            for idx, result in zip(indices_to_process, results):
                if result and "points" in result:
                    slides[idx].content = result["points"]
                    
        return slides
