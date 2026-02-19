"""Tests for security core functions."""

import pytest
from datetime import timedelta

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_password_hashing(self):
        """Test that passwords are hashed and can be verified."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # Hash should be different from plain text
        assert hashed != password
        # Should be able to verify
        assert verify_password(password, hashed) is True
        # Wrong password should fail
        assert verify_password("wrongpassword", hashed) is False

    def test_password_hash_is_salted(self):
        """Test that same password produces different hashes (salting)."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        # Both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTToken:
    """Test JWT token functions."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "1", "email": "test@example.com"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "1"}
        token = create_refresh_token(data)
        
        assert token is not None
        assert isinstance(token, str)

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        data = {"sub": "1", "email": "test@example.com"}
        token = create_access_token(data)
        decoded = decode_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == "1"
        assert decoded["email"] == "test@example.com"
        assert decoded["type"] == "access"

    def test_decode_invalid_token(self):
        """Test decoding an invalid token."""
        decoded = decode_token("invalid_token")
        assert decoded is None

    def test_decode_expired_token(self):
        """Test decoding an expired token."""
        data = {"sub": "1"}
        # Create token that expired 1 hour ago
        token = create_access_token(data, expires_delta=timedelta(hours=-1))
        decoded = decode_token(token)
        
        assert decoded is None

    def test_token_type_distinction(self):
        """Test that access and refresh tokens have different types."""
        access_token = create_access_token({"sub": "1"})
        refresh_token = create_refresh_token({"sub": "1"})
        
        access_decoded = decode_token(access_token)
        refresh_decoded = decode_token(refresh_token)
        
        assert access_decoded["type"] == "access"
        assert refresh_decoded["type"] == "refresh"

    def test_token_contains_expiry(self):
        """Test that tokens contain expiration time."""
        data = {"sub": "1"}
        token = create_access_token(data)
        decoded = decode_token(token)
        
        assert "exp" in decoded
