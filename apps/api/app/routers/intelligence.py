from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.intelligence import AIJobCreateSchema, AgentRunRequestSchema, DiagnosisCreateSchema
from app.services import intelligence as intelligence_service

router = APIRouter()


@router.get("/devices")
def list_devices(db: Session = Depends(get_db)) -> list[dict]:
    return intelligence_service.list_devices(db)


@router.get("/devices/{device_id}")
def get_device(device_id: str, db: Session = Depends(get_db)) -> dict:
    return intelligence_service.get_device(db, device_id)


@router.get("/agents")
def list_agents(db: Session = Depends(get_db)) -> list[dict]:
    return intelligence_service.list_agents(db)


@router.get("/agents/{agent_id}")
def get_agent(agent_id: str, db: Session = Depends(get_db)) -> dict:
    return intelligence_service.get_agent(db, agent_id)


@router.post("/agents/{agent_id}/run")
def run_agent(agent_id: str, body: AgentRunRequestSchema, db: Session = Depends(get_db)) -> dict:
    return intelligence_service.run_agent(db, agent_id, body)


@router.get("/diagnoses")
def list_diagnoses(db: Session = Depends(get_db)) -> list[dict]:
    return intelligence_service.list_diagnoses(db)


@router.post("/diagnoses")
def create_diagnosis(body: DiagnosisCreateSchema, db: Session = Depends(get_db)) -> dict:
    return intelligence_service.create_diagnosis(db, body)


@router.get("/ai-center/jobs")
def list_jobs(db: Session = Depends(get_db)) -> list[dict]:
    return intelligence_service.list_jobs(db)


@router.post("/ai-center/jobs")
def create_job(body: AIJobCreateSchema, db: Session = Depends(get_db)) -> dict:
    return intelligence_service.create_job(db, body)
