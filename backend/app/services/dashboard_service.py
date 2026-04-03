from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.alarm_record import AlarmRecord
from app.models.device import Device
from app.models.module import Module
from app.models.relay_command import RelayCommand
from app.models.user import User
from app.schemas.dashboard import (
    DashboardAlarmItem,
    DashboardCharts,
    DashboardHome,
    DashboardRelayCommandItem,
    DashboardTrendPoint,
    MiniProgramAlarmItem,
    MiniProgramDeviceItem,
)
from app.services.device_service import (
    get_device_monitoring_list,
    get_device_overview,
    get_device_statistics,
)


async def get_dashboard_home(db: AsyncSession, user: User) -> DashboardHome:
    overview = await get_device_overview(db, user)
    statistics = await get_device_statistics(db, user)
    monitoring = await get_device_monitoring_list(db, user)

    recent_alarm_stmt = (
        select(func.count(AlarmRecord.id))
        .join(Module, AlarmRecord.module_id == Module.id)
        .join(Device, Module.device_id == Device.id)
        .where(AlarmRecord.alarm_status == "triggered")
    )
    pending_command_stmt = (
        select(func.count(RelayCommand.id))
        .join(Module, RelayCommand.module_id == Module.id)
        .join(Device, Module.device_id == Device.id)
        .where(RelayCommand.execution_status.in_(["queued", "pending"]))
    )

    # 首页聚合接口要遵守账号可见范围，普通用户只能看到自己名下设备数据。
    if user.role != "super_admin":
        recent_alarm_stmt = recent_alarm_stmt.where(Device.owner_id == user.id)
        pending_command_stmt = pending_command_stmt.where(Device.owner_id == user.id)

    recent_alarm_count = (await db.execute(recent_alarm_stmt)).scalar_one() or 0
    pending_command_count = (await db.execute(pending_command_stmt)).scalar_one() or 0

    return DashboardHome(
        overview=overview,
        statistics=statistics,
        monitoring=monitoring[:10],
        recent_alarm_count=recent_alarm_count,
        pending_command_count=pending_command_count,
    )


async def list_dashboard_recent_alarms(
    db: AsyncSession,
    user: User,
    limit: int = 10,
) -> list[DashboardAlarmItem]:
    stmt = (
        select(AlarmRecord, Module, Device)
        .join(Module, AlarmRecord.module_id == Module.id)
        .join(Device, Module.device_id == Device.id)
        .order_by(AlarmRecord.triggered_at.desc(), AlarmRecord.id.desc())
        .limit(limit)
    )
    if user.role != "super_admin":
        stmt = stmt.where(Device.owner_id == user.id)

    rows = (await db.execute(stmt)).all()
    return [
        DashboardAlarmItem(
            id=alarm.id,
            module_id=alarm.module_id,
            device_id=device.id,
            device_name=device.name,
            module_code=module.module_code,
            alarm_type=alarm.alarm_type,
            alarm_status=alarm.alarm_status,
            source=alarm.source,
            linkage_status=alarm.linkage_status,
            message=alarm.message,
            triggered_at=alarm.triggered_at,
        )
        for alarm, module, device in rows
    ]


async def list_dashboard_recent_commands(
    db: AsyncSession,
    user: User,
    limit: int = 10,
) -> list[DashboardRelayCommandItem]:
    stmt = (
        select(RelayCommand, Module, Device)
        .join(Module, RelayCommand.module_id == Module.id)
        .join(Device, Module.device_id == Device.id)
        .order_by(RelayCommand.created_at.desc(), RelayCommand.id.desc())
        .limit(limit)
    )
    if user.role != "super_admin":
        stmt = stmt.where(Device.owner_id == user.id)

    rows = (await db.execute(stmt)).all()
    return [
        DashboardRelayCommandItem(
            id=command.id,
            module_id=command.module_id,
            device_id=device.id,
            device_name=device.name,
            module_code=module.module_code,
            command_source=command.command_source,
            target_state=command.target_state,
            execution_status=command.execution_status,
            feedback_status=command.feedback_status,
            feedback_message=command.feedback_message,
            created_at=command.created_at,
            executed_at=command.executed_at,
        )
        for command, module, device in rows
    ]


