"""
Prompt view — main workflow generation interface.
User types a natural language prompt → agent generates n8n workflow JSON.
"""

import asyncio
import json
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
    connection_diagram,
    divider,
    empty_state,
    ghost_button,
    json_text_view,
    loading_spinner,
    muted_text,
    node_card,
    section_title,
    show_snack,
    status_badge,
    tag_chip,
    theme_container,
)

EXAMPLE_PROMPTS: list[str] = [
    "Send me an email every day at 9am with the latest Bitcoin price",
    "Create a workflow that fetches crypto prices every hour and sends to Telegram",
    "When a webhook is received, call OpenAI API and respond with the AI answer",
    "Every weekday at 8am, fetch sales data from an API and email a report",
    "Monitor a webhook and forward notifications to Discord",
    "Read emails from inbox and save them to Notion database",
]


class PromptView(ft.Column):
    def __init__(self, api_base: str, on_workflow_select: Callable[[dict[str, Any]], None]) -> None:
        super().__init__(expand=True, spacing=0)
        self._api_base = api_base
        self._on_workflow_select = on_workflow_select
        self._generated: dict[str, Any] | None = None
        self._loading = False

        self._prompt_field = ft.TextField(
            hint_text='e.g. "Send me an email every day at 9am with the latest Bitcoin price"',
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_color=BORDER,
            focused_border_color=ACCENT,
            bgcolor=SURFACE2,
            color=TEXT,
            hint_style=ft.TextStyle(color=TEXT_MUTED),
            text_size=14,
            expand=True,
            on_submit=self._on_generate,
        )

        self._provider_dropdown = ft.Dropdown(
            value="openai",
            options=[
                ft.dropdown.Option("openai", "GPT-4o (OpenAI)"),
                ft.dropdown.Option("anthropic", "Claude (Anthropic)"),
            ],
            bgcolor=SURFACE2,
            color=TEXT,
            border_color=BORDER,
            focused_border_color=ACCENT,
            width=200,
        )

        self._generate_btn = accent_button(
            "Generate Workflow",
            on_click=self._on_generate,
            icon=ft.icons.AUTO_AWESOME,
        )

        self._content_area = ft.Column(
            [self._empty_state()],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        self.controls = [
            self._build_input_panel(),
            ft.Container(height=16),
            ft.Expanded(child=self._content_area),
        ]

    def _build_input_panel(self) -> ft.Container:
        examples_row = ft.Row(
            [
                ft.TextButton(
                    text=p[:48] + "..." if len(p) > 48 else p,
                    on_click=lambda e, prompt=p: self._use_example(prompt),
                    style=ft.ButtonStyle(
                        color=TEXT_MUTED,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    ),
                )
                for p in EXAMPLE_PROMPTS
            ],
            wrap=True,
            spacing=6,
            run_spacing=4,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            section_title("Generate Workflow", 18),
                            ft.Container(expand=True),
                            self._provider_dropdown,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=12),
                    ft.Row([self._prompt_field], expand=True),
                    ft.Container(height=10),
                    ft.Row(
                        [
                            self._generate_btn,
                            ghost_button("Clear", on_click=self._on_clear, icon=ft.icons.CLEAR),
                        ],
                        spacing=10,
                    ),
                    ft.Container(height=12),
                    divider(),
                    ft.Container(height=8),
                    muted_text("Example prompts:", 12),
                    ft.Container(height=4),
                    examples_row,
                ],
                spacing=0,
            ),
            padding=20,
            bgcolor=SURFACE,
            border_radius=12,
            border=ft.Border.all(1, BORDER),
        )

    def _empty_state(self) -> ft.Container:
        return empty_state(
            "🤖",
            "Ready to generate",
            "Type a natural language description above\nand click Generate Workflow",
        )

    def _use_example(self, prompt: str) -> None:
        self._prompt_field.value = prompt
        self._prompt_field.update()

    async def _on_generate(self, e: ft.ControlEvent) -> None:
        prompt = (self._prompt_field.value or "").strip()
        if not prompt:
            show_snack(self.page, "Please enter a prompt", error=True)
            return

        if self._loading:
            return

        self._loading = True
        self._generate_btn.disabled = True
        self._generate_btn.text = "Generating..."
        self._generate_btn.update()

        self._content_area.controls = [loading_spinner("Generating workflow with AI...")]
        self._content_area.update()

        try:
            payload = {
                "prompt": prompt,
                "llm_provider": self._provider_dropdown.value,
            }
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self._api_base}/generate",
                    json=payload,
                )

            if response.status_code == 200:
                data = response.json()
                self._generated = data
                self._content_area.controls = [self._build_result_panel(data)]
                show_snack(self.page, f"Workflow '{data['name']}' generated successfully!")
            else:
                detail = response.json().get("detail", response.text)
                self._content_area.controls = [self._build_error_panel(detail)]
                show_snack(self.page, f"Generation failed: {detail}", error=True)

        except Exception as exc:
            self._content_area.controls = [self._build_error_panel(str(exc))]
            show_snack(self.page, f"Error: {exc}", error=True)
        finally:
            self._loading = False
            self._generate_btn.disabled = False
            self._generate_btn.text = "Generate Workflow"
            self._generate_btn.update()
            self._content_area.update()

    def _on_clear(self, e: ft.ControlEvent) -> None:
        self._prompt_field.value = ""
        self._generated = None
        self._content_area.controls = [self._empty_state()]
        self._prompt_field.update()
        self._content_area.update()

    def _build_result_panel(self, data: dict[str, Any]) -> ft.Column:
        workflow_json: dict[str, Any] = data.get("workflow_json", {})
        nodes: list[dict[str, Any]] = workflow_json.get("nodes", [])
        json_str = json.dumps(workflow_json, indent=2)

        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=200,
            tabs=[
                ft.Tab(
                    text="Overview",
                    icon=ft.icons.ACCOUNT_TREE,
                    content=ft.Container(
                        content=self._build_overview_tab(workflow_json, nodes),
                        padding=ft.Padding.only(top=16),
                    ),
                ),
                ft.Tab(
                    text="Nodes",
                    icon=ft.icons.LAYERS,
                    content=ft.Container(
                        content=self._build_nodes_tab(nodes),
                        padding=ft.Padding.only(top=16),
                    ),
                ),
                ft.Tab(
                    text="JSON",
                    icon=ft.icons.CODE,
                    content=ft.Container(
                        content=json_text_view(json_str, max_height=500),
                        padding=ft.Padding.only(top=16),
                    ),
                ),
            ],
            expand=True,
        )

        action_row = ft.Row(
            [
                accent_button(
                    "Deploy to n8n",
                    icon=ft.icons.ROCKET_LAUNCH,
                    on_click=lambda e: asyncio.create_task(
                        self._deploy_workflow(data["id"])
                    ),
                ),
                ghost_button(
                    "Open in Editor",
                    icon=ft.icons.EDIT,
                    on_click=lambda e: self._on_workflow_select(data),
                ),
                ghost_button(
                    "Copy JSON",
                    icon=ft.icons.COPY,
                    on_click=lambda e: self._copy_json(json_str),
                ),
            ],
            spacing=8,
        )

        meta_row = ft.Row(
            [
                muted_text(f"Model: {data.get('llm_model', '')}"),
                muted_text("·"),
                muted_text(f"{len(nodes)} nodes"),
                muted_text("·"),
                muted_text(
                    f"ID: {data.get('id', '')[:8]}..."
                ),
            ],
            spacing=6,
        )

        return ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    section_title(workflow_json.get("name", "Workflow"), 16),
                                    ft.Container(expand=True),
                                    status_badge("Generated", True),
                                ]
                            ),
                            meta_row,
                            ft.Container(height=8),
                            action_row,
                            ft.Container(height=12),
                            divider(),
                            ft.Container(height=12),
                            tabs,
                        ],
                        spacing=4,
                    ),
                    padding=20,
                    bgcolor=SURFACE,
                    border_radius=12,
                    border=ft.Border.all(1, BORDER),
                    expand=True,
                )
            ],
            expand=True,
        )

    def _build_overview_tab(
        self, workflow: dict[str, Any], nodes: list[dict[str, Any]]
    ) -> ft.Column:
        return ft.Column(
            [
                section_title("Connection Flow", 13),
                ft.Container(height=8),
                ft.Container(
                    content=connection_diagram(workflow),
                    padding=12,
                    bgcolor=SURFACE2,
                    border_radius=8,
                    border=ft.Border.all(1, BORDER),
                ),
                ft.Container(height=16),
                section_title("Workflow Info", 13),
                ft.Container(height=8),
                ft.Container(
                    content=ft.Column(
                        [
                            _info_row("Name", workflow.get("name", "")),
                            _info_row("Nodes", str(len(nodes))),
                            _info_row(
                                "Active",
                                "Yes" if workflow.get("active") else "No",
                            ),
                            _info_row(
                                "Execution Order",
                                workflow.get("settings", {}).get("executionOrder", "v1"),
                            ),
                        ],
                        spacing=4,
                    ),
                    padding=12,
                    bgcolor=SURFACE2,
                    border_radius=8,
                    border=ft.Border.all(1, BORDER),
                ),
            ],
            spacing=0,
        )

    def _build_nodes_tab(self, nodes: list[dict[str, Any]]) -> ft.Column:
        if not nodes:
            return ft.Column([muted_text("No nodes in workflow")])

        cards = [node_card(node) for node in nodes]
        return ft.Column(cards, spacing=8)

    def _build_error_panel(self, detail: str) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("⚠️", size=40),
                    ft.Text(
                        "Generation Failed",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=ERROR,
                    ),
                    ft.Container(
                        content=ft.Text(
                            detail,
                            size=12,
                            color=TEXT_MUTED,
                            selectable=True,
                        ),
                        padding=12,
                        bgcolor=SURFACE2,
                        border_radius=8,
                        border=ft.Border.all(1, ERROR + "44"),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            padding=24,
            bgcolor=SURFACE,
            border_radius=12,
            border=ft.Border.all(1, BORDER),
            alignment=ft.alignment.center,
        )

    async def _deploy_workflow(self, workflow_id: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self._api_base}/workflows/{workflow_id}/deploy",
                    json={"activate": False},
                )
            data = response.json()
            if data.get("success"):
                show_snack(self.page, f"Deployed! n8n ID: {data.get('n8n_workflow_id', '')}")
            else:
                show_snack(self.page, data.get("message", "Deployment failed"), error=True)
        except Exception as exc:
            show_snack(self.page, f"Deploy error: {exc}", error=True)

    def _copy_json(self, json_str: str) -> None:
        self.page.set_clipboard(json_str)
        show_snack(self.page, "JSON copied to clipboard!")


def _info_row(label: str, value: str) -> ft.Row:
    return ft.Row(
        [
            ft.Text(label, size=12, color=TEXT_MUTED, width=130),
            ft.Text(value, size=12, color=TEXT),
        ],
        spacing=8,
    )
