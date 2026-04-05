from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import Token, UserProfile, WechatBindResult, WechatIdentityPayload
from app.services.user_service import get_user_by_username
from app.services.wechat_service import (
    bind_wechat_identity,
    get_user_by_wechat_open_id,
    resolve_wechat_identity_async,
)

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    user = await get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    access_token = create_access_token(subject=user.username)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserProfile)
async def read_current_user(
    current_user: User = Depends(get_current_user),
) -> UserProfile:
    return UserProfile(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        is_active=current_user.is_active,
        wechat_bound=bool(current_user.wechat_open_id),
        wechat_bound_at=current_user.wechat_bound_at,
    )


@router.post("/wechat-login", response_model=Token)
async def wechat_login(
    payload: WechatIdentityPayload,
    db: AsyncSession = Depends(get_db),
) -> Token:
    wechat_open_id, _ = await resolve_wechat_identity_async(payload)
    user = await get_user_by_wechat_open_id(db, wechat_open_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="WeChat account is not bound to any user",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    access_token = create_access_token(subject=user.username)
    return Token(access_token=access_token)


@router.post("/wechat-bind", response_model=WechatBindResult)
async def wechat_bind(
    payload: WechatIdentityPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WechatBindResult:
    try:
        user = await bind_wechat_identity(db, current_user, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return WechatBindResult(
        user_id=user.id,
        username=user.username,
        wechat_open_id=user.wechat_open_id or "",
        wechat_union_id=user.wechat_union_id,
        wechat_bound_at=user.wechat_bound_at,
    )
