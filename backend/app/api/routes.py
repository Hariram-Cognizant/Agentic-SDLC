from __future__ import annotations

import csv
import io
import json
import zipfile
from typing import Annotated, Any, cast
from xml.etree import ElementTree

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status

from app.api.dependencies import Container
from app.api.schemas import (
    ApprovalRequest,
    ArtifactResponse,
    CreateWorkflowRequest,
    HealthResponse,
    WorkflowResponse,
)
from app.application.exceptions import InvalidApprovalError, WorkflowNotFoundError

router = APIRouter()


def _container(request: Request) -> Container:
    return cast(Container, request.app.state.container)


def _workflow_response(container: Container, workflow_id: str) -> WorkflowResponse:
    workflow = container.orchestrator.get(workflow_id)
    payload = workflow.to_dict()
    payload["artifact_count"] = len(container.repository.list_artifacts(workflow_id))
    return WorkflowResponse.model_validate(payload)


@router.get("/health/live", response_model=HealthResponse, tags=["health"])
def liveness(request: Request) -> HealthResponse:
    container = _container(request)
    return HealthResponse(
        status="ok",
        service="agentic-sdlc",
        generation_provider=container.generation_provider,
    )


@router.get("/health/ready", response_model=HealthResponse, tags=["health"])
def readiness(request: Request) -> HealthResponse:
    container = _container(request)
    try:
        container.repository.list_workflows(limit=1)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Persistence is not ready") from exc
    return HealthResponse(
        status="ready",
        service="agentic-sdlc",
        generation_provider=container.generation_provider,
    )


@router.post(
    "/workflows",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["workflows"],
)
def create_workflow(payload: CreateWorkflowRequest, request: Request) -> WorkflowResponse:
    container = _container(request)
    workflow = container.orchestrator.create(
        payload.title, payload.requirement, payload.source_name
    )
    return _workflow_response(container, workflow.id)


@router.post(
    "/workflows/upload",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["workflows"],
)
async def upload_workflow(
    request: Request,
    title: Annotated[str, Form(min_length=3, max_length=160)],
    file: Annotated[UploadFile, File()],
) -> WorkflowResponse:
    raw = await file.read()
    if len(raw) > 5_000_000:
        raise HTTPException(status_code=413, detail="Requirement file exceeds 5 MB")
    try:
        requirement = _extract_requirement(file.filename or "requirement.txt", raw)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    payload = CreateWorkflowRequest(
        title=title, requirement=requirement, source_name=file.filename
    )
    return create_workflow(payload, request)


@router.get("/workflows", response_model=list[WorkflowResponse], tags=["workflows"])
def list_workflows(request: Request, limit: int = 50) -> list[WorkflowResponse]:
    container = _container(request)
    bounded_limit = min(max(limit, 1), 100)
    return [
        _workflow_response(container, workflow.id)
        for workflow in container.repository.list_workflows(bounded_limit)
    ]


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse, tags=["workflows"])
def get_workflow(workflow_id: str, request: Request) -> WorkflowResponse:
    try:
        return _workflow_response(_container(request), workflow_id)
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/workflows/{workflow_id}/artifacts",
    response_model=list[ArtifactResponse],
    tags=["artifacts"],
)
def list_artifacts(workflow_id: str, request: Request) -> list[ArtifactResponse]:
    container = _container(request)
    try:
        container.orchestrator.get(workflow_id)
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [
        ArtifactResponse.model_validate(item.to_dict())
        for item in container.repository.list_artifacts(workflow_id)
    ]


@router.post(
    "/workflows/{workflow_id}/approvals",
    response_model=WorkflowResponse,
    tags=["workflows"],
)
def approve_workflow(
    workflow_id: str, payload: ApprovalRequest, request: Request
) -> WorkflowResponse:
    container = _container(request)
    try:
        workflow = container.orchestrator.approve(
            workflow_id, payload.gate, payload.model_dump()
        )
        return _workflow_response(container, workflow.id)
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidApprovalError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def _extract_requirement(filename: str, raw: bytes) -> str:
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else "txt"
    if suffix in {"txt", "md"}:
        return raw.decode("utf-8").strip()
    if suffix == "json":
        payload: Any = json.loads(raw.decode("utf-8"))
        return json.dumps(payload, indent=2)
    if suffix == "csv":
        rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
        return "\n".join(" | ".join(cell.strip() for cell in row) for row in rows)
    if suffix == "docx":
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            xml = archive.read("word/document.xml")
        root = ElementTree.fromstring(xml)
        namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        paragraphs = []
        for paragraph in root.iter(f"{namespace}p"):
            text = "".join(node.text or "" for node in paragraph.iter(f"{namespace}t"))
            if text.strip():
                paragraphs.append(text.strip())
        return "\n".join(paragraphs)
    raise ValueError("Supported requirement formats: .txt, .md, .json, .csv, and .docx")
