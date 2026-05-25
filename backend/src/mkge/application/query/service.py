"""
GraphRAG Query Service.
"""
import json
import logging
import time
import uuid
from typing import Any

from neo4j import AsyncDriver
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from src.mkge.config import settings
from src.mkge.infrastructure.db.neo4j.graph_repo import GraphRepository
from src.mkge.infrastructure.db.qdrant.vector_repo import VectorRepository
from src.mkge.infrastructure.db.postgres.query_history_repo import QueryHistoryRepository
from src.mkge.application.pipeline.embedder import embed_text
from src.mkge.infrastructure.llm.llm_generator import generate_graphrag_answer

logger = logging.getLogger(__name__)


class GraphRAGQueryService:
    def __init__(self, neo4j_driver: AsyncDriver, db: AsyncSession | None = None):
        self.graph_repo = GraphRepository(neo4j_driver)
        self.vector_repo = VectorRepository()
        self.redis = redis.from_url(settings.redis_url, decode_responses=True)
        self._db = db

    async def query(
        self,
        question: str,
        user_id: str | None = None,
        top_k: int = 20,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        start_time = time.monotonic()

        cache_key = f"query:{question}:{top_k}:{temperature}"
        if user_id:
            cache_key = f"query:{user_id}:{question}:{top_k}:{temperature}"

        try:
            cached = await self.redis.get(cache_key)
            if cached:
                logger.info("Cache hit for query: %s", question)
                result = json.loads(cached)
                await self._save_history(user_id, question, result.get("answer"), start_time)
                return result
        except Exception as e:
            logger.warning("Redis cache error: %s", e)

        # 1. Embed query
        logger.info("Embedding query: %s", question)
        query_vector = embed_text(question, task_type="RETRIEVAL_QUERY")

        # 2. Search Qdrant for semantic chunks
        uid = uuid.UUID(user_id) if user_id else None
        chunks = self.vector_repo.search(query_vector, top_k=top_k, user_id=uid)

        # If no relevant chunks were found, return a helpful message early
        if not chunks:
            logger.info("No relevant chunks found for query; returning fallback answer.")
            result = {
                "answer": "Không tìm thấy thông tin liên quan trong tài liệu hiện có.",
                "subgraph": {"nodes": [], "edges": []},
                "citations": [],
            }
            try:
                await self.redis.set(cache_key, json.dumps(result), ex=3600)
            except Exception as e:
                logger.warning("Redis cache set error: %s", e)
            await self._save_history(user_id, question, result["answer"], start_time)
            return result

        # 3. Extract entity IDs from retrieved chunks
        entity_ids: set[str] = set()
        for chunk in chunks:
            eids = chunk.get("entity_ids", [])
            entity_ids.update(eids)

        # 4. Fetch subgraph for these entities
        subgraph: dict[str, Any] = {"nodes": [], "edges": []}
        if entity_ids:
            subgraph = await self.graph_repo.get_subgraph_by_entities(list(entity_ids))

        # 5. Prepare context for LLM
        context_parts = ["--- TEXT EXCERPTS ---"]
        for i, chunk in enumerate(chunks, 1):
            text = chunk.get("text", "")
            page = chunk.get("page", "?")
            doc_id = chunk.get("doc_id", "")
            doc_title = doc_id
            context_parts.append(f"[Excerpt {i} - Page {page} - Doc {doc_title}]: {text}")

        context_parts.append("\n--- MEDICAL ENTITIES AND RELATIONSHIPS (GRAPH) ---")
        for edge in subgraph.get("edges", []):
            s = next((n for n in subgraph["nodes"] if n["id"] == edge["source"]), None)
            t = next((n for n in subgraph["nodes"] if n["id"] == edge["target"]), None)
            if s and t:
                rel_type = edge.get("type", "")
                context_parts.append(
                    f"{s['name']} ({s['type']}) -[{rel_type}]-> {t['name']} ({t['type']})"
                )

        context_text = "\n".join(context_parts)

        # 6. Generate answer using LLM
        answer = generate_graphrag_answer(question, context_text, temperature=temperature)
        if not answer or not answer.strip():
            logger.warning("LLM returned empty answer; using fallback message.")
            answer = "Không có thông tin phù hợp để trả lời câu hỏi này."

        # Determine if answer indicates no information was found
        answer_lower = answer.lower()
        negative_keywords = [
            "không có thông tin",
            "không tìm thấy",
            "không biết",
            "không đề cập",
            "không cung cấp",
            "chưa đề cập",
            "không nhắc đến",
            "don't know",
            "do not know",
            "not mentioned",
            "no information",
            "insufficient information",
            "unable to answer",
        ]
        has_no_info = any(kw in answer_lower for kw in negative_keywords)

        # 7. Assemble result
        result = {
            "answer": answer,
            "subgraph": subgraph,
            "citations": [] if has_no_info else chunks,
        }

        # Cache result for 1 hour (3600 seconds)
        try:
            await self.redis.set(cache_key, json.dumps(result), ex=3600)
        except Exception as e:
            logger.warning("Redis cache set error: %s", e)

        await self._save_history(user_id, question, answer, start_time)
        return result

    # ------------------------------------------------------------------
    async def _save_history(
        self,
        user_id: str | None,
        question: str,
        answer: str | None,
        start_time: float,
    ) -> None:
        """Persist query to Postgres query_history table (best-effort)."""
        if not user_id or not self._db:
            return
        latency_ms = int((time.monotonic() - start_time) * 1000)
        try:
            repo = QueryHistoryRepository(self._db)
            await repo.create(
                user_id=uuid.UUID(user_id),
                question=question,
                answer=answer,
                latency_ms=latency_ms,
            )
        except Exception as e:
            logger.warning("Failed to persist query history: %s", e)

        try:
            from src.mkge.infrastructure.db.postgres.audit_repo import AuditRepository
            from src.mkge.domain.value_objects.audit import AuditAction
            audit_repo = AuditRepository(self._db)
            await audit_repo.create(
                user_id=uuid.UUID(user_id),
                action=AuditAction.QUERY_GRAPHRAG,
                details=f"Question: '{question[:200]}...', Latency: {latency_ms}ms",
            )
        except Exception as e:
            logger.warning("Failed to log audit for query: %s", e)
