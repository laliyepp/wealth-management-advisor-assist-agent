from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import BaseMessage



class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_response(self, messages: List[BaseMessage]) -> str:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", **kwargs):
        self.api_key = api_key
        self.model = model
        self.llm = ChatOpenAI(
            model_name=model,
            openai_api_key=api_key,
            **kwargs
        ) if api_key else None
    
    async def generate_response(self, messages: List[BaseMessage]) -> str:
        if not self.llm:
            raise ValueError("OpenAI provider not properly initialized")
        response = await self.llm.agenerate([messages])
        return response.generations[0][0].text
    
    def is_available(self) -> bool:
        return self.llm is not None


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229", **kwargs):
        self.api_key = api_key
        self.model = model
        self.llm = ChatAnthropic(
            model=model,
            anthropic_api_key=api_key,
            **kwargs
        ) if api_key else None
    
    async def generate_response(self, messages: List[BaseMessage]) -> str:
        if not self.llm:
            raise ValueError("Anthropic provider not properly initialized")
        response = await self.llm.agenerate([messages])
        return response.generations[0][0].text
    
    def is_available(self) -> bool:
        return self.llm is not None


class OpenRouterProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "openai/gpt-3.5-turbo", **kwargs):
        self.api_key = api_key
        self.model = model
        self.llm = ChatOpenAI(
            model_name=model,
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            **kwargs
        ) if api_key else None
    
    async def generate_response(self, messages: List[BaseMessage]) -> str:
        if not self.llm:
            raise ValueError("OpenRouter provider not properly initialized")
        response = await self.llm.agenerate([messages])
        return response.generations[0][0].text
    
    def is_available(self) -> bool:
        return self.llm is not None


class LLMProviderFactory:
    @staticmethod
    def create_provider(provider_type: str, config: Dict[str, Any]) -> Optional[BaseLLMProvider]:
        providers = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "openrouter": OpenRouterProvider
        }
        
        provider_class = providers.get(provider_type.lower())
        if not provider_class:
            return None
        
        try:
            return provider_class(**config)
        except Exception:
            return None