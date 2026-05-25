import uuid
from datetime import datetime
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.mkge.domain.entities.document import Document
from src.mkge.infrastructure.db.postgres.models import DocumentModel

class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, document: Document) -> Document:
        db_doc = DocumentModel(
            id=document.id,
            user_id=document.user_id,
            filename=document.filename,
            file_path=document.file_path,
            file_size=document.file_size,
            status=document.status,
            error_message=document.error_message,
            entity_count=document.entity_count,
            relation_count=document.relation_count,
            created_at=document.created_at,
            processed_at=document.processed_at,
        )
        self.session.add(db_doc)
        await self.session.commit()
        await self.session.refresh(db_doc)
        return self._to_domain(db_doc)

    async def get(self, document_id: uuid.UUID) -> Document | None:
        result = await self.session.execute(select(DocumentModel).filter_by(id=document_id))
        db_doc = result.scalar_one_or_none()
        if not db_doc:
            return None
        return self._to_domain(db_doc)

    async def get_all_by_user(self, user_id: uuid.UUID) -> Sequence[Document]:
        result = await self.session.execute(
            select(DocumentModel).filter_by(user_id=user_id).order_by(DocumentModel.created_at.desc())
        )
        return [self._to_domain(doc) for doc in result.scalars().all()]

    async def get_all(self, offset: int = 0, limit: int = 100) -> Sequence[Document]:
        result = await self.session.execute(
            select(DocumentModel).order_by(DocumentModel.created_at.desc()).offset(offset).limit(limit)
        )
        return [self._to_domain(doc) for doc in result.scalars().all()]

    async def count_by_status(self) -> dict[str, int]:
        from sqlalchemy import func
        result = await self.session.execute(
            select(DocumentModel.status, func.count()).group_by(DocumentModel.status)
        )
        return {row[0]: row[1] for row in result.all()}

    async def count_all(self) -> int:
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count()).select_from(DocumentModel)
        )
        return result.scalar_one()

    async def update_status(self, document_id: uuid.UUID, status: str, error_message: str | None = None) -> None:
        db_doc = await self.session.get(DocumentModel, document_id)
        if db_doc:
            db_doc.status = status
            if error_message is not None:
                db_doc.error_message = error_message
            await self.session.commit()

    async def update_processing_result(
        self,
        document_id: uuid.UUID,
        status: str,
        entity_count: int,
        relation_count: int,
        processed_at: datetime,
        error_message: str | None = None,
    ) -> None:
        db_doc = await self.session.get(DocumentModel, document_id)
        if db_doc:
            db_doc.status = status
            db_doc.entity_count = entity_count
            db_doc.relation_count = relation_count
            db_doc.processed_at = processed_at
            db_doc.error_message = error_message
            await self.session.commit()

    async def delete(self, document_id: uuid.UUID) -> None:
        db_doc = await self.session.get(DocumentModel, document_id)
        if db_doc:
            await self.session.delete(db_doc)
            await self.session.commit()

    def _to_domain(self, db_doc: DocumentModel) -> Document:
        return Document(
            id=db_doc.id,
            user_id=db_doc.user_id,
            filename=db_doc.filename,
            file_path=db_doc.file_path,
            file_size=db_doc.file_size,
            status=db_doc.status,
            error_message=db_doc.error_message,
            entity_count=db_doc.entity_count,
            relation_count=db_doc.relation_count,
            created_at=db_doc.created_at,
            processed_at=db_doc.processed_at,
        )
