import uuid
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Literal

from src.mkge.interface.api.deps import require_role, get_admin_service, get_audit_repository
from src.mkge.infrastructure.db.postgres.models import UserModel
from src.mkge.application.admin.services import AdminService
from src.mkge.infrastructure.db.postgres.audit_repo import AuditRepository

router = APIRouter(prefix="/admin", tags=["admin"])


class UpdateUserRequest(BaseModel):
    role: Literal["admin", "researcher"] | None = None
    is_active: bool | None = None


@router.get("/users")
async def list_users(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    admin: UserModel = Depends(require_role("admin")),
    admin_service: AdminService = Depends(get_admin_service),
):
    users = await admin_service.list_users(offset=offset, limit=limit)
    return {
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ]
    }


@router.patch("/users/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    body: UpdateUserRequest,
    admin: UserModel = Depends(require_role("admin")),
    admin_service: AdminService = Depends(get_admin_service),
):
    user = await admin_service.update_user(
        admin_id=admin.id,
        user_id=user_id,
        role=body.role,
        is_active=body.is_active,
    )
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    admin: UserModel = Depends(require_role("admin")),
    admin_service: AdminService = Depends(get_admin_service),
):
    await admin_service.delete_user(admin_id=admin.id, user_id=user_id)
    return {"status": "success", "message": f"User {user_id} deleted successfully"}


@router.get("/stats")
async def get_stats(
    admin: UserModel = Depends(require_role("admin")),
    admin_service: AdminService = Depends(get_admin_service),
):
    stats = await admin_service.get_stats()
    return stats


@router.get("/audit")
async def list_audit_logs(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    admin: UserModel = Depends(require_role("admin")),
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    logs = await audit_repo.list_all(offset=offset, limit=limit)
    total = await audit_repo.count_all()
    return {
        "total": total,
        "items": [
            {
                "id": str(l.id),
                "user_id": str(l.user_id) if l.user_id else None,
                "action": l.action,
                "details": l.details,
                "ip_address": l.ip_address,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ]
    }
