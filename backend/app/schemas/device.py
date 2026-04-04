from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ModuleCreate(BaseModel):
    module_code: str = Field(min_length=1, max_length=32)


class ModuleRead(BaseModel):
    id: int
    module_code: str
    relay_state: bool
    is_online: bool
    battery_level: int | None
    voltage_value: float | None
    last_seen_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ModuleDetail(ModuleRead):
    device_id: int


class ModuleStatusHistoryRead(BaseModel):
    id: int
    module_id: int
    device_id: int
    source: str
    is_online: bool
    relay_state: bool | None
    battery_level: int | None
    voltage_value: float | None
    trigger_alarm_type: str | None
    alarm_message: str | None
    reported_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ModuleStatusHistoryPage(BaseModel):
    total: int
    items: list[ModuleStatusHistoryRead]
    limit: int
    offset: int


class ModuleStatusReport(BaseModel):
    is_online: bool
    source: str = Field(default="http_report", max_length=32)
    relay_state: bool | None = None
    battery_level: int | None = Field(default=None, ge=0, le=100)
    voltage_value: float | None = None
    trigger_alarm_type: str | None = Field(default=None, max_length=32)
    alarm_message: str | None = None


class DeviceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    serial_number: str = Field(min_length=1, max_length=128)


class DeviceBind(BaseModel):
    serial_number: str = Field(min_length=1, max_length=128)
    name: str | None = Field(default=None, max_length=128)


class DeviceAssignOwner(BaseModel):
    owner_id: int | None = Field(default=None, ge=1)


class DeviceAssignProtocolProfile(BaseModel):
    protocol_profile_id: int | None = Field(default=None, ge=1)


class DeviceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    status: str | None = Field(default=None, min_length=1, max_length=32)


class DeviceRead(BaseModel):
    id: int
    name: str
    serial_number: str
    status: str
    owner_id: int | None
    linkage_group_id: int | None = None
    protocol_profile_id: int | None = None
    created_at: datetime
    updated_at: datetime
    modules: list[ModuleRead] = []

    model_config = ConfigDict(from_attributes=True)


class DeviceOverview(BaseModel):
    total_devices: int
    total_modules: int
    online_modules: int
    offline_modules: int
    triggered_alarm_count: int


class DeviceStatistics(BaseModel):
    total_devices: int
    owned_devices: int
    total_modules: int
    online_modules: int
    offline_modules: int
    online_rate: float
    triggered_alarm_count: int
    low_battery_alarm_count: int
    low_voltage_alarm_count: int


class DeviceMonitoringItem(BaseModel):
    device_id: int
    device_name: str
    serial_number: str
    owner_id: int | None
    module_count: int
    online_module_count: int
    offline_module_count: int
    latest_alarm_type: str | None
    latest_alarm_time: datetime | None
    device_status: str


class DeviceDeleteResult(BaseModel):
    device_id: int
    deleted: bool = True


class ModuleDeleteResult(BaseModel):
    module_id: int
    deleted: bool = True


class DeviceGroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)
    owner_id: int | None = Field(default=None, ge=1)


class DeviceGroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)
    owner_id: int | None = Field(default=None, ge=1)


class DeviceGroupAssign(BaseModel):
    linkage_group_id: int | None = Field(default=None, ge=1)


class DeviceGroupRead(BaseModel):
    id: int
    name: str
    description: str | None
    owner_id: int | None
    created_at: datetime
    updated_at: datetime
    device_count: int = 0
    device_ids: list[int] = []

    model_config = ConfigDict(from_attributes=True)


class DeviceGroupDeleteResult(BaseModel):
    group_id: int
    deleted: bool = True
