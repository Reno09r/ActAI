from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL

# Создаем асинхронный движок базы данных
saengine = create_async_engine(
    DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'),
    echo=True
)

# Создаем фабрику асинхронных сессий
async_session = sessionmaker(
    saengine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Создаем базовый класс для моделей
Base = declarative_base()

async def init_db():
    """Асинхронная функция для создания таблиц"""
    async with saengine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """Dependency для получения асинхронной сессии базы данных"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()