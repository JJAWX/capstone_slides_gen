from typing import Dict, Any, List
from ..agents.outline_agent import OutlineAgent
from ..agents.content_agent import ContentAgent
from ..agents.design_agent import DesignAgent
from ..agents.review_agent import ReviewAgent
from ..agents.layout_agent import LayoutAgent
from ..agents.image_agent import ImageAgent
from ..agents.image_search_agent import ImageSearchAgent
from ..agents.layout_adjustment_agent import LayoutAdjustmentAgent
from ..models import DeckRequest, SlideContent
import logging

logger = logging.getLogger(__name__)

class WorkflowManager:
    """
    Manages the sophisticated PPT generation workflow.
    
    Workflow Steps:
    1. 大纲 (Outline) - Strategic outline creation
    2. 权重布局 (Weighted Layout) - Structure analysis & slide allocation
    3. 内容生成 (Content Generation) - Parallel content development
    4. 背景嵌入 (Background Embedding) - Image suggestions
    5. 字体颜色调整 (Font Color Adjustment) - Auto contrast based on background
    6. 图片搜索 (Image Search) - Find images for sparse slides
    7. 布局调整 (Layout Adjustment) - Validate text overflow & image sizes
    8. 最终检查 (Final Review) - Quality review and polish
    9. 生成完毕 (Generation Complete)
    """
    
    def __init__(self):
        self.outline_agent = OutlineAgent()
        self.content_agent = ContentAgent()
        self.design_agent = DesignAgent()
        self.review_agent = ReviewAgent()
        self.layout_agent = LayoutAgent()
        self.image_agent = ImageAgent()
        self.image_search_agent = ImageSearchAgent()
        self.layout_adjustment_agent = LayoutAdjustmentAgent()
    
    async def execute_workflow(self, deck_id: str, request: DeckRequest, storage: Dict[str, Any]) -> tuple[List[SlideContent], Dict[str, Any]]:
        """
        Execute the complete generation workflow.
        Returns: (slides, design_config)
        """
        
        # Step 1: 大纲 - Strategic Outline Creation
        await self._update_progress(storage, deck_id, "outline", 10, "📋 Creating strategic outline structure...")
        outline = await self.outline_agent.generate_outline(request)
        
        # Step 2: 权重布局 - Structure Analysis & Expansion
        await self._update_progress(storage, deck_id, "analyze", 18, "⚖️ Analyzing structure and allocating slides by weight...")
        slide_blueprints = self._expand_outline_to_slides(outline, request.slideCount)
        
        # Step 3: 内容生成 - Concurrent Content Development
        await self._update_progress(storage, deck_id, "content", 30, f"✍️ Generating content for {len(slide_blueprints)} slides...")
        detailed_slides = await self.content_agent.generate_all_content(slide_blueprints, request, outline.title)
        
        # Step 4: Content Optimization
        await self._update_progress(storage, deck_id, "optimize", 42, "🔧 Optimizing content for impact...")
        optimized_content = await self._optimize_content(detailed_slides, request)
        
        # Step 5: Layout Selection (Using Manual KB)
        await self._update_progress(storage, deck_id, "layout", 52, "📐 Selecting optimal layouts based on content analysis...")
        laid_out_content = await self.layout_agent.assign_layouts_all(optimized_content)
        
        # Step 6: 背景嵌入 - Visual Design & Background Images
        await self._update_progress(storage, deck_id, "design", 60, "🎨 Planning visual design and background images...")
        design_config = await self.design_agent.generate_design(request)
        laid_out_content = await self.image_agent.suggest_images(laid_out_content, outline.title, request.template)
        
        # Step 7: 图片搜索 - Find images for sparse slides (< 100 chars)
        await self._update_progress(storage, deck_id, "images", 70, "🔍 Finding relevant images for sparse slides...")
        laid_out_content = await self.image_search_agent.find_images_for_sparse_slides(
            laid_out_content, 
            outline.title,
            max_text_length=100
        )
        
        # Step 8: 布局调整 - Validate & Adjust Layouts
        await self._update_progress(storage, deck_id, "adjust", 80, "📏 Validating layout and adjusting text overflow...")
        laid_out_content = self.layout_adjustment_agent.validate_and_adjust_all(laid_out_content)
        
        # Step 9: 最终检查 - Final Review & Assembly
        await self._update_progress(storage, deck_id, "review", 90, "✅ Final quality review and assembly...")
        final_content = await self.review_agent.review_slides(laid_out_content, outline.title, request.audience)
        
        return final_content, design_config

    def _expand_outline_to_slides(self, outline, target_count: int) -> List[SlideContent]:
        """
        Expands high-level sections into individual slide blueprints based on weight.
        Structure: Title -> [Section Title -> Details... -> Section Summary]... -> Final Summary
        Flexibly adapts based on allocated slide count for each section.
        """
        sections = outline.sections
        total_weight = sum(s.weight for s in sections)
        
        # Reserve 1 slide for Title + 1 for final summary
        available_slides = max(2, target_count - 2)
        
        slide_blueprints = []
        
        # 1. Title Slide
        slide_blueprints.append(SlideContent(
            title=outline.title,
            content=[f"Presentation for {outline.title}"],
            slideType="title"
        ))
        
        # 2. Distribute remaining slides to sections
        for section in sections:
            # Calculate proportion based on weight
            ratio = section.weight / total_weight
            num_slides = max(1, round(ratio * available_slides))
            
            # Adaptive Structure based on allocated slides:
            if num_slides == 1:
                # Minimal: Just section outline (bullet points)
                slide_blueprints.append(SlideContent(
                    title=section.title,
                    content=section.key_points,
                    slideType="content",
                    content_role="outline"
                ))
                
            elif num_slides == 2:
                # Small section: Section Title + 1 Detail
                slide_blueprints.append(SlideContent(
                    title=section.title,
                    content=section.key_points,
                    slideType="content",
                    content_role="outline"
                ))
                slide_blueprints.append(SlideContent(
                    title=f"{section.title} - Details",
                    content=[f"Detailed explanation of {section.title}"],
                    slideType="content",
                    content_role="detail"
                ))
                
            elif num_slides == 3:
                # Medium section: Section Title + 2 Details (no summary yet)
                slide_blueprints.append(SlideContent(
                    title=section.title,
                    content=section.key_points,
                    slideType="content",
                    content_role="outline"
                ))
                # Split key points for multiple detail slides
                num_details = 2
                for i in range(num_details):
                    slide_blueprints.append(SlideContent(
                        title=f"{section.title} - Part {i+1}",
                        content=[f"Aspect {i+1}: {section.key_points[i] if i < len(section.key_points) else 'Additional details'}"],
                        slideType="content",
                        content_role="detail"
                    ))
                    
            else:
                # Large section (4+ slides): Section Title + Details + Section Summary
                # Pattern: 1 outline + (n-2) details + 1 summary
                slide_blueprints.append(SlideContent(
                    title=section.title,
                    content=section.key_points,
                    slideType="content",
                    content_role="outline"
                ))
                
                # Add detail slides (num_slides - 2, at least 2)
                num_details = num_slides - 2
                for i in range(num_details):
                    slide_blueprints.append(SlideContent(
                        title=f"{section.title} - Part {i+1}",
                        content=[f"Aspect {i+1}: {section.key_points[i] if i < len(section.key_points) else 'Additional details'}"],
                        slideType="content",
                        content_role="detail"
                    ))
                
                # Add section summary (table)
                slide_blueprints.append(SlideContent(
                    title=f"{section.title} - Summary",
                    content=[f"Key takeaways from {section.title}"],
                    slideType="content",
                    content_role="summary"
                ))
        
        # 3. Final Summary Slide (always included)
        slide_blueprints.append(SlideContent(
            title="Conclusion",
            content=["Overall summary and key takeaways from this presentation"],
            slideType="content",
            content_role="summary"
        ))
                    
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
            image_url=slide.image_url,
            background_image_url=slide.background_image_url,
            notes=slide.notes,
            content_role=slide.content_role
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
