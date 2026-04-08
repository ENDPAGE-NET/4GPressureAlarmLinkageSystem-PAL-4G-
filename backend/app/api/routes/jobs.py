from fastapi import APIRouter, Depends

from app.api.deps import get_current_admin
from app.models.user import User
from app.schemas.jobs import SchedulerJobRead, SchedulerStatus
from app.services.scheduler_service import scheduler

router = APIRouter()


@router.get("/scheduler", response_model=SchedulerStatus)
async def read_scheduler_status(
    _: User = Depends(get_current_admin),
) -> SchedulerStatus:
    """后台调度器健康检查，仅返回运行状态和已注册任务列表。"""
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
