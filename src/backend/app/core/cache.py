"""Cache JSON trên Redis cho dữ liệu đọc nhiều (PLAN task 3.5).

Namespace `real_estate:cache:*` tách khỏi `real_estate:rate_limit:*` và khỏi
broker Celery (Phase 4 dùng database Redis riêng), để xóa cache không đụng tới
bộ đếm hay hàng đợi job.

Route thường fail open (ARCHITECTURE §3): Redis lỗi thì đọc thẳng database và
chỉ ghi log, không trả 503 như rate limit của route nhạy cảm. Tạo client mới mỗi
lần gọi vì cùng lý do với `app/core/rate_limit.py`.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from redis.asyncio import from_url as redis_from_url

from app.core.config import settings


logger = logging.getLogger(__name__)

CACHE_PREFIX = "real_estate:cache"


def _full_key(key: str) -> str:
    return f"{CACHE_PREFIX}:{key}"


async def get_json(key: str) -> Any | None:
    redis = redis_from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    try:
        raw = await redis.get(_full_key(key))
    except Exception:
        logger.warning("Đọc cache thất bại, dùng database", extra={"cache_key": key})
        return None
    finally:
        await redis.aclose()
    return json.loads(raw) if raw is not None else None


async def set_json(key: str, value: Any, *, ttl_seconds: int) -> None:
    redis = redis_from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    try:
        await redis.set(_full_key(key), json.dumps(value, ensure_ascii=False), ex=ttl_seconds)
    except Exception:
        logger.warning("Ghi cache thất bại", extra={"cache_key": key})
    finally:
        await redis.aclose()


async def delete(*keys: str) -> None:
    """Gọi sau khi transaction đã commit, để request khác không nạp lại dữ liệu cũ
    vào cache trong lúc transaction còn mở. Nếu xóa thất bại, TTL ngắn giới hạn
    thời gian dữ liệu cũ còn tồn tại."""
    redis = redis_from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    try:
        await redis.delete(*(_full_key(key) for key in keys))
    except Exception:
        logger.warning("Xóa cache thất bại", extra={"cache_keys": list(keys)})
    finally:
        await redis.aclose()
