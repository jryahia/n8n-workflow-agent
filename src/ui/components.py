"""
Shared UI components — node cards, connection diagrams, syntax highlighting.
All components use the dark theme palette.
"""

from typing import Any

import flet as ft

# ── Theme Palette ─────────────────────────────────────────────────────────────
BG = "#0f1117"
SURFACE = "#1a1d27"
SURFACE2 = "#21263a"
ACCENT = "#4f8cff"
ACCENT2 = "#7eb3ff"
SUCCESS = "#2ecc71"
WARNING = "#f39c12"
ERROR = "#e74c3c"
TEXT = "#e8eaf0"
TEXT_MUTED = "#6b7280"
BORDER = "#2d3250"

# ── JSON Syntax Colors ────────────────────────────────────────────────────────
JSON_KEY = "#7ec8e3"
JSON_STRING = "#98c379"
JSON_NUMBER = "#e5c07b"
JSON_BOOL = "#c678dd"
JSON_NULL = "#c678dd"

# ── Node Type Icons ───────────────────────────────────────────────────────────
NODE_TYPE_ICONS: dict[str, str] = {
    "n8n-nodes-base.scheduleTrigger": "⏰",
    "n8n-nodes-base.webhook": "🌐",
    "n8n-nodes-base.start": "▶️",
    "n8n-nodes-base.chatTrigger": "💬",
    "n8n-nodes-base.httpRequest": "🌍",
    "n8n-nodes-base.if": "🔀",
    "n8n-nodes-base.switch": "⚡",
    "n8n-nodes-base.code": "💻",
    "n8n-nodes-base.wait": "⏳",
    "n8n-nodes-base.splitInBatches": "📦",
    "n8n-nodes-base.merge": "🔗",
    "n8n-nodes-base.set": "📝",
    "n8n-nodes-base.telegram": "📱",
    "n8n-nodes-base.slack": "💬",
    "n8n-nodes-base.discord": "🎮",
    "n8n-nodes-base.emailSend": "📧",
    "n8n-nodes-base.emailReadImap": "📬",
    "n8n-nodes-base.notion": "📓",
    "n8n-nodes-base.googleSheets": "📊",
    "n8n-nodes-base.openAi": "🤖",
    "n8n-nodes-base.respondToWebhook": "↩️",
}

NODE_TYPE_COLORS: dict[str, str] = {
    "n8n-nodes-base.scheduleTrigger": "#f39c12",
    "n8n-nodes-base.webhook": "#3498db",
    "n8n-nodes-base.start": "#2ecc71",
    "n8n-nodes-base.chatTrigger": "#9b59b6",
    "n8n-nodes-base.httpRequest": "#1abc9c",
    "n8n-nodes-base.if": "#e67e22",
    "n8n-nodes-base.switch": "#e67e22",
    "n8n-nodes-base.code": "#95a5a6",
    "n8n-nodes-base.wait": "#7f8c8d",
    "n8n-nodes-base.set": "#27ae60",
    "n8n-nodes-base.telegram": "#2980b9",
    "n8n-nodes-base.slack": "#8e44ad",
    "n8n-nodes-base.discord": "#7289da",
    "n8n-nodes-base.emailSend": "#e74c3c",
    "n8n-nodes-base.emailReadImap": "#c0392b",
    "n8n-nodes-base.notion": "#ecf0f1",
    "n8n-nodes-base.googleSheets": "#27ae60",
    "n8n-nodes-base.openAi": "#16a085",
    "n8n-nodes-base.respondToWebhook": "#2c3e50",
}


def get_node_icon(node_type: str) -> str:
    return NODE_TYPE_ICONS.get(node_type, "🔲")


def get_node_color(node_type: str) -> str:
    return NODE_TYPE_COLORS.get(node_type, ACCENT)


# ── Reusable Components ───────────────────────────────────────────────────────

def theme_container(
    content: ft.Control,
    padding: int = 16,
    border_radius: int = 8,
    bgcolor: str = SURFACE,
    border_color: str = BORDER,
) -> ft.Container:
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=border_radius,
        bgcolor=bgcolor,
        border=ft.border.all(1, border_color),
    )


def accent_button(
    text: str,
    on_click: Any = None,
    icon: str | None = None,
    width: int | None = None,
) -> ft.ElevatedButton:
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        width=width,
        style=ft.ButtonStyle(
            bgcolor=ACCENT,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=6),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
        ),
    )


def ghost_button(
    text: str,
    on_click: Any = None,
    icon: str | None = None,
    color: str = TEXT_MUTED,
) -> ft.TextButton:
    return ft.TextButton(
        text=text,
        icon=icon,
        on_click=on_click,
        style=ft.ButtonStyle(color=color),
    )


def danger_button(
    text: str,
    on_click: Any = None,
    icon: str | None = None,
) -> ft.OutlinedButton:
    return ft.OutlinedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        style=ft.ButtonStyle(
            color=ERROR,
            side=ft.BorderSide(1, ERROR),
            shape=ft.RoundedRectangleBorder(radius=6),
        ),
    )


