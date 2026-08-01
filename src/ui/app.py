"""
Main Flet application shell — WEB app only (no native desktop window).
Blocky black & white "Minecraft" theme: stone panels, black block-outlines,
pixel font for titles/nav, monospace for body.
"""

import os
from typing import Any

import flet as ft

from src.config import settings
from src.ui.components import (
    ACCENT,
    BG,
    BORDER,
    FONT_MONO,
    FONT_PIXEL,
    PIXEL_FONT_URL,
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

# Fonts are bundled under assets/fonts and served by Flet from ASSETS_DIR, so
# the pixel theme renders offline. If a file is missing we fall back to the
# upstream URL rather than shipping a broken font reference.
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "assets")

MONO_FONT_URL = (
    "https://raw.githubusercontent.com/google/fonts/main/ofl/"
    "spacemono/SpaceMono-Regular.ttf"
)


def _font_source(filename: str, fallback_url: str) -> str:
    """Return the Flet asset path if the font is bundled, else the remote URL."""
    if os.path.exists(os.path.join(ASSETS_DIR, "fonts", filename)):
        return f"/fonts/{filename}"
    return fallback_url

# (label, icon) — icons are ft.Icons enum members (integer code points in 0.85+).
NAV_ITEMS: list[tuple[str, Any]] = [
    ("Generate", ft.Icons.AUTO_AWESOME),
    ("Editor", ft.Icons.EDIT_NOTE),
    ("Library", ft.Icons.FOLDER_OPEN),
    ("Instance", ft.Icons.CLOUD),
    ("Settings", ft.Icons.SETTINGS),
]


async def main(page: ft.Page) -> None:
    api_base = f"http://{settings.api_host}:{settings.api_port}"

    # ── Page Setup ────────────────────────────────────────────────────────────
    page.title = "n8n Workflow Agent"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG
    page.padding = 0
    page.fonts = {
        FONT_PIXEL: _font_source("PressStart2P-Regular.ttf", PIXEL_FONT_URL),
        FONT_MONO: _font_source("SpaceMono-Regular.ttf", MONO_FONT_URL),
    }
    page.theme = ft.Theme(
        font_family=FONT_MONO,
        color_scheme=ft.ColorScheme(
            primary=ACCENT,
            surface=SURFACE,
            on_surface=TEXT,
        ),
        text_theme=ft.TextTheme(
            body_medium=ft.TextStyle(color=TEXT, font_family=FONT_MONO),
            body_small=ft.TextStyle(color=TEXT_MUTED, font_family=FONT_MONO),
        ),
    )

    # ── Views ──────────────────────────────────────────────────────────────────
    editor_view = EditorView(api_base=api_base)

    def open_in_editor(workflow_data: dict[str, Any]) -> None:
        editor_view.load_workflow(workflow_data)
        _select(1)

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

    # ── Navigation (custom blocky sidebar) ──────────────────────────────────────
    selected = {"idx": 0}
    nav_column = ft.Column(spacing=0, tight=True)

    def _nav_button(index: int, label: str, icon: Any) -> ft.Container:
        is_sel = index == selected["idx"]
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, color=TEXT if is_sel else TEXT_MUTED, size=22),
                    ft.Text(
                        label,
                        size=7,
                        color=TEXT if is_sel else TEXT_MUTED,
                        font_family=FONT_PIXEL,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                tight=True,
            ),
            width=92,
            padding=ft.Padding.symmetric(vertical=16),
            bgcolor=SURFACE2 if is_sel else SURFACE,
            border=ft.Border.all(2, BORDER),
            on_click=lambda e, i=index: _select(i),
            ink=True,
        )

    def _build_nav() -> None:
        nav_column.controls = [
            _nav_button(i, label, icon) for i, (label, icon) in enumerate(NAV_ITEMS)
        ]

    def _select(index: int) -> None:
        selected["idx"] = index
        content_area.content = views[index]
        _build_nav()
        page.update()

    _build_nav()

    # ── Header ─────────────────────────────────────────────────────────────────
    header = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text("⬛", size=18),
                            ft.Text(
                                "n8n WORKFLOW AGENT",
                                size=12,
                                color=TEXT,
                                font_family=FONT_PIXEL,
                            ),
                        ],
                        spacing=10,
                        tight=True,
                    ),
                    padding=ft.Padding.symmetric(horizontal=16),
                ),
                ft.Container(
                    content=ft.Text(
                        f"v{settings.app_version}",
                        size=11,
                        color=TEXT_MUTED,
                        font_family=FONT_MONO,
                    ),
                ),
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text("API:", size=11, color=TEXT_MUTED, font_family=FONT_MONO),
                            ft.Text(
                                api_base,
                                size=11,
                                color=ACCENT,
                                selectable=True,
                                font_family=FONT_MONO,
                            ),
                        ],
                        spacing=4,
                        tight=True,
                    ),
                    padding=ft.Padding.symmetric(horizontal=16),
                ),
            ],
            spacing=0,
        ),
        height=52,
        bgcolor=SURFACE,
        border=ft.Border.only(bottom=ft.BorderSide(2, BORDER)),
        padding=ft.Padding.symmetric(horizontal=8),
    )

    # ── Layout ────────────────────────────────────────────────────────────────
    main_row = ft.Row(
        [
            ft.Container(
                content=nav_column,
                bgcolor=SURFACE,
                border=ft.Border.only(right=ft.BorderSide(2, BORDER)),
                width=96,
            ),
            content_area,
        ],
        expand=True,
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    page.add(
        ft.Column(
            [header, ft.Container(content=main_row, expand=True)],
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
    """Run as a web app in the browser (no native desktop window)."""
    # Absolute path: a relative "assets" only resolves when the process happens
    # to be started from the project root.
    os.makedirs(os.path.join(ASSETS_DIR, "fonts"), exist_ok=True)
    ft.run(
        main=main,
        view=ft.AppView.WEB_BROWSER,
        port=8550,
        assets_dir=ASSETS_DIR,
    )
