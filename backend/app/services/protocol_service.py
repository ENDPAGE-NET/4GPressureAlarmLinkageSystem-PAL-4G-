from datetime import datetime, timezone

from app.core.config import settings
from app.models.protocol_profile import ProtocolProfile
from app.schemas.protocol import (
    ProtocolFeedbackResult,
    ProtocolTopicInfo,
    RelayCommandPayload,
)
from app.services.protocol_profile_service import render_topic_template


def _normalize_topic_prefix(prefix: str) -> list[str]:
    return [segment for segment in prefix.strip("/").split("/") if segment]


def parse_mqtt_topic(topic: str) -> ProtocolTopicInfo:
    # topic 解析优先基于配置前缀，不把规则硬编码死在业务层。
    parts = [segment for segment in topic.strip("/").split("/") if segment]
    status_prefix = _normalize_topic_prefix(settings.MQTT_STATUS_TOPIC.replace("#", ""))
    feedback_prefix = _normalize_topic_prefix(settings.MQTT_FEEDBACK_TOPIC.replace("#", ""))

    for category, prefix in (("status", status_prefix), ("feedback", feedback_prefix)):
        if len(parts) >= len(prefix) + 2 and parts[: len(prefix)] == prefix:
            return ProtocolTopicInfo(
                category=category,
                serial_number=parts[len(prefix)],
                module_code=parts[len(prefix) + 1],
                raw_topic=topic,
                matched_prefix="/".join(prefix),
            )

    return ProtocolTopicInfo(category="unknown", raw_topic=topic)


def build_relay_command_topic(serial_number: str, module_code: str) -> str:
    return f"{settings.MQTT_COMMAND_TOPIC_PREFIX}/{serial_number}/{module_code}"


def build_protocol_command_topic(
    serial_number: str,
    module_code: str,
    profile: ProtocolProfile | None = None,
) -> str:
    if profile:
        return render_topic_template(
            profile.command_topic_template,
            serial_number=serial_number,
            module_code=module_code,
        )
    return build_relay_command_topic(serial_number, module_code)


def build_relay_command_payload(
    serial_number: str,
    module_code: str,
    target_state: str,
    command_id: int,
) -> RelayCommandPayload:
    # 下发 payload 统一在协议层组装，后续替换真实协议字段时只改这一处。
    return RelayCommandPayload(
        serial_number=serial_number,
        module_code=module_code,
        target_state=target_state,
        command_id=command_id,
        sent_at=datetime.now(timezone.utc).isoformat(),
    )


def map_feedback_payload(
    execution_status: str,
    feedback_status: str | None,
    feedback_message: str | None,
    error_code: str | None,
) -> ProtocolFeedbackResult:
    # 设备反馈统一在协议层做错误码与状态归一化，业务层只处理标准状态。
    normalized_feedback_status = feedback_status or "device_ack"
    normalized_execution_status = execution_status
    normalized_feedback_message = feedback_message

    if error_code:
        normalized_execution_status = "failed"
        normalized_feedback_status = "device_error"
        normalized_feedback_message = feedback_message or f"device error: {error_code}"

    return ProtocolFeedbackResult(
        execution_status=normalized_execution_status,
        feedback_status=normalized_feedback_status,
        feedback_message=normalized_feedback_message,
        error_code=error_code,
    )
