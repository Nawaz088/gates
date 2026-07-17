from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GATES_",
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,
    )

    env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    public_url: str = "http://localhost:8000"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://gates:gates@localhost:5432/gates"
    database_test_url: str = "postgresql+asyncpg://gates:gates@localhost:5433/gates_test"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Crypto
    field_encryption_key: str = ""
    jwt_signing_key: str = "dev-test-key-that-is-at-least-32-bytes-long!!"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    refresh_token_expire_days: int = 60

    # Cookies
    cookie_domain: str = "localhost"
    cookie_secure: bool = False
    cookie_same_site: str = "lax"

    # Email
    email_provider: str = "postmark"
    postmark_token: str = ""
    ses_region: str = "us-east-1"

    # SMS
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_messaging_service_sid: str = ""

    # S3
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minio"
    s3_secret_key: str = "minio123"
    s3_bucket: str = "gates"
    s3_region: str = "us-east-1"

    # Captcha / bot protection
    captcha_provider: str = ""
    turnstile_secret: str = ""

    # Webhook
    webhook_timeout: int = 10

    # Logging
    log_level: str = "INFO"


settings = Settings()
