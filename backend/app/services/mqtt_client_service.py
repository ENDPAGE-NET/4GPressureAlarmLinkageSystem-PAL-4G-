import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from paho.mqtt import client as mqtt_client

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.schemas.mqtt_client import MqttClientStatus, MqttPublishResult
from app.services.logging_service import write_communication_log, write_runtime_log
from app.services.mqtt_adapter import (
    process_mqtt_feedback_message,
    process_mqtt_status_message,
)
from app.services.protocol_service import build_relay_command_topic, parse_mqtt_topic

logger = logging.getLogger(__name__)


class MqttClientService:
    def __init__(self) -> None:
        self._client: mqtt_client.Client | None = None
        self._connected = False
        self._subscribed_topics = [settings.MQTT_STATUS_TOPIC, settings.MQTT_FEEDBACK_TOPIC]
        self._received_message_count = 0
        self._published_message_count = 0
        self._last_inbound_topic: str | None = None
        self._last_inbound_at: datetime | None = None
        self._last_outbound_topic: str | None = None
        self._last_outbound_at: datetime | None = None

    def status(self) -> MqttClientStatus:
        return MqttClientStatus(
            enabled=settings.MQTT_ENABLED,
            connected=self._connected,
            broker_host=settings.MQTT_BROKER_HOST,
            broker_port=settings.MQTT_BROKER_PORT,
            status_topic=settings.MQTT_STATUS_TOPIC,
            subscribed_topics=self._subscribed_topics,
            received_message_count=self._received_message_count,
            published_message_count=self._published_message_count,
            last_inbound_topic=self._last_inbound_topic,
            last_inbound_at=self._last_inbound_at.isoformat() if self._last_inbound_at else None,
            last_outbound_topic=self._last_outbound_topic,
            last_outbound_at=self._last_outbound_at.isoformat() if self._last_outbound_at else None,
        )

    def start(self) -> None:
        if not settings.MQTT_ENABLED:
            logger.info("MQTT is disabled, skip starting client")
            return
        if self._client:
            return

        client = mqtt_client.Client(
            client_id=settings.MQTT_CLIENT_ID,
            protocol=mqtt_client.MQTTv311,
        )
        if settings.MQTT_USERNAME:
            client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message

        self._client = client
        try:
            client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, keepalive=60)
            client.loop_start()
            logger.info(
                "MQTT client started for broker %s:%s",
                settings.MQTT_BROKER_HOST,
                settings.MQTT_BROKER_PORT,
            )
        except Exception as exc:
            logger.exception("Failed to start MQTT client: %s", exc)

    def stop(self) -> None:
        if not self._client:
            return
        self._client.loop_stop()
        self._client.disconnect()
        self._client = None
        self._connected = False
        logger.info("MQTT client stopped")

    def _on_connect(
        self,
        client: mqtt_client.Client,
        _userdata: Any,
        _flags: dict,
        rc: int,
    ) -> None:
        self._connected = rc == 0
        if rc == 0:
            # 连接成功后同时订阅状态主题和反馈主题，确保设备上下行都能被消费。
            for topic in self._subscribed_topics:
                client.subscribe(topic)
            logger.info("MQTT subscribed topics: %s", ",".join(self._subscribed_topics))
        else:
            logger.error("MQTT connect failed with rc=%s", rc)

    def _on_disconnect(
        self,
        _client: mqtt_client.Client,
        _userdata: Any,
        rc: int,
    ) -> None:
        self._connected = False
        logger.warning("MQTT disconnected with rc=%s", rc)

    def _on_message(
        self,
        _client: mqtt_client.Client,
        _userdata: Any,
        msg: mqtt_client.MQTTMessage,
    ) -> None:
        payload_text = msg.payload.decode("utf-8")
        asyncio.run(self.process_raw_message(msg.topic, payload_text))

    async def process_raw_message(self, topic: str, payload_text: str) -> None:
        async with AsyncSessionLocal() as session:
            try:
                payload = json.loads(payload_text)
                topic_info = parse_mqtt_topic(topic)
                self._received_message_count += 1
                self._last_inbound_topic = topic
                self._last_inbound_at = datetime.now(timezone.utc)

                # 依据 topic 分类分发到状态上报或设备反馈处理链路。
                if topic_info.category == "feedback":
                    updated_command = await process_mqtt_feedback_message(session, payload)
                    await write_communication_log(
                        session,
                        channel="mqtt_feedback",
                        direction="inbound",
                        status=updated_command.execution_status,
                        device_serial=payload.get("serial_number"),
                        module_code=payload.get("module_code"),
                        payload=payload,
                        message=f"processed mqtt feedback topic {topic}",
                    )
                    return

                await process_mqtt_status_message(session, payload)
                await write_communication_log(
                    session,
                    channel="mqtt",
                    direction="inbound",
                    status="success",
                    device_serial=topic_info.serial_number or payload.get("serial_number"),
                    module_code=topic_info.module_code or payload.get("module_code"),
                    payload=payload,
                    message=f"processed mqtt topic {topic}",
                )
            except Exception as exc:
                await write_runtime_log(
                    session,
                    level="ERROR",
                    event="mqtt_message_error",
                    message=str(exc),
                    context={"topic": topic, "payload": payload_text},
                )
                logger.exception("Failed to process MQTT message: %s", exc)

    def publish_relay_command(
        self,
        serial_number: str,
        module_code: str,
        payload: dict,
    ) -> MqttPublishResult:
        topic = build_relay_command_topic(serial_number, module_code)
        # 无论 broker 是否在线，都返回统一结果结构，便于上层记录通信日志和调试。
        if self._client and self._connected:
            self._client.publish(topic, json.dumps(payload, ensure_ascii=False))
            self._published_message_count += 1
            self._last_outbound_topic = topic
            self._last_outbound_at = datetime.now(timezone.utc)
            return MqttPublishResult(
                topic=topic,
                payload=payload,
                published=True,
                reason="published to mqtt broker",
            )

        return MqttPublishResult(
            topic=topic,
            payload=payload,
            published=False,
            reason="mqtt client is disabled or disconnected",
        )


mqtt_client_service = MqttClientService()
