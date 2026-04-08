from datetime import datetime

from pydantic import BaseModel


class SchedulerJobRead(BaseModel):
    id: str
    next_run_time: datetime | None
    trigger: str


class SchedulerStatus(BaseModel):
    running: bool
    jobs: list[SchedulerJobRead]
