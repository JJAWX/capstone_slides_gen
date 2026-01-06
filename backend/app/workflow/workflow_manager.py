from typing import Dict, Any, List
from ..agents.outline_agent import OutlineAgent
from ..agents.content_agent import ContentAgent
from ..agents.design_agent import DesignAgent
from ..agents.review_agent import ReviewAgent
from ..agents.layout_agent import LayoutAgent
from ..models import DeckRequest, SlideContent
import logging

logger = logging.getLogger(__name__)

class WorkflowManager:
    """Manages the sophisticated PPT generation workflow."""
    
    def __init__(self):
        self.outline_agent = OutlineAgent()
        self.content_agent = ContentAgent()
        self.design_agent = DesignAgent()
        self.review_agent = ReviewAgent()
        self.layout_agent = LayoutAgent()
    
    async def execute_workflow(self, deck_id: str, request: DeckRequest, storage: Dict[str, Any]) -> tuple[List[SlideContent], Dict[str, Any]]:
        """
        Execute the complete generation workflow.
        Returns: (slides, design_config)
        """
        
        # Step 1: Strategic Outline Creation (SECTIONS)
        await self._update_progress(storage, deck_id, "outline", 10, "Creating strategic outline structure...")
        outline = await self.outline_agent.generate_outline(request)
        
        # Step 2: Structure Analysis & Expansion (LAYOUT logic)
        await self._update_progress(storage, deck_id, "analyze", 20, "Analyzing structure and allocating slides...")
        slide_blueprints = self._expand_outline_to_slides(outline, request.slideCount)
        
        # Step 3: Concurrent Content Development
        await self._update_progress(storage, deck_id, "content", 35, f"Developing content for {len(slide_blueprints)} slides in parallel...")
        detailed_slides = await self.content_agent.generate_all_content(slide_blueprints, request, outline.title)
        
        # Step 4: Content Optimization
        await self._update_progress(storage, deck_id, "optimize", 50, "Optimizing content for impact...")
        optimized_content = await self._optimize_content(detailed_slides, request)
        
        # Step 5: Layout Selection (Using Manual KB)
        await self._update_progress(storage, deck_id, "layout", 65, "Selecting optimal python-pptx layouts...")
        laid_out_content = await self.layout_agent.assign_layouts_all(optimized_content)
        
        # Step 6: Visual Design
        await self._update_progress(storage, deck_id, "layout", 75, "Planning visual design scheme...")
        design_config = await self.design_agent.generate_design(request)
        
        # Step 7: Final Review & Assembly
        await self._update_progress(storage, deck_id, "review", 85, "Final quality review and assembly...")
        final_content = await self.review_agent.review_slides(laid_out_content, outline.title, request.audience)
        
        return final_content, design_config

    def _expand_outline_to_slides(self, outline, target_count: int) -> List[SlideContent]:
        """
        Expands high-level sections into individual slide blueprints based on weight.
        """
        sections = outline.sections
        total_weight = sum(s.weight for s in sections)
        
        # Reserve 1 slide for Title
        available_slides = max(1, target_count - 1)
        
        slide_blueprints = []
        
        # 1. Title Slide
        slide_blueprints.append(SlideContent(
            title=outline.title,
            content=[f"Presentation for {outline.title}"],
            slideType="title"
        ))
        
        # 2. Distribute remaining slides
        for section in sections:
            # Calculate proportion
            ratio = section.weight / total_weight
            num_slides = max(1, round(ratio * available_slides))
            
            # Create blueprints for this section
            if num_slides == 1:
                slide_blueprints.append(SlideContent(
                    title=section.title,
                    content=section.key_points, # Pass hints to content agent
                    slideType="content"
                ))
            else:
                # Split section into multiple parts
                for i in range(num_slides):
                    slide_blueprints.append(SlideContent(
                        title=f"{section.title} (Part {i+1})",
                        content=[f"Focus on part {i+1} of {section.title}. Key points: {', '.join(section.key_points)}"],
                        slideType="content"
                    ))
                    
        # Ensure we don't exceed target too much (or too little), but specific truncation isn't strict here.
        return slide_blueprints
    
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
        # For non-content slides (tables, images, narratives), we skip the bullet point optimization
        # to preserve the integrity of the generated content.
        if slide.slideType in ["table", "image", "narrative"]:
            return slide

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
            slideType=slide.slideType,
            paragraph=slide.paragraph,
            table=slide.table,
            image_description=slide.image_description,
            notes=slide.notes
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
