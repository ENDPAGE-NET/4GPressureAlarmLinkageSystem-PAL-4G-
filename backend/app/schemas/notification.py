from datetime import datetime

from pydantic import BaseModel, Field


class NotificationSubscriptionStatus(BaseModel):
    subscription_type: str = "alarm"
    enabled: bool
    template_ids: list[str]
    available_template_ids: list[str] = []
    source: str | None = None
    subscribed_at: datetime | None = None
    unsubscribed_at: datetime | None = None
    updated_at: datetime | None = None


class NotificationSubscribeRequest(BaseModel):
    template_ids: list[str] = Field(min_length=1)
    source: str | None = Field(default="wechat-miniprogram", max_length=64)
