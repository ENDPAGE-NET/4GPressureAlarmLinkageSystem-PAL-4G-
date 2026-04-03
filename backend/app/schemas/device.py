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


class ModuleStatusReport(BaseModel):
    is_online: bool
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


class DeviceRead(BaseModel):
    id: int
    name: str
    serial_number: str
    status: str
    owner_id: int | None
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
