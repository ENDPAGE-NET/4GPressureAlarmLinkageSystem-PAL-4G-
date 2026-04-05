from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AlarmRecordCreate(BaseModel):
    module_id: int
    alarm_type: str = Field(min_length=1, max_length=32)
    source: str = Field(default="manual", max_length=32)
    linkage_status: str = Field(default="pending", max_length=32)
    linkage_result: str | None = None
    message: str | None = None


class AlarmRecordRecover(BaseModel):
    recovered_at: datetime | None = None


class AlarmLinkageDispatchResult(BaseModel):
    alarm_id: int
    generated_command_count: int
    dispatched_count: int
    queued_count: int
    skipped_count: int
    linkage_status: str
    linkage_result: str


class AlarmRecordRead(BaseModel):
    id: int
    module_id: int
    alarm_type: str
    alarm_status: str
    source: str
    linkage_status: str
    linkage_result: str | None
    notification_status: str
    notification_result: str | None
    notification_attempts: int
    message: str | None
    triggered_at: datetime
    recovered_at: datetime | None
    notification_sent_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AlarmRecordPage(BaseModel):
    total: int
    items: list[AlarmRecordRead]
    limit: int
    offset: int
