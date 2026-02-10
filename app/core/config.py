from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str

    # config for JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # config for redis
    REDIS_URL: str
    ORDER_CACHE_EXPIRE_SECONDS: int

    # config for RabbitMQ
    RABBIT_URL: str
    NEW_ORDER_QUEUE: str

settings = Settings()
