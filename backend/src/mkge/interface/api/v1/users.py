from fastapi import APIRouter, Depends

from src.mkge.infrastructure.db.postgres.models import UserModel
from src.mkge.interface.api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def me(user: UserModel = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
    }
