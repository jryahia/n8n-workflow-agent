"""
FastAPI REST API server.
Provides endpoints for workflow generation, management, and n8n integration.
"""

import time
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_db, init_db
from src.export import (
    WorkflowImportError,
    import_workflow_from_json_string,
    workflow_to_json_string,
)
from src.models import GeneratedWorkflow, PromptLog, WorkflowTemplate
from src.n8n_client import N8nAPIError, N8nClient, refresh_client
from src.schemas import (
    DeployWorkflowRequest,
    DeployWorkflowResponse,
    ErrorResponse,
    GenerateWorkflowRequest,
    GenerateWorkflowResponse,
    ImportWorkflowRequest,
    N8nCredentialItem,
    N8nWorkflowItem,
    SettingsResponse,
    SettingsUpdateRequest,
    TemplateDetail,
    TemplateListItem,
    ValidationResult,
    WorkflowListItem,
)
from src.templates import BUILTIN_TEMPLATES
from src.workflow_generator import generate_workflow
from src.workflow_validator import validate_workflow

app = FastAPI(
    title="n8n Workflow Agent",
    version=settings.app_version,
    description="AI-powered n8n workflow generation and management",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    await init_db()
    await _seed_builtin_templates()


async def _seed_builtin_templates() -> None:
    """Insert built-in templates if they don't exist yet."""
    from src.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        for tpl in BUILTIN_TEMPLATES:
            existing = await session.execute(
                select(WorkflowTemplate).where(
                    WorkflowTemplate.name == tpl["name"],
                    WorkflowTemplate.is_builtin == True,  # noqa: E712
                )
            )
            if existing.scalar_one_or_none() is None:
                session.add(
                    WorkflowTemplate(
                        name=tpl["name"],
                        description=tpl["description"],
                        category=tpl["category"],
                        workflow_json=tpl["workflow"],
                        tags=tpl["tags"],
                        is_builtin=True,
                    )
                )
        await session.commit()


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.app_version}


# ── Workflow Generation ───────────────────────────────────────────────────────

