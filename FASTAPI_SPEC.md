# FastAPI Backend Specification

This document describes the FastAPI backend interface that the Next.js frontend expects.

## Base URL

```
http://localhost:8000
```

## Overview

The FastAPI backend is responsible for:
1. **OpenAI Integration**: Calling ChatGPT for outline generation, content planning, and text compression
2. **Text Overflow Management**: Intelligently handling text that exceeds slide boundaries
3. **PPTX Generation**: Creating PowerPoint files using python-pptx library

## Pipeline Flow

```
1. OUTLINE   → Use OpenAI to generate slide structure
2. PLAN      → Use OpenAI to plan content for each slide
3. FIX       → Compress/optimize text to fit slide constraints
4. RENDER    → Generate .pptx file using python-pptx
5. DONE      → File ready for download
```

## API Endpoints

### 1. POST /decks

Create a new deck generation task.

**Request:**
```json
{
  "prompt": "AI in Healthcare",
  "slideCount": 10,
  "audience": "business",
  "template": "corporate"
}
```

**Fields:**
- `prompt` (string, required): The presentation topic
- `slideCount` (number, required): Number of slides (5-30)
- `audience` (string, required): One of: "technical", "business", "academic", "general"
- `template` (string, required): One of: "corporate", "academic", "startup", "minimal"

**Response (201 Created):**
```json
{
  "deckId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "outline",
  "message": "Deck generation started"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "Invalid request",
  "details": "slideCount must be between 5 and 30"
}
```

---

### 2. GET /decks/{deckId}/status

Get the current status of a deck generation task.

**Response (200 OK):**
```json
{
  "deckId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "render",
  "progress": 75,
  "currentStep": "Generating slide 8 of 10"
}
```

**Fields:**
- `deckId` (string): The unique identifier
- `status` (string): One of: "outline", "plan", "fix", "render", "done", "error"
- `progress` (number, optional): Progress percentage (0-100)
- `currentStep` (string, optional): Human-readable current step
- `error` (string, optional): Error message if status is "error"

**Error Response (404 Not Found):**
```json
{
  "error": "Deck not found",
  "deckId": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 3. GET /decks/{deckId}/download

Download the generated PowerPoint file.

**Response (200 OK):**
- Content-Type: `application/vnd.openxmlformats-officedocument.presentationml.presentation`
- Content-Disposition: `attachment; filename="presentation-{deckId}.pptx"`
- Body: Binary .pptx file

**Error Response (404 Not Found):**
```json
{
  "error": "Deck not found or not ready",
  "deckId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "render"
}
```

## Implementation Requirements

### 1. OpenAI Integration

Use OpenAI ChatGPT API to:

**Outline Generation:**
```python
# Prompt example:
"Create an outline for a {slideCount}-slide presentation on {prompt}.
Target audience: {audience}.
Return JSON with slide titles and key points."
```

**Content Planning:**
```python
# For each slide, generate detailed content
"Generate content for slide titled '{title}'.
Keep text concise for PowerPoint slide.
Target audience: {audience}."
```

**Text Compression:**
```python
# If text overflows slide boundaries
"Compress the following text to fit in a PowerPoint slide:
{original_text}
Keep key points, remove redundancy."
```

### 2. Text Overflow Management

- Calculate text bounds based on slide template
- Automatically compress text if it exceeds boundaries
- Use OpenAI to intelligently summarize/reflow text
- Maintain readability and key information

### 3. PPTX Generation (python-pptx)

```python
from pptx import Presentation
from pptx.util import Inches, Pt

# Load template based on user selection
prs = Presentation(f'templates/{template}.pptx')

# Add slides programmatically
slide = prs.slides.add_slide(prs.slide_layouts[1])
title = slide.shapes.title
title.text = "Slide Title"

# Handle text fitting
text_frame = slide.shapes[1].text_frame
text_frame.text = compressed_content

# Save file
prs.save(f'output/{deckId}.pptx')
```

### 4. Template Support

Provide templates for:
- **corporate**: Professional business theme
- **academic**: Academic/research theme
- **startup**: Modern startup pitch deck
- **minimal**: Clean minimal design

### 5. Async Task Management

Since generation takes time:
1. Create task immediately and return deckId
2. Process generation in background (use Celery, FastAPI BackgroundTasks, etc.)
3. Update status as pipeline progresses
4. Store .pptx file when complete

### 6. Error Handling

Handle errors gracefully:
- OpenAI API failures → retry with exponential backoff
- Text overflow issues → auto-compress
- Template not found → use default
- Set status to "error" and include error message

## Example Implementation Structure

```python
# main.py
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid

app = FastAPI()

class DeckRequest(BaseModel):
    prompt: str
    slideCount: int
    audience: str
    template: str

# In-memory storage (use Redis/DB in production)
decks = {}

@app.post("/decks")
async def create_deck(request: DeckRequest, background_tasks: BackgroundTasks):
    deck_id = str(uuid.uuid4())
    decks[deck_id] = {"status": "outline", "progress": 0}

    # Start background task
    background_tasks.add_task(generate_deck, deck_id, request)

    return {"deckId": deck_id, "status": "outline"}

async def generate_deck(deck_id: str, request: DeckRequest):
    try:
        # 1. OUTLINE - Call OpenAI to generate structure
        update_status(deck_id, "outline", 20, "Generating outline...")
        outline = await generate_outline(request)

        # 2. PLAN - Generate content for each slide
        update_status(deck_id, "plan", 40, "Planning content...")
        content = await generate_content(outline, request)

        # 3. FIX - Handle text overflow
        update_status(deck_id, "fix", 60, "Optimizing layout...")
        optimized = await fix_overflow(content, request.template)

        # 4. RENDER - Create PPTX
        update_status(deck_id, "render", 80, "Rendering presentation...")
        file_path = await render_pptx(optimized, request.template, deck_id)

        # 5. DONE
        decks[deck_id]["status"] = "done"
        decks[deck_id]["file_path"] = file_path
        decks[deck_id]["progress"] = 100
    except Exception as e:
        decks[deck_id]["status"] = "error"
        decks[deck_id]["error"] = str(e)

@app.get("/decks/{deck_id}/status")
async def get_status(deck_id: str):
    if deck_id not in decks:
        raise HTTPException(status_code=404, detail="Deck not found")
    return {"deckId": deck_id, **decks[deck_id]}

@app.get("/decks/{deck_id}/download")
async def download_deck(deck_id: str):
    if deck_id not in decks:
        raise HTTPException(status_code=404, detail="Deck not found")

    if decks[deck_id]["status"] != "done":
        raise HTTPException(status_code=400, detail="Deck not ready")

    file_path = decks[deck_id]["file_path"]
    return FileResponse(file_path, filename=f"presentation-{deck_id}.pptx")
```

## Environment Variables

Required environment variables for FastAPI:

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
TEMPLATES_DIR=/app/templates
OUTPUT_DIR=/app/output
```

## Testing

Test the endpoints:

```bash
# Create deck
curl -X POST http://localhost:8000/decks \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "AI in Healthcare",
    "slideCount": 10,
    "audience": "business",
    "template": "corporate"
  }'

# Check status
curl http://localhost:8000/decks/{deckId}/status

# Download when done
curl -O http://localhost:8000/decks/{deckId}/download
```
