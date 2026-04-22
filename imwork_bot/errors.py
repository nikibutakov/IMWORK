"""
Middleware для обработки ошибок и исключений в боте.
Ловит необработанные исключения, логирует их и отправляет уведомления админу.
"""

import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import Bot
from aiogram.types import ErrorEvent, Message, CallbackQuery
from aiogram.filters import ExceptionTypeFilter

from config import logger, ADMIN_ID


async def errors_handler(event: ErrorEvent, bot: Bot) -> None:
    """
    Глобальный обработчик ошибок для всех исключений.
    Логирует ошибку и уведомляет администратора.
    """
    exception = event.exception
    
    # Получаем информацию о событии, где произошла ошибка
    error_context = get_error_context(event)
    
    # Логируем ошибку с полным стек-трейсом
    logger.critical(
        f"❌ Критическая ошибка в боте:\n"
        f"Тип: {type(exception).__name__}\n"
        f"Сообщение: {str(exception)}\n"
        f"Контекст: {error_context}",
        exc_info=exception
    )
    
    # Уведомляем админа (если ADMIN_ID настроен)
    if ADMIN_ID:
        try:
            admin_message = (
                f"🚨 <b>Ошибка в боте!</b>\n\n"
                f"📋 <b>Информация:</b>\n"
                f"Тип: <code>{type(exception).__name__}</code>\n"
                f"Сообщение: <code>{escape_html(str(exception))}</code>\n\n"
                f"👤 <b>Пользователь:</b>\n"
                f"ID: <code>{error_context.get('user_id', 'N/A')}</code>\n"
                f"Username: @{error_context.get('username', 'N/A')}\n\n"
                f"💬 <b>Чат:</b>\n"
                f"ID: <code>{error_context.get('chat_id', 'N/A')}</code>\n\n"
                f"🔧 <b>Детали:</b>\n"
                f"Update ID: <code>{event.update.update_id}</code>"
            )
            
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_message,
                parse_mode="HTML"
            )
        except Exception as notify_error:
            logger.error(f"Не удалось отправить уведомление админу: {notify_error}")


def get_error_context(event: ErrorEvent) -> Dict[str, Any]:
    """
    Извлекает контекст из события ошибки (пользователь, чат, тип действия).
    """
    context = {
        "user_id": None,
        "username": None,
        "chat_id": None,
        "action_type": None,
        "data": None
    }
    
    # Проверяем тип события, где произошла ошибка
    if isinstance(event.event, Message):
        msg = event.event
        context["user_id"] = msg.from_user.id if msg.from_user else None
        context["username"] = msg.from_user.username if msg.from_user else None
        context["chat_id"] = msg.chat.id
        context["action_type"] = "message"
        context["data"] = msg.text or msg.caption
        
    elif isinstance(event.event, CallbackQuery):
        callback = event.event
        context["user_id"] = callback.from_user.id if callback.from_user else None
        context["username"] = callback.from_user.username if callback.from_user else None
        context["chat_id"] = callback.message.chat.id if callback.message else None
        context["action_type"] = "callback_query"
        context["data"] = callback.data
        
    return context


def escape_html(text: str) -> str:
    """
    Экранирует специальные HTML-символы для безопасного вывода в Telegram.
    """
    if not text:
        return ""
    
    replacements = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    return text[:1000]  # Ограничиваем длину сообщения


# Специализированные обработчики для конкретных типов ошибок
async def telegram_api_error_handler(event: ErrorEvent, bot: Bot) -> None:
    """Обработчик ошибок Telegram API"""
    exception = event.exception
    logger.warning(f"Telegram API ошибка: {exception}")
    
    # Пробуем ответить пользователю, если возможно
    if isinstance(event.event, Message):
        try:
            await event.event.answer(
                "⚠️ Произошла техническая ошибка. Пожалуйста, попробуйте позже."
            )
        except Exception:
            pass


async def validation_error_handler(event: ErrorEvent, bot: Bot) -> None:
    """Обработчик ошибок валидации данных"""
    exception = event.exception
    logger.warning(f"Ошибка валидации: {exception}")
    
    if isinstance(event.event, Message):
        try:
            await event.event.answer(
                "❌ Неверный формат данных. Пожалуйста, проверьте ввод и попробуйте снова."
            )
        except Exception:
            pass


async def database_error_handler(event: ErrorEvent, bot: Bot) -> None:
    """Обработчик ошибок базы данных"""
    exception = event.exception
    logger.error(f"Ошибка базы данных: {exception}", exc_info=True)
    
    if isinstance(event.event, Message):
        try:
            await event.event.answer(
                "🔴 Временные проблемы с базой данных. Попробуйте через минуту."
            )
        except Exception:
            pass
    
    # Уведомляем админа об ошибке БД
    if ADMIN_ID:
        try:
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔴 <b>Ошибка БД:</b> {escape_html(str(exception))}",
                parse_mode="HTML"
            )
        except Exception:
            pass
