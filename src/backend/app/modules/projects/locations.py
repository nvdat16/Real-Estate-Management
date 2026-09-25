"""Danh mục địa bàn đã cấu hình (SPEC SP-02, ERD mục 4).

ERD không có bảng địa bàn: danh mục được cấu hình trong mã và dùng chung cho
validate dự án, bộ lọc tìm kiếm công khai và `scripts/seed.py`. Mở rộng danh mục
bằng cách thêm phần tử vào `LOCATIONS`; dự án chỉ được gắn cặp mã có ở đây.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    province_code: str
    ward_code: str
    province_name: str
    ward_name: str


LOCATIONS: tuple[Location, ...] = (
    Location("01", "00004", "Hà Nội", "Ba Đình"),
    Location("01", "00008", "Hà Nội", "Hoàn Kiếm"),
    Location("79", "26734", "TP Hồ Chí Minh", "Quận 1"),
    Location("79", "26746", "TP Hồ Chí Minh", "Quận 3"),
    Location("48", "20194", "Đà Nẵng", "Hải Châu"),
    Location("31", "11317", "Hải Phòng", "Hồng Bàng"),
)

_PAIRS = frozenset((item.province_code, item.ward_code) for item in LOCATIONS)
_PROVINCES = frozenset(item.province_code for item in LOCATIONS)


def is_known_location(province_code: str, ward_code: str) -> bool:
    return (province_code, ward_code) in _PAIRS


def is_known_province(province_code: str) -> bool:
    return province_code in _PROVINCES
