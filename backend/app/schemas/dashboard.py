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


class DashboardModulePanelItem(BaseModel):
    module_id: int
    device_id: int
    device_name: str
    serial_number: str
    module_code: str
    is_online: bool
    battery_level: int | None
    voltage_value: float | None
    relay_state: bool
    last_seen_at: datetime | None
    latest_alarm_type: str | None
    latest_alarm_time: datetime | None


class DashboardHome(BaseModel):
    overview: DeviceOverview
    statistics: DeviceStatistics
    monitoring: list[DeviceMonitoringItem]
    module_panels: list[DashboardModulePanelItem] = []
    recent_alarm_count: int
    pending_command_count: int


class MiniProgramHome(BaseModel):
    device_count: int
    online_device_count: int
    triggered_alarm_count: int
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


class PaginationMeta(BaseModel):
    total: int
    limit: int
    offset: int


class DashboardAlarmPage(BaseModel):
    items: list[DashboardAlarmItem]
    pagination: PaginationMeta


class DashboardRelayCommandPage(BaseModel):
    items: list[DashboardRelayCommandItem]
    pagination: PaginationMeta


class MiniProgramAlarmPage(BaseModel):
    items: list[MiniProgramAlarmItem]
    pagination: PaginationMeta


class DashboardDeviceDetail(BaseModel):
    device_id: int
    device_name: str
    serial_number: str
    status: str
    owner_id: int | None
    linkage_group_id: int | None
    module_count: int
    online_module_count: int
    offline_module_count: int
    latest_alarm_type: str | None
    latest_alarm_time: datetime | None
    device_status: str
    recent_alarms: list[DashboardAlarmItem]
    recent_commands: list[DashboardRelayCommandItem]
