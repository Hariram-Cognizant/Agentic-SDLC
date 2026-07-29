from __future__ import annotations

from app.application.agents.base import AgentContext, slug
from app.domain.models import Artifact, ArtifactType


class CodeAgent:
    name = "code_agent"

    def plan(self, context: AgentContext) -> Artifact:
        brd = context.latest(ArtifactType.BRD)
        backlog = context.latest(ArtifactType.BACKLOG)
        feature_slug = slug(context.workflow.title).replace("-", "_")
        acceptance_ids = [
            criterion["id"]
            for story in backlog.content.get("stories", [])
            for criterion in story.get("acceptance_criteria", [])
        ]
        content = {
            "architecture": "ports_and_adapters",
            "module": f"features/{feature_slug}",
            "changes": [
                "Add typed domain model and validation",
                "Add application service and repository port",
                "Add HTTP endpoint with structured errors",
                "Add unit and integration tests",
            ],
            "security": ["Validate inputs", "Enforce authorization at the boundary"],
            "observability": ["Correlation ID", "Structured success/failure event"],
            "test_mapping": [
                {"acceptance_criterion_id": item, "test": f"test_{item.lower()}"}
                for item in acceptance_ids
            ],
            "traceability": {
                "brd_id": brd.content.get("document_id"),
                "acceptance_criteria": acceptance_ids,
            },
        }
        return context.create(
            ArtifactType.CODE_PLAN, "Code Plan", content, self.name, [brd, backlog]
        )

    def implement(self, context: AgentContext) -> Artifact:
        code_plan = context.latest(ArtifactType.CODE_PLAN)
        module_name = str(code_plan.content["module"]).replace("/", ".")
        code = (
            '"""Generated feature boundary; replace the handler with domain behavior."""\n\n'
            "from dataclasses import dataclass\n\n"
            "@dataclass(frozen=True, slots=True)\n"
            "class FeatureRequest:\n"
            "    value: str\n\n"
            "def execute(request: FeatureRequest) -> dict[str, str]:\n"
            "    if not request.value.strip():\n"
            '        raise ValueError("value must not be empty")\n'
            '    return {"status": "accepted", "value": request.value}\n'
        )
        tests = (
            "import pytest\n\n"
            f"from {module_name} import FeatureRequest, execute\n\n"
            "def test_valid_request_is_accepted():\n"
            '    assert execute(FeatureRequest("sample"))["status"] == "accepted"\n\n'
            "def test_empty_request_is_rejected():\n"
            "    with pytest.raises(ValueError):\n"
            '        execute(FeatureRequest("  "))\n'
        )
        content = {
            "language": "python",
            "files": [
                {"path": f"{code_plan.content['module']}.py", "content": code},
                {"path": f"tests/test_{slug(context.workflow.title)}.py", "content": tests},
            ],
            "status": "generated_stub",
            "notice": "The stub is an artifact; source-control application requires approval.",
        }
        return context.create(
            ArtifactType.IMPLEMENTATION,
            "Generated Implementation",
            content,
            self.name,
            [code_plan],
        )
