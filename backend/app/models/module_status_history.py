from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ModuleStatusHistory(Base):
    __tablename__ = "module_status_histories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id"), index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    source: Mapped[str] = mapped_column(String(32), index=True, default="http_report")
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    relay_state: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    battery_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    voltage_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    trigger_alarm_type: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    alarm_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    module = relationship("Module")
    device = relationship("Device")
