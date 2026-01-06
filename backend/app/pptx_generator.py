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
        # Resolve absolute paths relative to this file: backend/app/pptx_generator.py -> backend/
        base_dir = Path(__file__).resolve().parent.parent
        
        default_output = str(base_dir / "output")
        default_templates = str(base_dir / "templates")

        self.output_dir = os.getenv("OUTPUT_DIR", default_output)
        self.templates_dir = os.getenv("TEMPLATES_DIR", default_templates)

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
        title: str,
        design_config: dict = None
    ) -> str:
        """
        Create a PowerPoint presentation from slide content.
        
        Args:
            design_config: Optional output from DesignAgent with specific colors/fonts
        """
        logger.info(f"Creating presentation with {len(slides)} slides")

        # Create presentation
        prs = Presentation()
        prs.slide_width = Inches(10)
        prs.slide_height = Inches(7.5)

        # Determine colors: Use Agent config if available, fallback to template, then default
        colors = self.color_schemes.get("corporate") # default
        
        if design_config and "fonts" in design_config:
            # Could implement font selection here if OS supports it
            pass

        # Add slides
        for i, slide_content in enumerate(slides):
            # Select layout logic
            layout_idx = 1 # Default content
            if slide_content.layout:
                layout_idx = slide_content.layout.layout_idx
            elif i == 0 or slide_content.slideType == "title":
                layout_idx = 0
            
            # Create slide with dynamic layout
            try:
                layout = prs.slide_layouts[layout_idx]
            except:
                layout = prs.slide_layouts[1] # Safe fallback
                
            slide = prs.slides.add_slide(layout)
            
            # Apply content based on layout type
            self._fill_slide_content(slide, slide_content, colors, layout_idx)

        # Save presentation
        file_path = os.path.join(self.output_dir, f"{deck_id}.pptx")
        prs.save(file_path)

        logger.info(f"Presentation saved: {file_path}")
        return file_path

    def _fill_slide_content(self, slide, content: SlideContent, colors: dict, layout_idx: int):
        """
        Dynamically fill slide content based on the selected layout.
        Uses standard python-pptx placeholders (0=Title, 1=Content/Subtitle...).
        """
        
        # 1. Set Title (Almost all layouts have title at index 0)
        if slide.shapes.title:
            slide.shapes.title.text = content.title
            # Style title
            for paragraph in slide.shapes.title.text_frame.paragraphs:
                paragraph.font.size = Pt(40) if layout_idx == 0 else Pt(32)
                paragraph.font.color.rgb = colors["primary"]
                paragraph.font.bold = True
                
        # 2. Main content filling logic
        if layout_idx == 0: # Title Slide
            # Usually has subtitle at placeholder 1
            if len(slide.placeholders) > 1 and content.content:
                subtitle = slide.placeholders[1]
                subtitle.text = content.content[0]
                # Style subtitle
                for p in subtitle.text_frame.paragraphs:
                    p.font.size = Pt(24)
                    p.font.color.rgb = colors["secondary"]
                    
        elif layout_idx == 1: # Title + Content
            if len(slide.placeholders) > 1:
                body = slide.placeholders[1]
                tf = body.text_frame
                tf.clear() # Clear default prompt text
                
                for point in content.content:
                    p = tf.add_paragraph()
                    p.text = point
                    p.font.size = Pt(20)
                    p.font.color.rgb = colors["text_main"] if "text_main" in colors else colors["secondary"]
                    p.space_before = Pt(12)
                    
        elif layout_idx == 3: # Two Content
            # Left (1) and Right (2)
            left_points = content.content[:len(content.content)//2]
            right_points = content.content[len(content.content)//2:]
            
            if len(slide.placeholders) > 1:
                self._populate_text_frame(slide.placeholders[1].text_frame, left_points, colors)
            if len(slide.placeholders) > 2:
                self._populate_text_frame(slide.placeholders[2].text_frame, right_points, colors)
                
        else: # Fallback for unknown layouts - try to find any body placeholder
            if len(slide.placeholders) > 1:
                self._populate_text_frame(slide.placeholders[1].text_frame, content.content, colors)


    def _populate_text_frame(self, text_frame, points, colors):
        text_frame.clear()
        for point in points:
            p = text_frame.add_paragraph()
            p.text = point
            p.font.size = Pt(18)
            p.font.color.rgb = colors.get("secondary", RGBColor(0,0,0))
            p.space_after = Pt(10)

