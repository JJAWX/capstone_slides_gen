# FastAPI Backend - Intelligent Slides Generator

This is the backend service for the Intelligent Slides Generator. It handles:
- OpenAI API integration for content generation
- Text overflow management
- PowerPoint (.pptx) file generation

## Setup

### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview
TEMPLATES_DIR=backend/templates
OUTPUT_DIR=backend/output
```

### 3. Run the Server

```bash
# From the backend directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or from the project root
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Architecture

```
Backend Pipeline:
1. OUTLINE  → Use OpenAI to generate slide structure
2. PLAN     → Generate detailed content for each slide
3. FIX      → Optimize text to fit slide constraints
4. RENDER   → Create .pptx file using python-pptx
5. DONE     → File ready for download
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   ├── deck_generator.py    # Main generation pipeline
│   ├── openai_client.py     # OpenAI API client
│   └── pptx_generator.py    # PowerPoint generation
├── templates/               # PowerPoint templates (optional)
├── output/                  # Generated .pptx files
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## API Endpoints

### POST /decks
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

**Response:**
```json
{
  "deckId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "outline",
  "message": "Deck generation started"
}
```

### GET /decks/{deckId}/status
Get generation status.

**Response:**
```json
{
  "deckId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "render",
  "progress": 75,
  "currentStep": "Generating slide 8 of 10"
}
```

### GET /decks/{deckId}/download
Download the generated .pptx file.

## Development

### Run with Auto-reload

```bash
uvicorn app.main:app --reload --port 8000
```

### Run Tests

```bash
pytest
```

### Check Code Quality

```bash
# Install dev dependencies
pip install black flake8 mypy

# Format code
black app/

# Lint
flake8 app/

# Type check
mypy app/
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4-turbo-preview` |
| `TEMPLATES_DIR` | Directory for PowerPoint templates | `backend/templates` |
| `OUTPUT_DIR` | Directory for generated files | `backend/output` |

## Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations

1. **Storage**: Use cloud storage (S3, GCS) instead of local filesystem
2. **Queue**: Use Celery or Redis Queue for background tasks
3. **Database**: Use PostgreSQL/MongoDB to store deck metadata
4. **Rate Limiting**: Implement rate limiting for OpenAI API calls
5. **Monitoring**: Add logging and monitoring (Sentry, DataDog)

## Troubleshooting

### OpenAI API Errors

If you see errors like "Invalid API key":
1. Check that your `.env` file contains a valid `OPENAI_API_KEY`
2. Ensure the key starts with `sk-`
3. Verify the key has sufficient credits

### Import Errors

If you see "ModuleNotFoundError":
```bash
# Make sure you're in the right directory
cd backend
pip install -r requirements.txt
```

### Permission Errors

If you can't write files to `output/`:
```bash
mkdir -p output
chmod 755 output
```

## License

MIT
