from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProtocolProfile(Base):
    __tablename__ = "protocol_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    protocol_type: Mapped[str] = mapped_column(String(32), default="usr_mqtt_standard")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    broker_host: Mapped[str] = mapped_column(String(255))
    broker_port: Mapped[int] = mapped_column(Integer, default=1883)
    client_id_template: Mapped[str] = mapped_column(String(255), default="pal_{serial_number}")
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_topic_template: Mapped[str] = mapped_column(String(255))
    feedback_topic_template: Mapped[str] = mapped_column(String(255))
    command_topic_template: Mapped[str] = mapped_column(String(255))
    tls_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    devices = relationship("Device", back_populates="protocol_profile")
