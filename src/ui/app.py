"""
Main Flet application shell.
Navigation rail on the left, view content on the right.
Dark theme throughout.
"""

from typing import Any

import flet as ft

from src.config import settings
from src.ui.components import (
    ACCENT,
    BG,
    BORDER,
    SURFACE,
    SURFACE2,
    TEXT,
    TEXT_MUTED,
)
from src.ui.editor_view import EditorView
from src.ui.instance_view import InstanceView
from src.ui.library_view import LibraryView
from src.ui.prompt_view import PromptView
from src.ui.settings_view import SettingsView


NAV_ITEMS = [
    ("Generate", ft.icons.AUTO_AWESOME, ft.icons.AUTO_AWESOME_OUTLINED),
    ("Editor", ft.icons.EDIT_NOTE, ft.icons.EDIT_NOTE_OUTLINED),
    ("Library", ft.icons.FOLDER_OPEN, ft.icons.FOLDER_OUTLINED),
    ("Instance", ft.icons.CLOUD, ft.icons.CLOUD_OUTLINED),
    ("Settings", ft.icons.SETTINGS, ft.icons.SETTINGS_OUTLINED),
]


async def main(page: ft.Page) -> None:
    api_base = f"http://{settings.api_host}:{settings.api_port}"

    # ── Page Setup ────────────────────────────────────────────────────────────
    page.title = "n8n Workflow Agent"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG
    page.window.width = 1280
    page.window.height = 820
    page.window.min_width = 900
    page.window.min_height = 600
    page.padding = 0
    page.fonts = {"monospace": "Courier New"}

    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ACCENT,
            background=BG,
            surface=SURFACE,
            on_background=TEXT,
            on_surface=TEXT,
        ),
        text_theme=ft.TextTheme(
            body_medium=ft.TextStyle(color=TEXT),
            body_small=ft.TextStyle(color=TEXT_MUTED),
        ),
    )

    # ── Views ──────────────────────────────────────────────────────────────────
    editor_view = EditorView(api_base=api_base)

    def open_in_editor(workflow_data: dict[str, Any]) -> None:
        editor_view.load_workflow(workflow_data)
        nav_rail.selected_index = 1
        _switch_view(1)

    prompt_view = PromptView(
        api_base=api_base,
        on_workflow_select=open_in_editor,
    )
    library_view = LibraryView(
        api_base=api_base,
        on_open_editor=open_in_editor,
    )
    instance_view = InstanceView(api_base=api_base)
    settings_view = SettingsView(api_base=api_base)

    views: list[ft.Control] = [
        prompt_view,
        editor_view,
        library_view,
        instance_view,
        settings_view,
    ]

    content_area = ft.Container(
        content=views[0],
        expand=True,
        padding=ft.Padding.all(20),
    )

    # ── Navigation Rail ────────────────────────────────────────────────────────
    nav_destinations = [
        ft.NavigationRailDestination(
            label=label,
            icon=icon_inactive,
            selected_icon=icon_active,
        )
        for label, icon_active, icon_inactive in NAV_ITEMS
    ]

    def _switch_view(index: int) -> None:
        content_area.content = views[index]
        page.update()

    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=80,
        min_extended_width=160,
        bgcolor=SURFACE,
        indicator_color=ACCENT + "33",
        destinations=nav_destinations,
        on_change=lambda e: _switch_view(e.control.selected_index),
    )

    # ── Header ─────────────────────────────────────────────────────────────────
    header = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text("⚡", size=20),
                            ft.Text(
                                "n8n Workflow Agent",
                                size=16,
                                weight=ft.FontWeight.W_700,
                                color=TEXT,
                            ),
                        ],
                        spacing=6,
                        tight=True,
                    ),
                    padding=ft.Padding.symmetric(horizontal=16),
                ),
                ft.Container(
                    content=ft.Text(
                        f"v{settings.app_version}",
                        size=11,
                        color=TEXT_MUTED,
                    ),
                ),
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text("API:", size=11, color=TEXT_MUTED),
                            ft.Text(api_base, size=11, color=ACCENT, selectable=True),
                        ],
                        spacing=4,
                        tight=True,
                    ),
                    padding=ft.Padding.symmetric(horizontal=16),
                ),
            ],
            spacing=0,
        ),
        height=48,
        bgcolor=SURFACE,
        border=ft.Border.only(bottom=ft.BorderSide(1, BORDER)),
        padding=ft.Padding.symmetric(horizontal=8),
    )

    # ── Layout ────────────────────────────────────────────────────────────────
    main_row = ft.Row(
        [
            ft.Container(
                content=nav_rail,
                bgcolor=SURFACE,
                border=ft.Border.only(right=ft.BorderSide(1, BORDER)),
                width=90,
            ),
            content_area,
        ],
        expand=True,
        spacing=0,
    )

    page.add(
        ft.Column(
            [header, ft.Expanded(child=main_row)],
            expand=True,
            spacing=0,
        )
    )

    # Trigger initial data loading for views that support it
    if hasattr(library_view, "did_mount"):
        library_view.did_mount()
    if hasattr(instance_view, "did_mount"):
        instance_view.did_mount()


def run_flet_app() -> None:
    ft.app(target=main, assets_dir="assets")
