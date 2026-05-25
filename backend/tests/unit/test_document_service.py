import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import UploadFile
from src.mkge.application.documents.services import DocumentService
from src.mkge.domain.entities.document import Document, DocumentStatus
from src.mkge.domain.exceptions import NotFoundError, ValidationError, AuthorizationError


@pytest.mark.anyio
@patch("src.mkge.application.documents.services.process_document")
@patch("os.path.getsize")
async def test_upload_document_success(mock_getsize, mock_process_task):
    mock_repo = MagicMock()
    mock_repo.create = AsyncMock()
    mock_repo.session = MagicMock()
    
    # Mock AuditRepository
    with patch("src.mkge.application.documents.services.AuditRepository") as mock_audit_repo:
        audit_instance = mock_audit_repo.return_value
        audit_instance.create = AsyncMock()
        
        mock_storage = MagicMock()
        mock_storage.save_file = AsyncMock(return_value="/tmp/file.pdf")
        mock_getsize.return_value = 1024
        
        # Mock UploadFile
        file_mock = MagicMock(spec=UploadFile)
        file_mock.filename = "medical_guide.pdf"
        file_mock.size = 1024
        
        # Mock repo response
        fake_doc = MagicMock(spec=Document)
        fake_doc.id = uuid.uuid4()
        fake_doc.filename = "medical_guide.pdf"
        mock_repo.create.return_value = fake_doc
        
        service = DocumentService(mock_repo, mock_storage)
        user_id = uuid.uuid4()
        
        res = await service.upload_document(user_id, file_mock)
        
        assert res == fake_doc
        mock_storage.save_file.assert_called_once()
        mock_repo.create.assert_called_once()
        mock_process_task.delay.assert_called_once()
        audit_instance.create.assert_called_once()


@pytest.mark.anyio
async def test_upload_document_invalid_extension():
    mock_repo = MagicMock()
    mock_storage = MagicMock()
    
    file_mock = MagicMock(spec=UploadFile)
    file_mock.filename = "medical_guide.docx"  # Not a PDF
    file_mock.size = 1024
    
    service = DocumentService(mock_repo, mock_storage)
    user_id = uuid.uuid4()
    
    with pytest.raises(ValidationError, match="Only PDF files are supported"):
        await service.upload_document(user_id, file_mock)


@pytest.mark.anyio
async def test_get_document_authorization():
    from datetime import datetime, timezone
    mock_repo = MagicMock()
    mock_storage = MagicMock()
    
    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    
    fake_doc = Document(
        id=doc_id,
        user_id=user_id,
        filename="guide.pdf",
        file_path="/tmp/guide.pdf",
        file_size=100,
        status="done",
        created_at=datetime.now(timezone.utc),
    )
    
    mock_repo.get = AsyncMock(return_value=fake_doc)
    service = DocumentService(mock_repo, mock_storage)
    
    # 1. Owner gets document: should succeed
    res = await service.get_document(doc_id, user_id, "researcher")
    assert res == fake_doc
    
    # 2. Non-owner researcher gets document: should raise AuthorizationError
    with pytest.raises(AuthorizationError):
        await service.get_document(doc_id, other_user_id, "researcher")
        
    # 3. Admin gets other user's document: should succeed
    res_admin = await service.get_document(doc_id, other_user_id, "admin")
    assert res_admin == fake_doc
