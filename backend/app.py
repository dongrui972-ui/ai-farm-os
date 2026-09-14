from __future__ import annotations

import json
import os
import random
import re
import secrets
import threading
import time
import uuid
from datetime import datetime
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from backend.db import ROOT, connect, init_db

conn = connect()
init_db(conn)
lock = threading.Lock()

app = FastAPI(title="一级芯界 AI Farm OS", version="1.1.0")
trusted_origins = [
    item.strip()
    for item in os.environ.get(
        "AI_FARM_ALLOWED_ORIGINS",
        "http://127.0.0.1:8080,http://localhost:8080,http://127.0.0.1:8090,http://localhost:8090",
    ).split(",")
    if item.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=trusted_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-AI-Farm-Token", "Idempotency-Key"],
)


class LimitedRequestBodyMiddleware:
    """Enforce the API body limit even when Content-Length is absent or untrusted."""

    def __init__(self, app: Any, max_body_bytes: int = 65_536) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        method = str(scope.get("method", "GET")).upper()
        if (
            scope.get("type") != "http"
            or not str(scope.get("path", "")).startswith("/api/")
            or method in {"GET", "HEAD", "OPTIONS"}
        ):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        raw_length = headers.get(b"content-length", b"").strip()
        if raw_length.isdigit() and int(raw_length) > self.max_body_bytes:
            response = JSONResponse(
                status_code=413,
                content={"detail": "请求体超过 64 KiB 限制", "error_code": "PAYLOAD_TOO_LARGE", "retryable": False},
            )
            await response(scope, receive, send)
            return

        body_parts: list[bytes] = []
        received = 0
        while True:
            message = await receive()
            if message.get("type") == "http.disconnect":
                return
            if message.get("type") != "http.request":
                continue
            chunk = message.get("body", b"")
            received += len(chunk)
            if received > self.max_body_bytes:
                response = JSONResponse(
                    status_code=413,
                    content={"detail": "请求体超过 64 KiB 限制", "error_code": "PAYLOAD_TOO_LARGE", "retryable": False},
                )
                await response(scope, receive, send)
                return
            body_parts.append(chunk)
            if not message.get("more_body", False):
                break

        buffered_body = b"".join(body_parts)
        delivered = False

        async def replay_receive() -> dict[str, Any]:
            nonlocal delivered
            if delivered:
                return {"type": "http.request", "body": b"", "more_body": False}
            delivered = True
            return {"type": "http.request", "body": buffered_body, "more_body": False}

        await self.app(scope, replay_receive, send)


app.add_middleware(LimitedRequestBodyMiddleware, max_body_bytes=65_536)

ALLOW_DEMO_WRITES = os.environ.get("AI_FARM_ALLOW_DEMO_WRITES", "0") == "1"
WRITE_TOKEN = os.environ.get("AI_FARM_WRITE_TOKEN", "")
SIMULATOR_ENABLED = os.environ.get("AI_FARM_SIMULATOR", "0") == "1"
simulator_health: dict[str, Any] = {
    "enabled": SIMULATOR_ENABLED,
    "status": "disabled" if not SIMULATOR_ENABLED else "starting",
    "last_error": None,
    "last_generated_at": None,
}


@app.middleware("http")
async def security_boundary(request: Request, call_next):
    request_id = (request.headers.get("Idempotency-Key") or str(uuid.uuid4())).strip()[:128]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", request_id):
        request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = None
    if request.url.path.startswith("/api/"):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > 65_536:
                    response = JSONResponse(
                        status_code=413,
                        content={"detail": "请求体超过 64 KiB 限制", "error_code": "PAYLOAD_TOO_LARGE", "retryable": False},
                    )
            except ValueError:
                response = JSONResponse(
                    status_code=400,
                    content={"detail": "Content-Length 无效", "error_code": "INVALID_CONTENT_LENGTH", "retryable": False},
                )
    if request.url.path.startswith("/api/") and request.method not in ("GET", "HEAD", "OPTIONS"):
        if response is None and not ALLOW_DEMO_WRITES:
            response = JSONResponse(
                status_code=423,
                content={
                    "detail": "后端仿真写操作默认锁定；如需沙箱写入，请显式配置令牌。",
                    "error_code": "DEMO_WRITES_LOCKED",
                    "retryable": False,
                },
            )
        elif response is None:
            supplied = request.headers.get("X-AI-Farm-Token", "")
        if response is None and (not WRITE_TOKEN or not secrets.compare_digest(supplied, WRITE_TOKEN)):
            response = JSONResponse(
                status_code=401,
                content={"detail": "缺少或无效的仿真写入令牌", "error_code": "AUTH_REQUIRED", "retryable": False},
            )
    if response is None:
        response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Request-ID"] = request_id
    return response

LOOP = "传感器 → 数据平台 → 农业大模型 → Multi-Agent → 无人设备 → 生产反馈"
ARCHITECTURE = {
    "layers": [
        {"name": "感知层", "items": ["传感器", "无人机", "卫星", "农机"]},
        {"name": "数据层", "items": ["PostgreSQL", "PostGIS", "TimescaleDB", "Milvus", "Neo4j", "MinIO"]},
        {"name": "AI层", "items": ["农业大模型", "RAG", "Vision", "Prediction", "Simulation"]},
        {"name": "Agent层", "items": ["Farm Master", "Crop", "Irrigation", "Vision", "Robot", "Yield", "Finance"]},
        {"name": "执行层", "items": ["水肥设备", "无人机", "无人农机", "机器人"]},
        {"name": "商业层", "items": ["SaaS", "数据资产", "Agent市场", "模型市场"]},
    ],
    "loop": LOOP,
}
EDGE = {
    "gateway": "MQTT Gateway · 仿真接入状态",
    "cache": "本地缓存 · 模拟口径（非实测）",
    "edge_ai": "边缘推理节点 ×3 · 规划模拟",
    "protocol": "MQTT / HTTP / WebSocket",
    "topics": [
        "farm/{farmId}/device/{deviceId}/data",
        "farm/{farmId}/device/{deviceId}/cmd",
        "farm/{farmId}/agent/event",
    ],
}


