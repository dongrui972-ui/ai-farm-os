from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DataSource, IrrigationCircuit, Plant, Zone
from app.services.clock import DEMO_FOCUS_DATE, DEMO_NOW_LABEL

MU_M2 = 666.67
SOURCE = DataSource.SIMULATION.value

# 怀柔 9 月中旬典型晴到多云日，Hargreaves/FAO-56 量级的情景值。
# 不是气象站实况，禁止标 REAL。
SIMULATED_WEATHER = {
    "observed_at": "2026-09-13 08:00",
    "location": "北京市怀柔区桥梓镇",
    "et0_mm": 3.6,
    "tmax_c": 26.0,
    "tmin_c": 14.0,
    "rh_pct": 58,
    "rain_mm": 0.0,
    "wind_ms": 2.1,
    "sky": "晴间多云",
    "data_source": SOURCE,
    "disclaimer": "ET₀ 与气温为示范场仿真情景，不是气象站实况，不能当实时天气用。",
    "forecast": [
        {"date": "2026-09-13", "et0_mm": 3.6, "rain_mm": 0.0, "tmax_c": 26.0, "sky": "晴间多云"},
        {"date": "2026-09-14", "et0_mm": 3.3, "rain_mm": 0.0, "tmax_c": 24.0, "sky": "多云"},
        {"date": "2026-09-15", "et0_mm": 2.4, "rain_mm": 6.0, "tmax_c": 21.0, "sky": "阵雨"},
    ],
}

GREENHOUSE_ET_FACTOR = 0.78
GREENHOUSE_RH_PCT = 82
ROOT_MM = 200  # 0–20cm 管理层
MAX_EVENT_MM = {"drip": 12.0, "micro_spray": 8.0, "sprinkler": 18.0, "furrow": 20.0}
WETTED_FRACTION = {"drip": 0.25, "micro_spray": 0.5, "sprinkler": 1.0, "furrow": 0.6}

ACTION_LABELS = {
    "irrigate": "建议补灌",
    "shorten": "缩短本次灌溉",
    "hold_for_harvest": "采收前停水",
    "watch": "继续观察",
    "hold": "维持计划",
}

CLIMATE_LABELS = {
    "dehumidify": "优先通风排湿",
    "ok": "棚室气候可维持",
    "open_field": "露地按天气执行",
    "na": "非种植区",
}


@dataclass(frozen=True)
class StageSpec:
    kc: float
    mad: float
    care: tuple[str, ...]
    watch: tuple[str, ...]
    harvest_hold: bool = False
    evening_ok: bool = True
    window: str = "清晨或午前"


@dataclass(frozen=True)
class CropSpec:
    fc_pct: float
    pwp_pct: float
    stages: dict[str, StageSpec]


DEFAULT_STAGE = StageSpec(
    kc=1.0,
    mad=0.45,
    care=("按墒情与天气预报补水，避免一次灌透造成沤根。",),
    watch=("缺水萎蔫", "涝渍"),
)

