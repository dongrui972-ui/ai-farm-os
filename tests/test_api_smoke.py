from __future__ import annotations

from typing import Any

ALLOWED_DATA_SOURCES = {"REAL", "SIMULATION", "MANUAL"}

ENDPOINTS = [
    "/api/health",
    "/api/meta",
    "/api/dashboard",
    "/api/twin",
    "/api/agronomy",
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


def _assert_data_source(item: dict[str, Any], field: str = "data_source") -> None:
    value = item.get(field)
    assert value in ALLOWED_DATA_SOURCES, f"unexpected data_source: {value}"


def test_p0_to_p3_routes_ok(client) -> None:
    for path in ENDPOINTS:
        response = client.get(path)
        assert response.status_code == 200, f"{path} failed: {response.status_code} {response.text}"


def test_seed_entities_and_detail_routes(client) -> None:
    assets = client.get("/api/assets").json()
    plants = client.get("/api/plants").json()
    irrigation = client.get("/api/irrigation").json()
    devices = client.get("/api/devices").json()
    agents = client.get("/api/agents").json()
    robots = client.get("/api/robots").json()
    assert assets and plants and irrigation and devices and agents and robots

    assert client.get(f"/api/assets/{assets[0]['id']}").status_code == 200
    assert client.get(f"/api/plants/{plants[0]['id']}").status_code == 200
    assert client.get(f"/api/irrigation/{irrigation[0]['id']}").status_code == 200
    assert client.get(f"/api/devices/{devices[0]['id']}").status_code == 200
    assert client.get(f"/api/agents/{agents[0]['id']}").status_code == 200
    assert client.get(f"/api/robots/{robots[0]['id']}").status_code == 200

    missing = client.get("/api/twin/zones/zone-missing")
    assert missing.status_code == 404


def test_write_paths_keep_data_source(client) -> None:
    task_create = client.post(
        "/api/tasks",
        json={"title": "pytest-task", "task_type": "general", "assignee": "测试", "data_source": "MANUAL"},
    )
    assert task_create.status_code == 200, task_create.text
    created = task_create.json()
    _assert_data_source(created)

    patched = client.patch(f"/api/tasks/{created['id']}", json={"status": "done"})
    assert patched.status_code == 200
    assert patched.json()["status"] == "done"

    diagnosis = client.post(
        "/api/diagnoses",
        json={"title": "pytest-diagnosis", "symptom": "叶背有斑", "data_source": "MANUAL", "confidence": 0},
    )
    assert diagnosis.status_code == 200
    _assert_data_source(diagnosis.json())

    job = client.post("/api/ai-center/jobs", json={"title": "pytest-job"})
    assert job.status_code == 200
    _assert_data_source(job.json())

    note = client.post(
        "/api/collaboration",
        json={"author": "测试", "role": "值班", "title": "pytest-note", "body": "仅用于测试", "related_module": "tests"},
    )
    assert note.status_code == 200
    _assert_data_source(note.json())

    agents = client.get("/api/agents").json()
    run = client.post(f"/api/agents/{agents[0]['id']}/run", json={"note": "pytest replay"})
    assert run.status_code == 200
    _assert_data_source(run.json())


def test_dashboard_is_decision_first(client) -> None:
    dashboard = client.get("/api/dashboard").json()
    assert dashboard["decisions"]
    assert dashboard["weather"]["data_source"] == "SIMULATION"
    assert dashboard["weather"]["et0_mm"] > 0
    assert "REAL" not in {dashboard["weather"]["data_source"]}
    kinds = {item["kind"] for item in dashboard["decisions"]}
    assert "irrigation" in kinds
    for decision in dashboard["decisions"]:
        _assert_data_source(decision)
        assert decision.get("why")
    assert dashboard["agronomy_counts"]["irrigate"] >= 1
