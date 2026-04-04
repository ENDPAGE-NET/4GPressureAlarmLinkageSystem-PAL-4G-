from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProtocolProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    protocol_type: str = Field(default="usr_mqtt_standard", pattern="^(usr_mqtt_standard|custom_mqtt)$")
    description: str | None = Field(default=None, max_length=500)
    broker_host: str = Field(min_length=1, max_length=255)
    broker_port: int = Field(default=1883, ge=1, le=65535)
    client_id_template: str = Field(default="pal_{serial_number}", min_length=1, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, max_length=255)
    status_topic_template: str = Field(min_length=1, max_length=255)
    feedback_topic_template: str = Field(min_length=1, max_length=255)
    command_topic_template: str = Field(min_length=1, max_length=255)
    tls_enabled: bool = False
    is_active: bool = True


class ProtocolProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    protocol_type: str | None = Field(default=None, pattern="^(usr_mqtt_standard|custom_mqtt)$")
    description: str | None = Field(default=None, max_length=500)
    broker_host: str | None = Field(default=None, min_length=1, max_length=255)
    broker_port: int | None = Field(default=None, ge=1, le=65535)
    client_id_template: str | None = Field(default=None, min_length=1, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, max_length=255)
    status_topic_template: str | None = Field(default=None, min_length=1, max_length=255)
    feedback_topic_template: str | None = Field(default=None, min_length=1, max_length=255)
    command_topic_template: str | None = Field(default=None, min_length=1, max_length=255)
    tls_enabled: bool | None = None
    is_active: bool | None = None


class ProtocolProfileRead(BaseModel):
    id: int
    name: str
    protocol_type: str
    description: str | None
    broker_host: str
    broker_port: int
    client_id_template: str
    username: str | None
    has_password: bool
    status_topic_template: str
    feedback_topic_template: str
    command_topic_template: str
    tls_enabled: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeviceProtocolAssign(BaseModel):
    protocol_profile_id: int | None = Field(default=None, ge=1)
