from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import DEFAULT_MANUAL_SOURCE, DataSourceLiteral, TaskPriorityLiteral, TaskStatusLiteral


class TaskCreateSchema(BaseModel):
    title: str
    task_type: str = "general"
    zone_id: str | None = None
    assignee: str = ""
    priority: TaskPriorityLiteral = "normal"
    due_at: str | None = None
    notes: str = ""
    origin: str = "manual"
    data_source: DataSourceLiteral = DEFAULT_MANUAL_SOURCE


class TaskPatchSchema(BaseModel):
    status: TaskStatusLiteral | None = None
    assignee: str | None = None
    notes: str | None = None
    priority: TaskPriorityLiteral | None = None


class AcceptIrrigationSchema(BaseModel):
    assignee: str = Field(default="张永强")
