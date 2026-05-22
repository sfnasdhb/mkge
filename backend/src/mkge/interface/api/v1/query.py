from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.mkge.interface.api.deps import get_current_user
from src.mkge.infrastructure.db.postgres.database import get_db
from src.mkge.infrastructure.db.postgres.models import UserModel
from src.mkge.application.query.service import GraphRAGQueryService
from src.mkge.infrastructure.db.neo4j.driver import get_driver

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    question: str


def get_query_service() -> GraphRAGQueryService:
    return GraphRAGQueryService(get_driver())


@router.post("")
async def graphrag_query(
    body: QueryRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    query_service: GraphRAGQueryService = Depends(get_query_service),
):
    result = await query_service.query(body.question, user_id=str(user.id))
    return result


@router.get("/history")
async def query_history(user: UserModel = Depends(get_current_user)):
    # TODO: Implement history retrieval from DB if required
    return {"items": []}
