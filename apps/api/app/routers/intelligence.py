from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AIJob, Agent, AgentRun, DataSource, Device, Diagnosis, SensorReading
from app.serialize import row, zone_map

router = APIRouter()


class DiagnosisCreate(BaseModel):
    zone_id: str | None = None
    plant_id: str | None = None
    title: str
    symptom: str
    conclusion: str = "待农技员确认"
    confidence: float = 0
    severity: str = "medium"
    data_source: str = "MANUAL"


class AgentRunRequest(BaseModel):
    note: str = ""


class AIJobCreate(BaseModel):
    title: str
    job_type: str = "briefing"
    input_summary: str = ""


@router.get("/devices")
def list_devices(db: Session = Depends(get_db)) -> list[dict]:
    zmap = zone_map(db)
    items = db.scalars(select(Device)).all()
    return [
        row(
            d,
            {
                "zone_code": zmap[d.zone_id].code if d.zone_id and d.zone_id in zmap else None,
                "live": False,
                "status_label": {
                    "sim_online": "仿真在线",
                    "sim_offline": "仿真离线",
                    "unbound": "未接入",
                    "manual": "人工抄表",
                }.get(d.status, d.status),
            },
        )
        for d in items
    ]


@router.get("/devices/{device_id}")
def get_device(device_id: str, db: Session = Depends(get_db)) -> dict:
    item = db.get(Device, device_id)
    if not item:
        raise HTTPException(404, "device_not_found")
    readings = db.scalars(
        select(SensorReading).where(SensorReading.device_id == device_id).order_by(SensorReading.recorded_at)
    ).all()
    return {
        **row(item, {"live": False}),
        "readings": [row(r) for r in readings],
    }


@router.get("/agents")
def list_agents(db: Session = Depends(get_db)) -> list[dict]:
    items = db.scalars(select(Agent)).all()
    return [row(a, {"controls_hardware": bool(a.controls_hardware)}) for a in items]


@router.get("/agents/{agent_id}")
def get_agent(agent_id: str, db: Session = Depends(get_db)) -> dict:
    item = db.get(Agent, agent_id)
    if not item:
        raise HTTPException(404, "agent_not_found")
    runs = db.scalars(select(AgentRun).where(AgentRun.agent_id == agent_id)).all()
    return {**row(item, {"controls_hardware": bool(item.controls_hardware)}), "runs": [row(r) for r in runs]}


@router.post("/agents/{agent_id}/run")
def run_agent(agent_id: str, body: AgentRunRequest, db: Session = Depends(get_db)) -> dict:
    agent = db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, "agent_not_found")
    if agent.controls_hardware:
        raise HTTPException(409, "hardware_control_forbidden")
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    run = AgentRun(
        id=f"run-{uuid4().hex[:8]}",
        agent_id=agent.id,
        summary=body.note or f"重跑 {agent.name}（仿真）",
        recommendation="本次为仿真重放，不连接机身或传感器。结论供人工拍板。",
        created_at=now,
        data_source=DataSource.SIMULATION.value,
    )
    agent.last_run_at = now
    db.add(run)
    db.commit()
    db.refresh(run)
    return row(run)


@router.get("/diagnoses")
def list_diagnoses(db: Session = Depends(get_db)) -> list[dict]:
    zmap = zone_map(db)
    items = db.scalars(select(Diagnosis)).all()
    return [
        row(d, {"zone_code": zmap[d.zone_id].code if d.zone_id and d.zone_id in zmap else None})
        for d in items
    ]


@router.post("/diagnoses")
def create_diagnosis(body: DiagnosisCreate, db: Session = Depends(get_db)) -> dict:
    item = Diagnosis(
        id=f"diag-{uuid4().hex[:8]}",
        created_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        **body.model_dump(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return row(item)


@router.get("/ai-center/jobs")
def list_jobs(db: Session = Depends(get_db)) -> list[dict]:
    return [row(j, {"controls_hardware": bool(j.controls_hardware)}) for j in db.scalars(select(AIJob)).all()]


@router.post("/ai-center/jobs")
def create_job(body: AIJobCreate, db: Session = Depends(get_db)) -> dict:
    item = AIJob(
        id=f"job-{uuid4().hex[:8]}",
        title=body.title,
        job_type=body.job_type,
        status="queued",
        input_summary=body.input_summary,
        output_summary="已入队。后台不会触发设备动作。",
        created_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        data_source=DataSource.SIMULATION.value,
        controls_hardware=0,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return row(item)
