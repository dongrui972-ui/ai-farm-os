from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.logistics import NoteCreateSchema, RobotCommandSchema
from app.services import logistics as logistics_service

router = APIRouter()


@router.get("/robots")
def list_robots(db: Session = Depends(get_db)) -> list[dict]:
    return logistics_service.list_robots(db)


@router.get("/robots/{robot_id}")
def get_robot(robot_id: str, db: Session = Depends(get_db)) -> dict:
    return logistics_service.get_robot(db, robot_id)


@router.post("/robots/{robot_id}/command")
def command_robot(robot_id: str, body: RobotCommandSchema) -> dict:
    _ = robot_id
    logistics_service.reject_robot_command(body)
    return {}


@router.get("/fleet")
def list_fleet(db: Session = Depends(get_db)) -> list[dict]:
    return logistics_service.list_fleet(db)


@router.get("/postharvest")
def list_lots(db: Session = Depends(get_db)) -> list[dict]:
    return logistics_service.list_lots(db)


@router.get("/vendors")
def list_vendors(db: Session = Depends(get_db)) -> list[dict]:
    return logistics_service.list_vendors(db)


@router.get("/collaboration")
def list_notes(db: Session = Depends(get_db)) -> list[dict]:
    return logistics_service.list_notes(db)


@router.post("/collaboration")
def create_note(body: NoteCreateSchema, db: Session = Depends(get_db)) -> dict:
    return logistics_service.create_note(db, body)
