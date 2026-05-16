from src.mkge.infrastructure.celery_app import celery_app


@celery_app.task(bind=True, name="pipeline.process_document", max_retries=2)
def process_document(self, document_id: str) -> dict:
    """Phase 0 stub — replaced in Phase 2."""
    import time
    time.sleep(5)
    return {"document_id": document_id, "status": "done"}
