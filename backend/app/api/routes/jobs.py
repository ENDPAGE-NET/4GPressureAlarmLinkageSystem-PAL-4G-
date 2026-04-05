from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.jobs import AlarmRecoveryCheckResult, OfflineCheckResult, SchedulerJobRead, SchedulerStatus
from app.schemas.jobs import AlarmNotificationDispatchResult
from app.schemas.maintenance import (
    CleanupResult,
    DatabaseBackupFileRead,
    DatabaseBackupResult,
    JobExecutionLogRead,
)
from app.schemas.relay import RelayRetryResult
from app.services.maintenance_service import (
    backup_database,
    list_database_backups,
    list_job_execution_logs,
)
from app.services.scheduler_service import (
    mark_offline_modules,
    run_alarm_recovery_check_job,
    run_alarm_notification_dispatch_job,
    run_cleanup_runtime_files_job,
    run_retry_pending_commands_job,
    scheduler,
)

router = APIRouter()


@router.get("/scheduler", response_model=SchedulerStatus)
async def read_scheduler_status(
    _: User = Depends(get_current_admin),
) -> SchedulerStatus:
    return SchedulerStatus(
        running=scheduler.running,
        jobs=[
            SchedulerJobRead(
                id=job.id,
                next_run_time=job.next_run_time,
                trigger=str(job.trigger),
            )
            for job in scheduler.get_jobs()
        ],
    )


@router.get("/history", response_model=list[JobExecutionLogRead])
async def read_job_history(
    job_name: str | None = Query(default=None),
    trigger_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[JobExecutionLogRead]:
    logs = await list_job_execution_logs(
        db,
        job_name=job_name,
        trigger_type=trigger_type,
        status=status,
        limit=limit,
    )
    return [
        JobExecutionLogRead(
            id=log.id,
            job_name=log.job_name,
            trigger_type=log.trigger_type,
            status=log.status,
            message=log.message,
            context=log.context,
            started_at=log.started_at,
            finished_at=log.finished_at,
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.post("/offline-check", response_model=OfflineCheckResult)
async def run_offline_check(
    _: User = Depends(get_current_admin),
) -> OfflineCheckResult:
    updated_count = await mark_offline_modules(trigger_type="manual")
    return OfflineCheckResult(updated_count=updated_count)


@router.post("/retry-pending", response_model=RelayRetryResult)
async def run_retry_pending(
    _: User = Depends(get_current_admin),
) -> RelayRetryResult:
    result = await run_retry_pending_commands_job(trigger_type="manual")
    return RelayRetryResult(**result)


@router.post("/alarm-recovery-check", response_model=AlarmRecoveryCheckResult)
async def run_alarm_recovery_check(
    _: User = Depends(get_current_admin),
) -> AlarmRecoveryCheckResult:
    result = await run_alarm_recovery_check_job(trigger_type="manual")
    return AlarmRecoveryCheckResult(**result)


@router.post("/alarm-notification-dispatch", response_model=AlarmNotificationDispatchResult)
async def run_alarm_notification_dispatch(
    _: User = Depends(get_current_admin),
) -> AlarmNotificationDispatchResult:
    result = await run_alarm_notification_dispatch_job(trigger_type="manual")
    return AlarmNotificationDispatchResult(**result)


@router.post("/cleanup-files", response_model=CleanupResult)
async def run_cleanup_files(
    _: User = Depends(get_current_admin),
) -> CleanupResult:
    result = await run_cleanup_runtime_files_job(trigger_type="manual")
    return CleanupResult(**result)


@router.post("/backup-database", response_model=DatabaseBackupResult)
async def run_backup_database(
    _: User = Depends(get_current_admin),
) -> DatabaseBackupResult:
    # 数据库备份属于显式运维动作，只允许管理员手动触发。
    return await backup_database()


@router.get("/backups", response_model=list[DatabaseBackupFileRead])
async def read_database_backups(
    limit: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_admin),
) -> list[DatabaseBackupFileRead]:
    return await list_database_backups(limit=limit)
