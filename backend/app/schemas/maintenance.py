from datetime import datetime

from pydantic import BaseModel


class JobExecutionLogRead(BaseModel):
    id: int
    job_name: str
    trigger_type: str
    status: str
    message: str | None
    context: str | None
    started_at: datetime
    finished_at: datetime | None
    created_at: datetime


class CleanupResult(BaseModel):
    removed_log_directories: int
    removed_backup_directories: int
