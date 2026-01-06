import logging
import asyncio
from typing import Dict, Any
from .models import DeckRequest, SlideContent, DeckOutline
from .openai_client import OpenAIClient
from .pptx_generator import PPTXGenerator
from .storage import deck_storage

logger = logging.getLogger(__name__)


class DeckGenerator:
    """
    Main class responsible for orchestrating the deck generation pipeline.

    Pipeline stages:
    1. OUTLINE - Generate slide structure using OpenAI
    2. PLAN - Generate detailed content for each slide
    3. FIX - Optimize text to fit slide constraints
    4. RENDER - Create the actual PPTX file
    5. DONE - Mark as complete
    """

    def __init__(self):
        self.openai_client = OpenAIClient()
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
            logger.info(f"[{deck_id}] Starting deck generation")

            # Stage 1: OUTLINE
            await self._update_status(
                storage, deck_id, "outline", 10,
                "Generating presentation outline..."
            )
            outline = await self._generate_outline(request)

            # Stage 2: PLAN
            await self._update_status(
                storage, deck_id, "plan", 30,
                "Planning slide content..."
            )
            detailed_slides = await self._generate_content(outline, request)

            # Stage 3: FIX
            await self._update_status(
                storage, deck_id, "fix", 60,
                "Optimizing text and layout..."
            )
            optimized_slides = await self._fix_overflow(detailed_slides, request.template)

            # Stage 4: RENDER
            await self._update_status(
                storage, deck_id, "render", 80,
                "Rendering PowerPoint file..."
            )
            file_path = await self._render_pptx(
                deck_id, optimized_slides, request
            )

            # Stage 5: DONE
            storage[deck_id]["status"] = "done"
            storage[deck_id]["progress"] = 100
            storage[deck_id]["currentStep"] = "Presentation ready for download"
            storage[deck_id]["file_path"] = file_path

            # Save final state to persistent storage
            deck_storage.save(storage)

            logger.info(f"[{deck_id}] Deck generation complete: {file_path}")

        except Exception as e:
            logger.error(f"[{deck_id}] Generation failed: {str(e)}")
            storage[deck_id]["status"] = "error"
            storage[deck_id]["error"] = str(e)
            storage[deck_id]["currentStep"] = "Generation failed"

            # Save error state to persistent storage
            deck_storage.save(storage)

    async def _generate_outline(self, request: DeckRequest) -> DeckOutline:
        """
        Stage 1: Generate presentation outline using OpenAI.
        Creates the overall structure and slide titles.
        """
        logger.info("Generating outline...")

        outline = await self.openai_client.generate_outline(
            prompt=request.prompt,
            slide_count=request.slideCount,
            audience=request.audience
        )

        logger.info(f"Outline generated: {len(outline.slides)} slides")
        return outline

    async def _generate_content(
        self,
        outline: DeckOutline,
        request: DeckRequest
    ) -> list[SlideContent]:
        """
        Stage 2: Generate detailed content for each slide.
        Uses OpenAI to flesh out each slide with specific content.
        """
        logger.info("Generating detailed content...")

        detailed_slides = await self.openai_client.generate_slide_content(
            outline=outline,
            audience=request.audience
        )

        logger.info(f"Content generated for {len(detailed_slides)} slides")
        return detailed_slides

    async def _fix_overflow(
        self,
        slides: list[SlideContent],
        template: str
    ) -> list[SlideContent]:
        """
        Stage 3: Fix text overflow issues.
        Ensures text fits within slide boundaries by compressing/summarizing.
        """
        logger.info("Fixing text overflow...")

        optimized_slides = await self.openai_client.optimize_text_length(
            slides=slides,
            template=template
        )

        logger.info("Text optimization complete")
        return optimized_slides

    async def _render_pptx(
        self,
        deck_id: str,
        slides: list[SlideContent],
        request: DeckRequest
    ) -> str:
        """
        Stage 4: Render the actual PPTX file.
        Uses python-pptx to create the PowerPoint presentation.
        """
        logger.info("Rendering PPTX...")

        file_path = await self.pptx_generator.create_presentation(
            deck_id=deck_id,
            slides=slides,
            template=request.template,
            title=slides[0].title if slides else "Presentation"
        )

        logger.info(f"PPTX rendered: {file_path}")
        return file_path

    async def _update_status(
        self,
        storage: Dict[str, Any],
        deck_id: str,
        status: str,
        progress: int,
        step: str
    ):
        """Helper to update deck status in storage."""
        storage[deck_id]["status"] = status
        storage[deck_id]["progress"] = progress
        storage[deck_id]["currentStep"] = step

        # Save to persistent storage
        deck_storage.save(storage)

        # Small delay to simulate processing
        await asyncio.sleep(0.1)
