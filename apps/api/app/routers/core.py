from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Agent,
    AIJob,
    CollaborationNote,
    DataSource,
    Device,
    Diagnosis,
    Farm,
    IrrigationCircuit,
    Plant,
    Season,
    Task,
    Zone,
)
from app.serialize import parse_polygon, row, zone_map

router = APIRouter()

LAYER_KEYS = ("moisture", "crop", "risk", "device", "sensors")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-farm-os"}


@router.get("/meta")
def meta(db: Session = Depends(get_db)) -> dict:
    farm = db.scalar(select(Farm).limit(1))
    season = db.scalar(select(Season).where(Season.status == "active"))
    return {
        "name": "一级芯界 AI Farm OS",
        "line": "Unified Mainline",
        "farm": row(farm) if farm else None,
        "season": row(season) if season else None,
        "data_policy": {
            "allowed_sources": [s.value for s in DataSource],
            "rule": "传感、机器人与设备控制必须标注 REAL / SIMULATION / MANUAL。禁止伪造实时机身、GPS 或闭环控制。",
        },
        "layers": list(LAYER_KEYS),
    }


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict:
    farm = db.scalar(select(Farm).limit(1))
    season = db.scalar(select(Season).where(Season.status == "active"))
    zones = db.scalars(select(Zone)).all()
    plants = db.scalars(select(Plant)).all()
    tasks = db.scalars(select(Task)).all()
    circuits = db.scalars(select(IrrigationCircuit)).all()
    diagnoses = db.scalars(select(Diagnosis)).all()
    devices = db.scalars(select(Device)).all()
    zmap = {z.id: z for z in zones}

    open_tasks = [t for t in tasks if t.status in ("todo", "in_progress")]
    overdue = [t for t in open_tasks if t.due_at and t.due_at < "2026-09-13 09:00"]
    high_risk = [z for z in zones if z.risk_level == "high"]
    harvestable = [p for p in plants if p.growth_stage == "采收期"]
    need_water = [c for c in circuits if c.status == "needs_action"]
    sim_devices = [d for d in devices if d.data_source == DataSource.SIMULATION.value]
    unbound = [d for d in devices if d.status == "unbound"]

    decisions = []
    for circuit in need_water:
        zone = zmap.get(circuit.zone_id)
        decisions.append(
            {
                "id": f"dec-{circuit.id}",
                "kind": "irrigation",
                "urgency": "urgent",
                "title": f"{zone.code if zone else ''} 需要补灌决策",
                "detail": circuit.recommendation,
                "zone_id": circuit.zone_id,
                "href": "/irrigation",
                "action_label": "去水肥回路",
                "data_source": circuit.data_source,
            }
        )
    for item in diagnoses:
        if item.severity != "high":
            continue
        zone = zmap.get(item.zone_id or "")
        decisions.append(
            {
                "id": f"dec-{item.id}",
                "kind": "diagnosis",
                "urgency": "high",
                "title": item.title,
                "detail": item.conclusion,
                "zone_id": item.zone_id,
                "href": "/diagnosis",
                "action_label": "看诊断依据",
                "data_source": item.data_source,
            }
        )
    for plant in harvestable:
        zone = zmap.get(plant.zone_id)
        decisions.append(
            {
                "id": f"dec-{plant.id}",
                "kind": "harvest",
                "urgency": "high" if zone and zone.code == "B2" else "normal",
                "title": f"{zone.code if zone else ''} {plant.crop_name}进入采收窗口",
                "detail": plant.notes or "按订单与天气安排采收。",
                "zone_id": plant.zone_id,
                "href": "/plants",
                "action_label": "看作物台账",
                "data_source": plant.data_source,
            }
        )
    for task in overdue:
        decisions.append(
            {
                "id": f"dec-{task.id}",
                "kind": "task",
                "urgency": "high",
                "title": f"逾期任务：{task.title}",
                "detail": task.notes or task.due_at,
                "zone_id": task.zone_id,
                "href": "/tasks",
                "action_label": "打开任务",
                "data_source": task.data_source,
            }
        )

    return {
        "farm": row(farm) if farm else None,
        "season": row(season) if season else None,
        "generated_at": "2026-09-13 08:30",
        "decisions": decisions[:6],
        "kpis": [
            {"key": "zones", "label": "在田生产分区", "value": len([z for z in zones if z.zone_type in ("greenhouse", "open_field")])},
            {"key": "open_tasks", "label": "未关闭任务", "value": len(open_tasks)},
            {"key": "overdue", "label": "逾期任务", "value": len(overdue)},
            {"key": "high_risk", "label": "高风险分区", "value": len(high_risk)},
            {"key": "sim_devices", "label": "仿真传感点", "value": len(sim_devices)},
            {"key": "unbound", "label": "未接入设备", "value": len(unbound)},
        ],
        "risk_zones": [
            {
                "id": z.id,
                "code": z.code,
                "name": z.name,
                "risk_level": z.risk_level,
                "risk_note": z.risk_note,
                "moisture_pct": z.moisture_pct,
                "data_source": z.data_source,
            }
            for z in zones
            if z.risk_level in ("high", "medium")
        ],
        "open_tasks": [row(t, {"zone_code": zmap.get(t.zone_id).code if t.zone_id and zmap.get(t.zone_id) else None}) for t in open_tasks],
        "data_source_legend": [
            {"source": "REAL", "label": "真实接入", "note": "本演示场暂无 REAL 传感或机身。"},
            {"source": "SIMULATION", "label": "仿真", "note": "墒情曲线、顾问建议、诊断假设。"},
            {"source": "MANUAL", "label": "人工台账", "note": "作物、资产、任务、冷库抄表。"},
        ],
    }


