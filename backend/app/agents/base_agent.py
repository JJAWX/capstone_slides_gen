"""
Base Agent class for all PPT generation agents.
"""
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import openai
import os
from dotenv import load_dotenv

# Load environment variables
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(backend_dir, '.env')
load_dotenv(dotenv_path=dotenv_path)

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the PPT generation system.
    """

    def __init__(self, model: str = "gpt-4o"):
        # Ensure environment variables are loaded
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dotenv_path = os.path.join(backend_dir, '.env')
        load_dotenv(dotenv_path=dotenv_path)

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")

        self.model = model
        self.client = openai.OpenAI(api_key=api_key)

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the agent's main task.
        Must be implemented by subclasses.
        """
        pass

    async def call_openai(self, messages: list, **kwargs) -> str:
        """
        Call OpenAI API with the given messages.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise e

    def validate_input(self, **kwargs) -> bool:
        """
        Validate input parameters.
        Can be overridden by subclasses.
        """
        return True
