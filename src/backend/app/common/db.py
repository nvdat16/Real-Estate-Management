"""Truy cập dữ liệu kiểu micro ORM (giống Dapper): SQL viết tay + map sang dataclass.

Module dùng các hàm này (hiện là projects, properties, listings — ADR-011) viết
SQL trực tiếp trong repository, chỉ dùng tham số bind `:ten`, và nhận về dataclass
bất biến thay vì object ORM. Engine, transaction và `AsyncSession` vẫn của
SQLAlchemy nên dùng chung transaction/savepoint với module còn dùng ORM, và
model ORM vẫn là định nghĩa schema cho Alembic.

Quy ước:

- Không nối giá trị người dùng vào SQL. Chỉ tên bảng/cột lấy từ hằng trong code
  (allowlist) mới được đưa vào chuỗi SQL, ví dụ ORDER BY hoặc SET động.
- Không dùng cú pháp ép kiểu `::type` (xung đột với tham số `:ten` của `text()`);
  dùng `CAST(x AS type)`.
- `updated_at` không có ORM `onupdate` hỗ trợ ở đây: mọi UPDATE phải tự đặt
  `updated_at = now()` (hàm `update_versioned` đã làm).
"""

from __future__ import annotations

import dataclasses
import re
from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import RowMapping, text
from sqlalchemy.ext.asyncio import AsyncSession


_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")


def _to_row[T](row_type: type[T], mapping: RowMapping) -> T:
    """Map theo tên cột như Dapper, nhưng chặt hơn: thiếu cột cho một field là lỗi
    (bắt SELECT viết sót cột ngay khi chạy test thay vì trả dữ liệu thiếu)."""
    names = {field.name for field in dataclasses.fields(row_type)}  # type: ignore[arg-type]
    return row_type(**{name: mapping[name] for name in names})


async def query[T](db: AsyncSession, row_type: type[T], sql: str, **params: Any) -> list[T]:
    result = await db.execute(text(sql), params)
    return [_to_row(row_type, row) for row in result.mappings()]


async def query_one[T](db: AsyncSession, row_type: type[T], sql: str, **params: Any) -> T | None:
    result = await db.execute(text(sql), params)
    row = result.mappings().first()
    return _to_row(row_type, row) if row is not None else None


async def scalar(db: AsyncSession, sql: str, **params: Any) -> Any:
    return await db.scalar(text(sql), params)


async def column(db: AsyncSession, sql: str, **params: Any) -> list[Any]:
    """Giá trị cột đầu tiên của mọi dòng, ví dụ danh sách mã role."""
    result = await db.execute(text(sql), params)
    return list(result.scalars())


async def execute(db: AsyncSession, sql: str, **params: Any) -> int:
    """Chạy INSERT/UPDATE/DELETE, trả số dòng bị ảnh hưởng."""
    result = await db.execute(text(sql), params)
    return int(result.rowcount)  # type: ignore[attr-defined]


def identifier(name: str, allowed: Sequence[str]) -> str:
    """Tên cột/bảng động phải nằm trong allowlist của repository."""
    if name not in allowed or not _IDENTIFIER.match(name):
        raise ValueError(f"Tên cột không hợp lệ: {name!r}")
    return name


async def update_versioned(
    db: AsyncSession,
    *,
    table: str,
    record_id: Any,
    expected_row_version: int,
    fields: Mapping[str, Any],
    allowed_columns: Sequence[str],
    increments: Sequence[str] = (),
) -> bool:
    """UPDATE có điều kiện `row_version` (SPEC mục 3.1) bằng SQL tay.

    `increments` là các cột tăng 1 ngay trong SQL (ví dụ `auth_version` khi khóa
    tài khoản) để không phải đọc giá trị cũ rồi ghi lại. `True` nếu đúng 1 dòng
    được cập nhật; `False` nghĩa là `row_version` đã cũ (bản ghi không biến mất
    vì các bảng này chỉ xóa mềm).
    """
    table_name = identifier(table, (table,))
    assignments = [f"{identifier(column, allowed_columns)} = :{column}" for column in fields]
    assignments += [
        f"{identifier(column, allowed_columns)} = {column} + 1" for column in increments
    ]
    assignments += ["row_version = row_version + 1", "updated_at = now()"]
    sql = (
        f"UPDATE {table_name} SET {', '.join(assignments)} "
        "WHERE id = :_id AND row_version = :_expected_row_version"
    )
    params = {**fields, "_id": record_id, "_expected_row_version": expected_row_version}
    return await execute(db, sql, **params) == 1


def order_by(sort: str, columns: Mapping[str, str], tiebreaker: str) -> str:
    """Biến `sort` (đã qua allowlist `Literal[...]` ở router, ví dụ `-created_at`)
    thành mệnh đề ORDER BY; luôn thêm khóa phụ để phân trang ổn định (SPEC 3.1)."""
    column = columns[sort.lstrip("-")]
    direction = "DESC" if sort.startswith("-") else "ASC"
    return f"ORDER BY {column} {direction}, {tiebreaker} ASC"


def where(clauses: Sequence[str]) -> str:
    return f"WHERE {' AND '.join(clauses)}" if clauses else ""
