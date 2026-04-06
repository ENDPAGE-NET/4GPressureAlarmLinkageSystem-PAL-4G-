from pydantic import BaseModel, Field


class MqttStatusMessage(BaseModel):
    serial_number: str = Field(min_length=1, max_length=128)
    module_code: str | None = Field(default=None, min_length=1, max_length=32)
    is_online: bool
    relay_state: bool | None = None
    battery_level: int | None = Field(default=None, ge=0, le=100)
    voltage_value: float | None = None
    trigger_alarm_type: str | None = Field(default=None, max_length=32)
    alarm_message: str | None = None


class MqttAlarmMessage(BaseModel):
    serial_number: str = Field(min_length=1, max_length=128)
    module_code: str | None = Field(default=None, min_length=1, max_length=32)
    alarm_type: str = Field(min_length=1, max_length=32)
    message: str | None = None
    battery_level: int | None = Field(default=None, ge=0, le=100)
    voltage_value: float | None = None
    relay_state: bool | None = None
    is_online: bool | None = None
    imei: str | None = Field(default=None, min_length=1, max_length=64)
    triggered_at: str | None = None


class MqttRelayFeedbackMessage(BaseModel):
    command_id: int = Field(ge=1)
    execution_status: str = Field(pattern="^(dispatched|success|failed|queued)$")
    feedback_status: str = Field(default="device_ack", max_length=32)
    feedback_message: str | None = None
    error_code: str | None = Field(default=None, max_length=64)
    serial_number: str | None = Field(default=None, min_length=1, max_length=128)
    module_code: str | None = Field(default=None, min_length=1, max_length=32)
