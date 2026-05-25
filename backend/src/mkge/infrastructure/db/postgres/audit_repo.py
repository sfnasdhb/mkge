"""Audit Log Repository — persists auditable events for tracking and compliance."""
import uuid
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.mkge.infrastructure.db.postgres.models import AuditLogModel


class AuditRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(
        self,
        user_id: uuid.UUID | None,
        action: str,
        details: str | None = None,
        ip_address: str | None = None,
    ) -> AuditLogModel:
        record = AuditLogModel(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address,
        )
        self._db.add(record)
        await self._db.commit()
        await self._db.refresh(record)
        return record

    async def list_all(
        self,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[AuditLogModel]:
        result = await self._db.execute(
            select(AuditLogModel)
            .order_by(AuditLogModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_all(self) -> int:
        result = await self._db.execute(
            select(func.count()).select_from(AuditLogModel)
        )
        return result.scalar_one()
