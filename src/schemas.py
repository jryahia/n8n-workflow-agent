import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


# ── n8n Core Structures ───────────────────────────────────────────────────────

class N8nNodeConnection(BaseModel):
    node: str
    type: str = "main"
    index: int = 0


class N8nNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str
    typeVersion: int = 1
    position: list[int] = Field(default_factory=lambda: [250, 300])
    parameters: dict[str, Any] = Field(default_factory=dict)
    credentials: dict[str, Any] | None = None
    disabled: bool = False


class N8nWorkflow(BaseModel):
    name: str
    nodes: list[N8nNode]
    connections: dict[str, dict[str, list[list[N8nNodeConnection]]]]
    pinData: dict[str, Any] = Field(default_factory=dict)
    versionId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    active: bool = False
    settings: dict[str, Any] = Field(
        default_factory=lambda: {"executionOrder": "v1"}
    )
    tags: list[Any] = Field(default_factory=list)
    staticData: Any = None

    @model_validator(mode="after")
    def validate_nodes_exist(self) -> "N8nWorkflow":
        node_names = {node.name for node in self.nodes}
        for source_name, outputs in self.connections.items():
            if source_name not in node_names:
                raise ValueError(
                    f"Connection source '{source_name}' not found in nodes"
                )
            for _output_type, output_groups in outputs.items():
                for group in output_groups:
                    for conn in group:
                        if conn.node not in node_names:
                            raise ValueError(
                                f"Connection target '{conn.node}' not found in nodes"
                            )
        return self


# ── Request / Response Schemas ────────────────────────────────────────────────

class GenerateWorkflowRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=2000)
    llm_provider: str | None = None
    llm_model: str | None = None


class GenerateWorkflowResponse(BaseModel):
    id: str
    name: str
    prompt: str
    workflow_json: dict[str, Any]
    llm_provider: str
    llm_model: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkflowListItem(BaseModel):
    id: str
    name: str
    prompt: str
    deployed: bool
    active: bool
    n8n_workflow_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DeployWorkflowRequest(BaseModel):
    activate: bool = False


class DeployWorkflowResponse(BaseModel):
    success: bool
    n8n_workflow_id: str | None = None
    message: str


class ImportWorkflowRequest(BaseModel):
    name: str
    workflow_json: dict[str, Any]
    prompt: str = "Imported workflow"


class SettingsResponse(BaseModel):
    n8n_base_url: str
    n8n_api_key: str
    llm_provider: str
    llm_model: str
    llm_temperature: float
    default_timezone: str


class SettingsUpdateRequest(BaseModel):
    n8n_base_url: str | None = None
    n8n_api_key: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_temperature: float | None = None
    default_timezone: str | None = None


class TemplateListItem(BaseModel):
    id: str
    name: str
    description: str
    category: str
    tags: list[str]
    is_builtin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TemplateDetail(BaseModel):
    id: str
    name: str
    description: str
    category: str
    tags: list[str]
    is_builtin: bool
    workflow_json: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class N8nWorkflowItem(BaseModel):
    id: str
    name: str
    active: bool
    createdAt: str | None = None
    updatedAt: str | None = None


class N8nCredentialItem(BaseModel):
    id: str
    name: str
    type: str


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None


class ValidationResult(BaseModel):
    valid: bool
    errors: list[str]
    warnings: list[str]
    node_count: int
    connection_count: int
