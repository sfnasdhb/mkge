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
    token: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> UserModel:
    raw_token = None
    if credentials:
        raw_token = credentials.credentials
    elif token:
        raw_token = token

    if not raw_token:
        raise AuthenticationError("Missing authorization header or token")

    try:
        payload = decode_access_token(raw_token)
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


def get_document_service(db: AsyncSession = Depends(get_db)):
    from src.mkge.infrastructure.db.postgres.document_repo import DocumentRepository
    from src.mkge.infrastructure.storage.local import LocalStorageService
    from src.mkge.application.documents.services import DocumentService
    
    repo = DocumentRepository(db)
    storage = LocalStorageService()
    return DocumentService(repo, storage)


def get_audit_repository(db: AsyncSession = Depends(get_db)):
    from src.mkge.infrastructure.db.postgres.audit_repo import AuditRepository
    return AuditRepository(db)


def get_admin_service(db: AsyncSession = Depends(get_db)):
    from src.mkge.infrastructure.db.postgres.user_repo import UserRepository
    from src.mkge.infrastructure.db.postgres.document_repo import DocumentRepository
    from src.mkge.infrastructure.db.postgres.audit_repo import AuditRepository
    from src.mkge.infrastructure.storage.local import LocalStorageService
    from src.mkge.infrastructure.db.neo4j.driver import get_driver
    from src.mkge.application.admin.services import AdminService

    user_repo = UserRepository(db)
    document_repo = DocumentRepository(db)
    audit_repo = AuditRepository(db)
    storage = LocalStorageService()
    driver = get_driver()
    return AdminService(user_repo, document_repo, audit_repo, storage, driver, db)

