from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import (
    DashboardAlarmItem,
    DashboardCharts,
    DashboardHome,
    DashboardRelayCommandItem,
    MiniProgramAlarmItem,
    MiniProgramDeviceItem,
)
from app.services.dashboard_service import (
    get_dashboard_charts,
    get_dashboard_home,
    list_dashboard_recent_alarms,
    list_dashboard_recent_commands,
    list_my_devices,
    list_my_recent_alarms,
)

router = APIRouter()


@router.get("/home", response_model=DashboardHome)
async def read_dashboard_home(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardHome:
    return await get_dashboard_home(db, current_user)


@router.get("/recent-alarms", response_model=list[DashboardAlarmItem])
async def read_dashboard_recent_alarms(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DashboardAlarmItem]:
    # Dashboard 接口直接返回页面所需结构，前端不必再额外做设备和模块拼装。
    return await list_dashboard_recent_alarms(db, current_user, limit=limit)


@router.get("/recent-commands", response_model=list[DashboardRelayCommandItem])
async def read_dashboard_recent_commands(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DashboardRelayCommandItem]:
    return await list_dashboard_recent_commands(db, current_user, limit=limit)


@router.get("/my/devices", response_model=list[MiniProgramDeviceItem])
async def read_my_devices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MiniProgramDeviceItem]:
    # 小程序侧更关心“我的设备”视图，这里直接返回压平后的设备摘要。
    return await list_my_devices(db, current_user)


@router.get("/my/alarms", response_model=list[MiniProgramAlarmItem])
async def read_my_recent_alarms(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MiniProgramAlarmItem]:
    return await list_my_recent_alarms(db, current_user, limit=limit)


@router.get("/charts", response_model=DashboardCharts)
async def read_dashboard_charts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardCharts:
    return await get_dashboard_charts(db, current_user)
