"""
Layout Adjustment Agent - Validates and adjusts slide layouts
Checks if content fits within slide boundaries and optimizes image sizes.
"""

from .base_agent import BaseAgent
from ..models import SlideContent
from typing import List, Dict, Any, Tuple
from pptx.util import Inches, Pt
import logging
import re

logger = logging.getLogger(__name__)

# PPT slide dimensions (in inches)
SLIDE_WIDTH = 10.0
SLIDE_HEIGHT = 7.5

# Safe content areas (with margins)
SAFE_LEFT = 0.5
SAFE_RIGHT = 9.5
SAFE_TOP = 1.5  # Below title
SAFE_BOTTOM = 7.0

# Maximum characters per line (approximate)
CHARS_PER_LINE = {
    40: 50,   # Pt(40) font
    32: 65,   # Pt(32) font
    24: 85,   # Pt(24) font
    20: 100,  # Pt(20) font
    18: 110,  # Pt(18) font
    16: 125,  # Pt(16) font
    14: 140,  # Pt(14) font
}

# Maximum lines per content area
MAX_LINES_CONTENT = 8
MAX_LINES_TWO_COLUMN = 6


class LayoutAdjustmentAgent:
    """
    Agent that validates and adjusts slide layouts to ensure:
    1. Text doesn't overflow the slide
    2. Images are appropriately sized
    3. Content is balanced across columns
    """
    
    def __init__(self):
        pass
    
    def _estimate_lines_needed(self, text: str, font_size: int = 18) -> int:
        """Estimate number of lines needed for text at given font size."""
        if not text:
            return 0
        
        chars_per_line = CHARS_PER_LINE.get(font_size, 100)
        return max(1, (len(text) + chars_per_line - 1) // chars_per_line)
    
    def _calculate_content_overflow(self, content: List[str], font_size: int = 18) -> Tuple[bool, int]:
        """
        Check if content will overflow the slide.
        Returns (is_overflow, lines_over)
        """
        total_lines = 0
        for point in content:
            total_lines += self._estimate_lines_needed(point, font_size)
            total_lines += 0.5  # Add spacing between points
        
        max_lines = MAX_LINES_CONTENT
        is_overflow = total_lines > max_lines
        lines_over = max(0, int(total_lines - max_lines))
        
        return is_overflow, lines_over
    
    def _calculate_optimal_font_size(self, content: List[str]) -> int:
        """Calculate optimal font size to fit content."""
        for font_size in [22, 20, 18, 16, 14]:
            is_overflow, _ = self._calculate_content_overflow(content, font_size)
            if not is_overflow:
                return font_size
        return 14  # Minimum font size
    
    def _should_use_two_columns(self, slide: SlideContent) -> bool:
        """Determine if content should be split into two columns."""
        if not slide.content:
            return False
        
        # Calculate total content length
        total_chars = sum(len(c) for c in slide.content)
        avg_chars = total_chars / len(slide.content) if slide.content else 0
        
        # Use two columns if:
        # 1. Many bullet points (>5)
        # 2. Average point length > 50 chars
        # 3. Total content length > 400 chars
        if len(slide.content) > 5:
            return True
        if avg_chars > 50:
            return True
        if total_chars > 400:
            return True
        
        return False
    
    def _calculate_image_size(
        self,
        has_content: bool,
        content_length: int,
        layout_idx: int
    ) -> Tuple[float, float]:
        """
        Calculate optimal image size based on content.
        Returns (width_inches, height_inches)
        """
        if layout_idx == 0:  # Title slide - full background
            return (SLIDE_WIDTH, SLIDE_HEIGHT)
        
        if not has_content:
            # Large centered image
            return (7.0, 4.5)
        
        if content_length > 200:
            # Small image for text-heavy slides
            return (3.0, 2.5)
        else:
            # Medium image for balanced slides
            return (4.0, 3.0)
        
        return (3.5, 2.5)
    
    def validate_and_adjust_slide(self, slide: SlideContent) -> SlideContent:
        """
        Validate a single slide and apply adjustments.
        Returns adjusted SlideContent with layout hints.
        """
        adjustments = {}
        
        # Calculate total text content
        total_chars = 0
        if slide.content:
            total_chars += sum(len(c) for c in slide.content)
        if slide.paragraph:
            total_chars += len(slide.paragraph)
        
        # Check for content overflow
        if slide.content:
            is_overflow, lines_over = self._calculate_content_overflow(slide.content)
            
            if is_overflow:
                # Option 1: Use smaller font
                optimal_font = self._calculate_optimal_font_size(slide.content)
                adjustments['recommended_font_size'] = optimal_font
                
                # Option 2: Split into two columns if still overflowing
                if self._should_use_two_columns(slide):
                    adjustments['use_two_columns'] = True
                    if slide.layout:
                        slide.layout.layout_idx = 3  # Two Content layout
                    
                logger.info(f"Slide '{slide.title}': overflow detected, font={optimal_font}pt, two_col={adjustments.get('use_two_columns', False)}")
        
        # Check paragraph overflow
        if slide.paragraph:
            lines = self._estimate_lines_needed(slide.paragraph, 20)
            if lines > MAX_LINES_CONTENT:
                # Truncate or split paragraph
                words = slide.paragraph.split()
                max_words = int(len(words) * (MAX_LINES_CONTENT / lines))
                slide.paragraph = " ".join(words[:max_words]) + "..."
                adjustments['paragraph_truncated'] = True
                logger.info(f"Slide '{slide.title}': paragraph truncated to fit")
        
        # Calculate optimal image size
        has_content = bool(slide.content or slide.paragraph)
        layout_idx = slide.layout.layout_idx if slide.layout else 1
        
        if slide.image_url or slide.image_description:
            img_width, img_height = self._calculate_image_size(
                has_content, total_chars, layout_idx
            )
            adjustments['image_width'] = img_width
            adjustments['image_height'] = img_height
        
        # Store adjustments in slide (layout_adjustments is now a model field)
        slide.layout_adjustments = adjustments
        
        return slide
    
    def validate_and_adjust_all(self, slides: List[SlideContent]) -> List[SlideContent]:
        """Validate and adjust all slides in the presentation."""
        logger.info(f"Validating layout for {len(slides)} slides")
        
        adjusted_slides = []
        for i, slide in enumerate(slides):
            adjusted = self.validate_and_adjust_slide(slide)
            adjusted_slides.append(adjusted)
            
            if hasattr(adjusted, 'layout_adjustments') and adjusted.layout_adjustments:
                logger.debug(f"Slide {i}: adjustments={adjusted.layout_adjustments}")
        
        return adjusted_slides
