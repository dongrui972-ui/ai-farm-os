from __future__ import annotations

from typing import Literal, TypeAlias

from app.models import DataSource

DataSourceLiteral: TypeAlias = Literal["REAL", "SIMULATION", "MANUAL"]
TaskStatusLiteral: TypeAlias = Literal["todo", "in_progress", "done", "cancelled"]
TaskPriorityLiteral: TypeAlias = Literal["low", "normal", "high", "urgent"]
RiskSeverityLiteral: TypeAlias = Literal["low", "medium", "high"]

DEFAULT_MANUAL_SOURCE: DataSourceLiteral = DataSource.MANUAL.value
DEFAULT_SIM_SOURCE: DataSourceLiteral = DataSource.SIMULATION.value
DATA_SOURCE_VALUES: tuple[DataSourceLiteral, ...] = tuple(source.value for source in DataSource)  # type: ignore[assignment]
