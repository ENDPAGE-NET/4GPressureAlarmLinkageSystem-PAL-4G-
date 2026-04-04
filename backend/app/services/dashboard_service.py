import csv
import io
from datetime import datetime

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alarm_record import AlarmRecord
from app.models.device import Device
from app.models.module import Module
from app.models.relay_command import RelayCommand
from app.models.user import User
from app.schemas.dashboard import (
    DashboardAlarmItem,
    DashboardAlarmPage,
    DashboardCharts,
    DashboardDeviceDetail,
    DashboardHome,
    DashboardModulePanelItem,
    DashboardRelayCommandItem,
    DashboardRelayCommandPage,
    DashboardTrendPoint,
    MiniProgramAlarmItem,
    MiniProgramAlarmPage,
    MiniProgramDeviceItem,
    MiniProgramHome,
    PaginationMeta,
)
from app.services.alarm_service import can_access_device
from app.services.device_service import (
    get_device_by_id,
    get_device_monitoring_list,
    get_device_overview,
    get_device_statistics,
)


async def list_dashboard_module_panels(
    db: AsyncSession,
    user: User,
) -> list[DashboardModulePanelItem]:
    stmt = select(Module, Device).join(Device, Module.device_id == Device.id)
    if user.role != "super_admin":
        stmt = stmt.where(Device.owner_id == user.id)

    rows = (
        await db.execute(
            stmt.order_by(Device.name.asc(), Device.id.asc(), Module.module_code.asc(), Module.id.asc())
        )
    ).all()

    module_ids = [module.id for module, _device in rows]
    latest_alarm_map: dict[int, AlarmRecord] = {}
    if module_ids:
        alarm_rows = (
            await db.execute(
                select(AlarmRecord)
                .where(AlarmRecord.module_id.in_(module_ids))
                .order_by(
                    AlarmRecord.module_id.asc(),
                    AlarmRecord.triggered_at.desc(),
                    AlarmRecord.id.desc(),
                )
            )
        ).scalars().all()
        for alarm in alarm_rows:
            latest_alarm_map.setdefault(alarm.module_id, alarm)

    return [
        DashboardModulePanelItem(
            module_id=module.id,
            device_id=device.id,
            device_name=device.name,
            serial_number=device.serial_number,
            module_code=module.module_code,
            is_online=module.is_online,
            battery_level=module.battery_level,
            voltage_value=module.voltage_value,
            relay_state=module.relay_state,
            last_seen_at=module.last_seen_at,
            latest_alarm_type=latest_alarm_map.get(module.id).alarm_type
            if latest_alarm_map.get(module.id)
            else None,
            latest_alarm_time=latest_alarm_map.get(module.id).triggered_at
            if latest_alarm_map.get(module.id)
            else None,
        )
        for module, device in rows
    ]


async def get_dashboard_home(db: AsyncSession, user: User) -> DashboardHome:
    overview = await get_device_overview(db, user)
    statistics = await get_device_statistics(db, user)
    monitoring = await get_device_monitoring_list(db, user)
    module_panels = (
        await list_dashboard_module_panels(db, user) if user.role != "super_admin" else []
    )

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

    if user.role != "super_admin":
        recent_alarm_stmt = recent_alarm_stmt.where(Device.owner_id == user.id)
        pending_command_stmt = pending_command_stmt.where(Device.owner_id == user.id)

    recent_alarm_count = (await db.execute(recent_alarm_stmt)).scalar_one() or 0
    pending_command_count = (await db.execute(pending_command_stmt)).scalar_one() or 0

    return DashboardHome(
        overview=overview,
        statistics=statistics,
        monitoring=monitoring[:10],
        module_panels=module_panels,
        recent_alarm_count=recent_alarm_count,
        pending_command_count=pending_command_count,
    )


async def list_dashboard_recent_alarms(
    db: AsyncSession,
    user: User,
    limit: int = 10,
    offset: int = 0,
    keyword: str | None = None,
    alarm_type: str | None = None,
    alarm_status: str | None = None,
    source: str | None = None,
    linkage_status: str | None = None,
    triggered_from: datetime | None = None,
    triggered_to: datetime | None = None,
) -> list[DashboardAlarmItem]:
    stmt = (
        select(AlarmRecord, Module, Device)
        .join(Module, AlarmRecord.module_id == Module.id)
        .join(Device, Module.device_id == Device.id)
    )
    if user.role != "super_admin":
        stmt = stmt.where(Device.owner_id == user.id)
    if keyword:
        fuzzy = f"%{keyword.strip()}%"
        stmt = stmt.where(or_(Device.name.ilike(fuzzy), Module.module_code.ilike(fuzzy)))
    if alarm_type:
        stmt = stmt.where(AlarmRecord.alarm_type == alarm_type)
    if alarm_status:
        stmt = stmt.where(AlarmRecord.alarm_status == alarm_status)
    if source:
        stmt = stmt.where(AlarmRecord.source == source)
    if linkage_status:
        stmt = stmt.where(AlarmRecord.linkage_status == linkage_status)
    if triggered_from:
        stmt = stmt.where(AlarmRecord.triggered_at >= triggered_from)
    if triggered_to:
        stmt = stmt.where(AlarmRecord.triggered_at <= triggered_to)

    rows = (
        await db.execute(
            stmt.order_by(AlarmRecord.triggered_at.desc(), AlarmRecord.id.desc())
            .offset(offset)
            .limit(limit)
        )
    ).all()
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


