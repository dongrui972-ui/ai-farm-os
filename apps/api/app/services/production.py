from __future__ import annotations

from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Asset, IrrigationCircuit, Plant, Task
from app.schemas.production import TaskCreateSchema, TaskPatchSchema
from app.serialize import row, zone_map


def list_assets(db: Session) -> list[dict]:
    zmap = zone_map(db)
    items = db.scalars(select(Asset)).all()
    return [
        row(
            item,
            {
                "zone_code": zmap[item.zone_id].code if item.zone_id and item.zone_id in zmap else None,
                "zone_name": zmap[item.zone_id].name if item.zone_id and item.zone_id in zmap else None,
            },
        )
        for item in items
    ]


def get_asset(db: Session, asset_id: str) -> dict:
    item = db.get(Asset, asset_id)
    if not item:
        raise HTTPException(status_code=404, detail="asset_not_found")
    return row(item)


def list_plants(db: Session) -> list[dict]:
    zmap = zone_map(db)
    items = db.scalars(select(Plant)).all()
    return [
        row(
            item,
            {
                "zone_code": zmap[item.zone_id].code if item.zone_id in zmap else None,
                "zone_name": zmap[item.zone_id].name if item.zone_id in zmap else None,
                "moisture_pct": zmap[item.zone_id].moisture_pct if item.zone_id in zmap else None,
                "risk_level": zmap[item.zone_id].risk_level if item.zone_id in zmap else None,
            },
        )
        for item in items
    ]


def get_plant(db: Session, plant_id: str) -> dict:
    item = db.get(Plant, plant_id)
    if not item:
        raise HTTPException(status_code=404, detail="plant_not_found")
    return row(item)


def list_irrigation(db: Session) -> list[dict]:
    zmap = zone_map(db)
    items = db.scalars(select(IrrigationCircuit)).all()
    return [
        row(
            item,
            {
                "zone_code": zmap[item.zone_id].code if item.zone_id in zmap else None,
                "zone_name": zmap[item.zone_id].name if item.zone_id in zmap else None,
                "moisture_pct": zmap[item.zone_id].moisture_pct if item.zone_id in zmap else None,
                "control_enabled": False,
                "control_note": "回路可记录建议与任务，不可远程开阀或启泵。",
            },
        )
        for item in items
    ]


def get_irrigation(db: Session, circuit_id: str) -> dict:
    item = db.get(IrrigationCircuit, circuit_id)
    if not item:
        raise HTTPException(status_code=404, detail="circuit_not_found")
    return row(item, {"control_enabled": False})


def accept_irrigation_recommendation(db: Session, circuit_id: str, assignee: str) -> dict:
    circuit = db.get(IrrigationCircuit, circuit_id)
    if not circuit:
        raise HTTPException(status_code=404, detail="circuit_not_found")
    if not circuit.recommendation:
        raise HTTPException(status_code=400, detail="no_recommendation")

    task = Task(
        id=f"task-{uuid4().hex[:8]}",
        title=f"执行灌溉建议：{circuit.name}",
        task_type="irrigation",
        zone_id=circuit.zone_id,
        assignee=assignee,
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
    return {
        "task": row(task),
        "circuit": row(circuit),
        "note": "已生成人工执行任务，未向阀门下发指令。",
    }


def list_tasks(db: Session) -> list[dict]:
    zmap = zone_map(db)
    items = db.scalars(select(Task)).all()
    return [row(item, {"zone_code": zmap[item.zone_id].code if item.zone_id and item.zone_id in zmap else None}) for item in items]


def create_task(db: Session, payload: TaskCreateSchema) -> dict:
    task = Task(id=f"task-{uuid4().hex[:8]}", **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return row(task)


def patch_task(db: Session, task_id: str, payload: TaskPatchSchema) -> dict:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task_not_found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return row(task)
