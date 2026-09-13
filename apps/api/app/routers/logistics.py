from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CollaborationNote, DataSource, FleetVehicle, PostHarvestLot, Robot, Vendor
from app.serialize import row

router = APIRouter()


class RobotCommand(BaseModel):
    command: str
    args: dict | None = None


class NoteCreate(BaseModel):
    author: str
    role: str = ""
    title: str
    body: str
    related_module: str = ""


@router.get("/robots")
def list_robots(db: Session = Depends(get_db)) -> list[dict]:
    return [
        row(
            r,
            {
                "pose": None,
                "live_gps": False,
                "control_enabled": False,
                "stub": True,
            },
        )
        for r in db.scalars(select(Robot)).all()
    ]


@router.get("/robots/{robot_id}")
def get_robot(robot_id: str, db: Session = Depends(get_db)) -> dict:
    item = db.get(Robot, robot_id)
    if not item:
        raise HTTPException(404, "robot_not_found")
    return row(item, {"pose": None, "live_gps": False, "control_enabled": False, "stub": True})


@router.post("/robots/{robot_id}/command")
def command_robot(robot_id: str, body: RobotCommand) -> dict:
    raise HTTPException(
        status_code=409,
        detail={
            "error": "robot_unbound",
            "message": "机身未接入，拒绝运动/喷雾/云台指令。",
            "command": body.command,
            "data_source": DataSource.SIMULATION.value,
        },
    )


@router.get("/fleet")
def list_fleet(db: Session = Depends(get_db)) -> list[dict]:
    return [
        row(v, {"live_gps": False, "location_note": "位置仅来自出车单或人工登记。"})
        for v in db.scalars(select(FleetVehicle)).all()
    ]


@router.get("/postharvest")
def list_lots(db: Session = Depends(get_db)) -> list[dict]:
    return [row(lot) for lot in db.scalars(select(PostHarvestLot)).all()]


@router.get("/vendors")
def list_vendors(db: Session = Depends(get_db)) -> list[dict]:
    return [row(v) for v in db.scalars(select(Vendor)).all()]


@router.get("/collaboration")
def list_notes(db: Session = Depends(get_db)) -> list[dict]:
    return [row(n) for n in db.scalars(select(CollaborationNote)).all()]


@router.post("/collaboration")
def create_note(body: NoteCreate, db: Session = Depends(get_db)) -> dict:
    note = CollaborationNote(
        id=f"note-{uuid4().hex[:8]}",
        created_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        data_source=DataSource.MANUAL.value,
        **body.model_dump(),
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return row(note)
