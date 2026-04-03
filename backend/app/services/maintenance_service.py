import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.job_execution_log import JobExecutionLog
from app.schemas.maintenance import CleanupResult, DatabaseBackupResult


def _resolve_sqlite_db_path() -> Path:
    database_url = settings.DATABASE_URL
    prefix = "sqlite+aiosqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("Database backup currently only supports sqlite+aiosqlite")

    raw_path = database_url.removeprefix(prefix)
    return Path(raw_path).resolve()


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


async def list_job_execution_logs(
    db: AsyncSession,
    job_name: str | None = None,
    trigger_type: str | None = None,
    status: str | None = None,
    limit: int = 20,
) -> list[JobExecutionLog]:
    stmt = select(JobExecutionLog).order_by(
        JobExecutionLog.created_at.desc(), JobExecutionLog.id.desc()
    )
    if job_name:
        stmt = stmt.where(JobExecutionLog.job_name == job_name)
    if trigger_type:
        stmt = stmt.where(JobExecutionLog.trigger_type == trigger_type)
    if status:
        stmt = stmt.where(JobExecutionLog.status == status)
    stmt = stmt.limit(limit)
    return list((await db.execute(stmt)).scalars().all())


async def backup_database() -> DatabaseBackupResult:
    source_path = _resolve_sqlite_db_path()
    if not source_path.exists():
        raise ValueError("Database file does not exist")

    today = datetime.now().strftime("%Y-%m-%d")
    backup_dir = settings.backup_root_path / today
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{source_path.stem}-{datetime.now().strftime('%H%M%S')}.db"

    # 当前先按文件复制实现 sqlite 备份，满足本地恢复与归档场景。
    shutil.copy2(source_path, backup_path)
    return DatabaseBackupResult(
        backup_file=str(backup_path),
        file_size=backup_path.stat().st_size,
    )


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
