from typing import Any

from app.application.agents.base import slug
from app.domain.models import Artifact, Workflow


class HandoffSourceControl:
    """Safe default adapter that plans Git operations without mutating a repository."""

    def prepare_handoff(
        self, workflow: Workflow, implementation: Artifact
    ) -> dict[str, Any]:
        branch = f"feature/{slug(workflow.title)}-{workflow.id[:8]}"
        return {
            "mode": "handoff",
            "branch": branch,
            "commit_message": f"feat: {workflow.title}",
            "files": [item["path"] for item in implementation.content.get("files", [])],
            "pull_request": {
                "title": f"feat: {workflow.title}",
                "body": (
                    f"Automated delivery artifact for workflow {workflow.id}. "
                    "Review lineage and validation results before applying."
                ),
            },
            "commands": [
                f"git switch -c {branch}",
                "apply generated implementation files",
                "run repository quality gates",
                "commit and push after human confirmation",
            ],
            "mutated_repository": False,
        }
