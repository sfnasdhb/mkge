from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel


class DocumentStatus(str, Enum):
    queued = "queued"
    parsing = "parsing"
    extracting = "extracting"
    verifying = "verifying"
    done = "done"
    failed = "failed"


class Document(BaseModel):
    id: UUID
    user_id: UUID
    filename: str
    file_path: str
    file_size: int
    status: DocumentStatus = DocumentStatus.queued
    error_message: str | None = None
    entity_count: int = 0
    relation_count: int = 0
    created_at: datetime
    processed_at: datetime | None = None
