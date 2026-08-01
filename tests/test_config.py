"""Tests for settings persistence — the Settings page writes through to .env."""

import os
from unittest.mock import patch

from src.config import Settings


def _persist_into(tmp_path, settings_obj, keys):
    """Run Settings.persist() against a throwaway .env under tmp_path."""
    fake_src = os.path.join(str(tmp_path), "src", "config.py")
    with patch("src.config.__file__", fake_src):
        return settings_obj.persist(keys)


def test_persist_creates_env_file(tmp_path):
    os.makedirs(tmp_path / "src", exist_ok=True)
    s = Settings(_env_file=None)
    s.update(n8n_base_url="http://n8n.local:5678", llm_model="gpt-4o-mini")

    path = _persist_into(tmp_path, s, ["n8n_base_url", "llm_model"])

    content = open(path, encoding="utf-8").read()
    assert "N8N_BASE_URL=http://n8n.local:5678" in content
    assert "LLM_MODEL=gpt-4o-mini" in content


def test_persist_rewrites_existing_key_in_place(tmp_path):
    os.makedirs(tmp_path / "src", exist_ok=True)
    env_path = tmp_path / ".env"
    env_path.write_text(
        "# comment\nLLM_MODEL=old-model\nAPI_PORT=8000\n", encoding="utf-8"
    )

    s = Settings(_env_file=None)
    s.update(llm_model="new-model")
    _persist_into(tmp_path, s, ["llm_model"])

    lines = env_path.read_text(encoding="utf-8").splitlines()
    assert lines.count("LLM_MODEL=new-model") == 1
    assert "LLM_MODEL=old-model" not in lines
    # Untouched keys and comments survive
    assert "API_PORT=8000" in lines
    assert "# comment" in lines


def test_persist_round_trips_through_a_fresh_settings_load(tmp_path):
    os.makedirs(tmp_path / "src", exist_ok=True)
    env_path = tmp_path / ".env"

    s = Settings(_env_file=None)
    s.update(llm_provider="anthropic", default_timezone="Europe/Paris")
    _persist_into(tmp_path, s, ["llm_provider", "default_timezone"])

    reloaded = Settings(_env_file=str(env_path))
    assert reloaded.llm_provider == "anthropic"
    assert reloaded.default_timezone == "Europe/Paris"


def test_api_key_for_known_and_unknown_providers():
    s = Settings(_env_file=None)
    s.update(openai_api_key="sk-abc", gemini_api_key="gm-xyz")
    assert s.api_key_for("openai") == "sk-abc"
    assert s.api_key_for("gemini") == "gm-xyz"
    assert s.api_key_for("nonexistent") == ""
