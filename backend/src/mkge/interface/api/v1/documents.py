import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from src.mkge.interface.api.deps import get_current_user, require_role, get_document_service
from src.mkge.infrastructure.db.postgres.models import UserModel
from src.mkge.application.documents.services import DocumentService
from src.mkge.domain.exceptions import NotFoundError, ValidationError, AuthorizationError

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", status_code=202)
async def upload_document(
    file: UploadFile = File(...),
    user: UserModel = Depends(require_role("admin", "researcher")),
    service: DocumentService = Depends(get_document_service)
):
    try:
        doc = await service.upload_document(user.id, file)
        return {"message": "Document uploaded successfully", "document_id": str(doc.id)}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
async def list_documents(
    user: UserModel = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    docs = await service.list_documents(user.id, user.role)
    return {"items": [doc.model_dump(mode='json') for doc in docs], "total": len(docs)}


@router.get("/{document_id}")
async def get_document(
    document_id: str, 
    user: UserModel = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    try:
        doc = await service.get_document(uuid.UUID(document_id), user.id, user.role)
        return doc.model_dump(mode='json')
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    except AuthorizationError:
        raise HTTPException(status_code=403, detail="Forbidden")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str, 
    user: UserModel = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    try:
        await service.delete_document(uuid.UUID(document_id), user.id, user.role)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    except AuthorizationError:
        raise HTTPException(status_code=403, detail="Forbidden")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")
