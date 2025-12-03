"""
Tests for Authentication Module
اختبارات وحدة المصادقة
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from jose import jwt, JWTError

from sahool_shared.auth.jwt import JWTHandler, TokenPayload
from sahool_shared.auth.password import hash_password, verify_password, needs_rehash


class TestJWTHandler:
    """Tests for JWT token handling."""

    @pytest.fixture
    def jwt_handler(self):
        """Create JWT handler for testing."""
        return JWTHandler(
            secret_key="test-secret-key-for-testing",
            refresh_secret_key="test-refresh-secret-key",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7,
        )

    def test_create_access_token(self, jwt_handler):
        """Test access token creation."""
        user_id = str(uuid4())
        tenant_id = str(uuid4())

        token = jwt_handler.create_access_token(user_id, tenant_id, "admin")

        assert token is not None
        assert isinstance(token, str)

        # Decode and verify
        payload = jwt.decode(token, jwt_handler.secret_key, algorithms=["HS256"])
        assert payload["sub"] == user_id
        assert payload["tenant_id"] == tenant_id
        assert payload["role"] == "admin"
        assert payload["type"] == "access"

    def test_create_refresh_token(self, jwt_handler):
        """Test refresh token creation."""
        user_id = str(uuid4())
        tenant_id = str(uuid4())

        token = jwt_handler.create_refresh_token(user_id, tenant_id, "viewer")

        assert token is not None

        payload = jwt.decode(token, jwt_handler.refresh_secret_key, algorithms=["HS256"])
        assert payload["type"] == "refresh"

    def test_verify_valid_token(self, jwt_handler):
        """Test verification of valid token."""
        user_id = str(uuid4())
        tenant_id = str(uuid4())

        token = jwt_handler.create_access_token(user_id, tenant_id, "manager")
        payload = jwt_handler.verify_token(token, "access")

        assert isinstance(payload, TokenPayload)
        assert payload.sub == user_id
        assert payload.tenant_id == tenant_id
        assert payload.role == "manager"

    def test_verify_invalid_token(self, jwt_handler):
        """Test verification of invalid token."""
        with pytest.raises(JWTError):
            jwt_handler.verify_token("invalid-token", "access")

    def test_verify_wrong_token_type(self, jwt_handler):
        """Test verification with wrong token type."""
        token = jwt_handler.create_refresh_token(str(uuid4()), str(uuid4()), "user")

        with pytest.raises(JWTError) as exc_info:
            jwt_handler.verify_token(token, "access")

        assert "Invalid token type" in str(exc_info.value)

    def test_create_token_pair(self, jwt_handler):
        """Test creation of token pair."""
        user_id = str(uuid4())
        tenant_id = str(uuid4())

        tokens = jwt_handler.create_token_pair(user_id, tenant_id, "analyst")

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"

    def test_token_expiration(self, jwt_handler):
        """Test token has correct expiration."""
        token = jwt_handler.create_access_token(str(uuid4()), str(uuid4()), "user")
        payload = jwt.decode(token, jwt_handler.secret_key, algorithms=["HS256"])

        exp = datetime.fromtimestamp(payload["exp"])
        iat = datetime.fromtimestamp(payload["iat"])

        # Should expire in ~30 minutes
        diff = exp - iat
        assert 29 <= diff.total_seconds() / 60 <= 31


class TestPasswordHashing:
    """Tests for password hashing."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_verify_correct_password(self):
        """Test verification of correct password."""
        password = "MyPassword456"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """Test verification of wrong password."""
        password = "CorrectPassword"
        wrong_password = "WrongPassword"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_different_hashes_for_same_password(self):
        """Test that same password produces different hashes (salt)."""
        password = "SamePassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        # But both should verify
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_needs_rehash_current_algorithm(self):
        """Test rehash not needed for current algorithm."""
        password = "TestPassword"
        hashed = hash_password(password)

        # Current bcrypt with 12 rounds shouldn't need rehash
        assert needs_rehash(hashed) is False


class TestTokenPayload:
    """Tests for TokenPayload model."""

    def test_token_payload_creation(self):
        """Test TokenPayload creation."""
        payload = TokenPayload(
            sub="user-123",
            tenant_id="tenant-456",
            role="admin",
            type="access",
            exp=datetime.utcnow() + timedelta(hours=1),
            iat=datetime.utcnow(),
            jti="unique-token-id"
        )

        assert payload.sub == "user-123"
        assert payload.tenant_id == "tenant-456"
        assert payload.role == "admin"
