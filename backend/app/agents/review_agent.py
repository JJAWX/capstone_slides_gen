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
                
                # 获取LLM返回的content，如果为空则保留原始content
                new_content = s_dict.get("content")
                if not new_content or (isinstance(new_content, list) and len(new_content) == 0):
                    new_content = original.content  # 保留原始content
                
                # 获取LLM返回的paragraph，如果为空则保留原始
                new_paragraph = s_dict.get("paragraph")
                if not new_paragraph:
                    new_paragraph = original.paragraph
                
                new_slide = SlideContent(
                    title=s_dict.get("title", original.title),
                    slideType=s_dict.get("slideType", original.slideType),
                    content=new_content if new_content else [],
                    paragraph=new_paragraph,
                    image_description=s_dict.get("image_description") or original.image_description,
                    image_url=original.image_url,  # Preserve image URLs
                    background_image_url=original.background_image_url,  # Preserve background URLs
                    table=table_data if table_data else original.table,
                    # CRITICAL: Preserve the layout assigned by LayoutAgent
                    layout=original.layout,
                    notes=original.notes,
                    # CRITICAL: Preserve content_role and layout_type
                    content_role=original.content_role,
                    layout_type=original.layout_type,
                    chart_url=original.chart_url,
                    chart_type=original.chart_type
                )
                reviewed_slides.append(new_slide)
            return reviewed_slides
            
        elif len(raw_slides) > 0:
            # Fallback for count mismatch - 保守策略：直接返回原始slides
            # 因为数量不匹配说明LLM可能出错了，不应该用它的结果
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"ReviewAgent: 幻灯片数量不匹配 (原始: {len(slides)}, 返回: {len(raw_slides)})，保留原始内容")
            return slides
        else:
            return slides