CROPS: dict[str, CropSpec] = {
    "番茄": CropSpec(
        fc_pct=66.0,
        pwp_pct=28.0,
        stages={
            "开花坐果": StageSpec(
                kc=1.10,
                mad=0.40,
                care=(
                    "开花坐果期允许亏缺较小，基质宜昼湿夜略干。",
                    "剧烈干旱后猛灌容易落花落果。",
                    "随水补钙，降低脐腐风险。",
                ),
                watch=("落花", "脐腐", "灰霉"),
                evening_ok=False,
                window="今日 16:00 前结束，避免棚内过夜高湿",
            ),
            "膨果期": StageSpec(
                kc=1.15,
                mad=0.45,
                care=("膨果需稳定水肥，忌忽干忽湿。",),
                watch=("裂果", "脐腐"),
                window="清晨滴灌",
            ),
        },
    ),
    "黄瓜": CropSpec(
        fc_pct=66.0,
        pwp_pct=28.0,
        stages={
            "盛果期": StageSpec(
                kc=1.05,
                mad=0.45,
                care=(
                    "盛果期耗水高，但棚湿过大时先排湿再灌。",
                    "禁止傍晚灌水，降低叶霉 / 灰霉。",
                ),
                watch=("叶霉", "灰霉", "霜霉"),
                evening_ok=False,
                window="晨灌并缩短时长，灌后加强通风",
            ),
        },
    ),
    "彩椒": CropSpec(
        fc_pct=64.0,
        pwp_pct=26.0,
        stages={
            "膨果期": StageSpec(
                kc=1.05,
                mad=0.45,
                care=("膨果配方高钾，保持均匀湿润。", "避免午间高温缺水造成日灼。"),
                watch=("日灼", "脐腐"),
                window="09-15 清晨按配方随水",
            ),
        },
    ),
    "草莓": CropSpec(
        fc_pct=70.0,
        pwp_pct=30.0,
        stages={
            "匍匐茎育苗": StageSpec(
                kc=0.85,
                mad=0.40,
                care=("育苗床保持基质湿润，微喷少量多次。", "避免积水烂茎。"),
                watch=("炭疽", "根腐"),
                window="每日 07:00 / 16:30 微喷保湿",
            ),
        },
    ),
    "生菜": CropSpec(
        fc_pct=58.0,
        pwp_pct=20.0,
        stages={
            "采收期": StageSpec(
                kc=1.00,
                mad=0.50,
                care=("采收前 24 小时停喷，降低叶面带水与泥土。", "清晨采收，避开午热。"),
                watch=("抽薹", "叶缘焦枯"),
                harvest_hold=True,
                window="采收后次日再恢复",
            ),
            "莲座期": StageSpec(
                kc=0.95,
                mad=0.40,
                care=("保持土壤湿润均匀。",),
                watch=("霜霉",),
            ),
        },
    ),
    "菠菜": CropSpec(
        fc_pct=56.0,
        pwp_pct=18.0,
        stages={
            "出苗": StageSpec(
                kc=0.70,
                mad=0.35,
                care=("出苗期表土不断干，小水勤浇。", "雨后注意排涝。"),
                watch=("立枯", "跳甲"),
                window="视表墒，忌大水漫灌",
            ),
        },
    ),
    "玉米": CropSpec(
        fc_pct=55.0,
        pwp_pct=18.0,
        stages={
            "灌浆期": StageSpec(
                kc=1.15,
                mad=0.50,
                care=("灌浆期需水关键，但一次沟灌见湿即可。", "明日有雨则推迟。"),
                watch=("秃尖", "茎腐"),
                window="隔日午后，避开今日阵性大风",
            ),
        },
    ),
}


def weather_payload() -> dict:
    return dict(SIMULATED_WEATHER)


def _crop(crop_name: str | None) -> CropSpec | None:
    if not crop_name:
        return None
    return CROPS.get(crop_name)


def _stage(crop: CropSpec | None, growth_stage: str | None) -> StageSpec:
    if crop and growth_stage and growth_stage in crop.stages:
        return crop.stages[growth_stage]
    return DEFAULT_STAGE


def _et0(zone_type: str) -> float:
    et0 = float(SIMULATED_WEATHER["et0_mm"])
    if zone_type == "greenhouse":
        return round(et0 * GREENHOUSE_ET_FACTOR, 2)
    return et0


def _method_defaults(method: str | None) -> tuple[float, float]:
    key = method or "drip"
    return MAX_EVENT_MM.get(key, 12.0), WETTED_FRACTION.get(key, 0.3)


