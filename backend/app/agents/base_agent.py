from abc import ABC, abstractmethod
from typing import Any, Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import logging
import os

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all PPT generation agents."""
    
    def __init__(self, model_name: str = "gpt-4-turbo-preview"):
        self.llm = ChatOpenAI(
            model_name=os.getenv("OPENAI_MODEL", model_name),
            temperature=self.get_temperature(),
            max_tokens=self.get_max_tokens(),
            api_key=os.getenv("OPENAI_API_KEY"),
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        self.parser = JsonOutputParser()
    
    @abstractmethod
    def get_temperature(self) -> float:
        """Temperature for creativity vs consistency."""
        pass
    
    @abstractmethod
    def get_max_tokens(self) -> int:
        """Max tokens for response."""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """System prompt for this agent."""
        pass
    
    @abstractmethod
    def get_user_prompt_template(self) -> str:
        """Template for user prompt."""
        pass
    
    async def process(self, **kwargs) -> Dict[str, Any]:
        """Main processing method."""
        try:
            system_prompt = self.get_system_prompt()
            # Pass template directly to LangChain to handle formatting
            user_prompt_template = self.get_user_prompt_template()
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", user_prompt_template)
            ])
            
            chain = prompt | self.llm | self.parser
            result = await chain.ainvoke(kwargs)
            
            logger.info(f"{self.__class__.__name__} completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__} failed: {str(e)}")
            logger.exception(e)
            return self.get_fallback_result(**kwargs)
    
    @abstractmethod
    def get_fallback_result(self, **kwargs) -> Dict[str, Any]:
        """Fallback result if processing fails."""
        pass
