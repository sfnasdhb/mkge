from fastapi import APIRouter, Depends

from src.mkge.interface.api.deps import get_current_user, require_role
from src.mkge.infrastructure.db.postgres.models import UserModel

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", status_code=202)
async def upload_document(
    user: UserModel = Depends(require_role("admin", "researcher")),
):
    # Phase 1 stub
    return {"message": "Upload endpoint — coming in Phase 1"}


@router.get("")
async def list_documents(user: UserModel = Depends(get_current_user)):
    return {"items": [], "total": 0}


@router.get("/{document_id}")
async def get_document(document_id: str, user: UserModel = Depends(get_current_user)):
    return {"id": document_id, "status": "queued"}


@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: str, user: UserModel = Depends(get_current_user)):
    pass