async def get_dashboard_alarm_page(
    db: AsyncSession,
    user: User,
    limit: int = 10,
    offset: int = 0,
    keyword: str | None = None,
    alarm_type: str | None = None,
    alarm_status: str | None = None,
    source: str | None = None,
    linkage_status: str | None = None,
    triggered_from: datetime | None = None,
    triggered_to: datetime | None = None,
) -> DashboardAlarmPage:
    items = await list_dashboard_recent_alarms(
        db,
        user,
        limit=limit,
        offset=offset,
        keyword=keyword,
        alarm_type=alarm_type,
        alarm_status=alarm_status,
        source=source,
        linkage_status=linkage_status,
        triggered_from=triggered_from,
        triggered_to=triggered_to,
    )
    count_stmt = (
        select(func.count(AlarmRecord.id))
        .join(Module, AlarmRecord.module_id == Module.id)
        .join(Device, Module.device_id == Device.id)
    )
    if user.role != "super_admin":
        count_stmt = count_stmt.where(Device.owner_id == user.id)
    if keyword:
        fuzzy = f"%{keyword.strip()}%"
        count_stmt = count_stmt.where(or_(Device.name.ilike(fuzzy), Module.module_code.ilike(fuzzy)))
    if alarm_type:
        count_stmt = count_stmt.where(AlarmRecord.alarm_type == alarm_type)
    if alarm_status:
        count_stmt = count_stmt.where(AlarmRecord.alarm_status == alarm_status)
    if source:
        count_stmt = count_stmt.where(AlarmRecord.source == source)
    if linkage_status:
        count_stmt = count_stmt.where(AlarmRecord.linkage_status == linkage_status)
    if triggered_from:
        count_stmt = count_stmt.where(AlarmRecord.triggered_at >= triggered_from)
    if triggered_to:
        count_stmt = count_stmt.where(AlarmRecord.triggered_at <= triggered_to)
    total = (await db.execute(count_stmt)).scalar_one() or 0
    return DashboardAlarmPage(
        items=items,
        pagination=PaginationMeta(total=total, limit=limit, offset=offset),
    )


async def list_dashboard_recent_commands(
    db: AsyncSession,
    user: User,
    limit: int = 10,
    offset: int = 0,
) -> list[DashboardRelayCommandItem]:
    stmt = (
        select(RelayCommand, Module, Device)
        .join(Module, RelayCommand.module_id == Module.id)
        .join(Device, Module.device_id == Device.id)
    )
    if user.role != "super_admin":
        stmt = stmt.where(Device.owner_id == user.id)

    rows = (
        await db.execute(
            stmt.order_by(RelayCommand.created_at.desc(), RelayCommand.id.desc())
            .offset(offset)
            .limit(limit)
        )
    ).all()
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


async def get_dashboard_command_page(
    db: AsyncSession,
    user: User,
    limit: int = 10,
    offset: int = 0,
) -> DashboardRelayCommandPage:
    items = await list_dashboard_recent_commands(db, user, limit=limit, offset=offset)
    count_stmt = (
        select(func.count(RelayCommand.id))
        .join(Module, RelayCommand.module_id == Module.id)
        .join(Device, Module.device_id == Device.id)
    )
    if user.role != "super_admin":
        count_stmt = count_stmt.where(Device.owner_id == user.id)
    total = (await db.execute(count_stmt)).scalar_one() or 0
    return DashboardRelayCommandPage(
        items=items,
        pagination=PaginationMeta(total=total, limit=limit, offset=offset),
    )


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


async def get_miniprogram_home(db: AsyncSession, user: User) -> MiniProgramHome:
    monitoring = await get_device_monitoring_list(db, user)
    pending_command_stmt = (
        select(func.count(RelayCommand.id))
        .join(Module, RelayCommand.module_id == Module.id)
        .join(Device, Module.device_id == Device.id)
        .where(RelayCommand.execution_status.in_(["queued", "pending"]))
    )
    triggered_alarm_stmt = (
        select(func.count(AlarmRecord.id))
        .join(Module, AlarmRecord.module_id == Module.id)
        .join(Device, Module.device_id == Device.id)
        .where(AlarmRecord.alarm_status == "triggered")
    )
    if user.role != "super_admin":
        pending_command_stmt = pending_command_stmt.where(Device.owner_id == user.id)
        triggered_alarm_stmt = triggered_alarm_stmt.where(Device.owner_id == user.id)

    # 小程序首页不需要全量统计，只保留最直接的 4 个摘要指标。
    return MiniProgramHome(
        device_count=len(monitoring),
        online_device_count=sum(1 for item in monitoring if item.online_module_count > 0),
        triggered_alarm_count=(await db.execute(triggered_alarm_stmt)).scalar_one() or 0,
        pending_command_count=(await db.execute(pending_command_stmt)).scalar_one() or 0,
    )


