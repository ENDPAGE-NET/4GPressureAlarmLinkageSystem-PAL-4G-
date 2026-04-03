from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    UserChangePassword,
    UserCreate,
    UserRead,
    UserResetPassword,
    UserUpdate,
)
from app.services.logging_service import write_operation_log
from app.services.user_service import (
    change_user_password,
    create_user,
    get_user_by_id,
    get_user_by_username,
    list_users,
    reset_user_password,
    update_user,
)

router = APIRouter()


@router.get("", response_model=list[UserRead])
async def read_users(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[UserRead]:
    users = await list_users(db)
    return [UserRead.model_validate(user) for user in users]


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    payload: UserCreate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    existing = await get_user_by_username(db, payload.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )
    user = await create_user(db, payload)
    await write_operation_log(
        db,
        action="create_user",
        target_type="user",
        actor_user_id=current_admin.id,
        target_id=user.id,
        detail=f"created user {user.username}",
    )
    return UserRead.model_validate(user)


@router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: int,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserRead.model_validate(user)


@router.patch("/{user_id}", response_model=UserRead)
async def patch_user(
    user_id: int,
    payload: UserUpdate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_admin.id and payload.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current admin cannot deactivate self",
        )
    updated_user = await update_user(db, user, payload)
    await write_operation_log(
        db,
        action="update_user",
        target_type="user",
        actor_user_id=current_admin.id,
        target_id=updated_user.id,
        detail=f"updated user {updated_user.username}",
    )
    return UserRead.model_validate(updated_user)


@router.post("/{user_id}/reset-password", response_model=UserRead)
async def reset_password(
    user_id: int,
    payload: UserResetPassword,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    updated_user = await reset_user_password(db, user, payload)
    await write_operation_log(
        db,
        action="reset_user_password",
        target_type="user",
        actor_user_id=current_admin.id,
        target_id=updated_user.id,
        detail=f"reset password for {updated_user.username}",
    )
    return UserRead.model_validate(updated_user)


@router.post("/me/change-password", response_model=UserRead)
async def change_password(
    payload: UserChangePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    try:
        updated_user = await change_user_password(db, current_user, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await write_operation_log(
        db,
        action="change_own_password",
        target_type="user",
        actor_user_id=current_user.id,
        target_id=updated_user.id,
        detail=f"user {updated_user.username} changed own password",
    )
    return UserRead.model_validate(updated_user)
