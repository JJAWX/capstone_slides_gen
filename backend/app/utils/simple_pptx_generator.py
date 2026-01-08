"""
简化的PPTX生成器 - 直接从JSON内容生成PPTX
不需要XML中间步骤
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, PP_PARAGRAPH_ALIGNMENT
from pptx.dml.color import RGBColor
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SimplePPTXGenerator:
    """直接从JSON内容生成PPTX，无需XML中间步骤"""
    
    def __init__(self):
        self.color_schemes = {
            "corporate": {
                "primary": RGBColor(0, 51, 102),
                "secondary": RGBColor(0, 102, 204),
                "accent": RGBColor(255, 153, 0),
                "text": RGBColor(51, 51, 51)
            },
            "academic": {
                "primary": RGBColor(51, 51, 51),
                "secondary": RGBColor(102, 102, 102),
                "accent": RGBColor(0, 102, 204),
                "text": RGBColor(0, 0, 0)
            },
            "startup": {
                "primary": RGBColor(138, 43, 226),
                "secondary": RGBColor(186, 85, 211),
                "accent": RGBColor(255, 215, 0),
                "text": RGBColor(33, 33, 33)
            },
            "minimal": {
                "primary": RGBColor(0, 0, 0),
                "secondary": RGBColor(128, 128, 128),
                "accent": RGBColor(0, 0, 0),
                "text": RGBColor(0, 0, 0)
            }
        }
    
    def generate_pptx(
        self,
        slides_data: List[Dict[str, Any]],
        design_config: Dict[str, Any],
        output_path: Path,
        title: str,
        template: str = "corporate"
    ) -> Path:
        """
        从幻灯片数据直接生成PPTX
        
        Args:
            slides_data: 幻灯片内容数据列表
            design_config: 设计配置
            output_path: 输出文件路径
            title: 演示文稿标题
            template: 模板类型
        
        Returns:
            生成的PPTX文件路径
        """
        
        logger.info(f"开始生成PPTX: {title}")
        logger.info(f"  - 幻灯片数量: {len(slides_data)}")
        logger.info(f"  - 模板: {template}")
        
        prs = Presentation()
        prs.slide_width = Inches(10)
        prs.slide_height = Inches(5.625)  # 16:9
        
        colors = self._get_colors(design_config, template)
        
        for idx, slide_data in enumerate(slides_data, 1):
            try:
                self._create_slide(prs, slide_data, colors, idx)
                if idx % 5 == 0:
                    logger.info(f"  已创建 {idx}/{len(slides_data)} 张幻灯片")
            except Exception as e:
                logger.error(f"  创建幻灯片 {idx} 失败: {e}")
                # 创建一个错误占位幻灯片
                self._create_error_slide(prs, idx, str(e))
        
        prs.save(str(output_path))
        
        logger.info(f"✓ PPTX生成完成!")
        logger.info(f"  - 文件路径: {output_path}")
        logger.info(f"  - 文件大小: {output_path.stat().st_size / 1024:.1f} KB")
        
        return output_path
    
    def _get_colors(self, design_config: Dict[str, Any], template: str) -> Dict[str, RGBColor]:
        """获取颜色方案"""
        
        # 如果design_config有颜色配置，使用它
        if design_config and "colors" in design_config:
            colors_data = design_config["colors"]
            try:
                return {
                    "primary": RGBColor(*colors_data.get("primary", [0, 51, 102])),
                    "secondary": RGBColor(*colors_data.get("secondary", [0, 102, 204])),
                    "accent": RGBColor(*colors_data.get("accent", [255, 153, 0])),
                    "text": RGBColor(*colors_data.get("text_main", [51, 51, 51]))
                }
            except Exception as e:
                logger.warning(f"无法解析design_config颜色: {e}, 使用默认模板")
        
        # 使用模板颜色
        return self.color_schemes.get(template, self.color_schemes["corporate"])
    
    def _create_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        colors: Dict[str, RGBColor],
        slide_number: int
    ):
        """创建单张幻灯片"""
        
        slide_type = slide_data.get("slideType", "content")
        title_text = slide_data.get("title", f"Slide {slide_number}")
        
        if slide_type == "title":
            self._create_title_slide(prs, slide_data, colors)
        elif slide_data.get("paragraph"):
            self._create_paragraph_slide(prs, slide_data, colors)
        elif slide_data.get("table"):
            self._create_table_slide(prs, slide_data, colors)
        else:
            self._create_content_slide(prs, slide_data, colors)
    
    def _create_title_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        colors: Dict[str, RGBColor]
    ):
        """创建标题页"""
        
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        
        title = slide.shapes.title
        title.text = slide_data.get("title", "")
        title.text_frame.paragraphs[0].font.size = Pt(44)
        title.text_frame.paragraphs[0].font.color.rgb = colors["primary"]
        title.text_frame.paragraphs[0].font.bold = True
        
        # 副标题
        if len(slide.placeholders) > 1:
            subtitle = slide.placeholders[1]
            content = slide_data.get("content", [])
            if content:
                subtitle.text = "\n".join(content)
                for paragraph in subtitle.text_frame.paragraphs:
                    paragraph.font.size = Pt(20)
                    paragraph.font.color.rgb = colors["text"]
    
    def _create_content_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        colors: Dict[str, RGBColor]
    ):
        """创建内容页（项目符号）"""
        
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        
        # 标题
        title = slide.shapes.title
        title.text = slide_data.get("title", "")
        title.text_frame.paragraphs[0].font.size = Pt(32)
        title.text_frame.paragraphs[0].font.color.rgb = colors["primary"]
        title.text_frame.paragraphs[0].font.bold = True
        
        # 内容
        if len(slide.placeholders) > 1:
            body = slide.placeholders[1]
            text_frame = body.text_frame
            text_frame.clear()
            
            content = slide_data.get("content", [])
            for i, point in enumerate(content):
                if i == 0:
                    p = text_frame.paragraphs[0]
                else:
                    p = text_frame.add_paragraph()
                
                p.text = point
                p.level = 0
                p.font.size = Pt(18)
                p.font.color.rgb = colors["text"]
                p.space_before = Pt(6)
                p.space_after = Pt(6)
    
    def _create_paragraph_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        colors: Dict[str, RGBColor]
    ):
        """创建段落页（narrative）"""
        
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        
        # 标题
        title = slide.shapes.title
        title.text = slide_data.get("title", "")
        title.text_frame.paragraphs[0].font.size = Pt(32)
        title.text_frame.paragraphs[0].font.color.rgb = colors["primary"]
        
        # 段落内容
        if len(slide.placeholders) > 1:
            body = slide.placeholders[1]
            text_frame = body.text_frame
            text_frame.clear()
            
            paragraph_text = slide_data.get("paragraph", "")
            p = text_frame.paragraphs[0]
            p.text = paragraph_text
            p.font.size = Pt(16)
            p.font.color.rgb = colors["text"]
            p.line_spacing = 1.5
    
    def _create_table_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        colors: Dict[str, RGBColor]
    ):
        """创建表格页"""
        
        slide = prs.slides.add_slide(prs.slide_layouts[5])  # Blank layout
        
        # 标题
        title_shape = slide.shapes.add_textbox(
            Inches(0.5), Inches(0.5),
            Inches(9), Inches(0.8)
        )
        title_frame = title_shape.text_frame
        title_frame.text = slide_data.get("title", "")
        title_frame.paragraphs[0].font.size = Pt(32)
        title_frame.paragraphs[0].font.color.rgb = colors["primary"]
        title_frame.paragraphs[0].font.bold = True
        
        # 表格
        table_data = slide_data.get("table", {})
        headers = table_data.get("headers", [])
        rows = table_data.get("rows", [])
        
        if headers and rows:
            rows_count = len(rows) + 1  # +1 for header
            cols_count = len(headers)
            
            # 创建表格
            table_shape = slide.shapes.add_table(
                rows_count, cols_count,
                Inches(0.5), Inches(1.5),
                Inches(9), Inches(3.5)
            )
            table = table_shape.table
            
            # 表头
            for col_idx, header in enumerate(headers):
                cell = table.rows[0].cells[col_idx]
                cell.text = str(header)
                cell.fill.solid()
                cell.fill.fore_color.rgb = colors["primary"]
                cell.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
                cell.text_frame.paragraphs[0].font.bold = True
                cell.text_frame.paragraphs[0].font.size = Pt(14)
            
            # 数据行
            for row_idx, row_data in enumerate(rows, 1):
                for col_idx, cell_data in enumerate(row_data):
                    cell = table.rows[row_idx].cells[col_idx]
                    cell.text = str(cell_data)
                    cell.text_frame.paragraphs[0].font.size = Pt(12)
                    cell.text_frame.paragraphs[0].font.color.rgb = colors["text"]
    
    def _create_error_slide(
        self,
        prs: Presentation,
        slide_number: int,
        error_message: str
    ):
        """创建错误占位幻灯片"""
        
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        
        title = slide.shapes.title
        title.text = f"Slide {slide_number} - Error"
        
        if len(slide.placeholders) > 1:
            body = slide.placeholders[1]
            text_frame = body.text_frame
            text_frame.text = f"Failed to generate this slide:\n{error_message}"
