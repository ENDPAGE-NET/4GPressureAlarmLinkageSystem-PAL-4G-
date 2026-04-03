from pydantic import BaseModel


class MqttClientStatus(BaseModel):
    enabled: bool
    connected: bool
    broker_host: str
    broker_port: int
    status_topic: str
    subscribed_topics: list[str]
    received_message_count: int
    published_message_count: int
    last_inbound_topic: str | None = None
    last_inbound_at: str | None = None
    last_outbound_topic: str | None = None
    last_outbound_at: str | None = None


class MqttRawMessage(BaseModel):
    topic: str
    payload: dict


class MqttPublishResult(BaseModel):
    topic: str
    payload: dict
    published: bool
    reason: str
