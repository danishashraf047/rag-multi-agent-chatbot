from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "LangGraph Multi-Agent Chatbot"
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", validation_alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        validation_alias="OPENAI_EMBEDDING_MODEL",
    )

    chroma_persist_dir: Path = Field(
        default=Path("./chroma_db"),
        validation_alias="CHROMA_PERSIST_DIR",
    )
    chroma_collection_name: str = Field(
        default="agent_knowledge",
        validation_alias="CHROMA_COLLECTION_NAME",
    )
    documents_dir: Path = Field(
        default=Path("./data/documents"),
        validation_alias="DOCUMENTS_DIR",
    )

    langsmith_tracing: bool = Field(default=False, validation_alias="LANGSMITH_TRACING")
    langsmith_api_key: str = Field(default="", validation_alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field(
        default="rag-multi-agent-chatbot",
        validation_alias="LANGSMITH_PROJECT",
    )

    request_timeout_seconds: float = Field(
        default=60.0,
        validation_alias="REQUEST_TIMEOUT_SECONDS",
    )
    max_retries: int = Field(default=2, validation_alias="MAX_RETRIES")


@lru_cache
def get_settings() -> Settings:
    return Settings()
