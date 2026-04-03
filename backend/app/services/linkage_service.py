from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.alarm_record import AlarmRecord
from app.models.device import Device
from app.models.module import Module
from app.models.relay_command import RelayCommand
from app.schemas.alarm import AlarmLinkageDispatchResult
from app.schemas.relay import RelayCommandCreate, RelayCommandFeedback, RelayRetryResult


async def dispatch_linkage_for_alarm(
    db: AsyncSession,
    alarm: AlarmRecord,
) -> AlarmLinkageDispatchResult:
    trigger_module_stmt = (
        select(Module)
        .options(selectinload(Module.device).selectinload(Device.linkage_group))
        .where(Module.id == alarm.module_id)
    )
    trigger_module = (await db.execute(trigger_module_stmt)).scalar_one_or_none()
    if not trigger_module:
        alarm.linkage_status = "failed"
        alarm.linkage_result = "trigger module not found"
        await db.commit()
        await db.refresh(alarm)
        return AlarmLinkageDispatchResult(
            alarm_id=alarm.id,
            generated_command_count=0,
            dispatched_count=0,
            queued_count=0,
            skipped_count=0,
            linkage_status=alarm.linkage_status,
            linkage_result=alarm.linkage_result or "",
        )

    # 联动优先按设备组找目标；如果设备还没挂组，则退回到原来的“同设备内其他模块”策略。
    if trigger_module.device and trigger_module.device.linkage_group_id:
        target_modules_stmt = (
            select(Module)
            .join(Module.device)
            .where(
                Device.linkage_group_id == trigger_module.device.linkage_group_id,
                Module.id != trigger_module.id,
            )
        )
        no_target_message = "no linkage targets found in the same device group"
    else:
        target_modules_stmt = select(Module).where(
            Module.device_id == trigger_module.device_id,
            Module.id != trigger_module.id,
        )
        no_target_message = "no linkage targets found in the same device"

    target_modules = list((await db.execute(target_modules_stmt)).scalars().all())
    if not target_modules:
        alarm.linkage_status = "no_targets"
        alarm.linkage_result = no_target_message
        await db.commit()
        await db.refresh(alarm)
        return AlarmLinkageDispatchResult(
            alarm_id=alarm.id,
            generated_command_count=0,
            dispatched_count=0,
            queued_count=0,
            skipped_count=0,
            linkage_status=alarm.linkage_status,
            linkage_result=alarm.linkage_result or "",
        )

    generated_command_count = 0
    dispatched_count = 0
    queued_count = 0
    skipped_count = 0

    for target_module in target_modules:
        existing_stmt = select(RelayCommand).where(
            RelayCommand.alarm_record_id == alarm.id,
            RelayCommand.module_id == target_module.id,
        )
        existing_command = (await db.execute(existing_stmt)).scalar_one_or_none()
        if existing_command:
            skipped_count += 1
            continue

        is_online = target_module.is_online
        command = RelayCommand(
            alarm_record_id=alarm.id,
            module_id=target_module.id,
            command_source="alarm_linkage",
            target_state="closed",
            execution_status="dispatched" if is_online else "queued",
            execution_result=(
                "relay close command dispatched immediately"
                if is_online
                else "target module offline, waiting for retry"
            ),
            retry_count=1 if is_online else 0,
            last_attempt_at=datetime.now(timezone.utc) if is_online else None,
        )
        db.add(command)
        generated_command_count += 1
        if is_online:
            dispatched_count += 1
        else:
            queued_count += 1

    if generated_command_count == 0 and skipped_count > 0:
        linkage_status = alarm.linkage_status or "already_generated"
        linkage_result = "linkage commands already exist for this alarm"
    elif queued_count > 0 and dispatched_count > 0:
        linkage_status = "partial_dispatched"
        linkage_result = (
            f"{dispatched_count} commands dispatched, {queued_count} queued for retry"
        )
    elif queued_count > 0:
        linkage_status = "queued"
        linkage_result = f"{queued_count} linkage commands queued for offline modules"
    else:
        linkage_status = "dispatched"
        linkage_result = f"{dispatched_count} linkage commands dispatched"

    alarm.linkage_status = linkage_status
    alarm.linkage_result = linkage_result

    await db.commit()
    await db.refresh(alarm)

    return AlarmLinkageDispatchResult(
        alarm_id=alarm.id,
        generated_command_count=generated_command_count,
        dispatched_count=dispatched_count,
        queued_count=queued_count,
        skipped_count=skipped_count,
        linkage_status=alarm.linkage_status,
        linkage_result=alarm.linkage_result or "",
    )


