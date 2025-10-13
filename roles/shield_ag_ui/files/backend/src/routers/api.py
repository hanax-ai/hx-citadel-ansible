"""Main API endpoints"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import structlog

router = APIRouter()
logger = structlog.get_logger()


class Job(BaseModel):
    id: str
    name: str
    status: str
    created_at: str


@router.get("/jobs", response_model=List[Job])
async def list_jobs():
    """List all jobs"""
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.get("/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str):
    """Get job by ID"""
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.post("/jobs")
async def create_job():
    """Create new job"""
    raise HTTPException(status_code=501, detail="Not yet implemented")
