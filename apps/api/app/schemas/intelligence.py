from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import DEFAULT_MANUAL_SOURCE, DataSourceLiteral, RiskSeverityLiteral


class DiagnosisCreateSchema(BaseModel):
    zone_id: str | None = None
    plant_id: str | None = None
    title: str
    symptom: str
    conclusion: str = "待农技员确认"
    confidence: float = 0
    severity: RiskSeverityLiteral = "medium"
    data_source: DataSourceLiteral = DEFAULT_MANUAL_SOURCE


class AgentRunRequestSchema(BaseModel):
    note: str = ""


class AIJobCreateSchema(BaseModel):
    title: str
    job_type: str = "briefing"
    input_summary: str = ""
