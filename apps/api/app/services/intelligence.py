from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AIJob, Agent, AgentRun, DataSource, Device, Diagnosis, SensorReading
from app.schemas.intelligence import AIJobCreateSchema, AgentRunRequestSchema, DiagnosisCreateSchema
from app.schemas.common import DEFAULT_SIM_SOURCE
from app.serialize import row, zone_map

DEVICE_STATUS_LABELS = {
    "sim_online": "仿真在线",
    "sim_offline": "仿真离线",
    "unbound": "未接入",
    "manual": "人工抄表",
}


def list_devices(db: Session) -> list[dict]:
    zmap = zone_map(db)
    items = db.scalars(select(Device)).all()
    return [
        row(
            item,
            {
                "zone_code": zmap[item.zone_id].code if item.zone_id and item.zone_id in zmap else None,
                "live": False,
                "status_label": DEVICE_STATUS_LABELS.get(item.status, item.status),
            },
        )
        for item in items
    ]


def get_device(db: Session, device_id: str) -> dict:
    item = db.get(Device, device_id)
    if not item:
        raise HTTPException(status_code=404, detail="device_not_found")
    readings = db.scalars(select(SensorReading).where(SensorReading.device_id == device_id).order_by(SensorReading.recorded_at)).all()
    return {**row(item, {"live": False}), "readings": [row(reading) for reading in readings]}


def list_agents(db: Session) -> list[dict]:
    return [row(agent, {"controls_hardware": bool(agent.controls_hardware)}) for agent in db.scalars(select(Agent)).all()]


def get_agent(db: Session, agent_id: str) -> dict:
    item = db.get(Agent, agent_id)
    if not item:
        raise HTTPException(status_code=404, detail="agent_not_found")
    runs = db.scalars(select(AgentRun).where(AgentRun.agent_id == agent_id)).all()
    return {**row(item, {"controls_hardware": bool(item.controls_hardware)}), "runs": [row(run) for run in runs]}


def run_agent(db: Session, agent_id: str, payload: AgentRunRequestSchema) -> dict:
    agent = db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="agent_not_found")
    if agent.controls_hardware:
        raise HTTPException(status_code=409, detail="hardware_control_forbidden")

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    run = AgentRun(
        id=f"run-{uuid4().hex[:8]}",
        agent_id=agent.id,
        summary=payload.note or f"重跑 {agent.name}（仿真）",
        recommendation="本次为仿真重放，不连接机身或传感器。结论供人工拍板。",
        created_at=now,
        data_source=DEFAULT_SIM_SOURCE,
    )
    agent.last_run_at = now
    db.add(run)
    db.commit()
    db.refresh(run)
    return row(run)


def list_diagnoses(db: Session) -> list[dict]:
    zmap = zone_map(db)
    items = db.scalars(select(Diagnosis)).all()
    return [row(item, {"zone_code": zmap[item.zone_id].code if item.zone_id and item.zone_id in zmap else None}) for item in items]


def create_diagnosis(db: Session, payload: DiagnosisCreateSchema) -> dict:
    item = Diagnosis(
        id=f"diag-{uuid4().hex[:8]}",
        created_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        **payload.model_dump(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return row(item)


def list_jobs(db: Session) -> list[dict]:
    return [row(job, {"controls_hardware": bool(job.controls_hardware)}) for job in db.scalars(select(AIJob)).all()]


def create_job(db: Session, payload: AIJobCreateSchema) -> dict:
    item = AIJob(
        id=f"job-{uuid4().hex[:8]}",
        title=payload.title,
        job_type=payload.job_type,
        status="queued",
        input_summary=payload.input_summary,
        output_summary="已入队。后台不会触发设备动作。",
        created_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        data_source=DataSource.SIMULATION.value,
        controls_hardware=0,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return row(item)
