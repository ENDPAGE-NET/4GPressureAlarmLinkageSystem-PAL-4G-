import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.services import scheduler_service
from app.services.user_service import ensure_default_admin


@pytest.fixture
def client():
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

    async def prepare_database() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with session_factory() as session:
            await ensure_default_admin(session)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    asyncio.run(prepare_database())
    scheduler_service.AsyncSessionLocal = session_factory

    app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        asyncio.run(engine.dispose())
