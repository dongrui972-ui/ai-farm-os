from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Asset, IrrigationCircuit, Plant, Task
from app.serialize import row, zone_map

router = APIRouter()


class TaskCreate(BaseModel):
    title: str
    task_type: str = "general"
    zone_id: str | None = None
    assignee: str = ""
    priority: str = "normal"
    due_at: str | None = None
    notes: str = ""
    origin: str = "manual"
    data_source: str = "MANUAL"


class TaskPatch(BaseModel):
    status: str | None = None
    assignee: str | None = None
    notes: str | None = None
    priority: str | None = None


class AcceptIrrigation(BaseModel):
    assignee: str = Field(default="张永强")


@router.get("/assets")
def list_assets(db: Session = Depends(get_db)) -> list[dict]:
    zmap = zone_map(db)
    items = db.scalars(select(Asset)).all()
    return [
        row(
            a,
            {
                "zone_code": zmap[a.zone_id].code if a.zone_id and a.zone_id in zmap else None,
                "zone_name": zmap[a.zone_id].name if a.zone_id and a.zone_id in zmap else None,
            },
        )
        for a in items
    ]


@router.get("/assets/{asset_id}")
def get_asset(asset_id: str, db: Session = Depends(get_db)) -> dict:
    item = db.get(Asset, asset_id)
    if not item:
        raise HTTPException(404, "asset_not_found")
    return row(item)


@router.get("/plants")
def list_plants(db: Session = Depends(get_db)) -> list[dict]:
    zmap = zone_map(db)
    items = db.scalars(select(Plant)).all()
    return [
        row(
            p,
            {
                "zone_code": zmap[p.zone_id].code if p.zone_id in zmap else None,
                "zone_name": zmap[p.zone_id].name if p.zone_id in zmap else None,
                "moisture_pct": zmap[p.zone_id].moisture_pct if p.zone_id in zmap else None,
                "risk_level": zmap[p.zone_id].risk_level if p.zone_id in zmap else None,
            },
        )
        for p in items
    ]


@router.get("/plants/{plant_id}")
def get_plant(plant_id: str, db: Session = Depends(get_db)) -> dict:
    item = db.get(Plant, plant_id)
    if not item:
        raise HTTPException(404, "plant_not_found")
    return row(item)


@router.get("/irrigation")
def list_irrigation(db: Session = Depends(get_db)) -> list[dict]:
    zmap = zone_map(db)
    items = db.scalars(select(IrrigationCircuit)).all()
    return [
        row(
            c,
            {
                "zone_code": zmap[c.zone_id].code if c.zone_id in zmap else None,
                "zone_name": zmap[c.zone_id].name if c.zone_id in zmap else None,
                "moisture_pct": zmap[c.zone_id].moisture_pct if c.zone_id in zmap else None,
                "control_enabled": False,
                "control_note": "回路可记录建议与任务，不可远程开阀或启泵。",
            },
        )
        for c in items
    ]


@router.get("/irrigation/{circuit_id}")
def get_irrigation(circuit_id: str, db: Session = Depends(get_db)) -> dict:
    item = db.get(IrrigationCircuit, circuit_id)
    if not item:
        raise HTTPException(404, "circuit_not_found")
    return row(item, {"control_enabled": False})


@router.post("/irrigation/{circuit_id}/accept-recommendation")
def accept_irrigation(circuit_id: str, body: AcceptIrrigation, db: Session = Depends(get_db)) -> dict:
    circuit = db.get(IrrigationCircuit, circuit_id)
    if not circuit:
        raise HTTPException(404, "circuit_not_found")
    if not circuit.recommendation:
        raise HTTPException(400, "no_recommendation")
    task = Task(
        id=f"task-{uuid4().hex[:8]}",
        title=f"执行灌溉建议：{circuit.name}",
        task_type="irrigation",
        zone_id=circuit.zone_id,
        assignee=body.assignee,
        priority="high",
        status="todo",
        due_at="2026-09-13 16:00",
        origin="ai_suggested",
        notes=circuit.recommendation,
        data_source=circuit.data_source,
    )
    db.add(task)
    circuit.status = "accepted"
    db.commit()
    db.refresh(task)
    return {"task": row(task), "circuit": row(circuit), "note": "已生成人工执行任务，未向阀门下发指令。"}


@router.get("/tasks")
def list_tasks(db: Session = Depends(get_db)) -> list[dict]:
    zmap = zone_map(db)
    items = db.scalars(select(Task)).all()
    return [
        row(t, {"zone_code": zmap[t.zone_id].code if t.zone_id and t.zone_id in zmap else None})
        for t in items
    ]


@router.post("/tasks")
def create_task(body: TaskCreate, db: Session = Depends(get_db)) -> dict:
    task = Task(id=f"task-{uuid4().hex[:8]}", **body.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return row(task)


@router.patch("/tasks/{task_id}")
def patch_task(task_id: str, body: TaskPatch, db: Session = Depends(get_db)) -> dict:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "task_not_found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return row(task)
