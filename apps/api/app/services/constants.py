from __future__ import annotations

from app.models import DataSource
from app.services.clock import DEMO_NOW_LABEL

TWIN_LAYER_KEYS: tuple[str, ...] = ("moisture", "crop", "risk", "device", "sensors")

TWIN_AVAILABLE_LAYERS = [
    {"id": "moisture", "label": "墒情层", "data_source": DataSource.SIMULATION.value},
    {"id": "crop", "label": "作物层", "data_source": DataSource.MANUAL.value},
    {"id": "risk", "label": "风险层", "data_source": DataSource.SIMULATION.value},
    {"id": "device", "label": "设备层", "data_source": DataSource.SIMULATION.value},
    {"id": "sensors", "label": "传感器层", "data_source": DataSource.SIMULATION.value},
]

DATA_SOURCE_LEGEND = [
    {"source": DataSource.REAL.value, "label": "真实接入", "note": "本演示场暂无 REAL 传感或机身。"},
    {"source": DataSource.SIMULATION.value, "label": "仿真", "note": "墒情曲线、顾问建议、诊断假设。"},
    {"source": DataSource.MANUAL.value, "label": "人工台账", "note": "作物、资产、任务、冷库抄表。"},
]

HONESTY_BOUNDARIES = [
    "没有 REAL 传感器接入，墒情/气象曲线为 SIMULATION。",
    "灌溉顾问用仿真 ET₀×Kc 与墒情阈值，只生成任务，不开阀。",
    "机器人模块为 stub：无位姿、无遥控、无视频。",
    "AI 智能体只产出建议，controls_hardware 恒为 false。",
    "车队位置来自出车单 MANUAL，不是 GPS 轨迹。",
    "阀门/泵不可远程闭环。",
]

DEMO_CLOCK_NOTE = f"示范场情景时钟固定为 {DEMO_NOW_LABEL}，便于建议与逾期判定可复现。"
