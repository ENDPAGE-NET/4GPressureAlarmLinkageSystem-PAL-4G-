from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_admin, get_current_user
from app.db.session import get_db
from app.models.device import Device
from app.models.module import Module
from app.models.user import User
from app.schemas.relay import (
    RelayCommandCreate,
    RelayCommandFeedback,
    RelayCommandRead,
    RelayRetryResult,
)
from app.services.linkage_service import (
    apply_relay_command_feedback,
    create_manual_relay_command,
    get_relay_command_by_id,
    list_relay_commands,
    retry_queued_relay_commands,
)
from app.services.logging_service import write_communication_log, write_operation_log
from app.services.mqtt_client_service import mqtt_client_service
from app.services.protocol_service import build_relay_command_payload

router = APIRouter()


async def get_relay_command_target_module(
    db: AsyncSession,
    module_id: int,
) -> Module | None:
    stmt = (
        select(Module)
        .options(selectinload(Module.device))
        .where(Module.id == module_id)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


@router.get("", response_model=list[RelayCommandRead])
async def read_relay_commands(
    alarm_record_id: int | None = Query(default=None),
    execution_status: str | None = Query(default=None),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[RelayCommandRead]:
    commands = await list_relay_commands(
        db,
        alarm_record_id=alarm_record_id,
        execution_status=execution_status,
    )
    return [RelayCommandRead.model_validate(command) for command in commands]


@router.post("/retry-pending", response_model=RelayRetryResult)
async def retry_pending_relay_commands(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> RelayRetryResult:
    return await retry_queued_relay_commands(db)


@router.post("", response_model=RelayCommandRead, status_code=status.HTTP_201_CREATED)
async def create_relay_command(
    payload: RelayCommandCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RelayCommandRead:
    module = (await db.execute(select(Module).where(Module.id == payload.module_id))).scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

    if current_user.role != "super_admin":
        module_with_device = await get_relay_command_target_module(db, payload.module_id)
        if not module_with_device or module_with_device.device.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    command = await create_manual_relay_command(db, payload)
    module_with_device = await get_relay_command_target_module(db, payload.module_id)
    if module_with_device and module_with_device.device:
        command_payload = build_relay_command_payload(
            serial_number=module_with_device.device.serial_number,
            module_code=module_with_device.module_code,
            target_state=payload.target_state,
            command_id=command.id,
        )
        publish_result = mqtt_client_service.publish_relay_command(
            serial_number=module_with_device.device.serial_number,
            module_code=module_with_device.module_code,
            payload=command_payload.model_dump(),
        )
        await write_communication_log(
            db,
            channel="mqtt_command",
            direction="outbound",
            status="published" if publish_result.published else "queued",
            device_serial=module_with_device.device.serial_number,
            module_code=module_with_device.module_code,
            payload=publish_result.payload,
            message=f"{publish_result.reason}: {publish_result.topic}",
        )
    await write_operation_log(
        db,
        action="create_relay_command",
        target_type="relay_command",
        actor_user_id=current_user.id,
        target_id=command.id,
        detail=f"manual relay command for module {payload.module_id}",
    )
    return RelayCommandRead.model_validate(command)


@router.post("/{command_id}/feedback", response_model=RelayCommandRead)
async def report_relay_command_feedback(
    command_id: int,
    payload: RelayCommandFeedback,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RelayCommandRead:
    command = await get_relay_command_by_id(db, command_id)
    if not command:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relay command not found")

    if current_user.role != "super_admin":
        module_with_device = await get_relay_command_target_module(db, command.module_id)
        if not module_with_device or module_with_device.device.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    updated_command = await apply_relay_command_feedback(db, command, payload)
    await write_communication_log(
        db,
        channel="device_feedback",
        direction="inbound",
        status=payload.execution_status,
        module_code=updated_command.module.module_code if updated_command.module else None,
        message=payload.feedback_message or "relay command feedback received",
    )
    return RelayCommandRead.model_validate(updated_command)
