"""Nhận diện nội dung tệp upload và dựng header tải xuống (SPEC SP-06).

MIME lưu trong `files.mime_type` luôn do server suy ra từ nội dung thực, không
lấy `Content-Type` hay đuôi tệp client gửi; tải xuống trả đúng MIME đó kèm
`nosniff` nên trình duyệt không tự đoán lại thành HTML/script.
"""

from __future__ import annotations

import io
import re
import unicodedata
import zipfile
from urllib.parse import quote


MIME_JPEG = "image/jpeg"
MIME_PNG = "image/png"
MIME_PDF = "application/pdf"
MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MIME_CSV = "text/csv"

EXTENSIONS = {
    MIME_JPEG: ".jpg",
    MIME_PNG: ".png",
    MIME_PDF: ".pdf",
    MIME_XLSX: ".xlsx",
    MIME_CSV: ".csv",
}

# Chặn zip bomb: XLSX 10 MB nén có thể bung ra hàng GB khi openpyxl đọc.
MAX_XLSX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_XLSX_ENTRIES = 10_000

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_ASCII_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def sniff_image_or_pdf(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return MIME_JPEG
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return MIME_PNG
    if data.startswith(b"%PDF-"):
        return MIME_PDF
    return None


def is_safe_xlsx(data: bytes) -> bool:
    """XLSX thật (OOXML), không macro, không external link, không zip bomb.
    Công thức trong ô được kiểm tra ở bước import (PLAN task 8.4)."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            names = {entry.filename for entry in entries}
            if len(entries) > MAX_XLSX_ENTRIES:
                return False
            if sum(entry.file_size for entry in entries) > MAX_XLSX_UNCOMPRESSED_BYTES:
                return False
            if "[Content_Types].xml" not in names or "xl/workbook.xml" not in names:
                return False
            if any(
                name.lower().endswith("vbaproject.bin") or name.startswith("xl/externalLinks/")
                for name in names
            ):
                return False
            content_types = archive.read("[Content_Types].xml")
    except (zipfile.BadZipFile, KeyError, ValueError, RuntimeError):
        return False
    return b"macroEnabled" not in content_types


def is_utf8_csv(data: bytes) -> bool:
    if b"\x00" in data:
        return False
    try:
        data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return False
    return True


def sanitize_filename(name: str | None) -> str | None:
    """Tên hiển thị: bỏ thư mục, ký tự điều khiển; chỉ dùng cho header tải
    xuống, không bao giờ dùng làm đường dẫn lưu trữ."""
    if not name:
        return None
    base = re.split(r"[\\/]", name)[-1]
    cleaned = _CONTROL_CHARS.sub("", unicodedata.normalize("NFC", base)).strip()
    return cleaned[:255] or None


def extension_of(name: str | None) -> str:
    if not name or "." not in name:
        return ""
    return "." + name.rsplit(".", 1)[-1].lower()


def content_disposition(filename: str) -> str:
    """`attachment` với tên ASCII dự phòng và `filename*` UTF-8 (RFC 6266) để
    tên tiếng Việt hiển thị đúng mà không chèn được ký tự phá header."""
    # NFKD tách dấu tiếng Việt khỏi chữ cái, riêng "đ" là chữ độc lập nên đổi tay.
    transliterated = filename.replace("đ", "d").replace("Đ", "D")
    ascii_name = (
        unicodedata.normalize("NFKD", transliterated).encode("ascii", "ignore").decode("ascii")
    )
    ascii_name = _ASCII_UNSAFE.sub("_", ascii_name).strip("._") or "download"
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename, safe='')}"
