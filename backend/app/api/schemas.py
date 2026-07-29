from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import GateType, WorkflowStatus


class CreateWorkflowRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=3, max_length=160)
    requirement: str = Field(min_length=10, max_length=100_000)
    source_name: str | None = Field(default=None, max_length=255)


class ApprovalRequest(BaseModel):
    gate: GateType
    approved: bool
    answers: dict[str, str] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    success_metrics: list[str] = Field(default_factory=list)
    comment: str | None = Field(default=None, max_length=5_000)


class ApprovalGateResponse(BaseModel):
    type: GateType
    title: str
    instructions: str
    required_fields: list[str]
    created_at: datetime


class WorkflowResponse(BaseModel):
    id: str
    title: str
    status: WorkflowStatus
    phase: str
    source_name: str | None
    active_gate: ApprovalGateResponse | None
    approvals: dict[str, dict[str, Any]]
    error: str | None
    created_at: datetime
    updated_at: datetime
    artifact_count: int


class ArtifactResponse(BaseModel):
    id: str
    workflow_id: str
    type: str
    name: str
    content: dict[str, Any]
    produced_by: str
    parent_ids: list[str]
    version: int
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    service: str
    generation_provider: str
