from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.mkge.infrastructure.db.postgres.models import UserModel


class UserRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_email(self, email: str) -> UserModel | None:
        result = await self._db.execute(select(UserModel).where(UserModel.email == email.lower()))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> UserModel | None:
        result = await self._db.execute(select(UserModel).where(UserModel.id == user_id))
        return result.scalar_one_or_none()

    async def create(self, email: str, password_hash: str, full_name: str, role: str = "researcher") -> UserModel:
        user = UserModel(
            email=email.lower(),
            password_hash=password_hash,
            full_name=full_name,
            role=role,
        )
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def list_all(self, offset: int = 0, limit: int = 50) -> list[UserModel]:
        result = await self._db.execute(select(UserModel).offset(offset).limit(limit))
        return list(result.scalars().all())
