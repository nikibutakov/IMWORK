--- imwork_bot/README.md (原始)


+++ imwork_bot/README.md (修改后)
# Инструкция по установке и запуску Telegram-бота «ИМВОРК»

## Структура проекта

```
imwork_bot/
├── __init__.py          # Инициализация пакета
├── config.py            # Конфигурация и переменные окружения
├── database.py          # Настройка БД и сессий SQLAlchemy
├── models.py            # Модели таблиц (users, vacancies, applications, career_materials)
├── main.py              # Точка входа, запуск бота
├── requirements.txt     # Зависимости Python
├── .env.example         # Шаблон файла с переменными окружения
└── README.md            # Эта инструкция
```

## Требования

- Python 3.10 или выше
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))

## Установка

### 1. Создайте виртуальное окружение (рекомендуется)

```bash
cd imwork_bot
python -m venv venv
```

Активируйте виртуальное окружение:

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 2. Установите зависимости

```bash
pip install -r requirements.txt
```

### 3. Настройте переменные окружения

Скопируйте файл `.env.example` в `.env`:

```bash
cp .env.example .env
```

Откройте `.env` и заполните необходимые значения:

```env
BOT_TOKEN=your_actual_bot_token_here
DATABASE_PATH=imwork_bot.db
LOG_LEVEL=INFO
```

**Важно:** Замените `your_actual_bot_token_here` на реальный токен вашего бота.

## Запуск бота

После настройки запустите бота:

```bash
python main.py
```

При успешном запуске вы увидите в логах:
```
YYYY-MM-DD HH:MM:SS - imwork_bot.config - INFO - База данных успешно инициализирована
YYYY-MM-DD HH:MM:SS - __main__ - INFO - Бот запускается...
YYYY-MM-DD HH:MM:SS - __main__ - INFO - Бот успешно запущен!
YYYY-MM-DD HH:MM:SS - __main__ - INFO - Запуск polling...
```

## Остановка бота

Нажмите `Ctrl+C` в терминале для остановки бота.

## Что дальше?

Сейчас бот запущен, но не обрабатывает сообщения. Следующие шаги:

1. Создать хендлеры для обработки команд и сообщений
2. Добавить клавиатуры и inline-кнопки
3. Реализовать сценарии взаимодействия с пользователем
4. Настроить FSM (Finite State Machine) для диалогов

## Примечания

- База данных SQLite будет создана автоматически в файле `imwork_bot.db` при первом запуске
- Логирование настроено на вывод в консоль с уровнем, указанным в `.env`
- Для продакшена рекомендуется использовать PostgreSQL вместо SQLite