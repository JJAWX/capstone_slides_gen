from typing import Dict, Any, List
from ..agents.outline_agent import OutlineAgent
from ..agents.content_agent import ContentAgent
from ..models import DeckRequest, SlideContent
import logging

logger = logging.getLogger(__name__)

class WorkflowManager:
    """Manages the sophisticated PPT generation workflow."""
    
    def __init__(self):
        self.outline_agent = OutlineAgent()
        self.content_agent = ContentAgent()
        # Future: Add more agents like LayoutAgent, ReviewAgent, etc.
    
    async def execute_workflow(self, deck_id: str, request: DeckRequest, storage: Dict[str, Any]) -> List[SlideContent]:
        """Execute the complete generation workflow."""
        
        # Step 1: Strategic Outline Creation
        await self._update_progress(storage, deck_id, "outline", 10, "Creating strategic outline...")
        outline = await self.outline_agent.generate_outline(request)
        
        # Step 2: Audience Analysis & Content Strategy
        await self._update_progress(storage, deck_id, "analyze", 20, "Analyzing audience and content strategy...")
        # Could add audience analysis agent here
        
        # Step 3: Content Development
        await self._update_progress(storage, deck_id, "content", 40, "Developing compelling content...")
        detailed_content = await self.content_agent.generate_all_content(outline, request)
        
        # Step 4: Content Optimization
        await self._update_progress(storage, deck_id, "optimize", 60, "Optimizing content for impact...")
        optimized_content = await self._optimize_content(detailed_content, request)
        
        # Step 5: Layout Planning
        await self._update_progress(storage, deck_id, "layout", 75, "Planning visual layout...")
        # Could add layout agent here
        
        # Step 6: Final Review
        await self._update_progress(storage, deck_id, "review", 85, "Final content review...")
        final_content = await self._final_review(optimized_content)
        
        return final_content
    
    async def _optimize_content(self, slides: List[SlideContent], request: DeckRequest) -> List[SlideContent]:
        """Optimize content for the specific template constraints."""
        # Template-specific optimizations
        max_words = {
            "corporate": 12,
            "academic": 18,
            "startup": 10,
            "minimal": 8
        }
        
        optimized = []
        for slide in slides:
            # Apply template-specific optimizations
            optimized_slide = self._apply_template_optimization(slide, request.template, max_words)
            optimized.append(optimized_slide)
        
        return optimized
    
    def _apply_template_optimization(self, slide: SlideContent, template: str, max_words: Dict) -> SlideContent:
        """Apply template-specific content optimizations."""
        max_w = max_words.get(template, 12)
        
        optimized_content = []
        for point in slide.content:
            words = point.split()
            if len(words) > max_w:
                # Truncate intelligently
                optimized_point = " ".join(words[:max_w]) + "..."
                optimized_content.append(optimized_point)
            else:
                optimized_content.append(point)
        
        return SlideContent(
            title=slide.title,
            content=optimized_content,
            slideType=slide.slideType
        )
    
    async def _final_review(self, slides: List[SlideContent]) -> List[SlideContent]:
        """Final quality review and adjustments."""
        # Could add a ReviewAgent here for final quality checks
        return slides
    
    async def _update_progress(self, storage: Dict[str, Any], deck_id: str, 
                             status: str, progress: int, step: str):
        """Update workflow progress."""
        if deck_id in storage:
            storage[deck_id]["status"] = status
            storage[deck_id]["progress"] = progress
            storage[deck_id]["currentStep"] = step
        logger.info(f"[{deck_id}] {step}")
