from fastapi import APIRouter

from app.api.routes.alarms import router as alarms_router
from app.api.routes.auth import router as auth_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.devices import router as devices_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.logs import router as logs_router
from app.api.routes.mqtt import router as mqtt_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.protocols import router as protocols_router
from app.api.routes.realtime import router as realtime_router
from app.api.routes.relay_commands import router as relay_commands_router
from app.api.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(alarms_router, prefix="/alarms", tags=["alarms"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(devices_router, prefix="/devices", tags=["devices"])
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(logs_router, prefix="/logs", tags=["logs"])
api_router.include_router(mqtt_router, prefix="/mqtt", tags=["mqtt"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
api_router.include_router(protocols_router, prefix="/protocols", tags=["protocols"])
api_router.include_router(realtime_router, prefix="/ws", tags=["realtime"])
api_router.include_router(relay_commands_router, prefix="/relay-commands", tags=["relay-commands"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
