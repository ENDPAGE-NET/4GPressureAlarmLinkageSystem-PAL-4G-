from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.notification import (
    NotificationSubscribeRequest,
    NotificationSubscriptionStatus,
)
from app.services.notification_service import (
    build_subscription_status,
    get_subscription_record,
    subscribe_notifications,
    unsubscribe_notifications,
)

router = APIRouter()


@router.get("/subscription-status", response_model=NotificationSubscriptionStatus)
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationSubscriptionStatus:
    record = await get_subscription_record(db, current_user.id)
    return build_subscription_status(record)


@router.post("/subscribe", response_model=NotificationSubscriptionStatus)
async def subscribe(
    payload: NotificationSubscribeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationSubscriptionStatus:
    record = await subscribe_notifications(db, current_user, payload)
    return build_subscription_status(record)


@router.post("/unsubscribe", response_model=NotificationSubscriptionStatus)
async def unsubscribe(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationSubscriptionStatus:
    record = await unsubscribe_notifications(db, current_user)
    return build_subscription_status(record)
