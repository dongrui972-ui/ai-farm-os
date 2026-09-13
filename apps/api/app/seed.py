from __future__ import annotations

import json
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AIJob,
    Agent,
    AgentRun,
    Asset,
    CollaborationNote,
    DataSource,
    Device,
    Diagnosis,
    Farm,
    FleetVehicle,
    IrrigationCircuit,
    Plant,
    PostHarvestLot,
    Robot,
    Season,
    SensorReading,
    Task,
    Vendor,
    Zone,
)


def _poly(*points: tuple[float, float]) -> str:
    return json.dumps([{"x": x, "y": y} for x, y in points])


def _asset(id, zone_id, name, asset_type, status, commissioned_at, notes, data_source) -> Asset:
    return Asset(
        id=id,
        zone_id=zone_id,
        name=name,
        asset_type=asset_type,
        status=status,
        commissioned_at=commissioned_at,
        notes=notes,
        data_source=data_source,
    )


def _plant(
    id, zone_id, crop_name, variety, planted_at, expected_harvest, growth_stage, plant_count, health_status, notes, data_source
) -> Plant:
    return Plant(
        id=id,
        zone_id=zone_id,
        crop_name=crop_name,
        variety=variety,
        planted_at=planted_at,
        expected_harvest=expected_harvest,
        growth_stage=growth_stage,
        plant_count=plant_count,
        health_status=health_status,
        notes=notes,
        data_source=data_source,
    )


def _irr(
    id, zone_id, name, method, valve_code, status, last_run_at, next_window, budget_m3, used_m3, recommendation, recommendation_mm, data_source
) -> IrrigationCircuit:
    return IrrigationCircuit(
        id=id,
        zone_id=zone_id,
        name=name,
        method=method,
        valve_code=valve_code,
        status=status,
        last_run_at=last_run_at,
        next_window=next_window,
        budget_m3=budget_m3,
        used_m3=used_m3,
        recommendation=recommendation,
        recommendation_mm=recommendation_mm,
        data_source=data_source,
    )


def _device(
    id, zone_id, name, device_type, vendor, status, metric, last_value, unit, last_seen_at, map_x, map_y, binding_note, data_source
) -> Device:
    return Device(
        id=id,
        zone_id=zone_id,
        name=name,
        device_type=device_type,
        vendor=vendor,
        status=status,
        metric=metric,
        last_value=last_value,
        unit=unit,
        last_seen_at=last_seen_at,
        map_x=map_x,
        map_y=map_y,
        binding_note=binding_note,
        data_source=data_source,
    )


def _agent(id, name, role, status, description, last_run_at, controls_hardware, data_source) -> Agent:
    return Agent(
        id=id,
        name=name,
        role=role,
        status=status,
        description=description,
        last_run_at=last_run_at,
        controls_hardware=controls_hardware,
        data_source=data_source,
    )


def _run(id, agent_id, summary, recommendation, created_at, data_source) -> AgentRun:
    return AgentRun(
        id=id,
        agent_id=agent_id,
        summary=summary,
        recommendation=recommendation,
        created_at=created_at,
        data_source=data_source,
    )


def _diag(id, zone_id, plant_id, title, symptom, conclusion, confidence, severity, created_at, data_source) -> Diagnosis:
    return Diagnosis(
        id=id,
        zone_id=zone_id,
        plant_id=plant_id,
        title=title,
        symptom=symptom,
        conclusion=conclusion,
        confidence=confidence,
        severity=severity,
        created_at=created_at,
        data_source=data_source,
    )


def _job(id, title, job_type, status, input_summary, output_summary, created_at, data_source, controls_hardware) -> AIJob:
    return AIJob(
        id=id,
        title=title,
        job_type=job_type,
        status=status,
        input_summary=input_summary,
        output_summary=output_summary,
        created_at=created_at,
        data_source=data_source,
        controls_hardware=controls_hardware,
    )


