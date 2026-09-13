from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.production import AcceptIrrigationSchema, TaskCreateSchema, TaskPatchSchema
from app.services import production as production_service

router = APIRouter()

@router.get("/assets")
def list_assets(db: Session = Depends(get_db)) -> list[dict]:
    return production_service.list_assets(db)


@router.get("/assets/{asset_id}")
def get_asset(asset_id: str, db: Session = Depends(get_db)) -> dict:
    return production_service.get_asset(db, asset_id)


@router.get("/plants")
def list_plants(db: Session = Depends(get_db)) -> list[dict]:
    return production_service.list_plants(db)


@router.get("/plants/{plant_id}")
def get_plant(plant_id: str, db: Session = Depends(get_db)) -> dict:
    return production_service.get_plant(db, plant_id)


@router.get("/irrigation")
def list_irrigation(db: Session = Depends(get_db)) -> list[dict]:
    return production_service.list_irrigation(db)


@router.get("/irrigation/{circuit_id}")
def get_irrigation(circuit_id: str, db: Session = Depends(get_db)) -> dict:
    return production_service.get_irrigation(db, circuit_id)


@router.post("/irrigation/{circuit_id}/accept-recommendation")
def accept_irrigation(circuit_id: str, body: AcceptIrrigationSchema, db: Session = Depends(get_db)) -> dict:
    return production_service.accept_irrigation_recommendation(db, circuit_id, assignee=body.assignee)


@router.get("/tasks")
def list_tasks(db: Session = Depends(get_db)) -> list[dict]:
    return production_service.list_tasks(db)


@router.post("/tasks")
def create_task(body: TaskCreateSchema, db: Session = Depends(get_db)) -> dict:
    return production_service.create_task(db, body)


@router.patch("/tasks/{task_id}")
def patch_task(task_id: str, body: TaskPatchSchema, db: Session = Depends(get_db)) -> dict:
    return production_service.patch_task(db, task_id, body)
