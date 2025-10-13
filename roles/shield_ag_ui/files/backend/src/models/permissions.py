"""Permission and RBAC models"""
from pydantic import BaseModel
from typing import List
from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    CONTRIBUTOR = "contributor"
    VIEWER = "viewer"


class Permission(str, Enum):
    READ_JOBS = "read:jobs"
    WRITE_JOBS = "write:jobs"
    DELETE_JOBS = "delete:jobs"
    READ_USERS = "read:users"
    WRITE_USERS = "write:users"
    DELETE_USERS = "delete:users"
    ADMIN_CONFIG = "admin:config"


ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.READ_JOBS,
        Permission.WRITE_JOBS,
        Permission.DELETE_JOBS,
        Permission.READ_USERS,
        Permission.WRITE_USERS,
        Permission.DELETE_USERS,
        Permission.ADMIN_CONFIG,
    ],
    Role.CONTRIBUTOR: [
        Permission.READ_JOBS,
        Permission.WRITE_JOBS,
    ],
    Role.VIEWER: [
        Permission.READ_JOBS,
    ],
}


class RBACPolicy(BaseModel):
    role: Role
    permissions: List[Permission]
