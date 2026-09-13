from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class DataSource(str, Enum):
    REAL = "REAL"
    SIMULATION = "SIMULATION"
    MANUAL = "MANUAL"


class ZoneType(str, Enum):
    GREENHOUSE = "greenhouse"
    OPEN_FIELD = "open_field"
    WATER = "water"
    FACILITY = "facility"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    location: Mapped[str] = mapped_column(String(200))
    operator: Mapped[str] = mapped_column(String(120))
    area_mu: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(Text, default="")
    current_season_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    year: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[str] = mapped_column(String(16))
    end_date: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(32))
    notes: Mapped[str] = mapped_column(Text, default="")
    data_source: Mapped[str] = mapped_column(String(20), default=DataSource.MANUAL.value)


class Zone(Base):
    __tablename__ = "zones"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    farm_id: Mapped[str] = mapped_column(ForeignKey("farms.id"))
    code: Mapped[str] = mapped_column(String(16), index=True)
    name: Mapped[str] = mapped_column(String(120))
    zone_type: Mapped[str] = mapped_column(String(32))
    area_mu: Mapped[float] = mapped_column(Float, default=0)
    polygon: Mapped[str] = mapped_column(Text)
    moisture_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    risk_note: Mapped[str] = mapped_column(Text, default="")
    data_source: Mapped[str] = mapped_column(String(20), default=DataSource.SIMULATION.value)

    plants: Mapped[list[Plant]] = relationship(back_populates="zone")
    devices: Mapped[list[Device]] = relationship(back_populates="zone")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    zone_id: Mapped[str | None] = mapped_column(ForeignKey("zones.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(120))
    asset_type: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(32), default="in_service")
    commissioned_at: Mapped[str | None] = mapped_column(String(16), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    data_source: Mapped[str] = mapped_column(String(20), default=DataSource.MANUAL.value)


class Plant(Base):
    __tablename__ = "plants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    zone_id: Mapped[str] = mapped_column(ForeignKey("zones.id"))
    crop_name: Mapped[str] = mapped_column(String(80))
    variety: Mapped[str] = mapped_column(String(80))
    planted_at: Mapped[str] = mapped_column(String(16))
    expected_harvest: Mapped[str | None] = mapped_column(String(16), nullable=True)
    growth_stage: Mapped[str] = mapped_column(String(40))
    plant_count: Mapped[int] = mapped_column(Integer, default=0)
    health_status: Mapped[str] = mapped_column(String(32), default="healthy")
    notes: Mapped[str] = mapped_column(Text, default="")
    data_source: Mapped[str] = mapped_column(String(20), default=DataSource.MANUAL.value)

    zone: Mapped[Zone] = relationship(back_populates="plants")


class IrrigationCircuit(Base):
    __tablename__ = "irrigation_circuits"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    zone_id: Mapped[str] = mapped_column(ForeignKey("zones.id"))
    name: Mapped[str] = mapped_column(String(120))
    method: Mapped[str] = mapped_column(String(40))
    valve_code: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(32), default="idle")
    last_run_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    next_window: Mapped[str | None] = mapped_column(String(80), nullable=True)
    budget_m3: Mapped[float] = mapped_column(Float, default=0)
    used_m3: Mapped[float] = mapped_column(Float, default=0)
    recommendation: Mapped[str] = mapped_column(Text, default="")
    recommendation_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_source: Mapped[str] = mapped_column(String(20), default=DataSource.SIMULATION.value)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    task_type: Mapped[str] = mapped_column(String(40))
    zone_id: Mapped[str | None] = mapped_column(ForeignKey("zones.id"), nullable=True)
    assignee: Mapped[str] = mapped_column(String(80), default="")
    priority: Mapped[str] = mapped_column(String(20), default=TaskPriority.NORMAL.value)
    status: Mapped[str] = mapped_column(String(20), default=TaskStatus.TODO.value)
    due_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    origin: Mapped[str] = mapped_column(String(40), default="manual")
    notes: Mapped[str] = mapped_column(Text, default="")
    data_source: Mapped[str] = mapped_column(String(20), default=DataSource.MANUAL.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    zone_id: Mapped[str | None] = mapped_column(ForeignKey("zones.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(120))
    device_type: Mapped[str] = mapped_column(String(40))
    vendor: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[str] = mapped_column(String(32))
    metric: Mapped[str | None] = mapped_column(String(40), nullable=True)
    last_value: Mapped[str | None] = mapped_column(String(40), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_seen_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    map_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    map_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    binding_note: Mapped[str] = mapped_column(Text, default="")
    data_source: Mapped[str] = mapped_column(String(20), default=DataSource.SIMULATION.value)

    zone: Mapped[Zone] = relationship(back_populates="devices")
    readings: Mapped[list[SensorReading]] = relationship(back_populates="device")


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id"))
    metric: Mapped[str] = mapped_column(String(40))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20))
    recorded_at: Mapped[str] = mapped_column(String(32))
    data_source: Mapped[str] = mapped_column(String(20), default=DataSource.SIMULATION.value)

    device: Mapped[Device] = relationship(back_populates="readings")


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(32), default="ready")
    description: Mapped[str] = mapped_column(Text, default="")
    last_run_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    controls_hardware: Mapped[int] = mapped_column(Integer, default=0)
    data_source: Mapped[str] = mapped_column(String(20), default=DataSource.SIMULATION.value)

    runs: Mapped[list[AgentRun]] = relationship(back_populates="agent")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"))
    summary: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String(32))
    data_source: Mapped[str] = mapped_column(String(20), default=DataSource.SIMULATION.value)

    agent: Mapped[Agent] = relationship(back_populates="runs")


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    zone_id: Mapped[str | None] = mapped_column(ForeignKey("zones.id"), nullable=True)
    plant_id: Mapped[str | None] = mapped_column(ForeignKey("plants.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    symptom: Mapped[str] = mapped_column(Text)
    conclusion: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    created_at: Mapped[str] = mapped_column(String(32))
    data_source: Mapped[str] = mapped_column(String(20), default=DataSource.SIMULATION.value)


class AIJob(Base):
    __tablename__ = "ai_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    job_type: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(32), default="queued")
    input_summary: Mapped[str] = mapped_column(Text, default="")
    output_summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String(32))
    data_source: Mapped[str] = mapped_column(String(20), default=DataSource.SIMULATION.value)
    controls_hardware: Mapped[int] = mapped_column(Integer, default=0)


class Robot(Base):
    __tablename__ = "robots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    robot_type: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(32), default="unbound")
    capability_boundary: Mapped[str] = mapped_column(Text)
    last_pose: Mapped[str | None] = mapped_column(String(80), nullable=True)
    control_enabled: Mapped[int] = mapped_column(Integer, default=0)
    data_source: Mapped[str] = mapped_column(String(20), default=DataSource.SIMULATION.value)


class FleetVehicle(Base):
    __tablename__ = "fleet_vehicles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    vehicle_type: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(32))
    operator: Mapped[str] = mapped_column(String(80), default="")
    last_service: Mapped[str | None] = mapped_column(String(16), nullable=True)
    last_known_place: Mapped[str] = mapped_column(String(120), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    data_source: Mapped[str] = mapped_column(String(20), default=DataSource.MANUAL.value)


class PostHarvestLot(Base):
    __tablename__ = "postharvest_lots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    crop_name: Mapped[str] = mapped_column(String(80))
    quantity_kg: Mapped[float] = mapped_column(Float)
    grade: Mapped[str] = mapped_column(String(20))
    location: Mapped[str] = mapped_column(String(80))
    harvested_at: Mapped[str] = mapped_column(String(16))
    destination: Mapped[str] = mapped_column(String(80), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    data_source: Mapped[str] = mapped_column(String(20), default=DataSource.MANUAL.value)


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(40))
    contact: Mapped[str] = mapped_column(String(80), default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    rating: Mapped[str] = mapped_column(String(20), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    data_source: Mapped[str] = mapped_column(String(20), default=DataSource.MANUAL.value)


class CollaborationNote(Base):
    __tablename__ = "collaboration_notes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    author: Mapped[str] = mapped_column(String(80))
    role: Mapped[str] = mapped_column(String(40), default="")
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    related_module: Mapped[str] = mapped_column(String(40), default="")
    created_at: Mapped[str] = mapped_column(String(32))
    data_source: Mapped[str] = mapped_column(String(20), default=DataSource.MANUAL.value)
