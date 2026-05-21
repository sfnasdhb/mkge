"""
Domain entities cho Knowledge Graph.
Tuân theo PROJECT_CONTEXT.md §4.2: 3 entity types (Drug, Disease, Symptom)
và 4 relation types (TREATS, CAUSES_SE, HAS_SYMPTOM, COMORBID).
"""
import uuid
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    drug = "DRUG"
    disease = "DISEASE"
    symptom = "SYMPTOM"


class RelationType(str, Enum):
    # Drug → Disease: thuốc điều trị bệnh
    treats = "TREATS"
    # Drug → Symptom: tác dụng phụ thuốc gây triệu chứng
    causes_se = "CAUSES_SE"
    # Disease → Symptom: bệnh biểu hiện qua triệu chứng
    has_symptom = "HAS_SYMPTOM"
    # Disease ↔ Disease: bệnh đồng mắc
    comorbid = "COMORBID"


class MedicalEntity(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    normalized_name: str
    type: EntityType
    document_id: uuid.UUID
    description: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Relationship(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    source_id: uuid.UUID
    target_id: uuid.UUID
    type: RelationType
    document_id: uuid.UUID
    confidence: float = 1.0
    evidence: str | None = None
    # PROJECT_CONTEXT.md §9: mỗi edge BẮT BUỘC có source_chunk_ids non-empty.
    # Phase 2 hiện tại lưu rỗng; Phase 2.5 (Stage 2 của refactor) sẽ điền.
    source_chunk_ids: list[uuid.UUID] = Field(default_factory=list)
