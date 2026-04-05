from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    wechat_bound: bool = False
    wechat_bound_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class WechatIdentityPayload(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=128)
    wechat_open_id: str | None = Field(default=None, min_length=1, max_length=128)
    wechat_union_id: str | None = Field(default=None, min_length=1, max_length=128)

    @model_validator(mode="after")
    def validate_identity(self):
        if not self.code and not self.wechat_open_id:
            raise ValueError("Either code or wechat_open_id is required")
        return self


class WechatBindResult(BaseModel):
    user_id: int
    username: str
    wechat_open_id: str
    wechat_union_id: str | None = None
    wechat_bound_at: datetime
