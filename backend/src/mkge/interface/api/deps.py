from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.mkge.domain.exceptions import AuthenticationError, AuthorizationError
from src.mkge.infrastructure.db.postgres.database import get_db
from src.mkge.infrastructure.db.postgres.user_repo import UserRepository
from src.mkge.infrastructure.db.postgres.models import UserModel
from src.mkge.shared.security import decode_access_token

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> UserModel:
    if credentials is None:
        raise AuthenticationError("Missing authorization header")

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError
    except (JWTError, ValueError):
        raise AuthenticationError("Invalid or expired token")

    repo = UserRepository(db)
    user = await repo.get_by_id(UUID(user_id))
    if not user or not user.is_active:
        raise AuthenticationError("User not found or disabled")
    return user


def require_role(*roles: str):
    async def checker(user: UserModel = Depends(get_current_user)) -> UserModel:
        if user.role not in roles:
            raise AuthorizationError("Insufficient permissions")
        return user
    return checker
