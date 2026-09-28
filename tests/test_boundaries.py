from __future__ import annotations

ALLOWED = {"REAL", "SIMULATION", "MANUAL"}


def test_robot_command_always_409(client) -> None:
    robots = client.get("/api/robots").json()
    assert robots
    assert robots[0]["last_pose"] is None
    assert robots[0]["live_gps"] is False
    assert robots[0]["control_enabled"] is False
    response = client.post(f"/api/robots/{robots[0]['id']}/command", json={"command": "goto"})
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["error"] == "robot_unbound"
    assert "拒绝" in detail["message"]


def test_irrigation_accept_is_task_only(client) -> None:
    irrigation = client.get("/api/irrigation").json()
    for item in irrigation:
        assert item["control_enabled"] is False
        assert item["agronomy"]["data_source"] == "SIMULATION"
        assert item["agronomy"]["control_enabled"] is False

    target = next(item for item in irrigation if item["agronomy"]["action"] == "irrigate")
    before_tasks = {row["id"] for row in client.get("/api/tasks").json()}
    accept = client.post(f"/api/irrigation/{target['id']}/accept-recommendation", json={})
    assert accept.status_code == 200, accept.text
    payload = accept.json()
    assert "未向阀门下发指令" in payload["note"]
    assert payload["task"]["task_type"] == "irrigation"
    assert payload["task"]["origin"] == "ai_suggested"
    assert payload["task"]["data_source"] in ALLOWED
    assert payload["circuit"]["status"] == "accepted"
    assert payload["task"]["id"] not in before_tasks
    assert "valve" not in payload
    assert payload["agronomy"]["control_enabled"] is False


def test_no_real_sensors_in_seed(client) -> None:
    for path in ("/api/devices", "/api/plants", "/api/irrigation", "/api/robots", "/api/agronomy"):
        body = client.get(path).json()
        rows = body if isinstance(body, list) else body.get("zones", [body])
        for item in rows:
            source = item.get("data_source")
            if source:
                assert source in ALLOWED
            assert source != "REAL"
    weather = client.get("/api/agronomy").json()["weather"]
    assert weather["data_source"] == "SIMULATION"
    devices = client.get("/api/devices").json()
    assert all(item.get("live") is False for item in devices)
