from pathlib import Path

from fastapi.testclient import TestClient

from app.infrastructure.settings import Settings
from app.main import create_app


def test_api_lifecycle(tmp_path: Path) -> None:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'api.db'}",
        artifact_dir=tmp_path / "artifacts",
        generation_provider="template",
    )
    with TestClient(create_app(settings)) as client:
        health = client.get("/api/v1/health/ready")
        assert health.status_code == 200

        created = client.post(
            "/api/v1/workflows",
            json={
                "title": "Invoice download",
                "requirement": "Customers download a PDF invoice from their order history.",
            },
        )
        assert created.status_code == 201
        workflow = created.json()
        assert workflow["active_gate"]["type"] == "clarification"

        for gate in ("clarification", "brd", "code_plan"):
            response = client.post(
                f"/api/v1/workflows/{workflow['id']}/approvals",
                json={"gate": gate, "approved": True},
            )
            assert response.status_code == 200
            workflow = response.json()

        assert workflow["status"] == "completed"
        artifacts = client.get(
            f"/api/v1/workflows/{workflow['id']}/artifacts"
        ).json()
        assert len(artifacts) == 13
        assert artifacts[-1]["type"] == "release_package"
