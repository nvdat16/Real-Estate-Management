"""UPDATE có điều kiện theo `row_version` — dùng chung cho mọi repository cần
optimistic locking (SPEC mục 3.1: thiếu `row_version` → 422 do pydantic field
required; `row_version` cũ → 409 `VERSION_CONFLICT` do service raise khi hàm
này trả `False`).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession


async def conditional_update(
    db: AsyncSession,
    model: type[Any],
    record_id: Any,
    expected_row_version: int,
    values: Mapping[str, Any],
) -> bool:
    """`True` nếu update đúng 1 dòng; `False` nếu `row_version` không khớp.

    Các bảng dùng hàm này đều soft-delete (không xóa cứng), nên `False` ở đây
    chỉ có thể là stale version — record không thể biến mất giữa lúc service
    load (đã qua bước 404/scope check) và lúc update.
    """
    stmt = (
        update(model)
        .where(model.id == record_id, model.row_version == expected_row_version)
        .values(**values, row_version=model.row_version + 1)
    )
    result = await db.execute(stmt)
    return result.rowcount == 1  # type: ignore[attr-defined]
