from typing import Dict, Any, Optional, List
from langchain.schema import HumanMessage, AIMessage, SystemMessage

from agents.core.base import BaseAgent, AgentResponse, Message, MessageType
from services.llm.providers import LLMProviderFactory, BaseLLMProvider
from config.settings import get_settings


class SimpleAgent(BaseAgent):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        settings = get_settings()
        config = config or {}
        
        super().__init__("SimpleAgent", config)
        
        self.settings = settings
        self.providers: List[BaseLLMProvider] = []
        self.system_prompt = "You are a helpful AI assistant."
        
        # Initialize providers
        self._setup_providers()
    
    async def initialize(self) -> None:
        # Add system message to conversation history
        system_message = Message(
            type=MessageType.SYSTEM,
            content=self.system_prompt
        )
        self.add_message(system_message)
    
    async def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        try:
            # Add user message to history
            user_message = Message(
                type=MessageType.USER,
                content=message,
                metadata=context
            )
            self.add_message(user_message)
            
            # Try providers in order until one succeeds
            response_content = await self._generate_response_with_fallback(message)
            
            # Add assistant response to history
            assistant_message = Message(
                type=MessageType.ASSISTANT,
                content=response_content
            )
            self.add_message(assistant_message)
            
            return AgentResponse(
                content=response_content,
                confidence=0.8,
                reasoning="Response generated using configured LLM or simple echo",
                actions_taken=["message_processing"],
                metadata={"context": context}
            )
            
        except Exception as e:
            return AgentResponse(
                content=f"I apologize, but I encountered an error: {str(e)}",
                confidence=0.0,
                reasoning=f"Error occurred: {str(e)}",
                actions_taken=["error_handling"],
                metadata={"error": str(e)}
            )
    
    def _setup_providers(self):
        """Initialize LLM providers based on settings."""
        provider_configs = {
            "openai": {
                "api_key": self.settings.openai_api_key,
                "model": self.settings.openai_model,
                "temperature": self.settings.temperature,
                "max_tokens": self.settings.max_tokens
            },
            "anthropic": {
                "api_key": self.settings.anthropic_api_key,
                "model": self.settings.anthropic_model,
                "temperature": self.settings.temperature,
                "max_tokens": self.settings.max_tokens
            },
            "openrouter": {
                "api_key": self.settings.openrouter_api_key,
                "model": self.settings.openrouter_model,
                "temperature": self.settings.temperature,
                "max_tokens": self.settings.max_tokens
            }
        }
        
        # Add primary provider first
        primary_provider = LLMProviderFactory.create_provider(
            self.settings.llm_provider, 
            provider_configs.get(self.settings.llm_provider, {})
        )
        if primary_provider and primary_provider.is_available():
            self.providers.append(primary_provider)
        
        # Add fallback providers
        for provider_name in self.settings.fallback_providers:
            if provider_name != self.settings.llm_provider:
                fallback_provider = LLMProviderFactory.create_provider(
                    provider_name,
                    provider_configs.get(provider_name, {})
                )
                if fallback_provider and fallback_provider.is_available():
                    self.providers.append(fallback_provider)
    
    async def _generate_response_with_fallback(self, message: str) -> str:
        """Generate response using primary provider with fallback support."""
        if not self.providers:
            return f"Echo: {message}"
        
        messages = self._prepare_messages_for_llm()
        
        for provider in self.providers:
            try:
                return await provider.generate_response(messages)
            except Exception as e:
                continue
        
        # All providers failed
        return f"Echo: {message}"
    
    def _prepare_messages_for_llm(self):
        """Convert conversation history to LangChain message format."""
        messages = []
        for msg in self.conversation_history:
            if msg.type == MessageType.SYSTEM:
                messages.append(SystemMessage(content=msg.content))
            elif msg.type == MessageType.USER:
                messages.append(HumanMessage(content=msg.content))
            elif msg.type == MessageType.ASSISTANT:
                messages.append(AIMessage(content=msg.content))
        return messages