"""
Domain entity Chunk theo PROJECT_CONTEXT.md §4.2:
(:Chunk {id, doc_id, page, text, qdrant_id})

Chunk là đơn vị nguyên tử cho:
- Source-of-truth citation (mỗi relationship có source_chunk_ids)
- Vector search (mỗi chunk có 1 embedding trong Qdrant)
- Anti-hallucination: edge Neo4j BẮT BUỘC có source_chunk_ids non-empty
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class Chunk(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    document_id: uuid.UUID
    page: int  # 1-indexed page number
    text: str
    qdrant_id: uuid.UUID | None = None  # set sau khi Qdrant upsert
    created_at: datetime = Field(default_factory=datetime.utcnow)