def section_title(text: str, size: int = 16) -> ft.Text:
    return ft.Text(text, size=size, weight=ft.FontWeight.W_600, color=TEXT)


def muted_text(text: str, size: int = 13) -> ft.Text:
    return ft.Text(text, size=size, color=TEXT_MUTED)


def tag_chip(label: str, color: str = ACCENT) -> ft.Container:
    return ft.Container(
        content=ft.Text(label, size=11, color=ft.Colors.WHITE),
        padding=ft.padding.symmetric(horizontal=8, vertical=3),
        border_radius=12,
        bgcolor=color + "33",
        border=ft.border.all(1, color + "66"),
    )


def status_badge(label: str, active: bool) -> ft.Container:
    color = SUCCESS if active else TEXT_MUTED
    bg = SUCCESS + "22" if active else SURFACE2
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    width=6,
                    height=6,
                    border_radius=3,
                    bgcolor=color,
                ),
                ft.Text(label, size=11, color=color),
            ],
            spacing=4,
            tight=True,
        ),
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        border_radius=12,
        bgcolor=bg,
    )


def divider() -> ft.Divider:
    return ft.Divider(height=1, color=BORDER)


# ── Node Card ─────────────────────────────────────────────────────────────────

def node_card(
    node: dict[str, Any],
    on_click: Any = None,
    compact: bool = False,
) -> ft.Container:
    node_type = node.get("type", "")
    name = node.get("name", "Unnamed")
    icon = get_node_icon(node_type)
    color = get_node_color(node_type)
    params = node.get("parameters", {})

    type_short = node_type.replace("n8n-nodes-base.", "").replace("n8n-nodes-base", "")
    param_preview = _params_preview(params) if not compact else ""

    content = ft.Column(
        [
            ft.Row(
                [
                    ft.Container(
                        content=ft.Text(icon, size=18),
                        width=32,
                        height=32,
                        border_radius=6,
                        bgcolor=color + "33",
                        alignment=ft.alignment.center,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                name,
                                size=13,
                                weight=ft.FontWeight.W_600,
                                color=TEXT,
                                no_wrap=True,
                            ),
                            ft.Text(
                                type_short,
                                size=11,
                                color=color,
                                no_wrap=True,
                            ),
                        ],
                        spacing=2,
                        tight=True,
                        expand=True,
                    ),
                ],
                spacing=10,
            ),
            *(
                [
                    ft.Container(height=4),
                    ft.Text(
                        param_preview,
                        size=11,
                        color=TEXT_MUTED,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ]
                if param_preview
                else []
            ),
        ],
        spacing=4,
        tight=True,
    )

    return ft.Container(
        content=content,
        padding=10,
        border_radius=8,
        bgcolor=SURFACE2,
        border=ft.border.all(1, color + "44"),
        on_click=on_click,
        ink=True,
    )


def _params_preview(params: dict[str, Any]) -> str:
    parts: list[str] = []
    for key, val in list(params.items())[:3]:
        if isinstance(val, str) and val:
            short = val[:40].replace("\n", " ")
            parts.append(f"{key}: {short}")
        elif isinstance(val, (int, float, bool)):
            parts.append(f"{key}: {val}")
    return "  ·  ".join(parts)


# ── Connection Diagram ────────────────────────────────────────────────────────

def connection_diagram(workflow: dict[str, Any]) -> ft.Control:
    nodes = {n["name"]: n for n in workflow.get("nodes", [])}
    connections = workflow.get("connections", {})

    if not nodes:
        return muted_text("No nodes in workflow")

    # Build ordered chain
    chain = _build_chain(nodes, connections)

    if not chain:
        # Fallback: just list nodes
        items: list[ft.Control] = []
        for node_name in nodes:
            node = nodes[node_name]
            icon = get_node_icon(node.get("type", ""))
            color = get_node_color(node.get("type", ""))
            items.append(
                ft.Container(
                    content=ft.Text(
                        f"{icon}  {node_name}",
                        size=13,
                        color=color,
                    ),
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    border_radius=6,
                    bgcolor=SURFACE2,
                )
            )
        return ft.Column(items, spacing=4)

    row_items: list[ft.Control] = []
    for idx, node_name in enumerate(chain):
        node = nodes.get(node_name, {})
        icon = get_node_icon(node.get("type", ""))
        color = get_node_color(node.get("type", ""))

        row_items.append(
            ft.Container(
                content=ft.Text(
                    f"{icon}  {node_name}",
                    size=12,
                    color=color,
                    weight=ft.FontWeight.W_500,
                ),
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                border_radius=6,
                bgcolor=color + "22",
                border=ft.border.all(1, color + "55"),
            )
        )

        if idx < len(chain) - 1:
            row_items.append(
                ft.Text("  →  ", size=16, color=TEXT_MUTED)
            )

    return ft.Column(
        [
            ft.Row(
                row_items,
                wrap=True,
                spacing=4,
                run_spacing=8,
            )
        ]
    )


