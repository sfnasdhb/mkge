import uuid
from datetime import datetime, timezone
from typing import Sequence
from fastapi import UploadFile

from src.mkge.domain.entities.document import Document, DocumentStatus
from src.mkge.domain.exceptions import NotFoundError, ValidationError, AuthorizationError
from src.mkge.infrastructure.db.neo4j.driver import get_driver
from src.mkge.infrastructure.db.neo4j.graph_repo import GraphRepository
from src.mkge.infrastructure.db.postgres.document_repo import DocumentRepository
from src.mkge.infrastructure.db.postgres.audit_repo import AuditRepository
from src.mkge.domain.value_objects.audit import AuditAction
from src.mkge.infrastructure.storage.local import LocalStorageService
from src.mkge.interface.workers.tasks import process_document
from src.mkge.config import settings

class DocumentService:
    def __init__(self, document_repo: DocumentRepository, storage_service: LocalStorageService):
        self.document_repo = document_repo
        self.storage_service = storage_service

    async def upload_document(self, user_id: uuid.UUID, file: UploadFile) -> Document:
        if file.size and file.size > settings.max_upload_size_mb * 1024 * 1024:
            raise ValidationError(f"File size exceeds {settings.max_upload_size_mb}MB limit.")

        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise ValidationError("Only PDF files are supported.")

        document_id = uuid.uuid4()
        file_path = await self.storage_service.save_file(str(document_id), file)

        # we don't always have file.size initially, try to get from file.file or os
        import os
        file_size = os.path.getsize(file_path)

        doc = Document(
            id=document_id,
            user_id=user_id,
            filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            status=DocumentStatus.queued,
            created_at=datetime.now(timezone.utc),
        )
        
        created_doc = await self.document_repo.create(doc)

        audit_repo = AuditRepository(self.document_repo.session)
        await audit_repo.create(
            user_id=user_id,
            action=AuditAction.UPLOAD_DOCUMENT,
            details=f"Uploaded document {created_doc.id} with filename '{created_doc.filename}'",
        )
        
        # enqueue celery task
        process_document.delay(str(document_id))
        
        return created_doc

    async def list_documents(self, user_id: uuid.UUID, user_role: str) -> Sequence[Document]:
        if user_role == "admin":
            return await self.document_repo.get_all()
        return await self.document_repo.get_all_by_user(user_id)

    async def get_document(self, document_id: uuid.UUID, user_id: uuid.UUID, user_role: str) -> Document:
        doc = await self.document_repo.get(document_id)
        if not doc:
            raise NotFoundError("Document not found")
            
        if doc.user_id != user_id and user_role != "admin":
            raise AuthorizationError("Not authorized to view this document")
            
        return doc

    async def delete_document(self, document_id: uuid.UUID, user_id: uuid.UUID, user_role: str) -> None:
        doc = await self.document_repo.get(document_id)
        if not doc:
            raise NotFoundError("Document not found")
            
        if doc.user_id != user_id and user_role != "admin":
            raise AuthorizationError("Not authorized to delete this document")
            
        self.storage_service.delete_file(doc.file_path)
        try:
            graph_repo = GraphRepository(get_driver())
            await graph_repo.delete_graph_for_document(document_id)
        except Exception:
            pass  # Neo4j cleanup failure should not block PostgreSQL delete
        try:
            from src.mkge.infrastructure.db.qdrant.vector_repo import VectorRepository
            VectorRepository().delete_by_document(document_id)
        except Exception:
            pass  # Qdrant cleanup failure non-blocking
        await self.document_repo.delete(document_id)

        audit_repo = AuditRepository(self.document_repo.session)
        await audit_repo.create(
            user_id=user_id,
            action=AuditAction.DELETE_DOCUMENT,
            details=f"Deleted document {document_id} with filename '{doc.filename}' (performed by role '{user_role}')",
        )
