from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/order_db"

    # конфиг для JWT
    JWT_SECRET_KEY: str = "CHNG_IT"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24

    # конфиг для redis
    REDIS_URL: str = "redis://redis:6379/0"
    ORDER_CACHE_EXPIRE_SECONDS: int = 300 


    class Config:
        env_file = ".env"

settings = Settings()