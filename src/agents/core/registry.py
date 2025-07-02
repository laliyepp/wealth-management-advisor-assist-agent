from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from .base import BaseAgent


@dataclass 
class AgentCapability:
    domain: str
    description: str
    expertise_areas: List[str]
    example_queries: List[str]


class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._capabilities: Dict[str, AgentCapability] = {}
        self._agent_configs: Dict[str, Dict[str, Any]] = {}
    
    def register_agent(self, agent: BaseAgent, capability: AgentCapability) -> None:
        agent_name = agent.name
        self._agents[agent_name] = agent
        self._capabilities[agent_name] = capability
        self._agent_configs[agent_name] = agent.config
    
    def unregister_agent(self, agent_name: str) -> bool:
        if agent_name in self._agents:
            del self._agents[agent_name]
            del self._capabilities[agent_name] 
            del self._agent_configs[agent_name]
            return True
        return False
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        return self._agents.get(agent_name)
    
    def get_all_agents(self) -> Dict[str, BaseAgent]:
        return self._agents.copy()
    
    def get_agent_capabilities_for_routing(self) -> Dict[str, str]:
        routing_info = {}
        for agent_name, capability in self._capabilities.items():
            routing_info[agent_name] = f"Domain: {capability.domain}\nExpertise: {', '.join(capability.expertise_areas)}\nDescription: {capability.description}"
        return routing_info
    
    def get_agent_capability(self, agent_name: str) -> Optional[AgentCapability]:
        return self._capabilities.get(agent_name)
    
    def list_all_capabilities(self) -> Dict[str, AgentCapability]:
        return self._capabilities.copy()
    
    def get_agent_count(self) -> int:
        return len(self._agents)
    
    def is_agent_registered(self, agent_name: str) -> bool:
        return agent_name in self._agents