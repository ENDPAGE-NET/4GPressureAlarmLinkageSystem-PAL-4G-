from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import init_db
from app.services.mqtt_client_service import mqtt_client_service
from app.services.scheduler_service import shutdown_scheduler, start_scheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    # 服务启动时统一完成建表和默认管理员初始化，避免首次运行缺少基础数据。
    await init_db()
    start_scheduler()
    mqtt_client_service.start()
    yield
    mqtt_client_service.stop()
    shutdown_scheduler()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    return {"message": f"{settings.APP_NAME} backend is running"}
