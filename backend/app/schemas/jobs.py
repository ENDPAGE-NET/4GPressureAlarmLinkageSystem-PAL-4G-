from datetime import datetime

from pydantic import BaseModel


class OfflineCheckResult(BaseModel):
    updated_count: int


class AlarmRecoveryCheckResult(BaseModel):
    recovered_count: int
    skipped_count: int


class AlarmNotificationDispatchResult(BaseModel):
    processed_count: int
    sent_count: int
    failed_count: int
    skipped_count: int


class SchedulerJobRead(BaseModel):
    id: str
    next_run_time: datetime | None
    trigger: str


class SchedulerStatus(BaseModel):
    running: bool
    jobs: list[SchedulerJobRead]
