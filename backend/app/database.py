from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

engine: AsyncEngine | None = None
SessionFactory: async_sessionmaker[AsyncSession] | None = None


def init_engine(url: str) -> None:
    global engine, SessionFactory
    kwargs: dict = {"echo": False}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        kwargs["poolclass"] = StaticPool
    engine = create_async_engine(url, **kwargs)
    SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


def session_factory() -> AsyncSession:
    if SessionFactory is None:
        raise RuntimeError("database is not initialized")
    return SessionFactory()


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    global engine
    if engine is not None:
        await engine.dispose()
        engine = None
