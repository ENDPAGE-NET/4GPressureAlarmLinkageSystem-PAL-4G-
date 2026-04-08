from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.device import (
    DeviceAssignOwner,
    DeviceAssignProtocolProfile,
    DeviceBind,
    DeviceCreate,
    DeviceDeleteResult,
    DeviceGroupAssign,
    DeviceGroupCreate,
    DeviceGroupDeleteResult,
    DeviceGroupPage,
    DeviceGroupRead,
    DeviceMonitoringPage,
    DeviceGroupUpdate,
    DeviceMonitoringItem,
    DeviceMqttConfig,
    DeviceOverview,
    DevicePage,
    DeviceRead,
    DeviceStatistics,
    DeviceUpdate,
    ModuleCreate,
    ModuleDeleteResult,
    ModuleDetail,
    ModuleStatusHistoryPage,
    ModuleStatusReport,
)
from app.services.logging_service import write_operation_log
from app.services.device_service import (
    add_module_to_device,
    assign_device_owner,
    assign_device_group,
    bind_device_by_serial,
    build_device_group_read,
    build_device_mqtt_config,
    create_device,
    create_device_group,
    delete_device,
    delete_device_group,
    delete_module,
    get_device_by_id,
    get_device_group_by_id,
    get_device_group_by_name,
    get_device_monitoring_list,
    get_device_by_serial_number,
    get_device_overview,
    get_device_monitoring_page,
    get_device_statistics,
    get_module_by_id,
    get_module_by_code,
    list_device_groups,
    list_device_groups_page,
    list_devices,
    list_devices_page,
    get_module_status_history_page,
    unbind_device,
    update_device_group,
    update_device,
    update_module_status,
)
from app.services.protocol_profile_service import (
    assign_device_protocol_profile,
    get_protocol_profile_by_id,
)
from app.services.user_service import get_user_by_id

router = APIRouter()


@router.get("/groups", response_model=list[DeviceGroupRead])
async def read_device_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DeviceGroupRead]:
    groups = await list_device_groups(db, current_user)
    return [build_device_group_read(group) for group in groups]


