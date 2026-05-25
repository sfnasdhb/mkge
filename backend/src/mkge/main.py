from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.mkge.config import settings
from src.mkge.infrastructure.db.neo4j.driver import close_driver
from src.mkge.interface.api.errors import register_exception_handlers
from src.mkge.interface.api.middleware import RequestIdMiddleware
from src.mkge.interface.api.v1 import auth, users, documents, graph, query, health, admin
from src.mkge.shared.logging import setup_logging


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(
        title="MKGE API",
        description="Medical Knowledge Graph Extraction + GraphRAG",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)

    register_exception_handlers(app)

    prefix = "/api/v1"
    app.include_router(health.router)
    app.include_router(auth.router, prefix=prefix)
    app.include_router(users.router, prefix=prefix)
    app.include_router(documents.router, prefix=prefix)
    app.include_router(graph.router, prefix=prefix)
    app.include_router(query.router, prefix=prefix)
    app.include_router(admin.router, prefix=prefix)

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        await close_driver()

    return app


app = create_app()
