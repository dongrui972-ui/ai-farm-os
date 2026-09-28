from __future__ import annotations

from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Asset, IrrigationCircuit, Plant, Task, Zone
from app.schemas.production import TaskCreateSchema, TaskPatchSchema
from app.serialize import row, zone_code, zone_map
from app.services.agronomy import advise_zone
from app.services.clock import DEMO_NOW_LABEL


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


def _plant_payload(item: Plant, zones: dict[str, Zone], circuits: dict[str, IrrigationCircuit] | None = None) -> dict:
    zone = zones.get(item.zone_id)
    circuit = (circuits or {}).get(item.zone_id)
    advice = advise_zone(zone, item, circuit) if zone else {"applicable": False, "data_source": "SIMULATION"}
    return row(
        item,
        {
            "zone_code": zone.code if zone else None,
            "zone_name": zone.name if zone else None,
            "moisture_pct": zone.moisture_pct if zone else None,
            "risk_level": zone.risk_level if zone else None,
            "agronomy": advice,
        },
    )


def list_plants(db: Session) -> list[dict]:
    zmap = zone_map(db)
    circuits = {item.zone_id: item for item in db.scalars(select(IrrigationCircuit)).all()}
    items = db.scalars(select(Plant)).all()
    return [_plant_payload(item, zmap, circuits) for item in items]


def get_plant(db: Session, plant_id: str) -> dict:
    item = db.get(Plant, plant_id)
    if not item:
        raise HTTPException(status_code=404, detail="plant_not_found")
    circuits = {row.zone_id: row for row in db.scalars(select(IrrigationCircuit)).all()}
    return _plant_payload(item, zone_map(db), circuits)


def _circuit_payload(item: IrrigationCircuit, zones: dict[str, Zone], plants: dict[str, Plant]) -> dict:
    zone = zones.get(item.zone_id)
    plant = plants.get(item.zone_id)
    advice = advise_zone(zone, plant, item) if zone else {"applicable": False, "data_source": "SIMULATION", "recommended_mm": 0}
    return row(
        item,
        {
            "zone_code": zone.code if zone else None,
            "zone_name": zone.name if zone else None,
            "moisture_pct": zone.moisture_pct if zone else None,
            "control_enabled": False,
            "control_note": "回路可记录建议与任务，不可远程开阀或启泵。",
            "recommendation": advice.get("summary") or item.recommendation,
            "recommendation_mm": advice.get("recommended_mm") if advice.get("applicable") else item.recommendation_mm,
            "agronomy": advice,
            "accept_allowed": bool(
                item.status != "accepted"
                and advice.get("action") in {"irrigate", "shorten", "hold_for_harvest"}
            ),
        },
    )


def list_irrigation(db: Session) -> list[dict]:
    zmap = zone_map(db)
    plants = {item.zone_id: item for item in db.scalars(select(Plant)).all()}
    items = db.scalars(select(IrrigationCircuit)).all()
    rows = [_circuit_payload(item, zmap, plants) for item in items]
    rank = {"irrigate": 0, "shorten": 1, "hold_for_harvest": 2, "watch": 3, "hold": 4}
    rows.sort(key=lambda item: rank.get((item.get("agronomy") or {}).get("action"), 9))
    return rows


def get_irrigation(db: Session, circuit_id: str) -> dict:
    item = db.get(IrrigationCircuit, circuit_id)
    if not item:
        raise HTTPException(status_code=404, detail="circuit_not_found")
    plants = {p.zone_id: p for p in db.scalars(select(Plant)).all()}
    return _circuit_payload(item, zone_map(db), plants)


def accept_irrigation_recommendation(db: Session, circuit_id: str, assignee: str) -> dict:
    circuit = db.get(IrrigationCircuit, circuit_id)
    if not circuit:
        raise HTTPException(status_code=404, detail="circuit_not_found")
    zone = db.get(Zone, circuit.zone_id)
    plant = db.scalar(select(Plant).where(Plant.zone_id == circuit.zone_id))
    advice = advise_zone(zone, plant, circuit) if zone else {}
    notes = advice.get("summary") or circuit.recommendation
    if not notes:
        raise HTTPException(status_code=400, detail="no_recommendation")
    reasons = advice.get("reasons") or []
    if reasons:
        notes = notes + "\n" + "\n".join(f"- {line}" for line in reasons)
    notes = notes + "\n未向阀门下发指令，需现场确认水压与阀位后人工执行。"

    task = Task(
        id=f"task-{uuid4().hex[:8]}",
        title=f"执行灌溉建议：{circuit.name}",
        task_type="irrigation",
        zone_id=circuit.zone_id,
        assignee=assignee,
        priority="high" if advice.get("action") == "irrigate" else "normal",
        status="todo",
        due_at=f"{DEMO_NOW_LABEL[:10]} 16:00",
        origin="ai_suggested",
        notes=notes,
        data_source=circuit.data_source,
    )
    db.add(task)
    circuit.status = "accepted"
    if advice.get("summary"):
        circuit.recommendation = advice["summary"]
    if advice.get("recommended_mm") is not None:
        circuit.recommendation_mm = float(advice["recommended_mm"])
    db.commit()
    db.refresh(task)
    return {
        "task": row(task),
        "circuit": row(circuit),
        "agronomy": advice,
        "note": "已生成人工执行任务，未向阀门下发指令。",
    }


def list_tasks(db: Session) -> list[dict]:
    zmap = zone_map(db)
    items = db.scalars(select(Task)).all()
    return [row(item, {"zone_code": zone_code(zmap, item.zone_id)}) for item in items]


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
