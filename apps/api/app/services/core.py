from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
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
from app.services.constants import DATA_SOURCE_LEGEND, HONESTY_BOUNDARIES, TWIN_AVAILABLE_LAYERS, TWIN_LAYER_KEYS


def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-farm-os"}


def meta(db: Session) -> dict:
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
        "layers": list(TWIN_LAYER_KEYS),
    }


def dashboard(db: Session) -> dict:
    farm = db.scalar(select(Farm).limit(1))
    season = db.scalar(select(Season).where(Season.status == "active"))
    zones = db.scalars(select(Zone)).all()
    plants = db.scalars(select(Plant)).all()
    tasks = db.scalars(select(Task)).all()
    circuits = db.scalars(select(IrrigationCircuit)).all()
    diagnoses = db.scalars(select(Diagnosis)).all()
    devices = db.scalars(select(Device)).all()
    zmap = {z.id: z for z in zones}

    open_tasks = [task for task in tasks if task.status in ("todo", "in_progress")]
    overdue_tasks = [task for task in open_tasks if task.due_at and task.due_at < "2026-09-13 09:00"]
    high_risk_zones = [zone for zone in zones if zone.risk_level == "high"]
    harvestable_plants = [plant for plant in plants if plant.growth_stage == "采收期"]
    irrigation_actions = [circuit for circuit in circuits if circuit.status == "needs_action"]
    simulation_devices = [device for device in devices if device.data_source == DataSource.SIMULATION.value]
    unbound_devices = [device for device in devices if device.status == "unbound"]

    decisions: list[dict] = []
    for circuit in irrigation_actions:
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

    for diagnosis in diagnoses:
        if diagnosis.severity != "high":
            continue
        decisions.append(
            {
                "id": f"dec-{diagnosis.id}",
                "kind": "diagnosis",
                "urgency": "high",
                "title": diagnosis.title,
                "detail": diagnosis.conclusion,
                "zone_id": diagnosis.zone_id,
                "href": "/diagnosis",
                "action_label": "看诊断依据",
                "data_source": diagnosis.data_source,
            }
        )

    for plant in harvestable_plants:
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

    for task in overdue_tasks:
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
            {"key": "overdue", "label": "逾期任务", "value": len(overdue_tasks)},
            {"key": "high_risk", "label": "高风险分区", "value": len(high_risk_zones)},
            {"key": "sim_devices", "label": "仿真传感点", "value": len(simulation_devices)},
            {"key": "unbound", "label": "未接入设备", "value": len(unbound_devices)},
        ],
        "risk_zones": [
            {
                "id": zone.id,
                "code": zone.code,
                "name": zone.name,
                "risk_level": zone.risk_level,
                "risk_note": zone.risk_note,
                "moisture_pct": zone.moisture_pct,
                "data_source": zone.data_source,
            }
            for zone in zones
            if zone.risk_level in ("high", "medium")
        ],
        "open_tasks": [
            row(task, {"zone_code": zmap.get(task.zone_id).code if task.zone_id and zmap.get(task.zone_id) else None})
            for task in open_tasks
        ],
        "data_source_legend": DATA_SOURCE_LEGEND,
    }


def twin(db: Session, layers: str = "moisture,crop,risk,device,sensors") -> dict:
    requested_layers = [item.strip() for item in layers.split(",") if item.strip()]
    zones = db.scalars(select(Zone)).all()
    plants = db.scalars(select(Plant)).all()
    devices = db.scalars(select(Device)).all()
    plant_by_zone = {plant.zone_id: plant for plant in plants}

    zone_features: list[dict] = []
    for zone in zones:
        plant = plant_by_zone.get(zone.id)
        zone_features.append(
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
        "layers": requested_layers,
        "available_layers": TWIN_AVAILABLE_LAYERS,
        "zones": zone_features,
        "disclaimer": "地图坐标为场内示意网格，不是测绘成果。传感值为仿真回放或人工抄表。",
    }
    if "device" in requested_layers or "sensors" in requested_layers:
        payload["devices"] = [
            {
                "id": device.id,
                "name": device.name,
                "device_type": device.device_type,
                "status": device.status,
                "metric": device.metric,
                "last_value": device.last_value,
                "unit": device.unit,
                "map_x": device.map_x,
                "map_y": device.map_y,
                "data_source": device.data_source,
                "binding_note": device.binding_note,
            }
            for device in devices
            if device.map_x is not None
        ]
    return payload


def twin_zone(db: Session, zone_id: str) -> dict:
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
        "devices": [row(device) for device in devices],
    }


def workbench(db: Session) -> dict:
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
                "items": [row(circuit, {"zone_code": zmap[circuit.zone_id].code if circuit.zone_id in zmap else None}) for circuit in circuits],
            },
            {
                "id": "tasks",
                "title": "执行队列",
                "items": [row(task, {"zone_code": zmap[task.zone_id].code if task.zone_id and task.zone_id in zmap else None}) for task in tasks],
            },
            {
                "id": "notes",
                "title": "协同留言",
                "items": [row(note) for note in notes],
            },
        ],
    }


def seasons(db: Session) -> list[dict]:
    return [row(season) for season in db.scalars(select(Season).order_by(Season.start_date.desc())).all()]


def architecture(db: Session) -> dict:
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
        "boundaries": HONESTY_BOUNDARIES,
        "data_sources": [source.value for source in DataSource],
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
    }