@app.post(
    "/generate",
    response_model=GenerateWorkflowResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def generate_workflow_endpoint(
    request: GenerateWorkflowRequest,
    db: AsyncSession = Depends(get_db),
) -> GenerateWorkflowResponse:
    t_start = time.perf_counter()
    try:
        result = await generate_workflow(
            prompt=request.prompt,
            llm_provider=request.llm_provider,
            llm_model=request.llm_model,
        )
    except ValueError as exc:
        # Log failed attempt
        log = PromptLog(
            prompt=request.prompt,
            llm_provider=request.llm_provider or settings.llm_provider,
            llm_model=request.llm_model or settings.llm_model,
            tokens_used=0,
            success=False,
            error_message=str(exc),
            latency_ms=(time.perf_counter() - t_start) * 1000,
        )
        db.add(log)
        raise HTTPException(status_code=400, detail=str(exc))

    workflow_json: dict[str, Any] = result["workflow_json"]
    name: str = workflow_json.get("name", "Generated Workflow")

    # Persist workflow
    record = GeneratedWorkflow(
        name=name,
        prompt=request.prompt,
        workflow_json=workflow_json,
        llm_provider=result["llm_provider"],
        llm_model=result["llm_model"],
    )
    db.add(record)

    # Log the prompt
    log = PromptLog(
        prompt=request.prompt,
        response_json=workflow_json,
        llm_provider=result["llm_provider"],
        llm_model=result["llm_model"],
        tokens_used=result.get("tokens_used", 0),
        success=True,
        latency_ms=result.get("latency_ms", 0.0),
    )
    db.add(log)
    await db.flush()

    return GenerateWorkflowResponse(
        id=record.id,
        name=name,
        prompt=request.prompt,
        workflow_json=workflow_json,
        llm_provider=result["llm_provider"],
        llm_model=result["llm_model"],
        created_at=record.created_at,
    )


# ── Saved Workflows ───────────────────────────────────────────────────────────

@app.get("/workflows", response_model=list[WorkflowListItem])
async def list_workflows(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    search: str = Query(default=""),
) -> list[WorkflowListItem]:
    query = select(GeneratedWorkflow).order_by(
        GeneratedWorkflow.created_at.desc()
    ).limit(limit).offset(offset)
    result = await db.execute(query)
    rows = result.scalars().all()
    if search:
        search_lower = search.lower()
        rows = [
            r for r in rows
            if search_lower in r.name.lower() or search_lower in r.prompt.lower()
        ]
    return [WorkflowListItem.model_validate(r) for r in rows]


@app.get("/workflows/{workflow_id}", response_model=GenerateWorkflowResponse)
async def get_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
) -> GenerateWorkflowResponse:
    result = await db.execute(
        select(GeneratedWorkflow).where(GeneratedWorkflow.id == workflow_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return GenerateWorkflowResponse.model_validate(record)


@app.delete("/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    result = await db.execute(
        select(GeneratedWorkflow).where(GeneratedWorkflow.id == workflow_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await db.delete(record)
    return {"message": "Workflow deleted"}


@app.put("/workflows/{workflow_id}", response_model=GenerateWorkflowResponse)
async def update_workflow(
    workflow_id: str,
    workflow_json: dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> GenerateWorkflowResponse:
    result = await db.execute(
        select(GeneratedWorkflow).where(GeneratedWorkflow.id == workflow_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Workflow not found")

    validation = validate_workflow(workflow_json)
    if not validation.valid:
        raise HTTPException(
            status_code=400,
            detail="Invalid workflow: " + "; ".join(validation.errors[:3]),
        )

    record.workflow_json = workflow_json
    record.name = workflow_json.get("name", record.name)
    record.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return GenerateWorkflowResponse.model_validate(record)


@app.post("/workflows/{workflow_id}/validate", response_model=ValidationResult)
async def validate_workflow_endpoint(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
) -> ValidationResult:
    result = await db.execute(
        select(GeneratedWorkflow).where(GeneratedWorkflow.id == workflow_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return validate_workflow(record.workflow_json)


# ── Import / Export ───────────────────────────────────────────────────────────

@app.post("/import", response_model=GenerateWorkflowResponse)
async def import_workflow(
    request: ImportWorkflowRequest,
    db: AsyncSession = Depends(get_db),
) -> GenerateWorkflowResponse:
    try:
        raw_json = workflow_to_json_string(request.workflow_json)
        workflow_json = import_workflow_from_json_string(raw_json)
    except WorkflowImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if request.name:
        workflow_json["name"] = request.name

    record = GeneratedWorkflow(
        name=workflow_json.get("name", request.name),
        prompt=request.prompt,
        workflow_json=workflow_json,
        llm_provider="import",
        llm_model="manual",
    )
    db.add(record)
    await db.flush()
    return GenerateWorkflowResponse.model_validate(record)


@app.get("/workflows/{workflow_id}/export")
async def export_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(
        select(GeneratedWorkflow).where(GeneratedWorkflow.id == workflow_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return record.workflow_json


# ── n8n Deployment ────────────────────────────────────────────────────────────

@app.post(
    "/workflows/{workflow_id}/deploy",
    response_model=DeployWorkflowResponse,
)
async def deploy_workflow(
    workflow_id: str,
    request: DeployWorkflowRequest,
    db: AsyncSession = Depends(get_db),
) -> DeployWorkflowResponse:
    result = await db.execute(
        select(GeneratedWorkflow).where(GeneratedWorkflow.id == workflow_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Workflow not found")

    client = N8nClient()
    try:
        deployed = await client.create_workflow(record.workflow_json)
        n8n_id: str = deployed.get("id", "")
        record.n8n_workflow_id = n8n_id
        record.deployed = True

        if request.activate and n8n_id:
            await client.activate_workflow(n8n_id)
            record.active = True

        await db.flush()
        return DeployWorkflowResponse(
            success=True,
            n8n_workflow_id=n8n_id,
            message=f"Workflow deployed to n8n (ID: {n8n_id})",
        )
    except N8nAPIError as exc:
        return DeployWorkflowResponse(
            success=False,
            message=f"Deployment failed: {exc}",
        )


@app.post("/workflows/{workflow_id}/activate")
async def activate_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(
        select(GeneratedWorkflow).where(GeneratedWorkflow.id == workflow_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if not record.n8n_workflow_id:
        raise HTTPException(status_code=400, detail="Workflow not deployed yet")

    client = N8nClient()
    try:
        response = await client.activate_workflow(record.n8n_workflow_id)
        record.active = True
        await db.flush()
        return {"success": True, "data": response}
    except N8nAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.post("/workflows/{workflow_id}/deactivate")
async def deactivate_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(
        select(GeneratedWorkflow).where(GeneratedWorkflow.id == workflow_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if not record.n8n_workflow_id:
        raise HTTPException(status_code=400, detail="Workflow not deployed yet")

    client = N8nClient()
    try:
        response = await client.deactivate_workflow(record.n8n_workflow_id)
        record.active = False
        await db.flush()
        return {"success": True, "data": response}
    except N8nAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


# ── Templates ─────────────────────────────────────────────────────────────────

@app.get("/templates", response_model=list[TemplateListItem])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    category: str = Query(default=""),
) -> list[TemplateListItem]:
    query = select(WorkflowTemplate).order_by(WorkflowTemplate.name)
    result = await db.execute(query)
    rows = result.scalars().all()
    if category:
        rows = [r for r in rows if r.category == category]
    return [TemplateListItem.model_validate(r) for r in rows]


@app.get("/templates/{template_id}", response_model=TemplateDetail)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
) -> TemplateDetail:
    result = await db.execute(
        select(WorkflowTemplate).where(WorkflowTemplate.id == template_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateDetail.model_validate(record)


@app.post("/templates/{template_id}/use", response_model=GenerateWorkflowResponse)
async def use_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
) -> GenerateWorkflowResponse:
    result = await db.execute(
        select(WorkflowTemplate).where(WorkflowTemplate.id == template_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Template not found")

    import copy
    import uuid

    wf = copy.deepcopy(record.workflow_json)
    wf["versionId"] = str(uuid.uuid4())

    generated = GeneratedWorkflow(
        name=wf.get("name", record.name),
        prompt=f"From template: {record.name}",
        workflow_json=wf,
        llm_provider="template",
        llm_model="builtin",
    )
    db.add(generated)
    await db.flush()
    return GenerateWorkflowResponse.model_validate(generated)


# ── n8n Instance ──────────────────────────────────────────────────────────────

@app.get("/n8n/health")
async def n8n_health() -> dict[str, Any]:
    client = N8nClient()
    ok = await client.health_check()
    return {"reachable": ok, "url": settings.n8n_base_url}


@app.get("/n8n/workflows", response_model=list[N8nWorkflowItem])
async def list_n8n_workflows() -> list[N8nWorkflowItem]:
    client = N8nClient()
    try:
        workflows = await client.list_workflows()
        return [
            N8nWorkflowItem(
                id=str(w.get("id", "")),
                name=w.get("name", ""),
                active=w.get("active", False),
                createdAt=w.get("createdAt"),
                updatedAt=w.get("updatedAt"),
            )
            for w in workflows
        ]
    except N8nAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.delete("/n8n/workflows/{n8n_id}")
async def delete_n8n_workflow(
    n8n_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    client = N8nClient()
    try:
        await client.delete_workflow(n8n_id)
    except N8nAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # Update local record if exists
    result = await db.execute(
        select(GeneratedWorkflow).where(GeneratedWorkflow.n8n_workflow_id == n8n_id)
    )
    record = result.scalar_one_or_none()
    if record:
        record.deployed = False
        record.active = False
        record.n8n_workflow_id = None
        await db.flush()

    return {"message": f"Workflow {n8n_id} deleted from n8n"}


@app.get("/n8n/credentials", response_model=list[N8nCredentialItem])
async def list_n8n_credentials() -> list[N8nCredentialItem]:
    client = N8nClient()
    try:
        creds = await client.list_credentials()
        return [
            N8nCredentialItem(
                id=str(c.get("id", "")),
                name=c.get("name", ""),
                type=c.get("type", ""),
            )
            for c in creds
        ]
    except N8nAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


# ── Settings ──────────────────────────────────────────────────────────────────

@app.get("/settings", response_model=SettingsResponse)
async def get_settings() -> SettingsResponse:
    return SettingsResponse(
        n8n_base_url=settings.n8n_base_url,
        n8n_api_key="***" if settings.n8n_api_key else "",
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
        llm_temperature=settings.llm_temperature,
        default_timezone=settings.default_timezone,
    )


@app.put("/settings", response_model=SettingsResponse)
async def update_settings(request: SettingsUpdateRequest) -> SettingsResponse:
    update_data = request.model_dump(exclude_none=True)
    settings.update(**update_data)
    refresh_client()
    return SettingsResponse(
        n8n_base_url=settings.n8n_base_url,
        n8n_api_key="***" if settings.n8n_api_key else "",
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
        llm_temperature=settings.llm_temperature,
        default_timezone=settings.default_timezone,
    )
