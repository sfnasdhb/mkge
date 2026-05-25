from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.mkge.interface.api.deps import get_current_user
from src.mkge.interface.api.rate_limit import RateLimitDep
from src.mkge.infrastructure.db.postgres.database import get_db
from src.mkge.infrastructure.db.postgres.models import UserModel
from src.mkge.infrastructure.db.postgres.query_history_repo import QueryHistoryRepository
from src.mkge.application.query.service import GraphRAGQueryService
from src.mkge.infrastructure.db.neo4j.driver import get_driver

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    question: str
    top_k: int | None = 20
    temperature: float | None = 0.2


def get_query_service(db: AsyncSession = Depends(get_db)) -> GraphRAGQueryService:
    return GraphRAGQueryService(get_driver(), db=db)


@router.post("", dependencies=[Depends(RateLimitDep("query"))])
async def graphrag_query(
    body: QueryRequest,
    user: UserModel = Depends(get_current_user),
    query_service: GraphRAGQueryService = Depends(get_query_service),
):
    result = await query_service.query(
        body.question,
        user_id=str(user.id),
        top_k=body.top_k or 20,
        temperature=body.temperature,
    )
    return result


@router.get("/history")
async def query_history(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    repo = QueryHistoryRepository(db)
    items = await repo.list_by_user(user.id, offset=offset, limit=limit)
    return {
        "items": [
            {
                "id": str(item.id),
                "question": item.question,
                "answer": item.answer,
                "latency_ms": item.latency_ms,
                "created_at": item.created_at.isoformat(),
            }
            for item in items
        ]
    }

