from datetime import datetime

from pydantic import BaseModel

from app.schemas.device import DeviceMonitoringItem, DeviceOverview, DeviceStatistics


class DashboardAlarmItem(BaseModel):
    id: int
    module_id: int
    device_id: int
    device_name: str
    module_code: str
    alarm_type: str
    alarm_status: str
    source: str
    linkage_status: str
    message: str | None
    triggered_at: datetime


class DashboardRelayCommandItem(BaseModel):
    id: int
    module_id: int
    device_id: int
    device_name: str
    module_code: str
    command_source: str
    target_state: str
    execution_status: str
    feedback_status: str | None
    feedback_message: str | None
    created_at: datetime
    executed_at: datetime | None


class DashboardHome(BaseModel):
    overview: DeviceOverview
    statistics: DeviceStatistics
    monitoring: list[DeviceMonitoringItem]
    recent_alarm_count: int
    pending_command_count: int


class MiniProgramDeviceItem(BaseModel):
    device_id: int
    device_name: str
    serial_number: str
    module_count: int
    online_module_count: int
    latest_alarm_type: str | None
    latest_alarm_time: datetime | None
    device_status: str


class MiniProgramAlarmItem(BaseModel):
    id: int
    device_id: int
    device_name: str
    module_code: str
    alarm_type: str
    alarm_status: str
    triggered_at: datetime
    message: str | None


class DashboardTrendPoint(BaseModel):
    label: str
    value: int


class DashboardCharts(BaseModel):
    alarm_type_distribution: list[DashboardTrendPoint]
    command_status_distribution: list[DashboardTrendPoint]
    device_status_distribution: list[DashboardTrendPoint]
