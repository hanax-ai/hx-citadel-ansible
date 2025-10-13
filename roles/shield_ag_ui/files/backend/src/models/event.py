"""Event data models"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class Event(BaseModel):
    id: str
    event_type: str
    job_id: Optional[str] = None
    data: Dict[str, Any]
    timestamp: datetime


class AGUIEvent(BaseModel):
    event_id: str
    type: str
    timestamp: datetime
    data: Dict[str, Any]