def rows(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    with lock:
        cur = conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


def one(sql: str, params: tuple = ()) -> dict[str, Any] | None:
    data = rows(sql, params)
    return data[0] if data else None


def execute(sql: str, params: tuple = ()) -> int:
    with lock:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid


def audit_replay(request_id: str) -> dict[str, Any] | None:
    event = one("SELECT * FROM audit_events WHERE request_id = ?", (request_id,))
    if not event:
        return None
    try:
        payload = json.loads(event.get("after_json") or "{}")
    except (TypeError, json.JSONDecodeError):
        payload = {}
    return {**payload, "idempotent_replay": True, "request_id": request_id}


def record_audit(
    request_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    before: dict[str, Any] | None,
    after: dict[str, Any],
    reason: str = "",
) -> None:
    farm = one("SELECT id FROM farms LIMIT 1") or {}
    execute(
        """
        INSERT INTO audit_events(
            request_id, farm_id, actor, action, resource_type, resource_id,
            before_json, after_json, reason, simulated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (
            request_id,
            farm.get("id"),
            "demo-token-user",
            action,
            resource_type,
            str(resource_id),
            json.dumps(before or {}, ensure_ascii=False, sort_keys=True),
            json.dumps(after, ensure_ascii=False, sort_keys=True),
            reason[:500],
        ),
    )


def get_role() -> str:
    row = one("SELECT value FROM app_state WHERE key = 'role'")
    return (row or {}).get("value") or "farm"


def set_role(role: str) -> None:
    execute("INSERT OR REPLACE INTO app_state(key, value) VALUES ('role', ?)", (role,))


def parse_json_list(raw: Any) -> list[Any]:
    if isinstance(raw, list):
        return raw
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def enrich_land(item: dict[str, Any]) -> dict[str, Any]:
    if item.get("geojson") and isinstance(item["geojson"], str):
        item["geojson"] = json.loads(item["geojson"])
    return item


def land_rows() -> list[dict[str, Any]]:
    items = rows(
        """
        SELECT l.*, c.name AS crop_name, c.variety, c.stage, c.expected_yield
        FROM lands l
        LEFT JOIN crops c ON c.land_id = l.id
        ORDER BY l.code
        """
    )
    return [{
        **enrich_land(i),
        "simulated": True,
        "verified": False,
        "data_origin": "SIMULATOR_GENERATED" if SIMULATOR_ENABLED else "SEED_SNAPSHOT",
        "generated_at": simulator_health.get("last_generated_at"),
        "observed_at": None,
        "quality_code": "DEMO_UNVERIFIED",
    } for i in items]


def device_rows() -> list[dict[str, Any]]:
    items = rows("SELECT * FROM devices ORDER BY id")
    for d in items:
        d["x"] = d.get("pos_x")
        d["y"] = d.get("pos_y")
        d["simulated"] = True
        d["production_connected"] = False
        d["data_origin"] = "SIMULATOR_GENERATED" if SIMULATOR_ENABLED else "SEED_SNAPSHOT"
        d["generated_at"] = simulator_health.get("last_generated_at")
        d["observed_at"] = None
        d["quality_code"] = "DEMO_UNVERIFIED"
    return items


def agent_rows() -> list[dict[str, Any]]:
    items = rows("SELECT * FROM agents ORDER BY id")
    for item in items:
        item["memory"] = parse_json_list(item.get("memory"))
        item["tools"] = parse_json_list(item.get("tools"))
        item["recent"] = rows(
            "SELECT * FROM agent_tasks WHERE agent_id = ? ORDER BY id DESC LIMIT 5",
            (item["id"],),
        )
        item["simulated"] = True
        item["validated"] = False
    return items


def kpis() -> dict[str, Any]:
    farm = one("SELECT * FROM farms LIMIT 1") or {}
    lands = rows("SELECT * FROM lands")
    devices = rows("SELECT * FROM devices")
    agents = rows("SELECT id FROM agents")
    avg_health = round(sum(l["health_index"] for l in lands) / max(len(lands), 1), 1)
    yield_avg = one("SELECT AVG(expected_yield) AS y FROM crops") or {"y": 0}
    avg_risk = round(sum(l.get("pest_risk") or 0 for l in lands) / max(len(lands), 1))
    return {
        "area_mu": farm.get("area_mu", 0),
        "agents": len(agents),
        "devices_online": 0,
        "devices_sample": len(devices),
        "devices_total": len(devices),
        "water_saving": 20,
        "income_per_mu": 560,
        "pest_accuracy": 89.5,
        "labor_cut": 52,
        "land_health": avg_health,
        "predicted_yield": round(yield_avg["y"] or 0, 0),
        "pest_risk_avg": avg_risk,
        "edge_nodes": farm.get("edge_nodes") or 3,
        "metric_status": "demo_targets_unverified",
        "metric_note": "节水、识别、人工下降与增收均为目标场景/场景值，须以基线和实测台账核验",
    }


def build_priority(lands: list[dict[str, Any]]) -> dict[str, Any]:
    dry = sorted([l for l in lands if (l.get("moisture") or 0) < 25], key=lambda x: x["moisture"])
    risky = sorted([l for l in lands if (l.get("pest_risk") or 0) > 50], key=lambda x: -x["pest_risk"])
    if dry:
        land = dry[0]
        return {
            "level": "review",
            "decision": "NO_GO",
            "executable": False,
            "kicker": "证据待补 · Irrigation Agent",
            "title": f"{land['code']} {land['name']} 墒情模拟触发补灌复核",
            "desc": f"仿真含水率为 {land['moisture']}%，但采样深度、田间持水量、根层、ETc、有效降雨、灌溉效率和传感器 QC 不完整，禁止自动生成执行水量。",
            "cta": "核对水肥证据",
            "jump": "water",
            "land_code": land["code"],
            "required_evidence": ["采样深度与传感器 QC", "田间持水量", "根层深度", "ETc 与有效降雨", "灌溉效率"],
            "owner": "水肥管理员 + 农艺专家",
            "deadline": "补齐证据后复核",
            "stop_condition": "任一关键输入缺失或现场阀泵状态不可确认",
        }
    if risky:
        land = risky[0]
        return {
            "level": "review",
            "decision": "NO_GO",
            "executable": False,
            "kicker": "田间核查 · Vision Agent",
            "title": f"{land['code']} 风险模拟偏高，先复飞与定点调查",
            "desc": f"仿真风险指数为 {land['pest_risk']}；缺少有害生物种类、虫态/病级、样方密度和当地防治阈值，不得据此施药。",
            "cta": "调度无人机巡田",
            "jump": "robots",
            "land_code": land["code"],
            "required_evidence": ["复飞影像", "样方调查", "物种与发生期", "当地防治阈值", "药械标签与天气窗"],
            "owner": "植保员 + 农艺专家",
            "deadline": "当天完成现场核查",
            "stop_condition": "物种或阈值未确认",
        }
    return {
        "level": "ok",
        "decision": "REVIEW",
        "executable": False,
        "kicker": "模拟未触发高优规则 · Farm Master",
        "title": "当前仿真快照未发现高优触发",
        "desc": "这不等于生产现场安全或合规；执行前仍需核验数据时效、设备回执和人工巡田证据。",
        "cta": "查看数字孪生",
        "jump": "twin",
        "land_code": "全场",
    }


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ChatIn(StrictModel):
    question: str = Field(min_length=1, max_length=1000)


class VisionIn(StrictModel):
    crop: str = Field(default="棉花", min_length=1, max_length=32)
    symptom: str = Field(default="叶片发黄", min_length=1, max_length=300)


class AgentDispatchIn(StrictModel):
    agent_id: int
    goal: str = Field(min_length=1, max_length=500)


class OrchestrateIn(StrictModel):
    goal: str = Field(default="全场今日精准作业协同", min_length=1, max_length=500)


class DeviceControlIn(StrictModel):
    action: Literal["start", "stop", "open", "close", "patrol", "idle"]
    payload: dict[str, Any] = Field(default_factory=dict)


class DeviceRegisterIn(StrictModel):
    code: str | None = Field(default=None, min_length=1, max_length=32, pattern=r"^[A-Z0-9][A-Z0-9._-]{0,31}$")
    name: str | None = Field(default=None, min_length=1, max_length=80)
    device_type: Literal["sensor", "weather", "rain", "irrigation", "drone", "tractor", "robot", "sprayer", "gateway", "soil_scan", "par", "canopy", "leafwet", "crop_node", "pest", "yield"] = "sensor"
    location: str = Field(default="场部", min_length=1, max_length=40)
    vendor_id: str = Field(default="unassigned", min_length=1, max_length=32, pattern=r"^[a-z0-9][a-z0-9._-]{0,31}$")


class RobotDispatchIn(StrictModel):
    device: str = Field(default="UAV-001", min_length=1, max_length=32, pattern=r"^[A-Z0-9][A-Z0-9._-]{0,31}$")
    mission: str = Field(default="临时巡田任务", min_length=1, max_length=120)


class TaskIn(StrictModel):
    title: str = Field(min_length=1, max_length=80)
    task_type: str = Field(default="农事", min_length=1, max_length=24)
    land_code: str = Field(default="全场", min_length=1, max_length=32, pattern=r"^(全场|[A-Z0-9][A-Z0-9._-]{0,31})$")
    assignee: str = Field(default="Farm Master Agent", min_length=1, max_length=60)
    priority: Literal["高", "中", "低"] = "中"


class RoleIn(StrictModel):
    role: Literal["farm", "expert", "gov"] = "farm"


class AuditIn(StrictModel):
    approved: bool = True
    comment: str = Field(default="", max_length=500)
    reviewer_id: str = Field(min_length=2, max_length=40)
    qualification_scope: Literal["综合农艺复核", "棉花农艺与植保", "水肥管理", "农业机械安全", "收获与仓储"]
    credential_ref: str = Field(min_length=3, max_length=80)
    evidence_refs: list[str] = Field(min_length=1, max_length=20)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "running",
        "product": "AI Farm OS",
        "spec": "FINAL_SPEC v1.2",
        "data_mode": "demo",
        "contract_version": "2026-09-14",
        "business_api": "partial",
        "control_mode": "simulation_locked" if not ALLOW_DEMO_WRITES else "simulation_token_required",
        "simulator": str(simulator_health["status"]),
        "simulator_last_generated_at": simulator_health.get("last_generated_at"),
    }


@app.get("/api/role")
def role_get() -> dict[str, str]:
    return {"role": "farm", "note": "角色选择仅控制当前浏览器视图，不作为服务端授权身份"}


@app.post("/api/role")
def role_set(body: RoleIn) -> dict[str, str]:
    return {"role": body.role, "note": "仅返回视图偏好；服务端未写入全局角色"}


@app.get("/api/dashboard")
def dashboard() -> dict[str, Any]:
    farm = one("SELECT * FROM farms LIMIT 1") or {}
    farm["mqtt_online"] = bool(farm.get("mqtt_online", 1))
    lands = land_rows()
    devices = device_rows()
    weather = next((d for d in devices if d["device_type"] == "weather"), None)
    dry = next((l for l in lands if l["moisture"] < 25), None)
    risky = next((l for l in lands if (l.get("pest_risk") or 0) > 50), None)
    alerts = [
        {"level": "warn" if dry else "info", "text": f"{dry['code']} 墒情模拟触发证据复核，关键输入不足，当前为 NO_GO" if dry else "仿真快照未触发低墒规则，仍需现场核验"},
        {"level": "warn" if risky else "info", "text": f"{risky['code']} 风险模拟偏高，须复飞与样方调查后再判断" if risky else "仿真快照未触发高风险规则，仍需田间调查"},
        {"level": "info", "text": "病虫识别 89.5% 为目标场景值，未附本场验证集与评估报告"},
        {"level": "info", "text": "MQTT 与 Edge AI 为界面仿真状态，未连接生产遥测"},
        {"level": "info", "text": "节水 20% 与亩增收 560 元为目标场景/模拟，待基线和实测台账核验"},
    ]
    return {
        "data_meta": {
            "mode": "demo",
            "source": "SQLite seed + simulator" if SIMULATOR_ENABLED else "SQLite seed snapshot",
            "source_label": "后端仿真数据",
            "as_of": "2026-09-14",
            "generated_at": simulator_health.get("last_generated_at"),
            "observed_at": None,
            "quality_code": "DEMO_UNVERIFIED",
            "simulated": True,
        },
        "geometry_meta": {
            "coordinate_space": "screen_demo",
            "crs": None,
            "version": "demo-layout-v1",
            "survey_status": "未测绘，不得用于导航或面积结算",
        },
        "farm": farm,
        "role": "farm",
        "kpis": kpis(),
        "lands": lands,
        "devices": devices,
        "agents": agent_rows(),
        "tasks": rows("SELECT * FROM farm_tasks ORDER BY id DESC LIMIT 8"),
        "alerts": alerts,
        "priority": build_priority(lands),
        "weather": {
            "summary": weather["last_value"] if weather else "气温 --",
            "sync": "仿真缓存模拟",
            "mqtt": "MQTT 仿真状态" if farm.get("mqtt_online", 1) else "MQTT 仿真离线状态",
            "last_sync": "后端数据刷新",
            "link": "SQLite 仿真库 · 非生产实时接入",
        },
        "architecture": ARCHITECTURE,
        "edge": EDGE,
        "loop": LOOP,
    }


@app.get("/api/architecture")
def architecture() -> dict[str, Any]:
    farm = one("SELECT * FROM farms LIMIT 1") or {}
    return {**ARCHITECTURE, "edge": EDGE, "farm": farm}


@app.get("/api/twin")
def twin(layer: str = "moisture") -> dict[str, Any]:
    return {
        "data_meta": {
            "mode": "demo",
            "source": "SQLite seed snapshot",
            "source_label": "后端仿真数据",
            "as_of": "2026-09-14",
            "simulated": True,
        },
        "geometry_meta": {
            "coordinate_space": "screen_demo",
            "crs": None,
            "version": "demo-layout-v1",
            "survey_status": "未测绘，不得用于导航或面积结算",
        },
        "lands": land_rows(),
        "devices": device_rows(),
        "layer": layer,
        "layers": [
            {"id": "moisture", "name": "土壤墒情"},
            {"id": "crop", "name": "作物长势"},
            {"id": "risk", "name": "风险热力"},
            {"id": "device", "name": "设备位置"},
        ],
        "decisions": [
            "Irrigation Agent：B-01 关键水量输入缺失，NO_GO",
            "Vision Agent：先复飞和样方调查，不据风险分数直接施药",
            "Robot Agent：C-02 仅为仿真排程，等待人工与设备回执",
        ],
        "loop": LOOP,
    }


@app.get("/api/farms")
def farms() -> list[dict[str, Any]]:
    return [{**item, "simulated": True, "production_connected": False} for item in rows("SELECT * FROM farms")]


@app.get("/api/lands")
def lands_api() -> list[dict[str, Any]]:
    return land_rows()


@app.get("/api/agents")
def agents() -> list[dict[str, Any]]:
    return agent_rows()


@app.post("/api/agents/dispatch")
def dispatch_agent(body: AgentDispatchIn) -> dict[str, Any]:
    agent = one("SELECT * FROM agents WHERE id = ?", (body.agent_id,))
    if not agent:
        raise HTTPException(404, "智能体不存在")
    result = _agent_result(agent["name"], body.goal)
    memory = parse_json_list(agent.get("memory"))
    memory.insert(0, body.goal[:24])
    memory = memory[:5]
    tid = execute(
        "INSERT INTO agent_tasks(agent_id, goal, status, result) VALUES (?, ?, ?, ?)",
        (body.agent_id, body.goal, "待人工复核", result),
    )
    execute(
        "UPDATE agents SET status = ?, last_action = ?, memory = ? WHERE id = ?",
        ("分析草稿", result, json.dumps(memory, ensure_ascii=False), body.agent_id),
    )
    item = one("SELECT * FROM agent_tasks WHERE id = ?", (tid,)) or {}
    return {**item, "simulated": True, "executable": False, "message": "已生成规则分析草稿，等待人工复核；未触发任何设备动作"}


@app.post("/api/agents/orchestrate")
def orchestrate(body: OrchestrateIn) -> dict[str, Any]:
    chain_names = ["Farm Master Agent", "Irrigation Agent", "Vision Agent", "Robot Agent"]
    steps = []
    for name in chain_names:
        agent = one("SELECT * FROM agents WHERE name = ?", (name,))
        if not agent:
            continue
        result = _agent_result(name, body.goal)
        execute(
            "INSERT INTO agent_tasks(agent_id, goal, status, result) VALUES (?, ?, ?, ?)",
            (agent["id"], body.goal, "待人工复核", result),
        )
        memory = parse_json_list(agent.get("memory"))
        memory.insert(0, body.goal[:24])
        execute(
            "UPDATE agents SET status = ?, last_action = ?, memory = ? WHERE id = ?",
            ("分析草稿", result, json.dumps(memory[:5], ensure_ascii=False), agent["id"]),
        )
        steps.append({"agent": name, "result": result})
    farm = one("SELECT id FROM farms LIMIT 1")
    execute(
        """
        INSERT INTO farm_tasks(farm_id, title, task_type, land_code, assignee, status, scheduled_at, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            farm["id"],
            "协同任务：" + body.goal[:18],
            "协同",
            "全场",
            "Farm Master Agent",
            "待审核",
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            "高",
        ),
    )
    return {
        "goal": body.goal,
        "steps": steps,
        "summary": "Multi-Agent 仿真编排草稿已生成：总控→灌溉→视觉→机器人；等待人工审核，未执行设备动作",
        "simulated": True,
        "executable": False,
    }


@app.get("/api/devices")
def devices() -> list[dict[str, Any]]:
    return device_rows()


@app.post("/api/devices/register")
def register_device(body: DeviceRegisterIn, request: Request) -> dict[str, Any]:
    replay = audit_replay(request.state.request_id)
    if replay:
        return replay
    farm = one("SELECT id FROM farms LIMIT 1")
    code = body.code or f"DEV-{int(time.time()) % 100000}"
    if one("SELECT id FROM devices WHERE farm_id = ? AND code = ?", (farm["id"], code)):
        raise HTTPException(409, "设备编号已存在")
    if body.location not in ("场部", "场部泵房", "机库") and not one(
        "SELECT id FROM lands WHERE farm_id = ? AND code = ?", (farm["id"], body.location)
    ):
        raise HTTPException(422, "设备位置不是当前农场的有效地块")
    tid = execute(
        """
        INSERT INTO devices(farm_id, code, name, device_type, status, location, last_value, mqtt, pos_x, pos_y, battery, vendor_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            farm["id"],
            code,
            body.name or "新设备",
            body.device_type,
            "沙箱待联调",
            body.location,
            "模拟 · 已登记，等待沙箱模拟首包",
            f"farm/{farm['id']}/device/{code}/data",
            300,
            300,
            100,
            body.vendor_id,
        ),
    )
    item = one("SELECT * FROM devices WHERE id = ?", (tid,)) or {}
    result = {
        **item,
        "simulated": True,
        "production_connected": False,
        "request_id": request.state.request_id,
        "message": "设备仅登记到沙箱目录；未建立生产连接、凭据或控制权限",
    }
    record_audit(request.state.request_id, "sandbox_register", "device", str(tid), None, result, "sandbox catalog only")
    return result


@app.post("/api/devices/{device_id}/control")
def control_device(device_id: int, body: DeviceControlIn, request: Request) -> dict[str, Any]:
    replay = audit_replay(request.state.request_id)
    if replay:
        return replay
    device = one("SELECT * FROM devices WHERE id = ?", (device_id,))
    if not device:
        raise HTTPException(404, "设备不存在")
    command = {
        "id": None,
        "action": body.action,
        "status": "沙箱请求已登记",
        "requested_at": datetime.now().isoformat(timespec="seconds"),
        "simulated": True,
        "executable": False,
    }
    result = {
        "ok": True,
        "device": {**device, "x": device.get("pos_x"), "y": device.get("pos_y")},
        "command": command,
        "simulation_request_id": f"SIM-DEV-{request.state.request_id[:12]}",
        "executable": False,
        "request_id": request.state.request_id,
        "message": "仿真控制请求已登记；未连接真实设备，不代表动作已执行",
    }
    record_audit(request.state.request_id, body.action, "device", str(device_id), device, result, "demo control request")
    return result


@app.get("/api/robots")
def robots() -> dict[str, Any]:
    return {
        "missions": [{**item, "simulated": True, "executable": False} for item in rows("SELECT * FROM robot_missions ORDER BY id DESC")],
        "devices": [d for d in device_rows() if d["device_type"] in ("drone", "tractor", "robot")],
        "data_meta": {"mode": "demo", "simulated": True, "production_connected": False},
    }


@app.post("/api/robots/dispatch")
def robots_dispatch(body: RobotDispatchIn, request: Request) -> dict[str, Any]:
    replay = audit_replay(request.state.request_id)
    if replay:
        return replay
    farm = one("SELECT id FROM farms LIMIT 1") or {}
    device = one("SELECT * FROM devices WHERE code = ? AND farm_id = ?", (body.device, farm.get("id")))
    if not device or device.get("device_type") not in ("drone", "tractor", "robot", "sprayer"):
        raise HTTPException(404, "无人设备不存在、类型不兼容或不属于当前农场")
    tid = execute(
        "INSERT INTO robot_missions(device, mission, status, progress, eta) VALUES (?, ?, ?, ?, ?)",
        (body.device, body.mission, "待人工确认", 0, "等待机手/设备回执"),
    )
    robot_agent = one("SELECT id FROM agents WHERE name LIKE ?", ("%Robot%",))
    if robot_agent:
        execute(
            "UPDATE agents SET last_action = ? WHERE id = ?",
            (f"已登记 {body.device} 仿真任务：{body.mission}", robot_agent["id"]),
        )
    mission = one("SELECT * FROM robot_missions WHERE id = ?", (tid,)) or {}
    result = {
        **mission,
        "ok": True,
        "command_id": None,
        "simulation_job_id": f"SIM-ROBOT-{request.state.request_id[:12]}",
        "simulated": True,
        "executable": False,
        "request_id": request.state.request_id,
        "message": "仿真任务已入队，等待人工确认；未向真实设备下发",
    }
    record_audit(request.state.request_id, "dispatch", "robot_mission", str(tid), None, result, body.mission)
    return result


@app.get("/api/tasks")
def list_tasks(role: Literal["farm", "expert", "gov"] = Query(default="farm")) -> list[dict[str, Any]]:
    items = rows("SELECT * FROM farm_tasks ORDER BY id DESC")
    if role == "expert":
        items = [t for t in items if t["status"] == "待审核" or t["task_type"] in ("分析", "水肥")]
    elif role == "gov":
        items = [t for t in items if t.get("priority") == "高" or t["land_code"] == "全场"]
    return items


@app.post("/api/tasks")
def create_task(body: TaskIn, request: Request) -> dict[str, Any]:
    replay = audit_replay(request.state.request_id)
    if replay:
        return replay
    farm = one("SELECT id FROM farms LIMIT 1")
    if not farm:
        raise HTTPException(503, "仿真农场未初始化")
    if body.land_code != "全场" and not one(
        "SELECT id FROM lands WHERE farm_id = ? AND code = ?", (farm["id"], body.land_code)
    ):
        raise HTTPException(422, "地块不存在或不属于当前农场")
    tid = execute(
        """
        INSERT INTO farm_tasks(farm_id, title, task_type, land_code, assignee, status, scheduled_at, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            farm["id"],
            body.title,
            body.task_type,
            body.land_code,
            body.assignee,
            "待人工确认",
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            body.priority,
        ),
    )
    item = one("SELECT * FROM farm_tasks WHERE id = ?", (tid,)) or {}
    result = {
        **item,
        "simulated": True,
        "executable": False,
        "request_id": request.state.request_id,
        "message": "任务已登记为仿真草稿，等待人工确认；未向设备下发",
    }
    record_audit(request.state.request_id, "create_draft", "farm_task", str(tid), None, result, "demo task draft")
    return result


@app.post("/api/tasks/{task_id}/status")
def update_task(
    task_id: int,
    request: Request,
    status: Literal["待人工确认", "回放队列", "待审核", "已审核", "已驳回", "已制止"] = Query(...),
) -> dict[str, Any]:
    replay = audit_replay(request.state.request_id)
    if replay:
        return replay
    current = one("SELECT * FROM farm_tasks WHERE id = ?", (task_id,))
    if not current:
        raise HTTPException(404, "任务不存在")
    transitions = {
        "待人工确认": {"回放队列", "待审核", "已制止"},
        "回放队列": {"待审核", "已制止"},
        "待审核": {"已审核", "已驳回", "已制止"},
        "已审核": {"回放队列", "已制止"},
        "已驳回": {"待人工确认"},
        "已制止": {"待人工确认"},
        "待执行": {"待人工确认", "待审核", "已制止"},
        "进行中": {"待审核", "已制止"},
        "已完成": set(),
    }
    if status not in transitions.get(current["status"], set()):
        raise HTTPException(409, f"不允许从 {current['status']} 跳转到 {status}")
    execute("UPDATE farm_tasks SET status = ? WHERE id = ?", (status, task_id))
    item = one("SELECT * FROM farm_tasks WHERE id = ?", (task_id,)) or {}
    result = {**item, "simulated": True, "executable": False, "request_id": request.state.request_id}
    record_audit(request.state.request_id, "change_demo_state", "farm_task", str(task_id), current, result, status)
    return result


@app.post("/api/tasks/{task_id}/audit")
def audit_task(task_id: int, body: AuditIn, request: Request) -> dict[str, Any]:
    replay = audit_replay(request.state.request_id)
    if replay:
        return replay
    current = one("SELECT * FROM farm_tasks WHERE id = ?", (task_id,))
    if not current:
        raise HTTPException(404, "任务不存在")
    if current["status"] != "待审核":
        raise HTTPException(409, "仅待审核任务可执行审核")
    evidence_refs = [item.strip() for item in body.evidence_refs if item.strip()]
    if not evidence_refs or any(len(item) > 120 or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", item) for item in evidence_refs):
        raise HTTPException(422, "证据引用不能为空、不得含控制字符且每项不超过 120 字符")
    status = "已审核" if body.approved else "已驳回"
    execute("UPDATE farm_tasks SET status = ? WHERE id = ?", (status, task_id))
    item = one("SELECT * FROM farm_tasks WHERE id = ?", (task_id,))
    item["audit_comment"] = body.comment
    item.update({
        "audit_by": body.reviewer_id.strip(),
        "qualification_scope": body.qualification_scope,
        "credential_ref": body.credential_ref.strip(),
        "evidence_refs": evidence_refs,
        "identity_assurance": "DECLARED_UNVERIFIED",
        "gate_scope": "ADVISORY_ONLY",
        "simulated": True,
        "executable": False,
        "request_id": request.state.request_id,
        "message": "专家身份与资质当前仅作声明记录；初审不构成设备执行放行",
    })
    record_audit(request.state.request_id, "expert_review", "farm_task", str(task_id), current, item, body.comment)
    return item


@app.get("/api/irrigation")
def irrigation() -> dict[str, Any]:
    lands = rows("SELECT code, name, moisture, health_index, k FROM lands ORDER BY code")
    plans = rows("SELECT * FROM irrigation_plans ORDER BY id DESC LIMIT 10")
    suggestions = []
    for land in lands:
        suggestions.append(
            {
                "land_code": land["code"],
                "land_name": land["name"],
                "moisture": land["moisture"],
                "k": land.get("k"),
                "water_mm": None,
                "calculation_status": "NOT_CALCULATED",
                "fertilizer": "不生成肥料或剂量",
                "priority": "复核" if land["moisture"] < 25 else "观察",
                "decision": "NO_GO",
                "executable": False,
                "missing_inputs": ["field_capacity", "root_depth_cm", "effective_rainfall", "ETc", "irrigation_efficiency", "sensor_qc"],
                "reason": f"含水率 {land['moisture']}% 为未核验模拟；缺关键水量与质量证据，不判断是否灌溉，也不计算剂量",
            }
        )
    return {
        "plans": plans,
        "suggestions": suggestions,
        "saving_target": "目标场景：节水约 20%（待实测核验）",
        "protocol": "仿真处方计算 · 未连接真实阀泵",
        "data_meta": {"mode": "demo", "source": "SQLite seed snapshot", "as_of": "2026-09-14", "simulated": True},
    }


@app.post("/api/irrigation/apply")
def apply_irrigation(
    request: Request,
    land_code: str = Query(..., min_length=1, max_length=32, pattern=r"^[A-Z0-9][A-Z0-9._-]{0,31}$"),
) -> dict[str, Any]:
    replay = audit_replay(request.state.request_id)
    if replay:
        return replay
    farm = one("SELECT id FROM farms LIMIT 1") or {}
    land = one("SELECT * FROM lands WHERE code = ? AND farm_id = ?", (land_code, farm.get("id")))
    if not land:
        raise HTTPException(404, "地块不存在")
    water = None
    fert = "不生成肥料或剂量；等待完整证据与属地处方"
    execute(
        """
        INSERT INTO irrigation_plans(land_code, water_mm, fertilizer, reason, status, calculation_status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (land_code, water, fert, "仅登记证据缺口；缺少田间持水量、根层、ETc、有效降雨、效率与传感器 QC，禁止计算或执行", "NO_GO · 待补证据", "NOT_CALCULATED"),
    )
    result = {
        "ok": True,
        "decision": "NO_GO",
        "executable": False,
        "land_code": land_code,
        "water_mm": water,
        "calculation_status": "NOT_CALCULATED",
        "fertilizer": fert,
        "command_id": None,
        "request_id": request.state.request_id,
        "simulated": True,
        "missing_inputs": ["field_capacity", "root_depth_cm", "effective_rainfall", "ETc", "irrigation_efficiency", "sensor_qc"],
        "message": "已保存仿真处方，但关键农艺输入不完整，禁止自动执行；观测值未被改写",
    }
    record_audit(request.state.request_id, "create_no_go_prescription", "land", land_code, land, result, "missing agronomic inputs")
    return result


@app.post("/api/ai/chat")
def ai_chat(body: ChatIn) -> dict[str, Any]:
    return _chat_answer(body.question)


@app.post("/api/ai/vision")
def ai_vision(body: VisionIn) -> dict[str, Any]:
    symptom = body.symptom
    crop = body.crop
    if any(k in symptom for k in ("斑", "霉", "枯萎", "虫")):
        return {
            "crop": crop,
            "disease": "文字规则命中：斑/霉/枯萎/虫相关症状",
            "confidence": None,
            "level": "待核查",
            "advice": "先补充带时间、位置和比例尺的原始影像，再由植保员复飞与样方调查；未确认物种、发生期和阈值前禁止施药。",
            "model": "keyword-demo-rule v1",
            "mode": "demo",
            "executable": False,
            "limitations": "本接口仅接收文字症状，不是图像识别或确诊结果",
        }
    if any(k in symptom for k in ("黄", "落叶", "弱")):
        return {
            "crop": crop,
            "disease": "文字规则命中：黄化/落叶/弱势症状",
            "confidence": None,
            "level": "待核查",
            "advice": "先核对叶位、发生比例、土壤/叶片化验、盐分和根区水分；未确认原因前不生成施肥剂量。",
            "model": "keyword-demo-rule v1",
            "mode": "demo",
            "executable": False,
            "limitations": "同类症状可能来自养分、盐害、水分、病害或衰老，不能凭文字确诊",
        }
    return {
        "crop": crop,
        "disease": "文字规则未命中已配置症状",
        "confidence": None,
        "level": "未知",
        "advice": "规则未命中不代表无病害；请上传/采集原始影像并由植保员核查。",
        "model": "keyword-demo-rule v1",
        "mode": "demo",
        "executable": False,
        "limitations": "本接口仅做关键词仿真，不能排除病虫害",
    }


@app.get("/api/ai/yield")
def ai_yield() -> dict[str, Any]:
    crops = rows(
        """
        SELECT c.name, c.variety, c.stage, c.expected_yield, l.code, l.health_index, l.moisture, l.pest_risk
        FROM crops c JOIN lands l ON l.id = c.land_id
        """
    )
    items = []
    for c in crops:
        adj = (c["health_index"] - 80) * 1.2 - max(0, 25 - c["moisture"]) * 2 - (c.get("pest_risk") or 0) * 0.3
        pred = round(c["expected_yield"] + adj, 0)
        items.append(
            {
                "code": c["code"],
                "name": c["name"],
                "stage": c["stage"],
                "predicted": pred,
                "delta": round(pred - c["expected_yield"], 0),
                "risk": c.get("pest_risk") or 0,
            }
        )
    total = round(sum(i["predicted"] for i in items) / max(len(items), 1), 0)
    return {
        "avg_kg_per_mu": total,
        "items": items,
        "note": "仿真估算 · 种子数据的简化算式，不可用于生产承诺、保险或结算",
        "model": "yield-demo-formula v1",
        "mode": "demo",
        "validated": False,
    }


@app.get("/api/ai/rag")
def ai_rag() -> dict[str, Any]:
    return {"knowledge": rows("SELECT * FROM knowledge ORDER BY id"), "models": rows("SELECT * FROM models ORDER BY id")}


@app.get("/api/ai/risk")
def ai_risk() -> dict[str, Any]:
    lands = rows("SELECT code, name, moisture, pest_risk FROM lands ORDER BY code")
    return {
        "items": [
            {
                "code": l["code"],
                "name": l["name"],
                "pest_risk": l.get("pest_risk") or 0,
                "moisture_risk": "高" if l["moisture"] < 22 else ("中" if l["moisture"] < 28 else "低"),
                "advice": "优先复飞与样方调查"
                if (l.get("pest_risk") or 0) > 50
                else ("核验传感深度、QC 与补灌条件" if l["moisture"] < 25 else "继续田间监测"),
            }
            for l in lands
        ],
        "mode": "demo",
        "executable": False,
        "note": "风险分数是仿真数据；施药、灌溉或机具动作均需现场证据和人工审批",
    }


@app.get("/api/assets")
def assets() -> list[dict[str, Any]]:
    return rows("SELECT * FROM data_assets ORDER BY id")


@app.get("/api/models")
def models() -> list[dict[str, Any]]:
    return rows("SELECT * FROM models ORDER BY id")


@app.get("/api/knowledge")
def knowledge() -> list[dict[str, Any]]:
    return rows("SELECT * FROM knowledge ORDER BY id")


def _agent_result(name: str, goal: str) -> str:
    blob = name + goal
    if "Irrigation" in blob or "灌溉" in blob:
        return f"规则分析草稿：{goal}。B-01 触发水分复核；田间持水量、根层、ETc、有效降雨、灌溉效率和传感器 QC 不全，当前 NO_GO。"
    if "Vision" in blob or "病" in blob or "识别" in blob:
        return f"规则分析草稿：{goal}。B-01 风险模拟偏高，需复飞、样方调查和植保员确认；89.5% 仅为待验证目标值。"
    if "Robot" in blob or "无人" in blob or "调度" in blob:
        return f"仿真调度草稿：{goal}。UAV-001、TRACTOR-001 与 ROBOT-001 仅生成待人工确认队列，未向真实设备下发。"
    if "Yield" in blob or "产量" in blob:
        return f"仿真估算草稿：{goal}。约 520kg/亩来自种子数据简化公式，尚未完成本场模型验证，不用于结算。"
    if "Finance" in blob or "收益" in blob:
        return f"仿真收益目标：{goal}。亩均增收 400–600 元是待基线与实测成本收益台账核验的目标区间。"
    if "Crop" in blob or "作物" in blob:
        return f"仿真作物分析草稿：{goal}。请补充生育期、叶片/土壤化验、盐分和田间调查后再形成农艺处方。"
    if "Master" in blob or "总控" in blob or "协同" in blob or "编排" in blob:
        return f"仿真编排草稿：{goal}。Irrigation→Vision→Robot 仅写入待人工审核队列，未执行设备动作。"
    return f"{name} 已生成规则分析草稿：{goal}。等待人工复核，未执行设备动作。"


def _chat_answer(question: str) -> dict[str, Any]:
    q = question.strip()
    knowledge = rows("SELECT * FROM knowledge ORDER BY id")
    hits = [k for k in knowledge if any(x in k["title"] + k["snippet"] for x in q[:2])]
    if any(k in q for k in ("灌溉", "水", "墒")):
        answer = "B-01 的仿真墒情模拟触发复核，但缺少采样深度、田间持水量、根层、ETc、有效降雨、灌溉效率与传感器 QC，当前结论为 NO_GO。补齐证据并由水肥管理员与农艺专家复核后，才能确定是否灌溉及水量。"
    elif any(k in q for k in ("病", "虫", "叶片")):
        answer = "89.5% 是目标场景值，并非本场已验证准确率。出现黄斑、枯萎或虫害线索时，应先复飞、定点样方调查并确认物种、发生期和当地阈值；未确认前不应施药。"
    elif any(k in q for k in ("产量", "增收", "收益")):
        answer = "约 520kg/亩和亩均增收 400–600 元均为仿真估算/目标。正式结论需提供分地块测产、商品率、投入成本、历史基线、市场价格与模型验证报告，不能直接用于经营承诺或结算。"
    elif any(k in q for k in ("无人", "农机", "无人机", "调度")):
        answer = "当前显示的是无人机、拖拉机和田间机器人的回放队列，不代表设备实况。实际调度前须核对设备 ACK、机手/监护人、地块边界、道路与人员隔离、天气窗和机械状态。"
    elif any(k in q for k in ("架构", "云边", "边缘")):
        answer = "系统采用云-边-端架构：云端承载大模型与 Agent 平台，边缘 MQTT Gateway + Edge AI，端侧为传感器与无人设备。"
    else:
        answer = (
            "AI Farm OS 当前以本地规则和仿真数据展示土地、Agent、IoT 与设备闭环设计，未声明生产接入。"
            f"关于「{q}」，可从驾驶舱查看证据缺口，并由 Farm Master Agent 生成待人工复核的计划草稿。"
        )
    rag = hits[:2] if hits else knowledge[:2]
    return {
        "answer": answer,
        "rag": [{"title": r["title"], "source": r["source"], "snippet": r["snippet"]} for r in rag],
        "mode": "demo",
        "executable": False,
        "notice": "内容为仿真辅助，不替代当地农艺、植保、机务和安全责任人的现场判断",
    }


def _simulate_sensors() -> None:
    simulator_health["status"] = "running"
    while True:
        time.sleep(8)
        try:
            for land in rows("SELECT id, moisture, temp, pest_risk FROM lands"):
                moisture = max(12.0, min(42.0, land["moisture"] + random.uniform(-0.6, 0.5)))
                temp = round((land.get("temp") or 22) + random.uniform(-0.3, 0.3), 1)
                risk = max(5, min(90, int((land.get("pest_risk") or 20) + random.uniform(-2, 1.5))))
                execute(
                    "UPDATE lands SET moisture = ?, temp = ?, pest_risk = ? WHERE id = ?",
                    (round(moisture, 1), temp, risk, land["id"]),
                )
            for sensor in rows("SELECT id, location FROM devices WHERE device_type = 'sensor'"):
                land = one("SELECT moisture, temp FROM lands WHERE code = ?", (sensor["location"],))
                if land:
                    execute(
                        "UPDATE devices SET last_value = ? WHERE id = ?",
                        (f"仿真生成值 · 含水率 {land['moisture']}% / 地温 {land['temp']}℃", sensor["id"]),
                    )
            weather = one("SELECT id FROM devices WHERE device_type = 'weather'")
            if weather:
                execute(
                    "UPDATE devices SET last_value = ? WHERE id = ?",
                    (f"仿真生成值 · 气温 {round(22 + random.uniform(-2, 6), 1)}℃ / 风速 {round(1 + random.uniform(0, 3), 1)}m/s", weather["id"]),
                )
            for m in rows("SELECT id, progress, status FROM robot_missions WHERE status = '执行中'"):
                progress = min(100, (m.get("progress") or 0) + 3)
                status = "已完成" if progress >= 100 else "执行中"
                execute("UPDATE robot_missions SET progress = ?, status = ? WHERE id = ?", (progress, status, m["id"]))
            simulator_health["last_generated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        except Exception as exc:
            simulator_health["status"] = "degraded"
            simulator_health["last_error"] = type(exc).__name__
            continue


if SIMULATOR_ENABLED:
    threading.Thread(target=_simulate_sensors, daemon=True).start()

frontend = ROOT / "frontend"
if frontend.exists():
    app.mount("/assets", StaticFiles(directory=frontend / "assets"), name="assets")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(frontend / "index.html")
