from .base_agent import BaseAgent
from .prompts import OUTLINE_SYSTEM, OUTLINE_USER
from ..models import DeckOutline, OutlineSection
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class OutlineAgent(BaseAgent):
    """Agent specialized in creating presentation outlines."""
    
    def get_temperature(self) -> float:
        return 0.7  # Creative but structured
    
    def get_max_tokens(self) -> int:
        return 3000  # 增加到3000以生成更详细的大纲
    
    def get_system_prompt(self) -> str:
        return OUTLINE_SYSTEM
    
    def get_user_prompt_template(self) -> str:
        return OUTLINE_USER
    
    def get_fallback_result(self, **kwargs) -> Dict[str, Any]:
        return {
            "title": kwargs.get("prompt", "Presentation"),
            "sections": [
                {
                    "title": "Introduction",
                    "description": "Introduction to the topic",
                    "weight": 3,
                    "key_points": ["Overview", "Goals"]
                },
                {
                    "title": "Main Content",
                    "description": "Core analysis",
                    "weight": 8,
                    "key_points": ["Detailed Point 1", "Detailed Point 2"]
                },
                {
                    "title": "Conclusion",
                    "description": "Summary",
                    "weight": 3,
                    "key_points": ["Summary", "Next Steps"]
                }
            ]
        }
    
    async def generate_outline(self, request) -> DeckOutline:
        result = await self.process(
            prompt=request.prompt,
            slide_count=request.slideCount,
            audience=request.audience,
            template=request.template
        )
        
        # Parse JSON into Pydantic models
        try:
            sections = []
            for sec in result.get("sections", []):
                sections.append(OutlineSection(
                    title=sec.get("title", "Section"),
                    description=sec.get("description", ""),
                    weight=sec.get("weight", 5),
                    key_points=sec.get("key_points", [])
                ))
            return DeckOutline(title=result.get("title", request.prompt), sections=sections)
        except Exception as e:
            logger.error(f"Error parsing outline result: {e}")
            fallback = self.get_fallback_result(prompt=request.prompt)
            # Re-construct manual fallback
            sections = [
                OutlineSection(**s) for s in fallback["sections"]
            ]
            return DeckOutline(title=fallback["title"], sections=sections)