def _build_chain(
    nodes: dict[str, Any], connections: dict[str, Any]
) -> list[str]:
    """Topologically sort nodes by connection order."""
    # Find nodes that are never a target (i.e., source/trigger nodes)
    all_targets: set[str] = set()
    for source_outputs in connections.values():
        for groups in source_outputs.values():
            for group in groups:
                for conn in group:
                    if isinstance(conn, dict):
                        all_targets.add(conn.get("node", ""))

    starts = [n for n in nodes if n not in all_targets]

    if not starts:
        return list(nodes.keys())

    # Walk the chain from each start
    visited: set[str] = set()
    chain: list[str] = []

    def walk(name: str) -> None:
        if name in visited:
            return
        visited.add(name)
        chain.append(name)
        node_connections = connections.get(name, {})
        for groups in node_connections.values():
            for group in groups:
                for conn in group:
                    if isinstance(conn, dict):
                        next_node = conn.get("node", "")
                        if next_node:
                            walk(next_node)

    for start in starts:
        walk(start)

    # Add any unvisited nodes at the end
    for name in nodes:
        if name not in visited:
            chain.append(name)

    return chain


# ── JSON Syntax Highlight ─────────────────────────────────────────────────────

def json_text_view(json_str: str, max_height: int = 400) -> ft.Container:
    """Display JSON with basic syntax highlighting as colored spans."""
    import json as json_mod

    lines = json_str.split("\n")
    spans: list[ft.TextSpan] = []

    for line in lines:
        colored = _colorize_json_line(line)
        spans.extend(colored)
        spans.append(ft.TextSpan("\n"))

    return ft.Container(
        content=ft.ListView(
            [
                ft.Text(
                    spans=spans,
                    size=12,
                    font_family="monospace",
                    selectable=True,
                )
            ],
            expand=True,
        ),
        bgcolor="#0d1117",
        border_radius=8,
        padding=12,
        border=ft.border.all(1, BORDER),
        height=max_height,
    )


def _colorize_json_line(line: str) -> list[ft.TextSpan]:
    import re

    spans: list[ft.TextSpan] = []
    pos = 0

    patterns = [
        (r'"[^"\\]*(?:\\.[^"\\]*)*"\s*:', JSON_KEY),   # key
        (r':\s*"[^"\\]*(?:\\.[^"\\]*)*"', JSON_STRING), # string value
        (r':\s*-?\d+(?:\.\d+)?', JSON_NUMBER),           # number value
        (r':\s*(true|false)', JSON_BOOL),                # bool value
        (r':\s*null', JSON_NULL),                        # null value
    ]

    remaining = line
    result_spans: list[ft.TextSpan] = []

    while remaining:
        earliest_match = None
        earliest_start = len(remaining)
        earliest_color = TEXT

        for pattern, color in patterns:
            m = re.search(pattern, remaining)
            if m and m.start() < earliest_start:
                earliest_match = m
                earliest_start = m.start()
                earliest_color = color

        if earliest_match:
            # Text before match
            if earliest_start > 0:
                result_spans.append(
                    ft.TextSpan(remaining[:earliest_start], ft.TextStyle(color=TEXT))
                )
            result_spans.append(
                ft.TextSpan(
                    earliest_match.group(),
                    ft.TextStyle(color=earliest_color),
                )
            )
            remaining = remaining[earliest_start + len(earliest_match.group()):]
        else:
            result_spans.append(ft.TextSpan(remaining, ft.TextStyle(color=TEXT)))
            break

    return result_spans


# ── Loading Overlay ───────────────────────────────────────────────────────────

def loading_spinner(message: str = "Processing...") -> ft.Container:
    return ft.Container(
        content=ft.Column(
            [
                ft.ProgressRing(width=40, height=40, stroke_width=3, color=ACCENT),
                ft.Text(message, color=TEXT_MUTED, size=13),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ),
        alignment=ft.alignment.center,
        expand=True,
    )


# ── Empty State ───────────────────────────────────────────────────────────────

def empty_state(
    icon: str,
    title: str,
    subtitle: str,
    action: ft.Control | None = None,
) -> ft.Container:
    children: list[ft.Control] = [
        ft.Text(icon, size=48),
        ft.Text(title, size=16, weight=ft.FontWeight.W_600, color=TEXT),
        ft.Text(subtitle, size=13, color=TEXT_MUTED, text_align=ft.TextAlign.CENTER),
    ]
    if action:
        children.append(ft.Container(height=4))
        children.append(action)

    return ft.Container(
        content=ft.Column(
            children,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        alignment=ft.alignment.center,
        expand=True,
    )


# ── Snackbar Helper ───────────────────────────────────────────────────────────

def show_snack(page: ft.Page, message: str, error: bool = False) -> None:
    color = ERROR if error else SUCCESS
    page.snack_bar = ft.SnackBar(
        content=ft.Text(message, color=ft.Colors.WHITE),
        bgcolor=color,
        duration=3000,
    )
    page.snack_bar.open = True
    page.update()
