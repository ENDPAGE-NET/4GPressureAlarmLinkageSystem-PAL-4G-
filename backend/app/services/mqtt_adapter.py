from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.device import Device
from app.models.module import Module
from app.schemas.device import ModuleStatusReport
from app.schemas.mqtt import MqttRelayFeedbackMessage, MqttStatusMessage
from app.schemas.relay import RelayCommandFeedback
from app.services.device_service import update_module_status
from app.services.linkage_service import apply_relay_command_feedback, get_relay_command_by_id
from app.services.protocol_service import map_feedback_payload


def normalize_mqtt_status_payload(payload: dict) -> MqttStatusMessage:
    # MQTT 上报字段先归一化成内部 schema，避免协议字段直接散落到业务代码里。
    return MqttStatusMessage.model_validate(payload)


def normalize_mqtt_feedback_payload(payload: dict) -> MqttRelayFeedbackMessage:
    # 设备反馈也统一走 schema 校验，便于后续替换成真实协议字段映射。
    return MqttRelayFeedbackMessage.model_validate(payload)


async def get_module_by_serial_and_code(
    db: AsyncSession,
    serial_number: str,
    module_code: str,
) -> Module | None:
    # 新模型优先按模块自身 SN 定位；旧数据继续兼容“设备 SN + 模块编码”。
    stmt = (
        select(Module)
        .options(selectinload(Module.device))
        .where(Module.serial_number == serial_number, Module.module_code == module_code)
    )
    result = await db.execute(stmt)
    module = result.scalar_one_or_none()
    if module:
        return module

    stmt = (
        select(Module)
        .join(Device, Module.device_id == Device.id)
        .options(selectinload(Module.device))
        .where(Device.serial_number == serial_number, Module.module_code == module_code)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def process_mqtt_status_message(
    db: AsyncSession,
    payload: dict,
) -> Module:
    message = normalize_mqtt_status_payload(payload)
    module = await get_module_by_serial_and_code(
        db=db,
        serial_number=message.serial_number,
        module_code=message.module_code,
    )
    if not module:
        raise ValueError("Module not found for incoming MQTT payload")

    # MQTT 状态消息最终复用模块状态更新主链路，避免和 HTTP 上报出现两套规则。
    updated_module = await update_module_status(
        db,
        module,
        ModuleStatusReport(
            is_online=message.is_online,
            source="mqtt_report",
            relay_state=message.relay_state,
            battery_level=message.battery_level,
            voltage_value=message.voltage_value,
            trigger_alarm_type=message.trigger_alarm_type,
            alarm_message=message.alarm_message,
        ),
    )
    return updated_module


async def process_mqtt_feedback_message(
    db: AsyncSession,
    payload: dict,
):
    message = normalize_mqtt_feedback_payload(payload)
    command = await get_relay_command_by_id(db, message.command_id)
    if not command:
        raise ValueError("Relay command not found for incoming MQTT feedback")

    # 设备 ACK 会直接回写指令执行状态，后续可继续扩展错误码与重试规则。
    feedback_result = map_feedback_payload(
        execution_status=message.execution_status,
        feedback_status=message.feedback_status,
        feedback_message=message.feedback_message,
        error_code=message.error_code,
    )

    updated_command = await apply_relay_command_feedback(
        db,
        command,
        RelayCommandFeedback(
            execution_status=feedback_result.execution_status,
            feedback_status=feedback_result.feedback_status,
            feedback_message=feedback_result.feedback_message,
        ),
    )
    return updated_command
