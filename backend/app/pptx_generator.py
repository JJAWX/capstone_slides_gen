import os
import logging
from typing import List
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from dotenv import load_dotenv
from .models import SlideContent

# Load environment variables from backend/.env
backend_dir = Path(__file__).resolve().parent.parent
dotenv_path = backend_dir / '.env'
load_dotenv(dotenv_path=dotenv_path)

logger = logging.getLogger(__name__)


class PPTXGenerator:
    """
    Generator for PowerPoint presentations using python-pptx.
    Handles template selection and slide creation.
    """

    def __init__(self):
        self.output_dir = os.getenv("OUTPUT_DIR", "backend/output")
        self.templates_dir = os.getenv("TEMPLATES_DIR", "backend/templates")

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        # Template color schemes
        self.color_schemes = {
            "corporate": {
                "primary": RGBColor(0, 51, 102),      # Dark blue
                "secondary": RGBColor(0, 102, 204),    # Medium blue
                "accent": RGBColor(255, 153, 0)        # Orange
            },
            "academic": {
                "primary": RGBColor(51, 51, 51),       # Dark gray
                "secondary": RGBColor(102, 102, 102),  # Medium gray
                "accent": RGBColor(153, 0, 0)          # Maroon
            },
            "startup": {
                "primary": RGBColor(102, 45, 145),     # Purple
                "secondary": RGBColor(153, 102, 255),  # Light purple
                "accent": RGBColor(255, 195, 0)        # Gold
            },
            "minimal": {
                "primary": RGBColor(0, 0, 0),          # Black
                "secondary": RGBColor(128, 128, 128),  # Gray
                "accent": RGBColor(255, 255, 255)      # White
            }
        }

    async def create_presentation(
        self,
        deck_id: str,
        slides: List[SlideContent],
        template: str,
        title: str
    ) -> str:
        """
        Create a PowerPoint presentation from slide content.

        Returns:
            str: Path to the generated .pptx file
        """
        logger.info(f"Creating presentation with {len(slides)} slides")

        # Create presentation
        prs = Presentation()
        prs.slide_width = Inches(10)
        prs.slide_height = Inches(7.5)

        colors = self.color_schemes.get(template, self.color_schemes["corporate"])

        # Add slides
        for i, slide_content in enumerate(slides):
            if i == 0 or slide_content.slideType == "title":
                self._add_title_slide(prs, slide_content, colors)
            else:
                self._add_content_slide(prs, slide_content, colors)

        # Save presentation
        file_path = os.path.join(self.output_dir, f"{deck_id}.pptx")
        prs.save(file_path)

        logger.info(f"Presentation saved: {file_path}")
        return file_path

    def _add_title_slide(
        self,
        prs: Presentation,
        content: SlideContent,
        colors: dict
    ):
        """Add a title slide."""
        slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

        # Add title
        left = Inches(1)
        top = Inches(2.5)
        width = Inches(8)
        height = Inches(1.5)

        title_box = slide.shapes.add_textbox(left, top, width, height)
        title_frame = title_box.text_frame
        title_frame.text = content.title

        # Format title
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(54)
        title_para.font.bold = True
        title_para.font.color.rgb = colors["primary"]
        title_para.alignment = PP_ALIGN.CENTER

        # Add subtitle if available
        if content.content:
            subtitle_box = slide.shapes.add_textbox(
                Inches(1), Inches(4.5), Inches(8), Inches(1)
            )
            subtitle_frame = subtitle_box.text_frame
            subtitle_frame.text = content.content[0] if content.content else ""

            subtitle_para = subtitle_frame.paragraphs[0]
            subtitle_para.font.size = Pt(24)
            subtitle_para.font.color.rgb = colors["secondary"]
            subtitle_para.alignment = PP_ALIGN.CENTER

    def _add_content_slide(
        self,
        prs: Presentation,
        content: SlideContent,
        colors: dict
    ):
        """Add a content slide with bullet points."""
        slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

        # Add title
        title_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(0.5), Inches(9), Inches(0.8)
        )
        title_frame = title_box.text_frame
        title_frame.text = content.title

        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(36)
        title_para.font.bold = True
        title_para.font.color.rgb = colors["primary"]

        # Add content area
        content_box = slide.shapes.add_textbox(
            Inches(0.8), Inches(1.8), Inches(8.4), Inches(5)
        )
        text_frame = content_box.text_frame
        text_frame.word_wrap = True

        # Add bullet points
        for i, point in enumerate(content.content):
            if i == 0:
                p = text_frame.paragraphs[0]
            else:
                p = text_frame.add_paragraph()

            p.text = point
            p.level = 0
            p.font.size = Pt(20)
            p.font.color.rgb = colors["secondary"]
            p.space_before = Pt(12)
            p.space_after = Pt(12)

        # Add slide number
        slide_num_box = slide.shapes.add_textbox(
            Inches(9), Inches(7), Inches(0.5), Inches(0.3)
        )
        slide_num_frame = slide_num_box.text_frame
        slide_num_frame.text = str(len(prs.slides))

        slide_num_para = slide_num_frame.paragraphs[0]
        slide_num_para.font.size = Pt(12)
        slide_num_para.font.color.rgb = colors["secondary"]
        slide_num_para.alignment = PP_ALIGN.RIGHT

    def _add_comparison_slide(
        self,
        prs: Presentation,
        content: SlideContent,
        colors: dict
    ):
        """Add a comparison slide (two columns)."""
        # TODO: Implement comparison layout
        # For now, use content slide
        self._add_content_slide(prs, content, colors)

    def _add_data_slide(
        self,
        prs: Presentation,
        content: SlideContent,
        colors: dict
    ):
        """Add a data visualization slide."""
        # TODO: Implement data visualization
        # For now, use content slide
        self._add_content_slide(prs, content, colors)