async def list_my_devices(db: AsyncSession, user: User) -> list[MiniProgramDeviceItem]:
    monitoring = await get_device_monitoring_list(db, user)
    return [
        MiniProgramDeviceItem(
            device_id=item.device_id,
            device_name=item.device_name,
            serial_number=item.serial_number,
            module_count=item.module_count,
            online_module_count=item.online_module_count,
            latest_alarm_type=item.latest_alarm_type,
            latest_alarm_time=item.latest_alarm_time,
            device_status=item.device_status,
        )
        for item in monitoring
    ]


async def list_my_recent_alarms(
    db: AsyncSession,
    user: User,
    limit: int = 10,
) -> list[MiniProgramAlarmItem]:
    stmt = (
        select(AlarmRecord, Module, Device)
        .join(Module, AlarmRecord.module_id == Module.id)
        .join(Device, Module.device_id == Device.id)
        .order_by(AlarmRecord.triggered_at.desc(), AlarmRecord.id.desc())
        .limit(limit)
    )
    if user.role != "super_admin":
        stmt = stmt.where(Device.owner_id == user.id)

    rows = (await db.execute(stmt)).all()
    return [
        MiniProgramAlarmItem(
            id=alarm.id,
            device_id=device.id,
            device_name=device.name,
            module_code=module.module_code,
            alarm_type=alarm.alarm_type,
            alarm_status=alarm.alarm_status,
            triggered_at=alarm.triggered_at,
            message=alarm.message,
        )
        for alarm, module, device in rows
    ]


async def get_dashboard_charts(db: AsyncSession, user: User) -> DashboardCharts:
    alarm_stmt = (
        select(AlarmRecord.alarm_type, func.count(AlarmRecord.id))
        .join(Module, AlarmRecord.module_id == Module.id)
        .join(Device, Module.device_id == Device.id)
        .group_by(AlarmRecord.alarm_type)
        .order_by(func.count(AlarmRecord.id).desc(), AlarmRecord.alarm_type.asc())
    )
    command_stmt = (
        select(RelayCommand.execution_status, func.count(RelayCommand.id))
        .join(Module, RelayCommand.module_id == Module.id)
        .join(Device, Module.device_id == Device.id)
        .group_by(RelayCommand.execution_status)
        .order_by(func.count(RelayCommand.id).desc(), RelayCommand.execution_status.asc())
    )
    device_status_stmt = select(
        func.count(Device.id),
        func.sum(
            case(
                (
                    Device.status == "active",
                    1,
                ),
                else_=0,
            )
        ),
        func.sum(
            case(
                (
                    Device.status == "inactive",
                    1,
                ),
                else_=0,
            )
        ),
    )

    # 图表接口也要按用户权限裁剪，保证 Web 和小程序直接复用时不越权。
    if user.role != "super_admin":
        alarm_stmt = alarm_stmt.where(Device.owner_id == user.id)
        command_stmt = command_stmt.where(Device.owner_id == user.id)
        device_status_stmt = device_status_stmt.where(Device.owner_id == user.id)

    alarm_rows = (await db.execute(alarm_stmt)).all()
    command_rows = (await db.execute(command_stmt)).all()
    device_status_row = (await db.execute(device_status_stmt)).one()

    total_devices = device_status_row[0] or 0
    active_devices = device_status_row[1] or 0
    inactive_devices = device_status_row[2] or 0
    other_devices = max(total_devices - active_devices - inactive_devices, 0)

    return DashboardCharts(
        alarm_type_distribution=[
            DashboardTrendPoint(label=alarm_type, value=count)
            for alarm_type, count in alarm_rows
        ],
        command_status_distribution=[
            DashboardTrendPoint(label=execution_status, value=count)
            for execution_status, count in command_rows
        ],
        device_status_distribution=[
            DashboardTrendPoint(label="active", value=active_devices),
            DashboardTrendPoint(label="inactive", value=inactive_devices),
            DashboardTrendPoint(label="other", value=other_devices),
        ],
    )
