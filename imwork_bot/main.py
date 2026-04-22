import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, logger
from database import init_db


# Создаем диспетчер и бота
dp = Dispatcher()
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)


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
        if bot.session.closed is False:
            asyncio.run(bot.session.close())