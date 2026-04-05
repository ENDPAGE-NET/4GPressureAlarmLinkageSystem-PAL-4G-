from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    # 当前业务默认角色是管理人员，device_user 先保留给后续终端用户场景扩展。
    role: Mapped[str] = mapped_column(String(32), default="manager")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    wechat_open_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    wechat_union_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    wechat_bound_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    devices = relationship("Device", back_populates="owner")
