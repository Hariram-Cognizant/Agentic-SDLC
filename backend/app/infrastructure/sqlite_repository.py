from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from app.domain.models import (
    ApprovalGate,
    Artifact,
    ArtifactType,
    GateType,
    Workflow,
    WorkflowStatus,
)


class SQLiteWorkflowRepository:
    def __init__(self, database_url: str) -> None:
        prefix = "sqlite:///"
        if not database_url.startswith(prefix):
            raise ValueError("Only sqlite:/// database URLs are supported")
        self.path = Path(database_url.removeprefix(prefix)).resolve()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_workflows_updated
                    ON workflows(updated_at DESC);
                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL REFERENCES workflows(id),
                    type TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    searchable_text TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    UNIQUE(workflow_id, type, version)
                );
                CREATE INDEX IF NOT EXISTS idx_artifacts_workflow
                    ON artifacts(workflow_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_artifacts_type
                    ON artifacts(type);
                """
            )

    def save_workflow(self, workflow: Workflow) -> None:
        payload = workflow.to_dict()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO workflows(id, status, updated_at, payload)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status,
                    updated_at=excluded.updated_at,
                    payload=excluded.payload
                """,
                (
                    workflow.id,
                    workflow.status.value,
                    workflow.updated_at.isoformat(),
                    json.dumps(payload),
                ),
            )

    def get_workflow(self, workflow_id: str) -> Workflow | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM workflows WHERE id = ?", (workflow_id,)
            ).fetchone()
        return self._workflow_from_payload(json.loads(row["payload"])) if row else None

    def list_workflows(self, limit: int = 50) -> list[Workflow]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM workflows ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._workflow_from_payload(json.loads(row["payload"])) for row in rows]

    def save_artifact(self, artifact: Artifact) -> None:
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT COALESCE(MAX(version), 0) AS version FROM artifacts "
                "WHERE workflow_id = ? AND type = ?",
                (artifact.workflow_id, artifact.type.value),
            ).fetchone()
            artifact.version = int(existing["version"]) + 1
            payload = artifact.to_dict()
            connection.execute(
                """
                INSERT INTO artifacts(
                    id, workflow_id, type, version, created_at, searchable_text, payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact.id,
                    artifact.workflow_id,
                    artifact.type.value,
                    artifact.version,
                    artifact.created_at.isoformat(),
                    json.dumps(artifact.content).lower(),
                    json.dumps(payload),
                ),
            )

    def list_artifacts(self, workflow_id: str) -> list[Artifact]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM artifacts WHERE workflow_id = ? ORDER BY created_at",
                (workflow_id,),
            ).fetchall()
        return [self._artifact_from_payload(json.loads(row["payload"])) for row in rows]

    def get_artifact(self, workflow_id: str, artifact_type: str) -> Artifact | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM artifacts WHERE workflow_id = ? AND type = ? "
                "ORDER BY version DESC LIMIT 1",
                (workflow_id, artifact_type),
            ).fetchone()
        return self._artifact_from_payload(json.loads(row["payload"])) if row else None

    def find_related_artifacts(self, query: str, limit: int = 5) -> list[Artifact]:
        terms = [term.lower() for term in query.split() if len(term) > 3][:5]
        if not terms:
            return []
        clauses = " OR ".join("searchable_text LIKE ?" for _ in terms)
        parameters = [f"%{term}%" for term in terms]
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT payload FROM artifacts WHERE {clauses} "
                "ORDER BY created_at DESC LIMIT ?",
                (*parameters, limit),
            ).fetchall()
        return [self._artifact_from_payload(json.loads(row["payload"])) for row in rows]

    @staticmethod
    def _workflow_from_payload(payload: dict[str, Any]) -> Workflow:
        gate_payload = payload.get("active_gate")
        gate = None
        if isinstance(gate_payload, dict):
            gate = ApprovalGate(
                type=GateType(str(gate_payload["type"])),
                title=str(gate_payload["title"]),
                instructions=str(gate_payload["instructions"]),
                required_fields=list(gate_payload.get("required_fields", [])),
                created_at=datetime.fromisoformat(str(gate_payload["created_at"])),
            )
        return Workflow(
            id=str(payload["id"]),
            title=str(payload["title"]),
            raw_requirement=str(payload["raw_requirement"]),
            source_name=(
                str(payload["source_name"]) if payload.get("source_name") is not None else None
            ),
            status=WorkflowStatus(str(payload["status"])),
            phase=str(payload["phase"]),
            active_gate=gate,
            approvals=dict(payload.get("approvals", {})),
            error=str(payload["error"]) if payload.get("error") is not None else None,
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
        )

    @staticmethod
    def _artifact_from_payload(payload: dict[str, Any]) -> Artifact:
        return Artifact(
            id=str(payload["id"]),
            workflow_id=str(payload["workflow_id"]),
            type=ArtifactType(str(payload["type"])),
            name=str(payload["name"]),
            content=dict(payload["content"]),
            produced_by=str(payload["produced_by"]),
            parent_ids=list(payload.get("parent_ids", [])),
            version=int(payload["version"]),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
        )
