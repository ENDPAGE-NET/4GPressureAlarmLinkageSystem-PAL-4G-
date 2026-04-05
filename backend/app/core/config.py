from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "PAL_4G Backend"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "sqlite+aiosqlite:///./pal_4g.db"

    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ALGORITHM: str = "HS256"
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123456"

    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: str = ""
    MQTT_PASSWORD: str = ""
    MQTT_CLIENT_ID: str = "pal_4g_backend"
    MQTT_STATUS_TOPIC: str = "pal_4g/status/#"
    MQTT_FEEDBACK_TOPIC: str = "pal_4g/feedback/#"
    MQTT_COMMAND_TOPIC_PREFIX: str = "pal_4g/commands"
    MQTT_ENABLED: bool = False

    LOG_LEVEL: str = "INFO"
    LOG_ROOT_DIR: str = "logs"
    BACKUP_ROOT_DIR: str = "backups"
    HEARTBEAT_TIMEOUT_SECONDS: int = 300
    OFFLINE_CHECK_INTERVAL_SECONDS: int = 60
    RETRY_PENDING_COMMANDS_INTERVAL_SECONDS: int = 60
    ALARM_RECOVERY_CHECK_INTERVAL_SECONDS: int = 60
    ALARM_NOTIFICATION_DISPATCH_INTERVAL_SECONDS: int = 60
    ALARM_LOW_BATTERY_RECOVERY_THRESHOLD: int = 30
    ALARM_LOW_VOLTAGE_RECOVERY_THRESHOLD: float = 3.3
    ALARM_HIGH_VOLTAGE_RECOVERY_THRESHOLD: float = 4.3
    LOG_RETENTION_DAYS: int = 7
    BACKUP_RETENTION_DAYS: int = 7

    WECHAT_ENABLED: bool = False
    WECHAT_LOGIN_USE_REAL_CODE2SESSION: bool = False
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""
    WECHAT_API_BASE_URL: str = "https://api.weixin.qq.com"
    WECHAT_SUBSCRIBE_TEMPLATE_ID: str = ""
    WECHAT_SUBSCRIBE_PAGE: str = "pages/alarms/index"
    WECHAT_SUBSCRIBE_MINIPROGRAM_STATE: str = "formal"
    WECHAT_SUBSCRIBE_LANG: str = "zh_CN"
    WECHAT_SUBSCRIBE_FIELD_ALARM_TYPE: str = "thing1"
    WECHAT_SUBSCRIBE_FIELD_DEVICE_NAME: str = "thing2"
    WECHAT_SUBSCRIBE_FIELD_TRIGGER_TIME: str = "time3"
    WECHAT_SUBSCRIBE_FIELD_REMARK: str = "thing4"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @property
    def log_root_path(self) -> Path:
        return Path(self.LOG_ROOT_DIR)

    @property
    def backup_root_path(self) -> Path:
        return Path(self.BACKUP_ROOT_DIR)


settings = Settings()
