"""
Settings view — configure n8n URL, API key, LLM provider, and preferences.
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
    accent_button,
    divider,
    ghost_button,
    muted_text,
    section_title,
    show_snack,
    theme_container,
)
from src.config import LLM_PROVIDERS, settings


class SettingsView(ft.Column):
    def __init__(self, api_base: str) -> None:
        super().__init__(expand=True, spacing=12, scroll=ft.ScrollMode.AUTO)
        self._api_base = api_base

        self._n8n_url = ft.TextField(
            label="n8n Instance URL",
            value=settings.n8n_base_url,
            hint_text="http://localhost:5678",
            border_color=BORDER,
            focused_border_color=ACCENT,
            bgcolor=SURFACE2,
            color=TEXT,
            text_size=13,
            expand=True,
        )
        self._n8n_api_key = ft.TextField(
            label="n8n API Key",
            value=settings.n8n_api_key,
            hint_text="Leave blank if n8n has no API key",
            password=True,
            can_reveal_password=True,
            border_color=BORDER,
            focused_border_color=ACCENT,
            bgcolor=SURFACE2,
            color=TEXT,
            text_size=13,
            expand=True,
        )
        self._llm_provider = ft.Dropdown(
            label="LLM Provider",
            value=settings.llm_provider,
            options=[
                ft.dropdown.Option(key, meta["label"])
                for key, meta in LLM_PROVIDERS.items()
            ],
            bgcolor=SURFACE2,
            color=TEXT,
            border_color=BORDER,
            focused_border_color=ACCENT,
            on_select=self._on_provider_change,
        )
        self._llm_model = ft.TextField(
            label="LLM Model",
            value=settings.llm_model,
            hint_text="gpt-4o or claude-3-5-sonnet-20241022",
            border_color=BORDER,
            focused_border_color=ACCENT,
            bgcolor=SURFACE2,
            color=TEXT,
            text_size=13,
        )
        self._openai_key = ft.TextField(
            label="OpenAI API Key",
            value=settings.openai_api_key,
            hint_text="sk-...",
            password=True,
            can_reveal_password=True,
            border_color=BORDER,
            focused_border_color=ACCENT,
            bgcolor=SURFACE2,
            color=TEXT,
            text_size=13,
            expand=True,
        )
        self._anthropic_key = ft.TextField(
            label="Anthropic API Key",
            value=settings.anthropic_api_key,
            hint_text="sk-ant-...",
            password=True,
            can_reveal_password=True,
            border_color=BORDER,
            focused_border_color=ACCENT,
            bgcolor=SURFACE2,
            color=TEXT,
            text_size=13,
            expand=True,
        )
        # API-key fields for the OpenAI-compatible providers, built from the
        # registry so adding a provider in config.py surfaces it here too.
        self._provider_key_fields: dict[str, ft.TextField] = {}
        for key, meta in LLM_PROVIDERS.items():
            if key in ("openai", "anthropic"):
                continue  # dedicated fields above
            self._provider_key_fields[meta["key_attr"]] = ft.TextField(
                label=f"{meta['label']} API Key",
                value=getattr(settings, meta["key_attr"], ""),
                hint_text="sk-...",
                password=True,
                can_reveal_password=True,
                border_color=BORDER,
                focused_border_color=ACCENT,
                bgcolor=SURFACE2,
                color=TEXT,
                text_size=13,
                expand=True,
            )
        self._temperature = ft.Slider(
            min=0.0,
            max=1.0,
            value=settings.llm_temperature,
            divisions=20,
            label="{value}",
            active_color=ACCENT,
            expand=True,
        )
        self._timezone = ft.Dropdown(
            label="Default Timezone",
            value=settings.default_timezone,
            options=[
                ft.dropdown.Option("UTC", "UTC"),
                ft.dropdown.Option("America/New_York", "US/Eastern"),
                ft.dropdown.Option("America/Chicago", "US/Central"),
                ft.dropdown.Option("America/Los_Angeles", "US/Pacific"),
                ft.dropdown.Option("Europe/London", "Europe/London"),
                ft.dropdown.Option("Europe/Paris", "Europe/Paris"),
                ft.dropdown.Option("Europe/Berlin", "Europe/Berlin"),
                ft.dropdown.Option("Asia/Tokyo", "Asia/Tokyo"),
                ft.dropdown.Option("Asia/Shanghai", "Asia/Shanghai"),
                ft.dropdown.Option("Asia/Dubai", "Asia/Dubai"),
                ft.dropdown.Option("Australia/Sydney", "Australia/Sydney"),
            ],
            bgcolor=SURFACE2,
            color=TEXT,
            border_color=BORDER,
            focused_border_color=ACCENT,
        )
        self._n8n_status = muted_text("")

        self._build_controls()

    def _build_controls(self) -> None:
        self.controls = [
            # n8n Connection
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                section_title("n8n Connection", 15),
                                ft.Container(expand=True),
                                ghost_button(
                                    "Test Connection",
                                    icon=ft.Icons.WIFI,
                                    on_click=lambda e: asyncio.create_task(
                                        self._test_n8n_connection()
                                    ),
                                ),
                            ]
                        ),
                        self._n8n_status,
                        ft.Container(height=8),
                        self._n8n_url,
                        ft.Container(height=8),
                        self._n8n_api_key,
                    ],
                    spacing=4,
                ),
                padding=20,
                bgcolor=SURFACE,
                border_radius=0,
                border=ft.Border.all(2, BORDER),
            ),
            # LLM Configuration
            ft.Container(
                content=ft.Column(
                    [
                        section_title("LLM Configuration", 15),
                        ft.Container(height=8),
                        ft.Row(
                            [self._llm_provider, ft.Container(width=12), self._llm_model],
                            spacing=0,
                        ),
                        ft.Container(height=8),
                        ft.Row(
                            [
                                ft.Text("Temperature:", size=13, color=TEXT_MUTED, width=100),
                                self._temperature,
                            ],
                            spacing=8,
                        ),
                        muted_text("Lower temperature = more deterministic workflow JSON"),
                    ],
                    spacing=4,
                ),
                padding=20,
                bgcolor=SURFACE,
                border_radius=0,
                border=ft.Border.all(2, BORDER),
            ),
            # API Keys
            ft.Container(
                content=ft.Column(
                    [
                        section_title("API Keys", 15),
                        ft.Container(height=8),
                        self._openai_key,
                        ft.Container(height=8),
                        self._anthropic_key,
                        *[
                            ctrl
                            for field in self._provider_key_fields.values()
                            for ctrl in (ft.Container(height=8), field)
                        ],
                    ],
                    spacing=4,
                ),
                padding=20,
                bgcolor=SURFACE,
                border_radius=0,
                border=ft.Border.all(2, BORDER),
            ),
            # Preferences
            ft.Container(
                content=ft.Column(
                    [
                        section_title("Preferences", 15),
                        ft.Container(height=8),
                        self._timezone,
                    ],
                    spacing=4,
                ),
                padding=20,
                bgcolor=SURFACE,
                border_radius=0,
                border=ft.Border.all(2, BORDER),
            ),
            # Save Button
            ft.Container(
                content=ft.Row(
                    [
                        accent_button(
                            "Save Settings",
                            icon=ft.Icons.SAVE,
                            on_click=lambda e: asyncio.create_task(self._save_settings()),
                            width=180,
                        ),
                        ghost_button(
                            "Reset to Defaults",
                            on_click=self._reset_defaults,
                            icon=ft.Icons.RESTORE,
                        ),
                    ],
                    spacing=12,
                ),
                padding=ft.Padding.symmetric(vertical=8),
            ),
            # About
            ft.Container(
                content=ft.Column(
                    [
                        section_title("About", 15),
                        ft.Container(height=4),
                        _info_row("Version", settings.app_version),
                        _info_row("API Server", f"http://{settings.api_host}:{settings.api_port}"),
                        _info_row(
                            "Database",
                            settings.database_url.split("///")[-1] if "///" in settings.database_url else settings.database_url,
                        ),
                        ft.Container(height=8),
                        ft.TextButton(
                            content="GitHub: n8n Workflow Agent",
                            url="https://github.com",
                            style=ft.ButtonStyle(color=ACCENT),
                        ),
                    ],
                    spacing=4,
                ),
                padding=20,
                bgcolor=SURFACE,
                border_radius=0,
                border=ft.Border.all(2, BORDER),
            ),
        ]

    def _on_provider_change(self, e: ft.ControlEvent) -> None:
        provider = self._llm_provider.value or "openai"
        meta = LLM_PROVIDERS.get(provider)
        if meta:
            self._llm_model.value = meta["default_model"]
        self._llm_model.update()

    async def _test_n8n_connection(self) -> None:
        self._n8n_status.value = "Testing connection..."
        self._n8n_status.color = TEXT_MUTED
        try:
            self._n8n_status.update()
        except Exception:
            pass

        url = (self._n8n_url.value or "").rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{url}/healthz")
            if response.status_code == 200:
                self._n8n_status.value = "n8n is reachable"
                self._n8n_status.color = SUCCESS
                show_snack(self.page, "n8n connection successful!")
            else:
                self._n8n_status.value = f"n8n returned {response.status_code}"
                self._n8n_status.color = ERROR
        except Exception as exc:
            self._n8n_status.value = f"Cannot reach n8n: {exc}"
            self._n8n_status.color = ERROR

        try:
            self._n8n_status.update()
        except Exception:
            pass

    async def _save_settings(self) -> None:
        update_data: dict[str, Any] = {
            "n8n_base_url": (self._n8n_url.value or "").rstrip("/"),
            "n8n_api_key": self._n8n_api_key.value or "",
            "llm_provider": self._llm_provider.value or "openai",
            "llm_model": self._llm_model.value or "gpt-4o",
            "llm_temperature": self._temperature.value,
            "default_timezone": self._timezone.value or "UTC",
        }

        # Provider keys go in the same payload so the server writes them to
        # .env too — only non-empty ones, so a blank field never wipes a key.
        if self._openai_key.value:
            update_data["openai_api_key"] = self._openai_key.value
        if self._anthropic_key.value:
            update_data["anthropic_api_key"] = self._anthropic_key.value
        for key_attr, field in self._provider_key_fields.items():
            if field.value:
                update_data[key_attr] = field.value

        # Apply in-process immediately so the UI is consistent even if the API
        # call fails; the API call is what persists them to .env.
        settings.update(**update_data)

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.put(
                    f"{self._api_base}/settings", json=update_data
                )
            if response.status_code == 200:
                show_snack(self.page, "Settings saved to .env!")
            else:
                detail = response.json().get("detail", response.text)
                show_snack(
                    self.page,
                    f"Applied for this session, but not saved: {detail}",
                    error=True,
                )
        except Exception as exc:
            show_snack(
                self.page,
                f"Applied for this session, but not saved: {exc}",
                error=True,
            )

    def _reset_defaults(self, e: ft.ControlEvent) -> None:
        self._n8n_url.value = "http://localhost:5678"
        self._n8n_api_key.value = ""
        self._llm_provider.value = "openai"
        self._llm_model.value = "gpt-4o"
        self._temperature.value = 0.1
        self._timezone.value = "UTC"
        self._n8n_url.update()
        self._n8n_api_key.update()
        self._llm_provider.update()
        self._llm_model.update()
        self._temperature.update()
        self._timezone.update()
        show_snack(self.page, "Reset to defaults (not saved)")


def _info_row(label: str, value: str) -> ft.Row:
    return ft.Row(
        [
            ft.Text(label + ":", size=12, color=TEXT_MUTED, width=90),
            ft.Text(value, size=12, color=TEXT, selectable=True),
        ],
        spacing=8,
    )
