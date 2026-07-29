from __future__ import annotations

from app.application.agents.base import AgentContext
from app.domain.models import Artifact, ArtifactType
from app.domain.ports import SourceControl


class GitAgent:
    name = "git_agent"

    def __init__(self, source_control: SourceControl) -> None:
        self._source_control = source_control

    def run(self, context: AgentContext) -> Artifact:
        implementation = context.latest(ArtifactType.IMPLEMENTATION)
        content = self._source_control.prepare_handoff(context.workflow, implementation)
        return context.create(
            ArtifactType.GIT_HANDOFF,
            "Source Control Handoff",
            content,
            self.name,
            [implementation],
        )


class ReviewAgent:
    name = "review_agent"

    def run(self, context: AgentContext) -> Artifact:
        implementation = context.latest(ArtifactType.IMPLEMENTATION)
        backlog = context.latest(ArtifactType.BACKLOG)
        criteria = [
            criterion
            for story in backlog.content.get("stories", [])
            for criterion in story.get("acceptance_criteria", [])
        ]
        file_text = "\n".join(
            item["content"] for item in implementation.content.get("files", [])
        )
        findings = []
        if "ValueError" not in file_text:
            findings.append(
                {
                    "severity": "high",
                    "category": "validation",
                    "message": "No explicit invalid-input handling was found.",
                }
            )
        content = {
            "decision": "approved_with_advisories" if not findings else "changes_requested",
            "findings": findings,
            "traceability": [
                {
                    "acceptance_criterion_id": criterion["id"],
                    "coverage": "mapped",
                    "evidence": "generated unit-test mapping",
                }
                for criterion in criteria
            ],
            "quality_checks": {
                "input_validation": "ValueError" in file_text,
                "unit_tests_present": any(
                    item["path"].startswith("tests/")
                    for item in implementation.content["files"]
                ),
                "critical_findings": any(
                    item["severity"] == "critical" for item in findings
                ),
            },
        }
        return context.create(
            ArtifactType.REVIEW,
            "Code Review Report",
            content,
            self.name,
            [implementation, backlog],
        )


class SanityAgent:
    name = "sanity_agent"

    def run(self, context: AgentContext) -> tuple[Artifact, Artifact]:
        implementation = context.latest(ArtifactType.IMPLEMENTATION)
        review = context.latest(ArtifactType.REVIEW)
        tests = [
            item
            for item in implementation.content.get("files", [])
            if item["path"].startswith("tests/")
        ]
        passed = review.content.get("decision") != "changes_requested" and bool(tests)
        result = context.create(
            ArtifactType.SANITY_RESULT,
            "Sanity Test Result",
            {
                "mode": "simulated",
                "status": "passed" if passed else "failed",
                "tests_discovered": len(tests),
                "tests_passed": len(tests) if passed else 0,
                "tests_failed": 0 if passed else len(tests),
                "acceptance_criteria_coverage": review.content.get("traceability", []),
            },
            self.name,
            [implementation, review],
        )
        defects = []
        if not passed:
            defects.append(
                {
                    "id": f"DEF-{context.workflow.id[:6].upper()}-001",
                    "severity": "high",
                    "summary": "Generated implementation failed sanity validation",
                    "status": "open",
                    "evidence_artifact_id": result.id,
                }
            )
        defect_register = context.create(
            ArtifactType.DEFECTS,
            "Defect Register",
            {"defects": defects, "count": len(defects)},
            self.name,
            [result],
        )
        return result, defect_register


class ReleaseAgent:
    name = "release_agent"

    def run(self, context: AgentContext) -> Artifact:
        requirement = context.latest(ArtifactType.REQUIREMENT)
        implementation = context.latest(ArtifactType.IMPLEMENTATION)
        review = context.latest(ArtifactType.REVIEW)
        sanity = context.latest(ArtifactType.SANITY_RESULT)
        defects = context.latest(ArtifactType.DEFECTS)
        artifacts = context.repository.list_artifacts(context.workflow.id)
        content = {
            "release_notes": {
                "title": context.workflow.title,
                "summary": requirement.content.get("feature_intent"),
                "changes": [
                    item["path"] for item in implementation.content.get("files", [])
                ],
            },
            "qa_handoff": {
                "test_status": sanity.content.get("status"),
                "review_decision": review.content.get("decision"),
                "open_defects": defects.content.get("count"),
                "risks": [
                    "Implementation is a generated stub requiring repository integration."
                ],
                "recommended_focus": [
                    "Authorization boundaries",
                    "External integration behavior",
                    "Performance under production load",
                ],
            },
            "lineage": [
                {
                    "artifact_id": item.id,
                    "type": item.type.value,
                    "parents": item.parent_ids,
                    "produced_by": item.produced_by,
                }
                for item in artifacts
            ],
            "readiness": (
                "ready_for_qa"
                if sanity.content.get("status") == "passed"
                else "blocked"
            ),
        }
        return context.create(
            ArtifactType.RELEASE_PACKAGE,
            "Release and QA Handoff Package",
            content,
            self.name,
            [requirement, implementation, review, sanity, defects],
        )
