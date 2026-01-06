import os
import logging
from typing import List
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.dml.color import RGBColor
from dotenv import load_dotenv
from .models import SlideContent
import requests
from io import BytesIO

# Load environment variables from backend/.env
backend_dir = Path(__file__).resolve().parent.parent
dotenv_path = backend_dir / '.env'
load_dotenv(dotenv_path=dotenv_path)

logger = logging.getLogger(__name__)


class PPTXGenerator:
    """
    Generator for PowerPoint presentations using python-pptx.
    Handles template selection, slide creation, and rich content rendering.
    """

    def __init__(self):
        # Resolve absolute paths relative to this file: backend/app/pptx_generator.py -> backend/
        base_dir = Path(__file__).resolve().parent.parent
        
        default_output = str(base_dir / "output")
        default_templates = str(base_dir / "templates")

        self.output_dir = os.getenv("OUTPUT_DIR", default_output)
        self.templates_dir = os.getenv("TEMPLATES_DIR", default_templates)

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
        logger.info(f"Creating presentation with {len(slides)} slides")

        prs = Presentation()
        prs.slide_width = Inches(10)
        prs.slide_height = Inches(7.5)

        # Determine colors
        colors = self.color_schemes.get("corporate").copy() 
        
        if design_config and "colors" in design_config:
            try:
                agent_colors = design_config["colors"]
                new_colors = {}
                for key, rgb_list in agent_colors.items():
                    if isinstance(rgb_list, list) and len(rgb_list) == 3:
                        new_colors[key] = RGBColor(int(rgb_list[0]), int(rgb_list[1]), int(rgb_list[2]))
                colors.update(new_colors)
            except Exception as e:
                logger.error(f"Failed to apply design colors: {e}")

        # Add slides
        for i, slide_content in enumerate(slides):
            layout_idx = 1 # Default
            if slide_content.layout:
                layout_idx = slide_content.layout.layout_idx
            elif i == 0 or slide_content.slideType == "title":
                layout_idx = 0
            
            try:
                layout = prs.slide_layouts[layout_idx]
            except:
                layout = prs.slide_layouts[1] 
                
            slide = prs.slides.add_slide(layout)
            
            # Set background (image or color)
            if slide_content.background_image_url:
                self._set_slide_background_image(slide, slide_content.background_image_url)
            else:
                self._set_slide_background(slide, colors)
            
            self._fill_slide_content(slide, slide_content, colors, layout_idx)

        file_path = os.path.join(self.output_dir, f"{deck_id}.pptx")
        prs.save(file_path)
        logger.info(f"Presentation saved: {file_path}")
        return file_path

    def _set_slide_background(self, slide, colors: dict):
        if "background" in colors:
            try:
                bg = slide.background
                fill = bg.fill
                fill.solid()
                fill.fore_color.rgb = colors["background"]
            except Exception:
                pass

    def _fill_slide_content(self, slide, content: SlideContent, colors: dict, layout_idx: int):
        # 1. Set Title
        if slide.shapes.title:
            slide.shapes.title.text = content.title
            for paragraph in slide.shapes.title.text_frame.paragraphs:
                paragraph.font.size = Pt(36) if layout_idx == 0 else Pt(28)
                paragraph.font.color.rgb = colors.get("primary", RGBColor(0,51,102))
                paragraph.font.bold = True
                
        # 2. Main Content Logic
        
        # A. TABLE SLIDE
        if content.slideType == "table" and content.table:
            self._add_table(slide, content.table, colors)
            return

        # B. IMAGE SLIDE
        if content.slideType == "image" or content.image_description or content.image_url:
            # Try to use actual image from URL if available
            if content.image_url:
                self._add_image_from_url(slide, content.image_url)
            else:
                # Fallback to placeholder
                self._add_image_placeholder(slide, content.image_description, colors)
            
            # Add text if exists
            if content.content and len(slide.placeholders) > 1:
                 # Check if placeholder 1 is text
                 try: 
                    self._populate_text_frame(slide.placeholders[1].text_frame, content.content, colors) 
                 except: pass
            return

        # C. NARRATIVE / PARAGRAPH
        if content.paragraph:
            # Use main body placeholder if available
            if len(slide.placeholders) > 1:
                body = slide.placeholders[1]
                if hasattr(body, "text_frame"):
                    self._populate_paragraph(body.text_frame, content.paragraph, colors)
            else:
                # Fallback: Create custom textbox for Layout 5 (Title Only) or similar
                left = Inches(1.0)
                top = Inches(2.0)
                width = Inches(8.0)
                height = Inches(5.0)
                txBox = slide.shapes.add_textbox(left, top, width, height)
                self._populate_paragraph(txBox.text_frame, content.paragraph, colors)
                # Enable word wrap for the new textbox
                txBox.text_frame.word_wrap = True
            return

        # D. STANDARD LISTS (Fallback)
        if layout_idx == 0: # Title Slide
            if len(slide.placeholders) > 1 and content.content:
                subtitle = slide.placeholders[1]
                subtitle.text = content.content[0]
                for p in subtitle.text_frame.paragraphs:
                    p.font.size = Pt(20)
                    p.font.color.rgb = colors.get("secondary", RGBColor(100,100,100))
                    
        elif layout_idx == 1: # Title + Content
            if len(slide.placeholders) > 1:
                self._populate_text_frame(slide.placeholders[1].text_frame, content.content, colors)
                    
        elif layout_idx == 3: # Two Content
            left_points = content.content[:len(content.content)//2]
            right_points = content.content[len(content.content)//2:]
            
            if len(slide.placeholders) > 1:
                self._populate_text_frame(slide.placeholders[1].text_frame, left_points, colors)
            if len(slide.placeholders) > 2:
                self._populate_text_frame(slide.placeholders[2].text_frame, right_points, colors)
                
        else: # Generic Fallback
            if len(slide.placeholders) > 1:
                try: 
                    self._populate_text_frame(slide.placeholders[1].text_frame, content.content, colors)
                except AttributeError:
                    pass

    def _add_table(self, slide, table_data, colors):
        """Add a table to the slide."""
        rows = table_data.rows
        headers = table_data.headers
        if not rows or not headers: 
            return

        # Dimensions
        rows_count = len(rows) + 1
        cols_count = len(headers)
        
        # Centered table
        width = Inches(8.0)
        height = Inches(0.5 * rows_count + 0.5)
        left = Inches(1.0)
        top = Inches(2.0)

        shape = slide.shapes.add_table(rows_count, cols_count, left, top, width, height)
        table = shape.table

        # Style Headers
        for col, header_text in enumerate(headers):
            cell = table.cell(0, col)
            cell.text = str(header_text)
            cell.fill.solid()
            cell.fill.fore_color.rgb = colors.get("primary", RGBColor(0,0,0))
            for p in cell.text_frame.paragraphs:
                p.font.color.rgb = RGBColor(255,255,255)
                p.font.bold = True
                p.alignment = PP_ALIGN.CENTER

        # Style Rows
        for r, row_data in enumerate(rows):
            for c, cell_data in enumerate(row_data):
                if c < cols_count:
                    cell = table.cell(r+1, c)
                    cell.text = str(cell_data)
                    for p in cell.text_frame.paragraphs:
                        p.font.size = Pt(12)
                        p.font.color.rgb = colors.get("text_main", RGBColor(0,0,0))
                        p.alignment = PP_ALIGN.LEFT

    def _download_image(self, url: str) -> BytesIO:
        """Download image from URL and return as BytesIO object."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return BytesIO(response.content)
        except Exception as e:
            logger.error(f"Failed to download image from {url}: {e}")
            return None
    
    def _set_slide_background_image(self, slide, image_url: str):
        """Set slide background to an image from URL."""
        try:
            image_stream = self._download_image(image_url)
            if image_stream:
                # python-pptx doesn't directly support background images easily
                # Workaround: Add image as a shape covering the entire slide and send to back
                left = Inches(0)
                top = Inches(0)
                width = Inches(10)
                height = Inches(7.5)
                
                pic = slide.shapes.add_picture(image_stream, left, top, width=width, height=height)
                
                # Send to back (move to first position in shape collection)
                slide.shapes._spTree.remove(pic._element)
                slide.shapes._spTree.insert(2, pic._element)  # Insert after background
                
                logger.info(f"Added background image from {image_url}")
        except Exception as e:
            logger.error(f"Failed to set background image: {e}")
    
    def _add_image_from_url(self, slide, image_url: str):
        """Add an image from URL to the slide."""
        try:
            image_stream = self._download_image(image_url)
            if image_stream:
                # Center the image
                left = Inches(2.0)
                top = Inches(2.0)
                width = Inches(6.0)
                
                slide.shapes.add_picture(image_stream, left, top, width=width)
                logger.info(f"Added image from {image_url}")
            else:
                # Fallback to placeholder
                self._add_image_placeholder(slide, "Image unavailable", {"secondary": RGBColor(200,200,200)})
        except Exception as e:
            logger.error(f"Failed to add image from URL: {e}")
            self._add_image_placeholder(slide, f"Image error: {str(e)[:50]}", {"secondary": RGBColor(200,200,200)})

    def _add_image_placeholder(self, slide, description, colors):
        """Add a placeholder shape for an image."""
        # Add a rounded rectangle
        left = Inches(1.5)
        top = Inches(2.5)
        width = Inches(7.0)
        height = Inches(4.0)
        
        # Check if we can put it in a specific placeholder?
        # For now, custom shape
        shape = slide.shapes.add_shape(
            1, # msoShapeRectangle
            left, top, width, height
        )
        fill = shape.fill
        fill.solid()
        fill.fore_color.rgb = colors.get("secondary", RGBColor(200,200,200)) # Light gray-ish
        
        # Add text
        tf = shape.text_frame
        p = tf.paragraphs[0]
        p.text = f"[IMAGE PLACEHOLDER]\n{description}"
        p.alignment = PP_ALIGN.CENTER
        p.font.color.rgb = RGBColor(255,255,255)

    def _populate_paragraph(self, text_frame, text, colors):
        """Render a single narrative paragraph."""
        text_frame.clear()
        p = text_frame.add_paragraph()
        p.text = text
        p.font.size = Pt(18)
        p.font.color.rgb = colors.get("text_main", RGBColor(0,0,0))
        p.alignment = PP_ALIGN.JUSTIFY
        p.space_after = Pt(10)

    def _populate_text_frame(self, text_frame, points, colors):
        text_frame.clear()
        count = len(points)
        if count <= 3:
            base_size = 22
            spacing = 14
        elif count <= 5:
            base_size = 18
            spacing = 12
        else:
            base_size = 16
            spacing = 10

        for point in points:
            p = text_frame.add_paragraph()
            # "Key: Value" bolding logic
            if ":" in point and len(point.split(":")[0]) < 50:
                parts = point.split(":", 1)
                run_key = p.add_run()
                run_key.text = parts[0] + ":"
                run_key.font.bold = True
                run_key.font.size = Pt(base_size)
                run_key.font.color.rgb = colors.get("primary", RGBColor(0,0,0))
                
                run_val = p.add_run()
                run_val.text = parts[1]
                run_val.font.size = Pt(base_size)
                run_val.font.color.rgb = colors.get("text_main", RGBColor(0,0,0))
            else:
                p.text = point
                p.font.size = Pt(base_size)
                p.font.color.rgb = colors.get("text_main", colors.get("secondary", RGBColor(0,0,0)))
                if len(point) < 40 and count <= 4:
                    p.font.bold = True
            
            p.space_after = Pt(spacing)
            p.space_before = Pt(spacing/2)
