# AI-Powered Presentation Generator

An intelligent presentation creation system that generates professional PowerPoint slides with diverse layouts, automatic chart generation, and sophisticated content quality controls. Built with a multi-agent architecture powered by GPT-4.

## Key Features

✨ **12+ Diverse Layout Types** - Dynamic slide layouts including two-column, comparison, timeline, quote, and more
📊 **Automatic Chart Generation** - AI analyzes content and generates relevant data visualizations  
🎨 **8 Professional Templates** - Corporate, academic, startup, minimal, creative, modern, elegant, and dark themes
🤖 **Multi-Agent Workflow** - Specialized AI agents for outline, content, design, layout, images, and review
🛡️ **Quality Assurance** - Automatic text truncation, fallback content, and empty slide prevention
🖼️ **Smart Image Integration** - Background images (title slides only) and content images with search
📐 **Direct PPTX Generation** - No XML templates - dynamic slide creation using python-pptx

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Next.js Frontend (UI)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  DeckForm    │  │  DeckStatus  │  │  DeckList    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└───────────────────────────┬─────────────────────────────────────┘
                            │ REST API
┌───────────────────────────▼─────────────────────────────────────┐
│              Next.js API Routes (BFF Layer)                     │
│    /api/decks  •  /api/decks/:id/status  •  /api/decks/:id/download │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP
┌───────────────────────────▼─────────────────────────────────────┐
│                    FastAPI Backend (Python)                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Workflow Manager (11 Steps)                 │   │
│  │  1. Outline → 2. Structure → 3. Content → 4. Charts     │   │
│  │  5. Optimize → 6. Layout → 7. Images → 8. Search        │   │
│  │  9. Adjust → 10. Review → 11. PPTX Generation           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │ OutlineAgent │ │ ContentAgent │ │ DesignAgent  │           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │ LayoutAgent  │ │  ImageAgent  │ │  ChartAgent  │           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
│  ┌──────────────┐ ┌──────────────────────────────┐            │
│  │ ReviewAgent  │ │  SimplePPTXGenerator         │            │
│  └──────────────┘ └──────────────────────────────┘            │
└──────────────────────────────────────────────────────────────────┘
                            │
                            ▼
               ┌─────────────────────────┐
               │    OpenAI GPT-4o-mini   │
               └─────────────────────────┘
```

## Project Structure

```
.
├── src/                                    # Next.js Frontend
│   ├── app/
│   │   ├── page.tsx                        # Main dashboard UI
│   │   ├── layout.tsx                      # Root layout with providers
│   │   ├── globals.css                     # Global styles
│   │   └── api/                            # Backend-for-Frontend routes
│   │       └── decks/
│   │           ├── route.ts                # POST /api/decks - Create task
│   │           └── [id]/
│   │               ├── status/route.ts     # GET - Poll status
│   │               └── download/route.ts   # GET - Download .pptx
│   ├── components/
│   │   ├── DeckForm.tsx                    # Presentation creation form
│   │   ├── DeckStatus.tsx                  # Real-time progress tracker
│   │   └── DeckList.tsx                    # Generated decks list
│   └── lib/
│       └── types.ts                        # TypeScript definitions
│
└── backend/                                # FastAPI Backend
    ├── app/
    │   ├── main.py                         # FastAPI app & endpoints
    │   ├── models.py                       # Pydantic models & schemas
    │   ├── storage.py                      # In-memory deck storage
    │   ├── openai_client.py                # OpenAI client wrapper
    │   │
    │   ├── agents/                         # AI Agent System
    │   │   ├── base_agent.py               # Base agent class
    │   │   ├── outline_agent.py            # Creates outline structure
    │   │   ├── content_agent.py            # Generates slide content
    │   │   ├── design_agent.py             # Visual design decisions
    │   │   ├── layout_agent.py             # Layout type assignment
    │   │   ├── image_agent.py              # Image suggestions
    │   │   ├── image_search_agent.py       # Image search & enhancement
    │   │   ├── chart_agent.py              # Data visualization
    │   │   ├── review_agent.py             # Quality review & polish
    │   │   ├── layout_adjustment_agent.py  # Text overflow fixes
    │   │   ├── prompts.py                  # LLM prompts
    │   │   └── knowledge/
    │   │       └── pptx_api_manual.py      # python-pptx reference
    │   │
    │   ├── workflow/
    │   │   └── workflow_manager.py         # 11-step pipeline orchestration
    │   │
    │   └── utils/
    │       └── simple_pptx_generator.py    # Direct PPTX creation
    │
    ├── templates/                          # 8 Template JSON files
    │   ├── corporate_template.json
    │   ├── academic_template.json
    │   ├── startup_template.json
    │   ├── minimal_template.json
    │   ├── creative_template.json
    │   ├── modern_template.json
    │   ├── elegant_template.json
    │   └── dark_template.json
    │
    ├── output/                             # Generated files
    │   ├── pptx/                           # Final .pptx files
    │   ├── charts/                         # Generated chart images
    │   ├── outlines/                       # Saved outlines
    │   ├── structures/                     # Saved structures
    │   └── contents/                       # Saved content JSON
    │
    ├── data/
    │   └── decks.json                      # Persistent deck metadata
    │
    └── requirements.txt                    # Python dependencies
