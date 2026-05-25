"""FastAPI dependency for per-user rate limiting."""
from fastapi import Depends

from src.mkge.config import settings
from src.mkge.domain.exceptions import RateLimitError
from src.mkge.infrastructure.cache.redis import check_rate_limit
from src.mkge.infrastructure.db.postgres.models import UserModel
from src.mkge.interface.api.deps import get_current_user

_ACTION_LIMITS: dict[str, tuple[str, int]] = {
    "upload": ("rate_limit_upload_per_hour", 3600),
    "query": ("rate_limit_query_per_hour", 3600),
}


class RateLimitDep:
    """Callable FastAPI dependency.

    Usage:
        @router.post("/documents", dependencies=[Depends(RateLimitDep("upload"))])
    """

    def __init__(self, action: str):
        self.action = action

    async def __call__(self, user: UserModel = Depends(get_current_user)) -> None:
        setting_attr, window = _ACTION_LIMITS.get(
            self.action, ("rate_limit_query_per_hour", 3600)
        )
        max_count = getattr(settings, setting_attr, 30)

        allowed, current = await check_rate_limit(
            user_id=str(user.id),
            action=self.action,
            max_count=max_count,
            window_seconds=window,
        )
        if not allowed:
            raise RateLimitError(
                f"Rate limit exceeded: {current}/{max_count} {self.action} requests per hour"
            )
