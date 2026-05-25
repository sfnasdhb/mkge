import time
import pytest
from jose import jwt
from src.mkge.shared.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from src.mkge.config import settings


def test_password_hashing():
    password = "MySecurePassword123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword123!", hashed)


def test_access_token_lifecycle():
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    role = "researcher"
    
    token = create_access_token(user_id, role)
    assert token is not None
    
    decoded = decode_access_token(token)
    assert decoded["sub"] == user_id
    assert decoded["role"] == role
    assert "exp" in decoded


def test_expired_token():
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    role = "admin"
    
    # Generate token with negative expiry to simulate expiration
    # We can encode directly using settings.jwt_secret
    payload = {
        "sub": user_id,
        "role": role,
        "exp": int(time.time()) - 10,  # 10 seconds in the past
    }
    expired_token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    
    with pytest.raises(Exception):
        decode_access_token(expired_token)
