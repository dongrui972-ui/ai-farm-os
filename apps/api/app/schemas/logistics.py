from __future__ import annotations

from pydantic import BaseModel


class RobotCommandSchema(BaseModel):
    command: str
    args: dict | None = None


class NoteCreateSchema(BaseModel):
    author: str
    role: str = ""
    title: str
    body: str
    related_module: str = ""
