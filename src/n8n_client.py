"""
REST client for the n8n API.
Handles workflow CRUD, activation/deactivation, and credential management.
"""

from typing import Any

import httpx

from src.config import settings


class N8nAPIError(Exception):
    def __init__(self, message: str, status_code: int = 0) -> None:
        super().__init__(message)
        self.status_code = status_code


class _WrappedAsyncClient(httpx.AsyncClient):
    """httpx client that reports transport failures as N8nAPIError.

    Without this, a stopped n8n instance raises httpx.ConnectError straight out
    of every client method; callers only catch N8nAPIError, so the API server
    turns a routine "n8n is offline" into a 500.
    """

    async def send(self, *args: Any, **kwargs: Any) -> httpx.Response:
        try:
            return await super().send(*args, **kwargs)
        except httpx.HTTPError as exc:
            raise N8nAPIError(
                f"Cannot reach n8n at {self.base_url}: {exc}"
            ) from exc


class N8nClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (base_url or settings.n8n_base_url).rstrip("/")
        self.api_key = api_key or settings.n8n_api_key
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key
        return headers

    def _client(self) -> httpx.AsyncClient:
        return _WrappedAsyncClient(
            base_url=self.base_url,
            headers=self._headers(),
            timeout=self._timeout,
        )

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code >= 400:
            try:
                detail = response.json().get("message", response.text[:200])
            except Exception:
                detail = response.text[:200]
            raise N8nAPIError(
                f"n8n API error {response.status_code}: {detail}",
                status_code=response.status_code,
            )

    # ── Health ────────────────────────────────────────────────────────────────

    async def health_check(self) -> bool:
        try:
            async with self._client() as client:
                response = await client.get("/healthz")
                return response.status_code == 200
        except Exception:
            return False

    # ── Workflows ─────────────────────────────────────────────────────────────

    async def list_workflows(self) -> list[dict[str, Any]]:
        async with self._client() as client:
            response = await client.get("/api/v1/workflows")
            self._raise_for_status(response)
            data = response.json()
            return data.get("data", data) if isinstance(data, dict) else data

    async def get_workflow(self, workflow_id: str) -> dict[str, Any]:
        async with self._client() as client:
            response = await client.get(f"/api/v1/workflows/{workflow_id}")
            self._raise_for_status(response)
            return response.json()

    async def create_workflow(
        self, workflow_json: dict[str, Any]
    ) -> dict[str, Any]:
        """POST /api/v1/workflows — create a new workflow."""
        payload = {
            "name": workflow_json.get("name", "Untitled Workflow"),
            "nodes": workflow_json.get("nodes", []),
            "connections": workflow_json.get("connections", {}),
            "settings": workflow_json.get("settings", {"executionOrder": "v1"}),
            "staticData": workflow_json.get("staticData"),
        }
        async with self._client() as client:
            response = await client.post("/api/v1/workflows", json=payload)
            self._raise_for_status(response)
            return response.json()

    async def update_workflow(
        self, workflow_id: str, workflow_json: dict[str, Any]
    ) -> dict[str, Any]:
        """PUT /api/v1/workflows/{id} — update an existing workflow."""
        async with self._client() as client:
            response = await client.put(
                f"/api/v1/workflows/{workflow_id}", json=workflow_json
            )
            self._raise_for_status(response)
            return response.json()

    async def delete_workflow(self, workflow_id: str) -> bool:
        async with self._client() as client:
            response = await client.delete(f"/api/v1/workflows/{workflow_id}")
            self._raise_for_status(response)
            return response.status_code in (200, 204)

    async def activate_workflow(self, workflow_id: str) -> dict[str, Any]:
        """POST /api/v1/workflows/{id}/activate"""
        async with self._client() as client:
            response = await client.post(
                f"/api/v1/workflows/{workflow_id}/activate"
            )
            self._raise_for_status(response)
            return response.json()

    async def deactivate_workflow(self, workflow_id: str) -> dict[str, Any]:
        """POST /api/v1/workflows/{id}/deactivate"""
        async with self._client() as client:
            response = await client.post(
                f"/api/v1/workflows/{workflow_id}/deactivate"
            )
            self._raise_for_status(response)
            return response.json()

    async def get_workflow_executions(
        self, workflow_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        async with self._client() as client:
            response = await client.get(
                "/api/v1/executions",
                params={"workflowId": workflow_id, "limit": limit},
            )
            self._raise_for_status(response)
            data = response.json()
            return data.get("data", data) if isinstance(data, dict) else data

    # ── Credentials ───────────────────────────────────────────────────────────

    async def list_credentials(self) -> list[dict[str, Any]]:
        async with self._client() as client:
            response = await client.get("/api/v1/credentials")
            self._raise_for_status(response)
            data = response.json()
            return data.get("data", data) if isinstance(data, dict) else data

    async def create_credential(
        self,
        name: str,
        cred_type: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "name": name,
            "type": cred_type,
            "data": data,
        }
        async with self._client() as client:
            response = await client.post("/api/v1/credentials", json=payload)
            self._raise_for_status(response)
            return response.json()

    async def delete_credential(self, credential_id: str) -> bool:
        async with self._client() as client:
            response = await client.delete(
                f"/api/v1/credentials/{credential_id}"
            )
            self._raise_for_status(response)
            return response.status_code in (200, 204)

    # ── Tags ──────────────────────────────────────────────────────────────────

    async def list_tags(self) -> list[dict[str, Any]]:
        async with self._client() as client:
            response = await client.get("/api/v1/tags")
            self._raise_for_status(response)
            data = response.json()
            return data.get("data", data) if isinstance(data, dict) else data

    # ── Executions ────────────────────────────────────────────────────────────

    async def execute_workflow(self, workflow_id: str) -> dict[str, Any]:
        """Trigger a manual execution of a workflow."""
        async with self._client() as client:
            response = await client.post(
                f"/api/v1/workflows/{workflow_id}/run"
            )
            self._raise_for_status(response)
            return response.json()


# Module-level default client instance
_default_client: N8nClient | None = None


def get_client() -> N8nClient:
    global _default_client
    if _default_client is None:
        _default_client = N8nClient()
    return _default_client


def refresh_client() -> N8nClient:
    """Re-create the default client from current settings (called after settings update)."""
    global _default_client
    _default_client = N8nClient(
        base_url=settings.n8n_base_url,
        api_key=settings.n8n_api_key,
    )
    return _default_client
