from .base_agent import BaseAgent
from .prompts import CONTENT_SYSTEM, CONTENT_USER
from ..models import SlideContent, DeckRequest, TableData
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
            "points": ["Key insight 1", "Key insight 2", "Key insight 3"],
            "suggested_slide_type": "content"
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
                "template": context["template"],
                "content_role": slide.content_role or "detail"  # Default to detail if not specified
            })
            
        # Execute batch if there are items
        if batch_inputs:
            results = await self.process_batch(batch_inputs)
            
            # Map results back to slides
            for idx, result in zip(indices_to_process, results):
                if not result:
                    continue
                    
                target_slide = slides[idx]
                
                # Map basic fields
                if "points" in result:
                    target_slide.content = result["points"]
                
                # Map new extended fields
                if "paragraph" in result:
                    target_slide.paragraph = result["paragraph"]
                
                if "image_description" in result:
                    target_slide.image_description = result["image_description"]
                    
                if "table" in result and isinstance(result["table"], dict):
                    # Ensure table structure is valid
                    t_data = result["table"]
                    if "headers" in t_data and "rows" in t_data:
                        target_slide.table = TableData(headers=t_data["headers"], rows=t_data["rows"])
                
                # Update slide type if suggested
                if "suggested_slide_type" in result:
                    stype = result["suggested_slide_type"]
                    # Map simplified types to model types
                    if stype == "narrative":
                        target_slide.slideType = "narrative"
                    elif stype == "table":
                        target_slide.slideType = "table"
                    elif stype == "image":
                        target_slide.slideType = "image"
                    # else keep 'content' or existing
                    
        return slides
