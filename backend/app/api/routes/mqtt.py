import json

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.device import ModuleDetail
from app.schemas.mqtt import MqttStatusMessage
from app.schemas.mqtt_client import MqttClientStatus, MqttRawMessage
from app.services.mqtt_adapter import process_mqtt_status_message
from app.services.mqtt_client_service import mqtt_client_service

router = APIRouter()


@router.get("/status", response_model=MqttClientStatus)
async def read_mqtt_status(
    _: User = Depends(get_current_admin),
) -> MqttClientStatus:
    return mqtt_client_service.status()


@router.post("/simulate", response_model=ModuleDetail)
async def simulate_mqtt_status_message(
    payload: MqttStatusMessage,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ModuleDetail:
    module = await process_mqtt_status_message(db, payload.model_dump())
    return ModuleDetail.model_validate(module)


@router.post("/simulate-raw", response_model=MqttClientStatus)
async def simulate_mqtt_raw_message(
    payload: MqttRawMessage,
    _: User = Depends(get_current_admin),
) -> MqttClientStatus:
    # 原始 topic 模拟入口用于本地联调协议解析与消息接入链路，不依赖真实 broker。
    await mqtt_client_service.process_raw_message(
        payload.topic,
        json.dumps(payload.payload, ensure_ascii=False),
    )
    return mqtt_client_service.status()