@router.get("/twin")
def twin(layers: str = "moisture,crop,risk,device,sensors", db: Session = Depends(get_db)) -> dict:
    requested = [item.strip() for item in layers.split(",") if item.strip()]
    zones = db.scalars(select(Zone)).all()
    plants = db.scalars(select(Plant)).all()
    devices = db.scalars(select(Device)).all()
    plant_by_zone = {p.zone_id: p for p in plants}

    features = []
    for zone in zones:
        plant = plant_by_zone.get(zone.id)
        features.append(
            {
                "id": zone.id,
                "code": zone.code,
                "name": zone.name,
                "zone_type": zone.zone_type,
                "polygon": parse_polygon(zone.polygon),
                "moisture_pct": zone.moisture_pct,
                "risk_level": zone.risk_level,
                "risk_note": zone.risk_note,
                "crop_name": plant.crop_name if plant else None,
                "variety": plant.variety if plant else None,
                "growth_stage": plant.growth_stage if plant else None,
                "data_source": zone.data_source,
            }
        )

    payload: dict = {
        "layers": requested,
        "available_layers": [
            {"id": "moisture", "label": "墒情层", "data_source": DataSource.SIMULATION.value},
            {"id": "crop", "label": "作物层", "data_source": DataSource.MANUAL.value},
            {"id": "risk", "label": "风险层", "data_source": DataSource.SIMULATION.value},
            {"id": "device", "label": "设备层", "data_source": DataSource.SIMULATION.value},
            {"id": "sensors", "label": "传感器层", "data_source": DataSource.SIMULATION.value},
        ],
        "zones": features,
        "disclaimer": "地图坐标为场内示意网格，不是测绘成果。传感值为仿真回放或人工抄表。",
    }
    if "device" in requested or "sensors" in requested:
        payload["devices"] = [
            {
                "id": d.id,
                "name": d.name,
                "device_type": d.device_type,
                "status": d.status,
                "metric": d.metric,
                "last_value": d.last_value,
                "unit": d.unit,
                "map_x": d.map_x,
                "map_y": d.map_y,
                "data_source": d.data_source,
                "binding_note": d.binding_note,
            }
            for d in devices
            if d.map_x is not None
        ]
    return payload


@router.get("/twin/zones/{zone_id}")
def twin_zone(zone_id: str, db: Session = Depends(get_db)) -> dict:
    zone = db.get(Zone, zone_id)
    if not zone:
        return {"error": "zone_not_found"}
    plant = db.scalar(select(Plant).where(Plant.zone_id == zone_id))
    devices = db.scalars(select(Device).where(Device.zone_id == zone_id)).all()
    circuit = db.scalar(select(IrrigationCircuit).where(IrrigationCircuit.zone_id == zone_id))
    return {
        "zone": {**row(zone), "polygon": parse_polygon(zone.polygon)},
        "plant": row(plant) if plant else None,
        "irrigation": row(circuit) if circuit else None,
        "devices": [row(d) for d in devices],
    }


@router.get("/workbench")
def workbench(db: Session = Depends(get_db)) -> dict:
    zmap = zone_map(db)
    tasks = db.scalars(select(Task).where(Task.status != "done")).all()
    circuits = db.scalars(select(IrrigationCircuit).where(IrrigationCircuit.status == "needs_action")).all()
    notes = db.scalars(select(CollaborationNote)).all()
    return {
        "title": "今日工作台",
        "focus_date": "2026-09-13",
        "blocks": [
            {
                "id": "water",
                "title": "水肥待拍板",
                "items": [row(c, {"zone_code": zmap[c.zone_id].code if c.zone_id in zmap else None}) for c in circuits],
            },
            {
                "id": "tasks",
                "title": "执行队列",
                "items": [row(t, {"zone_code": zmap[t.zone_id].code if t.zone_id and t.zone_id in zmap else None}) for t in tasks],
            },
            {
                "id": "notes",
                "title": "协同留言",
                "items": [row(n) for n in notes],
            },
        ],
    }


@router.get("/seasons")
def seasons(db: Session = Depends(get_db)) -> list[dict]:
    return [row(s) for s in db.scalars(select(Season).order_by(Season.start_date.desc())).all()]


@router.get("/architecture")
def architecture(db: Session = Depends(get_db)) -> dict:
    farm = db.scalar(select(Farm).limit(1))
    return {
        "product": "一级芯界 AI Farm OS Unified Mainline",
        "farm": farm.name if farm else "",
        "stack": {
            "web": "Vite + React + TypeScript",
            "api": "FastAPI",
            "db": "SQLite（DATABASE_URL 未设置时）",
        },
        "modules": {
            "P0": ["dashboard", "twin", "assets", "plants", "irrigation", "tasks"],
            "P1": ["devices", "agents", "diagnosis", "ai-center"],
            "P2": ["robots", "fleet", "postharvest"],
            "P3": ["vendors", "collaboration", "architecture"],
        },
        "boundaries": [
            "没有 REAL 传感器接入，墒情/气象曲线为 SIMULATION。",
            "机器人模块为 stub：无位姿、无遥控、无视频。",
            "AI 智能体只产出建议，controls_hardware 恒为 false。",
            "车队位置来自出车单 MANUAL，不是 GPS 轨迹。",
            "阀门/泵不可远程闭环。",
        ],
        "data_sources": [s.value for s in DataSource],
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
    }
