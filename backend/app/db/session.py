from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base
from app.models import (  # noqa: F401
    AlarmRecord,
    CommunicationLog,
    Device,
    DeviceGroup,
    JobExecutionLog,
    Module,
    ModuleStatusHistory,
    NotificationSubscription,
    OperationLog,
    ProtocolProfile,
    RelayCommand,
    RuntimeLog,
    User,
)
from app.services.user_service import ensure_default_admin


engine = create_async_engine(settings.DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def ensure_sqlite_schema_compatibility() -> None:
    if not settings.DATABASE_URL.startswith("sqlite+aiosqlite:///"):
        return

    async with engine.begin() as conn:
        result = await conn.execute(text("PRAGMA table_info(devices)"))
        device_columns = {row[1] for row in result.fetchall()}
        result = await conn.execute(text("PRAGMA table_info(modules)"))
        module_columns = {row[1] for row in result.fetchall()}
        result = await conn.execute(text("PRAGMA table_info(users)"))
        user_columns = {row[1] for row in result.fetchall()}
        result = await conn.execute(text("PRAGMA table_info(alarm_records)"))
        alarm_columns = {row[1] for row in result.fetchall()}

        migration_statements: list[str] = []

        # 老库的 devices 表缺少后续迭代新增的字段，create_all 不会自动补列。
        if "linkage_group_id" not in device_columns:
            migration_statements.append(
                "ALTER TABLE devices ADD COLUMN linkage_group_id INTEGER"
            )
            migration_statements.append(
                "CREATE INDEX IF NOT EXISTS ix_devices_linkage_group_id "
                "ON devices (linkage_group_id)"
            )

        if "protocol_profile_id" not in device_columns:
            migration_statements.append(
                "ALTER TABLE devices ADD COLUMN protocol_profile_id INTEGER"
            )
            migration_statements.append(
                "CREATE INDEX IF NOT EXISTS ix_devices_protocol_profile_id "
                "ON devices (protocol_profile_id)"
            )

        if "serial_number" not in module_columns:
            migration_statements.append(
                "ALTER TABLE modules ADD COLUMN serial_number VARCHAR(128)"
            )
            migration_statements.append(
                "UPDATE modules "
                "SET serial_number = ("
                "SELECT devices.serial_number || '-' || modules.module_code "
                "FROM devices WHERE devices.id = modules.device_id"
                ") "
                "WHERE serial_number IS NULL"
            )
            migration_statements.append(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_modules_serial_number "
                "ON modules (serial_number)"
            )

        if "imei" not in module_columns:
            migration_statements.append(
                "ALTER TABLE modules ADD COLUMN imei VARCHAR(64)"
            )
            migration_statements.append(
                "CREATE INDEX IF NOT EXISTS ix_modules_imei ON modules (imei)"
            )

        if "wechat_open_id" not in user_columns:
            migration_statements.append(
                "ALTER TABLE users ADD COLUMN wechat_open_id VARCHAR(128)"
            )
            migration_statements.append(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_wechat_open_id "
                "ON users (wechat_open_id)"
            )

        if "wechat_union_id" not in user_columns:
            migration_statements.append(
                "ALTER TABLE users ADD COLUMN wechat_union_id VARCHAR(128)"
            )

        if "wechat_bound_at" not in user_columns:
            migration_statements.append(
                "ALTER TABLE users ADD COLUMN wechat_bound_at DATETIME"
            )

        if "notification_status" not in alarm_columns:
            migration_statements.append(
                "ALTER TABLE alarm_records ADD COLUMN notification_status VARCHAR(32) DEFAULT 'pending'"
            )
            migration_statements.append(
                "CREATE INDEX IF NOT EXISTS ix_alarm_records_notification_status "
                "ON alarm_records (notification_status)"
            )

        if "notification_result" not in alarm_columns:
            migration_statements.append(
                "ALTER TABLE alarm_records ADD COLUMN notification_result TEXT"
            )

        if "notification_attempts" not in alarm_columns:
            migration_statements.append(
                "ALTER TABLE alarm_records ADD COLUMN notification_attempts INTEGER DEFAULT 0"
            )

        if "notification_sent_at" not in alarm_columns:
            migration_statements.append(
                "ALTER TABLE alarm_records ADD COLUMN notification_sent_at DATETIME"
            )

        for statement in migration_statements:
            await conn.execute(text(statement))


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    # 先确保所有 ORM 模型对应的数据表存在。
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 再补齐历史 SQLite 数据库缺失的新增列，避免 merge 后老库直接 500。
    await ensure_sqlite_schema_compatibility()
    # 再补齐默认管理员，保证系统首次启动后可直接登录。
    async with AsyncSessionLocal() as session:
        await ensure_default_admin(session)
