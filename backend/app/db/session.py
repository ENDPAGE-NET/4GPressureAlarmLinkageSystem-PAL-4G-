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
