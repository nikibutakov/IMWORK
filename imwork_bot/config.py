import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler

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

# ID администратора для доступа к админ-панели
ADMIN_ID = os.getenv("ADMIN_ID")
if not ADMIN_ID:
    # В MVP допускаем отсутствие, но логируем предупреждение
    print("⚠️ WARNING: ADMIN_ID не найден в .env. Команда /admin_panel будет недоступна.")
    ADMIN_ID = None

# Настройка логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = BASE_DIR / os.getenv("LOG_FILE", "logs/bot.log")
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 10 * 1024 * 1024))  # 10 MB по умолчанию
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))  # 5 файлов по умолчанию

# Создаем директорию для логов
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Настраиваем root logger
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# Форматтер
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
console_handler.setFormatter(formatter)

# File handler с ротацией
file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=LOG_MAX_BYTES,
    backupCount=LOG_BACKUP_COUNT,
    encoding="utf-8"
)
file_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
file_handler.setFormatter(formatter)

# Добавляем обработчики
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Предотвращаем дублирование логов от дочерних логгеров
logging.getLogger("aiogram").setLevel(logging.WARNING)