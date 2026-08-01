import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ── LLM Provider Registry ─────────────────────────────────────────────────────
# All providers except native "openai"/"anthropic" speak the OpenAI Chat
# Completions API, so they only differ by base_url, api key, and default model.
# base_url == "" means a native SDK path (OpenAI json-mode / Anthropic messages).
LLM_PROVIDERS: dict[str, dict[str, str]] = {
    "openai": {
        "label": "OpenAI (GPT)",
        "default_model": "gpt-4o",
        "key_attr": "openai_api_key",
        "base_url": "",
    },
    "anthropic": {
        "label": "Anthropic (Claude)",
        "default_model": "claude-3-5-sonnet-20241022",
        "key_attr": "anthropic_api_key",
        "base_url": "",
    },
    "openrouter": {
        "label": "OpenRouter",
        "default_model": "openai/gpt-4o",
        "key_attr": "openrouter_api_key",
        "base_url": "https://openrouter.ai/api/v1",
    },
    "grok": {
        "label": "Grok (xAI)",
        "default_model": "grok-2-latest",
        "key_attr": "xai_api_key",
        "base_url": "https://api.x.ai/v1",
    },
    "gemini": {
        "label": "Gemini (Google)",
        "default_model": "gemini-2.0-flash",
        "key_attr": "gemini_api_key",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
    },
    "deepseek": {
        "label": "DeepSeek",
        "default_model": "deepseek-chat",
        "key_attr": "deepseek_api_key",
        "base_url": "https://api.deepseek.com/v1",
    },
    "kimi": {
        "label": "Kimi (Moonshot)",
        "default_model": "moonshot-v1-8k",
        "key_attr": "moonshot_api_key",
        "base_url": "https://api.moonshot.ai/v1",
    },
}


# Settings the UI is allowed to write back to .env (everything user-editable
# on the Settings page — deployment knobs like API_HOST stay file-only).
_PERSISTED_KEYS: tuple[str, ...] = (
    "n8n_base_url",
    "n8n_api_key",
    "llm_provider",
    "llm_model",
    "llm_temperature",
    "default_timezone",
    *(meta["key_attr"] for meta in LLM_PROVIDERS.values()),
)


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
    llm_provider: str = "openai"
    openai_api_key: str = Field(default="")
    anthropic_api_key: str = Field(default="")
    openrouter_api_key: str = Field(default="")
    xai_api_key: str = Field(default="")
    gemini_api_key: str = Field(default="")
    deepseek_api_key: str = Field(default="")
    moonshot_api_key: str = Field(default="")
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

    def persist(self, keys: list[str] | None = None) -> str:
        """Write the current values of `keys` back to the project .env file.

        `update()` only changes this process's in-memory settings, so without
        this everything configured in the Settings page is lost on restart.
        Existing lines are rewritten in place; unknown lines are left alone.
        """
        keys = keys or list(_PERSISTED_KEYS)
        env_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".env"
        )

        wanted = {
            k.upper(): str(getattr(self, k))
            for k in keys
            if hasattr(self, k)
        }

        lines: list[str] = []
        if os.path.exists(env_path):
            with open(env_path, encoding="utf-8") as fh:
                lines = fh.read().splitlines()

        seen: set[str] = set()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            name = stripped.split("=", 1)[0].strip().upper()
            if name in wanted:
                lines[i] = f"{name}={wanted[name]}"
                seen.add(name)

        missing = [f"{k}={v}" for k, v in wanted.items() if k not in seen]
        if missing:
            if lines and lines[-1].strip():
                lines.append("")
            lines.append("# Written by the Settings page")
            lines.extend(missing)

        with open(env_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")

        return env_path

    def api_key_for(self, provider: str) -> str:
        """Return the configured API key for the given LLM provider."""
        meta = LLM_PROVIDERS.get(provider)
        if not meta:
            return ""
        return str(getattr(self, meta["key_attr"], "") or "")


settings = Settings()
