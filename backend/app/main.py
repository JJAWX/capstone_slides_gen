from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
import uuid
import logging
import os
from dotenv import load_dotenv

# Load environment variables from backend/.env
backend_dir = Path(__file__).resolve().parent.parent
dotenv_path = backend_dir / '.env'
load_dotenv(dotenv_path=dotenv_path)

# Import our modules
from .deck_generator import DeckGenerator
from .models import DeckRequest, DeckResponse, DeckStatusResponse
from .storage import deck_storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Intelligent Slides Generator API")

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Persistent storage - load existing data on startup
decks_storage = deck_storage.load()
logger.info(f"Loaded {len(decks_storage)} existing decks from storage")

# Initialize deck generator
deck_generator = DeckGenerator()


@app.get("/")
async def root():
    return {
        "message": "Intelligent Slides Generator API",
        "version": "1.0.0",
        "endpoints": [
            "GET /decks - List all decks",
            "POST /decks - Create new deck",
            "GET /decks/{deck_id}/status - Get deck status",
            "GET /decks/{deck_id}/download - Download deck file"
        ]
    }


@app.get("/decks")
async def list_decks():
    """
    Get a list of all decks.

    Returns:
    - List of decks with their current status
    """
    decks_list = []

    for deck_id, deck_data in decks_storage.items():
        deck_info = {
            "deckId": deck_data["deckId"],
            "status": deck_data["status"],
            "progress": deck_data.get("progress", 0),
            "prompt": deck_data.get("request", {}).get("prompt", "Unknown"),
            "slideCount": deck_data.get("request", {}).get("slideCount", 0),
            "template": deck_data.get("request", {}).get("template", "corporate"),
            "createdAt": deck_data.get("createdAt", None),
            "error": deck_data.get("error")
        }
        decks_list.append(deck_info)

    # Sort by creation time (most recent first)
    # For now, just return in order since we don't have timestamps yet
    return {"decks": decks_list, "total": len(decks_list)}


@app.post("/decks", response_model=DeckResponse, status_code=201)
async def create_deck(
    request: DeckRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new deck generation task.

    This endpoint:
    1. Validates the request
    2. Creates a unique deck ID
    3. Starts background generation process
    4. Returns immediately with deck ID and initial status
    """
    try:
        # Generate unique deck ID
        deck_id = str(uuid.uuid4())

        logger.info(f"Creating deck {deck_id} with prompt: {request.prompt[:50]}...")

        # Initialize deck status
        from datetime import datetime
        deck_data = {
            "deckId": deck_id,
            "status": "outline",
            "progress": 0,
            "currentStep": "Starting generation...",
            "request": request.dict(),
            "createdAt": datetime.now().isoformat()
        }

        # Save to persistent storage
        deck_storage.update_deck(deck_id, deck_data, decks_storage)

        # Start background task for deck generation
        background_tasks.add_task(
            deck_generator.generate_deck,
            deck_id,
            request,
            decks_storage
        )

        return DeckResponse(
            deckId=deck_id,
            status="outline",
            message="Deck generation started"
        )

    except Exception as e:
        logger.error(f"Error creating deck: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/decks/{deck_id}/status", response_model=DeckStatusResponse)
async def get_deck_status(deck_id: str):
    """
    Get the current status of a deck generation task.

    Returns:
    - status: Current generation stage (outline/plan/fix/render/done/error)
    - progress: Percentage complete (0-100)
    - currentStep: Human-readable description of current step
    """
    if deck_id not in decks_storage:
        raise HTTPException(
            status_code=404,
            detail=f"Deck {deck_id} not found"
        )

    deck_data = decks_storage[deck_id]

    return DeckStatusResponse(
        deckId=deck_data["deckId"],
        status=deck_data["status"],
        progress=deck_data.get("progress"),
        currentStep=deck_data.get("currentStep"),
        error=deck_data.get("error")
    )


@app.get("/decks/{deck_id}/download")
async def download_deck(deck_id: str):
    """
    Download the generated PowerPoint file.

    Only available when status is 'done'.
    Returns the .pptx file as a download.
    """
    if deck_id not in decks_storage:
        raise HTTPException(
            status_code=404,
            detail=f"Deck {deck_id} not found"
        )

    deck_data = decks_storage[deck_id]

    if deck_data["status"] != "done":
        raise HTTPException(
            status_code=400,
            detail=f"Deck is not ready. Current status: {deck_data['status']}"
        )

    file_path = deck_data.get("file_path")

    if not file_path:
        raise HTTPException(
            status_code=500,
            detail="File path not found"
        )
    
    # Ensure absolute path
    if not os.path.isabs(file_path):
        # Assuming file_path is relative to project root (where script is run)
        # But just in case, let's resolve it carefully
        # If it starts with backend/, and we are in root, it is fine
        file_path = os.path.abspath(file_path)

    if not os.path.exists(file_path):
        logger.error(f"File not found at path: {file_path}")
        raise HTTPException(
            status_code=500,
            detail=f"File missing on server at {file_path}"
        )

    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=f"presentation-{deck_id}.pptx"
    )


@app.delete("/decks/{deck_id}")
async def delete_deck(deck_id: str):
    """
    Delete a deck and its associated file (optional cleanup endpoint).
    """
    if deck_id not in decks_storage:
        raise HTTPException(
            status_code=404,
            detail=f"Deck {deck_id} not found"
        )

    # Clean up file if it exists
    deck_data = decks_storage[deck_id]
    if "file_path" in deck_data:
        try:
            os.remove(deck_data["file_path"])
        except Exception as e:
            logger.warning(f"Failed to delete file: {str(e)}")

    # Remove from storage (both in-memory and persistent)
    deck_storage.delete_deck(deck_id, decks_storage)

    return {"message": f"Deck {deck_id} deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
