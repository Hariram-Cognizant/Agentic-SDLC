from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.domain.models import Artifact, ArtifactType, Workflow
from app.domain.ports import TextGenerator, WorkflowRepository


@dataclass(slots=True)
class AgentContext:
    workflow: Workflow
    repository: WorkflowRepository
    generator: TextGenerator

    def latest(self, artifact_type: ArtifactType) -> Artifact:
        artifact = self.repository.get_artifact(self.workflow.id, artifact_type.value)
        if artifact is None:
            raise RuntimeError(f"Required artifact is missing: {artifact_type.value}")
        return artifact

    def create(
        self,
        artifact_type: ArtifactType,
        name: str,
        content: dict[str, Any],
        produced_by: str,
        parents: list[Artifact] | None = None,
    ) -> Artifact:
        artifact = Artifact(
            workflow_id=self.workflow.id,
            type=artifact_type,
            name=name,
            content=content,
            produced_by=produced_by,
            parent_ids=[item.id for item in parents or []],
        )
        self.repository.save_artifact(artifact)
        return artifact


def sentences(text: str) -> list[str]:
    return [item.strip(" -\t") for item in re.split(r"[\n.!?]+", text) if item.strip()]


def slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned[:48] or "feature"
