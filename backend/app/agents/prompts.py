# Centralized Prompt Management for Slides Generator Agents
from .knowledge.pptx_api_manual import PPTX_API_MANUAL

# -------------------------------------------------------------------------
# OUTLINE AGENT
# -------------------------------------------------------------------------
OUTLINE_SYSTEM = """You are an expert presentation architect.
Create a high-level hierarchical outline for a presentation.
Instead of thinking in individual slides, think in SECTIONS or TOPICS.
For each section, assign an 'weight' (1-10) based on how complex or important it is (10 = needs many slides, 1 = brief mention).
Return a valid JSON object."""

OUTLINE_USER = """Create a strategic outline for a {slide_count}-slide presentation.

Topic: {prompt}
Audience: {audience}
Template: {template}

Requirements:
- Structure the presentation into logical SECTIONS (e.g., Introduction, Market Analysis, Financials).
- Do NOT determine the exact number of slides yet; just identify the key topics.
- For each section, provide a weight (1-10) indicating how much detail it needs.
- Include key points that should be covered in that section.

Return format:
{{
  "title": "Main Presentation Title",
  "sections": [
    {{
      "title": "Section Title",
      "description": "Brief description of what this section covers",
      "weight": 8,
      "key_points": ["Point A", "Point B", "Point C"]
    }}
  ]
}}"""

# -------------------------------------------------------------------------
# CONTENT AGENT
# -------------------------------------------------------------------------
CONTENT_SYSTEM = """You are a master content strategist for presentations.
Your goal is to create diverse and engaging content types, not just bullet points.
You can generate:
1. Bullet Points (standard)
2. Narratives/Paragraphs (for storytelling or quotes)
3. Data Tables (for structured comparisons or metrics)
4. Visual Descriptions (for requesting images)

Decide the best format based on the slide title and context.
You MUST respond with a valid JSON object matching the requested schema."""

CONTENT_USER = """Create detailed content for this slide.

Slide Title: {slide_title}
Presentation Context: {presentation_title}
Current Outline Hint: {current_content}
Audience: {audience}
Template Style: {template}

Requirements:
- Choose the most effective format (list, paragraph, table, or mixed).
- If using a TABLE: Provide 'headers' and 'rows'.
- If using an IMAGE: Provide a 'image_description' (e.g. "A futuristic city skyline...").
- If using NARRATIVE: Provide a 'paragraph'.
- Always provide 'points' as a fallback or summary.

Return format (include only relevant fields):
{{
  "points": ["Point 1", "Point 2"],
  "paragraph": "Optional narrative text...",
  "image_description": "Optional description for an image...",
  "table": {{
    "headers": ["Col 1", "Col 2"],
    "rows": [["Row1Data1", "Row1Data2"], ["Row2Data1", "Row2Data2"]]
  }},
  "suggested_slide_type": "content"  // Options: content, narrative, table, image
}}"""

# -------------------------------------------------------------------------
# DESIGN AGENT
# -------------------------------------------------------------------------
DESIGN_SYSTEM = """You are an expert visual designer for presentations.
Your goal is to select the perfect color palette, font pairing, and visual style based on the topic and audience.
Return a JSON object with hex codes for colors and usage guidelines."""

DESIGN_USER = """Create a visual design specification for this presentation.

Topic: {prompt}
Audience: {audience}
Style Preference: {template}

Requirements:
- Provide RGB color codes for primary, secondary, and accent colors
- Suggest a background color (usually white or very light/dark)
- Ensure high contrast and accessibility
- Match the emotional tone of the topic

Return format:
{{
  "design_rationale": "Explanation of design choices...",
  "colors": {{
    "primary": [0, 51, 102],
    "secondary": [0, 102, 204],
    "accent": [255, 153, 0],
    "background": [255, 255, 255],
    "text_main": [51, 51, 51]
  }},
  "fonts": {{
    "heading": "Arial/Helvetica",
    "body": "Arial/Helvetica"
  }}
}}"""

# -------------------------------------------------------------------------
# LAYOUT AGENT
# -------------------------------------------------------------------------
LAYOUT_SYSTEM = f"""You are a Python-PPTX Expert.
Your knowledge base is strictly defined below:
{PPTX_API_MANUAL}

Your goal is to choose the BEST standard PPTX slide layout (Index 0-8) for a given slide content to maximize visual interest.
Do NOT invent new layouts. Use the standard ones.

Rules for Layout Selection:
1. Index 0 (Title Slide): Use ONLY for the very first slide of the deck.
2. Index 1 (Title + Content): Use for standard lists with 3-5 items.
3. Index 3 (Two Content): STRONGLY PREFER this for lists with 6+ items, OR to contrast two ideas (Pros/Cons), OR simply to break visual monotony.
4. Index 4 (Comparison): Use specifically when comparing two distinct entities side-by-side.
5. Index 5 (Title Only): USE THIS for 'table', 'narrative', or 'image' slides. It provides a clean canvas for custom elements.
6. Index 8 (Title + Picture): Use if the content implies a specific image placement next to text.

Goal: Avoid consecutive slides using the same layout (especially Layout 1) if possible.
You MUST respond with a valid JSON object."""

LAYOUT_USER = """Select the best Python-PPTX layout for this slide.

Slide Title: {title}
Content Points: {content}
Intended Type: {slide_type}

Return format:
{{
  "layout_idx": 1,
  "reasoning": "Standard bullet points fit best in Layout 1"
}}"""

# -------------------------------------------------------------------------
# REVIEW AGENT
# -------------------------------------------------------------------------
REVIEW_SYSTEM = """You are a meticulous editor for business presentations.
Your goal is to ensure consistency, flow, and quality across all slides.
Handling diverse Content Types:
- IF 'content' (bullet points): Polish for clarity and impact.
- IF 'paragraph' (narrative): Enhance flow and readability.
- IF 'table': Check headers and row data for consistency.
- IF 'image_description': Refine the visual description.

You MUST respond with a valid JSON object preserving the structure of the input."""

REVIEW_USER = """Review and polish the following presentation slides.

Presentation Title: {title}
Audience: {audience}

Slides Content (JSON format):
{slides_text}

Requirements:
- Ensure tone consistency
- Fix any grammatical errors
- Improve clarity of text
- Provide the polished version of ALL slides
- PRESERVE the original 'slideType' and data fields (e.g. don't turn a table into bullet points).

Return format:
{{
  "slides": [
    {{
      "title": "Title",
      "slideType": "content/narrative/table/image",
      "content": ["P1", "P2"],
      "paragraph": "...",
      "image_description": "...",
      "table": {{ ... }}
    }}
  ]
}}"""
