"""Kho tệp private (PLAN task 4.5, SPEC SP-06, T-02 phần tệp): upload kiểm tra
purpose/nội dung thực, tải kiểm tra quan hệ chủ sở hữu và trả header an toàn."""

from __future__ import annotations

import hashlib
import io
import zipfile

import httpx
import pytest
from openpyxl import Workbook
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import FilePurpose, FileStatus, JobType
from app.integrations.file_storage.service import LocalFileStorage
from app.models import File, User
from app.modules.files.service import MAX_UPLOAD_BYTES
from app.modules.notifications import service as notifications_service
from tests.integration import factories as f


pytestmark = [pytest.mark.integration]

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
PDF = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\n"


async def _customer_user(db: AsyncSession) -> User:
    customer = await f.make_customer(db)
    user = await db.get(User, customer.user_id)
    assert user is not None
    return user


async def _upload(
    client: httpx.AsyncClient,
    user: User,
    *,
    purpose: str,
    filename: str,
    content: bytes,
    content_type: str = "application/octet-stream",
) -> httpx.Response:
    return await client.post(
        "/api/v1/files",
        data={"purpose": purpose},
        files={"file": (filename, content, content_type)},
        headers=f.auth_headers(user),
    )


def _xlsx_bytes() -> bytes:
    workbook = Workbook()
    workbook.active.append(["code", "name"])
    workbook.active.append(["DA01", "Dự án A"])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _xlsx_with(extra_entry: str) -> bytes:
    source = zipfile.ZipFile(io.BytesIO(_xlsx_bytes()))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as target:
        for item in source.infolist():
            target.writestr(item, source.read(item.filename))
        target.writestr(extra_entry, b"payload")
    return buffer.getvalue()


# --- upload ---------------------------------------------------------------------------


async def test_khach_upload_kyc_va_tai_lai(
    client: httpx.AsyncClient, db_session: AsyncSession, file_storage: LocalFileStorage
) -> None:
    user = await _customer_user(db_session)
    response = await _upload(
        client, user, purpose="kyc", filename="../../etc/CCCD mặt trước.png", content=PNG
    )
    assert response.status_code == 201
    body = response.json()
    assert body["purpose"] == "kyc"
    assert body["status"] == "ready"
    # MIME từ nội dung, không từ Content-Type client gửi.
    assert body["mime_type"] == "image/png"
    assert body["size_bytes"] == len(PNG)
    assert body["sha256"] == hashlib.sha256(PNG).hexdigest()
    # Chỉ giữ tên tệp, bỏ thư mục; không trả khóa kho.
    assert body["original_name"] == "CCCD mặt trước.png"
    assert "storage_key" not in body

    storage_key = await db_session.scalar(
        text("SELECT storage_key FROM files WHERE id = :id"), {"id": body["id"]}
    )
    assert storage_key.startswith("kyc/")
    assert "CCCD" not in storage_key
    assert file_storage.read(storage_key) == PNG

    audit = await db_session.scalar(
        text("SELECT action FROM audit_logs WHERE entity_type = 'files' AND entity_id = :id"),
        {"id": body["id"]},
    )
    assert audit == "file.upload"

    download = await client.get(
        f"/api/v1/files/{body['id']}/download", headers=f.auth_headers(user)
    )
    assert download.status_code == 200
    assert download.content == PNG
    assert download.headers["content-type"] == "image/png"
    assert download.headers["x-content-type-options"] == "nosniff"
    assert download.headers["cache-control"] == "private, no-store"
    disposition = download.headers["content-disposition"]
    assert disposition.startswith("attachment;")
    assert "filename*=UTF-8''CCCD%20m%E1%BA%B7t%20tr%C6%B0%E1%BB%9Bc.png" in disposition


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("anh.png", b"<html><script>alert(1)</script></html>"),
        ("giay-to.exe", b"MZ\x90\x00"),
    ],
)
async def test_kyc_noi_dung_khong_phai_anh_pdf_bi_tu_choi(
    client: httpx.AsyncClient, db_session: AsyncSession, filename: str, content: bytes
) -> None:
    user = await _customer_user(db_session)
    response = await _upload(
        client, user, purpose="kyc", filename=filename, content=content, content_type="image/png"
    )
    assert response.status_code == 422
    assert response.json()["error"]["details"]["reason"] == "unsupported_type"
    assert await db_session.scalar(text("SELECT COUNT(*) FROM files")) == 0


