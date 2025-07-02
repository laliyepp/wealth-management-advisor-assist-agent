from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    
    # LLM Configuration
    llm_provider: str = "openrouter"  # primary provider
    fallback_providers: List[str] = ["openai"]  # fallback order
    
    # Model Configuration
    openai_model: str = "gpt-3.5-turbo"
    anthropic_model: str = "claude-3-sonnet-20240229"
    openrouter_model: str = "deepseek/deepseek-chat-v3-0324:free"
    
    # Model Parameters
    temperature: float = 0.7
    max_tokens: int = 2048
    
    # Database Configuration
    database_url: str = "sqlite:///./agent.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


_settings = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings