"""
Import and export n8n workflow JSON files.
Handles file I/O, validation, and format normalization.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.workflow_validator import auto_fix_workflow, validate_workflow


class WorkflowExportError(Exception):
    pass


class WorkflowImportError(Exception):
    pass


def export_workflow_to_file(
    workflow_json: dict[str, Any],
    output_path: str | Path,
    pretty: bool = True,
) -> Path:
    """
    Write workflow JSON to a file.
    Returns the absolute path of the written file.
    """
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    indent = 2 if pretty else None
    try:
        path.write_text(json.dumps(workflow_json, indent=indent, ensure_ascii=False), encoding="utf-8")
    except OSError as exc:
        raise WorkflowExportError(f"Cannot write workflow to '{path}': {exc}") from exc

    return path


def export_workflow_bundle(
    workflows: list[dict[str, Any]],
    output_path: str | Path,
) -> Path:
    """Export multiple workflows as a JSON array bundle."""
    bundle: dict[str, Any] = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "count": len(workflows),
        "workflows": workflows,
    }
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def import_workflow_from_file(
    file_path: str | Path,
) -> list[dict[str, Any]]:
    """
    Load one or more workflows from a JSON file.

    Accepts:
    - A single workflow object  { "name": ..., "nodes": [...], ... }
    - An array of workflow objects
    - A bundle exported by export_workflow_bundle

    Returns a list of workflow dicts (validated and auto-fixed).
    """
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        raise WorkflowImportError(f"File not found: '{path}'")

    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise WorkflowImportError(f"Invalid JSON in '{path}': {exc}") from exc
    except OSError as exc:
        raise WorkflowImportError(f"Cannot read '{path}': {exc}") from exc

    workflows = _normalize_import_data(data, str(path))
    validated: list[dict[str, Any]] = []

    for wf in workflows:
        fixed = auto_fix_workflow(wf)
        result = validate_workflow(fixed)
        if not result.valid:
            raise WorkflowImportError(
                f"Workflow '{fixed.get('name', 'unknown')}' failed validation: "
                + "; ".join(result.errors[:3])
            )
        validated.append(fixed)

    return validated


def import_workflow_from_json_string(raw: str) -> dict[str, Any]:
    """Parse and validate a workflow JSON string directly."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise WorkflowImportError(f"Invalid JSON string: {exc}") from exc

    if isinstance(data, list):
        if not data:
            raise WorkflowImportError("Empty workflow list")
        data = data[0]

    if not isinstance(data, dict):
        raise WorkflowImportError("Workflow must be a JSON object")

    fixed = auto_fix_workflow(data)
    result = validate_workflow(fixed)
    if not result.valid:
        raise WorkflowImportError(
            "Workflow failed validation: " + "; ".join(result.errors[:3])
        )

    return fixed


def workflow_to_json_string(workflow: dict[str, Any], pretty: bool = True) -> str:
    return json.dumps(workflow, indent=2 if pretty else None, ensure_ascii=False)


def _normalize_import_data(
    data: Any, source: str
) -> list[dict[str, Any]]:
    """Normalize various import formats to a list of workflow dicts."""
    if isinstance(data, dict):
        # Bundle format
        if "workflows" in data and isinstance(data["workflows"], list):
            return data["workflows"]
        # Single workflow
        if "nodes" in data or "name" in data:
            return [data]
        raise WorkflowImportError(
            f"Unrecognized JSON structure in '{source}': expected workflow object or bundle"
        )

    if isinstance(data, list):
        if not data:
            raise WorkflowImportError(f"Empty workflow array in '{source}'")
        return data

    raise WorkflowImportError(
        f"Unrecognized JSON structure in '{source}'"
    )


def get_default_export_dir() -> Path:
    """Return the default directory for exported workflows."""
    export_dir = Path.home() / ".n8n-agent" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir


def generate_export_filename(workflow_name: str) -> str:
    """Create a safe filename from a workflow name."""
    safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in workflow_name)
    safe = safe.strip().replace(" ", "_").lower()[:50]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"workflow_{safe}_{timestamp}.json"
