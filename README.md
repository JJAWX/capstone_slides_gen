# Intelligent Slides Generator

An AI-powered presentation generator that creates professional PowerPoint slides (.pptx) with well-structured content and visual design.

## Architecture

```
Browser (Next.js UI)
  ↓ call /api/decks (same origin)
Next.js Route Handlers (BFF)
  ↓ call FastAPI http://localhost:8000
FastAPI Pipeline
  - OpenAI outline/plan/compress
  - python-pptx render
  ↓ returns deckId/status/file
```

## Project Structure

```
.
├── src/                            # Next.js Frontend
│   ├── app/
│   │   ├── page.tsx                # Main UI page
│   │   ├── layout.tsx              # Root layout with Ant Design
│   │   └── api/
│   │       └── decks/
│   │           ├── route.ts        # POST /api/decks
│   │           └── [id]/
│   │               ├── status/
│   │               │   └── route.ts    # GET /api/decks/:id/status
│   │               └── download/
│   │                   └── route.ts    # GET /api/decks/:id/download
│   ├── components/
│   │   ├── DeckForm.tsx            # Form for creating presentations
│   │   └── DeckStatus.tsx          # Progress tracker and download
│   └── lib/
│       └── types.ts                # TypeScript type definitions
│
└── backend/                        # FastAPI Backend
    ├── app/
    │   ├── main.py                 # FastAPI application
    │   ├── models.py               # Pydantic models
    │   ├── deck_generator.py       # Generation pipeline
    │   ├── openai_client.py        # OpenAI integration
    │   └── pptx_generator.py       # PowerPoint generation
    ├── templates/                  # PowerPoint templates
    ├── output/                     # Generated .pptx files
    └── requirements.txt            # Python dependencies
```

## Features

- **Professional Output**: Generate clean, professional .pptx files
- **Smart Layout**: Intelligently manage text length and layout constraints
- **Template Support**: Apply professional templates and maintain design consistency
- **Multiple Slide Types**: Handle various slide types (title, content, comparison, data visualization)

## Prerequisites

- **Node.js** 20+
- **Python** 3.11+
- **OpenAI API Key**

## Getting Started

### Backend Setup (FastAPI)

#### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

#### 2. Configure Backend Environment

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview
```

#### 3. Run FastAPI Server

```bash
# From backend directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or from project root
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend API will be available at http://localhost:8000

📚 **Backend API Documentation**: http://localhost:8000/docs

### Frontend Setup (Next.js)

#### 1. Install Node Dependencies

```bash
npm install
```

#### 2. Configure Frontend Environment

```bash
cp .env.example .env.local
```

Edit `.env.local`:

```
FASTAPI_URL=http://localhost:8000
```

#### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3001](http://localhost:3001) in your browser.

### Running Both Servers

You need to run both servers simultaneously:

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
npm run dev
```

## API Routes

### POST /api/decks
Create a new presentation generation task.

**Request Body:**
```json
{
  "prompt": "AI in Healthcare",
  "slideCount": 10,
  "audience": "business",
  "template": "corporate"
}
```

**Response:**
```json
{
  "deckId": "uuid",
  "status": "outline"
}
```

### GET /api/decks/:id/status
Get the current status of a presentation generation task.

**Response:**
```json
{
  "deckId": "uuid",
  "status": "render",
  "progress": 75,
  "currentStep": "Generating slide 8 of 10"
}
```

**Status Values:**
- `outline`: Creating presentation structure
- `plan`: Planning slide content
- `fix`: Optimizing layout and text
- `render`: Generating PowerPoint file
- `done`: Presentation ready
- `error`: Generation failed

### GET /api/decks/:id/download
Download the generated PowerPoint file.

**Response:** Binary .pptx file

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **UI Library**: Ant Design 5
- **Language**: TypeScript
- **Styling**: Tailwind CSS

## Development

### Build for Production

```bash
npm run build
```

### Run Production Server

```bash
npm start
```

### Lint Code

```bash
npm run lint
```

## MVP Features Checklist

- [x] Single page UI (app/page.tsx)
- [x] Left panel: Input form with prompt, slideCount, audience, template
- [x] Right panel: Progress stepper (OUTLINE → PLAN → FIX → RENDER → DONE)
- [x] Download button (appears when done)
- [x] Three Next.js API routes
  - [x] POST /api/decks
  - [x] GET /api/decks/:id/status
  - [x] GET /api/decks/:id/download
- [x] Status polling every 2 seconds
- [x] Error handling and display

## Backend Requirements

This frontend requires a FastAPI backend running on `http://localhost:8000`.

**See [FASTAPI_SPEC.md](./FASTAPI_SPEC.md) for complete backend implementation specification.**

Required endpoints:
- `POST /decks` - Create deck generation task
- `GET /decks/{id}/status` - Get task status
- `GET /decks/{id}/download` - Download .pptx file

FastAPI backend responsibilities:
1. **OpenAI Integration**: Call ChatGPT for outline, planning, and text compression
2. **Text Overflow Management**: Intelligently handle text that exceeds slide boundaries
3. **PPTX Generation**: Create PowerPoint files using python-pptx

## License

MIT
