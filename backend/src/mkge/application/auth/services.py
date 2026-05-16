from sqlalchemy.ext.asyncio import AsyncSession

from src.mkge.domain.exceptions import AuthenticationError, ConflictError
from src.mkge.infrastructure.db.postgres.user_repo import UserRepository
from src.mkge.infrastructure.db.postgres.token_repo import RefreshTokenRepository
from src.mkge.shared.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    verify_password,
)


class AuthService:
    def __init__(self, db: AsyncSession):
        self._users = UserRepository(db)
        self._tokens = RefreshTokenRepository(db)

    async def register(self, email: str, password: str, full_name: str, role: str = "researcher") -> dict:
        if await self._users.get_by_email(email):
            raise ConflictError("Email already registered")

        user = await self._users.create(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=role,
        )
        access_token = create_access_token(str(user.id), user.role)
        refresh_token = generate_refresh_token()
        await self._tokens.create(user.id, refresh_token)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": _user_dict(user),
        }

    async def login(self, email: str, password: str) -> dict:
        user = await self._users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("Account is disabled")

        access_token = create_access_token(str(user.id), user.role)
        refresh_token = generate_refresh_token()
        await self._tokens.create(user.id, refresh_token)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": _user_dict(user),
        }

    async def refresh(self, raw_refresh_token: str) -> dict:
        token_record = await self._tokens.get_valid(raw_refresh_token)
        if not token_record:
            raise AuthenticationError("Invalid or expired refresh token")

        await self._tokens.revoke(raw_refresh_token)

        user = await self._users.get_by_id(token_record.user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User not found or disabled")

        access_token = create_access_token(str(user.id), user.role)
        new_refresh_token = generate_refresh_token()
        await self._tokens.create(user.id, new_refresh_token)

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    async def logout(self, raw_refresh_token: str) -> None:
        await self._tokens.revoke(raw_refresh_token)


def _user_dict(user) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
    }
