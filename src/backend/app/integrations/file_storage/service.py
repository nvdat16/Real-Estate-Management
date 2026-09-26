"""Kho tệp riêng tư (PLAN task 4.5, PLAN Q2): thư mục trên volume Docker cho MVP.

Service chỉ phụ thuộc `FileStorage` (save/read/delete theo `storage_key`) nên đổi
sang S3-compatible sau này không đụng tới module nghiệp vụ. Không có URL công
khai: tệp chỉ đi ra qua API đã kiểm tra quyền.

`storage_key` do server sinh (`files/service.py`), không bao giờ ghép từ tên tệp
người dùng gửi; adapter vẫn kiểm tra khóa để chặn path traversal nếu có lỗi ở
tầng trên.
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Protocol

from app.core.config import settings


_STORAGE_KEY = re.compile(r"^[a-z0-9_]+(/[a-z0-9_]+)*$")


class StorageError(Exception):
    """Kho tệp lỗi (đĩa đầy, mất mount...) — tạm thời, thử lại được."""


class StorageNotFoundError(StorageError):
    """Không có đối tượng với khóa này (bản ghi `files` trỏ tới tệp đã mất)."""


class FileStorage(Protocol):
    def save(self, key: str, data: bytes) -> None: ...

    def read(self, key: str) -> bytes: ...

    def delete(self, key: str) -> None: ...


class LocalFileStorage:
    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    def _path(self, key: str) -> Path:
        if not _STORAGE_KEY.match(key):
            raise ValueError(f"storage_key không hợp lệ: {key!r}")
        return self._root / key

    def save(self, key: str, data: bytes) -> None:
        """Ghi vào tệp tạm cùng thư mục rồi `os.replace`: người đọc không bao giờ
        thấy tệp ghi dở, kể cả khi tiến trình chết giữa chừng."""
        path = self._path(key)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=".upload-")
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(data)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(tmp_name, path)
            except BaseException:
                Path(tmp_name).unlink(missing_ok=True)
                raise
        except OSError as exc:
            raise StorageError("Không ghi được tệp vào kho") from exc

    def read(self, key: str) -> bytes:
        try:
            return self._path(key).read_bytes()
        except FileNotFoundError as exc:
            raise StorageNotFoundError("Tệp không còn trong kho") from exc
        except OSError as exc:
            raise StorageError("Không đọc được tệp từ kho") from exc

    def delete(self, key: str) -> None:
        try:
            self._path(key).unlink(missing_ok=True)
        except OSError as exc:
            raise StorageError("Không xóa được tệp khỏi kho") from exc


def get_file_storage() -> FileStorage:
    """Dependency FastAPI/worker; test override để dùng thư mục tạm."""
    return LocalFileStorage(settings.FILE_STORAGE_DIR)
