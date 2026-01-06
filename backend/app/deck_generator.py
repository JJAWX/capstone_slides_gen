import logging
from typing import Dict, Any
from .models import DeckRequest
from .pptx_generator import PPTXGenerator
from .storage import deck_storage
from .workflow.workflow_manager import WorkflowManager

logger = logging.getLogger(__name__)


class DeckGenerator:
    """
    Main class responsible for orchestrating the deck generation pipeline using Agent-Based Workflow.

    Pipeline stages delegated to WorkflowManager:
    1. OUTLINE - Strategic Outline Creation
    2. ANALYZE - Audience Analysis & Content Strategy
    3. CONTENT - Content Development
    4. OPTIMIZE - Content Optimization
    5. LAYOUT - Visual Layout Planning
    6. REVIEW - Final Quality Review
    7. DONE - Mark as complete
    """

    def __init__(self):
        self.workflow_manager = WorkflowManager()
        self.pptx_generator = PPTXGenerator()

    async def generate_deck(
        self,
        deck_id: str,
        request: DeckRequest,
        storage: Dict[str, Any]
    ):
        """
        Main generation pipeline. Updates storage with progress.
        """
        try:
            logger.info(f"[{deck_id}] Starting deck generation via WorkflowManager")

            # Execute sophisticated workflow
            slides = await self.workflow_manager.execute_workflow(deck_id, request, storage)

            # Final RENDER Stage (not part of content logic, but file creation)
            await self._update_status(
                storage, deck_id, "layout", 95,
                "Rendering PowerPoint file..."
            )
            file_path = await self.pptx_generator.create_presentation(
                deck_id=deck_id,
                slides=slides,
                template=request.template,
                title=request.prompt # Or use title from outline if we tracked it separately
            )

            # Stage: DONE
            storage[deck_id]["status"] = "done"
            storage[deck_id]["progress"] = 100
            storage[deck_id]["currentStep"] = "Presentation ready for download"
            storage[deck_id]["file_path"] = file_path

            # Save final state to persistent storage
            deck_storage.save(storage)

            logger.info(f"[{deck_id}] Deck generation complete: {file_path}")

        except Exception as e:
            logger.error(f"[{deck_id}] Generation failed: {str(e)}")
            logger.exception(e)
            storage[deck_id]["status"] = "error"
            storage[deck_id]["error"] = str(e)
            storage[deck_id]["currentStep"] = "Generation failed"

            # Save error state to persistent storage
            deck_storage.save(storage)

    async def _update_status(self, storage, deck_id, status, progress, step):
        if deck_id in storage:
            storage[deck_id]["status"] = status
            storage[deck_id]["progress"] = progress
            storage[deck_id]["currentStep"] = step
            deck_storage.save(storage)
