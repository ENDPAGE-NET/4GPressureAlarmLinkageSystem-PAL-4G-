from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    serial_number: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    linkage_group_id: Mapped[int | None] = mapped_column(
        ForeignKey("device_groups.id"), nullable=True, index=True
    )
    protocol_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("protocol_profiles.id"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(32), default="inactive")
    # MQTT 凭证：设备接入 EMQX 时使用，添加设备时自动生成或手动指定。
    mqtt_username: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mqtt_password: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mqtt_client_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # 设备级 MQTT Topic 前缀，透传模式下每台设备有固定的上行/下行 Topic。
    mqtt_pub_topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mqtt_sub_topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner = relationship("User", back_populates="devices")
    linkage_group = relationship("DeviceGroup", back_populates="devices")
    protocol_profile = relationship("ProtocolProfile", back_populates="devices")
    modules = relationship("Module", back_populates="device")
