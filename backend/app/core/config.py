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
    HEARTBEAT_TIMEOUT_SECONDS: int = 300
    OFFLINE_CHECK_INTERVAL_SECONDS: int = 60
    RETRY_PENDING_COMMANDS_INTERVAL_SECONDS: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @property
    def log_root_path(self) -> Path:
        return Path(self.LOG_ROOT_DIR)


settings = Settings()
