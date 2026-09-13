from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import core as core_service

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return core_service.health()


@router.get("/meta")
def meta(db: Session = Depends(get_db)) -> dict:
    return core_service.meta(db)


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict:
    return core_service.dashboard(db)


@router.get("/twin")
def twin(layers: str = "moisture,crop,risk,device,sensors", db: Session = Depends(get_db)) -> dict:
    return core_service.twin(db, layers=layers)


@router.get("/twin/zones/{zone_id}")
def twin_zone(zone_id: str, db: Session = Depends(get_db)) -> dict:
    return core_service.twin_zone(db, zone_id)


@router.get("/workbench")
def workbench(db: Session = Depends(get_db)) -> dict:
    return core_service.workbench(db)


@router.get("/seasons")
def seasons(db: Session = Depends(get_db)) -> list[dict]:
    return core_service.seasons(db)


@router.get("/architecture")
def architecture(db: Session = Depends(get_db)) -> dict:
    return core_service.architecture(db)
