"""Tests for workflow validation."""

import uuid

import pytest

from src.workflow_validator import auto_fix_workflow, validate_workflow


def _valid_workflow() -> dict:
    trigger_id = str(uuid.uuid4())
    http_id = str(uuid.uuid4())
    return {
        "name": "Test Workflow",
        "nodes": [
            {
                "id": trigger_id,
                "name": "Schedule Trigger",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1,
                "position": [250, 300],
                "parameters": {
                    "rule": {"interval": [{"field": "hours", "hoursInterval": 1}]}
                },
                "disabled": False,
            },
            {
                "id": http_id,
                "name": "HTTP Request",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4,
                "position": [450, 300],
                "parameters": {
                    "method": "GET",
                    "url": "https://api.example.com/data",
                    "options": {},
                },
                "disabled": False,
            },
        ],
        "connections": {
            "Schedule Trigger": {
                "main": [[{"node": "HTTP Request", "type": "main", "index": 0}]]
            }
        },
        "pinData": {},
        "versionId": str(uuid.uuid4()),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "tags": [],
        "staticData": None,
    }


def test_valid_workflow_passes():
    result = validate_workflow(_valid_workflow())
    assert result.valid is True
    assert len(result.errors) == 0
    assert result.node_count == 2
    assert result.connection_count == 1


def test_missing_name_field():
    wf = _valid_workflow()
    del wf["name"]
    result = validate_workflow(wf)
    assert result.valid is False
    assert any("name" in e for e in result.errors)


def test_missing_nodes_field():
    wf = _valid_workflow()
    del wf["nodes"]
    result = validate_workflow(wf)
    assert result.valid is False
    assert any("nodes" in e for e in result.errors)


def test_invalid_connection_source():
    wf = _valid_workflow()
    wf["connections"]["NonExistentNode"] = {
        "main": [[{"node": "HTTP Request", "type": "main", "index": 0}]]
    }
    result = validate_workflow(wf)
    assert result.valid is False
    assert any("NonExistentNode" in e for e in result.errors)


def test_invalid_connection_target():
    wf = _valid_workflow()
    wf["connections"]["Schedule Trigger"]["main"] = [
        [{"node": "DoesNotExist", "type": "main", "index": 0}]
    ]
    result = validate_workflow(wf)
    assert result.valid is False
    assert any("DoesNotExist" in e for e in result.errors)


def test_no_trigger_produces_warning():
    wf = {
        "name": "No Trigger",
        "nodes": [
            {
                "id": str(uuid.uuid4()),
                "name": "HTTP Request",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4,
                "position": [250, 300],
                "parameters": {"method": "GET", "url": "https://example.com"},
                "disabled": False,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Set Node",
                "type": "n8n-nodes-base.set",
                "typeVersion": 3,
                "position": [450, 300],
                "parameters": {},
                "disabled": False,
            },
        ],
        "connections": {
            "HTTP Request": {
                "main": [[{"node": "Set Node", "type": "main", "index": 0}]]
            }
        },
        "pinData": {},
        "versionId": str(uuid.uuid4()),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "tags": [],
        "staticData": None,
    }
    result = validate_workflow(wf)
    assert result.valid is True
    assert any("trigger" in w.lower() for w in result.warnings)


def test_node_missing_required_field():
    wf = _valid_workflow()
    del wf["nodes"][0]["id"]
    result = validate_workflow(wf)
    assert result.valid is False
    assert any("id" in e for e in result.errors)


def test_node_invalid_position():
    wf = _valid_workflow()
    wf["nodes"][0]["position"] = "invalid"
    result = validate_workflow(wf)
    assert result.valid is False
    assert any("position" in e for e in result.errors)


def test_auto_fix_adds_missing_defaults():
    wf = {
        "name": "Minimal",
        "nodes": [
            {
                "name": "Start",
                "type": "n8n-nodes-base.start",
                "typeVersion": 1,
                "position": [250, 300],
                "parameters": {},
            }
        ],
        "connections": {},
        "settings": {"executionOrder": "v1"},
    }
    fixed = auto_fix_workflow(wf)
    assert "pinData" in fixed
    assert "versionId" in fixed
    assert "active" in fixed
    assert "tags" in fixed
    assert "staticData" in fixed
    assert fixed["nodes"][0].get("id") is not None
    assert fixed["nodes"][0].get("disabled") is not None


def test_auto_fix_assigns_positions():
    wf = {
        "name": "No Positions",
        "nodes": [
            {
                "name": "Node A",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 1,
                "parameters": {},
            },
            {
                "name": "Node B",
                "type": "n8n-nodes-base.set",
                "typeVersion": 3,
                "parameters": {},
            },
        ],
        "connections": {},
        "settings": {"executionOrder": "v1"},
    }
    fixed = auto_fix_workflow(wf)
    assert isinstance(fixed["nodes"][0]["position"], list)
    assert len(fixed["nodes"][0]["position"]) == 2
    # Second node should be further right
    assert fixed["nodes"][1]["position"][0] > fixed["nodes"][0]["position"][0]


def test_empty_connections_is_valid():
    wf = {
        "name": "Single Node",
        "nodes": [
            {
                "id": str(uuid.uuid4()),
                "name": "Trigger",
                "type": "n8n-nodes-base.start",
                "typeVersion": 1,
                "position": [250, 300],
                "parameters": {},
                "disabled": False,
            }
        ],
        "connections": {},
        "pinData": {},
        "versionId": str(uuid.uuid4()),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "tags": [],
        "staticData": None,
    }
    result = validate_workflow(wf)
    assert result.valid is True
