"""User data models"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class User(BaseModel):
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: str = "viewer"
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    role: str = "viewer"


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
