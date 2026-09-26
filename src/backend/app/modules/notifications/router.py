"""HTTP↔schema mapping cho theo dõi tác vụ nền (SPEC §11 nhóm "Vận hành").

Không có endpoint tạo job trực tiếp: job chỉ sinh ra từ lệnh nghiệp vụ của module
khác (reset mật khẩu, gửi ký, xuất dữ liệu...), cùng transaction với lệnh đó.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import JobStatus, JobType
from app.common.schemas.pagination import Page
from app.common.utils.pagination import PageParams, page_params
from app.core.database import get_db
from app.dependencies import get_current_user
from app.modules.notifications import service as notifications_service
from app.modules.notifications.schemas import JobScope, JobSort, JobView
from app.modules.users.repository import UserRow


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=Page[JobView])
async def list_jobs(
    scope: JobScope = Query(default="mine"),
    status: JobStatus | None = Query(default=None),
    job_type: JobType | None = Query(default=None),
    sort: JobSort = Query(default="-created_at"),
    pagination: PageParams = Depends(page_params),
    actor: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Page[JobView]:
    return await notifications_service.list_jobs(
        db,
        actor=actor,
        scope=scope,
        page_params=pagination,
        sort=sort,
        status=status,
        job_type=job_type,
    )


@router.get("/{job_id}", response_model=JobView)
async def get_job(
    job_id: uuid.UUID,
    actor: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobView:
    return await notifications_service.get_job(db, actor=actor, job_id=job_id)


@router.post("/{job_id}/retry", response_model=JobView)
async def retry_job(
    job_id: uuid.UUID,
    actor: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobView:
    return await notifications_service.retry_job(db, actor=actor, job_id=job_id)
