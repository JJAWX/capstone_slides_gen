import os
import json
import logging
from typing import List
from pathlib import Path
from openai import AsyncOpenAI
from dotenv import load_dotenv
from .models import DeckOutline, SlideContent

# Load environment variables from backend/.env
# Get the backend directory path
backend_dir = Path(__file__).resolve().parent.parent
dotenv_path = backend_dir / '.env'
load_dotenv(dotenv_path=dotenv_path)

logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    Client for OpenAI API interactions.
    Handles outline generation, content planning, and text optimization.
    """

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

    async def generate_outline(
        self,
        prompt: str,
        slide_count: int,
        audience: str
    ) -> DeckOutline:
        """
        Generate presentation outline using OpenAI.
        Creates overall structure and slide titles.
        """
        system_prompt = f"""You are a professional presentation designer.
Create a structured outline for a {slide_count}-slide presentation.
Target audience: {audience}.
Return a JSON object with this structure:
{{
  "title": "Presentation Title",
  "slides": [
    {{
      "title": "Slide Title",
      "content": ["Key point 1", "Key point 2"],
      "slideType": "title|content|comparison|data"
    }}
  ]
}}
The first slide should be a title slide. Keep titles concise and impactful."""

        user_prompt = f"Topic: {prompt}\nNumber of slides: {slide_count}"

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            logger.info(f"Generated outline: {result['title']}")

            # Convert to DeckOutline model
            slides = [
                SlideContent(**slide)
                for slide in result["slides"][:slide_count]
            ]

            return DeckOutline(title=result["title"], slides=slides)

        except Exception as e:
            logger.error(f"Error generating outline: {str(e)}")
            # Fallback to simple outline
            return self._create_fallback_outline(prompt, slide_count)

    async def generate_slide_content(
        self,
        outline: DeckOutline,
        audience: str
    ) -> List[SlideContent]:
        """
        Generate detailed content for each slide.
        Fleshes out the outline with specific talking points.
        """
        detailed_slides = []

        for i, slide in enumerate(outline.slides):
            logger.info(f"Generating content for slide {i+1}: {slide.title}")

            # Skip title slide (already has minimal content)
            if i == 0 or slide.slideType == "title":
                detailed_slides.append(slide)
                continue

            system_prompt = f"""You are a presentation content writer.
Create detailed bullet points for a slide.
Target audience: {audience}.
Keep each point concise (max 15 words).
Return 3-5 bullet points as a JSON array of strings."""

            user_prompt = f"""Slide title: {slide.title}
Context: {outline.title}
Current outline points: {', '.join(slide.content)}"""

            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )

                result = json.loads(response.choices[0].message.content)
                content = result.get("points", slide.content)

                detailed_slides.append(
                    SlideContent(
                        title=slide.title,
                        content=content,
                        slideType=slide.slideType
                    )
                )

            except Exception as e:
                logger.warning(f"Error generating content for slide {i+1}: {str(e)}")
                detailed_slides.append(slide)  # Use original

        return detailed_slides

    async def optimize_text_length(
        self,
        slides: List[SlideContent],
        template: str
    ) -> List[SlideContent]:
        """
        Optimize text to fit slide constraints.
        Compresses overly long content while preserving key information.
        """
        # Define max words per bullet point by template
        max_words = {
            "corporate": 15,
            "academic": 20,
            "startup": 12,
            "minimal": 10
        }
        max_words_per_point = max_words.get(template, 15)

        optimized_slides = []

        for slide in slides:
            needs_optimization = any(
                len(point.split()) > max_words_per_point
                for point in slide.content
            )

            if not needs_optimization:
                optimized_slides.append(slide)
                continue

            logger.info(f"Optimizing text for slide: {slide.title}")

            system_prompt = f"""You are a text optimizer for presentations.
Compress the following bullet points to fit slide constraints.
Max words per point: {max_words_per_point}
Preserve key information and impact.
Return compressed points as a JSON array of strings."""

            user_prompt = f"""Points to compress:
{json.dumps(slide.content, indent=2)}"""

            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.5,
                    response_format={"type": "json_object"}
                )

                result = json.loads(response.choices[0].message.content)
                optimized_content = result.get("points", slide.content)

                optimized_slides.append(
                    SlideContent(
                        title=slide.title,
                        content=optimized_content,
                        slideType=slide.slideType
                    )
                )

            except Exception as e:
                logger.warning(f"Error optimizing slide {slide.title}: {str(e)}")
                optimized_slides.append(slide)  # Use original

        return optimized_slides

    def _create_fallback_outline(
        self,
        prompt: str,
        slide_count: int
    ) -> DeckOutline:
        """Create a simple fallback outline if OpenAI fails."""
        slides = [
            SlideContent(
                title=prompt,
                content=["Professional Presentation"],
                slideType="title"
            )
        ]

        for i in range(1, slide_count):
            slides.append(
                SlideContent(
                    title=f"Topic {i}",
                    content=[
                        "Key point 1",
                        "Key point 2",
                        "Key point 3"
                    ],
                    slideType="content"
                )
            )

        return DeckOutline(title=prompt, slides=slides)
