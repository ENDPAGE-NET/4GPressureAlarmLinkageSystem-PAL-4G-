from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.protocol_profile import (
    ProtocolProfileCreate,
    ProtocolProfileRead,
    ProtocolProfileUpdate,
)
from app.services.logging_service import write_operation_log
from app.services.protocol_profile_service import (
    build_protocol_profile_read,
    create_protocol_profile,
    get_protocol_profile_by_id,
    get_protocol_profile_by_name,
    list_protocol_profiles,
    update_protocol_profile,
)

router = APIRouter()


@router.get("", response_model=list[ProtocolProfileRead])
async def read_protocol_profiles(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[ProtocolProfileRead]:
    profiles = await list_protocol_profiles(db)
    return [build_protocol_profile_read(profile) for profile in profiles]


@router.post("", response_model=ProtocolProfileRead, status_code=status.HTTP_201_CREATED)
async def create_new_protocol_profile(
    payload: ProtocolProfileCreate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ProtocolProfileRead:
    existing = await get_protocol_profile_by_name(db, payload.name)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Protocol profile name already exists")
    try:
        profile = await create_protocol_profile(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    await write_operation_log(
        db,
        action="create_protocol_profile",
        target_type="protocol_profile",
        actor_user_id=current_admin.id,
        target_id=profile.id,
        detail=f"created protocol profile {profile.name}",
    )
    return build_protocol_profile_read(profile)


@router.get("/{protocol_profile_id}", response_model=ProtocolProfileRead)
async def read_protocol_profile(
    protocol_profile_id: int,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ProtocolProfileRead:
    profile = await get_protocol_profile_by_id(db, protocol_profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Protocol profile not found")
    return build_protocol_profile_read(profile)


@router.patch("/{protocol_profile_id}", response_model=ProtocolProfileRead)
async def patch_protocol_profile(
    protocol_profile_id: int,
    payload: ProtocolProfileUpdate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ProtocolProfileRead:
    profile = await get_protocol_profile_by_id(db, protocol_profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Protocol profile not found")

    if payload.name and payload.name != profile.name:
        existing = await get_protocol_profile_by_name(db, payload.name)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Protocol profile name already exists")
    try:
        updated_profile = await update_protocol_profile(db, profile, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    await write_operation_log(
        db,
        action="update_protocol_profile",
        target_type="protocol_profile",
        actor_user_id=current_admin.id,
        target_id=updated_profile.id,
        detail=f"updated protocol profile {updated_profile.name}",
    )
    return build_protocol_profile_read(updated_profile)
