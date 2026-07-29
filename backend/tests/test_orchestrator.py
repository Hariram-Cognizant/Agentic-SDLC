from pathlib import Path

import pytest

from app.application.exceptions import InvalidApprovalError
from app.application.orchestrator import WorkflowOrchestrator
from app.domain.models import ArtifactType, GateType, WorkflowStatus
from app.infrastructure.generation import TemplateGenerator
from app.infrastructure.source_control import HandoffSourceControl
from app.infrastructure.sqlite_repository import SQLiteWorkflowRepository


@pytest.fixture
def system(tmp_path: Path) -> tuple[WorkflowOrchestrator, SQLiteWorkflowRepository]:
    repository = SQLiteWorkflowRepository(f"sqlite:///{tmp_path / 'test.db'}")
    repository.initialize()
    orchestrator = WorkflowOrchestrator(
        repository, TemplateGenerator(), HandoffSourceControl()
    )
    return orchestrator, repository


def test_workflow_runs_end_to_end_through_three_gates(
    system: tuple[WorkflowOrchestrator, SQLiteWorkflowRepository],
) -> None:
    orchestrator, repository = system
    workflow = orchestrator.create(
        "Passwordless sign in",
        "Customers can sign in with an emailed one-time link. Links expire in ten minutes.",
    )
    assert workflow.status == WorkflowStatus.AWAITING_APPROVAL
    assert workflow.active_gate and workflow.active_gate.type == GateType.CLARIFICATION

    workflow = orchestrator.approve(
        workflow.id,
        GateType.CLARIFICATION,
        {"approved": True, "answers": {"roles": "customer"}},
    )
    assert workflow.active_gate and workflow.active_gate.type == GateType.BRD

    workflow = orchestrator.approve(workflow.id, GateType.BRD, {"approved": True})
    assert workflow.active_gate and workflow.active_gate.type == GateType.CODE_PLAN

    workflow = orchestrator.approve(workflow.id, GateType.CODE_PLAN, {"approved": True})
    assert workflow.status == WorkflowStatus.COMPLETED
    assert workflow.phase == "complete"

    artifacts = repository.list_artifacts(workflow.id)
    artifact_types = {artifact.type for artifact in artifacts}
    assert len(artifacts) == 13
    assert ArtifactType.RELEASE_PACKAGE in artifact_types
    assert ArtifactType.DEFECTS in artifact_types
    release = repository.get_artifact(workflow.id, ArtifactType.RELEASE_PACKAGE.value)
    assert release is not None
    assert release.content["readiness"] == "ready_for_qa"
    assert len(release.content["lineage"]) == 12


def test_wrong_gate_is_rejected_without_advancing(
    system: tuple[WorkflowOrchestrator, SQLiteWorkflowRepository],
) -> None:
    orchestrator, _ = system
    workflow = orchestrator.create(
        "Audit export",
        "Administrators can export a date-bounded audit report as a CSV document.",
    )
    with pytest.raises(InvalidApprovalError):
        orchestrator.approve(workflow.id, GateType.CODE_PLAN, {"approved": True})
    persisted = orchestrator.get(workflow.id)
    assert persisted.active_gate
    assert persisted.active_gate.type == GateType.CLARIFICATION


def test_approval_must_be_explicit(
    system: tuple[WorkflowOrchestrator, SQLiteWorkflowRepository],
) -> None:
    orchestrator, _ = system
    workflow = orchestrator.create(
        "Profile notice",
        "Customers receive a notice when their profile information changes.",
    )
    with pytest.raises(InvalidApprovalError, match="approved=true"):
        orchestrator.approve(
            workflow.id, GateType.CLARIFICATION, {"approved": False}
        )
