"""
Celery task: process_document
Pipeline 1 (PROJECT_CONTEXT §9):
  parse_pdf → extract_entities → verify → generate_embeddings → persist_graph → update_status
"""
import asyncio
import logging
import uuid
from datetime import datetime, timezone

from neo4j import AsyncGraphDatabase
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.mkge.application.pipeline.embedder import embed_batch
from src.mkge.application.pipeline.service import build_extraction_result
from src.mkge.config import settings
from src.mkge.infrastructure.celery_app import celery_app
from src.mkge.infrastructure.db.neo4j.graph_repo import GraphRepository
from src.mkge.infrastructure.db.postgres.document_repo import DocumentRepository
from src.mkge.infrastructure.db.qdrant.vector_repo import VectorRepository

logger = logging.getLogger(__name__)


async def _update_status(document_id: str, status: str, error_message: str | None = None) -> None:
    engine = create_async_engine(settings.async_database_url, poolclass=NullPool)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_maker() as session:
            repo = DocumentRepository(session)
            await repo.update_status(uuid.UUID(document_id), status, error_message)
    finally:
        await engine.dispose()


async def _finalize_document(
    document_id: str, status: str, entity_count: int, relation_count: int,
    error_message: str | None = None,
) -> None:
    engine = create_async_engine(settings.async_database_url, poolclass=NullPool)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_maker() as session:
            repo = DocumentRepository(session)
            await repo.update_processing_result(
                document_id=uuid.UUID(document_id),
                status=status,
                entity_count=entity_count,
                relation_count=relation_count,
                processed_at=datetime.now(timezone.utc),
                error_message=error_message,
            )
    finally:
        await engine.dispose()


async def _get_doc_info(document_id: str) -> tuple[str, uuid.UUID, str] | None:
    """Return (file_path, user_id, filename) or None."""
    engine = create_async_engine(settings.async_database_url, poolclass=NullPool)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_maker() as session:
            repo = DocumentRepository(session)
            doc = await repo.get(uuid.UUID(document_id))
            if not doc:
                return None
            return doc.file_path, doc.user_id, doc.filename
    finally:
        await engine.dispose()


async def _persist_to_neo4j(
    document_id: uuid.UUID,
    user_id: uuid.UUID,
    filename: str,
    result,  # ExtractionResult
) -> None:
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        repo = GraphRepository(driver)
        await repo.ensure_constraints()
        await repo.upsert_document(document_id, user_id, filename)
        await repo.create_chunks_batch(result.chunks)
        await repo.create_entities_batch(result.entities)
        await repo.create_mentions_batch(result.mentions)
        await repo.create_relationships_batch(result.relationships)
    finally:
        await driver.close()


def _persist_to_qdrant(
    document_id: uuid.UUID,
    user_id: uuid.UUID,
    result,  # ExtractionResult
) -> None:
    """Embed mỗi chunk, upsert Qdrant. Sync vì qdrant-client là sync."""
    if not result.chunks:
        return
    if not settings.qdrant_url or not settings.qdrant_api_key:
        logger.warning("Qdrant không cấu hình — skip embedding step")
        return

    # Map chunk → list entity_ids (qua mentions)
    chunk_entities: dict[uuid.UUID, list[uuid.UUID]] = {c.id: [] for c in result.chunks}
    for chunk_id, entity_id in result.mentions:
        chunk_entities.setdefault(chunk_id, []).append(entity_id)

    texts = [c.text for c in result.chunks]
    try:
        vectors = embed_batch(texts)
    except Exception as exc:
        logger.warning("Embedding failed: %s — skip Qdrant", exc)
        return

    vrepo = VectorRepository()
    try:
        vrepo.ensure_collection()
        vrepo.upsert_chunks(
            chunk_ids=[c.id for c in result.chunks],
            doc_id=document_id,
            user_id=user_id,
            pages=[c.page for c in result.chunks],
            texts=texts,
            entity_ids_per_chunk=[chunk_entities[c.id] for c in result.chunks],
            vectors=vectors,
        )
    except Exception as exc:
        logger.warning("Qdrant upsert failed: %s", exc)


async def _process(document_id: str) -> dict:
    info = await _get_doc_info(document_id)
    if not info:
        await _finalize_document(document_id, "failed", 0, 0, "Document not found")
        return {"document_id": document_id, "status": "failed"}

    file_path, user_id, filename = info
    doc_uuid = uuid.UUID(document_id)

    try:
        # Stage 1+2: parse + extract + verify (sync inside thread)
        await _update_status(document_id, "parsing")
        result = await asyncio.to_thread(build_extraction_result, file_path, doc_uuid)
        logger.info(
            "Pipeline result: %d chunks, %d entities, %d rels, %d mentions",
            len(result.chunks), len(result.entities),
            len(result.relationships), len(result.mentions),
        )

        await _update_status(document_id, "extracting")
        await _update_status(document_id, "verifying")

        # Stage 4: Qdrant embeddings (sync)
        await asyncio.to_thread(_persist_to_qdrant, doc_uuid, user_id, result)

        # Stage 5: Neo4j persist (async)
        await _persist_to_neo4j(doc_uuid, user_id, filename, result)

        await _finalize_document(
            document_id, "done", len(result.entities), len(result.relationships)
        )
        return {
            "document_id": document_id,
            "status": "done",
            "entity_count": len(result.entities),
            "relation_count": len(result.relationships),
            "chunk_count": len(result.chunks),
        }
    except Exception as e:
        logger.exception("Pipeline failed for document %s", document_id)
        await _finalize_document(document_id, "failed", 0, 0, str(e)[:500])
        return {"document_id": document_id, "status": "failed", "error": str(e)}


@celery_app.task(bind=True, name="pipeline.process_document", max_retries=2)
def process_document(self, document_id: str) -> dict:
    return asyncio.run(_process(document_id))
