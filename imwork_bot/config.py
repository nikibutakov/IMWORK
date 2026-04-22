import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка путей
BASE_DIR = Path(__file__).parent
DATABASE_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "imwork_bot.db")

# Конфигурация бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения. Проверьте .env файл.")

# Настройка логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)