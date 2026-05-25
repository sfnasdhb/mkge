import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.mkge.application.auth.services import AuthService
from src.mkge.domain.exceptions import AuthenticationError, ConflictError


@pytest.mark.anyio
@patch("src.mkge.application.auth.services.UserRepository")
@patch("src.mkge.application.auth.services.RefreshTokenRepository")
@patch("src.mkge.application.auth.services.AuditRepository")
async def test_register_success(mock_audit_repo, mock_token_repo, mock_user_repo):
    db_mock = MagicMock()
    
    # Mock repositories
    user_repo_instance = mock_user_repo.return_value
    user_repo_instance.get_by_email = AsyncMock(return_value=None)
    
    fake_user = MagicMock()
    fake_user.id = "user-uuid"
    fake_user.role = "researcher"
    fake_user.email = "test@example.com"
    fake_user.full_name = "Test User"
    fake_user.is_active = True
    fake_user.created_at.isoformat.return_value = "2026-05-25T00:00:00"
    
    user_repo_instance.create = AsyncMock(return_value=fake_user)
    
    token_repo_instance = mock_token_repo.return_value
    token_repo_instance.create = AsyncMock()
    
    audit_repo_instance = mock_audit_repo.return_value
    audit_repo_instance.create = AsyncMock()

    service = AuthService(db_mock)
    res = await service.register("test@example.com", "password123", "Test User")
    
    assert res["access_token"] is not None
    assert res["refresh_token"] is not None
    assert res["user"]["email"] == "test@example.com"
    
    user_repo_instance.get_by_email.assert_called_once_with("test@example.com")
    user_repo_instance.create.assert_called_once()
    token_repo_instance.create.assert_called_once()
    audit_repo_instance.create.assert_called_once()


@pytest.mark.anyio
@patch("src.mkge.application.auth.services.UserRepository")
@patch("src.mkge.application.auth.services.RefreshTokenRepository")
async def test_register_conflict(mock_token_repo, mock_user_repo):
    db_mock = MagicMock()
    
    user_repo_instance = mock_user_repo.return_value
    user_repo_instance.get_by_email = AsyncMock(return_value=MagicMock())  # User already exists

    service = AuthService(db_mock)
    with pytest.raises(ConflictError):
        await service.register("test@example.com", "password123", "Test User")


@pytest.mark.anyio
@patch("src.mkge.application.auth.services.UserRepository")
@patch("src.mkge.application.auth.services.RefreshTokenRepository")
@patch("src.mkge.application.auth.services.AuditRepository")
async def test_login_success(mock_audit_repo, mock_token_repo, mock_user_repo):
    db_mock = MagicMock()
    
    user_repo_instance = mock_user_repo.return_value
    
    fake_user = MagicMock()
    fake_user.id = "user-uuid"
    fake_user.role = "researcher"
    fake_user.email = "test@example.com"
    fake_user.full_name = "Test User"
    fake_user.is_active = True
    # mock password matching
    from src.mkge.shared.security import hash_password
    fake_user.password_hash = hash_password("password123")
    fake_user.created_at.isoformat.return_value = "2026-05-25T00:00:00"
    
    user_repo_instance.get_by_email = AsyncMock(return_value=fake_user)
    
    token_repo_instance = mock_token_repo.return_value
    token_repo_instance.create = AsyncMock()
    
    audit_repo_instance = mock_audit_repo.return_value
    audit_repo_instance.create = AsyncMock()

    service = AuthService(db_mock)
    res = await service.login("test@example.com", "password123")
    
    assert res["access_token"] is not None
    assert res["user"]["email"] == "test@example.com"
    audit_repo_instance.create.assert_called_once()


@pytest.mark.anyio
@patch("src.mkge.application.auth.services.UserRepository")
@patch("src.mkge.application.auth.services.RefreshTokenRepository")
async def test_login_disabled_account(mock_token_repo, mock_user_repo):
    db_mock = MagicMock()
    
    user_repo_instance = mock_user_repo.return_value
    
    fake_user = MagicMock()
    fake_user.is_active = False  # Account is disabled
    from src.mkge.shared.security import hash_password
    fake_user.password_hash = hash_password("password123")
    
    user_repo_instance.get_by_email = AsyncMock(return_value=fake_user)

    service = AuthService(db_mock)
    with pytest.raises(AuthenticationError, match="Account is disabled"):
        await service.login("test@example.com", "password123")