async def list_my_recent_alarms(
    db: AsyncSession,
    user: User,
    limit: int = 10,
    offset: int = 0,
) -> list[MiniProgramAlarmItem]:
    stmt = (
        select(AlarmRecord, Module, Device)
        .join(Module, AlarmRecord.module_id == Module.id)
        .join(Device, Module.device_id == Device.id)
    )
    if user.role != "super_admin":
        stmt = stmt.where(Device.owner_id == user.id)

    rows = (
        await db.execute(
            stmt.order_by(AlarmRecord.triggered_at.desc(), AlarmRecord.id.desc())
            .offset(offset)
            .limit(limit)
        )
    ).all()
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


async def get_my_alarm_page(
    db: AsyncSession,
    user: User,
    limit: int = 10,
    offset: int = 0,
) -> MiniProgramAlarmPage:
    items = await list_my_recent_alarms(db, user, limit=limit, offset=offset)
    count_stmt = (
        select(func.count(AlarmRecord.id))
        .join(Module, AlarmRecord.module_id == Module.id)
        .join(Device, Module.device_id == Device.id)
    )
    if user.role != "super_admin":
        count_stmt = count_stmt.where(Device.owner_id == user.id)
    total = (await db.execute(count_stmt)).scalar_one() or 0
    return MiniProgramAlarmPage(
        items=items,
        pagination=PaginationMeta(total=total, limit=limit, offset=offset),
    )


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
        func.sum(case((Device.status == "active", 1), else_=0)),
        func.sum(case((Device.status == "inactive", 1), else_=0)),
    )
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


async def get_dashboard_device_detail(
    db: AsyncSession,
    user: User,
    device_id: int,
) -> DashboardDeviceDetail | None:
    device = await get_device_by_id(db, device_id)
    if not device or not can_access_device(user, device):
        return None

    monitoring_items = await get_device_monitoring_list(db, user)
    monitoring_item = next((item for item in monitoring_items if item.device_id == device_id), None)

    # 设备详情页直接返回最近报警和最近指令，前端不再额外拼多次请求。
    recent_alarm_rows = (
        await db.execute(
            select(AlarmRecord, Module)
            .join(Module, AlarmRecord.module_id == Module.id)
            .where(Module.device_id == device_id)
            .order_by(AlarmRecord.triggered_at.desc(), AlarmRecord.id.desc())
            .limit(10)
        )
    ).all()
    recent_command_rows = (
        await db.execute(
            select(RelayCommand, Module)
            .join(Module, RelayCommand.module_id == Module.id)
            .where(Module.device_id == device_id)
            .order_by(RelayCommand.created_at.desc(), RelayCommand.id.desc())
            .limit(10)
        )
    ).all()

    return DashboardDeviceDetail(
        device_id=device.id,
        device_name=device.name,
        serial_number=device.serial_number,
        status=device.status,
        owner_id=device.owner_id,
        linkage_group_id=device.linkage_group_id,
        module_count=monitoring_item.module_count if monitoring_item else len(device.modules),
        online_module_count=monitoring_item.online_module_count if monitoring_item else sum(1 for item in device.modules if item.is_online),
        offline_module_count=monitoring_item.offline_module_count if monitoring_item else sum(1 for item in device.modules if not item.is_online),
        latest_alarm_type=monitoring_item.latest_alarm_type if monitoring_item else None,
        latest_alarm_time=monitoring_item.latest_alarm_time if monitoring_item else None,
        device_status=monitoring_item.device_status if monitoring_item else device.status,
        recent_alarms=[
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
            for alarm, module in recent_alarm_rows
        ],
        recent_commands=[
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
            for command, module in recent_command_rows
        ],
    )


def build_alarm_export_csv(items: list[DashboardAlarmItem]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "alarm_id",
            "device_id",
            "device_name",
            "module_code",
            "alarm_type",
            "alarm_status",
            "source",
            "linkage_status",
            "message",
            "triggered_at",
        ]
    )
    for item in items:
        writer.writerow(
            [
                item.id,
                item.device_id,
                item.device_name,
                item.module_code,
                item.alarm_type,
                item.alarm_status,
                item.source,
                item.linkage_status,
                item.message or "",
                item.triggered_at.isoformat(),
            ]
        )
    return output.getvalue()


def build_command_export_csv(items: list[DashboardRelayCommandItem]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "command_id",
            "device_id",
            "device_name",
            "module_code",
            "command_source",
            "target_state",
            "execution_status",
            "feedback_status",
            "feedback_message",
            "created_at",
            "executed_at",
        ]
    )
    for item in items:
        writer.writerow(
            [
                item.id,
                item.device_id,
                item.device_name,
                item.module_code,
                item.command_source,
                item.target_state,
                item.execution_status,
                item.feedback_status or "",
                item.feedback_message or "",
                item.created_at.isoformat(),
                item.executed_at.isoformat() if item.executed_at else "",
            ]
        )
    return output.getvalue()
