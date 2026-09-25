"""HTTP↔schema mapping cho auth.

SPEC đặt `GET/PATCH /me` ở gốc (không có tiền tố `/auth`) trong khi các lệnh
khác đều dưới `/auth/...` — nên có 2 router riêng, cả hai được mount ở
`app/main.py` dưới cùng `/api/v1`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.modules.auth import service as auth_service
from app.modules.auth.schemas import (
    MessageResponse,
    MeUpdateRequest,
    PasswordResetConfirmSchema,
    PasswordResetRequestSchema,
    RegisterRequest,
    TokenResponse,
    UserPublic,
)
from app.modules.users.models import User


router = APIRouter(prefix="/auth", tags=["auth"])
me_router = APIRouter(tags=["me"])

_RESET_ACCEPTED_MESSAGE = "Nếu email tồn tại, liên kết đặt lại mật khẩu đã được gửi."


@router.post("/register", response_model=UserPublic, status_code=201)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> UserPublic:
    user = await auth_service.register(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        phone=payload.phone,
    )
    return await auth_service.get_me(db, user=user)


@router.post("/token", response_model=TokenResponse)
async def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    access_token = await auth_service.login(
        db, email=form_data.username, password=form_data.password
    )
    return TokenResponse(access_token=access_token)


@router.post("/logout", status_code=204)
async def logout(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> None:
    await auth_service.logout(db, user=user)


@router.post("/password-reset/request", response_model=MessageResponse)
async def request_password_reset(
    payload: PasswordResetRequestSchema, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    await auth_service.request_password_reset(db, email=payload.email)
    return MessageResponse(message=_RESET_ACCEPTED_MESSAGE)


@router.post("/password-reset/confirm", response_model=MessageResponse)
async def confirm_password_reset(
    payload: PasswordResetConfirmSchema, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    await auth_service.confirm_password_reset(
        db, token=payload.token, new_password=payload.new_password
    )
    return MessageResponse(message="Mật khẩu đã được đặt lại.")


@me_router.get("/me", response_model=UserPublic)
async def get_me(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> UserPublic:
    return await auth_service.get_me(db, user=user)


@me_router.patch("/me", response_model=UserPublic)
async def update_me(
    payload: MeUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserPublic:
    return await auth_service.update_me(
        db,
        user=user,
        full_name=payload.full_name,
        phone=payload.phone,
        expected_row_version=payload.row_version,
    )
