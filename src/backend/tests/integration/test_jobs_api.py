"""Scope API tác vụ nền (SPEC SP-07, UC-22, T-02 phần job): mỗi actor chỉ thấy
và thử lại job của mình; job hệ thống và job người khác chỉ `job.manage` thấy."""

from __future__ import annotations

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import JobType
from app.models import User
from app.modules.notifications import service as notifications_service
from app.modules.notifications.exceptions import JobErrorCode
from app.modules.notifications.repository import JobRow
from tests.integration import factories as f


pytestmark = [pytest.mark.integration]


async def _job_for(db: AsyncSession, requested_by: User | None, key: str) -> JobRow:
    return await notifications_service.enqueue_job(
        db,
        job_type=JobType.EXPORT_DATA,
        idempotency_key=key,
        requested_by=requested_by.id if requested_by else None,
        payload={"filters": {"status": "approved"}},
    )


async def _fail(db: AsyncSession, job: JobRow, error_code: str) -> None:
    await db.execute(
        text("UPDATE jobs SET status = 'failed', attempts = 3, error_code = :code WHERE id = :id"),
        {"code": error_code, "id": job.id},
    )


async def test_moi_actor_chi_thay_job_cua_minh(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    owner = await f.make_actor(db_session, role_code="customer")
    other = await f.make_actor(db_session, role_code="customer")
    own_job = await _job_for(db_session, owner, "job:owner")
    await _job_for(db_session, other, "job:other")
    await _job_for(db_session, None, "job:system")
    await db_session.commit()

    response = await client.get("/api/v1/jobs", headers=f.auth_headers(owner))
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    item = body["items"][0]
    assert item["id"] == str(own_job.id)
    assert item["status"] == "pending"
    assert "payload" not in item
    assert "idempotency_key" not in item

    detail = await client.get(f"/api/v1/jobs/{own_job.id}", headers=f.auth_headers(owner))
    assert detail.status_code == 200

    # Đổi UUID sang job người khác: 404 như job không tồn tại.
    foreign = await client.get(f"/api/v1/jobs/{own_job.id}", headers=f.auth_headers(other))
    assert foreign.status_code == 404
    retry = await client.post(f"/api/v1/jobs/{own_job.id}/retry", headers=f.auth_headers(other))
    assert retry.status_code == 404


async def test_scope_all_can_job_manage(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    user = await f.make_actor(db_session, role_code="agent", permission_codes=("listing.manage",))
    admin = await f.make_actor(db_session, role_code="admin", permission_codes=("job.manage",))
    await _job_for(db_session, user, "job:user")
    system_job = await _job_for(db_session, None, "job:system")
    await db_session.commit()

    forbidden = await client.get("/api/v1/jobs?scope=all", headers=f.auth_headers(user))
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "PERMISSION_DENIED"

    everything = await client.get("/api/v1/jobs?scope=all", headers=f.auth_headers(admin))
    assert everything.status_code == 200
    assert everything.json()["total"] == 2

    # Job hệ thống không lọt vào "của tôi" của Admin nhưng Admin đọc được theo ID.
    mine = await client.get("/api/v1/jobs", headers=f.auth_headers(admin))
    assert mine.json()["total"] == 0
    detail = await client.get(f"/api/v1/jobs/{system_job.id}", headers=f.auth_headers(admin))
    assert detail.status_code == 200
    assert detail.json()["requested_by"] is None


async def test_loc_theo_trang_thai_va_loai(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    owner = await f.make_actor(db_session, role_code="customer")
    failed_job = await _job_for(db_session, owner, "job:1")
    await _job_for(db_session, owner, "job:2")
    await _fail(db_session, failed_job, JobErrorCode.STORAGE_UNAVAILABLE)
    await db_session.commit()

    response = await client.get(
        "/api/v1/jobs?status=failed&job_type=export_data", headers=f.auth_headers(owner)
    )
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["retryable"] is True

    invalid = await client.get("/api/v1/jobs?status=done", headers=f.auth_headers(owner))
    assert invalid.status_code == 422


async def test_chu_job_retry_loi_tam_thoi_khong_retry_loi_vinh_vien(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    owner = await f.make_actor(db_session, role_code="customer")
    transient = await _job_for(db_session, owner, "job:transient")
    permanent = await _job_for(db_session, owner, "job:permanent")
    pending = await _job_for(db_session, owner, "job:pending")
    await _fail(db_session, transient, JobErrorCode.STORAGE_UNAVAILABLE)
    await _fail(db_session, permanent, JobErrorCode.PERMISSION_REVOKED)
    await db_session.commit()

    ok = await client.post(f"/api/v1/jobs/{transient.id}/retry", headers=f.auth_headers(owner))
    assert ok.status_code == 200
    assert ok.json()["status"] == "pending"
    assert ok.json()["attempts"] == 0

    for job in (permanent, pending):
        response = await client.post(f"/api/v1/jobs/{job.id}/retry", headers=f.auth_headers(owner))
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "INVALID_STATE"

    actor = await db_session.scalar(
        text("SELECT actor_user_id FROM audit_logs WHERE action = 'job.retry'")
    )
    assert actor == owner.id


async def test_jobs_can_dang_nhap(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/jobs")
    assert response.status_code == 401
