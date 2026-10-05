"""
Editor view — visual workflow editor with node list, parameter editor, JSON view.
"""

import asyncio
import json
import uuid
from typing import Any, Callable

import flet as ft
import httpx

from src.ui.components import (
    ACCENT,
    BG,
    BORDER,
    ERROR,
    SURFACE,
    SURFACE2,
    TEXT,
    TEXT_MUTED,
    WARNING,
    accent_button,
    build_tabs,
    connection_diagram,
    danger_button,
    divider,
    ghost_button,
    json_text_view,
    loading_spinner,
    muted_text,
    node_card,
    section_title,
    show_snack,
    status_badge,
    theme_container,
)
from src.node_templates import NODE_TEMPLATES


class EditorView(ft.Column):
    def __init__(self, api_base: str) -> None:
        super().__init__(expand=True, spacing=0)
        self._api_base = api_base
        self._workflow: dict[str, Any] | None = None
        self._workflow_id: str | None = None
        self._selected_node_idx: int | None = None
        self._dirty = False

        self._node_list_col = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)
        self._detail_panel = ft.Column(
            [muted_text("Select a node to edit its parameters")],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
        self._diagram_container = ft.Container(
            content=muted_text("Load a workflow to see the connection diagram"),
            padding=12,
            bgcolor=SURFACE2,
            border_radius=0,
            border=ft.Border.all(2, BORDER),
        )
        self._json_container = ft.Container(
            content=muted_text("No workflow loaded"),
            padding=12,
            bgcolor="#0d0d0d",
            border_radius=0,
            height=400,
        )
        self._name_field = ft.TextField(
            label="Workflow Name",
            border_color=BORDER,
            focused_border_color=ACCENT,
            bgcolor=SURFACE2,
            color=TEXT,
            text_size=14,
            on_change=self._on_name_change,
        )
        self._status_text = muted_text("No workflow loaded")

        self._tabs = build_tabs(
            [
                (
                    "Nodes",
                    "layers",
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Container(
                                    content=self._node_list_col,
                                    width=280,
                                    border=ft.Border.only(right=ft.BorderSide(2, BORDER)),
                                    padding=ft.Padding.only(right=12),
                                ),
                                ft.Container(
                                    content=self._detail_panel,
                                    expand=True,
                                    padding=ft.Padding.only(left=12),
                                ),
                            ],
                            expand=True,
                            spacing=0,
                        ),
                        padding=ft.Padding.only(top=16),
                        expand=True,
                    ),
                ),
                (
                    "Diagram",
                    "account_tree",
                    ft.Container(
                        content=self._diagram_container,
                        padding=ft.Padding.only(top=16),
                        expand=True,
                    ),
                ),
                (
                    "JSON",
                    "code",
                    ft.Container(
                        content=self._json_container,
                        padding=ft.Padding.only(top=16),
                        expand=True,
                    ),
                ),
            ]
        )

        self.controls = [
            self._build_toolbar(),
            ft.Container(height=12),
            self._tabs,
        ]

    def _build_toolbar(self) -> ft.Container:
        return ft.Container(
            content=ft.Row(
                [
                    self._name_field,
                    ft.Container(width=12),
                    accent_button(
                        "Save",
                        icon=ft.Icons.SAVE,
                        on_click=lambda e: asyncio.create_task(self._save_workflow()),
                    ),
                    ghost_button(
                        "Deploy",
                        icon=ft.Icons.ROCKET_LAUNCH,
                        on_click=lambda e: asyncio.create_task(self._deploy_workflow()),
                    ),
                    ghost_button(
                        "Copy JSON",
                        icon=ft.Icons.COPY,
                        on_click=self._copy_json,
                    ),
                    ft.Container(expand=True),
                    self._status_text,
                ],
                spacing=8,
            ),
            padding=16,
            bgcolor=SURFACE,
            border_radius=0,
            border=ft.Border.all(2, BORDER),
        )

    def load_workflow(self, workflow_data: dict[str, Any]) -> None:
        """Load a workflow into the editor (called from outside)."""
        self._workflow_id = workflow_data.get("id")
        self._workflow = workflow_data.get("workflow_json", {})
        self._dirty = False
        self._name_field.value = self._workflow.get("name", "")
        self._selected_node_idx = None
        self._refresh_all()
        self._name_field.update()

    def _refresh_all(self) -> None:
        self._refresh_node_list()
        self._refresh_diagram()
        self._refresh_json()
        status = f"{len(self._workflow.get('nodes', []))} nodes"
        if self._workflow_id:
            status += f" · ID {self._workflow_id[:8]}..."
        if self._dirty:
            status += " · unsaved"
        self._status_text.value = status
        self._status_text.color = WARNING if self._dirty else TEXT_MUTED
        try:
            self._status_text.update()
        except Exception:
            pass

    def _refresh_node_list(self) -> None:
        nodes: list[dict[str, Any]] = self._workflow.get("nodes", []) if self._workflow else []

        add_btn = ft.TextButton(
            content="+ Add Node",
            icon=ft.Icons.ADD,
            on_click=self._show_add_node_dialog,
            style=ft.ButtonStyle(color=ACCENT),
        )

        cards: list[ft.Control] = [add_btn, divider()]
        for idx, node in enumerate(nodes):
            is_selected = idx == self._selected_node_idx
            cards.append(self._make_node_list_item(node, idx, is_selected))

        self._node_list_col.controls = cards
        try:
            self._node_list_col.update()
        except Exception:
            pass

    def _make_node_list_item(
        self, node: dict[str, Any], idx: int, selected: bool
    ) -> ft.Container:
        from src.ui.components import get_node_color, get_node_icon

        node_type = node.get("type", "")
        name = node.get("name", "Unnamed")
        icon = get_node_icon(node_type)
        color = get_node_color(node_type)

        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(icon, size=16, color=color),
                        width=28,
                        height=28,
                        border_radius=0,
                        bgcolor=color + "33",
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Column(
                        [
                            ft.Text(name, size=12, color=TEXT, weight=ft.FontWeight.W_500, no_wrap=True),
                            ft.Text(
                                node_type.replace("n8n-nodes-base.", ""),
                                size=10,
                                color=color,
                                no_wrap=True,
                            ),
                        ],
                        spacing=1,
                        tight=True,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_size=14,
                        icon_color=TEXT_MUTED,
                        on_click=lambda e, i=idx: self._remove_node(i),
                        tooltip="Remove node",
                    ),
                ],
                spacing=8,
                tight=True,
            ),
            padding=8,
            border_radius=0,
            bgcolor=ACCENT + "22" if selected else SURFACE2,
            border=ft.Border.all(2, ACCENT if selected else BORDER),
            on_click=lambda e, i=idx: self._select_node(i),
            ink=True,
        )

    def _select_node(self, idx: int) -> None:
        self._selected_node_idx = idx
        nodes: list[dict[str, Any]] = self._workflow.get("nodes", []) if self._workflow else []
        if idx >= len(nodes):
            return
        node = nodes[idx]
        self._refresh_node_list()
        self._show_node_detail(node, idx)

    def _show_node_detail(self, node: dict[str, Any], idx: int) -> None:
        name_field = ft.TextField(
            label="Node Name",
            value=node.get("name", ""),
            border_color=BORDER,
            focused_border_color=ACCENT,
            bgcolor=SURFACE2,
            color=TEXT,
            text_size=13,
        )
        params_field = ft.TextField(
            label="Parameters (JSON)",
            value=json.dumps(node.get("parameters", {}), indent=2),
            multiline=True,
            min_lines=8,
            max_lines=20,
            border_color=BORDER,
            focused_border_color=ACCENT,
            bgcolor=SURFACE2,
            color=TEXT,
            text_size=12,
            text_style=ft.TextStyle(font_family="monospace"),
        )

        def save_node_changes(e: ft.ControlEvent) -> None:
            nodes = self._workflow.get("nodes", [])
            if idx >= len(nodes):
                return
            new_name = name_field.value or node.get("name", "")
            try:
                new_params = json.loads(params_field.value or "{}")
            except json.JSONDecodeError:
                show_snack(self.page, "Invalid JSON in parameters", error=True)
                return

            old_name = nodes[idx]["name"]
            nodes[idx]["name"] = new_name
            nodes[idx]["parameters"] = new_params

            # Update connections if name changed
            if old_name != new_name:
                connections = self._workflow.get("connections", {})
                if old_name in connections:
                    connections[new_name] = connections.pop(old_name)
                for source_outputs in connections.values():
                    for groups in source_outputs.values():
                        for group in groups:
                            for conn in group:
                                if isinstance(conn, dict) and conn.get("node") == old_name:
                                    conn["node"] = new_name
                self._workflow["connections"] = connections

            self._dirty = True
            self._refresh_all()
            show_snack(self.page, "Node updated")

        pos_text = f"Position: {node.get('position', [0, 0])}"
        type_text = node.get("type", "")

        self._detail_panel.controls = [
            section_title("Edit Node", 14),
            ft.Container(height=8),
            ft.Text(type_text, size=11, color=TEXT_MUTED),
            ft.Text(pos_text, size=11, color=TEXT_MUTED),
            ft.Container(height=12),
            name_field,
            ft.Container(height=8),
            params_field,
            ft.Container(height=12),
            accent_button("Apply Changes", on_click=save_node_changes, icon=ft.Icons.CHECK),
        ]
        try:
            self._detail_panel.update()
        except Exception:
            pass

    def _remove_node(self, idx: int) -> None:
        if not self._workflow:
            return
        nodes: list[dict[str, Any]] = self._workflow.get("nodes", [])
        if idx >= len(nodes):
            return
        node_name = nodes[idx].get("name", "")
        nodes.pop(idx)

        # Remove associated connections
        connections: dict[str, Any] = self._workflow.get("connections", {})
        connections.pop(node_name, None)
        for source in list(connections.keys()):
            for output_type in list(connections[source].keys()):
                new_groups: list[list[Any]] = []
                for group in connections[source][output_type]:
                    new_group = [c for c in group if isinstance(c, dict) and c.get("node") != node_name]
                    new_groups.append(new_group)
                connections[source][output_type] = new_groups

        self._workflow["nodes"] = nodes
        self._workflow["connections"] = connections
        self._selected_node_idx = None
        self._dirty = True
        self._detail_panel.controls = [muted_text("Select a node to edit its parameters")]
        self._refresh_all()
        try:
            self._detail_panel.update()
        except Exception:
            pass

    def _show_add_node_dialog(self, e: ft.ControlEvent) -> None:
        options = [
            ft.dropdown.Option(key, tpl["type"].replace("n8n-nodes-base.", ""))
            for key, tpl in NODE_TEMPLATES.items()
        ]
        type_dropdown = ft.Dropdown(
            label="Node Type",
            options=options,
            value="httpRequest",
            bgcolor=SURFACE2,
            color=TEXT,
            border_color=BORDER,
        )
        name_field = ft.TextField(
            label="Node Name",
            value="New Node",
            bgcolor=SURFACE2,
            color=TEXT,
            border_color=BORDER,
        )

        def do_add(e: ft.ControlEvent) -> None:
            tpl = NODE_TEMPLATES.get(type_dropdown.value or "httpRequest", {})
            import copy

            nodes = self._workflow.get("nodes", [])
            x_pos = 250 + len(nodes) * 200

            new_node: dict[str, Any] = {
                "id": str(uuid.uuid4()),
                "name": name_field.value or "New Node",
                "type": tpl.get("type", "n8n-nodes-base.httpRequest"),
                "typeVersion": tpl.get("typeVersion", 1),
                "position": [x_pos, 300],
                "parameters": copy.deepcopy(tpl.get("parameters", {})),
                "disabled": False,
            }
            nodes.append(new_node)
            self._workflow["nodes"] = nodes
            self._dirty = True
            self._refresh_all()
            self.page.pop_dialog()
            show_snack(self.page, f"Added node '{new_node['name']}'")

        dlg = ft.AlertDialog(
            title=ft.Text("Add Node", color=TEXT),
            bgcolor=SURFACE,
            content=ft.Column(
                [type_dropdown, ft.Container(height=8), name_field],
                tight=True,
            ),
            actions=[
                accent_button("Add", on_click=do_add),
                ghost_button("Cancel", on_click=lambda e: self.page.pop_dialog()),
            ],
        )
        self.page.show_dialog(dlg)

    def _refresh_diagram(self) -> None:
        if self._workflow:
            self._diagram_container.content = connection_diagram(self._workflow)
        else:
            self._diagram_container.content = muted_text("No workflow loaded")
        try:
            self._diagram_container.update()
        except Exception:
            pass

    def _refresh_json(self) -> None:
        if self._workflow:
            json_str = json.dumps(self._workflow, indent=2)
            self._json_container.content = json_text_view(json_str, max_height=500)
            self._json_container.bgcolor = None
        else:
            self._json_container.content = muted_text("No workflow loaded")
        try:
            self._json_container.update()
        except Exception:
            pass

    def _on_name_change(self, e: ft.ControlEvent) -> None:
        if self._workflow:
            self._workflow["name"] = self._name_field.value or ""
            self._dirty = True

    def _copy_json(self, e: ft.ControlEvent) -> None:
        if self._workflow:
            self.page.run_task(
                self.page.clipboard.set, json.dumps(self._workflow, indent=2)
            )
            show_snack(self.page, "JSON copied to clipboard!")

    async def _save_workflow(self) -> None:
        if not self._workflow or not self._workflow_id:
            show_snack(self.page, "No workflow to save", error=True)
            return
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.put(
                    f"{self._api_base}/workflows/{self._workflow_id}",
                    json=self._workflow,
                )
            if response.status_code == 200:
                self._dirty = False
                self._refresh_all()
                show_snack(self.page, "Workflow saved!")
            else:
                detail = response.json().get("detail", response.text)
                show_snack(self.page, f"Save failed: {detail}", error=True)
        except Exception as exc:
            show_snack(self.page, f"Save error: {exc}", error=True)

    async def _deploy_workflow(self) -> None:
        if not self._workflow_id:
            show_snack(self.page, "No workflow loaded or saved", error=True)
            return
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self._api_base}/workflows/{self._workflow_id}/deploy",
                    json={"activate": False},
                )
            data = response.json()
            if data.get("success"):
                show_snack(self.page, f"Deployed! n8n ID: {data.get('n8n_workflow_id', '')}")
            else:
                show_snack(self.page, data.get("message", "Deployment failed"), error=True)
        except Exception as exc:
            show_snack(self.page, f"Deploy error: {exc}", error=True)
