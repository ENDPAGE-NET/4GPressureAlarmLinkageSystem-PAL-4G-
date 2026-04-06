from pydantic import BaseModel, Field


class ProtocolTopicInfo(BaseModel):
    category: str
    serial_number: str | None = None
    module_code: str | None = None
    raw_topic: str
    matched_prefix: str | None = None


class ProtocolFeedbackResult(BaseModel):
    execution_status: str = Field(pattern="^(dispatched|success|failed|queued)$")
    feedback_status: str
    feedback_message: str | None = None
    error_code: str | None = None


class RelayCommandPayload(BaseModel):
    serial_number: str
    module_code: str | None = None
    command_type: str = "relay_control"
    target_state: str = Field(pattern="^(open|closed)$")
    command_id: int
    protocol_version: str = "v1"
    sent_at: str
