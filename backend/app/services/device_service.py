from datetime import datetime, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.alarm_record import AlarmRecord
from app.models.device import Device
from app.models.module import Module
from app.models.user import User
from app.schemas.alarm import AlarmRecordCreate
from app.schemas.device import (
    DeviceBind,
    DeviceCreate,
    DeviceOverview,
    ModuleCreate,
    ModuleStatusReport,
)
from app.services.alarm_service import create_alarm_record


async def list_devices(db: AsyncSession, user: User) -> list[Device]:
    stmt = select(Device).options(selectinload(Device.modules))
    if user.role != "super_admin":
        stmt = stmt.where(Device.owner_id == user.id)
    stmt = stmt.order_by(Device.id.desc())
    result = await db.execute(stmt)
    return list(result.scalars().unique().all())


async def get_device_by_id(db: AsyncSession, device_id: int) -> Device | None:
    stmt = (
        select(Device)
        .execution_options(populate_existing=True)
        .options(selectinload(Device.modules))
        .where(Device.id == device_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_device_by_serial_number(db: AsyncSession, serial_number: str) -> Device | None:
    result = await db.execute(select(Device).where(Device.serial_number == serial_number))
    return result.scalar_one_or_none()


async def create_device(db: AsyncSession, payload: DeviceCreate, owner: User) -> Device:
    device = Device(
        name=payload.name,
        serial_number=payload.serial_number,
        owner_id=owner.id if owner.role != "super_admin" else None,
        status="inactive",
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


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


async def get_module_by_id(db: AsyncSession, module_id: int) -> Module | None:
    stmt = select(Module).options(selectinload(Module.device)).where(Module.id == module_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def add_module_to_device(
    db: AsyncSession,
    device: Device,
    payload: ModuleCreate,
) -> Module:
    module = Module(device_id=device.id, module_code=payload.module_code)
    db.add(module)
    await db.commit()
    await db.refresh(module)
    return module


async def bind_device_by_serial(
    db: AsyncSession,
    payload: DeviceBind,
    current_user: User,
) -> Device:
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
    return device


async def update_module_status(
    db: AsyncSession,
    module: Module,
    payload: ModuleStatusReport,
) -> Module:
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

    if payload.trigger_alarm_type:
        await create_alarm_record(
            db,
            AlarmRecordCreate(
                module_id=module.id,
                alarm_type=payload.trigger_alarm_type,
                message=payload.alarm_message,
            ),
        )

    refreshed = await get_module_by_id(db, module.id)
    return refreshed or module


async def get_device_overview(db: AsyncSession, user: User) -> DeviceOverview:
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
