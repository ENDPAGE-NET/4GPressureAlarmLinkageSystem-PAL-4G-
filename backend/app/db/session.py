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


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    # 先确保所有 ORM 模型对应的数据表存在。
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 再补齐默认管理员，保证系统首次启动后可直接登录。
    async with AsyncSessionLocal() as session:
        await ensure_default_admin(session)
