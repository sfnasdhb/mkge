from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.mkge.config import settings
from src.mkge.infrastructure.db.postgres.models import RefreshTokenModel
from src.mkge.shared.security import hash_refresh_token


class RefreshTokenRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, user_id: UUID, raw_token: str) -> RefreshTokenModel:
        token = RefreshTokenModel(
            user_id=user_id,
            token_hash=hash_refresh_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
        )
        self._db.add(token)
        await self._db.commit()
        await self._db.refresh(token)
        return token

    async def get_valid(self, raw_token: str) -> RefreshTokenModel | None:
        token_hash = hash_refresh_token(raw_token)
        result = await self._db.execute(
            select(RefreshTokenModel).where(
                RefreshTokenModel.token_hash == token_hash,
                RefreshTokenModel.revoked == False,
                RefreshTokenModel.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()

    async def revoke(self, raw_token: str) -> None:
        token_hash = hash_refresh_token(raw_token)
        await self._db.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.token_hash == token_hash)
            .values(revoked=True)
        )
        await self._db.commit()

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        await self._db.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == user_id, RefreshTokenModel.revoked == False)
            .values(revoked=True)
        )
        await self._db.commit()
