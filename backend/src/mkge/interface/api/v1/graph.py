import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.mkge.domain.exceptions import AuthorizationError, NotFoundError
from src.mkge.infrastructure.db.neo4j.driver import get_driver
from src.mkge.infrastructure.db.neo4j.graph_repo import GraphRepository
from src.mkge.infrastructure.db.postgres.database import get_db
from src.mkge.infrastructure.db.postgres.document_repo import DocumentRepository
from src.mkge.infrastructure.db.postgres.models import UserModel
from src.mkge.interface.api.deps import get_current_user

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/overview")
async def graph_overview(user: UserModel = Depends(get_current_user)):
    repo = GraphRepository(get_driver())
    return await repo.get_overview()


@router.get("/documents/{document_id}")
async def document_graph(
    document_id: uuid.UUID,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc_repo = DocumentRepository(db)
    doc = await doc_repo.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    if doc.user_id != user.id and user.role != "admin":
        raise AuthorizationError("Not authorized to view this document")

    repo = GraphRepository(get_driver())
    graph = await repo.get_graph_for_document(document_id)
    return {
        "document_id": str(document_id),
        "filename": doc.filename,
        "status": doc.status,
        **graph,
    }


@router.get("/entity/{entity_id}")
async def entity_subgraph(entity_id: str, user: UserModel = Depends(get_current_user)):
    repo = GraphRepository(get_driver())
    subgraph = await repo.get_subgraph_by_entities([entity_id])
    return subgraph
