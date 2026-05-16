import asyncio
import time
import uuid
from src.mkge.infrastructure.celery_app import celery_app
from src.mkge.infrastructure.db.postgres.database import AsyncSessionLocal
from src.mkge.infrastructure.db.postgres.document_repo import DocumentRepository

async def _update_document_status(document_id: str):
    async with AsyncSessionLocal() as session:
        repo = DocumentRepository(session)
        await repo.update_status(uuid.UUID(document_id), "done")

@celery_app.task(bind=True, name="pipeline.process_document", max_retries=2)
def process_document(self, document_id: str) -> dict:
    """Phase 1 stub — sleep 5s and update status to done."""
    time.sleep(5)
    
    # Update DB
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(_update_document_status(document_id))
    
    return {"document_id": document_id, "status": "done"}
