"""
Tests for workflow generator utilities (non-LLM parts).
LLM integration tests require API keys and are skipped in CI.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from src.workflow_generator import (
    _derive_name_from_prompt,
    _extract_json_from_text,
    build_minimal_workflow,
)
from src.workflow_validator import validate_workflow


@pytest.fixture
def openai_key():
    """generate_workflow refuses to call a provider with no key configured,
    so mocked-LLM tests must supply one."""
    from src.config import settings

    original = settings.openai_api_key
    settings.update(openai_api_key="sk-test-key")
    yield
    object.__setattr__(settings, "openai_api_key", original)


def test_derive_name_short_prompt():
    result = _derive_name_from_prompt("send email every day")
    assert "Send" in result or "send" in result.lower()


def test_derive_name_long_prompt():
    long = "create a workflow that monitors an API endpoint every minute and sends a Slack notification when the response time exceeds 2 seconds"
    result = _derive_name_from_prompt(long)
    assert len(result) <= 64


def test_derive_name_empty_prompt():
    result = _derive_name_from_prompt("")
    assert result == "Generated Workflow"


def test_extract_json_from_text_plain():
    raw = '{"name": "test", "nodes": []}'
    assert _extract_json_from_text(raw) == raw


def test_extract_json_from_text_with_fences():
    raw = '```json\n{"name": "test"}\n```'
    result = _extract_json_from_text(raw)
    assert result.startswith("{")
    assert "test" in result


def test_extract_json_from_text_with_preamble():
    raw = 'Here is the workflow:\n{"name": "result", "nodes": []}\nEnd.'
    result = _extract_json_from_text(raw)
    assert result.startswith("{")


def test_build_minimal_workflow_structure():
    wf = build_minimal_workflow("Test Workflow")
    assert wf["name"] == "Test Workflow"
    assert len(wf["nodes"]) == 1
    assert wf["nodes"][0]["type"] == "n8n-nodes-base.start"
    assert wf["active"] is False
    assert wf["settings"]["executionOrder"] == "v1"


def test_build_minimal_workflow_is_valid():
    wf = build_minimal_workflow("Minimal Test")
    result = validate_workflow(wf)
    assert result.valid is True


def test_build_minimal_workflow_unique_version_id():
    wf1 = build_minimal_workflow("WF1")
    wf2 = build_minimal_workflow("WF2")
    assert wf1["versionId"] != wf2["versionId"]


@pytest.mark.asyncio
async def test_generate_workflow_openai_mocked(openai_key):
    """Test generate_workflow with a mocked OpenAI response."""
    import json
    from src.workflow_generator import generate_workflow

    mock_workflow = {
        "name": "Mocked Crypto Alert",
        "nodes": [
            {
                "id": str(uuid.uuid4()),
                "name": "Schedule Trigger",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1,
                "position": [250, 300],
                "parameters": {
                    "rule": {"interval": [{"field": "hours", "hoursInterval": 1}]}
                },
                "disabled": False,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Fetch Price",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4,
                "position": [450, 300],
                "parameters": {
                    "method": "GET",
                    "url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
                    "options": {},
                },
                "disabled": False,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Send Email",
                "type": "n8n-nodes-base.emailSend",
                "typeVersion": 2,
                "position": [650, 300],
                "parameters": {
                    "fromEmail": "bot@example.com",
                    "toEmail": "user@example.com",
                    "subject": "Bitcoin Price",
                    "emailFormat": "html",
                    "message": "<p>{{ $json.bitcoin.usd }}</p>",
                    "options": {},
                },
                "disabled": False,
            },
        ],
        "connections": {
            "Schedule Trigger": {
                "main": [[{"node": "Fetch Price", "type": "main", "index": 0}]]
            },
            "Fetch Price": {
                "main": [[{"node": "Send Email", "type": "main", "index": 0}]]
            },
        },
        "pinData": {},
        "versionId": str(uuid.uuid4()),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "tags": [],
        "staticData": None,
    }

    with patch(
        "src.workflow_generator._generate_openai",
        new=AsyncMock(return_value=(mock_workflow, 500)),
    ):
        result = await generate_workflow(
            "Send me an email with Bitcoin price every hour",
            llm_provider="openai",
            llm_model="gpt-4o",
        )

    assert result["workflow_json"]["name"] == "Mocked Crypto Alert"
    assert result["llm_provider"] == "openai"
    assert result["tokens_used"] == 500
    assert result["latency_ms"] >= 0


@pytest.mark.asyncio
async def test_generate_workflow_validation_failure(openai_key):
    """Test that invalid LLM output raises ValueError."""
    from src.workflow_generator import generate_workflow

    bad_workflow = {"name": "Bad", "nodes": "not-a-list"}

    with patch(
        "src.workflow_generator._generate_openai",
        new=AsyncMock(return_value=(bad_workflow, 100)),
    ):
        with pytest.raises(ValueError, match="validation"):
            await generate_workflow("some prompt", llm_provider="openai")


@pytest.mark.asyncio
async def test_generate_workflow_without_api_key_fails_fast():
    """A missing key must produce a readable error, not a wrapped SDK failure."""
    from src.config import settings
    from src.workflow_generator import generate_workflow

    original = settings.openai_api_key
    settings.update(openai_api_key="")
    object.__setattr__(settings, "openai_api_key", "")
    try:
        with pytest.raises(ValueError, match="No API key configured"):
            await generate_workflow("some prompt", llm_provider="openai")
    finally:
        object.__setattr__(settings, "openai_api_key", original)


@pytest.mark.asyncio
async def test_generate_workflow_unknown_provider():
    from src.workflow_generator import generate_workflow

    with pytest.raises(ValueError, match="Unknown LLM provider"):
        await generate_workflow("some prompt", llm_provider="not-a-provider")


def test_node_templates_reference_is_valid_json():
    """Ensure the node reference JSON we embed in the LLM prompt is valid."""
    import json
    from src.node_templates import build_node_reference_json

    ref = build_node_reference_json()
    assert isinstance(ref, dict)
    serialized = json.dumps(ref)
    parsed = json.loads(serialized)
    assert len(parsed) > 5


def test_all_node_templates_have_required_keys():
    from src.node_templates import NODE_TEMPLATES

    for key, tpl in NODE_TEMPLATES.items():
        assert "type" in tpl, f"Template '{key}' missing 'type'"
        assert "typeVersion" in tpl, f"Template '{key}' missing 'typeVersion'"
        assert "parameters" in tpl, f"Template '{key}' missing 'parameters'"
        assert "description" in tpl, f"Template '{key}' missing 'description'"
        assert isinstance(tpl["type"], str), f"Template '{key}' type must be str"
        assert tpl["type"].startswith("n8n-nodes-base."), f"Template '{key}' type must be n8n node type"