async def test_upload_qua_10mb_va_rong_bi_tu_choi(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    user = await _customer_user(db_session)
    too_big = PDF + b"0" * MAX_UPLOAD_BYTES
    response = await _upload(client, user, purpose="kyc", filename="a.pdf", content=too_big)
    assert response.status_code == 422
    assert response.json()["error"]["details"]["reason"] == "too_large"

    empty = await _upload(client, user, purpose="kyc", filename="a.pdf", content=b"")
    assert empty.status_code == 422
    assert empty.json()["error"]["details"]["reason"] == "empty"


async def test_client_khong_upload_duoc_purpose_he_thong(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    user = await _customer_user(db_session)
    for purpose in ("contract_pdf", "invoice_pdf", "report", "data_export", "khac"):
        response = await _upload(client, user, purpose=purpose, filename="a.pdf", content=PDF)
        assert response.status_code == 422, purpose


async def test_upload_kyc_can_ho_so_khach(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    agent_user, _ = await f.make_agent_actor(db_session)
    response = await _upload(client, agent_user, purpose="kyc", filename="a.png", content=PNG)
    assert response.status_code == 403


async def test_upload_import_can_quyen_va_chan_macro(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    customer = await _customer_user(db_session)
    denied = await _upload(client, customer, purpose="import", filename="a.csv", content=b"a,b\n")
    assert denied.status_code == 403

    admin = await f.make_actor(db_session, role_code="admin", permission_codes=("data.import",))
    csv_ok = await _upload(
        client,
        admin,
        purpose="import",
        filename="du-an.csv",
        content="code,name\nDA,Dự án\n".encode(),
    )
    assert csv_ok.status_code == 201
    assert csv_ok.json()["mime_type"] == "text/csv"

    xlsx_ok = await _upload(
        client, admin, purpose="import", filename="du-an.xlsx", content=_xlsx_bytes()
    )
    assert xlsx_ok.status_code == 201
    assert xlsx_ok.json()["mime_type"].endswith("spreadsheetml.sheet")

    rejected = [
        ("macro.xlsx", _xlsx_with("xl/vbaProject.bin")),
        ("link.xlsx", _xlsx_with("xl/externalLinks/externalLink1.xml")),
        ("macro.xlsm", _xlsx_bytes()),
        ("gia.xlsx", b"code,name\n"),
        ("latin1.csv", "Dự án".encode("cp1258", errors="replace") + b"\xff\xfe"),
        ("anh.csv", PNG),
    ]
    for filename, content in rejected:
        response = await _upload(
            client, admin, purpose="import", filename=filename, content=content
        )
        assert response.status_code == 422, filename


# --- quyền tải --------------------------------------------------------------------------


async def test_kyc_chi_chu_so_huu_va_nguoi_co_quyen_tai(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    owner = await _customer_user(db_session)
    other_customer = await _customer_user(db_session)
    agent_user, _ = await f.make_agent_actor(
        db_session, permission_codes=("listing.manage", "customer.read_scope")
    )
    kyc_admin = await f.make_actor(
        db_session, role_code="admin", permission_codes=("kyc.read_sensitive",)
    )
    uploaded = await _upload(client, owner, purpose="kyc", filename="cccd.pdf", content=PDF)
    file_id = uploaded.json()["id"]

    for outsider in (other_customer, agent_user):
        response = await client.get(
            f"/api/v1/files/{file_id}/download", headers=f.auth_headers(outsider)
        )
        assert response.status_code == 404

    allowed = await client.get(
        f"/api/v1/files/{file_id}/download", headers=f.auth_headers(kyc_admin)
    )
    assert allowed.status_code == 200
    assert allowed.content == PDF


async def test_tep_he_thong_chi_nguoi_yeu_cau_job_tai_duoc(
    client: httpx.AsyncClient, db_session: AsyncSession, file_storage: LocalFileStorage
) -> None:
    requester = await f.make_actor(db_session, role_code="agent")
    other = await f.make_actor(db_session, role_code="agent")
    content = b"code,name\n"
    file_storage.save("data_export/2026/09/abc", content)
    exported = File(
        storage_key="data_export/2026/09/abc",
        original_name=None,
        mime_type="text/csv",
        size_bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
        purpose=FilePurpose.DATA_EXPORT,
        status=FileStatus.READY,
    )
    db_session.add(exported)
    await db_session.flush()
    job = await notifications_service.enqueue_job(
        db_session,
        job_type=JobType.EXPORT_DATA,
        idempotency_key="export:file-test",
        requested_by=requester.id,
        payload={},
    )
    await db_session.execute(
        text("UPDATE jobs SET output_file_id = :file_id WHERE id = :id"),
        {"file_id": exported.id, "id": job.id},
    )
    await db_session.commit()

    ok = await client.get(
        f"/api/v1/files/{exported.id}/download", headers=f.auth_headers(requester)
    )
    assert ok.status_code == 200
    # Không có tên gốc: tên tải xuống sinh từ ID và MIME.
    assert f'filename="{exported.id}.csv"' in ok.headers["content-disposition"]

    denied = await client.get(
        f"/api/v1/files/{exported.id}/download", headers=f.auth_headers(other)
    )
    assert denied.status_code == 404


async def test_tep_chua_ready_hoac_mat_khoi_kho(
    client: httpx.AsyncClient, db_session: AsyncSession, file_storage: LocalFileStorage
) -> None:
    owner = await _customer_user(db_session)
    pending = File(
        uploaded_by=owner.id,
        storage_key="kyc/2026/09/pending",
        mime_type="image/png",
        purpose=FilePurpose.KYC,
        status=FileStatus.PENDING,
    )
    db_session.add(pending)
    await db_session.flush()
    response = await client.get(
        f"/api/v1/files/{pending.id}/download", headers=f.auth_headers(owner)
    )
    assert response.status_code == 404

    uploaded = await _upload(client, owner, purpose="kyc", filename="a.png", content=PNG)
    file_id = uploaded.json()["id"]
    storage_key = await db_session.scalar(
        text("SELECT storage_key FROM files WHERE id = :id"), {"id": file_id}
    )

    file_storage.save(storage_key, PNG + b"tampered")
    tampered = await client.get(f"/api/v1/files/{file_id}/download", headers=f.auth_headers(owner))
    assert tampered.status_code == 503

    file_storage.delete(storage_key)
    missing = await client.get(f"/api/v1/files/{file_id}/download", headers=f.auth_headers(owner))
    assert missing.status_code == 503
    assert missing.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"


async def test_uuid_khong_ton_tai_va_chua_dang_nhap(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    owner = await _customer_user(db_session)
    missing = await client.get(
        "/api/v1/files/00000000-0000-0000-0000-000000000000/download",
        headers=f.auth_headers(owner),
    )
    assert missing.status_code == 404
    anonymous = await client.post("/api/v1/files", data={"purpose": "kyc"})
    assert anonymous.status_code == 401
