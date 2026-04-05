from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    module_code: Mapped[str] = mapped_column(String(32), index=True)
    # 每个联网模块保留自己的唯一 SN/IMEI，设备表只保留整套设备的聚合标识。
    serial_number: Mapped[str | None] = mapped_column(
        String(128), unique=True, index=True, nullable=True
    )
    imei: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    relay_state: Mapped[bool] = mapped_column(Boolean, default=False)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    battery_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    voltage_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    device = relationship("Device", back_populates="modules")
    alarm_records = relationship("AlarmRecord", back_populates="module")
    relay_commands = relationship("RelayCommand", back_populates="module")
