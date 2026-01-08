import logging
from typing import Dict, Any
from .models import DeckRequest
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

            # Execute sophisticated workflow (包含PPTX生成)
            slides, design_config = await self.workflow_manager.execute_workflow(deck_id, request, storage)

            # Workflow已经生成了PPTX文件，从workflow获取文件路径
            pptx_files = list(self.workflow_manager.pptx_dir.glob(f"presentation_{deck_id}_*.pptx"))
            if pptx_files:
                # 使用最新的PPTX文件
                file_path = str(sorted(pptx_files, key=lambda x: x.stat().st_mtime)[-1])
                logger.info(f"[{deck_id}] Using generated PPTX: {file_path}")
            else:
                raise FileNotFoundError(f"No PPTX file found for deck {deck_id}")

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
