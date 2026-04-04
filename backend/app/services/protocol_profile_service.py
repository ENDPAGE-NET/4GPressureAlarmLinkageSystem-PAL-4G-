from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.protocol_crypto import decrypt_protocol_secret, encrypt_protocol_secret
from app.models.device import Device
from app.models.protocol_profile import ProtocolProfile
from app.schemas.protocol_profile import (
    ProtocolProfileCreate,
    ProtocolProfileRead,
    ProtocolProfileUpdate,
)

ALLOWED_TOPIC_PLACEHOLDERS = {"serial_number", "module_code"}
ALLOWED_CLIENT_ID_PLACEHOLDERS = {"serial_number", "device_id"}


def _validate_template_placeholders(template: str, allowed: set[str]) -> None:
    cursor = 0
    while True:
        start = template.find("{", cursor)
        if start == -1:
            return
        end = template.find("}", start + 1)
        if end == -1:
            raise ValueError("Template placeholder is not closed")
        key = template[start + 1 : end]
        if key not in allowed:
            raise ValueError(f"Unsupported placeholder: {key}")
        cursor = end + 1


def validate_protocol_profile_payload(
    *,
    client_id_template: str,
    status_topic_template: str,
    feedback_topic_template: str,
    command_topic_template: str,
) -> None:
    # 模板只允许有限占位符，防止前端把协议配置变成任意执行入口。
    _validate_template_placeholders(client_id_template, ALLOWED_CLIENT_ID_PLACEHOLDERS)
    _validate_template_placeholders(status_topic_template, ALLOWED_TOPIC_PLACEHOLDERS)
    _validate_template_placeholders(feedback_topic_template, ALLOWED_TOPIC_PLACEHOLDERS)
    _validate_template_placeholders(command_topic_template, ALLOWED_TOPIC_PLACEHOLDERS)


def build_protocol_profile_read(profile: ProtocolProfile) -> ProtocolProfileRead:
    return ProtocolProfileRead(
        id=profile.id,
        name=profile.name,
        protocol_type=profile.protocol_type,
        description=profile.description,
        broker_host=profile.broker_host,
        broker_port=profile.broker_port,
        client_id_template=profile.client_id_template,
        username=profile.username,
        has_password=bool(profile.password_encrypted),
        status_topic_template=profile.status_topic_template,
        feedback_topic_template=profile.feedback_topic_template,
        command_topic_template=profile.command_topic_template,
        tls_enabled=profile.tls_enabled,
        is_active=profile.is_active,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


async def list_protocol_profiles(db: AsyncSession) -> list[ProtocolProfile]:
    return list(
        (
            await db.execute(
                select(ProtocolProfile).order_by(
                    ProtocolProfile.id.desc()
                )
            )
        ).scalars().all()
    )


async def get_protocol_profile_by_id(
    db: AsyncSession,
    protocol_profile_id: int,
) -> ProtocolProfile | None:
    return (
        await db.execute(
            select(ProtocolProfile).where(ProtocolProfile.id == protocol_profile_id)
        )
    ).scalar_one_or_none()


async def get_protocol_profile_by_name(db: AsyncSession, name: str) -> ProtocolProfile | None:
    return (
        await db.execute(select(ProtocolProfile).where(ProtocolProfile.name == name))
    ).scalar_one_or_none()


async def create_protocol_profile(
    db: AsyncSession,
    payload: ProtocolProfileCreate,
) -> ProtocolProfile:
    validate_protocol_profile_payload(
        client_id_template=payload.client_id_template,
        status_topic_template=payload.status_topic_template,
        feedback_topic_template=payload.feedback_topic_template,
        command_topic_template=payload.command_topic_template,
    )
    profile = ProtocolProfile(
        name=payload.name,
        protocol_type=payload.protocol_type,
        description=payload.description,
        broker_host=payload.broker_host,
        broker_port=payload.broker_port,
        client_id_template=payload.client_id_template,
        username=payload.username,
        password_encrypted=encrypt_protocol_secret(payload.password)
        if payload.password
        else None,
        status_topic_template=payload.status_topic_template,
        feedback_topic_template=payload.feedback_topic_template,
        command_topic_template=payload.command_topic_template,
        tls_enabled=payload.tls_enabled,
        is_active=payload.is_active,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def update_protocol_profile(
    db: AsyncSession,
    profile: ProtocolProfile,
    payload: ProtocolProfileUpdate,
) -> ProtocolProfile:
    next_client_id_template = payload.client_id_template or profile.client_id_template
    next_status_topic_template = payload.status_topic_template or profile.status_topic_template
    next_feedback_topic_template = payload.feedback_topic_template or profile.feedback_topic_template
    next_command_topic_template = payload.command_topic_template or profile.command_topic_template
    validate_protocol_profile_payload(
        client_id_template=next_client_id_template,
        status_topic_template=next_status_topic_template,
        feedback_topic_template=next_feedback_topic_template,
        command_topic_template=next_command_topic_template,
    )

    for field in (
        "name",
        "protocol_type",
        "description",
        "broker_host",
        "broker_port",
        "client_id_template",
        "username",
        "status_topic_template",
        "feedback_topic_template",
        "command_topic_template",
        "tls_enabled",
        "is_active",
    ):
        value = getattr(payload, field)
        if value is not None:
            setattr(profile, field, value)

    if payload.password is not None:
        profile.password_encrypted = (
            encrypt_protocol_secret(payload.password) if payload.password else None
        )

    await db.commit()
    await db.refresh(profile)
    return profile


async def assign_device_protocol_profile(
    db: AsyncSession,
    device: Device,
    profile: ProtocolProfile | None,
) -> Device:
    device.protocol_profile_id = profile.id if profile else None
    await db.commit()
    await db.refresh(device)
    return device


def render_topic_template(
    template: str,
    *,
    serial_number: str,
    module_code: str,
) -> str:
    return template.format(serial_number=serial_number, module_code=module_code)


def render_client_id_template(
    template: str,
    *,
    serial_number: str,
    device_id: int,
) -> str:
    return template.format(serial_number=serial_number, device_id=device_id)


def get_protocol_profile_password(profile: ProtocolProfile | None) -> str | None:
    if not profile:
        return None
    return decrypt_protocol_secret(profile.password_encrypted)