async def retry_queued_relay_commands(db: AsyncSession) -> RelayRetryResult:
    queued_stmt = (
        select(RelayCommand)
        .options(selectinload(RelayCommand.module))
        .where(RelayCommand.execution_status.in_(["queued", "pending"]))
        .order_by(RelayCommand.created_at.asc(), RelayCommand.id.asc())
    )
    queued_commands = list((await db.execute(queued_stmt)).scalars().all())

    dispatched_count = 0
    still_queued_count = 0
    now = datetime.now(timezone.utc)

    for command in queued_commands:
        command.retry_count += 1
        command.last_attempt_at = now
        if command.module and command.module.is_online:
            command.execution_status = "dispatched"
            command.execution_result = "queued command dispatched after retry scan"
            dispatched_count += 1
        else:
            command.execution_status = "queued"
            command.execution_result = "target module still offline during retry scan"
            still_queued_count += 1

    await db.commit()

    return RelayRetryResult(
        total_scanned=len(queued_commands),
        dispatched_count=dispatched_count,
        still_queued_count=still_queued_count,
    )


async def list_relay_commands(
    db: AsyncSession,
    alarm_record_id: int | None = None,
    execution_status: str | None = None,
) -> list[RelayCommand]:
    stmt = select(RelayCommand).order_by(RelayCommand.created_at.desc(), RelayCommand.id.desc())
    if alarm_record_id:
        stmt = stmt.where(RelayCommand.alarm_record_id == alarm_record_id)
    if execution_status:
        stmt = stmt.where(RelayCommand.execution_status == execution_status)
    return list((await db.execute(stmt)).scalars().all())


async def get_relay_command_by_id(
    db: AsyncSession,
    command_id: int,
) -> RelayCommand | None:
    stmt = (
        select(RelayCommand)
        .options(selectinload(RelayCommand.module))
        .where(RelayCommand.id == command_id)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def create_manual_relay_command(
    db: AsyncSession,
    payload: RelayCommandCreate,
) -> RelayCommand:
    module = (await db.execute(select(Module).where(Module.id == payload.module_id))).scalar_one_or_none()
    if not module:
        raise ValueError("Module not found")

    is_online = module.is_online
    now = datetime.now(timezone.utc)

    # 人工控制也复用同一张指令表，便于后续统一查询和补发。
    command = RelayCommand(
        module_id=payload.module_id,
        command_source=payload.command_source,
        target_state=payload.target_state,
        execution_status="dispatched" if is_online else "queued",
        execution_result=(
            "manual relay command dispatched immediately"
            if is_online
            else "manual relay command queued for offline module"
        ),
        retry_count=1 if is_online else 0,
        last_attempt_at=now if is_online else None,
    )
    db.add(command)
    await db.commit()
    await db.refresh(command)
    return command


async def apply_relay_command_feedback(
    db: AsyncSession,
    command: RelayCommand,
    payload: RelayCommandFeedback,
) -> RelayCommand:
    command.execution_status = payload.execution_status
    command.feedback_status = payload.feedback_status
    command.feedback_message = payload.feedback_message
    command.executed_at = datetime.now(timezone.utc)
    command.execution_result = payload.feedback_message or command.execution_result
    await db.commit()
    await db.refresh(command)
    return command
