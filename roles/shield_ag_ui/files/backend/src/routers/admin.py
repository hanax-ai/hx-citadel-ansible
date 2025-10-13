"""Admin endpoints"""
from fastapi import APIRouter, HTTPException
import structlog

router = APIRouter()
logger = structlog.get_logger()


@router.get("/users")
async def list_users():
    """List all users"""
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.get("/config")
async def get_config():
    """Get system configuration"""
    raise HTTPException(status_code=501, detail="Not yet implemented")
