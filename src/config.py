import os
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "n8n Workflow Agent"
    app_version: str = "1.0.0"
    debug: bool = False

    # API Server
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/workflows.db",
        description="Async SQLAlchemy database URL",
    )

    # n8n Instance
    n8n_base_url: str = Field(default="http://localhost:5678")
    n8n_api_key: str = Field(default="")

    # LLM
    llm_provider: Literal["openai", "anthropic"] = "openai"
    openai_api_key: str = Field(default="")
    anthropic_api_key: str = Field(default="")
    llm_model: str = Field(default="gpt-4o")
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=4096, gt=0)

    # Workflow
    default_timezone: str = "UTC"
    max_nodes_per_workflow: int = 20

    # Security
    secret_key: str = Field(default="change-me-in-production-super-secret-key")

    @property
    def data_dir(self) -> str:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        os.makedirs(path, exist_ok=True)
        return path

    def update(self, **kwargs: object) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                object.__setattr__(self, key, value)


settings = Settings()
