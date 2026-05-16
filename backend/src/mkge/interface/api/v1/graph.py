from fastapi import APIRouter, Depends

from src.mkge.interface.api.deps import get_current_user
from src.mkge.infrastructure.db.postgres.models import UserModel

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/overview")
async def graph_overview(user: UserModel = Depends(get_current_user)):
    # Phase 2 stub
    return {"nodes": [], "edges": []}


@router.get("/entity/{entity_id}")
async def entity_subgraph(entity_id: str, user: UserModel = Depends(get_current_user)):
    return {"entity_id": entity_id, "nodes": [], "edges": []}
