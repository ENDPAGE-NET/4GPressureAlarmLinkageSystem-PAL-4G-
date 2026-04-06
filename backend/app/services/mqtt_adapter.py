from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.module import Module
from app.schemas.alarm import AlarmRecordCreate
from app.schemas.device import ModuleStatusReport
from app.schemas.mqtt import MqttAlarmMessage, MqttRelayFeedbackMessage, MqttStatusMessage
from app.schemas.relay import RelayCommandFeedback
from app.services.alarm_service import create_alarm_record
from app.services.device_service import update_module_status
from app.services.linkage_service import (
    apply_relay_command_feedback,
    dispatch_linkage_for_alarm,
    get_relay_command_by_id,
)
from app.services.protocol_service import map_feedback_payload
from app.services.realtime_service import realtime_service


def normalize_mqtt_status_payload(payload: dict) -> MqttStatusMessage:
    return MqttStatusMessage.model_validate(payload)


def normalize_mqtt_feedback_payload(payload: dict) -> MqttRelayFeedbackMessage:
    return MqttRelayFeedbackMessage.model_validate(payload)


def normalize_mqtt_alarm_payload(payload: dict) -> MqttAlarmMessage:
    return MqttAlarmMessage.model_validate(payload)


async def get_module_by_serial_and_code(
    db: AsyncSession,
    serial_number: str,
    module_code: str | None,
) -> Module | None:
    stmt = (
        select(Module)
        .join(Module.device)
        .options(selectinload(Module.device))
        .where(Module.device.has(serial_number=serial_number))
        .order_by(Module.id.asc())
        .limit(1)
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


async def process_mqtt_alarm_message(
    db: AsyncSession,
    payload: dict,
):
    message = normalize_mqtt_alarm_payload(payload)
    module = await get_module_by_serial_and_code(
        db=db,
        serial_number=message.serial_number,
        module_code=message.module_code,
    )
    if not module:
        raise ValueError("Module not found for incoming MQTT alarm payload")

    if (
        message.is_online is not None
        or message.relay_state is not None
        or message.battery_level is not None
        or message.voltage_value is not None
    ):
        module = await update_module_status(
            db,
            module,
            ModuleStatusReport(
                is_online=message.is_online if message.is_online is not None else True,
                source="mqtt_alarm",
                relay_state=message.relay_state,
                battery_level=message.battery_level,
                voltage_value=message.voltage_value,
            ),
        )

    alarm = await create_alarm_record(
        db,
        AlarmRecordCreate(
            module_id=module.id,
            alarm_type=message.alarm_type,
            source="mqtt_alarm",
            message=message.message or "mqtt alarm triggered",
        ),
    )
    await dispatch_linkage_for_alarm(db, alarm)
    await realtime_service.broadcast(
        "alarm.created",
        {
            "alarm_id": alarm.id,
            "device_id": module.device_id,
            "module_id": module.id,
            "alarm_type": alarm.alarm_type,
            "alarm_status": alarm.alarm_status,
            "source": alarm.source,
        },
        owner_id=module.device.owner_id if module.device else None,
    )
    return alarm


async def process_mqtt_feedback_message(
    db: AsyncSession,
    payload: dict,
):
    message = normalize_mqtt_feedback_payload(payload)
    command = await get_relay_command_by_id(db, message.command_id)
    if not command:
        raise ValueError("Relay command not found for incoming MQTT feedback")

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
