from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Real Estate Management"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/real_estate"

    REDIS_URL: str = "redis://redis:6379/0"

    # Không đặt default: thiếu biến này thì ứng dụng phải dừng ngay khi khởi động
    # thay vì chạy với secret ai cũng biết (PLAN task 0.7).
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    # SPEC SP-01: access token đề xuất 15 phút, không có refresh token trong MVP.
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