def advise_plot(
    *,
    crop_name: str | None,
    growth_stage: str | None,
    zone_type: str,
    moisture_pct: float | None,
    area_mu: float,
    health_status: str | None = None,
    method: str | None = None,
    zone_code: str = "",
) -> dict:
    """FAO-56 风格的管理层水量平衡（仿真）。不读写硬件。"""
    if zone_type in ("water", "facility") or moisture_pct is None or not crop_name:
        return {
            "data_source": SOURCE,
            "applicable": False,
            "action": "hold",
            "action_label": "非种植区 / 无墒情",
            "climate_action": "na",
            "climate_label": CLIMATE_LABELS["na"],
            "recommended_mm": 0.0,
            "volume_m3": 0.0,
            "reasons": ["该分区没有可计算的作物墒情。"],
            "care": [],
            "watch": [],
            "moisture_status": "na",
        }

    crop = _crop(crop_name)
    stage = _stage(crop, growth_stage)
    fc = crop.fc_pct if crop else 60.0
    pwp = crop.pwp_pct if crop else 20.0
    taw = max(fc - pwp, 1.0)
    raw = taw * stage.mad
    threshold = round(fc - raw, 1)
    depletion = max(0.0, round(fc - moisture_pct, 1))
    if depletion <= raw:
        ks = 1.0
    else:
        ks = max(0.1, round((taw - depletion) / max(taw - raw, 0.1), 2))

    et0 = _et0(zone_type)
    etc = round(et0 * stage.kc * ks, 2)
    max_event, wetted = _method_defaults(method)
    refill_mm = round(depletion * ROOT_MM / 100.0, 1)
    pulse_mm = round(min(max_event, refill_mm), 1)

    greenhouse = zone_type == "greenhouse"
    humid = greenhouse and health_status in {"watch", "risk"}
    stressed = health_status == "stress" or moisture_pct < threshold
    moisture_status = "dry" if moisture_pct < threshold else "ok"
    if moisture_pct >= fc - 2:
        moisture_status = "wet"

    reasons: list[str] = [
        f"仿真 0–20cm 含水率 {moisture_pct:.0f}%（田间持水量 {fc:.0f}%，凋萎 {pwp:.0f}%）。",
        f"生育期「{growth_stage or '—'}」Kc={stage.kc:.2f}，允许亏缺 MAD={stage.mad:.0%}，灌水阈值 {threshold:.0f}%。",
        f"ET₀ {et0:.2f} mm（{'棚室折减' if greenhouse else '露地'}），ETc {etc:.2f} mm/d，Ks={ks:.2f}。",
    ]

    climate_action = "ok"
    if greenhouse:
        reasons.append(f"棚室仿真相对湿度约 {GREENHOUSE_RH_PCT}%（不是探头实况）。")
        if humid:
            climate_action = "dehumidify"
            reasons.append("叶片或棚湿风险升高，先通风排湿，避免傍晚灌水。")
    else:
        climate_action = "open_field"
        rain = SIMULATED_WEATHER["forecast"][2]["rain_mm"]
        reasons.append(f"未来 48h 仿真降雨 {SIMULATED_WEATHER['forecast'][1]['rain_mm']}+{rain} mm，仅作风险提示。")

    if stage.harvest_hold:
        action = "hold_for_harvest"
        recommended_mm = 0.0
        reasons.append("采收窗口内停水，防止叶面带水泥污、降低货架损耗。")
    elif humid and moisture_pct >= threshold - 2:
        action = "shorten"
        recommended_mm = min(pulse_mm, 6.0) if pulse_mm > 0 else 4.0
        reasons.append(f"水分尚可但棚湿偏高，建议缩短本次至约 {recommended_mm:.0f} mm。")
    elif moisture_pct < threshold:
        action = "irrigate"
        recommended_mm = max(pulse_mm, round(etc, 1))
        recommended_mm = min(max_event, recommended_mm)
        reasons.append(
            f"亏缺 {depletion:.1f} 个百分点，已跌破阈值。本次按 {method or 'drip'} 单次上限给 {recommended_mm:.0f} mm，不一次灌到田间持水量。"
        )
        if not stage.evening_ok:
            reasons.append("禁止傍晚灌溉，降低病害与落花风险。")
    elif depletion >= raw * 0.65:
        action = "watch"
        recommended_mm = 0.0
        reasons.append("接近灌水阈值，明日按 ET 再核，今日不必加开。")
    else:
        action = "hold"
        recommended_mm = 0.0
        reasons.append("墒情在舒适区，维持原计划即可。")

    if stressed and action == "irrigate":
        reasons.append("田间已见水分胁迫症状，与仿真墒情一致，优先补灌而不是用药。")

    volume_m3 = round(recommended_mm / 1000.0 * max(area_mu, 0.0) * MU_M2 * wetted, 1)
    window = stage.window
    if action == "hold_for_harvest":
        window = "采收前 24h 停水"
    elif action == "irrigate" and zone_code == "A3":
        window = "今日 16:00 前补灌，15:30 前结束"

    summary = ACTION_LABELS[action]
    if recommended_mm > 0:
        summary = f"{summary} {recommended_mm:.0f} mm（约 {volume_m3:.1f} m³，滴灌按湿润比折算）"

    return {
        "data_source": SOURCE,
        "applicable": True,
        "model": "fao56_mad_pulse",
        "model_note": "管理允许亏缺 + ET₀×Kc，单次脉冲不超过灌溉方式上限。不启泵、不开阀。",
        "crop_name": crop_name,
        "growth_stage": growth_stage,
        "moisture_pct": moisture_pct,
        "fc_pct": fc,
        "pwp_pct": pwp,
        "taw_pct": round(taw, 1),
        "raw_pct": round(raw, 1),
        "mad": stage.mad,
        "threshold_pct": threshold,
        "depletion_pct": depletion,
        "ks": ks,
        "et0_mm": et0,
        "kc": stage.kc,
        "etc_mm": etc,
        "moisture_status": moisture_status,
        "action": action,
        "action_label": ACTION_LABELS[action],
        "climate_action": climate_action,
        "climate_label": CLIMATE_LABELS[climate_action],
        "recommended_mm": recommended_mm,
        "volume_m3": volume_m3,
        "window_hint": window,
        "summary": summary,
        "reasons": reasons,
        "care": list(stage.care),
        "watch": list(stage.watch),
        "control_enabled": False,
        "generated_at": DEMO_NOW_LABEL,
    }


