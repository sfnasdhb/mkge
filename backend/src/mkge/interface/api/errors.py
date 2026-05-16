import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.mkge.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)

logger = structlog.get_logger()


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _error_response(code: str, message: str, status: int, request: Request, details: dict | None = None):
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "request_id": _request_id(request),
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found(request: Request, exc: NotFoundError):
        return _error_response("NOT_FOUND", str(exc), 404, request)

    @app.exception_handler(AuthenticationError)
    async def auth_error(request: Request, exc: AuthenticationError):
        return _error_response("AUTHENTICATION_ERROR", str(exc), 401, request)

    @app.exception_handler(AuthorizationError)
    async def authz_error(request: Request, exc: AuthorizationError):
        return _error_response("FORBIDDEN", str(exc), 403, request)

    @app.exception_handler(ConflictError)
    async def conflict(request: Request, exc: ConflictError):
        return _error_response("CONFLICT", str(exc), 409, request)

    @app.exception_handler(ValidationError)
    async def validation(request: Request, exc: ValidationError):
        return _error_response("VALIDATION_ERROR", str(exc), 422, request)

    @app.exception_handler(Exception)
    async def generic(request: Request, exc: Exception):
        logger.exception("unhandled_exception", path=request.url.path, error=str(exc))
        return _error_response("INTERNAL_ERROR", "An unexpected error occurred", 500, request)
