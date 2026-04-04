from datetime import datetime, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.alarm_record import AlarmRecord
from app.models.device import Device
from app.models.module import Module
from app.models.user import User
from app.services.dashboard_service import get_dashboard_home


@pytest.mark.asyncio
async def test_get_dashboard_home_returns_owned_module_panels_for_manager():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        async with session_factory() as session:
            manager = User(username="manager", password_hash="x", role="manager", is_active=True)
            other_user = User(username="other", password_hash="x", role="manager", is_active=True)
            session.add_all([manager, other_user])
            await session.flush()

            owned_device = Device(
                name="North Pump",
                serial_number="SN-001",
                owner_id=manager.id,
                status="active",
            )
            foreign_device = Device(
                name="South Pump",
                serial_number="SN-002",
                owner_id=other_user.id,
                status="active",
            )
            session.add_all([owned_device, foreign_device])
            await session.flush()

            owned_module_online = Module(
                device_id=owned_device.id,
                module_code="A-01",
                is_online=True,
                battery_level=82,
                voltage_value=3.72,
                relay_state=True,
                last_seen_at=datetime(2026, 4, 4, 8, 0, tzinfo=timezone.utc),
            )
            owned_module_offline = Module(
                device_id=owned_device.id,
                module_code="A-02",
                is_online=False,
                battery_level=16,
                voltage_value=3.08,
                relay_state=False,
                last_seen_at=datetime(2026, 4, 4, 7, 30, tzinfo=timezone.utc),
            )
            foreign_module = Module(
                device_id=foreign_device.id,
                module_code="B-01",
                is_online=True,
                battery_level=90,
                voltage_value=3.95,
                relay_state=False,
            )
            session.add_all([owned_module_online, owned_module_offline, foreign_module])
            await session.flush()

            session.add_all(
                [
                    AlarmRecord(
                        module_id=owned_module_online.id,
                        alarm_type="low_battery",
                        alarm_status="triggered",
                        source="mqtt",
                        linkage_status="pending",
                        triggered_at=datetime(2026, 4, 4, 7, 0, tzinfo=timezone.utc),
                    ),
                    AlarmRecord(
                        module_id=owned_module_online.id,
                        alarm_type="high_voltage",
                        alarm_status="triggered",
                        source="mqtt",
                        linkage_status="pending",
                        triggered_at=datetime(2026, 4, 4, 8, 5, tzinfo=timezone.utc),
                    ),
                    AlarmRecord(
                        module_id=foreign_module.id,
                        alarm_type="low_voltage",
                        alarm_status="triggered",
                        source="mqtt",
                        linkage_status="pending",
                        triggered_at=datetime(2026, 4, 4, 9, 0, tzinfo=timezone.utc),
                    ),
                ]
            )
            await session.commit()

            home = await get_dashboard_home(session, manager)

            assert home.overview.total_devices == 1
            assert home.overview.total_modules == 2
            assert len(home.module_panels) == 2

            panels_by_code = {item.module_code: item for item in home.module_panels}
            assert set(panels_by_code) == {"A-01", "A-02"}

            online_panel = panels_by_code["A-01"]
            assert online_panel.device_name == "North Pump"
            assert online_panel.serial_number == "SN-001"
            assert online_panel.is_online is True
            assert online_panel.battery_level == 82
            assert online_panel.voltage_value == 3.72
            assert online_panel.relay_state is True
            assert online_panel.latest_alarm_type == "high_voltage"
            assert online_panel.latest_alarm_time == datetime(
                2026, 4, 4, 8, 5, tzinfo=timezone.utc
            )

            offline_panel = panels_by_code["A-02"]
            assert offline_panel.is_online is False
            assert offline_panel.battery_level == 16
            assert offline_panel.voltage_value == 3.08
            assert offline_panel.relay_state is False
            assert offline_panel.latest_alarm_type is None
            assert offline_panel.latest_alarm_time is None
    finally:
        await engine.dispose()
