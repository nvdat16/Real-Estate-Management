"""Query params phân trang chung — mặc định page=1/page_size=20, tối đa 100
(SPEC mục 3.1). `sort` không có validator chung: mỗi router tự khai
`Literal[...]` cho allowlist cột của mình.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Query


DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@dataclass(frozen=True)
class PageParams:
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def page_params(
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> PageParams:
    return PageParams(page=page, page_size=page_size)


def escape_like(term: str) -> str:
    """Escape ký tự đại diện của LIKE để từ khóa người dùng được so khớp nguyên văn."""
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
