from typing import AsyncGenerator

import sqlalchemy
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker

from config import DATABASE_PATH, logger
from models import Base


# Создаем асинхронный движок SQLAlchemy с aiosqlite
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Установить True для отладки SQL-запросов
    future=True,
)

# Асинхронная фабрика сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    """
    Инициализация базы данных: создание всех таблиц.
    Вызывается один раз при запуске бота.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("База данных успешно инициализирована")
    except Exception as e:
        logger.error(f"Ошибка при инициализации БД: {e}")
        raise


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Генератор асинхронных сессий для использования в хендлерах.

    Использование:
        async with get_async_session() as session:
            # работа с сессией
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_context():
    """
    Контекстный менеджер для работы с БД.
    Возвращает сессию и гарантирует закрытие.

    Использование:
        async with get_db_context() as session:
            # работа с сессией
    """
    session = async_session_maker()
    try:
        yield session
    finally:
        await session.close()


async def check_db_connection() -> bool:
    """
    Проверка подключения к базе данных.
    Возвращает True если подключение успешно.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(sqlalchemy.text("SELECT 1"))
        logger.debug("Подключение к БД успешно")
        return True
    except Exception as e:
        logger.error(f"Ошибка подключения к БД: {e}")
        return False