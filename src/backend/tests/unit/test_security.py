"""JWT thuần logic — không cần DB (PLAN task 2.1)."""

from __future__ import annotations

import uuid

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import (
    TokenError,
    TokenExpiredError,
    create_access_token,
    decode_access_token,
)


def test_access_token_round_trip_giu_dung_claims() -> None:
    user_id = uuid.uuid4()
    token = create_access_token(user_id, auth_version=3)

    payload = decode_access_token(token)

    assert payload.sub == user_id
    assert payload.auth_version == 3

    claims = jwt.get_unverified_claims(token)
    assert set(claims) == {"sub", "iat", "exp", "auth_version"}


def test_token_het_han_bi_bao_loi_rieng() -> None:
    claims = {"sub": str(uuid.uuid4()), "iat": 0, "exp": 1, "auth_version": 1}
    expired_token = jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(TokenExpiredError):
        decode_access_token(expired_token)


def test_token_sai_secret_bi_tu_choi() -> None:
    token = create_access_token(uuid.uuid4(), auth_version=1)
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

    with pytest.raises(TokenError):
        decode_access_token(tampered)


def test_token_thieu_claim_bi_tu_choi() -> None:
    claims = {"sub": str(uuid.uuid4())}
    token = jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(TokenError):
        decode_access_token(token)
