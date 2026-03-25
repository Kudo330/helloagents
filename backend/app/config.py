from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(extra="ignore")

    # AMap server-side API key
    amap_api_key: str = ""

    # AMap web key used by frontend
    amap_web_key: str = ""

    # Prefer Hello-Agents MCPTool-based AMap access, matching upstream chapter13 design.
    use_amap_mcp: bool = True

    # Unsplash API key
    unsplash_access_key: str = ""

    # Optional LLM config
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_provider: Optional[str] = "auto"
    llm_model: Optional[str] = None

    # Comma-separated origins
    cors_origins: str = "http://localhost:3000"


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    # Load .env at runtime without forcing tests to pick local values.
    load_dotenv(".env", override=False)
    return Settings()
