"""
Qdrant Vector Repository theo PROJECT_CONTEXT.md §4.3.

Collection: medical_chunks
Vector: 768 dim, Cosine
Payload: chunk_id, doc_id, user_id, page, text, entity_ids
"""
import logging
import uuid
from typing import Sequence

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    Filter,
    FieldCondition,
    MatchValue,
    PointStruct,
    VectorParams,
)

from src.mkge.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "medical_chunks"


class VectorRepository:
    def __init__(self) -> None:
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=30,
        )

    def ensure_collection(self) -> None:
        existing = {c.name for c in self.client.get_collections().collections}
        if COLLECTION_NAME in existing:
            return
        self.client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=settings.embedding_dims,
                distance=Distance.COSINE,
            ),
        )
        logger.info("Qdrant collection '%s' created", COLLECTION_NAME)

    def upsert_chunks(
        self,
        *,
        chunk_ids: Sequence[uuid.UUID],
        doc_id: uuid.UUID,
        user_id: uuid.UUID,
        pages: Sequence[int],
        texts: Sequence[str],
        entity_ids_per_chunk: Sequence[Sequence[uuid.UUID]],
        vectors: Sequence[Sequence[float]],
    ) -> None:
        assert len(chunk_ids) == len(pages) == len(texts) == len(vectors) == len(entity_ids_per_chunk)
        if not chunk_ids:
            return

        points = [
            PointStruct(
                id=str(cid),
                vector=list(vec),
                payload={
                    "chunk_id": str(cid),
                    "doc_id": str(doc_id),
                    "user_id": str(user_id),
                    "page": page,
                    "text": text,
                    "entity_ids": [str(eid) for eid in eids],
                },
            )
            for cid, page, text, eids, vec in zip(
                chunk_ids, pages, texts, entity_ids_per_chunk, vectors
            )
        ]
        self.client.upsert(collection_name=COLLECTION_NAME, points=points)
        logger.info("Qdrant upsert: %d chunk(s)", len(points))

    def delete_by_document(self, doc_id: uuid.UUID) -> None:
        self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=str(doc_id)))]
            ),
        )

    def search(
        self,
        query_vector: Sequence[float],
        top_k: int = 5,
        user_id: uuid.UUID | None = None,
    ) -> list[dict]:
        flt = None
        if user_id:
            flt = Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=str(user_id)))]
            )
        results = self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=list(query_vector),
            limit=top_k,
            query_filter=flt,
        )
        return [{"score": r.score, **(r.payload or {})} for r in results]
