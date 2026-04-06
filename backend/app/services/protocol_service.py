from datetime import datetime, timezone

from app.models.protocol_profile import ProtocolProfile
from app.schemas.protocol import (
    ProtocolFeedbackResult,
    ProtocolTopicInfo,
    RelayCommandPayload,
)
from app.services.protocol_profile_service import render_topic_template


def parse_mqtt_topic(topic: str) -> ProtocolTopicInfo:
    parts = [segment for segment in topic.strip("/").split("/") if segment]
    if len(parts) == 4 and parts[0] == "pal4g" and parts[1] == "devices":
        category = parts[3]
        if category in {"status", "alarm", "feedback", "command"}:
            return ProtocolTopicInfo(
                category=category,
                serial_number=parts[2],
                module_code=None,
                raw_topic=topic,
                matched_prefix="pal4g/devices",
            )

    return ProtocolTopicInfo(category="unknown", raw_topic=topic)


def build_relay_command_topic(serial_number: str, module_code: str | None = None) -> str:
    return f"pal4g/devices/{serial_number}/command"


def build_protocol_command_topic(
    serial_number: str,
    module_code: str | None,
    profile: ProtocolProfile | None = None,
) -> str:
    if profile:
        return render_topic_template(
            profile.command_topic_template,
            serial_number=serial_number,
            module_code=module_code or "MAIN",
        )
    return build_relay_command_topic(serial_number, module_code)


def build_relay_command_payload(
    serial_number: str,
    module_code: str | None,
    target_state: str,
    command_id: int,
) -> RelayCommandPayload:
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
