from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://cinema:cinema_pass@localhost:5432/cinemaseat"
    REDIS_URL: str = "redis://localhost:6379"
    GATEWAY_URL: str = "http://localhost:9000"
    PAYMENT_CALLBACK_URL: str = "http://localhost:8000/webhooks/payment"
    OTP_CALLBACK_URL: str = "http://localhost:8000/webhooks/otp"
    HOLD_TTL_SECONDS: int = 300
    GATEWAY_SECRET: str = "z2p-2026-secret"

    class Config:
        env_file = ".env"

settings = Settings()
