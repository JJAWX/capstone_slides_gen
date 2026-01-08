from .base_agent import BaseAgent
from .prompts import REVIEW_SYSTEM, REVIEW_USER
from ..models import SlideContent
from typing import List, Dict, Any

class ReviewAgent(BaseAgent):
    """Agent specialized in reviewing and polishing the presentation."""
    
    def get_temperature(self) -> float:
        return 0.3  # Precise and critical
    
    def get_max_tokens(self) -> int:
        return 4000  # 增加到4000以完整审查所有幻灯片
    
    def get_system_prompt(self) -> str:
        return REVIEW_SYSTEM
    
    def get_user_prompt_template(self) -> str:
        return REVIEW_USER
    
    def get_fallback_result(self, **kwargs) -> Dict[str, Any]:
        # Fallback: return original slides structure (reconstructed from input logic if complex, 
        # but here we might just return empty or catch it upper level)
        return {"slides": []}
    
    async def review_slides(self, slides: List[SlideContent], title: str, audience: str) -> List[SlideContent]:
        # Serialize full objects to JSON string so LLM sees all fields
        import json
        # We strip layout from the input to the LLM to save tokens and avoid confusion, 
        # as the LLM shouldn't be editing layout indices.
        slides_data_for_llm = []
        for s in slides:
            d = s.model_dump(exclude={"layout"})
            slides_data_for_llm.append(d)
            
        slides_text = json.dumps(slides_data_for_llm, indent=2, ensure_ascii=False)
            
        result = await self.process(
            title=title,
            audience=audience,
            slides_text=slides_text
        )
        
        # Parse result back to objects
        reviewed_slides = []
        raw_slides = result.get("slides", [])
        
        # Merge Strategy:
        # If the LLM returns the same number of slides, we map them 1:1 and preserve 'layout' and 'notes' from original.
        # If the count differs, we accept the LLM's structure but we lose the specific layout assignments (they revert to None/Default).
        
        if len(raw_slides) == len(slides):
            for i, s_dict in enumerate(raw_slides):
                original = slides[i]
                
                # We need to construct the TableData object correctly if it exists
                table_data = s_dict.get("table")
                
                new_slide = SlideContent(
                    title=s_dict.get("title", original.title),
                    slideType=s_dict.get("slideType", original.slideType),
                    content=s_dict.get("content", []),
                    paragraph=s_dict.get("paragraph"),
                    image_description=s_dict.get("image_description"),
                    image_url=original.image_url,  # Preserve image URLs
                    background_image_url=original.background_image_url,  # Preserve background URLs
                    table=table_data,
                    # CRITICAL: Preserve the layout assigned by LayoutAgent
                    layout=original.layout,
                    notes=original.notes
                )
                reviewed_slides.append(new_slide)
            return reviewed_slides
            
        elif len(raw_slides) > 0:
            # Fallback for count mismatch - customized slides but layout data is lost
            for s_dict in raw_slides:
                reviewed_slides.append(SlideContent(
                    title=s_dict.get("title", "Untitled"),
                    slideType=s_dict.get("slideType", "content"),
                    content=s_dict.get("content", []),
                    paragraph=s_dict.get("paragraph"),
                    image_description=s_dict.get("image_description"),
                    table=s_dict.get("table")
                ))
            return reviewed_slides
        else:
            return slides
