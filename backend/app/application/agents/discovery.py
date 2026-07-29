from __future__ import annotations

from app.application.agents.base import AgentContext, sentences
from app.domain.models import Artifact, ArtifactType


class IntakeAgent:
    name = "intake_agent"

    def run(self, context: AgentContext) -> Artifact:
        workflow = context.workflow
        items = sentences(workflow.raw_requirement)
        fallback = {
            "feature_intent": items[0] if items else workflow.title,
            "actors": ["End user", "System administrator"],
            "business_rules": items[1:4],
            "constraints": ["Preserve backward compatibility", "Maintain auditability"],
            "non_functional_requirements": [
                "Secure-by-default access control",
                "Observable execution",
                "Deterministic failure recovery",
            ],
            "dependencies": [],
            "assumptions": [
                "The requirement describes one independently deliverable feature",
                "Human approvers are authorized to accept delivery decisions",
            ],
            "open_questions": [
                "Which user roles may access the feature?",
                "What measurable success criteria apply?",
                "Are there external integration constraints?",
            ],
            "source": {"name": workflow.source_name, "kind": "text"},
        }
        content = context.generator.generate_json(
            system_prompt="Normalize a software feature requirement into structured JSON.",
            user_prompt=workflow.raw_requirement,
            fallback=fallback,
        )
        return context.create(
            ArtifactType.REQUIREMENT, "Normalized Requirement", content, self.name
        )


class ContextAgent:
    name = "context_agent"

    def run(self, context: AgentContext) -> Artifact:
        requirement = context.latest(ArtifactType.REQUIREMENT)
        query = str(requirement.content.get("feature_intent", context.workflow.title))
        matches = [
            {
                "artifact_id": artifact.id,
                "workflow_id": artifact.workflow_id,
                "type": artifact.type.value,
                "name": artifact.name,
                "relevance": "keyword_match",
            }
            for artifact in context.repository.find_related_artifacts(query)
            if artifact.workflow_id != context.workflow.id
        ]
        content = {
            "query": query,
            "related_artifacts": matches,
            "prior_decisions": [],
            "reusable_patterns": [
                "Version every generated artifact",
                "Require approval before implementation",
                "Map tests to acceptance criteria",
            ],
            "retrieval_summary": f"Found {len(matches)} related artifact(s).",
        }
        return context.create(
            ArtifactType.CONTEXT_PACK,
            "Knowledge Context Pack",
            content,
            self.name,
            [requirement],
        )


class ClarificationAgent:
    name = "clarification_agent"

    def run(self, context: AgentContext) -> Artifact:
        requirement = context.latest(ArtifactType.REQUIREMENT)
        context_pack = context.latest(ArtifactType.CONTEXT_PACK)
        content = {
            "questions": requirement.content.get("open_questions", []),
            "recommended_assumptions": requirement.content.get("assumptions", []),
            "context_considered": context_pack.content.get("retrieval_summary"),
            "status": "awaiting_architect",
        }
        return context.create(
            ArtifactType.CLARIFICATIONS,
            "Clarification Register",
            content,
            self.name,
            [requirement, context_pack],
        )
