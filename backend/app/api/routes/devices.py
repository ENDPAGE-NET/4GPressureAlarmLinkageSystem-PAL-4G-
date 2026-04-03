from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.device import (
    DeviceBind,
    DeviceCreate,
    DeviceOverview,
    DeviceRead,
    ModuleCreate,
    ModuleDetail,
    ModuleStatusReport,
)
from app.services.device_service import (
    add_module_to_device,
    bind_device_by_serial,
    create_device,
    get_device_by_id,
    get_device_by_serial_number,
    get_device_overview,
    get_module_by_id,
    get_module_by_code,
    list_devices,
    update_module_status,
)

router = APIRouter()


@router.get("/overview", response_model=DeviceOverview)
async def read_device_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceOverview:
    return await get_device_overview(db, current_user)


@router.post("/bind", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
async def bind_device(
    payload: DeviceBind,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceRead:
    try:
        device = await bind_device_by_serial(db, payload, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    refreshed_device = await get_device_by_id(db, device.id)
    return DeviceRead.model_validate(refreshed_device)


@router.get("", response_model=list[DeviceRead])
async def read_devices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DeviceRead]:
    devices = await list_devices(db, current_user)
    return [DeviceRead.model_validate(device) for device in devices]


@router.get("/modules/{module_id}", response_model=ModuleDetail)
async def read_module_detail(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModuleDetail:
    module = await get_module_by_id(db, module_id)
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    if current_user.role != "super_admin" and module.device.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return ModuleDetail.model_validate(module)


@router.post("/modules/{module_id}/status", response_model=ModuleDetail)
async def report_module_status(
    module_id: int,
    payload: ModuleStatusReport,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModuleDetail:
    module = await get_module_by_id(db, module_id)
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    if current_user.role != "super_admin" and module.device.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    updated_module = await update_module_status(db, module, payload)
    return ModuleDetail.model_validate(updated_module)


@router.post("", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
async def create_new_device(
    payload: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceRead:
    existing = await get_device_by_serial_number(db, payload.serial_number)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device serial number already exists",
        )
    device = await create_device(db, payload, current_user)
    device = await get_device_by_id(db, device.id)
    return DeviceRead.model_validate(device)


@router.get("/{device_id}", response_model=DeviceRead)
async def read_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceRead:
    device = await get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    if current_user.role != "super_admin" and device.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return DeviceRead.model_validate(device)


@router.post("/{device_id}/modules", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
async def create_device_module(
    device_id: int,
    payload: ModuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceRead:
    device = await get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    if current_user.role != "super_admin" and device.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    existing_module = await get_module_by_code(db, device_id, payload.module_code)
    if existing_module:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Module code already exists in this device",
        )

    await add_module_to_device(db, device, payload)
    refreshed_device = await get_device_by_id(db, device_id)
    return DeviceRead.model_validate(refreshed_device)
