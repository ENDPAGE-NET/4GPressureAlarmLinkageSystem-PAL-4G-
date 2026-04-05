import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.alarm_record import AlarmRecord
from app.models.module import Module
from app.schemas.alarm import AlarmRecordRecover
from app.services.alarm_service import recover_alarm_record
from app.services.linkage_service import retry_queued_relay_commands
from app.services.linkage_service import dispatch_recovery_for_alarm
from app.services.logging_service import write_runtime_log
from app.services.maintenance_service import cleanup_runtime_files, write_job_execution_log
from app.services.notification_service import dispatch_pending_alarm_notifications

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="UTC")


async def mark_offline_modules(trigger_type: str = "scheduler") -> int:
    started_at = datetime.now(timezone.utc)
    timeout_at = datetime.now(timezone.utc) - timedelta(
        seconds=settings.HEARTBEAT_TIMEOUT_SECONDS
    )
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(Module).where(
                Module.is_online.is_(True),
                Module.last_seen_at.is_not(None),
                Module.last_seen_at < timeout_at,
            )
            modules = list((await session.execute(stmt)).scalars().all())
            for module in modules:
                module.is_online = False
            await session.commit()

            if modules:
                await write_runtime_log(
                    session,
                    level="INFO",
                    event="offline_check",
                    message=f"updated {len(modules)} modules to offline",
                    context={"module_count": len(modules)},
                )

            await write_job_execution_log(
                session,
                job_name="offline_check",
                trigger_type=trigger_type,
                status="success",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                message=f"updated {len(modules)} modules to offline",
                context={"module_count": len(modules)},
            )
            return len(modules)
        except Exception as exc:
            await write_job_execution_log(
                session,
                job_name="offline_check",
                trigger_type=trigger_type,
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                message=str(exc),
            )
            raise


async def run_retry_pending_commands_job(
    trigger_type: str = "scheduler",
) -> dict[str, int]:
    started_at = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        try:
            result = await retry_queued_relay_commands(session)
            await write_runtime_log(
                session,
                level="INFO",
                event="retry_pending_commands",
                message=(
                    f"scanned {result.total_scanned}, dispatched {result.dispatched_count}, "
                    f"still queued {result.still_queued_count}"
                ),
                context=result.model_dump(),
            )
            await write_job_execution_log(
                session,
                job_name="retry_pending_commands",
                trigger_type=trigger_type,
                status="success",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                message="retry pending commands completed",
                context=result.model_dump(),
            )
            return result.model_dump()
        except Exception as exc:
            await write_job_execution_log(
                session,
                job_name="retry_pending_commands",
                trigger_type=trigger_type,
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                message=str(exc),
            )
            raise


async def run_cleanup_runtime_files_job(
    trigger_type: str = "scheduler",
) -> dict[str, int]:
    started_at = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        try:
            result = await cleanup_runtime_files()
            await write_runtime_log(
                session,
                level="INFO",
                event="cleanup_runtime_files",
                message="cleanup runtime files completed",
                context=result.model_dump(),
            )
            await write_job_execution_log(
                session,
                job_name="cleanup_runtime_files",
                trigger_type=trigger_type,
                status="success",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                message="cleanup runtime files completed",
                context=result.model_dump(),
            )
            return result.model_dump()
        except Exception as exc:
            await write_job_execution_log(
                session,
                job_name="cleanup_runtime_files",
                trigger_type=trigger_type,
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                message=str(exc),
            )
            raise


def _should_auto_recover_alarm(alarm: AlarmRecord, module: Module | None) -> bool:
    if not module or not module.is_online:
        return False

    alarm_type = alarm.alarm_type.lower()

    # 低电量和电压类报警优先按阈值恢复，避免只看在线状态导致误恢复。
    if alarm_type == "low_battery":
        return (
            module.battery_level is not None
            and module.battery_level >= settings.ALARM_LOW_BATTERY_RECOVERY_THRESHOLD
        )
    if alarm_type == "low_voltage":
        return (
            module.voltage_value is not None
            and module.voltage_value >= settings.ALARM_LOW_VOLTAGE_RECOVERY_THRESHOLD
        )
    if alarm_type == "high_voltage":
        return (
            module.voltage_value is not None
            and module.voltage_value <= settings.ALARM_HIGH_VOLTAGE_RECOVERY_THRESHOLD
        )

    # 通用类报警暂时按模块已在线且继电器回到关闭态视为恢复。
    return module.relay_state is False


