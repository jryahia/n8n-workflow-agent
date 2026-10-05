"""
Library view — saved workflows, built-in templates, import/export.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Callable

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
    tag_chip,
)


class LibraryView(ft.Column):
    def __init__(
        self,
        api_base: str,
        on_open_editor: Callable[[dict[str, Any]], None],
    ) -> None:
        super().__init__(expand=True, spacing=0)
        self._api_base = api_base
        self._on_open_editor = on_open_editor

        self._search_field = ft.TextField(
            hint_text="Search workflows...",
            prefix_icon=ft.Icons.SEARCH,
            border_color=BORDER,
            focused_border_color=ACCENT,
            bgcolor=SURFACE2,
            color=TEXT,
            hint_style=ft.TextStyle(color=TEXT_MUTED),
            text_size=13,
            on_change=self._on_search_change,
            expand=True,
        )

        self._tab_index = 0
        self._workflows_data: list[dict[str, Any]] = []
        self._templates_data: list[dict[str, Any]] = []
        self._search_query = ""

        self._workflows_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        self._templates_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

        self._tabs = build_tabs(
            [
                (
                    "Generated",
                    "auto_awesome",
                    ft.Container(
                        content=self._workflows_col,
                        padding=ft.Padding.only(top=16),
                        expand=True,
                    ),
                ),
                (
                    "Templates",
                    "bookmark",
                    ft.Container(
                        content=self._templates_col,
                        padding=ft.Padding.only(top=16),
                        expand=True,
                    ),
                ),
                (
                    "Import",
                    "upload_file",
                    ft.Container(
                        content=self._build_import_panel(),
                        padding=ft.Padding.only(top=16),
                        expand=True,
                    ),
                ),
            ],
            on_change=self._on_tab_change,
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
                    self._search_field,
                    ft.Container(width=8),
                    accent_button(
                        "Refresh",
                        icon=ft.Icons.REFRESH,
                        on_click=lambda e: asyncio.create_task(self._load_all()),
                    ),
                ],
                spacing=0,
            ),
            padding=16,
            bgcolor=SURFACE,
            border_radius=0,
            border=ft.Border.all(2, BORDER),
        )

    def _build_import_panel(self) -> ft.Container:
        self._import_text = ft.TextField(
            label="Paste workflow JSON here",
            multiline=True,
            min_lines=10,
            max_lines=20,
            border_color=BORDER,
            focused_border_color=ACCENT,
            bgcolor=SURFACE2,
            color=TEXT,
            text_size=12,
            text_style=ft.TextStyle(font_family="monospace"),
            expand=True,
        )
        self._import_name = ft.TextField(
            label="Workflow Name",
            value="Imported Workflow",
            border_color=BORDER,
            focused_border_color=ACCENT,
            bgcolor=SURFACE2,
            color=TEXT,
            text_size=13,
        )

        return ft.Container(
            content=ft.Column(
                [
                    section_title("Import Workflow JSON", 14),
                    ft.Container(height=8),
                    muted_text("Paste n8n workflow JSON exported from n8n or another agent session."),
                    ft.Container(height=12),
                    self._import_name,
                    ft.Container(height=8),
                    self._import_text,
                    ft.Container(height=12),
                    ft.Row(
                        [
                            accent_button(
                                "Import Workflow",
                                icon=ft.Icons.UPLOAD,
                                on_click=lambda e: asyncio.create_task(self._import_workflow()),
                            ),
                            ghost_button("Clear", on_click=self._clear_import, icon=ft.Icons.CLEAR),
                        ],
                        spacing=8,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            expand=True,
        )

    def did_mount(self) -> None:
        asyncio.create_task(self._load_all())

    async def _load_all(self) -> None:
        await asyncio.gather(
            self._load_workflows(),
            self._load_templates(),
        )

    async def _load_workflows(self) -> None:
        self._workflows_col.controls = [loading_spinner("Loading workflows...")]
        try:
            self._workflows_col.update()
        except Exception:
            pass

        try:
            params: dict[str, str] = {}
            if self._search_query:
                params["search"] = self._search_query

            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    f"{self._api_base}/workflows",
                    params=params,
                )
            if response.status_code == 200:
                self._workflows_data = response.json()
                self._render_workflows()
            else:
                self._workflows_col.controls = [
                    muted_text(f"Error loading workflows: {response.status_code}")
                ]
        except Exception as exc:
            self._workflows_col.controls = [muted_text(f"Error: {exc}")]

        try:
            self._workflows_col.update()
        except Exception:
            pass

    async def _load_templates(self) -> None:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(f"{self._api_base}/templates")
            if response.status_code == 200:
                self._templates_data = response.json()
                self._render_templates()
        except Exception:
            pass

    def _render_workflows(self) -> None:
        if not self._workflows_data:
            self._workflows_col.controls = [
                empty_state(
                    ft.Icons.FOLDER_OPEN,
                    "No workflows yet",
                    "Generate a workflow from the Prompt tab to see it here",
                )
            ]
            return

        cards = [self._workflow_card(wf) for wf in self._workflows_data]
        self._workflows_col.controls = cards

    def _workflow_card(self, wf: dict[str, Any]) -> ft.Container:
        name = wf.get("name", "Untitled")
        prompt = wf.get("prompt", "")
        deployed = wf.get("deployed", False)
        active = wf.get("active", False)
        created = wf.get("created_at", "")[:10]
        wf_id = wf.get("id", "")

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
                            status_badge("Active", active) if active else status_badge("Inactive", False),
                            ft.Container(width=4),
                            ft.Container(
                                content=ft.Text(
                                    "Deployed" if deployed else "Local",
                                    size=11,
                                    color=SUCCESS if deployed else TEXT_MUTED,
                                ),
                                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                border_radius=0,
                                bgcolor=(SUCCESS + "22") if deployed else SURFACE,
                            ),
                        ],
                        spacing=6,
                    ),
                    ft.Text(
                        prompt[:100] + ("..." if len(prompt) > 100 else ""),
                        size=12,
                        color=TEXT_MUTED,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Container(height=4),
                    ft.Row(
                        [
                            muted_text(created),
                            ft.Container(expand=True),
                            ghost_button(
                                "Edit",
                                icon=ft.Icons.EDIT,
                                on_click=lambda e, id=wf_id: asyncio.create_task(
                                    self._open_in_editor(id)
                                ),
                            ),
                            ghost_button(
                                "Deploy",
                                icon=ft.Icons.ROCKET_LAUNCH,
                                on_click=lambda e, id=wf_id: asyncio.create_task(
                                    self._deploy_workflow(id)
                                ),
                            ),
                            ghost_button(
                                "Export",
                                icon=ft.Icons.DOWNLOAD,
                                on_click=lambda e, id=wf_id: asyncio.create_task(
                                    self._export_workflow(id, name)
                                ),
                            ),
                            danger_button(
                                "Delete",
                                icon=ft.Icons.DELETE,
                                on_click=lambda e, id=wf_id: asyncio.create_task(
                                    self._delete_workflow(id)
                                ),
                            ),
                        ],
                        spacing=4,
                    ),
                ],
                spacing=4,
            ),
            padding=14,
            bgcolor=SURFACE,
            border_radius=0,
            border=ft.Border.all(2, BORDER),
        )

    def _render_templates(self) -> None:
        if not self._templates_data:
            self._templates_col.controls = [
                muted_text("No templates available")
            ]
            return

        cards = [self._template_card(t) for t in self._templates_data]
        self._templates_col.controls = cards

    def _template_card(self, tpl: dict[str, Any]) -> ft.Container:
        name = tpl.get("name", "")
        description = tpl.get("description", "")
        category = tpl.get("category", "")
        tags: list[str] = tpl.get("tags", [])
        tpl_id = tpl.get("id", "")

        tag_row = ft.Row(
            [tag_chip(t) for t in tags[:4]],
            spacing=4,
            wrap=True,
        )

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
                            ft.Container(
                                content=ft.Text(category, size=11, color=ACCENT),
                                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                border_radius=0,
                                bgcolor=ACCENT + "22",
                            ),
                        ]
                    ),
                    ft.Text(description, size=12, color=TEXT_MUTED, max_lines=2),
                    ft.Container(height=4),
                    tag_row,
                    ft.Container(height=4),
                    ft.Row(
                        [
                            ft.Container(expand=True),
                            accent_button(
                                "Use Template",
                                icon=ft.Icons.PLAY_ARROW,
                                on_click=lambda e, id=tpl_id: asyncio.create_task(
                                    self._use_template(id)
                                ),
                            ),
                        ]
                    ),
                ],
                spacing=4,
            ),
            padding=14,
            bgcolor=SURFACE,
            border_radius=0,
            border=ft.Border.all(2, BORDER),
        )

    def _on_search_change(self, e: ft.ControlEvent) -> None:
        self._search_query = (self._search_field.value or "").strip()
        asyncio.create_task(self._load_workflows())

    def _on_tab_change(self, e: ft.ControlEvent) -> None:
        self._tab_index = e.control.selected_index

    async def _open_in_editor(self, workflow_id: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(f"{self._api_base}/workflows/{workflow_id}")
            if response.status_code == 200:
                self._on_open_editor(response.json())
            else:
                show_snack(self.page, "Failed to load workflow", error=True)
        except Exception as exc:
            show_snack(self.page, f"Error: {exc}", error=True)

    async def _deploy_workflow(self, workflow_id: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self._api_base}/workflows/{workflow_id}/deploy",
                    json={"activate": False},
                )
            data = response.json()
            if data.get("success"):
                show_snack(self.page, f"Deployed! ID: {data.get('n8n_workflow_id', '')}")
                await self._load_workflows()
            else:
                show_snack(self.page, data.get("message", "Failed"), error=True)
        except Exception as exc:
            show_snack(self.page, f"Deploy error: {exc}", error=True)

    async def _delete_workflow(self, workflow_id: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.delete(f"{self._api_base}/workflows/{workflow_id}")
            if response.status_code == 200:
                show_snack(self.page, "Workflow deleted")
                await self._load_workflows()
            else:
                show_snack(self.page, "Delete failed", error=True)
        except Exception as exc:
            show_snack(self.page, f"Error: {exc}", error=True)

    async def _export_workflow(self, workflow_id: str, name: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(f"{self._api_base}/workflows/{workflow_id}/export")
            if response.status_code == 200:
                from src.export import generate_export_filename, get_default_export_dir

                filename = generate_export_filename(name)
                export_path = get_default_export_dir() / filename
                export_path.write_text(
                    json.dumps(response.json(), indent=2), encoding="utf-8"
                )
                show_snack(self.page, f"Exported to {export_path}")
            else:
                show_snack(self.page, "Export failed", error=True)
        except Exception as exc:
            show_snack(self.page, f"Export error: {exc}", error=True)

    async def _use_template(self, template_id: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"{self._api_base}/templates/{template_id}/use"
                )
            if response.status_code == 200:
                data = response.json()
                show_snack(self.page, f"Created from template: {data.get('name', '')}")
                await self._load_workflows()
                self._on_open_editor(data)
            else:
                show_snack(self.page, "Failed to use template", error=True)
        except Exception as exc:
            show_snack(self.page, f"Error: {exc}", error=True)

    async def _import_workflow(self) -> None:
        raw = (self._import_text.value or "").strip()
        if not raw:
            show_snack(self.page, "Please paste workflow JSON first", error=True)
            return
        name = self._import_name.value or "Imported Workflow"
        try:
            wf_json = json.loads(raw)
        except json.JSONDecodeError as exc:
            show_snack(self.page, f"Invalid JSON: {exc}", error=True)
            return

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"{self._api_base}/import",
                    json={"name": name, "workflow_json": wf_json, "prompt": "Imported"},
                )
            if response.status_code == 200:
                data = response.json()
                show_snack(self.page, f"Imported: {data.get('name', '')}")
                self._import_text.value = ""
                self._import_text.update()
                await self._load_workflows()
            else:
                detail = response.json().get("detail", response.text)
                show_snack(self.page, f"Import failed: {detail}", error=True)
        except Exception as exc:
            show_snack(self.page, f"Import error: {exc}", error=True)

    def _clear_import(self, e: ft.ControlEvent) -> None:
        self._import_text.value = ""
        self._import_name.value = "Imported Workflow"
        self._import_text.update()
        self._import_name.update()
