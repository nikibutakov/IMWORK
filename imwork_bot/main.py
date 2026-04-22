"""
ImWork Bot - MVP Version
Main entry point for the Telegram bot.
Includes error handling, logging, admin panel, and all handlers.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram import types

from config import BOT_TOKEN, ADMIN_ID, logger
from database import init_db, async_session_maker
from errors import errors_handler, telegram_api_error_handler, database_error_handler
from handlers.onboarding import router as onboarding_router
from handlers.student_jobs import router as student_jobs_router
from handlers.career_center import router as career_center_router
from handlers.employer_jobs import router as employer_jobs_router
from handlers.moderation import router as moderation_router


def setup_dispatcher() -> Dispatcher:
    """
    Creates and configures the dispatcher with all routers and middleware.
    Returns configured Dispatcher instance.
    """
    # Создаем диспетчер и бот
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрируем все роутеры
    dp.include_router(onboarding_router)
    dp.include_router(student_jobs_router)
    dp.include_router(career_center_router)
    dp.include_router(employer_jobs_router)
    dp.include_router(moderation_router)
    
    # Middleware для передачи сессии БД во все хендлеры
    @dp.message.middleware()
    @dp.callback_query.middleware()
    async def db_session_middleware(handler, event, data):
        """Автоматически добавляет сессию БД в данные хендлера"""
        async with async_session_maker() as session:
            data['session'] = session
            return await handler(event, data)
    
    # Регистрируем глобальный обработчик ошибок
    dp.errors.register(errors_handler)
    
    # TODO V2: Добавить специализированные обработчики ошибок
    # dp.errors.register(telegram_api_error_handler, exception_filter=ExceptionTypeFilter(TelegramAPIError))
    # dp.errors.register(database_error_handler, exception_filter=ExceptionTypeFilter(SQLAlchemyError))
    
    logger.info("Dispatcher настроен и готов к работе")
    
    return dp


# Инициализируем диспетчер при импорте
dp = setup_dispatcher()

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

async def on_startup():
    """Функция, вызываемая при запуске бота"""
    logger.info("Бот запускается...")
    
    # Инициализация базы данных
    await init_db()
    
    # Информация о конфигурации
    logger.info(f"ADMIN_ID: {'настроен' if ADMIN_ID else 'не настроен'}")
    
    logger.info("Бот успешно запущен!")


async def on_shutdown():
    """Функция, вызываемая при остановке бота"""
    logger.info("Бот останавливается...")
    await bot.session.close()
    logger.info("Сессия бота закрыта")


# ==================== Админ-панель ====================

@dp.message(Command("admin_panel"))
async def cmd_admin_panel(message: types.Message):
    """
    Команда /admin_panel - доступ только для ADMIN_ID из .env
    Показывает панель управления с быстрым доступом к модерации и статистике.
    """
    user_id = str(message.from_user.id)
    
    # Проверяем права администратора
    if not ADMIN_ID or user_id != str(ADMIN_ID):
        logger.warning(f"Попытка доступа к /admin_panel от пользователя {user_id}")
        await message.answer(
            "❌ У вас нет прав доступа к админ-панели."
        )
        return
    
    logger.info(f"Админ-панель открыта пользователем {user_id}")
    
    # Формируем клавиатуру админ-панели
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="📋 Вакансии на модерации", callback_data="admin_mod_queue"),
            ],
            [
                types.InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
                types.InlineKeyboardButton(text="📊 Статистика бота", callback_data="admin_stats"),
            ],
            [
                types.InlineKeyboardButton(text="🔍 Поиск по ID", callback_data="admin_search"),
            ],
        ]
    )
    
    await message.answer(
        "🛠 <b>Админ-панель ImWork Bot</b>\n\n"
        "Выберите действие:\n\n"
        "<i>MVP версия: доступны базовые функции модерации и статистики.</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "admin_mod_queue")
async def admin_show_moderation_queue(callback: types.CallbackQuery, session):
    """Показ вакансий на модерации из админ-панели"""
    from sqlalchemy import select
    from models import Vacancy
    
    result = await session.execute(
        select(Vacancy)
        .where(Vacancy.status == "moderation")
        .order_by(Vacancy.created_at.asc())
    )
    vacancies = result.scalars().all()
    
    if not vacancies:
        await callback.answer("Нет вакансий на модерации", show_alert=True)
        return
    
    text = f"🟡 <b>Вакансии на модерации: {len(vacancies)}</b>\n\n"
    for v in vacancies[:10]:  # Показываем максимум 10
        text += f"• #{v.id} {v.title[:40]}...\n"
    
    if len(vacancies) > 10:
        text += f"\n... и ещё {len(vacancies) - 10}"
    
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data == "admin_stats")
async def admin_show_statistics(callback: types.CallbackQuery, session):
    """Показ общей статистики бота"""
    from sqlalchemy import func, select
    from models import User, Vacancy, Application
    
    # Считаем пользователей по ролям
    total_users = await session.execute(select(func.count()).select_from(User))
    total_users = total_users.scalar() or 0
    
    students = await session.execute(
        select(func.count()).select_from(User).where(User.role == "student")
    )
    students = students.scalar() or 0
    
    employers = await session.execute(
        select(func.count()).select_from(User).where(User.role == "employer")
    )
    employers = employers.scalar() or 0
    
    # Считаем вакансии по статусам
    total_vacancies = await session.execute(select(func.count()).select_from(Vacancy))
    total_vacancies = total_vacancies.scalar() or 0
    
    active_vacancies = await session.execute(
        select(func.count()).select_from(Vacancy).where(Vacancy.status == "active")
    )
    active_vacancies = active_vacancies.scalar() or 0
    
    moderation_queue = await session.execute(
        select(func.count()).select_from(Vacancy).where(Vacancy.status == "moderation")
    )
    moderation_queue = moderation_queue.scalar() or 0
    
    # Считаем отклики
    total_applications = await session.execute(select(func.count()).select_from(Application))
    total_applications = total_applications.scalar() or 0
    
    text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 <b>Пользователи:</b> {total_users}\n"
        f"  • Студенты: {students}\n"
        f"  • Работодатели: {employers}\n\n"
        f"📄 <b>Вакансии:</b> {total_vacancies}\n"
        f"  • Активные: {active_vacancies}\n"
        f"  • На модерации: {moderation_queue}\n\n"
        f"💼 <b>Отклики:</b> {total_applications}\n\n"
        "<i>Данные актуальны на момент запроса.</i>"
    )
    
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data == "admin_users")
async def admin_users_info(callback: types.CallbackQuery):
    """Информация о пользователях (заглушка для MVP)"""
    await callback.message.answer(
        "👥 <b>Управление пользователями</b>\n\n"
        "<i>В MVP версии доступно только через прямые SQL-запросы.</i>\n\n"
        "# TODO V2: Реализовать полный интерфейс управления пользователями\n"
        "• Поиск по Telegram ID\n"
        "• Просмотр профиля\n"
        "• Бан/разбан\n"
        "• Изменение роли",
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "admin_search")
async def admin_search_info(callback: types.CallbackQuery):
    """Поиск по ID (заглушка для MVP)"""
    await callback.message.answer(
        "🔍 <b>Поиск по ID</b>\n\n"
        "<i>В MVP версии используйте команду:</i>\n"
        "<code>/get_user &lt;telegram_id&gt;</code>\n\n"
        "# TODO V2: Реализовать интерактивный поиск",
        parse_mode="HTML"
    )
    await callback.answer()


async def main():
    """Основная функция запуска бота"""
    # Регистрируем хуки старта/остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Запуск процесса поллинга (получение обновлений от Telegram)
    logger.info("Запуск polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
    finally:
        # Закрываем сессию бота при завершении
        try:
            asyncio.run(bot.session.close())
        except Exception:
            pass