@router.get("/groups/page", response_model=DeviceGroupPage)
async def read_device_groups_page(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceGroupPage:
    return await list_device_groups_page(db, current_user, limit=limit, offset=offset)


@router.post("/groups", response_model=DeviceGroupRead, status_code=status.HTTP_201_CREATED)
async def create_new_device_group(
    payload: DeviceGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> DeviceGroupRead:
    existing = await get_device_group_by_name(db, payload.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device group name already exists",
        )

    owner = None
    if payload.owner_id is not None:
        owner = await get_user_by_id(db, payload.owner_id)
        if not owner:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    group = await create_device_group(db, payload, owner)
    group = await get_device_group_by_id(db, group.id)
    await write_operation_log(
        db,
        action="create_device_group",
        target_type="device_group",
        actor_user_id=current_admin.id,
        target_id=group.id,
        detail=f"created device group {group.name}",
    )
    return build_device_group_read(group)


@router.get("/groups/{group_id}", response_model=DeviceGroupRead)
async def read_device_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceGroupRead:
    group = await get_device_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device group not found")
    if current_user.role != "super_admin" and group.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return build_device_group_read(group)


@router.patch("/groups/{group_id}", response_model=DeviceGroupRead)
async def patch_device_group(
    group_id: int,
    payload: DeviceGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> DeviceGroupRead:
    group = await get_device_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device group not found")

    owner = None
    if payload.owner_id is not None:
        owner = await get_user_by_id(db, payload.owner_id)
        if not owner:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.name and payload.name != group.name:
        existing = await get_device_group_by_name(db, payload.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Device group name already exists",
            )

    updated_group = await update_device_group(db, group, payload, owner)
    refreshed_group = await get_device_group_by_id(db, updated_group.id)
    await write_operation_log(
        db,
        action="update_device_group",
        target_type="device_group",
        actor_user_id=current_admin.id,
        target_id=group_id,
        detail=f"updated device group {updated_group.name}",
    )
    return build_device_group_read(refreshed_group)


@router.delete("/groups/{group_id}", response_model=DeviceGroupDeleteResult)
async def remove_device_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> DeviceGroupDeleteResult:
    group = await get_device_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device group not found")

    try:
        await delete_device_group(db, group)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    await write_operation_log(
        db,
        action="delete_device_group",
        target_type="device_group",
        actor_user_id=current_admin.id,
        target_id=group_id,
        detail=f"deleted device group {group.name}",
    )
    return DeviceGroupDeleteResult(group_id=group_id)


@router.get("/overview", response_model=DeviceOverview)
async def read_device_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceOverview:
    return await get_device_overview(db, current_user)


@router.get("/statistics", response_model=DeviceStatistics)
async def read_device_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceStatistics:
    return await get_device_statistics(db, current_user)


@router.get("/monitoring", response_model=list[DeviceMonitoringItem])
async def read_device_monitoring(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DeviceMonitoringItem]:
    return await get_device_monitoring_list(db, current_user)


@router.get("/monitoring/page", response_model=DeviceMonitoringPage)
async def read_device_monitoring_page(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceMonitoringPage:
    return await get_device_monitoring_page(db, current_user, limit=limit, offset=offset)


@router.post("/bind", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
async def bind_device(
    payload: DeviceBind,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceRead:
    try:
        # 绑定动作放到 service 层统一处理，避免路由层散落归属规则。
        device = await bind_device_by_serial(db, payload, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    refreshed_device = await get_device_by_id(db, device.id)
    await write_operation_log(
        db,
        action="bind_device",
        target_type="device",
        actor_user_id=current_user.id,
        target_id=device.id,
        detail=f"bound device {device.serial_number}",
    )
    return DeviceRead.model_validate(refreshed_device)


@router.get("", response_model=list[DeviceRead])
async def read_devices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DeviceRead]:
    devices = await list_devices(db, current_user)
    return [DeviceRead.model_validate(device) for device in devices]


@router.get("/page", response_model=DevicePage)
async def read_devices_page(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DevicePage:
    page = await list_devices_page(db, current_user, limit=limit, offset=offset)
    return DevicePage(
        total=page.total,
        items=[DeviceRead.model_validate(device) for device in page.items],
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/{device_id}/mqtt-config", response_model=DeviceMqttConfig)
async def read_device_mqtt_config(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceMqttConfig:
    """返回设备的 MQTT 接入配置信息，供管理员抄录到实体硬件。"""
    device = await get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    if current_user.role != "super_admin" and device.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return build_device_mqtt_config(device)


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


@router.get("/modules/{module_id}/status-history", response_model=ModuleStatusHistoryPage)
async def read_module_status_history(
    module_id: int,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModuleStatusHistoryPage:
    module = await get_module_by_id(db, module_id)
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    if current_user.role != "super_admin" and module.device.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return await get_module_status_history_page(db, module_id, limit=limit, offset=offset)


@router.delete("/modules/{module_id}", response_model=ModuleDeleteResult)
async def remove_module(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModuleDeleteResult:
    module = await get_module_by_id(db, module_id)
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    if current_user.role != "super_admin" and module.device.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        await delete_module(db, module)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    await write_operation_log(
        db,
        action="delete_module",
        target_type="module",
        actor_user_id=current_user.id,
        target_id=module_id,
        detail=f"deleted module {module.module_code}",
    )
    return ModuleDeleteResult(module_id=module_id)


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

    # 这里先提供 HTTP 版状态上报入口，后续接 MQTT 时复用同一套 service 逻辑。
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


@router.patch("/{device_id}", response_model=DeviceRead)
async def patch_device(
    device_id: int,
    payload: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceRead:
    device = await get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    if current_user.role != "super_admin" and device.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    updated_device = await update_device(db, device, payload)
    refreshed_device = await get_device_by_id(db, updated_device.id)
    await write_operation_log(
        db,
        action="update_device",
        target_type="device",
        actor_user_id=current_user.id,
        target_id=device_id,
        detail=f"updated device {updated_device.serial_number}",
    )
    return DeviceRead.model_validate(refreshed_device)


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


@router.post("/{device_id}/assign-owner", response_model=DeviceRead)
async def assign_owner(
    device_id: int,
    payload: DeviceAssignOwner,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> DeviceRead:
    device = await get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    owner = None
    if payload.owner_id is not None:
        owner = await get_user_by_id(db, payload.owner_id)
        if not owner:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # 设备分配与回收都走这一入口，owner_id 为空时表示回收到公共池。
    updated_device = await assign_device_owner(db, device, payload, owner)
    refreshed_device = await get_device_by_id(db, updated_device.id)
    await write_operation_log(
        db,
        action="assign_device_owner",
        target_type="device",
        actor_user_id=current_admin.id,
        target_id=device_id,
        detail=f"assigned device {updated_device.serial_number} to owner {payload.owner_id}",
    )
    return DeviceRead.model_validate(refreshed_device)


@router.post("/{device_id}/assign-group", response_model=DeviceRead)
async def assign_group(
    device_id: int,
    payload: DeviceGroupAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceRead:
    device = await get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    if current_user.role != "super_admin" and device.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    group = None
    if payload.linkage_group_id is not None:
        group = await get_device_group_by_id(db, payload.linkage_group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device group not found")
        if current_user.role != "super_admin" and group.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # 设备可随时切换组，联动时会实时按最新映射生效。
    updated_device = await assign_device_group(db, device, group)
    refreshed_device = await get_device_by_id(db, updated_device.id)
    await write_operation_log(
        db,
        action="assign_device_group",
        target_type="device",
        actor_user_id=current_user.id,
        target_id=device_id,
        detail=f"assigned device {updated_device.serial_number} to group {payload.linkage_group_id}",
    )
    return DeviceRead.model_validate(refreshed_device)


@router.post("/{device_id}/assign-protocol", response_model=DeviceRead)
async def assign_protocol(
    device_id: int,
    payload: DeviceAssignProtocolProfile,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> DeviceRead:
    device = await get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    profile = None
    if payload.protocol_profile_id is not None:
        profile = await get_protocol_profile_by_id(db, payload.protocol_profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Protocol profile not found",
            )
        if not profile.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Protocol profile is inactive",
            )

    updated_device = await assign_device_protocol_profile(db, device, profile)
    refreshed_device = await get_device_by_id(db, updated_device.id)
    await write_operation_log(
        db,
        action="assign_device_protocol_profile",
        target_type="device",
        actor_user_id=current_admin.id,
        target_id=device_id,
        detail=(
            f"assigned protocol profile {payload.protocol_profile_id} "
            f"to device {updated_device.serial_number}"
        ),
    )
    return DeviceRead.model_validate(refreshed_device)


@router.post("/{device_id}/unbind", response_model=DeviceRead)
async def release_device_owner(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceRead:
    device = await get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    if current_user.role != "super_admin" and device.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    updated_device = await unbind_device(db, device)
    refreshed_device = await get_device_by_id(db, updated_device.id)
    await write_operation_log(
        db,
        action="unbind_device",
        target_type="device",
        actor_user_id=current_user.id,
        target_id=device_id,
        detail=f"unbound device {updated_device.serial_number}",
    )
    return DeviceRead.model_validate(refreshed_device)


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


@router.delete("/{device_id}", response_model=DeviceDeleteResult)
async def remove_device(
    device_id: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> DeviceDeleteResult:
    device = await get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    try:
        await delete_device(db, device)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    await write_operation_log(
        db,
        action="delete_device",
        target_type="device",
        actor_user_id=current_admin.id,
        target_id=device_id,
        detail=f"deleted device {device.serial_number}",
    )
    return DeviceDeleteResult(device_id=device_id)
