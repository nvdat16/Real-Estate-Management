from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app as main_app
from app.middleware import (
    AppError,
    RateLimit,
    RateLimitMiddleware,
    RequestIDMiddleware,
    register_exception_handlers,
)


class FakePipeline:
    def __init__(self, redis: FakeRedis) -> None:
        self.redis = redis

    def incr(self, key: str) -> FakePipeline:
        self.redis.last_key = key
        return self

    def expire(self, key: str, seconds: int) -> FakePipeline:
        return self

    async def execute(self) -> list[int | bool]:
        if self.redis.unavailable:
            raise ConnectionError("Redis unavailable")
        self.redis.count += 1
        return [self.redis.count, True]


class FakeRedis:
    def __init__(self, *, unavailable: bool = False) -> None:
        self.count = 0
        self.last_key = ""
        self.unavailable = unavailable

    def pipeline(self, transaction: bool = True) -> FakePipeline:
        return FakePipeline(self)


def test_health_has_request_id_without_contacting_redis() -> None:
    with TestClient(main_app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"].startswith("req-")


def test_request_id_is_echoed_and_invalid_value_is_replaced() -> None:
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/")
    async def root() -> dict[str, bool]:
        return {"ok": True}

    client = TestClient(app)
    assert client.get("/", headers={"X-Request-ID": "req-client"}).headers[
        "x-request-id"
    ] == "req-client"
    generated = client.get("/", headers={"X-Request-ID": "bad\nvalue"}).headers[
        "x-request-id"
    ]
    assert generated.startswith("req-")
    assert generated != "bad\nvalue"


def test_app_error_uses_standard_contract() -> None:
    app = FastAPI()
    register_exception_handlers(app)
    app.add_middleware(RequestIDMiddleware)

    @app.get("/conflict")
    async def conflict() -> None:
        raise AppError(
            "VERSION_CONFLICT",
            "Dữ liệu đã thay đổi.",
            status_code=409,
            details={"field": "row_version"},
        )

    response = TestClient(app).get("/conflict")

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "VERSION_CONFLICT",
            "message": "Dữ liệu đã thay đổi.",
            "details": {"field": "row_version"},
        },
        "request_id": response.headers["x-request-id"],
    }


def test_rate_limit_rejects_request_and_hashes_client_identity() -> None:
    app = FastAPI()
    redis = FakeRedis()
    app.add_middleware(
        RateLimitMiddleware,
        redis=redis,
        route_limits={("GET", "/limited"): RateLimit(2, 60)},
        default_limit=None,
        excluded_paths=(),
    )
    app.add_middleware(RequestIDMiddleware)

    @app.get("/limited")
    async def limited() -> dict[str, bool]:
        return {"ok": True}

    client = TestClient(app)
    assert client.get("/limited").status_code == 200
    assert client.get("/limited").status_code == 200
    response = client.get("/limited")

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "RATE_LIMITED"
    assert int(response.headers["retry-after"]) >= 1
    assert "testclient" not in redis.last_key


def test_sensitive_route_fails_closed_when_redis_is_unavailable() -> None:
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        redis=FakeRedis(unavailable=True),
        route_limits={("POST", "/auth/token"): RateLimit(10, 60)},
        default_limit=None,
        excluded_paths=(),
    )
    app.add_middleware(RequestIDMiddleware)

    @app.post("/auth/token")
    async def token() -> dict[str, str]:
        return {"token": "secret"}

    response = TestClient(app).post("/auth/token")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
    assert response.json()["request_id"] == response.headers["x-request-id"]
