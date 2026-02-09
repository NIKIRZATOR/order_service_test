from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# подключение и управление сессией
engine = create_async_engine(settings.database_url, echo=True)
asyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_database():
    async with asyncSessionLocal() as session:
        yield session