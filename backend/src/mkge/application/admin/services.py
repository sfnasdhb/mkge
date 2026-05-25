import uuid
import logging
from typing import Any, Sequence
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver

from src.mkge.infrastructure.db.postgres.user_repo import UserRepository
from src.mkge.infrastructure.db.postgres.document_repo import DocumentRepository
from src.mkge.infrastructure.db.postgres.audit_repo import AuditRepository
from src.mkge.infrastructure.db.postgres.query_history_repo import QueryHistoryRepository
from src.mkge.infrastructure.db.postgres.models import QueryHistoryModel, UserModel
from src.mkge.infrastructure.db.neo4j.graph_repo import GraphRepository
from src.mkge.infrastructure.db.qdrant.vector_repo import VectorRepository
from src.mkge.infrastructure.storage.local import LocalStorageService
from src.mkge.domain.exceptions import NotFoundError
from src.mkge.domain.value_objects.audit import AuditAction

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(
        self,
        user_repo: UserRepository,
        document_repo: DocumentRepository,
        audit_repo: AuditRepository,
        storage_service: LocalStorageService,
        neo4j_driver: AsyncDriver,
        db: AsyncSession,
    ):
        self.user_repo = user_repo
        self.document_repo = document_repo
        self.audit_repo = audit_repo
        self.storage_service = storage_service
        self.neo4j_driver = neo4j_driver
        self.db = db

    async def list_users(self, offset: int = 0, limit: int = 50) -> Sequence[UserModel]:
        return await self.user_repo.list_all(offset=offset, limit=limit)

    async def update_user(self, admin_id: uuid.UUID, user_id: uuid.UUID, role: str | None = None, is_active: bool | None = None) -> UserModel:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        old_role = user.role
        old_is_active = user.is_active

        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active

        await self.db.commit()
        await self.db.refresh(user)

        details = f"Updated user {user_id}. Changes: "
        changes = []
        if role is not None and old_role != role:
            changes.append(f"role: {old_role} -> {role}")
        if is_active is not None and old_is_active != is_active:
            changes.append(f"is_active: {old_is_active} -> {is_active}")
        details += ", ".join(changes) if changes else "No changes"

        await self.audit_repo.create(
            user_id=admin_id,
            action=AuditAction.ADMIN_UPDATE_USER,
            details=details,
        )
        return user

    async def delete_user(self, admin_id: uuid.UUID, user_id: uuid.UUID) -> None:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        # 1. List user documents
        docs = await self.document_repo.get_all_by_user(user_id)

        # 2. Clean up files, Neo4j, Qdrant for each document
        for doc in docs:
            # Delete file
            try:
                self.storage_service.delete_file(doc.file_path)
            except Exception as e:
                logger.warning("Failed to delete file %s for document %s: %s", doc.file_path, doc.id, e)

            # Delete Neo4j graph
            try:
                graph_repo = GraphRepository(self.neo4j_driver)
                await graph_repo.delete_graph_for_document(doc.id)
            except Exception as e:
                logger.warning("Failed to delete Neo4j graph for document %s: %s", doc.id, e)

            # Delete Qdrant vectors
            try:
                vector_repo = VectorRepository()
                vector_repo.delete_by_document(doc.id)
            except Exception as e:
                logger.warning("Failed to delete Qdrant vectors for document %s: %s", doc.id, e)

        # 3. Delete Query History (to prevent foreign key constraint violations)
        try:
            await self.db.execute(delete(QueryHistoryModel).where(QueryHistoryModel.user_id == user_id))
            await self.db.commit()
        except Exception as e:
            logger.warning("Failed to delete query history for user %s: %s", user_id, e)

        # 4. Delete user from Postgres (cascades documents and refresh tokens)
        await self.user_repo.delete(user_id)

        await self.audit_repo.create(
            user_id=admin_id,
            action=AuditAction.ADMIN_DELETE_USER,
            details=f"Deleted user {user_id} with email {user.email}",
        )

    async def get_stats(self) -> dict[str, Any]:
        # 1. Total users
        total_users = await self.user_repo.count_all()

        # 2. Total documents + doc status breakdown
        total_documents = await self.document_repo.count_all()
        doc_stats = await self.document_repo.count_by_status()

        # 3. Total queries
        query_history_repo = QueryHistoryRepository(self.db)
        total_queries = await query_history_repo.count_all()

        # 4. Total entities + relationships from Neo4j
        try:
            graph_repo = GraphRepository(self.neo4j_driver)
            overview = await graph_repo.get_overview()
            total_entities = sum(overview.get("entity_counts_by_type", {}).values())
            total_relationships = overview.get("relationship_count", 0)
        except Exception as e:
            logger.warning("Failed to get Neo4j overview stats: %s", e)
            total_entities = 0
            total_relationships = 0

        return {
            "total_users": total_users,
            "total_documents": total_documents,
            "total_queries": total_queries,
            "total_entities": total_entities,
            "total_relationships": total_relationships,
            "document_stats": doc_stats,
        }
