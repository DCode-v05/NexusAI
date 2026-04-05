"""Unit tests for src.auth.service — token creation, verification, and blacklist."""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-32ch")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://skip:skip@localhost/skip")

import pytest
from datetime import timedelta
from jose import jwt

from src.auth.service import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from src.config import settings


# ── Password hashing ──────────────────────────────────────────────────────────

class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = get_password_hash("mysecret")
        assert hashed != "mysecret"

    def test_correct_password_verifies(self):
        hashed = get_password_hash("correct-horse-battery")
        assert verify_password("correct-horse-battery", hashed) is True

    def test_wrong_password_fails(self):
        hashed = get_password_hash("correct-horse-battery")
        assert verify_password("wrong-password", hashed) is False

    def test_empty_password_hashes(self):
        hashed = get_password_hash("")
        assert isinstance(hashed, str)
        assert len(hashed) > 0


# ── Access token ──────────────────────────────────────────────────────────────

class TestAccessToken:
    def test_creates_jwt(self):
        token = create_access_token({"sub": "42"})
        assert isinstance(token, str)
        assert token.count(".") == 2  # JWT format: header.payload.signature

    def test_decodes_correctly(self):
        token = create_access_token({"sub": "42"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload["sub"] == "42"

    def test_has_jti_claim(self):
        token = create_access_token({"sub": "1"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert "jti" in payload
        assert len(payload["jti"]) == 36  # UUID4 length

    def test_type_is_access(self):
        token = create_access_token({"sub": "1"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload["type"] == "access"

    def test_has_expiry(self):
        token = create_access_token({"sub": "1"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert "exp" in payload

    def test_custom_expiry(self):
        token = create_access_token({"sub": "1"}, expires_delta=timedelta(minutes=5))
        token_long = create_access_token({"sub": "1"}, expires_delta=timedelta(hours=1))
        p1 = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        p2 = jwt.decode(token_long, settings.SECRET_KEY, algorithms=["HS256"])
        assert p2["exp"] > p1["exp"]

    def test_each_token_has_unique_jti(self):
        t1 = create_access_token({"sub": "1"})
        t2 = create_access_token({"sub": "1"})
        p1 = jwt.decode(t1, settings.SECRET_KEY, algorithms=["HS256"])
        p2 = jwt.decode(t2, settings.SECRET_KEY, algorithms=["HS256"])
        assert p1["jti"] != p2["jti"]


# ── Refresh token ─────────────────────────────────────────────────────────────

class TestRefreshToken:
    def test_creates_jwt(self):
        token = create_refresh_token({"sub": "42"})
        assert isinstance(token, str)

    def test_type_is_refresh(self):
        token = create_refresh_token({"sub": "42"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload["type"] == "refresh"

    def test_refresh_expires_later_than_access(self):
        access = create_access_token({"sub": "1"})
        refresh = create_refresh_token({"sub": "1"})
        pa = jwt.decode(access, settings.SECRET_KEY, algorithms=["HS256"])
        pr = jwt.decode(refresh, settings.SECRET_KEY, algorithms=["HS256"])
        assert pr["exp"] > pa["exp"]

    def test_has_jti(self):
        token = create_refresh_token({"sub": "1"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert "jti" in payload


# ── Config validation ─────────────────────────────────────────────────────────

class TestConfig:
    def test_secret_key_is_set(self):
        assert len(settings.SECRET_KEY) >= 32

    def test_access_token_expire_minutes_positive(self):
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0

    def test_refresh_token_expire_days_positive(self):
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS > 0
