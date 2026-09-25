"""Rate limit theo khóa tuỳ ý (ví dụ email đã chuẩn hóa/hash), dùng trong
service — bổ sung cho `RateLimitMiddleware` vốn chỉ giới hạn theo IP (xem
docstring của `app/middleware/rate_limit.py`: "Per-account/email limits belong
in the auth service"). SPEC yêu cầu login 5 lần/phút/email và reset 3 lần/15
phút/email, tách biệt hoàn toàn khỏi giới hạn IP.
"""

from __future__ import annotations

import time

from redis.asyncio import from_url as redis_from_url

from app.core.config import settings
from app.core.exceptions import dependency_unavailable, rate_limited


async def enforce_fixed_window(*, key: str, limit: int, window_seconds: int) -> None:
    """Tạo client Redis mới mỗi lần gọi — KHÔNG cache client ở module scope.

    `redis.asyncio.Redis` gắn với event loop lúc tạo; cache toàn cục sẽ vỡ khi
    loop đổi (ví dụ mỗi test async của pytest-asyncio chạy trên loop riêng),
    và trong production một client sống lâu nên do lifespan của app quản lý
    (như `RateLimitMiddleware` đang làm), không phải một hàm tiện ích như này.
    """
    now = int(time.time())
    window = now // window_seconds
    redis_key = f"real_estate:rate_limit:custom:{key}:{window}"
    redis = redis_from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    try:
        pipeline = redis.pipeline(transaction=True)
        pipeline.incr(redis_key)
        pipeline.expire(redis_key, window_seconds + 1)
        result = await pipeline.execute()
        current = int(result[0])
    except Exception as exc:
        raise dependency_unavailable() from exc
    finally:
        await redis.aclose()

    if current > limit:
        retry_after = max(1, (window + 1) * window_seconds - now)
        raise rate_limited(retry_after)
