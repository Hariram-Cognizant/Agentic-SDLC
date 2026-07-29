from __future__ import annotations

from app.application.agents.base import AgentContext
from app.domain.models import Artifact, ArtifactType


class BrdAgent:
    name = "brd_agent"

    def run(self, context: AgentContext) -> Artifact:
        requirement = context.latest(ArtifactType.REQUIREMENT)
        clarification = context.latest(ArtifactType.CLARIFICATIONS)
        approval = context.workflow.approvals.get("clarification", {})
        intent = str(requirement.content.get("feature_intent", context.workflow.title))
        fallback = {
            "document_id": f"BRD-{context.workflow.id[:8].upper()}",
            "version": "1.0",
            "title": context.workflow.title,
            "executive_summary": intent,
            "business_objectives": [
                "Deliver the requested capability with end-to-end traceability",
                "Reduce manual handoffs and ambiguity",
            ],
            "in_scope": [intent],
            "out_of_scope": approval.get("out_of_scope", []),
            "stakeholders": requirement.content.get("actors", []),
            "functional_requirements": [
                {"id": "FR-001", "description": intent, "priority": "must"}
            ],
            "non_functional_requirements": requirement.content.get(
                "non_functional_requirements", []
            ),
            "constraints": requirement.content.get("constraints", []),
            "assumptions": approval.get(
                "assumptions", requirement.content.get("assumptions", [])
            ),
            "success_metrics": approval.get(
                "success_metrics",
                ["All acceptance criteria pass", "No critical review findings"],
            ),
            "clarification_answers": approval.get("answers", {}),
            "confidence": {
                "executive_summary": 0.95,
                "scope": 0.85,
                "requirements": 0.85,
                "success_metrics": 0.75,
            },
        }
        content = context.generator.generate_json(
            system_prompt="Create a concise, versioned business requirements document as JSON.",
            user_prompt=str({"requirement": requirement.content, "approval": approval}),
            fallback=fallback,
        )
        return context.create(
            ArtifactType.BRD,
            "Business Requirements Document",
            content,
            self.name,
            [requirement, clarification],
        )


class StoryAgent:
    name = "story_agent"

    def run(self, context: AgentContext) -> Artifact:
        brd = context.latest(ArtifactType.BRD)
        functional = brd.content.get("functional_requirements", [])
        stories = []
        for index, item in enumerate(functional or [{}], start=1):
            description = item.get(
                "description", brd.content.get("executive_summary", "feature")
            )
            story_id = f"US-{index:03d}"
            stories.append(
                {
                    "id": story_id,
                    "epic_id": "EPIC-001",
                    "title": description,
                    "narrative": (
                        f"As an authorized user, I want {description.lower()} "
                        "so that the business objective is achieved."
                    ),
                    "acceptance_criteria": [
                        {
                            "id": f"AC-{index:03d}-1",
                            "given": "an authorized user and valid input",
                            "when": "the feature is invoked",
                            "then": "the requested outcome is completed and auditable",
                        },
                        {
                            "id": f"AC-{index:03d}-2",
                            "given": "invalid or unauthorized input",
                            "when": "the feature is invoked",
                            "then": "the request is rejected with a safe error",
                        },
                    ],
                    "subtasks": ["Implement behavior", "Add tests", "Add observability"],
                    "story_points": 5,
                    "dependencies": [],
                }
            )
        content = {
            "epics": [
                {"id": "EPIC-001", "title": brd.content.get("title"), "priority": "high"}
            ],
            "stories": stories,
            "dependency_map": [
                {"from": story["id"], "to": "EPIC-001", "type": "belongs_to"}
                for story in stories
            ],
        }
        return context.create(ArtifactType.BACKLOG, "Delivery Backlog", content, self.name, [brd])


class PlanAgent:
    name = "plan_agent"

    def run(self, context: AgentContext) -> Artifact:
        backlog = context.latest(ArtifactType.BACKLOG)
        stories = backlog.content.get("stories", [])
        sequence = [
            {
                "order": index,
                "story_id": story["id"],
                "story_points": story["story_points"],
                "readiness": "ready",
            }
            for index, story in enumerate(stories, start=1)
        ]
        content = {
            "sprint_goal": f"Deliver {context.workflow.title}",
            "capacity_points": 20,
            "planned_points": sum(item["story_points"] for item in sequence),
            "sequence": sequence,
            "critical_path": [item["story_id"] for item in sequence],
            "risks": [
                {
                    "id": "RISK-001",
                    "description": "Unvalidated integration assumptions",
                    "mitigation": "Validate adapters before production rollout",
                    "severity": "medium",
                }
            ],
            "handoff_readiness": {
                "requirements_approved": True,
                "acceptance_criteria_present": all(
                    bool(story.get("acceptance_criteria")) for story in stories
                ),
                "dependencies_resolved": True,
            },
        }
        return context.create(
            ArtifactType.SPRINT_PLAN, "Sprint Plan", content, self.name, [backlog]
        )
