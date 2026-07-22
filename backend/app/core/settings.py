from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    supabase_url: str
    supabase_secret_key: str = Field(
        validation_alias=AliasChoices(
            "SUPABASE_SECRET_KEY",
            "SUPABASE_SERVICE_ROLE_KEY",
        )
    )
    ai_provider: str = "groq"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_chat_model: str = "llama-3.1-8b-instant"
    xai_api_key: str = ""
    xai_base_url: str = "https://api.x.ai/v1"
    xai_chat_model: str = "grok-4.5"
    ai_agent_enabled: bool = False
    ai_agent_max_tool_calls: int = 6
    ai_health_disclaimer_enabled: bool = True
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8001"
    sslcommerz_store_id: str = ""
    sslcommerz_store_password: str = ""
    sslcommerz_sandbox: bool = True

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
