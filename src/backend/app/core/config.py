from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Real Estate Management"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/real_estate"

    REDIS_URL: str = "redis://redis:6379/0"
    # Broker Celery dùng database Redis riêng với cache/rate limit (ARCHITECTURE R8):
    # FLUSHDB hay eviction của cache không làm mất message job.
    CELERY_BROKER_URL: str = "redis://redis:6379/1"

    # Không đặt default: thiếu biến này thì ứng dụng phải dừng ngay khi khởi động
    # thay vì chạy với secret ai cũng biết (PLAN task 0.7).
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    # SPEC SP-01: access token đề xuất 15 phút, không có refresh token trong MVP.
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # Kho tệp riêng tư (PLAN task 4.5): volume Docker cho MVP (PLAN Q2).
    FILE_STORAGE_DIR: str = "/var/lib/rem/files"

    # SMTP (PLAN task 4.4). Dev dùng MailHog trong compose, không cần đăng nhập.
    SMTP_HOST: str = "mailhog"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_STARTTLS: bool = False
    SMTP_TIMEOUT_SECONDS: float = 10.0
    SMTP_FROM: str = "Real Estate Management <no-reply@demo.com>"

    # Địa chỉ giao diện người dùng, dùng để dựng liên kết trong email.
    PUBLIC_APP_URL: str = "http://localhost:8080"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
