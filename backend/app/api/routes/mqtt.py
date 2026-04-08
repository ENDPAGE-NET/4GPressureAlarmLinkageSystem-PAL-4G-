import json
import logging

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.device import Device
from app.models.user import User
from app.schemas.device import ModuleDetail
from app.schemas.mqtt import MqttStatusMessage
from app.schemas.mqtt_client import (
    EmqxAclRequest,
    EmqxAuthRequest,
    MqttClientStatus,
    MqttRawMessage,
)
from app.services.mqtt_adapter import process_mqtt_status_message
from app.services.mqtt_client_service import mqtt_client_service

logger = logging.getLogger(__name__)

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
    await mqtt_client_service.process_raw_message(
        payload.topic,
        json.dumps(payload.payload, ensure_ascii=False),
    )
    return mqtt_client_service.status()


# ── EMQX HTTP 认证/鉴权回调 ──────────────────────────────────────
# 这两个端点供 EMQX HTTP Auth Plugin 调用，不需要 JWT，靠内网隔离保护。


@router.post("/emqx/auth")
async def emqx_device_auth(
    payload: EmqxAuthRequest,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    EMQX 设备接入认证回调。
    设备连接 EMQX 时，EMQX 用设备提供的 username/password 请求本接口。
    200 = 允许连接；401 = 拒绝。
    同时允许后端自身的 MQTT 客户端（mqtt_client_id）连接。
    """
    from app.core.config import settings

    # 放行后端自身的 MQTT 客户端
    if payload.username == settings.MQTT_USERNAME and payload.password == settings.MQTT_PASSWORD:
        return Response(status_code=200, content='{"result": "allow"}', media_type="application/json")

    result = await db.execute(
        select(Device).where(Device.mqtt_username == payload.username)
    )
    device = result.scalar_one_or_none()
    if not device:
        logger.warning("EMQX auth: unknown username %s", payload.username)
        return Response(status_code=401, content='{"result": "deny"}', media_type="application/json")

    if device.mqtt_password != payload.password:
        logger.warning("EMQX auth: wrong password for device %s", device.serial_number)
        return Response(status_code=401, content='{"result": "deny"}', media_type="application/json")

    logger.info("EMQX auth: device %s authenticated", device.serial_number)
    return Response(status_code=200, content='{"result": "allow"}', media_type="application/json")


@router.post("/emqx/acl")
async def emqx_device_acl(
    payload: EmqxAclRequest,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    EMQX 设备发布/订阅鉴权回调。
    确保设备只能访问自己的 Topic，防止串设备读取他人数据。
    """
    from app.core.config import settings

    # 放行后端自身的 MQTT 客户端（需要订阅通配符 Topic）
    if payload.username == settings.MQTT_USERNAME:
        return Response(status_code=200, content='{"result": "allow"}', media_type="application/json")

    result = await db.execute(
        select(Device).where(Device.mqtt_username == payload.username)
    )
    device = result.scalar_one_or_none()
    if not device:
        return Response(status_code=403, content='{"result": "deny"}', media_type="application/json")

    # 设备只允许发布自己的上行 Topic、订阅自己的下行 Topic
    allowed = False
    if payload.action == "publish" and payload.topic == device.mqtt_pub_topic:
        allowed = True
    elif payload.action == "subscribe" and payload.topic == device.mqtt_sub_topic:
        allowed = True

    if allowed:
        return Response(status_code=200, content='{"result": "allow"}', media_type="application/json")

    logger.warning(
        "EMQX ACL denied: device %s %s on topic %s",
        device.serial_number, payload.action, payload.topic,
    )
    return Response(status_code=403, content='{"result": "deny"}', media_type="application/json")
