"""ReAct framework tools module."""

# This module can be extended with additional tools specific to wealth management
# For now, we use the base tools from src/utils/tools/

from ...utils.tools import AsyncWeaviateKnowledgeBase, get_news_events

__all__ = ["AsyncWeaviateKnowledgeBase", "get_news_events"]