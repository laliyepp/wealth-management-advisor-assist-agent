from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class MessageType(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    type: MessageType
    content: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentResponse:
    content: str
    confidence: float
    reasoning: str
    actions_taken: List[str]
    metadata: Optional[Dict[str, Any]] = None


class BaseAgent(ABC):
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.conversation_history: List[Message] = []
        self.llm_provider = None
        
    @abstractmethod
    async def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        pass
    
    def set_llm_provider(self, provider):
        self.llm_provider = provider
    
    def add_message(self, message: Message) -> None:
        self.conversation_history.append(message)
    
    def get_conversation_history(self) -> List[Message]:
        return self.conversation_history.copy()
    
    def clear_conversation_history(self) -> None:
        self.conversation_history.clear()