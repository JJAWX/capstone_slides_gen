from .base_agent import BaseAgent
from .prompts import DESIGN_SYSTEM, DESIGN_USER
from typing import Dict, Any

class DesignAgent(BaseAgent):
    """Agent specialized in determining visual design and formatting."""
    
    def get_temperature(self) -> float:
        return 0.5  # Balanced for consistent but creative design
    
    def get_max_tokens(self) -> int:
        return 1000
    
    def get_system_prompt(self) -> str:
        return DESIGN_SYSTEM
    
    def get_user_prompt_template(self) -> str:
        return DESIGN_USER
    
    def get_fallback_result(self, **kwargs) -> Dict[str, Any]:
        return {
            "design_rationale": "Fallback corporate design",
            "colors": {
                "primary": [0, 51, 102],
                "secondary": [0, 102, 204],
                "accent": [255, 153, 0],
                "background": [255, 255, 255],
                "text_main": [0, 0, 0]
            },
            "fonts": {
                "heading": "Arial",
                "body": "Arial"
            }
        }
    
    async def generate_design(self, request) -> Dict[str, Any]:
        return await self.process(
            prompt=request.prompt,
            audience=request.audience,
            template=request.template
        )
