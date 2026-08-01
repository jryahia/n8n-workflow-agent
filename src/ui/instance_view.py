"""
Instance view — manage the connected n8n instance.
Shows deployed workflows, allows activation/deactivation and deletion.
"""

import asyncio
from typing import Any

import flet as ft
import httpx

from src.ui.components import (
    ACCENT,
    BORDER,
    ERROR,
    SUCCESS,
    SURFACE,
    SURFACE2,
    TEXT,
    TEXT_MUTED,
    WARNING,
    accent_button,
    build_tabs,
    danger_button,
    divider,
    empty_state,
    ghost_button,
    loading_spinner,
    muted_text,
    section_title,
    show_snack,
    status_badge,
)


class InstanceView(ft.Column):
    def __init__(self, api_base: str) -> None:
        super().__init__(expand=True, spacing=0)
        self._api_base = api_base
        self._workflows: list[dict[str, Any]] = []
        self._credentials: list[dict[str, Any]] = []
        self._connected = False

        self._connection_indicator = ft.Container(
            content=ft.Row(
                [
                    ft.Container(width=10, height=10, border_radius=0, bgcolor=TEXT_MUTED),
                    ft.Text("Not connected", size=13, color=TEXT_MUTED),
                ],
                spacing=6,
                tight=True,
            ),
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            border_radius=0,
            bgcolor=SURFACE2,
        )

        self._workflows_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        self._creds_col = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)

        self._tabs = build_tabs(
            [
                (
                    "Workflows",
                    "account_tree",
                    ft.Container(
                        content=self._workflows_col,
                        padding=ft.Padding.only(top=16),
                        expand=True,
                    ),
                ),
                (
                    "Credentials",
                    "vpn_key",
                    ft.Container(
                        content=self._creds_col,
                        padding=ft.Padding.only(top=16),
                    ),
                ),
            ]
        )

        self.controls = [
            self._build_header(),
            ft.Container(height=12),
            self._tabs,
        ]

    def _build_header(self) -> ft.Container:
        return ft.Container(
            content=ft.Row(
                [
                    self._connection_indicator,
                    ft.Container(expand=True),
                    accent_button(
                        "Check Connection",
                        icon=ft.Icons.WIFI,
                        on_click=lambda e: asyncio.create_task(self._check_connection()),
                    ),
                    ghost_button(
                        "Refresh",
                        icon=ft.Icons.REFRESH,
                        on_click=lambda e: asyncio.create_task(self._load_all()),
                    ),
                ],
                spacing=8,
            ),
            padding=16,
            bgcolor=SURFACE,
            border_radius=0,
            border=ft.Border.all(2, BORDER),
        )

    def did_mount(self) -> None:
        asyncio.create_task(self._check_connection())

    async def _check_connection(self) -> None:
        self._set_connection_status(None)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self._api_base}/n8n/health")
            data = response.json()
            self._connected = data.get("reachable", False)
            self._set_connection_status(self._connected)
            if self._connected:
                await self._load_all()
            else:
                url = data.get("url", "")
                self._workflows_col.controls = [
                    empty_state(
                        "🔌",
                        "n8n instance not reachable",
                        f"Configure the n8n URL in Settings.\nCurrent URL: {url}",
                    )
                ]
                try:
                    self._workflows_col.update()
                except Exception:
                    pass
        except Exception as exc:
            self._connected = False
            self._set_connection_status(False)
            self._workflows_col.controls = [muted_text(f"Connection error: {exc}")]
            try:
                self._workflows_col.update()
            except Exception:
                pass

    def _set_connection_status(self, connected: bool | None) -> None:
        if connected is None:
            color = WARNING
            label = "Checking..."
        elif connected:
            color = SUCCESS
            label = "Connected"
        else:
            color = ERROR
            label = "Not connected"

        self._connection_indicator.content = ft.Row(
            [
                ft.Container(width=10, height=10, border_radius=0, bgcolor=color),
                ft.Text(label, size=13, color=color),
            ],
            spacing=6,
            tight=True,
        )
        try:
            self._connection_indicator.update()
        except Exception:
            pass

    async def _load_all(self) -> None:
        await asyncio.gather(
            self._load_workflows(),
            self._load_credentials(),
        )

    async def _load_workflows(self) -> None:
        self._workflows_col.controls = [loading_spinner("Loading n8n workflows...")]
        try:
            self._workflows_col.update()
        except Exception:
            pass

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(f"{self._api_base}/n8n/workflows")

            if response.status_code == 200:
                self._workflows = response.json()
                self._render_workflows()
            elif response.status_code == 502:
                detail = response.json().get("detail", "n8n unreachable")
                self._workflows_col.controls = [
                    empty_state("🔌", "Cannot reach n8n", detail)
                ]
            else:
                self._workflows_col.controls = [
                    muted_text(f"Error {response.status_code}: {response.text[:100]}")
                ]
        except Exception as exc:
            self._workflows_col.controls = [muted_text(f"Error: {exc}")]

        try:
            self._workflows_col.update()
        except Exception:
            pass

    def _render_workflows(self) -> None:
        if not self._workflows:
            self._workflows_col.controls = [
                empty_state(
                    "📋",
                    "No workflows in n8n",
                    "Deploy a workflow from the Library tab to see it here",
                )
            ]
            return

        self._workflows_col.controls = [self._workflow_card(wf) for wf in self._workflows]

    def _workflow_card(self, wf: dict[str, Any]) -> ft.Container:
        wf_id = str(wf.get("id", ""))
        name = wf.get("name", "Untitled")
        active = wf.get("active", False)
        created = (wf.get("createdAt") or "")[:10]

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                name,
                                size=14,
                                weight=ft.FontWeight.W_600,
                                color=TEXT,
                                expand=True,
                            ),
                            status_badge("Active", active),
                        ],
                        spacing=6,
                    ),
                    ft.Row(
                        [
                            muted_text(f"ID: {wf_id}"),
                            ft.Container(expand=True),
                            muted_text(f"Created: {created}"),
                        ],
                        spacing=4,
                    ),
                    ft.Container(height=4),
                    ft.Row(
                        [
                            (
                                ghost_button(
                                    "Deactivate",
                                    icon=ft.Icons.PAUSE,
                                    on_click=lambda e, id=wf_id: asyncio.create_task(
                                        self._deactivate(id)
                                    ),
                                    color=WARNING,
                                )
                                if active
                                else ghost_button(
                                    "Activate",
                                    icon=ft.Icons.PLAY_ARROW,
                                    on_click=lambda e, id=wf_id: asyncio.create_task(
                                        self._activate(id)
                                    ),
                                    color=SUCCESS,
                                )
                            ),
                            danger_button(
                                "Delete",
                                icon=ft.Icons.DELETE,
                                on_click=lambda e, id=wf_id: asyncio.create_task(
                                    self._delete_workflow(id)
                                ),
                            ),
                        ],
                        spacing=6,
                    ),
                ],
                spacing=4,
            ),
            padding=14,
            bgcolor=SURFACE,
            border_radius=0,
            border=ft.Border.all(
                1, SUCCESS + "66" if active else BORDER
            ),
        )

    async def _activate(self, workflow_id: str) -> None:
        # These ids come from n8n itself, so talk to n8n directly — the local
        # /workflows/{id}/activate endpoint keys off our own workflow ids.
        try:
            from src.n8n_client import N8nClient
            await N8nClient().activate_workflow(workflow_id)
            show_snack(self.page, "Workflow activated")
            await self._load_workflows()
        except Exception as exc:
            show_snack(self.page, f"Error: {exc}", error=True)

    async def _deactivate(self, workflow_id: str) -> None:
        try:
            from src.n8n_client import N8nClient
            client_n8n = N8nClient()
            await client_n8n.deactivate_workflow(workflow_id)
            show_snack(self.page, "Workflow deactivated")
            await self._load_workflows()
        except Exception as exc:
            show_snack(self.page, f"Error: {exc}", error=True)

    async def _delete_workflow(self, workflow_id: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.delete(
                    f"{self._api_base}/n8n/workflows/{workflow_id}"
                )
            if response.status_code == 200:
                show_snack(self.page, "Workflow deleted from n8n")
                await self._load_workflows()
            else:
                detail = response.json().get("detail", response.text)
                show_snack(self.page, f"Delete failed: {detail}", error=True)
        except Exception as exc:
            show_snack(self.page, f"Error: {exc}", error=True)

    async def _load_credentials(self) -> None:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(f"{self._api_base}/n8n/credentials")
            if response.status_code == 200:
                self._credentials = response.json()
                self._render_credentials()
        except Exception:
            pass

    def _render_credentials(self) -> None:
        if not self._credentials:
            self._creds_col.controls = [muted_text("No credentials found in n8n")]
            return

        items: list[ft.Control] = [section_title("Credentials", 14), divider(), ft.Container(height=4)]
        for cred in self._credentials:
            items.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text("🔑", size=16),
                            ft.Column(
                                [
                                    ft.Text(cred.get("name", ""), size=13, color=TEXT),
                                    ft.Text(cred.get("type", ""), size=11, color=TEXT_MUTED),
                                ],
                                spacing=2,
                                tight=True,
                                expand=True,
                            ),
                            muted_text(f"ID: {str(cred.get('id', ''))[:8]}"),
                        ],
                        spacing=8,
                    ),
                    padding=10,
                    bgcolor=SURFACE2,
                    border_radius=0,
                    border=ft.Border.all(2, BORDER),
                )
            )

        self._creds_col.controls = items
        try:
            self._creds_col.update()
        except Exception:
            pass
