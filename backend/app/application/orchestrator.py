from __future__ import annotations

import logging
from typing import Any

from app.application.agents import (
    BrdAgent,
    ClarificationAgent,
    CodeAgent,
    ContextAgent,
    GitAgent,
    IntakeAgent,
    PlanAgent,
    ReleaseAgent,
    ReviewAgent,
    SanityAgent,
    StoryAgent,
)
from app.application.agents.base import AgentContext
from app.application.exceptions import InvalidApprovalError, WorkflowNotFoundError
from app.domain.models import ApprovalGate, GateType, Workflow, WorkflowStatus, utc_now
from app.domain.ports import SourceControl, TextGenerator, WorkflowRepository

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    def __init__(
        self,
        repository: WorkflowRepository,
        generator: TextGenerator,
        source_control: SourceControl,
    ) -> None:
        self.repository = repository
        self.generator = generator
        self.intake = IntakeAgent()
        self.context = ContextAgent()
        self.clarification = ClarificationAgent()
        self.brd = BrdAgent()
        self.story = StoryAgent()
        self.plan = PlanAgent()
        self.code = CodeAgent()
        self.git = GitAgent(source_control)
        self.review = ReviewAgent()
        self.sanity = SanityAgent()
        self.release = ReleaseAgent()

    def create(self, title: str, requirement: str, source_name: str | None = None) -> Workflow:
        workflow = Workflow(
            title=title.strip(), raw_requirement=requirement.strip(), source_name=source_name
        )
        self.repository.save_workflow(workflow)
        return self._advance(workflow)

    def approve(
        self, workflow_id: str, gate: GateType, decision_data: dict[str, Any]
    ) -> Workflow:
        workflow = self.get(workflow_id)
        if (
            workflow.status != WorkflowStatus.AWAITING_APPROVAL
            or workflow.active_gate is None
            or workflow.active_gate.type != gate
        ):
            expected = workflow.active_gate.type.value if workflow.active_gate else "none"
            raise InvalidApprovalError(
                f"Workflow is not awaiting '{gate.value}' approval; expected '{expected}'."
            )
        if decision_data.get("approved") is not True:
            raise InvalidApprovalError("Approval payload must explicitly set approved=true.")
        workflow.approvals[gate.value] = decision_data
        workflow.active_gate = None
        workflow.status = WorkflowStatus.RUNNING
        workflow.updated_at = utc_now()
        self.repository.save_workflow(workflow)
        return self._advance(workflow)

    def get(self, workflow_id: str) -> Workflow:
        workflow = self.repository.get_workflow(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError(f"Workflow '{workflow_id}' does not exist.")
        return workflow

    def _advance(self, workflow: Workflow) -> Workflow:
        context = AgentContext(workflow, self.repository, self.generator)
        try:
            if workflow.phase == "intake":
                self.intake.run(context)
                self.context.run(context)
                self.clarification.run(context)
                self._pause(
                    workflow,
                    next_phase="planning",
                    gate=ApprovalGate(
                        GateType.CLARIFICATION,
                        "Resolve requirement clarifications",
                        "Answer open questions and confirm assumptions before BRD creation.",
                        ["approved"],
                    ),
                )
                return workflow

            if workflow.phase == "planning":
                self.brd.run(context)
                self.story.run(context)
                self.plan.run(context)
                self._pause(
                    workflow,
                    next_phase="code_planning",
                    gate=ApprovalGate(
                        GateType.BRD,
                        "Approve BRD and delivery plan",
                        "Review scope, stories, acceptance criteria, and sprint risks.",
                        ["approved"],
                    ),
                )
                return workflow

            if workflow.phase == "code_planning":
                self.code.plan(context)
                self._pause(
                    workflow,
                    next_phase="delivery",
                    gate=ApprovalGate(
                        GateType.CODE_PLAN,
                        "Approve code plan",
                        "Confirm architecture, security controls, and test mapping.",
                        ["approved"],
                    ),
                )
                return workflow

            if workflow.phase == "delivery":
                self.code.implement(context)
                self.git.run(context)
                self.review.run(context)
                self.sanity.run(context)
                self.release.run(context)
                workflow.phase = "complete"
                workflow.status = WorkflowStatus.COMPLETED
                workflow.updated_at = utc_now()
                self.repository.save_workflow(workflow)
                return workflow

            return workflow
        except Exception as exc:
            logger.exception("Workflow %s failed in phase %s", workflow.id, workflow.phase)
            workflow.status = WorkflowStatus.FAILED
            workflow.error = str(exc)
            workflow.updated_at = utc_now()
            self.repository.save_workflow(workflow)
            raise

    def _pause(
        self, workflow: Workflow, *, next_phase: str, gate: ApprovalGate
    ) -> None:
        workflow.phase = next_phase
        workflow.status = WorkflowStatus.AWAITING_APPROVAL
        workflow.active_gate = gate
        workflow.updated_at = utc_now()
        self.repository.save_workflow(workflow)
