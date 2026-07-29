from dataclasses import dataclass

from app.application.orchestrator import WorkflowOrchestrator
from app.domain.ports import WorkflowRepository


@dataclass(frozen=True, slots=True)
class Container:
    repository: WorkflowRepository
    orchestrator: WorkflowOrchestrator
    generation_provider: str