def _veh(id, name, vehicle_type, status, operator, last_service, last_known_place, notes, data_source) -> FleetVehicle:
    return FleetVehicle(
        id=id,
        name=name,
        vehicle_type=vehicle_type,
        status=status,
        operator=operator,
        last_service=last_service,
        last_known_place=last_known_place,
        notes=notes,
        data_source=data_source,
    )


def _lot(id, crop_name, quantity_kg, grade, location, harvested_at, destination, notes, data_source) -> PostHarvestLot:
    return PostHarvestLot(
        id=id,
        crop_name=crop_name,
        quantity_kg=quantity_kg,
        grade=grade,
        location=location,
        harvested_at=harvested_at,
        destination=destination,
        notes=notes,
        data_source=data_source,
    )


def _vendor(id, name, category, contact, phone, rating, notes, data_source) -> Vendor:
    return Vendor(
        id=id,
        name=name,
        category=category,
        contact=contact,
        phone=phone,
        rating=rating,
        notes=notes,
        data_source=data_source,
    )


def _note(id, author, role, title, body, related_module, created_at, data_source) -> CollaborationNote:
    return CollaborationNote(
        id=id,
        author=author,
        role=role,
        title=title,
        body=body,
        related_module=related_module,
        created_at=created_at,
        data_source=data_source,
    )


def seed_if_empty(db: Session) -> bool:
    count = db.scalar(select(func.count()).select_from(Farm)) or 0
    if count:
        return False
    seed_demo(db)
    return True


