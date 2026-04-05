from datetime import datetime, timezone

from sqlalchemy import case, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.alarm_record import AlarmRecord
from app.models.device import Device
from app.models.device_group import DeviceGroup
from app.models.module import Module
from app.models.module_status_history import ModuleStatusHistory
from app.models.protocol_profile import ProtocolProfile
from app.models.relay_command import RelayCommand
from app.models.user import User
from app.schemas.alarm import AlarmRecordCreate
from app.schemas.device import (
    DeviceAssignOwner,
    DeviceBind,
    DeviceCreate,
    DeviceGroupCreate,
    DeviceGroupPage,
    DeviceGroupRead,
    DeviceGroupUpdate,
    DeviceMonitoringItem,
    DeviceMonitoringPage,
    DeviceOverview,
    DevicePage,
    DeviceStatistics,
    DeviceUpdate,
    ModuleCreate,
    ModuleStatusHistoryPage,
    ModuleStatusReport,
)
from app.services.alarm_service import create_alarm_record
from app.services.linkage_service import dispatch_linkage_for_alarm
from app.services.logging_service import write_communication_log
from app.services.realtime_service import realtime_service


async def get_primary_module_by_device_id(
    db: AsyncSession,
    device_id: int,
) -> Module | None:
    stmt = (
        select(Module)
        .options(selectinload(Module.device))
        .where(Module.device_id == device_id)
        .order_by(Module.id.asc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _ensure_primary_module(
    db: AsyncSession,
    device: Device,
) -> Module:
    # 当前业务按“一个设备一个 SN”处理，这里保留一个默认模块做内部兼容层。
    existing_module = await get_primary_module_by_device_id(db, device.id)
    if existing_module:
        return existing_module

    module = Module(
        device_id=device.id,
        module_code="MAIN",
        serial_number=device.serial_number,
    )
    db.add(module)
    await db.commit()
    await db.refresh(module)
    return module


async def list_devices(db: AsyncSession, user: User) -> list[Device]:
    stmt = select(Device).options(selectinload(Device.modules))
    # 普通用户只能看到自己绑定的设备，管理员可查看全量。
    if user.role != "super_admin":
        stmt = stmt.where(Device.owner_id == user.id)
    stmt = stmt.order_by(Device.id.desc())
    result = await db.execute(stmt)
    return list(result.scalars().unique().all())


async def list_devices_page(
    db: AsyncSession,
    user: User,
    limit: int = 20,
    offset: int = 0,
) -> DevicePage:
    count_stmt = select(func.count(Device.id))
    stmt = (
        select(Device)
        .options(selectinload(Device.modules))
        .order_by(Device.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if user.role != "super_admin":
        count_stmt = count_stmt.where(Device.owner_id == user.id)
        stmt = stmt.where(Device.owner_id == user.id)
    total = (await db.execute(count_stmt)).scalar_one() or 0
    items = list((await db.execute(stmt)).scalars().unique().all())
    return DevicePage(total=total, items=items, limit=limit, offset=offset)


async def get_device_by_id(db: AsyncSession, device_id: int) -> Device | None:
    stmt = (
        select(Device)
        .execution_options(populate_existing=True)
        .options(
            selectinload(Device.modules),
            selectinload(Device.linkage_group),
            selectinload(Device.protocol_profile),
        )
        .where(Device.id == device_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_device_by_serial_number(db: AsyncSession, serial_number: str) -> Device | None:
    result = await db.execute(
        select(Device)
        .options(selectinload(Device.linkage_group), selectinload(Device.protocol_profile))
        .where(Device.serial_number == serial_number)
    )
    return result.scalar_one_or_none()


async def create_device(db: AsyncSession, payload: DeviceCreate, owner: User) -> Device:
    # 管理员创建的设备先不强绑 owner，便于后续再分配或由普通用户主动绑定。
    device = Device(
        name=payload.name,
        serial_number=payload.serial_number,
        owner_id=owner.id,
        status="inactive",
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    await _ensure_primary_module(db, device)
    return device


async def list_device_groups(db: AsyncSession, user: User) -> list[DeviceGroup]:
    stmt = select(DeviceGroup).options(selectinload(DeviceGroup.devices)).order_by(
        DeviceGroup.id.desc()
    )
    if user.role != "super_admin":
        stmt = stmt.where(DeviceGroup.owner_id == user.id)
    return list((await db.execute(stmt)).scalars().unique().all())


async def list_device_groups_page(
    db: AsyncSession,
    user: User,
    limit: int = 20,
    offset: int = 0,
) -> DeviceGroupPage:
    count_stmt = select(func.count(DeviceGroup.id))
    stmt = (
        select(DeviceGroup)
        .options(selectinload(DeviceGroup.devices))
        .order_by(DeviceGroup.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if user.role != "super_admin":
        count_stmt = count_stmt.where(DeviceGroup.owner_id == user.id)
        stmt = stmt.where(DeviceGroup.owner_id == user.id)
    total = (await db.execute(count_stmt)).scalar_one() or 0
    groups = list((await db.execute(stmt)).scalars().unique().all())
    items = [build_device_group_read(group) for group in groups]
    return DeviceGroupPage(total=total, items=items, limit=limit, offset=offset)


async def get_device_group_by_id(db: AsyncSession, group_id: int) -> DeviceGroup | None:
    stmt = (
        select(DeviceGroup)
        .options(selectinload(DeviceGroup.devices))
        .where(DeviceGroup.id == group_id)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_device_group_by_name(db: AsyncSession, name: str) -> DeviceGroup | None:
    stmt = select(DeviceGroup).where(DeviceGroup.name == name)
    return (await db.execute(stmt)).scalar_one_or_none()


async def create_device_group(
    db: AsyncSession,
    payload: DeviceGroupCreate,
    owner: User | None,
) -> DeviceGroup:
    # 联动组描述的是报警传播范围，不等同于账号归属，所以 owner 可为空。
    group = DeviceGroup(
        name=payload.name,
        description=payload.description,
        owner_id=owner.id if owner else None,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def update_device_group(
    db: AsyncSession,
    group: DeviceGroup,
    payload: DeviceGroupUpdate,
    owner: User | None,
) -> DeviceGroup:
    if payload.name is not None:
        group.name = payload.name
    if payload.description is not None:
        group.description = payload.description
    if payload.owner_id is not None:
        group.owner_id = owner.id if owner else None

    await db.commit()
    await db.refresh(group)
    return group


async def assign_device_group(
    db: AsyncSession,
    device: Device,
    group: DeviceGroup | None,
) -> Device:
    # 设备挂组后，后续报警联动优先按组内模块计算目标。
    device.linkage_group_id = group.id if group else None
    await db.commit()
    await db.refresh(device)
    return device


async def delete_device_group(
    db: AsyncSession,
    group: DeviceGroup,
) -> None:
    if group.devices:
        raise ValueError("Device group still has assigned devices")

    await db.execute(delete(DeviceGroup).where(DeviceGroup.id == group.id))
    await db.commit()


def build_device_group_read(group: DeviceGroup) -> DeviceGroupRead:
    return DeviceGroupRead(
        id=group.id,
        name=group.name,
        description=group.description,
        owner_id=group.owner_id,
        created_at=group.created_at,
        updated_at=group.updated_at,
        device_count=len(group.devices),
        device_ids=[device.id for device in group.devices],
    )


async def get_module_by_code(
    db: AsyncSession,
    device_id: int,
    module_code: str,
) -> Module | None:
    stmt = select(Module).where(
        Module.device_id == device_id,
        Module.module_code == module_code,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_device_by_serial_with_protocol(
    db: AsyncSession,
    serial_number: str,
) -> Device | None:
    stmt = (
        select(Device)
        .options(selectinload(Device.protocol_profile))
        .where(Device.serial_number == serial_number)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_module_by_id(db: AsyncSession, module_id: int) -> Module | None:
    stmt = select(Module).options(selectinload(Module.device)).where(Module.id == module_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def add_module_to_device(
    db: AsyncSession,
    device: Device,
    payload: ModuleCreate,
) -> Module:
    # 当前业务不允许一个设备挂多个模块，这里把旧接口收敛成“配置默认模块”。
    existing_module = await get_primary_module_by_device_id(db, device.id)
    if existing_module:
        existing_module.module_code = payload.module_code
        existing_module.serial_number = device.serial_number
        if payload.imei is not None:
            existing_module.imei = payload.imei
        await db.commit()
        await db.refresh(existing_module)
        return existing_module

    module = Module(
        device_id=device.id,
        module_code=payload.module_code,
        serial_number=device.serial_number,
        imei=payload.imei,
    )
    db.add(module)
    await db.commit()
    await db.refresh(module)
    return module


async def bind_device_by_serial(
    db: AsyncSession,
    payload: DeviceBind,
    current_user: User,
) -> Device:
    # 绑定逻辑分两种：已存在但未归属的设备归到当前用户；不存在则按 SN 直接建档。
    # 新模型下优先按模块 SN 绑定所属整套设备，兼容旧的设备级 SN 绑定方式。
    existing_device = await get_device_by_serial_number(db, payload.serial_number)
    if existing_device:
        if existing_device.owner_id and existing_device.owner_id != current_user.id:
            raise ValueError("Device is already bound to another user")
        if existing_device.owner_id != current_user.id:
            existing_device.owner_id = current_user.id
            if payload.name:
                existing_device.name = payload.name
            await db.commit()
            await db.refresh(existing_device)
        return existing_device

    device = Device(
        name=payload.name or payload.serial_number,
        serial_number=payload.serial_number,
        owner_id=current_user.id,
        status="inactive",
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    await _ensure_primary_module(db, device)
    return device


async def update_device(
    db: AsyncSession,
    device: Device,
    payload: DeviceUpdate,
) -> Device:
    # 设备基础资料更新只允许改展示信息和业务状态，不允许改 SN。
    if payload.name is not None:
        device.name = payload.name
    if payload.status is not None:
        device.status = payload.status

    await db.commit()
    await db.refresh(device)
    return device


async def assign_device_owner(
    db: AsyncSession,
    device: Device,
    payload: DeviceAssignOwner,
    owner: User | None,
) -> Device:
    # 设备归属调整统一收口到这里，owner 为空表示回收为未归属设备。
    device.owner_id = owner.id if owner else None
    await db.commit()
    await db.refresh(device)
    return device


async def unbind_device(
    db: AsyncSession,
    device: Device,
) -> Device:
    # 解绑后保留设备与历史数据，只清掉账号归属。
    device.owner_id = None
    await db.commit()
    await db.refresh(device)
    return device


async def delete_module(
    db: AsyncSession,
    module: Module,
) -> None:
    alarm_count = (
        await db.execute(
            select(func.count(AlarmRecord.id)).where(AlarmRecord.module_id == module.id)
        )
    ).scalar_one()
    command_count = (
        await db.execute(
            select(func.count(RelayCommand.id)).where(RelayCommand.module_id == module.id)
        )
    ).scalar_one()

    # 已产生报警或联动记录的模块不能直接删，否则会破坏追溯链路。
    if alarm_count or command_count:
        raise ValueError("Module has historical records and cannot be deleted")

    await db.execute(delete(Module).where(Module.id == module.id))
    await db.commit()


async def delete_device(
    db: AsyncSession,
    device: Device,
) -> None:
    module_count = (
        await db.execute(select(func.count(Module.id)).where(Module.device_id == device.id))
    ).scalar_one()

    # 设备只有在完全空载时才允许删除，避免把模块历史一起带丢。
    if module_count:
        raise ValueError("Device still has modules and cannot be deleted")

    await db.execute(delete(Device).where(Device.id == device.id))
    await db.commit()


async def delete_device(
    db: AsyncSession,
    device: Device,
) -> None:
    # 覆盖旧实现：当前业务允许删除仅带一个默认兼容模块、且没有历史记录的设备。
    modules = list(
        (
            await db.execute(
                select(Module).where(Module.device_id == device.id).order_by(Module.id.asc())
            )
        ).scalars().all()
    )
    if len(modules) > 1:
        raise ValueError("Device still has multiple modules and cannot be deleted")

    if len(modules) == 1:
        module = modules[0]
        alarm_count = (
            await db.execute(
                select(func.count(AlarmRecord.id)).where(AlarmRecord.module_id == module.id)
            )
        ).scalar_one()
        command_count = (
            await db.execute(
                select(func.count(RelayCommand.id)).where(RelayCommand.module_id == module.id)
            )
        ).scalar_one()
        if alarm_count or command_count:
            raise ValueError("Device still has module history and cannot be deleted")
        await db.execute(delete(Module).where(Module.id == module.id))

    await db.execute(delete(Device).where(Device.id == device.id))
    await db.commit()


async def update_module_status(
    db: AsyncSession,
    module: Module,
    payload: ModuleStatusReport,
) -> Module:
    # 这里作为统一的“状态入口”，HTTP 上报和后续 MQTT 上报都可以复用这段逻辑。
    module.is_online = payload.is_online
    module.last_seen_at = datetime.now(timezone.utc)

    if payload.relay_state is not None:
        module.relay_state = payload.relay_state
    if payload.battery_level is not None:
        module.battery_level = payload.battery_level
    if payload.voltage_value is not None:
        module.voltage_value = payload.voltage_value

    await db.commit()
    await db.refresh(module)

    # 模块每次状态上报都写入专门的状态历史表，后续统计与轨迹查询不再依赖运行日志反推。
    status_history = ModuleStatusHistory(
        module_id=module.id,
        device_id=module.device_id,
        source=payload.source,
        is_online=module.is_online,
        relay_state=module.relay_state,
        battery_level=module.battery_level,
        voltage_value=module.voltage_value,
        trigger_alarm_type=payload.trigger_alarm_type,
        alarm_message=payload.alarm_message,
        reported_at=module.last_seen_at or datetime.now(timezone.utc),
    )
    db.add(status_history)
    await db.commit()

    await write_communication_log(
        db,
        channel=payload.source if payload.source != "http_report" else "http",
        direction="inbound",
        status="success",
        device_serial=module.device.serial_number if module.device else None,
        module_code=module.module_code,
        payload=payload.model_dump(),
        message="module status updated",
    )

    await realtime_service.broadcast(
        "module.status_updated",
        {
            "module_id": module.id,
            "device_id": module.device_id,
            "serial_number": module.device.serial_number if module.device else None,
            "module_serial_number": module.serial_number,
            "module_code": module.module_code,
            "is_online": module.is_online,
            "relay_state": module.relay_state,
            "battery_level": module.battery_level,
            "voltage_value": module.voltage_value,
            "last_seen_at": module.last_seen_at.isoformat() if module.last_seen_at else None,
        },
        owner_id=module.device.owner_id if module.device else None,
    )

    if payload.trigger_alarm_type:
        # 上报里带了报警类型时，顺手落一条报警记录，先形成最小业务闭环。
        alarm = await create_alarm_record(
            db,
            AlarmRecordCreate(
                module_id=module.id,
                alarm_type=payload.trigger_alarm_type,
                source=payload.source,
                message=payload.alarm_message,
            ),
        )
        await dispatch_linkage_for_alarm(db, alarm)
        await realtime_service.broadcast(
            "alarm.created",
            {
                "alarm_id": alarm.id,
                "module_id": alarm.module_id,
                "device_id": module.device_id,
                "alarm_type": alarm.alarm_type,
                "alarm_status": alarm.alarm_status,
                "source": alarm.source,
                "linkage_status": alarm.linkage_status,
                "triggered_at": alarm.triggered_at.isoformat(),
            },
            owner_id=module.device.owner_id if module.device else None,
        )

    refreshed = await get_module_by_id(db, module.id)
    return refreshed or module


async def get_module_status_history_page(
    db: AsyncSession,
    module_id: int,
    limit: int = 20,
    offset: int = 0,
) -> ModuleStatusHistoryPage:
    count_stmt = select(func.count(ModuleStatusHistory.id)).where(
        ModuleStatusHistory.module_id == module_id
    )
    stmt = (
        select(ModuleStatusHistory)
        .where(ModuleStatusHistory.module_id == module_id)
        .order_by(ModuleStatusHistory.reported_at.desc(), ModuleStatusHistory.id.desc())
        .limit(limit)
        .offset(offset)
    )
    total = (await db.execute(count_stmt)).scalar_one() or 0
    items = list((await db.execute(stmt)).scalars().all())
    return ModuleStatusHistoryPage(
        total=total,
        items=items,
        limit=limit,
        offset=offset,
    )


async def get_device_overview(db: AsyncSession, user: User) -> DeviceOverview:
    # 总览接口先聚合最核心的 5 个指标，后续可继续补运行率、报警频次等统计维度。
    device_stmt = select(func.count(Device.id))
    module_stmt = select(
        func.count(Module.id),
        func.sum(case((Module.is_online.is_(True), 1), else_=0)),
    ).join(Device, Module.device_id == Device.id)
    alarm_stmt = (
        select(func.count(AlarmRecord.id))
        .join(Module, AlarmRecord.module_id == Module.id)
        .join(Device, Module.device_id == Device.id)
        .where(AlarmRecord.alarm_status == "triggered")
    )

    if user.role != "super_admin":
        device_stmt = device_stmt.where(Device.owner_id == user.id)
        module_stmt = module_stmt.where(Device.owner_id == user.id)
        alarm_stmt = alarm_stmt.where(Device.owner_id == user.id)

    total_devices = (await db.execute(device_stmt)).scalar_one() or 0
    module_result = (await db.execute(module_stmt)).one()
    total_modules = module_result[0] or 0
    online_modules = module_result[1] or 0
    triggered_alarm_count = (await db.execute(alarm_stmt)).scalar_one() or 0

    return DeviceOverview(
        total_devices=total_devices,
        total_modules=total_modules,
        online_modules=online_modules,
        offline_modules=max(total_modules - online_modules, 0),
        triggered_alarm_count=triggered_alarm_count,
    )


async def get_device_statistics(db: AsyncSession, user: User) -> DeviceStatistics:
    # 统计接口在总览的基础上补齐报警类型维度，供后台首页和图表直接使用。
    device_stmt = select(func.count(Device.id))
    owned_device_stmt = select(func.count(Device.id)).where(Device.owner_id.is_not(None))
    module_stmt = select(
        func.count(Module.id),
        func.sum(case((Module.is_online.is_(True), 1), else_=0)),
    ).join(Device, Module.device_id == Device.id)
    alarm_stmt = (
        select(
            func.count(AlarmRecord.id),
            func.sum(case((AlarmRecord.alarm_type == "low_battery", 1), else_=0)),
            func.sum(case((AlarmRecord.alarm_type.in_(["low_voltage", "high_voltage"]), 1), else_=0)),
        )
        .join(Module, AlarmRecord.module_id == Module.id)
        .join(Device, Module.device_id == Device.id)
        .where(AlarmRecord.alarm_status == "triggered")
    )

    if user.role != "super_admin":
        device_stmt = device_stmt.where(Device.owner_id == user.id)
        owned_device_stmt = owned_device_stmt.where(Device.owner_id == user.id)
        module_stmt = module_stmt.where(Device.owner_id == user.id)
        alarm_stmt = alarm_stmt.where(Device.owner_id == user.id)

    total_devices = (await db.execute(device_stmt)).scalar_one() or 0
    owned_devices = (await db.execute(owned_device_stmt)).scalar_one() or 0
    module_result = (await db.execute(module_stmt)).one()
    total_modules = module_result[0] or 0
    online_modules = module_result[1] or 0
    offline_modules = max(total_modules - online_modules, 0)
    alarm_result = (await db.execute(alarm_stmt)).one()
    triggered_alarm_count = alarm_result[0] or 0
    low_battery_alarm_count = alarm_result[1] or 0
    low_voltage_alarm_count = alarm_result[2] or 0

    return DeviceStatistics(
        total_devices=total_devices,
        owned_devices=owned_devices,
        total_modules=total_modules,
        online_modules=online_modules,
        offline_modules=offline_modules,
        online_rate=(online_modules / total_modules) if total_modules else 0.0,
        triggered_alarm_count=triggered_alarm_count,
        low_battery_alarm_count=low_battery_alarm_count,
        low_voltage_alarm_count=low_voltage_alarm_count,
    )


async def get_device_monitoring_list(
    db: AsyncSession,
    user: User,
) -> list[DeviceMonitoringItem]:
    devices = await list_devices(db, user)
    monitoring_items: list[DeviceMonitoringItem] = []

    for device in devices:
        online_module_count = sum(1 for module in device.modules if module.is_online)
        module_count = len(device.modules)
        offline_module_count = max(module_count - online_module_count, 0)

        latest_alarm_stmt = (
            select(AlarmRecord)
            .join(Module, AlarmRecord.module_id == Module.id)
            .where(Module.device_id == device.id)
            .order_by(AlarmRecord.triggered_at.desc(), AlarmRecord.id.desc())
            .limit(1)
        )
        latest_alarm = (await db.execute(latest_alarm_stmt)).scalar_one_or_none()

        # 设备状态先按模块在线情况简单归类，后续接入心跳阈值后再细化。
        if module_count == 0:
            device_status = "no_modules"
        elif online_module_count == module_count:
            device_status = "all_online"
        elif online_module_count == 0:
            device_status = "all_offline"
        else:
            device_status = "part_online"

        monitoring_items.append(
            DeviceMonitoringItem(
                device_id=device.id,
                device_name=device.name,
                serial_number=device.serial_number,
                owner_id=device.owner_id,
                module_count=module_count,
                online_module_count=online_module_count,
                offline_module_count=offline_module_count,
                latest_alarm_type=latest_alarm.alarm_type if latest_alarm else None,
                latest_alarm_time=latest_alarm.triggered_at if latest_alarm else None,
                device_status=device_status,
            )
        )

    return monitoring_items


async def get_device_monitoring_page(
    db: AsyncSession,
    user: User,
    limit: int = 20,
    offset: int = 0,
) -> DeviceMonitoringPage:
    items = await get_device_monitoring_list(db, user)
    total = len(items)
    paged_items = items[offset : offset + limit]
    return DeviceMonitoringPage(total=total, items=paged_items, limit=limit, offset=offset)
