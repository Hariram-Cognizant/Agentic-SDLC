from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(UTC)


class WorkflowStatus(StrEnum):
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


class GateType(StrEnum):
    CLARIFICATION = "clarification"
    BRD = "brd"
    CODE_PLAN = "code_plan"


class ArtifactType(StrEnum):
    REQUIREMENT = "requirement"
    CONTEXT_PACK = "context_pack"
    CLARIFICATIONS = "clarifications"
    BRD = "brd"
    BACKLOG = "backlog"
    SPRINT_PLAN = "sprint_plan"
    CODE_PLAN = "code_plan"
    IMPLEMENTATION = "implementation"
    GIT_HANDOFF = "git_handoff"
    REVIEW = "review"
    SANITY_RESULT = "sanity_result"
    DEFECTS = "defects"
    RELEASE_PACKAGE = "release_package"


@dataclass(slots=True)
class Artifact:
    workflow_id: str
    type: ArtifactType
    name: str
    content: dict[str, Any]
    produced_by: str
    parent_ids: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    version: int = 1
    created_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "type": self.type.value,
            "name": self.name,
            "content": self.content,
            "produced_by": self.produced_by,
            "parent_ids": self.parent_ids,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(slots=True)
class ApprovalGate:
    type: GateType
    title: str
    instructions: str
    required_fields: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "title": self.title,
            "instructions": self.instructions,
            "required_fields": self.required_fields,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(slots=True)
class Workflow:
    title: str
    raw_requirement: str
    source_name: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))
    status: WorkflowStatus = WorkflowStatus.RUNNING
    phase: str = "intake"
    active_gate: ApprovalGate | None = None
    approvals: dict[str, dict[str, Any]] = field(default_factory=dict)
    error: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "raw_requirement": self.raw_requirement,
            "source_name": self.source_name,
            "status": self.status.value,
            "phase": self.phase,
            "active_gate": self.active_gate.to_dict() if self.active_gate else None,
            "approvals": self.approvals,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