async def run_alarm_recovery_check_job(
    trigger_type: str = "scheduler",
) -> dict[str, int]:
    started_at = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        try:
            stmt = (
                select(AlarmRecord)
                .options(selectinload(AlarmRecord.module))
                .where(AlarmRecord.alarm_status == "triggered")
                .order_by(AlarmRecord.triggered_at.asc(), AlarmRecord.id.asc())
            )
            alarms = list((await session.execute(stmt)).scalars().all())

            recovered_count = 0
            skipped_count = 0

            for alarm in alarms:
                if not _should_auto_recover_alarm(alarm, alarm.module):
                    skipped_count += 1
                    continue

                # 定时任务只负责识别“已恢复”的报警，真正的恢复动作仍复用现有业务链路。
                await recover_alarm_record(session, alarm, AlarmRecordRecover())
                await dispatch_recovery_for_alarm(session, alarm)
                recovered_count += 1

            await write_runtime_log(
                session,
                level="INFO",
                event="alarm_recovery_check",
                message=(
                    f"recovered {recovered_count} alarms, skipped {skipped_count} alarms"
                ),
                context={
                    "recovered_count": recovered_count,
                    "skipped_count": skipped_count,
                },
            )
            await write_job_execution_log(
                session,
                job_name="alarm_recovery_check",
                trigger_type=trigger_type,
                status="success",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                message="alarm recovery check completed",
                context={
                    "recovered_count": recovered_count,
                    "skipped_count": skipped_count,
                },
            )
            return {
                "recovered_count": recovered_count,
                "skipped_count": skipped_count,
            }
        except Exception as exc:
            await write_job_execution_log(
                session,
                job_name="alarm_recovery_check",
                trigger_type=trigger_type,
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                message=str(exc),
            )
            raise


async def run_alarm_notification_dispatch_job(
    trigger_type: str = "scheduler",
) -> dict[str, int]:
    started_at = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        try:
            result = await dispatch_pending_alarm_notifications(session)
            await write_runtime_log(
                session,
                level="INFO",
                event="alarm_notification_dispatch",
                message=(
                    f"processed {result['processed_count']}, sent {result['sent_count']}, "
                    f"failed {result['failed_count']}, skipped {result['skipped_count']}"
                ),
                context=result,
            )
            await write_job_execution_log(
                session,
                job_name="alarm_notification_dispatch",
                trigger_type=trigger_type,
                status="success",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                message="alarm notification dispatch completed",
                context=result,
            )
            return result
        except Exception as exc:
            await write_job_execution_log(
                session,
                job_name="alarm_notification_dispatch",
                trigger_type=trigger_type,
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                message=str(exc),
            )
            raise


def start_scheduler() -> None:
    if scheduler.running:
        return

    scheduler.add_job(
        mark_offline_modules,
        "interval",
        seconds=settings.OFFLINE_CHECK_INTERVAL_SECONDS,
        id="mark-offline-modules",
        replace_existing=True,
    )
    scheduler.add_job(
        run_retry_pending_commands_job,
        "interval",
        seconds=settings.RETRY_PENDING_COMMANDS_INTERVAL_SECONDS,
        id="retry-pending-relay-commands",
        replace_existing=True,
    )
    scheduler.add_job(
        run_cleanup_runtime_files_job,
        "interval",
        hours=24,
        id="cleanup-runtime-files",
        replace_existing=True,
    )
    scheduler.add_job(
        run_alarm_recovery_check_job,
        "interval",
        seconds=settings.ALARM_RECOVERY_CHECK_INTERVAL_SECONDS,
        id="alarm-recovery-check",
        replace_existing=True,
    )
    scheduler.add_job(
        run_alarm_notification_dispatch_job,
        "interval",
        seconds=settings.ALARM_NOTIFICATION_DISPATCH_INTERVAL_SECONDS,
        id="alarm-notification-dispatch",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("APScheduler started")


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
