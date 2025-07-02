from typing import Dict, Any, Optional, List
from agents.core.base import AgentResponse, Message, MessageType
from agents.core.registry import AgentRegistry, AgentCapability
from agents.implementations.simple_agent import SimpleAgent
from services.llm.providers import LLMProviderFactory, BaseLLMProvider
from config.settings import get_settings
from langchain.schema import HumanMessage, SystemMessage


class AgentOrchestrator:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.registry = AgentRegistry()
        self.default_agent = None
        self.settings = get_settings()
        self.routing_provider = None
        self.conversation_history: List[Message] = []
        self._setup_routing_provider()
        
    def _setup_routing_provider(self):
        provider_configs = {
            "openai": {
                "api_key": self.settings.openai_api_key,
                "model": self.settings.openai_model,
                "temperature": 0.3,
                "max_tokens": 500
            },
            "anthropic": {
                "api_key": self.settings.anthropic_api_key,
                "model": self.settings.anthropic_model,
                "temperature": 0.3,
                "max_tokens": 500
            },
            "openrouter": {
                "api_key": self.settings.openrouter_api_key,
                "model": self.settings.openrouter_model,
                "temperature": 0.3,
                "max_tokens": 500
            }
        }
        
        self.routing_provider = LLMProviderFactory.create_provider(
            self.settings.llm_provider,
            provider_configs.get(self.settings.llm_provider, {})
        )
        
        if not self.routing_provider or not self.routing_provider.is_available():
            for provider_name in self.settings.fallback_providers:
                provider = LLMProviderFactory.create_provider(
                    provider_name,
                    provider_configs.get(provider_name, {})
                )
                if provider and provider.is_available():
                    self.routing_provider = provider
                    break
        
    async def initialize(self) -> None:
        self.default_agent = SimpleAgent(self.config)
        await self.default_agent.initialize()
        
        self.registry.register_agent(
            self.default_agent,
            AgentCapability(
                domain="general_assistance",
                description="General AI assistance, basic conversations, and fallback for unspecialized queries",
                expertise_areas=["general questions", "basic conversations", "help requests"],
                example_queries=["hello", "how are you", "what can you do"]
            )
        )
        
        system_message = Message(
            type=MessageType.SYSTEM,
            content="You are an agent orchestrator that intelligently routes financial queries to specialized agents based on semantic understanding."
        )
        self.conversation_history.append(system_message)
    
    async def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        try:
            user_message = Message(
                type=MessageType.USER,
                content=message,
                metadata=context
            )
            self.conversation_history.append(user_message)
            
            selected_agent = await self._route_to_agent(message, context)
            
            response = await selected_agent.process_message(message, context)
            
            response.metadata = response.metadata or {}
            response.metadata["selected_agent"] = selected_agent.name
            response.metadata["routing_decision"] = "semantic_analysis"
            response.metadata["orchestrator"] = "AgentOrchestrator"
            
            assistant_message = Message(
                type=MessageType.ASSISTANT,
                content=response.content
            )
            self.conversation_history.append(assistant_message)
            
            return response
            
        except Exception as e:
            return AgentResponse(
                content=f"I apologize, but I encountered an error: {str(e)}",
                confidence=0.0,
                reasoning=f"Error in agent orchestration: {str(e)}",
                actions_taken=["error_handling"],
                metadata={"error": str(e), "orchestrator": "AgentOrchestrator"}
            )
    
    async def _route_to_agent(self, message: str, context: Optional[Dict[str, Any]] = None):
        if not self.routing_provider:
            return self.default_agent
            
        agent_capabilities = self.registry.get_agent_capabilities_for_routing()
        
        if len(agent_capabilities) <= 1:
            return self.default_agent
            
        routing_prompt = self._create_routing_prompt(message, agent_capabilities)
        
        try:
            routing_messages = [
                SystemMessage(content="You are an expert financial advisor routing system. Analyze the user query and determine which specialized agent should handle it."),
                HumanMessage(content=routing_prompt)
            ]
            
            routing_response = await self.routing_provider.generate_response(routing_messages)
            selected_agent_name = self._parse_routing_response(routing_response)
            
            selected_agent = self.registry.get_agent(selected_agent_name)
            return selected_agent if selected_agent else self.default_agent
            
        except Exception:
            return self.default_agent
    
    def _create_routing_prompt(self, user_message: str, agent_capabilities: Dict[str, str]) -> str:
        capabilities_text = "\n\n".join([
            f"Agent: {name}\n{capabilities}" 
            for name, capabilities in agent_capabilities.items()
        ])
        
        return f"""
User Query: "{user_message}"

Available Agents:
{capabilities_text}

Based on the user's query, which agent would be most appropriate to handle this request?

Instructions:
- Analyze the semantic meaning and financial domain of the user's query
- Match it to the agent with the most relevant expertise
- Consider the specific financial topic, complexity, and user intent
- Respond with ONLY the agent name (e.g., "SimpleAgent", "PortfolioAgent", etc.)
- If no specialized agent fits perfectly, choose the most general one

Agent Name:"""
    
    def _parse_routing_response(self, response: str) -> str:
        response = response.strip()
        
        first_line = response.split('\n')[0].strip()
        
        registered_agents = set(self.registry.get_all_agents().keys())
        
        if first_line in registered_agents:
            return first_line
            
        for agent_name in registered_agents:
            if agent_name.lower() in response.lower():
                return agent_name
                
        return self.default_agent.name if self.default_agent else "SimpleAgent"
    
    def register_agent(self, agent, capability: AgentCapability) -> None:
        self.registry.register_agent(agent, capability)
    
    def unregister_agent(self, agent_name: str) -> bool:
        return self.registry.unregister_agent(agent_name)
    
    def get_registered_agents(self) -> Dict[str, Any]:
        return self.registry.get_all_agents()
    
    def get_agent_capabilities_summary(self) -> Dict[str, str]:
        summary = {}
        for agent_name, capability in self.registry.list_all_capabilities().items():
            summary[agent_name] = f"{capability.domain}: {capability.description}"
        return summary
    
    def get_conversation_history(self) -> List[Message]:
        return self.conversation_history.copy()
    
    def clear_conversation_history(self) -> None:
        self.conversation_history.clear()