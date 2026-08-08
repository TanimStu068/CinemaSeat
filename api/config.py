import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://cinema:cinema_pass@localhost:5432/cinemaseat",
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    GATEWAY_URL: str = os.getenv("GATEWAY_URL", "http://localhost:9000")
    PAYMENT_CALLBACK_URL: str = os.getenv(
        "PAYMENT_CALLBACK_URL",
        "http://localhost:8000/webhooks/payment",
    )
    OTP_CALLBACK_URL: str = os.getenv(
        "OTP_CALLBACK_URL",
        "http://localhost:8000/webhooks/otp",
    )
    HOLD_TTL_SECONDS: int = int(os.getenv("HOLD_TTL_SECONDS", "300"))
    GATEWAY_SECRET: str = os.getenv("GATEWAY_SECRET", "z2p-2026-secret")

    class Config:
        env_file = ".env"


settings = Settings()