```

## Multi-Agent Workflow

The system uses an 11-step sophisticated workflow coordinated by the WorkflowManager:

1. **📋 Outline Creation** - OutlineAgent analyzes topic and creates strategic structure
2. **⚖️ Structure Analysis** - Weighted slide allocation based on section importance
3. **✍️ Content Generation** - ContentAgent generates detailed content with layout-specific requirements
4. **📊 Chart Generation** - ChartAgent analyzes slides and generates data visualizations (min 1 per deck)
5. **🔧 Content Optimization** - Template-specific content refinements
6. **📐 Layout Selection** - LayoutAgent assigns optimal layout types for visual variety
7. **🎨 Visual Design** - DesignAgent creates color schemes and ImageAgent suggests images
8. **🔍 Image Search** - ImageSearchAgent finds images for sparse slides
9. **📏 Layout Adjustment** - LayoutAdjustmentAgent validates text overflow
10. **✅ Final Review** - ReviewAgent polishes content while preserving all metadata
11. **🎬 PPTX Generation** - SimplePPTXGenerator creates final PowerPoint file

### Layout Types

The system supports 12+ diverse layout types for visual variety:

- **title_slide** - Main title page with optional background image
- **section_divider** - Chapter/section separator with colored background
- **bullet_points** - Standard bullet list (4-6 points)
- **two_column** - Split content into left/right columns
- **comparison** - Side-by-side comparison cards with VS indicator
- **quote** - Large quotation with attribution
- **timeline** - Horizontal timeline with events
- **narrative** - Full paragraph text (200-400 words)
- **image_content** - Image with supporting text
- **table_data** - Structured data table
- **chart_data** - Data visualization chart

### Quality Assurance Features

- **Empty Slide Prevention** - Automatic fallback content generation for slides without data
- **Text Truncation** - `MAX_BULLET_CHARS=80`, `MAX_PARAGRAPH_CHARS=600`
- **Dynamic Font Sizing** - Automatically adjusts font size based on content length
- **Content Validation** - Detects placeholder text and generates meaningful alternatives
- **Background Control** - Background images restricted to title slide only
- **Chart Guarantee** - Forces at least 1 chart per presentation if none generated naturally

## Prerequisites

- **Node.js** 20+ (for Next.js frontend)
- **Python** 3.11+ (for FastAPI backend)
- **OpenAI API Key** (GPT-4o-mini or GPT-4)
- **pip** (Python package manager)
- **npm** or **yarn** (Node package manager)

## Getting Started

### Backend Setup (FastAPI)

#### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Key dependencies:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `openai` - GPT-4 integration
- `python-pptx` - PowerPoint generation
- `matplotlib` - Chart generation
- `requests` - HTTP client
- `pydantic` - Data validation

#### 2. Configure Backend Environment

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
UNSPLASH_ACCESS_KEY=your-unsplash-key-optional
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

The output directories will be created automatically:
- `backend/output/pptx/` - Generated PowerPoint files
- `backend/output/charts/` - Generated chart images
- `backend/output/outlines/` - Saved outline structures
- `backend/output/contents/` - Saved content JSON files

### Frontend Setup (Next.js)

#### 1. Install Node Dependencies

```bash
npm install
# or
yarn install
```

Key dependencies:
- `next` 15.1.4 - React framework
- `react` 19 - UI library
- `antd` 5 - UI components
- `tailwindcss` - Utility CSS
- `typescript` - Type safety

#### 2. Configure Frontend Environment

```bash
cp .env.example .env.local
```

Edit `.env.local`:

```env
FASTAPI_URL=http://localhost:8000
```

#### 3. Run Development Server

```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3001](http://localhost:3001) in your browser.

The UI will display:
- **Left Panel**: Creation form (prompt, slide count, audience, template selection)
- **Right Panel**: Real-time progress tracker with 11-step workflow visualization
- **Generated Decks**: List of previously created presentations with download buttons

### Running Both Servers

You need to run both servers simultaneously for the application to work:

**Terminal 1 - Backend (FastAPI):**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend (Next.js):**
```bash
npm run dev
```

**Or use the convenience script (macOS/Linux):**
```bash
chmod +x start-dev.sh
./start-dev.sh
```

The script will start both servers in the background and tail their logs.

## API Documentation

### Frontend API Routes (Next.js)

#### POST /api/decks
Create a new presentation generation task.

**Request Body:**
```json
{
  "prompt": "Future of Artificial Intelligence in Healthcare",
  "slideCount": 12,
  "audience": "business",
  "template": "corporate"
}
```

**Available Templates:**
- `corporate` - Professional business presentations
- `academic` - Research and education
- `startup` - Modern pitch decks
- `minimal` - Clean and simple
- `creative` - Vibrant and artistic
- `modern` - Contemporary design
- `elegant` - Sophisticated style
- `dark` - Dark theme

**Response:**
```json
{
  "deckId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "outline"
}
```

#### GET /api/decks/:id/status
Poll the current status of a presentation generation task.

**Response:**
```json
{
  "deckId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "charts",
  "progress": 40,
  "currentStep": "📊 Generating charts for data visualization...",
  "title": "Future of Artificial Intelligence in Healthcare"
}
```

**Workflow Status Values:**
- `outline` (10%) - Creating strategic outline structure
- `analyze` (18%) - Analyzing structure and allocating slides
- `content` (30%) - Generating detailed slide content
- `charts` (36%) - Creating data visualizations
- `optimize` (42%) - Optimizing content for template
- `layout` (52%) - Selecting optimal layouts
- `design` (60%) - Planning visual design
- `images` (70%) - Finding relevant images
- `adjust` (80%) - Validating layout and text
- `review` (90%) - Final quality review
- `generating` (95%) - Creating PPTX file
- `done` (100%) - Generation complete
- `error` - Generation failed

#### GET /api/decks/:id/download
Download the generated PowerPoint file.

**Response:** Binary `.pptx` file with appropriate headers

### Backend API Endpoints (FastAPI)

#### POST /decks
Creates a deck generation task (called by Next.js BFF).

#### GET /decks/{deck_id}/status
Returns current generation status and progress.

#### GET /decks/{deck_id}/download
Streams the generated `.pptx` file.

#### GET /docs
Interactive API documentation (Swagger UI).

#### GET /
API health check endpoint.

## Tech Stack

### Frontend
- **Framework**: Next.js 15.1.4 (App Router with React 19)
- **UI Library**: Ant Design 5
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 3
- **State Management**: React Hooks
- **HTTP Client**: Fetch API

### Backend
- **Framework**: FastAPI (Python async web framework)
- **AI/LLM**: OpenAI GPT-4o-mini via official SDK
- **PowerPoint**: python-pptx (direct PPTX generation)
- **Charts**: matplotlib (data visualization)
- **Data Validation**: Pydantic v2
- **ASGI Server**: Uvicorn
- **Image Search**: Unsplash API / Lorem Picsum (fallback)

### Architecture Patterns
- **Multi-Agent System**: Specialized AI agents for different tasks
- **Backend-for-Frontend (BFF)**: Next.js API routes proxy FastAPI
- **Workflow Orchestration**: 11-step pipeline with progress tracking
- **Fallback Mechanisms**: Multiple quality assurance layers

## Development

### Build for Production

**Frontend:**
```bash
npm run build
npm start
```

**Backend:**
```bash
# Production mode (no auto-reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Code Quality

**Lint Frontend:**
```bash
npm run lint
```

**Format Code:**
```bash
# Frontend
npm run format

# Backend (if using black/ruff)
black backend/app
ruff check backend/app
```

### Testing

```bash
# Frontend tests
npm test

# Backend tests
pytest backend/tests
```

### Environment Variables

**Frontend (.env.local):**
```env
FASTAPI_URL=http://localhost:8000
```

**Backend (.env):**
```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
UNSPLASH_ACCESS_KEY=...  # Optional
```

## Features Checklist

### Core Features
- [x] Multi-agent AI architecture with specialized agents
- [x] 11-step sophisticated workflow pipeline
- [x] 12+ diverse layout types for visual variety
- [x] Automatic chart generation (minimum 1 per presentation)
- [x] 8 professional templates with color schemes
- [x] Direct PPTX generation using python-pptx
- [x] Smart image integration (background + content images)
- [x] Text overflow prevention with automatic truncation
- [x] Empty slide detection with fallback content
- [x] Dynamic font sizing based on content length
- [x] Layout-specific content generation
- [x] Quality assurance with ReviewAgent

### UI Features
- [x] Single-page dashboard application
- [x] Left panel: Creation form with all options
- [x] Right panel: Real-time 11-step progress tracker
- [x] Generated decks list with metadata
- [x] Download button for completed presentations
- [x] Error handling and display
- [x] Status polling (2-second intervals)
- [x] Responsive design with Tailwind CSS

### API Features
- [x] POST /api/decks - Create generation task
- [x] GET /api/decks/:id/status - Poll progress
- [x] GET /api/decks/:id/download - Download .pptx
- [x] FastAPI backend with async support
- [x] OpenAPI/Swagger documentation
- [x] CORS configuration for local development
- [x] Persistent deck metadata storage

### Quality Assurance
- [x] Content validation and sanitization
- [x] Fallback content generation for empty slides
- [x] Background image restriction (title only)
- [x] Chart generation guarantee (min 1 per deck)
- [x] Text truncation constants (MAX_BULLET_CHARS=80, MAX_PARAGRAPH_CHARS=600)
- [x] Dynamic font sizing
- [x] Layout adjustment agent for overflow
- [x] Review agent preserves all metadata

## Troubleshooting

### Common Issues

**Port conflicts:**
- Backend: Change port in `.env.local` and backend startup command
- Frontend: Use `PORT=3002 npm run dev` to change Next.js port

**OpenAI API errors:**
- Verify `OPENAI_API_KEY` in `backend/.env`
- Check API quota and billing
- Ensure using compatible model (gpt-4o-mini or gpt-4)

**Empty slides appearing:**
- Check backend logs for ContentAgent failures
- Fallback content should trigger automatically
- Verify ReviewAgent is preserving content

**Charts not generating:**
- Check `backend/output/charts/` directory exists
- Verify matplotlib is installed correctly
- Review ChartAgent logs for errors
- At least 1 chart should be forced if none generated

**Download fails:**
- Verify PPTX file exists in `backend/output/pptx/`
- Check file permissions
- Review backend logs for generation errors

### Logs

**Backend logs:**
```bash
tail -f backend.log
```

**Frontend logs:**
Browser console (F12) shows API calls and errors

## Project Documentation

- **FASTAPI_SPEC.md** - Complete FastAPI implementation specification
- **README.md** - This file (project overview and setup)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT
