from .base_agent import BaseAgent
from .prompts import LAYOUT_SYSTEM, LAYOUT_USER
from ..models import SlideContent, SlideLayoutResponse
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class LayoutAgent(BaseAgent):
    """Agent specialized in selecting python-pptx layouts."""
    
    def get_temperature(self) -> float:
        return 0.4  # Conservative for code logic
    
    def get_max_tokens(self) -> int:
        return 1500
    
    def get_system_prompt(self) -> str:
        return LAYOUT_SYSTEM

    def get_user_prompt_template(self) -> str:
        return LAYOUT_USER
    
    def get_fallback_result(self, **kwargs) -> Dict[str, Any]:
        stype = kwargs.get("slide_type", "content")
        idx = 1
        if stype == "title": idx = 0
        elif stype == "comparison": idx = 4
        
        return {
            "layout_idx": idx,
            "reasoning": "Fallback default"
        }
    
    async def assign_layout(self, slide: SlideContent) -> SlideContent:
        result = await self.process(
            title=slide.title,
            content=slide.content,
            slide_type=slide.slideType
        )
        
        layout_info = SlideLayoutResponse(
            layout_idx=result.get("layout_idx", 1),
            notes=result.get("reasoning", "")
        )
        
        slide.layout = layout_info
        return slide
    
    async def assign_layouts_all(self, slides: List[SlideContent]) -> List[SlideContent]:
        import asyncio
        tasks = [self.assign_layout(s) for s in slides]
        return list(await asyncio.gather(*tasks))