def advise_zone(zone: Zone, plant: Plant | None, circuit: IrrigationCircuit | None = None) -> dict:
    return advise_plot(
        crop_name=plant.crop_name if plant else None,
        growth_stage=plant.growth_stage if plant else None,
        zone_type=zone.zone_type,
        moisture_pct=zone.moisture_pct,
        area_mu=zone.area_mu,
        health_status=plant.health_status if plant else None,
        method=circuit.method if circuit else None,
        zone_code=zone.code,
    )


def farm_snapshot(zones: list[Zone], plants: list[Plant], circuits: list[IrrigationCircuit]) -> dict:
    plant_by_zone = {item.zone_id: item for item in plants}
    circuit_by_zone = {item.zone_id: item for item in circuits}
    rows: list[dict] = []
    irrigate = 0
    harvest = 0
    climate = 0
    for zone in zones:
        plant = plant_by_zone.get(zone.id)
        circuit = circuit_by_zone.get(zone.id)
        advice = advise_zone(zone, plant, circuit)
        if advice.get("action") == "irrigate":
            irrigate += 1
        if advice.get("action") == "hold_for_harvest":
            harvest += 1
        if advice.get("climate_action") == "dehumidify":
            climate += 1
        rows.append(
            {
                "zone_id": zone.id,
                "zone_code": zone.code,
                "zone_name": zone.name,
                "plant_id": plant.id if plant else None,
                "circuit_id": circuit.id if circuit else None,
                **advice,
            }
        )
    return {
        "focus_date": DEMO_FOCUS_DATE,
        "generated_at": DEMO_NOW_LABEL,
        "data_source": SOURCE,
        "weather": weather_payload(),
        "counts": {
            "irrigate": irrigate,
            "harvest_hold": harvest,
            "dehumidify": climate,
        },
        "zones": rows,
    }


def farm_snapshot_from_db(db: Session) -> dict:
    zones = db.scalars(select(Zone)).all()
    plants = db.scalars(select(Plant)).all()
    circuits = db.scalars(select(IrrigationCircuit)).all()
    return farm_snapshot(zones, plants, circuits)
