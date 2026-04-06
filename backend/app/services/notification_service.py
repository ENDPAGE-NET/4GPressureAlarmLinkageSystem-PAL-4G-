import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.alarm_record import AlarmRecord
from app.models.device import Device
from app.models.module import Module
from app.models.notification_subscription import NotificationSubscription
from app.models.user import User
from app.schemas.notification import (
    NotificationSubscribeRequest,
    NotificationSubscriptionStatus,
)
from app.services.logging_service import write_communication_log
from app.services.wechat_service import send_subscribe_message


def _deserialize_template_ids(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    try:
        values = json.loads(raw_value)
    except json.JSONDecodeError:
        return []
    if not isinstance(values, list):
        return []
    return [str(item) for item in values if str(item).strip()]


def _serialize_template_ids(template_ids: list[str]) -> str:
    return json.dumps(template_ids, ensure_ascii=False)


def get_available_template_ids(
    record: NotificationSubscription | None = None,
) -> list[str]:
    if settings.WECHAT_SUBSCRIBE_TEMPLATE_ID:
        return [settings.WECHAT_SUBSCRIBE_TEMPLATE_ID]
    if record:
        return _deserialize_template_ids(record.template_ids)
    return []


async def get_subscription_record(
    db: AsyncSession,
    user_id: int,
) -> NotificationSubscription | None:
    result = await db.execute(
        select(NotificationSubscription).where(NotificationSubscription.user_id == user_id)
    )
    return result.scalar_one_or_none()


def build_subscription_status(
    record: NotificationSubscription | None,
) -> NotificationSubscriptionStatus:
    if not record:
        return NotificationSubscriptionStatus(
            enabled=False,
            template_ids=[],
            available_template_ids=get_available_template_ids(),
        )
    return NotificationSubscriptionStatus(
        subscription_type=record.subscription_type,
        enabled=record.is_enabled,
        template_ids=_deserialize_template_ids(record.template_ids),
        available_template_ids=get_available_template_ids(record),
        source=record.source,
        subscribed_at=record.subscribed_at,
        unsubscribed_at=record.unsubscribed_at,
        updated_at=record.updated_at,
    )


async def subscribe_notifications(
    db: AsyncSession,
    user: User,
    payload: NotificationSubscribeRequest,
) -> NotificationSubscription:
    record = await get_subscription_record(db, user.id)
    now = datetime.now(timezone.utc)
    if not record:
        record = NotificationSubscription(user_id=user.id)
        db.add(record)

    record.subscription_type = "alarm"
    record.is_enabled = True
    record.template_ids = _serialize_template_ids(payload.template_ids)
    record.source = payload.source
    record.subscribed_at = now
    await db.commit()
    await db.refresh(record)
    return record


async def unsubscribe_notifications(
    db: AsyncSession,
    user: User,
) -> NotificationSubscription:
    record = await get_subscription_record(db, user.id)
    now = datetime.now(timezone.utc)
    if not record:
        record = NotificationSubscription(
            user_id=user.id,
            subscription_type="alarm",
            is_enabled=False,
            template_ids=_serialize_template_ids([]),
        )
        db.add(record)

    record.is_enabled = False
    record.unsubscribed_at = now
    await db.commit()
    await db.refresh(record)
    return record


def _format_time_value(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def build_alarm_notification_payload(alarm: AlarmRecord) -> dict:
    device = alarm.module.device if alarm.module else None
    return {
        settings.WECHAT_SUBSCRIBE_FIELD_ALARM_TYPE: {
            "value": alarm.alarm_type,
        },
        settings.WECHAT_SUBSCRIBE_FIELD_DEVICE_NAME: {
            "value": device.name if device else "-",
        },
        settings.WECHAT_SUBSCRIBE_FIELD_TRIGGER_TIME: {
            "value": _format_time_value(alarm.triggered_at),
        },
        settings.WECHAT_SUBSCRIBE_FIELD_REMARK: {
            "value": alarm.message or "设备报警，请尽快处理",
        },
    }


def resolve_alarm_template_id(record: NotificationSubscription) -> str:
    if settings.WECHAT_SUBSCRIBE_TEMPLATE_ID:
        return settings.WECHAT_SUBSCRIBE_TEMPLATE_ID
    template_ids = _deserialize_template_ids(record.template_ids)
    if template_ids:
        return template_ids[0]
    raise ValueError("No WeChat subscribe template id configured")


async def dispatch_pending_alarm_notifications(
    db: AsyncSession,
    limit: int = 20,
) -> dict[str, int]:
    stmt = (
        select(AlarmRecord)
        .options(
            selectinload(AlarmRecord.module)
            .selectinload(Module.device)
            .selectinload(Device.owner)
        )
        .where(AlarmRecord.notification_status.in_(["pending", "failed"]))
        .order_by(AlarmRecord.triggered_at.asc(), AlarmRecord.id.asc())
        .limit(limit)
    )
    alarms = list((await db.execute(stmt)).scalars().all())

    processed_count = 0
    sent_count = 0
    failed_count = 0
    skipped_count = 0

    for alarm in alarms:
        processed_count += 1
        alarm.notification_attempts += 1
        device = alarm.module.device if alarm.module else None
        owner = device.owner if device else None

        if not owner or not owner.wechat_open_id:
            alarm.notification_status = "skipped"
            alarm.notification_result = "Device owner has no bound WeChat account"
            skipped_count += 1
            await db.commit()
            continue

        subscription_record = await get_subscription_record(db, owner.id)
        if not subscription_record or not subscription_record.is_enabled:
            alarm.notification_status = "skipped"
            alarm.notification_result = "Alarm notification subscription is disabled"
            skipped_count += 1
            await db.commit()
            continue

        try:
            template_id = resolve_alarm_template_id(subscription_record)
            message_payload = build_alarm_notification_payload(alarm)
            result = await send_subscribe_message(
                openid=owner.wechat_open_id,
                template_id=template_id,
                data=message_payload,
            )
            alarm.notification_status = "sent"
            alarm.notification_result = json.dumps(result, ensure_ascii=False)
            alarm.notification_sent_at = datetime.now(timezone.utc)
            sent_count += 1
            await db.commit()
            await write_communication_log(
                db,
                channel="wechat_subscribe_message",
                direction="outbound",
                status="success",
                device_serial=device.serial_number if device else None,
                module_code=alarm.module.module_code if alarm.module else None,
                payload=message_payload,
                message=f"alarm_id={alarm.id}",
            )
        except Exception as exc:
            alarm.notification_status = "failed"
            alarm.notification_result = str(exc)
            failed_count += 1
            await db.commit()
            await write_communication_log(
                db,
                channel="wechat_subscribe_message",
                direction="outbound",
                status="failed",
                device_serial=device.serial_number if device else None,
                module_code=alarm.module.module_code if alarm.module else None,
                message=f"alarm_id={alarm.id}: {exc}",
            )

    return {
        "processed_count": processed_count,
        "sent_count": sent_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
    }
