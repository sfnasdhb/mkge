from fastapi import APIRouter
from src.mkge.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}
