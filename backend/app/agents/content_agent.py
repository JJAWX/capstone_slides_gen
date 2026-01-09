from .base_agent import BaseAgent
from .prompts import CONTENT_SYSTEM, CONTENT_USER
from ..models import SlideContent, DeckRequest, TableData
from typing import List, Dict, Any

class ContentAgent(BaseAgent):
    """Agent specialized in creating detailed slide content."""
    
    def get_temperature(self) -> float:
        return 0.8  # More creative for content
    
    def get_max_tokens(self) -> int:
        return 3000  # 增加到3000以生成更丰富的内容
    
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
                "content_role": slide.content_role or "detail",  # Default to detail if not specified
                "layout_type": slide.layout_type or "bullet_points"  # Default to bullet_points
            })
            
        # Execute batch if there are items
        if batch_inputs:
            results = await self.process_batch(batch_inputs)
            
            # Map results back to slides
            for idx, result in zip(indices_to_process, results):
                if not result:
                    continue
                    
                target_slide = slides[idx]
                
                # Update layout_type if returned
                if "layout_type" in result:
                    target_slide.layout_type = result["layout_type"]
                
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
                
                # Handle chart data
                if "chart_type" in result:
                    target_slide.chart_type = result["chart_type"]
                
                # Handle quote data - only if quote_text has actual content
                quote_text = result.get("quote_text", "")
                if quote_text and len(quote_text.strip()) > 10:  # Must have substantial content
                    target_slide.paragraph = quote_text
                    quote_author = result.get("quote_author", "")
                    if quote_author and len(quote_author.strip()) > 0:
                        target_slide.paragraph += f"\n\n— {quote_author}"
                
                # Handle timeline data
                if "timeline_events" in result:
                    # Convert timeline to bullet points for now
                    events = result["timeline_events"]
                    target_slide.content = [f"{e.get('date', '')}: {e.get('title', '')} - {e.get('description', '')}" for e in events]
                
                # Handle two-column layout
                if "two_column_left" in result and "two_column_right" in result:
                    left = result["two_column_left"]
                    right = result["two_column_right"]
                    # Store in content with separator
                    target_slide.content = [f"LEFT: {p}" for p in left] + [f"RIGHT: {p}" for p in right]
                
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
                
                # CRITICAL: Validate content_role="detail" slides have content
                # detail slides should have paragraph OR substantial content
                if target_slide.content_role == "detail":
                    has_paragraph = target_slide.paragraph and len(target_slide.paragraph.strip()) >= 30
                    has_content = target_slide.content and any(len(c) > 20 for c in target_slide.content)
                    
                    if not has_paragraph and not has_content:
                        # Generate fallback content for detail slides
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Detail slide '{target_slide.title}' has no content, generating fallback")
                        target_slide.content = [
                            f"Key aspects of {target_slide.title}",
                            "Important considerations and details",
                            "Practical applications and examples",
                            "Future implications and recommendations"
                        ]
                    
                    # Ensure detail slides use narrative layout if they have paragraph
                    if has_paragraph:
                        target_slide.layout_type = "narrative"
                    
        return slides
