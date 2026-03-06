"""
AI Engine - Configuration
"""
from pydantic_settings import BaseSettings
from pydantic import Field, model_validator
from typing import Optional


class Settings(BaseSettings):
    # Anthropic
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    anthropic_base_url: Optional[str] = Field(None, env="ANTHROPIC_BASE_URL")
    anthropic_auth_token: Optional[str] = Field(None, env="ANTHROPIC_AUTH_TOKEN")
    claude_model: str = Field("claude-sonnet-4-6", env="CLAUDE_MODEL")

    # Default server (dùng để seed DB lần đầu, và cho AlertManager webhook)
    default_prometheus_url: str = Field("http://localhost:9090", env="PROMETHEUS_URL")
    default_loki_url: str = Field("http://localhost:3100", env="LOKI_URL")
    alertmanager_url: str = Field("http://localhost:9093", env="ALERTMANAGER_URL")

    # Server
    ai_engine_host: str = Field("0.0.0.0", env="AI_ENGINE_HOST")
    ai_engine_port: int = Field(8765, env="AI_ENGINE_PORT")

    # Scheduler
    analysis_interval_seconds: int = Field(300, env="ANALYSIS_INTERVAL_SECONDS")

    # Database
    db_path: str = Field("./data/ai_engine.db", env="DB_PATH")

    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")

    # Notifications
    google_chat_webhook_url: Optional[str] = Field(None, env="GOOGLE_CHAT_WEBHOOK_URL")

    # Authentication
    auth_username: str = Field("admin", env="AUTH_USERNAME")
    auth_password: str = Field("@ISystemInt3llig3nc3Platf()rm", env="AUTH_PASSWORD")
    auth_secret_key: str = Field("change-me-in-production-32chars!!", env="AUTH_SECRET_KEY")
    auth_session_max_age: int = Field(28800, env="AUTH_SESSION_MAX_AGE")

    @model_validator(mode="after")
    def check_api_key_or_base_url(self) -> "Settings":
        if not self.anthropic_base_url and not self.anthropic_api_key:
            raise ValueError(
                "Phải cấu hình ít nhất một trong hai:\n"
                "  - ANTHROPIC_API_KEY\n"
                "  - ANTHROPIC_BASE_URL"
            )
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