def seed_demo(db: Session) -> None:
    now = datetime(2026, 9, 13, 8, 30, 0)
    sim = DataSource.SIMULATION.value
    manual = DataSource.MANUAL.value

    db.add(
        Farm(
            id="farm-huairou",
            name="一级芯界怀柔示范农场",
            location="北京市怀柔区桥梓镇",
            operator="一级芯界农业科技",
            area_mu=186,
            description="日光温室与露地混作示范场，用于决策台、数字孪生与水肥调度验证。田间传感与机器人为仿真/未接入，不冒充实时机身。",
            current_season_id="season-2026-autumn",
        )
    )

    seasons = [
        Season(
            id="season-2025-spring",
            name="2025 春茬",
            year=2025,
            start_date="2025-02-20",
            end_date="2025-06-30",
            status="closed",
            notes="番茄/黄瓜春茬已归档，产量记录来自人工台账。",
            data_source=manual,
        ),
        Season(
            id="season-2025-autumn",
            name="2025 秋茬",
            year=2025,
            start_date="2025-08-01",
            end_date="2025-12-15",
            status="closed",
            notes="秋延后番茄与生菜，冷库周转正常。",
            data_source=manual,
        ),
        Season(
            id="season-2026-spring",
            name="2026 春茬",
            year=2026,
            start_date="2026-02-18",
            end_date="2026-06-28",
            status="closed",
            notes="春茬已结束，部分设施转入秋茬换茬。",
            data_source=manual,
        ),
        Season(
            id="season-2026-autumn",
            name="2026 秋茬",
            year=2026,
            start_date="2026-08-05",
            end_date="2026-12-20",
            status="active",
            notes="当前生产季。A3 墒情偏低，A5 叶部风险升高，B2 生菜接近采收窗口。",
            data_source=manual,
        ),
    ]
    db.add_all(seasons)

    zones = [
        Zone(
            id="zone-a1",
            farm_id="farm-huairou",
            code="A1",
            name="A1 日光温室 · 樱桃番茄",
            zone_type="greenhouse",
            area_mu=4.2,
            polygon=_poly((40, 80), (220, 80), (220, 180), (40, 180)),
            moisture_pct=62,
            risk_level="low",
            risk_note="长势均匀，暂无病征。",
            data_source=sim,
        ),
        Zone(
            id="zone-a2",
            farm_id="farm-huairou",
            code="A2",
            name="A2 日光温室 · 黄瓜盛果",
            zone_type="greenhouse",
            area_mu=4.0,
            polygon=_poly((240, 80), (420, 80), (420, 180), (240, 180)),
            moisture_pct=58,
            risk_level="medium",
            risk_note="棚湿偏高，注意通风降湿。",
            data_source=sim,
        ),
        Zone(
            id="zone-a3",
            farm_id="farm-huairou",
            code="A3",
            name="A3 日光温室 · 硬粉番茄",
            zone_type="greenhouse",
            area_mu=4.1,
            polygon=_poly((40, 200), (220, 200), (220, 300), (40, 300)),
            moisture_pct=41,
            risk_level="high",
            risk_note="0–20cm 墒情跌破阈值，今日需补灌。",
            data_source=sim,
        ),
        Zone(
            id="zone-a4",
            farm_id="farm-huairou",
            code="A4",
            name="A4 日光温室 · 彩椒膨果",
            zone_type="greenhouse",
            area_mu=3.8,
            polygon=_poly((240, 200), (420, 200), (420, 300), (240, 300)),
            moisture_pct=55,
            risk_level="low",
            risk_note="膨果期水肥节奏正常。",
            data_source=sim,
        ),
        Zone(
            id="zone-a5",
            farm_id="farm-huairou",
            code="A5",
            name="A5 日光温室 · 黄瓜",
            zone_type="greenhouse",
            area_mu=4.0,
            polygon=_poly((40, 320), (220, 320), (220, 420), (40, 420)),
            moisture_pct=64,
            risk_level="high",
            risk_note="中部叶片疑似叶霉，仿真诊断置信度 0.74。",
            data_source=sim,
        ),
        Zone(
            id="zone-a6",
            farm_id="farm-huairou",
            code="A6",
            name="A6 日光温室 · 草莓育苗",
            zone_type="greenhouse",
            area_mu=3.6,
            polygon=_poly((240, 320), (420, 320), (420, 420), (240, 420)),
            moisture_pct=68,
            risk_level="low",
            risk_note="匍匐茎繁苗，基质湿度充足。",
            data_source=sim,
        ),
        Zone(
            id="zone-b1",
            farm_id="farm-huairou",
            code="B1",
            name="B1 露地 · 散叶生菜",
            zone_type="open_field",
            area_mu=8.5,
            polygon=_poly((500, 80), (680, 80), (680, 200), (500, 200)),
            moisture_pct=52,
            risk_level="low",
            risk_note="可分批采收。",
            data_source=sim,
        ),
        Zone(
            id="zone-b2",
            farm_id="farm-huairou",
            code="B2",
            name="B2 露地 · 奶油生菜",
            zone_type="open_field",
            area_mu=7.8,
            polygon=_poly((700, 80), (880, 80), (880, 200), (700, 200)),
            moisture_pct=48,
            risk_level="medium",
            risk_note="叶球紧实，建议明日清晨采收。",
            data_source=sim,
        ),
        Zone(
            id="zone-b3",
            farm_id="farm-huairou",
            code="B3",
            name="B3 露地 · 菠菜",
            zone_type="open_field",
            area_mu=6.4,
            polygon=_poly((500, 220), (680, 220), (680, 340), (500, 340)),
            moisture_pct=50,
            risk_level="low",
            risk_note="出苗整齐。",
            data_source=sim,
        ),
        Zone(
            id="zone-b4",
            farm_id="farm-huairou",
            code="B4",
            name="B4 露地 · 鲜食玉米",
            zone_type="open_field",
            area_mu=12.0,
            polygon=_poly((700, 220), (880, 220), (880, 340), (700, 340)),
            moisture_pct=46,
            risk_level="low",
            risk_note="灌浆期，按需补水即可。",
            data_source=sim,
        ),
        Zone(
            id="zone-w1",
            farm_id="farm-huairou",
            code="W1",
            name="W1 蓄水池",
            zone_type="water",
            area_mu=2.1,
            polygon=_poly((500, 380), (640, 380), (640, 500), (500, 500)),
            moisture_pct=None,
            risk_level="low",
            risk_note="水位人工抄表，非在线液位计。",
            data_source=manual,
        ),
        Zone(
            id="zone-f1",
            farm_id="farm-huairou",
            code="F1",
            name="F1 泵房 / 阀井",
            zone_type="facility",
            area_mu=0.4,
            polygon=_poly((660, 400), (740, 400), (740, 460), (660, 460)),
            moisture_pct=None,
            risk_level="low",
            risk_note="电磁阀未做远程闭环，仅台账与仿真建议。",
            data_source=manual,
        ),
        Zone(
            id="zone-p1",
            farm_id="farm-huairou",
            code="P1",
            name="P1 包装分拣间",
            zone_type="facility",
            area_mu=1.2,
            polygon=_poly((760, 380), (880, 380), (880, 500), (760, 500)),
            moisture_pct=None,
            risk_level="low",
            risk_note="人工分拣线。",
            data_source=manual,
        ),
        Zone(
            id="zone-c1",
            farm_id="farm-huairou",
            code="C1",
            name="C1 预冷冷库",
            zone_type="facility",
            area_mu=0.8,
            polygon=_poly((760, 520), (880, 520), (880, 600), (760, 600)),
            moisture_pct=None,
            risk_level="low",
            risk_note="库温由值班员每两小时抄表。",
            data_source=manual,
        ),
    ]
    db.add_all(zones)

    assets = [
        _asset("asset-gh-a1", "zone-a1", "A1 日光温室骨架", "greenhouse", "in_service", "2019-04-12", "镀锌骨架 + PO 膜，2025 秋换膜。", manual),
        _asset("asset-gh-a2", "zone-a2", "A2 日光温室骨架", "greenhouse", "in_service", "2019-04-12", "卷帘被正常。", manual),
        _asset("asset-gh-a3", "zone-a3", "A3 日光温室骨架", "greenhouse", "in_service", "2020-03-08", "东侧侧窗密封待检修。", manual),
        _asset("asset-gh-a4", "zone-a4", "A4 日光温室骨架", "greenhouse", "in_service", "2020-03-08", "", manual),
        _asset("asset-gh-a5", "zone-a5", "A5 日光温室骨架", "greenhouse", "in_service", "2021-03-20", "", manual),
        _asset("asset-gh-a6", "zone-a6", "A6 日光温室骨架", "greenhouse", "in_service", "2021-03-20", "育苗床架 2024 更换。", manual),
        _asset("asset-tank-w1", "zone-w1", "300m³ 蓄水池", "reservoir", "in_service", "2018-10-01", "水位 68%，人工抄表。", manual),
        _asset("asset-pump-f1", "zone-f1", "变频泵组 P-1", "pump", "in_service", "2022-05-16", "无远程启停，现场按钮。", manual),
        _asset("asset-valve-a3", "zone-a3", "A3 单元阀 V-A3", "valve", "in_service", "2023-04-02", "未接入物联网闭环。", manual),
        _asset("asset-cool-c1", "zone-c1", "预冷库 1#", "cold_storage", "in_service", "2021-08-11", "设定 4°C，值班抄表。", manual),
        _asset("asset-pack-p1", "zone-p1", "分拣包装线", "packing", "in_service", "2022-01-09", "人工分级。", manual),
        _asset("asset-well", "zone-f1", "农用井 1#", "well", "in_service", "2016-06-01", "取水许可有效。", manual),
    ]
    db.add_all(assets)

    plants = [
        _plant("plant-a1", "zone-a1", "番茄", "粉果樱桃", "2026-08-08", "2026-10-20", "开花坐果", 2400, "healthy", "第一穗坐果稳定。", manual),
        _plant("plant-a2", "zone-a2", "黄瓜", "津优 401", "2026-07-22", "2026-09-28", "盛果期", 1800, "watch", "棚湿偏高，注意灰霉。", manual),
        _plant("plant-a3", "zone-a3", "番茄", "硬粉 808", "2026-08-02", "2026-10-25", "开花坐果", 2100, "stress", "中午萎蔫加重，与墒情一致。", manual),
        _plant("plant-a4", "zone-a4", "彩椒", "红黄双色", "2026-07-18", "2026-10-12", "膨果期", 1600, "healthy", "", manual),
        _plant("plant-a5", "zone-a5", "黄瓜", "博耐 14", "2026-07-25", "2026-09-30", "盛果期", 1750, "risk", "中部叶背见霉层，待人工复核。", manual),
        _plant("plant-a6", "zone-a6", "草莓", "红颜", "2026-08-20", "2026-11-15", "匍匐茎育苗", 3200, "healthy", "子苗尚未定植。", manual),
        _plant("plant-b1", "zone-b1", "生菜", "散叶青", "2026-08-16", "2026-09-18", "采收期", 0, "healthy", "可按订单分批割。", manual),
        _plant("plant-b2", "zone-b2", "生菜", "奶油球", "2026-08-12", "2026-09-14", "采收期", 0, "healthy", "建议 9/14 清晨采，避开午热。", manual),
        _plant("plant-b3", "zone-b3", "菠菜", "尖叶", "2026-09-02", "2026-10-08", "出苗", 0, "healthy", "", manual),
        _plant("plant-b4", "zone-b4", "玉米", "京科糯 2000", "2026-06-28", "2026-09-25", "灌浆期", 0, "healthy", "", manual),
    ]
    db.add_all(plants)

    circuits = [
        _irr("irr-a1", "zone-a1", "A1 滴灌回路", "drip", "V-A1", "idle", "2026-09-12 06:40", "09-14 05:30–06:10", 18, 11.2, "维持现计划，无需加开。", None, sim),
        _irr("irr-a2", "zone-a2", "A2 滴灌回路", "drip", "V-A2", "idle", "2026-09-12 07:10", "09-14 06:20–07:00", 16, 10.4, "棚湿偏高，建议缩短 8 分钟。", 4.0, sim),
        _irr("irr-a3", "zone-a3", "A3 滴灌回路", "drip", "V-A3", "needs_action", "2026-09-11 06:20", "建议今日 16:00 前补灌", 18, 9.1, "0–20cm 仿真墒情 41%，建议补灌 12mm，约 8.2m³。", 12.0, sim),
        _irr("irr-a4", "zone-a4", "A4 滴灌回路", "drip", "V-A4", "idle", "2026-09-13 05:50", "09-15 05:40–06:20", 15, 8.6, "按膨果配方继续。", None, sim),
        _irr("irr-a5", "zone-a5", "A5 滴灌回路", "drip", "V-A5", "idle", "2026-09-13 06:10", "09-14 06:30–07:00", 16, 9.8, "发病风险期控制叶片湿度，避免傍晚灌。", 6.0, sim),
        _irr("irr-a6", "zone-a6", "A6 微喷回路", "micro_spray", "V-A6", "idle", "2026-09-13 07:00", "每日 07:00 / 16:30", 10, 6.2, "基质保湿即可。", None, sim),
        _irr("irr-b1", "zone-b1", "B1 喷灌回路", "sprinkler", "V-B1", "idle", "2026-09-11 18:10", "视天气", 40, 22.0, "采收前 24h 停喷。", None, sim),
        _irr("irr-b2", "zone-b2", "B2 喷灌回路", "sprinkler", "V-B2", "idle", "2026-09-11 18:40", "采收后恢复", 36, 19.4, "明日采收，今日停水。", None, sim),
        _irr("irr-b4", "zone-b4", "B4 沟灌/软管", "furrow", "V-B4", "idle", "2026-09-10 17:00", "灌浆视墒", 50, 28.0, "可隔日补一次。", 15.0, sim),
    ]
    db.add_all(circuits)

    tasks = [
        Task(
            id="task-irr-a3",
            title="A3 硬粉番茄补灌 12mm",
            task_type="irrigation",
            zone_id="zone-a3",
            assignee="张永强",
            priority="urgent",
            status="todo",
            due_at="2026-09-13 16:00",
            origin="ai_suggested",
            notes="来自灌溉顾问仿真建议，需现场确认阀门与水压后再执行。",
            data_source=sim,
        ),
        Task(
            id="task-scout-a5",
            title="A5 黄瓜叶霉人工复核",
            task_type="scouting",
            zone_id="zone-a5",
            assignee="李敏",
            priority="high",
            status="in_progress",
            due_at="2026-09-13 12:00",
            origin="ai_suggested",
            notes="仿真诊断不可替代田间镜检。",
            data_source=sim,
        ),
        Task(
            id="task-harvest-b2",
            title="B2 奶油生菜清晨采收",
            task_type="harvest",
            zone_id="zone-b2",
            assignee="王秀兰",
            priority="high",
            status="todo",
            due_at="2026-09-14 06:30",
            origin="manual",
            notes="对接商超订单 1.2 吨。",
            data_source=manual,
        ),
        Task(
            id="task-vent-a2",
            title="A2 午前通风排湿",
            task_type="climate",
            zone_id="zone-a2",
            assignee="张永强",
            priority="normal",
            status="todo",
            due_at="2026-09-13 10:30",
            origin="manual",
            notes="",
            data_source=manual,
        ),
        Task(
            id="task-overdue-film",
            title="A3 东侧窗密封修补",
            task_type="maintenance",
            zone_id="zone-a3",
            assignee="赵师傅",
            priority="normal",
            status="todo",
            due_at="2026-09-11 17:00",
            origin="manual",
            notes="已逾期，刮风天漏风。",
            data_source=manual,
        ),
        Task(
            id="task-fert-a4",
            title="A4 彩椒膨果肥",
            task_type="fertigation",
            zone_id="zone-a4",
            assignee="李敏",
            priority="normal",
            status="done",
            due_at="2026-09-12 07:00",
            origin="manual",
            notes="已按配方随水冲施。",
            data_source=manual,
        ),
        Task(
            id="task-cool-check",
            title="冷库抄表与预冷位核对",
            task_type="postharvest",
            zone_id="zone-c1",
            assignee="值班",
            priority="normal",
            status="todo",
            due_at="2026-09-13 18:00",
            origin="manual",
            notes="",
            data_source=manual,
        ),
    ]
    db.add_all(tasks)

    devices = [
        _device("dev-sm-a1", "zone-a1", "A1 土壤墒情", "soil_moisture", "田芯传感（仿真）", "sim_online", "moisture", "62", "%", "2026-09-13 08:00", 130, 130, "回放仿真曲线，非现场探针。", sim),
        _device("dev-sm-a3", "zone-a3", "A3 土壤墒情", "soil_moisture", "田芯传感（仿真）", "sim_online", "moisture", "41", "%", "2026-09-13 08:00", 130, 250, "回放仿真曲线，非现场探针。", sim),
        _device("dev-sm-a5", "zone-a5", "A5 土壤墒情", "soil_moisture", "田芯传感（仿真）", "sim_online", "moisture", "64", "%", "2026-09-13 08:00", 130, 370, "回放仿真曲线，非现场探针。", sim),
        _device("dev-sm-b2", "zone-b2", "B2 土壤墒情", "soil_moisture", "田芯传感（仿真）", "sim_online", "moisture", "48", "%", "2026-09-13 08:00", 790, 140, "回放仿真曲线，非现场探针。", sim),
        _device("dev-ws-01", None, "场部气象站", "weather", "未绑定", "unbound", None, None, None, None, 460, 40, "硬件未接入，页面不展示实时气象。", sim),
        _device("dev-cam-a5", "zone-a5", "A5 棚头摄像头", "camera", "未绑定", "unbound", None, None, None, None, 200, 340, "无视频流，仅占位资产。", sim),
        _device("dev-valve-a3", "zone-a3", "A3 单元阀遥测", "valve_telemetry", "未绑定", "unbound", None, None, None, None, 50, 250, "不可远程开阀。", sim),
        _device("dev-temp-c1", "zone-c1", "冷库温度抄表位", "manual_logger", "值班台账", "manual", "temperature", "4.2", "°C", "2026-09-13 08:00", 820, 560, "人工抄表写入。", manual),
    ]
    db.add_all(devices)

    readings: list[SensorReading] = []
    series = {
        "dev-sm-a1": (62.0, 0.4),
        "dev-sm-a3": (41.0, -1.6),
        "dev-sm-a5": (64.0, 0.2),
        "dev-sm-b2": (48.0, -0.5),
    }
    for device_id, (latest, slope) in series.items():
        for i in range(8, -1, -1):
            ts = now - timedelta(hours=i * 3)
            value = round(latest - slope * i, 1)
            readings.append(
                SensorReading(
                    id=f"{device_id}-r{i}",
                    device_id=device_id,
                    metric="moisture",
                    value=value,
                    unit="%",
                    recorded_at=ts.strftime("%Y-%m-%d %H:%M"),
                    data_source=sim,
                )
            )
    readings.append(
        SensorReading(
            id="dev-temp-c1-r0",
            device_id="dev-temp-c1",
            metric="temperature",
            value=4.2,
            unit="°C",
            recorded_at="2026-09-13 08:00",
            data_source=manual,
        )
    )
    db.add_all(readings)

    agents = [
        _agent("agent-irrigation", "灌溉顾问", "水肥", "ready", "根据仿真墒情与作物阶段给出补灌建议。不启泵、不开阀。", "2026-09-13 07:40", 0, sim),
        _agent("agent-diagnosis", "病虫害助手", "植保", "ready", "对人工描述或棚内照片备注做鉴别假设，需农技员确认。", "2026-09-13 07:55", 0, sim),
        _agent("agent-yield", "产量预估", "经营", "ready", "按本季台账做粗估，不连接称重设备。", "2026-09-12 19:10", 0, sim),
        _agent("agent-scout", "巡田编排", "任务", "ready", "把风险区编成巡田顺序，不调度机器人。", "2026-09-13 06:50", 0, sim),
    ]
    db.add_all(agents)
    db.add_all(
        [
            _run("run-irr-1", "agent-irrigation", "A3 墒情连续 24h 下行。", "建议今日补灌 12mm；A2 缩短晨灌。未向泵阀下发指令。", "2026-09-13 07:40", sim),
            _run("run-diag-1", "agent-diagnosis", "A5 中部叶背疑似霉层。", "倾向叶霉，置信度 0.74。请镜检后决定用药，系统不会喷药。", "2026-09-13 07:55", sim),
            _run("run-yield-1", "agent-yield", "秋茬温室番茄/黄瓜粗估。", "温室番茄约 18–20 吨，黄瓜 9–11 吨，区间来自历史台账。", "2026-09-12 19:10", sim),
            _run("run-scout-1", "agent-scout", "今日巡田顺序。", "A3 → A5 → A2 → B2。不包含机身路径。", "2026-09-13 06:50", sim),
        ]
    )

    db.add_all(
        [
            _diag(
                "diag-a5",
                "zone-a5",
                "plant-a5",
                "A5 黄瓜叶部霉层",
                "中部功能叶背面灰褐色霉层，棚湿偏高。",
                "仿真倾向叶霉病。须人工镜检后决策，系统不喷药、不联动植保机。",
                0.74,
                "high",
                "2026-09-13 07:55",
                sim,
            ),
            _diag(
                "diag-a3",
                "zone-a3",
                "plant-a3",
                "A3 午前萎蔫",
                "坐果期中午叶片下垂，土壤手测偏干。",
                "水分胁迫，与仿真墒情 41% 一致。优先补灌，排除根结线虫需另行取样。",
                0.81,
                "medium",
                "2026-09-13 08:05",
                sim,
            ),
            _diag(
                "diag-a2",
                "zone-a2",
                "plant-a2",
                "A2 高湿预警",
                "晨露未干，棚膜滴水。",
                "灰霉风险上升，建议通风与避免傍晚灌水。",
                0.66,
                "medium",
                "2026-09-13 07:20",
                sim,
            ),
        ]
    )

    db.add_all(
        [
            _job("job-weekly", "本周水肥纪要", "briefing", "done", "回路台账 + 仿真墒情", "三件需拍板：A3 补灌、A5 复核、B2 采收窗口。", "2026-09-13 07:10", sim, 0),
            _job("job-risk", "棚室风险扫描", "risk_scan", "done", "分区风险字段", "高风险：A3 水分、A5 叶部。", "2026-09-13 07:30", sim, 0),
            _job("job-queue", "订单与采收对齐", "planning", "queued", "B2 商超订单 1.2t", "等待人工确认包装规格后生成采收清单。", "2026-09-13 08:20", sim, 0),
        ]
    )

    db.add_all(
        [
            Robot(
                id="robot-scout-01",
                name="巡检机器人 01",
                robot_type="scout",
                status="unbound",
                capability_boundary="机身未接入。不提供实时 GPS，不接受运动/云台控制，不回传现场视频。",
                last_pose=None,
                control_enabled=0,
                data_source=sim,
            ),
            Robot(
                id="robot-spray-01",
                name="喷雾机器人 01",
                robot_type="spray",
                status="unbound",
                capability_boundary="未绑定喷雾机。系统不会下发喷药或行走指令。",
                last_pose=None,
                control_enabled=0,
                data_source=sim,
            ),
        ]
    )

    db.add_all(
        [
            _veh("veh-truck-1", "轻卡 京P·农01", "truck", "available", "刘师傅", "2026-08-21", "场部门口（人工登记）", "无车载 GPS。", manual),
            _veh("veh-van-1", "厢货 京P·农02", "van", "out", "王秀兰", "2026-07-03", "去往新发地（出车单）", "位置来自出车单，非轨迹。", manual),
            _veh("veh-tractor-1", "轮式拖拉机", "tractor", "maintenance", "赵师傅", "2026-09-08", "机库", "液压待修。", manual),
        ]
    )

    db.add_all(
        [
            _lot("lot-lettuce-1", "散叶生菜", 420, "A", "C1 预冷", "2026-09-12", "商超-绿叶", "昨夜入库。", manual),
            _lot("lot-cuke-1", "黄瓜", 280, "A", "P1 待装", "2026-09-13", "批发-新发地", "今晨采。", manual),
            _lot("lot-pepper-1", "彩椒", 160, "B", "C1 预冷", "2026-09-11", "待定", "等分级。", manual),
        ]
    )

    db.add_all(
        [
            _vendor("ven-seed", "京研种业", "种子", "陈工", "010-8000-1001", "长期", "番茄/生菜主供。", manual),
            _vendor("ven-fert", "绿源水溶肥", "肥料", "周经理", "010-8000-1002", "合格", "膨果高钾配方。", manual),
            _vendor("ven-film", "华北农膜", "农资", "马店长", "010-8000-1003", "合格", "PO 膜与滴灌带。", manual),
            _vendor("ven-pkg", "鲜达包装", "包装", "小吴", "010-8000-1004", "备用", "生菜周转筐。", manual),
        ]
    )

    db.add_all(
        [
            _note(
                "note-1",
                "李敏",
                "农技员",
                "A5 先镜检再谈药",
                "照片只能当线索。下午带手持镜，确认后再选保护性药剂。系统诊断不要直接写成处方。",
                "diagnosis",
                "2026-09-13 08:12",
                manual,
            ),
            _note(
                "note-2",
                "张永强",
                "场长",
                "A3 补灌不要傍晚",
                "按顾问建议 12mm，但改到 15:30 前结束，避免棚内过夜高湿。",
                "irrigation",
                "2026-09-13 08:18",
                manual,
            ),
            _note(
                "note-3",
                "王秀兰",
                "采收",
                "B2 筐量",
                "商超要 5kg 筐、去黄叶。冷库先留 2 托盘缓冲。",
                "postharvest",
                "2026-09-12 19:40",
                manual,
            ),
        ]
    )

    db.commit()
