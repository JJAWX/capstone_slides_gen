from typing import Dict, Any, List
from ..agents.outline_agent import OutlineAgent
from ..agents.content_agent import ContentAgent
from ..agents.design_agent import DesignAgent
from ..agents.review_agent import ReviewAgent
from ..agents.layout_agent import LayoutAgent
from ..agents.image_agent import ImageAgent
from ..agents.image_search_agent import ImageSearchAgent
from ..agents.layout_adjustment_agent import LayoutAdjustmentAgent
from ..agents.chart_agent import ChartAgent
from ..utils.simple_pptx_generator import SimplePPTXGenerator
from ..models import DeckRequest, SlideContent
from pathlib import Path
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class WorkflowManager:
    """
    Manages the sophisticated PPT generation workflow.

    Workflow Steps:
    1. 大纲 (Outline) - Strategic outline creation
    2. 权重布局 (Weighted Layout) - Structure analysis & slide allocation
    3. 内容生成 (Content Generation) - Parallel content development
    4. 图表生成 (Chart Generation) - Generate data visualization charts
    5. 内容优化 (Content Optimization) - Template-specific optimizations
    6. 布局选择 (Layout Selection) - Assign optimal layouts
    7. 背景嵌入 (Background Embedding) - Visual design & image suggestions
    8. 图片搜索 (Image Search) - Find images for sparse slides
    9. 布局调整 (Layout Adjustment) - Validate text overflow & image sizes
    10. 最终检查 (Final Review) - Quality review and polish
    11. PPTX生成 (PPTX Generation) - Direct JSON to PPTX conversion using python-pptx
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
        self.chart_agent = ChartAgent()
        self.pptx_generator = SimplePPTXGenerator()
        
        # Setup output directories
        self.base_dir = Path(__file__).parent.parent.parent
        self.output_dir = self.base_dir / "output"
        self.outlines_dir = self.output_dir / "outlines"
        self.structures_dir = self.output_dir / "structures"
        self.contents_dir = self.output_dir / "contents"
        self.pptx_dir = self.output_dir / "pptx"
        
        # Ensure all directories exist
        for dir_path in [self.outlines_dir, self.structures_dir,
                         self.contents_dir, self.pptx_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    async def execute_workflow(self, deck_id: str, request: DeckRequest, storage: Dict[str, Any]) -> tuple[List[SlideContent], Dict[str, Any]]:
        """
        Execute the complete generation workflow.
        Returns: (slides, design_config)
        """
        
        # Step 1: 大纲 - Strategic Outline Creation
        await self._update_progress(storage, deck_id, "outline", 10, "📋 Creating strategic outline structure...")
        outline = await self.outline_agent.generate_outline(request)
        
        # Save outline to file
        outline_file = self._save_outline(outline, deck_id)
        logger.info(f"Saved outline to: {outline_file}")
        
        # Step 2: 权重布局 - Structure Analysis & Expansion
        await self._update_progress(storage, deck_id, "analyze", 18, "⚖️ Analyzing structure and allocating slides by weight...")
        slide_blueprints = self._expand_outline_to_slides(outline, request.slideCount)
        
        # Save structure to file
        structure_file = self._save_structure(slide_blueprints, outline.title, deck_id)
        logger.info(f"Saved structure to: {structure_file}")
        
        # Step 3: 内容生成 - Concurrent Content Development
        await self._update_progress(storage, deck_id, "content", 30, f"✍️ Generating content for {len(slide_blueprints)} slides...")
        detailed_slides = await self.content_agent.generate_all_content(slide_blueprints, request, outline.title)
        
        # Save content to files
        content_files = self._save_contents(detailed_slides, deck_id)
        logger.info(f"Saved {len(content_files)} content files")

        # Step 4: 图表生成 - Chart Generation for Data Visualization
        await self._update_progress(storage, deck_id, "charts", 36, "📊 Generating charts for data visualization...")
        slides_dict = [slide.dict() for slide in detailed_slides]
        slides_with_charts = await self.chart_agent.suggest_charts_for_slides(
            slides_dict,
            request.template,
            request.audience
        )
        # Update slides with chart data
        for i, slide in enumerate(detailed_slides):
            if i < len(slides_with_charts):
                if "chart_url" in slides_with_charts[i]:
                    slide.chart_url = slides_with_charts[i]["chart_url"]
                if "chart_type" in slides_with_charts[i]:
                    slide.chart_type = slides_with_charts[i]["chart_type"]

        # Step 5: Content Optimization
        await self._update_progress(storage, deck_id, "optimize", 42, "🔧 Optimizing content for impact...")
        optimized_content = await self._optimize_content(detailed_slides, request)

        # Step 6: Layout Selection (Using Manual KB)
        await self._update_progress(storage, deck_id, "layout", 52, "📐 Selecting optimal layouts based on content analysis...")
        laid_out_content = await self.layout_agent.assign_layouts_all(optimized_content)

        # Step 7: 背景嵌入 - Visual Design & Background Images
        await self._update_progress(storage, deck_id, "design", 60, "🎨 Planning visual design and background images...")
        design_config = await self.design_agent.generate_design(request)
        laid_out_content = await self.image_agent.suggest_images(laid_out_content, outline.title, request.template)

        # Step 8: 图片搜索 - Find images for sparse slides (< 100 chars)
        await self._update_progress(storage, deck_id, "images", 70, "🔍 Finding relevant images for sparse slides...")
        laid_out_content = await self.image_search_agent.find_images_for_sparse_slides(
            laid_out_content,
            outline.title,
            max_text_length=100
        )

        # Step 9: 布局调整 - Validate & Adjust Layouts
        await self._update_progress(storage, deck_id, "adjust", 80, "📏 Validating layout and adjusting text overflow...")
        laid_out_content = self.layout_adjustment_agent.validate_and_adjust_all(laid_out_content)

        # Step 10: 最终检查 - Final Review & Assembly
        await self._update_progress(storage, deck_id, "review", 90, "✅ Final quality review and assembly...")
        final_content = await self.review_agent.review_slides(laid_out_content, outline.title, request.audience)
        
        # Step 11: 生成PPTX - Generate PPTX directly from JSON
        await self._update_progress(storage, deck_id, "generating", 95, "🎬 Generating PPTX file...")
        pptx_path = self._generate_pptx(final_content, design_config, deck_id, outline.title, request.template)
        
        logger.info(f"✓ 工作流完成: {pptx_path}")
        
        return final_content, design_config

    def _expand_outline_to_slides(self, outline, target_count: int) -> List[SlideContent]:
        """
        Expands high-level sections into individual slide blueprints based on weight.
        Structure: Title -> [Section Title -> Details... -> Section Summary]... -> Final Summary
        Flexibly adapts based on allocated slide count for each section.
        Assigns diverse layout_types to ensure visual variety.
        """
        sections = outline.sections
        total_weight = sum(s.weight for s in sections)
        
        # Reserve 1 slide for Title + 1 for final summary
        available_slides = max(2, target_count - 2)
        
        slide_blueprints = []
        
        # Layout rotation pool for variety
        layout_pool = ["bullet_points", "narrative", "two_column", "table_data", 
                       "chart_data", "image_content", "comparison", "quote", "timeline"]
        layout_idx = 0
        
        # 1. Title Slide
        slide_blueprints.append(SlideContent(
            title=outline.title,
            content=[f"Presentation for {outline.title}"],
            slideType="title",
            layout_type="title_slide"
        ))
        
        # 2. Distribute remaining slides to sections
        for section in sections:
            # Calculate proportion based on weight
            ratio = section.weight / total_weight
            num_slides = max(1, round(ratio * available_slides))
            
            # Get suggested layouts from section if available
            suggested_layouts = getattr(section, 'suggested_layouts', None) or []
            
            # Adaptive Structure based on allocated slides:
            if num_slides == 1:
                # Minimal: Just section outline (bullet points or quote)
                layout_type = suggested_layouts[0] if suggested_layouts else "bullet_points"
                slide_blueprints.append(SlideContent(
                    title=section.title,
                    content=section.key_points,
                    slideType="content",
                    content_role="outline",
                    layout_type=layout_type
                ))
                
            elif num_slides == 2:
                # Small section: Section Title + 1 Detail with variety
                layout1 = suggested_layouts[0] if len(suggested_layouts) > 0 else "bullet_points"
                layout2 = suggested_layouts[1] if len(suggested_layouts) > 1 else layout_pool[layout_idx % len(layout_pool)]
                layout_idx += 1
                
                slide_blueprints.append(SlideContent(
                    title=section.title,
                    content=section.key_points,
                    slideType="content",
                    content_role="outline",
                    layout_type=layout1
                ))
                # Part 1 页面使用section的key_points作为上下文
                detail_hints = section.key_points[:3] if section.key_points else ["Key details to explore"]
                slide_blueprints.append(SlideContent(
                    title=f"{section.title} - Part 1",
                    content=detail_hints,
                    slideType="content",
                    content_role="detail",
                    layout_type=layout2
                ))
                
            elif num_slides == 3:
                # Medium section: Vary with outline + different detail layouts
                layouts = suggested_layouts[:3] if len(suggested_layouts) >= 3 else [
                    "bullet_points", 
                    layout_pool[layout_idx % len(layout_pool)],
                    layout_pool[(layout_idx + 1) % len(layout_pool)]
                ]
                layout_idx += 2
                
                slide_blueprints.append(SlideContent(
                    title=section.title,
                    content=section.key_points,
                    slideType="content",
                    content_role="outline",
                    layout_type=layouts[0]
                ))
                
                num_details = 2
                for i in range(num_details):
                    # 使用section的key_points作为详情页的上下文
                    detail_content = []
                    if i < len(section.key_points):
                        detail_content = [section.key_points[i]]
                        # 添加相邻的key_points作为补充上下文
                        if i + 1 < len(section.key_points):
                            detail_content.append(section.key_points[i + 1])
                    else:
                        detail_content = [f"Detailed exploration of {section.title}"]
                    
                    slide_blueprints.append(SlideContent(
                        title=f"{section.title} - Part {i+1}",
                        content=detail_content,
                        slideType="content",
                        content_role="detail",
                        layout_type=layouts[i + 1]
                    ))
                    
            else:
                # Large section (4+ slides): Maximum variety with outline + details + summary
                slide_blueprints.append(SlideContent(
                    title=section.title,
                    content=section.key_points,
                    slideType="content",
                    content_role="outline",
                    layout_type="section_divider"
                ))
                
                # Add detail slides with rotating layouts
                num_details = num_slides - 2
                for i in range(num_details):
                    # Cycle through different layout types
                    detail_layout = suggested_layouts[i + 1] if i + 1 < len(suggested_layouts) else layout_pool[layout_idx % len(layout_pool)]
                    layout_idx += 1
                    
                    # 使用section的key_points作为详情页的上下文
                    detail_content = []
                    if i < len(section.key_points):
                        detail_content = [section.key_points[i]]
                        if i + 1 < len(section.key_points):
                            detail_content.append(section.key_points[i + 1])
                    else:
                        detail_content = section.key_points[:2] if section.key_points else [f"Exploration of {section.title}"]
                    
                    slide_blueprints.append(SlideContent(
                        title=f"{section.title} - Part {i+1}",
                        content=detail_content,
                        slideType="content",
                        content_role="detail",
                        layout_type=detail_layout
                    ))
                
                # Add section summary (table)
                slide_blueprints.append(SlideContent(
                    title=f"{section.title} - Summary",
                    content=section.key_points[:4] if section.key_points else ["Key takeaways"],
                    slideType="content",
                    content_role="summary",
                    layout_type="table_data"
                ))
        
        # 3. Final Summary Slide (always included)
        slide_blueprints.append(SlideContent(
            title="Conclusion",
            content=["Overall summary and key takeaways from this presentation"],
            slideType="content",
            content_role="summary",
            layout_type="table_data"
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
            chart_url=slide.chart_url,
            chart_type=slide.chart_type,
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
    
    # ==================== 文件保存方法 ====================
    
    def _save_outline(self, outline, deck_id: str) -> Path:
        """保存大纲到JSON文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"outline_{deck_id}_{timestamp}.json"
        filepath = self.outlines_dir / filename
        
        outline_data = {
            "title": outline.title,
            "sections": [
                {
                    "title": section.title,
                    "description": section.description,
                    "weight": section.weight,
                    "key_points": section.key_points
                }
                for section in outline.sections
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(outline_data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def _save_structure(self, slide_blueprints: List[SlideContent], title: str, deck_id: str) -> Path:
        """保存幻灯片结构到JSON文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"structure_{deck_id}_{timestamp}.json"
        filepath = self.structures_dir / filename
        
        structure_data = {
            "title": title,
            "total_slides": len(slide_blueprints),
            "slides": [slide.dict() for slide in slide_blueprints]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(structure_data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def _save_contents(self, slides: List[SlideContent], deck_id: str) -> List[Path]:
        """保存每张幻灯片的内容到单独的JSON文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_files = []
        
        for idx, slide in enumerate(slides, 1):
            filename = f"content_{deck_id}_{timestamp}_slide{idx:03d}.json"
            filepath = self.contents_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(slide.dict(), f, indent=2, ensure_ascii=False)
            
            saved_files.append(filepath)
        
        return saved_files
    
    def _generate_pptx(
        self,
        slides: List[SlideContent],
        design_config: Dict[str, Any],
        deck_id: str,
        title: str,
        template: str
    ) -> Path:
        """生成最终的PPTX文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"presentation_{deck_id}_{timestamp}.pptx"
        filepath = self.pptx_dir / filename
        
        logger.info(f"开始生成PPTX: {title}")
        logger.info(f"  - 幻灯片数量: {len(slides)}")
        logger.info(f"  - 模板: {template}")
        logger.info(f"  - 输出路径: {filepath}")
        
        # 转换SlideContent列表为字典列表
        slides_data = [slide.dict() for slide in slides]
        
        # 使用SimplePPTXGenerator生成PPTX
        result_path = self.pptx_generator.generate_pptx(
            slides_data=slides_data,
            design_config=design_config,
            output_path=filepath,
            title=title,
            template=template
        )
        
        logger.info(f"✓ PPTX生成完成: {result_path}")
        
        return result_path
