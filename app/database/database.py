from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from ..settings import settings
from .models import Base

engine = create_async_engine(url=settings.DB_URI, pool_pre_ping=True)
DBAsyncSession = async_sessionmaker(bind=engine)


async def create_all_tables() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
