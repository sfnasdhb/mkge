"""Query History Repository — persists GraphRAG Q&A for history + admin stats."""
import uuid
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.mkge.infrastructure.db.postgres.models import QueryHistoryModel


class QueryHistoryRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(
        self,
        user_id: uuid.UUID,
        question: str,
        answer: str | None,
        latency_ms: int | None,
    ) -> QueryHistoryModel:
        record = QueryHistoryModel(
            user_id=user_id,
            question=question,
            answer=answer,
            latency_ms=latency_ms,
        )
        self._db.add(record)
        await self._db.commit()
        await self._db.refresh(record)
        return record

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[QueryHistoryModel]:
        result = await self._db.execute(
            select(QueryHistoryModel)
            .where(QueryHistoryModel.user_id == user_id)
            .order_by(QueryHistoryModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_all(self) -> int:
        result = await self._db.execute(
            select(func.count()).select_from(QueryHistoryModel)
        )
        return result.scalar_one()
