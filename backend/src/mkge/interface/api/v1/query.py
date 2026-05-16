from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.mkge.interface.api.deps import get_current_user
from src.mkge.infrastructure.db.postgres.models import UserModel

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    question: str


@router.post("")
async def graphrag_query(body: QueryRequest, user: UserModel = Depends(get_current_user)):
    # Phase 3 stub
    return {"answer": "GraphRAG — coming in Phase 3", "subgraph": {}, "citations": []}


@router.get("/history")
async def query_history(user: UserModel = Depends(get_current_user)):
    return {"items": []}
