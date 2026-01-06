# Simplified python-pptx API Reference for Agents

PPTX_API_MANUAL = """
LIBRARY: python-pptx

KEY CONCEPTS:
1. Presentation: The root object.
   - prs = Presentation()
   - prs.slide_width, prs.slide_height (defaults to 10x7.5 inches)

2. Slide Layouts (prs.slide_layouts):
   Index | Name                | Placeholders
   ------|---------------------|---------------------------------------
   0     | Title Slide         | Title (0), Subtitle (1)
   1     | Title and Content   | Title (0), Main Content (1)
   2     | Section Header      | Title (0), Text (1)
   3     | Two Content         | Title (0), Left Content (1), Right Content (2)
   4     | Comparison          | Title (0), Left Title (1), Left Content (2), Right Title (3), Right Content (4)
   5     | Title Only          | Title (0)
   6     | Blank               | None
   7     | Content with Caption| Title (0), Content (1), Caption (2)
   8     | Picture with Caption| Title (0), Picture (1), Caption (2)

3. Shapes & Text:
   - slide.shapes.add_textbox(left, top, width, height)
   - shape.text_frame.text = "Hello"
   - shape.text_frame.paragraphs[0].font.size = Pt(24)
   - shape.text_frame.paragraphs[0].font.bold = True
   - shape.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

4. Colors:
   - text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 0, 0)
   - Solid fill: shape.fill.solid(); shape.fill.fore_color.rgb = RGBColor(0, 0, 255)

BEST PRACTICES FOR LAYOUT:
- Use Layout 0 for the very first slide (Deck Title).
- Use Layout 1 for standard bullet point slides.
- Use Layout 3 (Two Content) when comparing two items or showing Text + Image.
- Use Layout 4 (Comparison) for side-by-side lists with headers.
- Use Layout 2 (Section Header) for major transitions between topics.
"""
