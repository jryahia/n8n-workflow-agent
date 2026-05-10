"""
Validates n8n workflow JSON before accepting or deploying it.
Checks structure, required fields, node types, and connections.
"""

from typing import Any

from src.node_templates import NODE_TYPE_MAP
from src.schemas import ValidationResult

REQUIRED_WORKFLOW_KEYS: set[str] = {
    "name",
    "nodes",
    "connections",
    "settings",
}

REQUIRED_NODE_KEYS: set[str] = {
    "id",
    "name",
    "type",
    "typeVersion",
    "position",
    "parameters",
}


def validate_workflow(workflow: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    # Top-level keys
    missing_top = REQUIRED_WORKFLOW_KEYS - set(workflow.keys())
    for key in missing_top:
        errors.append(f"Missing required top-level key: '{key}'")

    if errors:
        return ValidationResult(
            valid=False,
            errors=errors,
            warnings=warnings,
            node_count=0,
            connection_count=0,
        )

    nodes: list[dict[str, Any]] = workflow.get("nodes", [])
    connections: dict[str, Any] = workflow.get("connections", {})

    if not isinstance(nodes, list):
        errors.append("'nodes' must be a list")
        return ValidationResult(
            valid=False,
            errors=errors,
            warnings=warnings,
            node_count=0,
            connection_count=0,
        )

    node_names: set[str] = set()

    for idx, node in enumerate(nodes):
        prefix = f"Node[{idx}]"
        if not isinstance(node, dict):
            errors.append(f"{prefix}: must be an object")
            continue

        missing_node = REQUIRED_NODE_KEYS - set(node.keys())
        for key in missing_node:
            errors.append(f"{prefix}: missing required field '{key}'")

        name = node.get("name", f"<unnamed-{idx}>")
        node_names.add(name)

        node_type = node.get("type", "")
        if node_type not in NODE_TYPE_MAP:
            warnings.append(
                f"{prefix} ('{name}'): unknown node type '{node_type}' — may not render correctly in n8n"
            )

        pos = node.get("position")
        if not isinstance(pos, list) or len(pos) != 2:
            errors.append(f"{prefix} ('{name}'): 'position' must be [x, y] list")

        if not isinstance(node.get("parameters"), dict):
            errors.append(f"{prefix} ('{name}'): 'parameters' must be an object")

    has_trigger = _has_trigger_node(nodes)
    if not has_trigger:
        warnings.append(
            "Workflow has no trigger node — it cannot be activated automatically. "
            "Add a scheduleTrigger, webhook, or other trigger."
        )

    connection_count = _count_connections(connections)

    # Validate connection references
    for source_name, outputs in connections.items():
        if source_name not in node_names:
            errors.append(
                f"Connection source '{source_name}' does not match any node name"
            )
            continue
        if not isinstance(outputs, dict):
            errors.append(
                f"Connection for '{source_name}' must be an object with 'main' key"
            )
            continue
        for output_key, groups in outputs.items():
            if not isinstance(groups, list):
                errors.append(
                    f"Connection '{source_name}.{output_key}' must be a list of groups"
                )
                continue
            for group_idx, group in enumerate(groups):
                if not isinstance(group, list):
                    errors.append(
                        f"Connection '{source_name}.{output_key}[{group_idx}]' must be a list"
                    )
                    continue
                for conn in group:
                    if not isinstance(conn, dict):
                        continue
                    target = conn.get("node")
                    if target not in node_names:
                        errors.append(
                            f"Connection target '{target}' from '{source_name}' not found in nodes"
                        )

    if len(nodes) == 1:
        warnings.append("Workflow has only 1 node — it will not do anything useful")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        node_count=len(nodes),
        connection_count=connection_count,
    )


def _has_trigger_node(nodes: list[dict[str, Any]]) -> bool:
    trigger_types = {
        "n8n-nodes-base.start",
        "n8n-nodes-base.webhook",
        "n8n-nodes-base.scheduleTrigger",
        "n8n-nodes-base.chatTrigger",
        "n8n-nodes-base.emailReadImap",
    }
    for node in nodes:
        if isinstance(node, dict) and node.get("type") in trigger_types:
            return True
    return False


def _count_connections(connections: dict[str, Any]) -> int:
    count = 0
    if not isinstance(connections, dict):
        return count
    for outputs in connections.values():
        if not isinstance(outputs, dict):
            continue
        for groups in outputs.values():
            if not isinstance(groups, list):
                continue
            for group in groups:
                if isinstance(group, list):
                    count += len(group)
    return count


def auto_fix_workflow(workflow: dict[str, Any]) -> dict[str, Any]:
    """Apply safe automatic fixes to common structural issues."""
    import uuid

    workflow.setdefault("pinData", {})
    workflow.setdefault("versionId", str(uuid.uuid4()))
    workflow.setdefault("active", False)
    workflow.setdefault("settings", {"executionOrder": "v1"})
    workflow.setdefault("tags", [])
    workflow.setdefault("staticData", None)
    workflow.setdefault("connections", {})

    nodes = workflow.get("nodes", [])
    x_offset = 250
    for idx, node in enumerate(nodes):
        if not isinstance(node, dict):
            continue
        node.setdefault("id", str(uuid.uuid4()))
        node.setdefault("typeVersion", 1)
        node.setdefault("parameters", {})
        node.setdefault("disabled", False)
        if "position" not in node or not isinstance(node["position"], list):
            node["position"] = [x_offset + idx * 200, 300]

    return workflow
