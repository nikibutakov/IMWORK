"""
Конфигурация pytest и фикстуры для тестирования ImWork Bot.

Фикстуры обеспечивают изоляцию тестов:
- Каждый тест получает чистую БД в памяти (:memory:)
- Мокированный bot и dispatcher
- Изолированное FSM storage
"""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import User as TelegramUser, Chat, Message, Update, CallbackQuery
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Base
from database import init_db
from main import setup_dispatcher


# ==================== Константы для тестов ====================

TEST_BOT_TOKEN = "1234567890:AABBccDDeeFFggHHiiJJkkLLmmNNooP"
TEST_USER_ID = 123456789
TEST_USERNAME = "test_user"
TEST_FIRST_NAME = "Test"
TEST_LAST_NAME = "User"
TEST_CHAT_ID = -987654321


# ==================== Фикстуры базы данных ====================

@pytest_asyncio.fixture(scope="function")
async def db_engine() -> AsyncGenerator:
    """
    Создает асинхронный движок SQLite в памяти.
    Каждый тест получает полностью изолированную БД.
    """
    # Используем :memory: для изоляции
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    
    # Создаем все таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Очищаем после теста
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Создает асинхронную сессию БД для каждого теста.
    Автоматически делает commit после каждого теста.
    """
    async_session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with async_session_maker() as session:
        yield session
        await session.commit()


@pytest_asyncio.fixture(scope="function")
async def initialized_db(db_engine) -> None:
    """
    Инициализирует БД (вызывает init_db).
    Используется когда требуется полная инициализация как при запуске бота.
    """
    # Переопределяем DATABASE_PATH для использования in-memory БД
    import database
    original_engine = database.engine
    database.engine = db_engine
    database.async_session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    await init_db()
    
    # Восстанавливаем оригинальный движок
    database.engine = original_engine


# ==================== Фикстуры бота и диспетчера ====================

@pytest.fixture(scope="function")
def mock_bot() -> Bot:
    """
    Создает мокированный объект Bot.
    Все методы бота заменены на AsyncMock для перехвата вызовов.
    """
    bot = Bot(
        token=TEST_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    
    # Мокаем все методы отправки сообщений
    bot.send_message = AsyncMock()
    bot.edit_message_text = AsyncMock()
    bot.edit_message_reply_markup = AsyncMock()
    bot.answer_callback_query = AsyncMock()
    bot.send_photo = AsyncMock()
    bot.send_document = AsyncMock()
    
    return bot


@pytest.fixture(scope="function")
def dp() -> Dispatcher:
    """
    Создает новый Dispatcher с MemoryStorage.
    Каждый тест получает чистый диспетчер без зарегистрированных хендлеров.
    """
    return Dispatcher(storage=MemoryStorage())


@pytest_asyncio.fixture(scope="function")
async def dp_with_handlers(db_session, mock_bot) -> Dispatcher:
    """
    Создает Dispatcher со всеми хендлерами и middleware.
    Добавляет middleware для передачи сессии БД и мокированного бота.
    
    Примечание: Роутеры импортируются из main.py где они уже зарегистрированы,
    поэтому мы используем их напрямую без повторного include.
    """
    # Создаем новый dispatcher для каждого теста
    dp = Dispatcher(storage=MemoryStorage())
    
    # Импортируем главный модуль чтобы получить доступ к роутерам
    # Роутеры в aiogram 3.x могут быть прикреплены только к одному диспетчеру
    # Поэтому мы создаем новые инстансы через копирование конфигурации
    from aiogram import Router
    
    # Создаем новые роутеры для тестов
    onboarding_router = Router()
    student_jobs_router = Router()
    career_center_router = Router()
    employer_jobs_router = Router()
    
    # Импортируем хендлеры напрямую и регистрируем в наши роутеры
    from handlers.onboarding import cmd_start, role_student_selected, role_employer_selected
    from handlers.student_jobs import job_search_start
    from handlers.career_center import career_center_start
    from handlers.employer_jobs import start_vacancy_creation
    
    # Регистрируем ключевые хендлеры для тестов
    onboarding_router.message(cmd_start)
    onboarding_router.callback_query(role_student_selected)
    onboarding_router.callback_query(role_employer_selected)
    
    student_jobs_router.callback_query(job_search_start)
    career_center_router.callback_query(career_center_start)
    employer_jobs_router.callback_query(start_vacancy_creation)
    
    dp.include_router(onboarding_router)
    dp.include_router(student_jobs_router)
    dp.include_router(career_center_router)
    dp.include_router(employer_jobs_router)
    
    # Middleware для передачи сессии БД и бота
    @dp.message.middleware()
    @dp.callback_query.middleware()
    async def test_middleware(handler, event, data):
        data['session'] = db_session
        data['bot'] = mock_bot
        return await handler(event, data)
    
    return dp


# ==================== Фикстуры для создания Update объектов ====================

@pytest.fixture
def telegram_user() -> TelegramUser:
    """Создает тестового пользователя Telegram."""
    return TelegramUser(
        id=TEST_USER_ID,
        is_bot=False,
        username=TEST_USERNAME,
        first_name=TEST_FIRST_NAME,
        last_name=TEST_LAST_NAME,
    )


@pytest.fixture
def telegram_chat() -> Chat:
    """Создает тестовый чат."""
    return Chat(
        id=TEST_CHAT_ID,
        type="private",
        first_name=TEST_FIRST_NAME,
        last_name=TEST_LAST_NAME,
        username=TEST_USERNAME,
    )


@pytest.fixture
def mock_message(telegram_user, telegram_chat) -> Message:
    """
    Создает тестовое сообщение.
    Используйте parametrize для изменения текста сообщения.
    """
    return Message(
        message_id=1,
        date=asyncio.get_event_loop().time(),
        chat=telegram_chat,
        from_user=telegram_user,
        text="/start",
    )


@pytest.fixture
def mock_update(mock_message) -> Update:
    """
    Создает Update объект с сообщением.
    Для callback_query используйте mock_callback_update.
    """
    return Update(update_id=1, message=mock_message)


@pytest.fixture
def mock_callback_query(telegram_user, telegram_chat) -> CallbackQuery:
    """
    Создает тестовый CallbackQuery.
    Используйте parametrize для изменения callback_data.
    """
    return CallbackQuery(
        id="callback_1",
        from_user=telegram_user,
        chat_instance="chat_instance_123",
        data="",
        message=Message(
            message_id=1,
            date=asyncio.get_event_loop().time(),
            chat=telegram_chat,
            from_user=telegram_user,
            text="Previous message text",
        ),
    )


@pytest.fixture
def mock_callback_update(mock_callback_query) -> Update:
    """
    Создает Update объект с callback_query.
    """
    return Update(update_id=1, callback_query=mock_callback_query)


# ==================== Утилиты для тестов ====================

@pytest.fixture
def state_storage() -> MemoryStorage:
    """
    Создает изолированное хранилище состояний FSM.
    """
    return MemoryStorage()


@pytest_asyncio.fixture
async def fsm_context(state_storage, telegram_user):
    """
    Создает контекст FSM для конкретного пользователя.
    """
    async with state_storage.lock(user=telegram_user.id):
        context = state_storage.user(user=telegram_user.id)
        yield context


# ==================== Хелперы для проверки результатов ====================

class BotCallChecker:
    """
    Утилитный класс для проверки вызовов методов бота.
    """
    
    def __init__(self, bot: Bot):
        self.bot = bot
    
    def assert_send_message_called(self, expected_text_contains: str = None):
        """Проверяет, что send_message был вызван с указанным текстом."""
        assert self.bot.send_message.called, "send_message не был вызван"
        
        if expected_text_contains:
            call_args = self.bot.send_message.call_args
            actual_text = call_args.kwargs.get('text') or call_args.args[0] if call_args.args else ''
            assert expected_text_contains in actual_text, \
                f"Ожидался текст содержащий '{expected_text_contains}', но получили '{actual_text}'"
    
    def assert_edit_message_text_called(self, expected_text_contains: str = None):
        """Проверяет, что edit_message_text был вызван."""
        assert self.bot.edit_message_text.called, "edit_message_text не был вызван"
        
        if expected_text_contains:
            call_args = self.bot.edit_message_text.call_args
            actual_text = call_args.kwargs.get('text', '')
            assert expected_text_contains in actual_text, \
                f"Ожидался текст содержащий '{expected_text_contains}', но получили '{actual_text}'"
    
    def assert_answer_callback_called(self, expected_text: str = None):
        """Проверяет, что answer_callback_query был вызван."""
        assert self.bot.answer_callback_query.called, "answer_callback_query не был вызван"
    
    def get_last_send_message_text(self) -> str:
        """Возвращает текст последнего вызова send_message."""
        if not self.bot.send_message.called:
            return ""
        call_args = self.bot.send_message.call_args
        return call_args.kwargs.get('text', '') or (call_args.args[0] if call_args.args else '')
    
    def get_last_edit_message_text(self) -> str:
        """Возвращает текст последнего вызова edit_message_text."""
        if not self.bot.edit_message_text.called:
            return ""
        call_args = self.bot.edit_message_text.call_args
        return call_args.kwargs.get('text', '')
    
    def reset_mocks(self):
        """Сбрасывает все моки бота."""
        self.bot.send_message.reset_mock()
        self.bot.edit_message_text.reset_mock()
        self.bot.edit_message_reply_markup.reset_mock()
        self.bot.answer_callback_query.reset_mock()


@pytest.fixture
def bot_checker(mock_bot) -> BotCallChecker:
    """
    Создает утилиту для проверки вызовов бота.
    
    Пример использования:
        def test_example(bot_checker, mock_bot):
            await some_handler(message, mock_bot)
            bot_checker.assert_send_message_called("приветствие")
    """
    return BotCallChecker(mock_bot)


# ==================== Фикстура для получения настроенного роутера ====================

@pytest_asyncio.fixture(scope="function")
async def configured_dp(db_session) -> Dispatcher:
    """
    Полностью настроенный Dispatcher готовый к тестированию.
    Включает все роутеры и middleware.
    """
    dp = setup_dispatcher()
    
    # Переопределяем middleware для использования тестовой сессии
    dp.message.middleware.clear()
    dp.callback_query.middleware.clear()
    
    @dp.message.middleware()
    @dp.callback_query.middleware()
    async def test_db_middleware(handler, event, data):
        data['session'] = db_session
        return await handler(event, data)
    
    return dp
