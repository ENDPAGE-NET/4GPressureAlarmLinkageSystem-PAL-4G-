import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.job_execution_log import JobExecutionLog
from app.schemas.maintenance import CleanupResult


async def write_job_execution_log(
    db: AsyncSession,
    job_name: str,
    trigger_type: str,
    status: str,
    started_at: datetime,
    finished_at: datetime | None,
    message: str | None = None,
    context: dict | None = None,
) -> JobExecutionLog:
    log = JobExecutionLog(
        job_name=job_name,
        trigger_type=trigger_type,
        status=status,
        message=message,
        context=json.dumps(context, ensure_ascii=False) if context else None,
        started_at=started_at,
        finished_at=finished_at,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


def _cleanup_dated_directories(root_path: Path, retention_days: int) -> int:
    if not root_path.exists():
        return 0

    cutoff_date = datetime.now().date() - timedelta(days=retention_days)
    removed_count = 0

    for child in root_path.iterdir():
        if not child.is_dir():
            continue
        try:
            child_date = datetime.strptime(child.name, "%Y-%m-%d").date()
        except ValueError:
            continue
        if child_date < cutoff_date:
            shutil.rmtree(child, ignore_errors=True)
            removed_count += 1

    return removed_count


async def cleanup_runtime_files() -> CleanupResult:
    removed_log_directories = _cleanup_dated_directories(
        settings.log_root_path,
        settings.LOG_RETENTION_DAYS,
    )
    removed_error_log_directories = _cleanup_dated_directories(
        settings.log_root_path / "errors",
        settings.LOG_RETENTION_DAYS,
    )
    removed_backup_directories = _cleanup_dated_directories(
        settings.backup_root_path,
        settings.BACKUP_RETENTION_DAYS,
    )
    return CleanupResult(
        removed_log_directories=removed_log_directories + removed_error_log_directories,
        removed_backup_directories=removed_backup_directories,
    )
