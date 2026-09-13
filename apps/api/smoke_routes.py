from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

ALLOWED_DATA_SOURCES = {"REAL", "SIMULATION", "MANUAL"}


def _assert_data_source(item: dict[str, Any], field: str = "data_source") -> None:
    value = item.get(field)
    assert value in ALLOWED_DATA_SOURCES, f"unexpected data_source: {value}"


def _assert_ok(client: TestClient, path: str) -> Any:
    response = client.get(path)
    assert response.status_code == 200, f"{path} failed: {response.status_code} {response.text}"
    return response.json()


def _run_smoke() -> None:
    endpoints = [
        "/api/health",
        "/api/meta",
        "/api/dashboard",
        "/api/twin",
        "/api/workbench",
        "/api/seasons",
        "/api/architecture",
        "/api/assets",
        "/api/plants",
        "/api/irrigation",
        "/api/tasks",
        "/api/devices",
        "/api/agents",
        "/api/diagnoses",
        "/api/ai-center/jobs",
        "/api/robots",
        "/api/fleet",
        "/api/postharvest",
        "/api/vendors",
        "/api/collaboration",
    ]

    with tempfile.TemporaryDirectory(prefix="ai-farm-smoke-") as temp_dir:
        db_path = Path(temp_dir) / "smoke.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        os.environ["SEED_ON_EMPTY"] = "true"

        from app.main import app

        with TestClient(app) as client:
            for path in endpoints:
                _assert_ok(client, path)

            dashboard = _assert_ok(client, "/api/dashboard")
            for decision in dashboard.get("decisions", []):
                _assert_data_source(decision)
            for zone in dashboard.get("risk_zones", []):
                _assert_data_source(zone)

            assets = _assert_ok(client, "/api/assets")
            plants = _assert_ok(client, "/api/plants")
            irrigation = _assert_ok(client, "/api/irrigation")
            devices = _assert_ok(client, "/api/devices")
            agents = _assert_ok(client, "/api/agents")
            robots = _assert_ok(client, "/api/robots")

            assert assets and plants and irrigation and devices and agents and robots, "seed data must not be empty"

            _assert_ok(client, f"/api/assets/{assets[0]['id']}")
            _assert_ok(client, f"/api/plants/{plants[0]['id']}")
            _assert_ok(client, f"/api/irrigation/{irrigation[0]['id']}")
            _assert_ok(client, f"/api/devices/{devices[0]['id']}")
            _assert_ok(client, f"/api/agents/{agents[0]['id']}")
            _assert_ok(client, f"/api/robots/{robots[0]['id']}")

            task_create = client.post(
                "/api/tasks",
                json={"title": "smoke-task", "task_type": "general", "assignee": "测试", "data_source": "MANUAL"},
            )
            assert task_create.status_code == 200, task_create.text
            created_task = task_create.json()
            _assert_data_source(created_task)

            task_patch = client.patch(f"/api/tasks/{created_task['id']}", json={"status": "done"})
            assert task_patch.status_code == 200, task_patch.text
            assert task_patch.json().get("status") == "done"

            diagnosis_create = client.post(
                "/api/diagnoses",
                json={"title": "smoke-diagnosis", "symptom": "叶背有斑", "data_source": "MANUAL", "confidence": 0},
            )
            assert diagnosis_create.status_code == 200, diagnosis_create.text
            _assert_data_source(diagnosis_create.json())

            job_create = client.post("/api/ai-center/jobs", json={"title": "smoke-job"})
            assert job_create.status_code == 200, job_create.text
            _assert_data_source(job_create.json())

            note_create = client.post(
                "/api/collaboration",
                json={"author": "测试", "role": "值班", "title": "smoke-note", "body": "仅用于冒烟脚本", "related_module": "smoke"},
            )
            assert note_create.status_code == 200, note_create.text
            _assert_data_source(note_create.json())

            run_agent = client.post(f"/api/agents/{agents[0]['id']}/run", json={"note": "smoke replay"})
            assert run_agent.status_code == 200, run_agent.text
            _assert_data_source(run_agent.json())

            robot_command = client.post(f"/api/robots/{robots[0]['id']}/command", json={"command": "goto"})
            assert robot_command.status_code == 409, f"robot command should be blocked: {robot_command.text}"
            detail = robot_command.json().get("detail", {})
            assert detail.get("error") == "robot_unbound"

            recommendable = next((item for item in irrigation if item.get("recommendation_mm")), None)
            assert recommendable, "irrigation seed must contain recommendable item"
            accept = client.post(f"/api/irrigation/{recommendable['id']}/accept-recommendation", json={})
            assert accept.status_code == 200, accept.text
            accept_payload = accept.json()
            assert "未向阀门下发指令" in accept_payload.get("note", "")
            _assert_data_source(accept_payload.get("task", {}))

        print("smoke_routes: ok")


if __name__ == "__main__":
    _run_smoke()
