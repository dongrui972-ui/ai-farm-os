from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CollaborationNote, DataSource, FleetVehicle, PostHarvestLot, Robot, Vendor
from app.schemas.logistics import NoteCreateSchema, RobotCommandSchema
from app.serialize import row


def list_robots(db: Session) -> list[dict]:
    return [
        row(
            item,
            {
                "pose": None,
                "live_gps": False,
                "control_enabled": False,
                "stub": True,
            },
        )
        for item in db.scalars(select(Robot)).all()
    ]


def get_robot(db: Session, robot_id: str) -> dict:
    item = db.get(Robot, robot_id)
    if not item:
        raise HTTPException(status_code=404, detail="robot_not_found")
    return row(item, {"pose": None, "live_gps": False, "control_enabled": False, "stub": True})


def reject_robot_command(payload: RobotCommandSchema) -> None:
    raise HTTPException(
        status_code=409,
        detail={
            "error": "robot_unbound",
            "message": "机身未接入，拒绝运动/喷雾/云台指令。",
            "command": payload.command,
            "data_source": DataSource.SIMULATION.value,
        },
    )


def list_fleet(db: Session) -> list[dict]:
    return [
        row(item, {"live_gps": False, "location_note": "位置仅来自出车单或人工登记。"})
        for item in db.scalars(select(FleetVehicle)).all()
    ]


def list_lots(db: Session) -> list[dict]:
    return [row(item) for item in db.scalars(select(PostHarvestLot)).all()]


def list_vendors(db: Session) -> list[dict]:
    return [row(item) for item in db.scalars(select(Vendor)).all()]


def list_notes(db: Session) -> list[dict]:
    return [row(item) for item in db.scalars(select(CollaborationNote)).all()]


def create_note(db: Session, payload: NoteCreateSchema) -> dict:
    note = CollaborationNote(
        id=f"note-{uuid4().hex[:8]}",
        created_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        data_source=DataSource.MANUAL.value,
        **payload.model_dump(),
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return row(note)
