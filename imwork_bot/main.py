import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, logger
from database import init_db, async_session_maker
from handlers.onboarding import router as onboarding_router
from handlers.student_jobs import router as student_jobs_router
from handlers.career_center import router as career_center_router


# Создаем диспетчер и бот
dp = Dispatcher(storage=MemoryStorage())
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

# Регистрируем роутеры
dp.include_router(onboarding_router)
dp.include_router(student_jobs_router)
dp.include_router(career_center_router)

# Middleware для передачи сессии БД во все хендлеры
@dp.message.middleware()
@dp.callback_query.middleware()
async def db_session_middleware(handler, event, data):
    """Автоматически добавляет сессию БД в данные хендлера"""
    async with async_session_maker() as session:
        data['session'] = session
        return await handler(event, data)

# Добавляем middleware также на уровень роутера для гарантии
onboarding_router.message.middleware(db_session_middleware)
onboarding_router.callback_query.middleware(db_session_middleware)
student_jobs_router.message.middleware(db_session_middleware)
student_jobs_router.callback_query.middleware(db_session_middleware)
career_center_router.message.middleware(db_session_middleware)
career_center_router.callback_query.middleware(db_session_middleware)

async def on_startup():
    """Функция, вызываемая при запуске бота"""
    logger.info("Бот запускается...")

    # Инициализация базы данных
    await init_db()

    logger.info("Бот успешно запущен!")


async def on_shutdown():
    """Функция, вызываемая при остановке бота"""
    logger.info("Бот останавливается...")
    await bot.session.close()
    logger.info("Сессия бота закрыта")


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
        if bot.session.close is False:
            asyncio.run(bot.session.close())