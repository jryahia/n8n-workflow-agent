"""
Tests for the n8n API client.
All network calls are mocked — no real n8n instance required.
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.n8n_client import N8nAPIError, N8nClient


def _make_response(status_code: int, body: dict | list) -> httpx.Response:
    """Helper: create a mock httpx.Response."""
    content = json.dumps(body).encode()
    return httpx.Response(
        status_code=status_code,
        content=content,
        headers={"content-type": "application/json"},
    )


@pytest.fixture
def client() -> N8nClient:
    return N8nClient(base_url="http://localhost:5678", api_key="test-api-key")


def test_headers_include_api_key(client: N8nClient) -> None:
    headers = client._headers()
    assert headers["X-N8N-API-KEY"] == "test-api-key"
    assert headers["Content-Type"] == "application/json"


def test_headers_no_api_key() -> None:
    c = N8nClient(base_url="http://localhost:5678", api_key="")
    headers = c._headers()
    assert "X-N8N-API-KEY" not in headers


@pytest.mark.asyncio
async def test_health_check_ok(client: N8nClient) -> None:
    mock_response = _make_response(200, {"status": "ok"})
    with patch.object(
        httpx.AsyncClient,
        "get",
        new=AsyncMock(return_value=mock_response),
    ):
        result = await client.health_check()
    assert result is True


@pytest.mark.asyncio
async def test_health_check_fail(client: N8nClient) -> None:
    with patch.object(
        httpx.AsyncClient,
        "get",
        new=AsyncMock(side_effect=httpx.ConnectError("refused")),
    ):
        result = await client.health_check()
    assert result is False


@pytest.mark.asyncio
async def test_list_workflows(client: N8nClient) -> None:
    workflows = [
        {"id": "1", "name": "Workflow A", "active": True},
        {"id": "2", "name": "Workflow B", "active": False},
    ]
    mock_response = _make_response(200, {"data": workflows})
    with patch.object(
        httpx.AsyncClient,
        "get",
        new=AsyncMock(return_value=mock_response),
    ):
        result = await client.list_workflows()
    assert len(result) == 2
    assert result[0]["name"] == "Workflow A"


@pytest.mark.asyncio
async def test_list_workflows_array_format(client: N8nClient) -> None:
    """n8n may return plain array instead of {data: []}."""
    workflows = [{"id": "1", "name": "WF", "active": False}]
    mock_response = _make_response(200, workflows)
    with patch.object(
        httpx.AsyncClient,
        "get",
        new=AsyncMock(return_value=mock_response),
    ):
        result = await client.list_workflows()
    assert len(result) == 1


@pytest.mark.asyncio
async def test_create_workflow(client: N8nClient) -> None:
    n8n_id = str(uuid.uuid4())
    created = {"id": n8n_id, "name": "Test", "active": False}
    mock_response = _make_response(201, created)

    workflow_json = {
        "name": "Test",
        "nodes": [],
        "connections": {},
        "settings": {"executionOrder": "v1"},
    }

    with patch.object(
        httpx.AsyncClient,
        "post",
        new=AsyncMock(return_value=mock_response),
    ):
        result = await client.create_workflow(workflow_json)

    assert result["id"] == n8n_id


@pytest.mark.asyncio
async def test_delete_workflow(client: N8nClient) -> None:
    mock_response = _make_response(200, {"success": True})
    with patch.object(
        httpx.AsyncClient,
        "delete",
        new=AsyncMock(return_value=mock_response),
    ):
        result = await client.delete_workflow("123")
    assert result is True


@pytest.mark.asyncio
async def test_activate_workflow(client: N8nClient) -> None:
    mock_response = _make_response(200, {"id": "123", "active": True})
    with patch.object(
        httpx.AsyncClient,
        "post",
        new=AsyncMock(return_value=mock_response),
    ):
        result = await client.activate_workflow("123")
    assert result["active"] is True


@pytest.mark.asyncio
async def test_api_error_raised_on_4xx(client: N8nClient) -> None:
    mock_response = _make_response(401, {"message": "Unauthorized"})
    with patch.object(
        httpx.AsyncClient,
        "get",
        new=AsyncMock(return_value=mock_response),
    ):
        with pytest.raises(N8nAPIError) as exc_info:
            await client.list_workflows()
    assert exc_info.value.status_code == 401
    assert "Unauthorized" in str(exc_info.value)


@pytest.mark.asyncio
async def test_api_error_raised_on_500(client: N8nClient) -> None:
    mock_response = _make_response(500, {"message": "Internal Server Error"})
    with patch.object(
        httpx.AsyncClient,
        "get",
        new=AsyncMock(return_value=mock_response),
    ):
        with pytest.raises(N8nAPIError) as exc_info:
            await client.list_workflows()
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_list_credentials(client: N8nClient) -> None:
    creds = [
        {"id": "cred-1", "name": "Telegram", "type": "telegramApi"},
        {"id": "cred-2", "name": "SMTP", "type": "smtp"},
    ]
    mock_response = _make_response(200, {"data": creds})
    with patch.object(
        httpx.AsyncClient,
        "get",
        new=AsyncMock(return_value=mock_response),
    ):
        result = await client.list_credentials()
    assert len(result) == 2
    assert result[0]["name"] == "Telegram"


def test_n8n_api_error_message() -> None:
    err = N8nAPIError("Test error message", status_code=404)
    assert str(err) == "Test error message"
    assert err.status_code == 404
