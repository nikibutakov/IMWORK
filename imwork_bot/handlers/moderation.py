"""Хендлеры для модерации вакансий: approve/reject, уведомления"""

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from models import User, Vacancy
from states import ModeratorActionState
from keyboards.employer_menu import get_moderation_decision_keyboard, get_back_to_employer_menu_keyboard

router = Router()

# ID админ-чата для уведомлений (заглушка)
ADMIN_CHAT_ID = None  # Заменить на реальный ID при настройке


# ==================== Команды модератора ====================

@router.message(F.text.startswith("/approve"))
async def approve_vacancy_command(message: types.Message, session: AsyncSession):
    """
    Команда модератора: /approve <vacancy_id>
    Одобряет вакансию и меняет статус на active
    """
    if not await check_moderator_access(message, session):
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Использование: /approve <vacancy_id>\nПример: /approve 123")
        return
    
    try:
        vacancy_id = int(parts[1])
    except ValueError:
        await message.answer("❌ Неверный ID вакансии. Используйте число.")
        return
    
    result = await session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        await message.answer(f"❌ Вакансия #{vacancy_id} не найдена.")
        return
    
    if vacancy.status == "active":
        await message.answer(f"⚠️ Вакансия #{vacancy_id} уже активна.")
        return
    
    # Одобряем вакансию
    vacancy.status = "active"
    vacancy.moderated_by = None  # Можно добавить поле moderator_id
    vacancy.moderated_at = datetime.utcnow()
    vacancy.moderation_comment = None
    
    await session.commit()
    
    await message.answer(
        f"✅ <b>Вакансия одобрена!</b>\n\n"
        f"📄 #{vacancy_id}: {vacancy.title}\n"
        f"🟢 Статус изменён на: active\n\n"
        f"Уведомление отправлено создателю.",
        parse_mode="HTML"
    )
    
    # Отправляем уведомление создателю
    await notify_creator_approved(session, vacancy)


@router.message(F.text.startswith("/reject"))
async def reject_vacancy_command(message: types.Message, session: AsyncSession, state: FSMContext):
    """
    Команда модератора: /reject <vacancy_id> [комментарий]
    Отклоняет вакансию с комментарием
    """
    if not await check_moderator_access(message, session):
        return
    
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        await message.answer("❌ Использование: /reject <vacancy_id> [комментарий]\nПример: /reject 123 Недостаточно информации")
        return
    
    try:
        vacancy_id = int(parts[1])
    except ValueError:
        await message.answer("❌ Неверный ID вакансии. Используйте число.")
        return
    
    result = await session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        await message.answer(f"❌ Вакансия #{vacancy_id} не найдена.")
        return
    
    if vacancy.status == "rejected":
        await message.answer(f"⚠️ Вакансия #{vacancy_id} уже отклонена.")
        return
    
    # Получаем комментарий
    comment = parts[2] if len(parts) > 2 else "Без комментария"
    
    # Отклоняем вакансию
    vacancy.status = "rejected"
    vacancy.moderated_at = datetime.utcnow()
    vacancy.moderation_comment = comment
    
    await session.commit()
    
    await message.answer(
        f"❌ <b>Вакансия отклонена!</b>\n\n"
        f"📄 #{vacancy_id}: {vacancy.title}\n"
        f"🔴 Статус изменён на: rejected\n"
        f"💬 Комментарий: {comment}\n\n"
        f"Уведомление отправлено создателю.",
        parse_mode="HTML"
    )
    
    # Отправляем уведомление создателю
    await notify_creator_rejected(session, vacancy, comment)


@router.callback_query(F.data.startswith("mod_approve_"))
async def mod_approve_callback(callback: types.CallbackQuery, session: AsyncSession):
    """Callback для одобрения вакансии из интерфейса модератора"""
    vacancy_id = int(callback.data.replace("mod_approve_", ""))
    
    result = await session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        await callback.answer("❌ Вакансия не найдена", show_alert=True)
        return
    
    vacancy.status = "active"
    vacancy.moderated_at = datetime.utcnow()
    vacancy.moderation_comment = None
    
    await session.commit()
    
    await callback.answer("✅ Вакансия одобрена!", show_alert=True)
    
    # Уведомляем создателя
    await notify_creator_approved(session, vacancy)
    
    # Обновляем сообщение
    await callback.message.edit_text(
        f"✅ <b>Вакансия одобрена</b>\n\n"
        f"#{vacancy_id}: {vacancy.title}\n"
        f"Статус: active",
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("mod_reject_"))
async def mod_reject_callback(callback: types.CallbackQuery, state: FSMContext):
    """Callback для отклонения вакансии - запрос комментария"""
    vacancy_id = int(callback.data.replace("mod_reject_", ""))
    
    # Сохраняем ID вакансии в состоянии
    await state.update_data(reject_vacancy_id=vacancy_id)
    
    await callback.message.edit_text(
        "❌ <b>Отклонение вакансии</b>\n\n"
        "Введите причину отклонения:\n\n"
        "<i>Или нажмите «Отмена»</i>",
        parse_mode="HTML"
    )
    await state.set_state(ModeratorActionState.reject_comment)
    await callback.answer()


@router.message(ModeratorActionState.reject_comment)
async def process_reject_comment(message: types.Message, state: FSMContext, session: AsyncSession):
    """Обработка комментария при отклонении"""
    data = await state.get_data()
    vacancy_id = data.get("reject_vacancy_id")
    
    if not vacancy_id:
        await message.answer("❌ Ошибка: ID вакансии не найден. Начните сначала.")
        await state.clear()
        return
    
    comment = message.text.strip()
    
    result = await session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        await message.answer("❌ Вакансия не найдена.")
        await state.clear()
        return
    
    vacancy.status = "rejected"
    vacancy.moderated_at = datetime.utcnow()
    vacancy.moderation_comment = comment
    
    await session.commit()
    await state.clear()
    
    await message.answer(
        f"❌ <b>Вакансия отклонена</b>\n\n"
        f"#{vacancy_id}: {vacancy.title}\n"
        f"Причина: {comment}",
        parse_mode="HTML"
    )
    
    # Уведомляем создателя
    await notify_creator_rejected(session, vacancy, comment)


# ==================== Уведомления создателям ====================

async def notify_creator_approved(session: AsyncSession, vacancy: Vacancy):
    """Отправка уведомления создателю об одобрении вакансии"""
    # Получаем пользователя-создателя
    user_result = await session.execute(
        select(User).where(User.id == vacancy.author_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        return
    
    try:
        await router.bot.send_message(
            chat_id=user.telegram_id,
            text=(
                f"🎉 <b>Вакансия одобрена!</b>\n\n"
                f"Ваша вакансия прошла модерацию и теперь активна.\n\n"
                f"📄 <b>{vacancy.title}</b>\n"
                f"🆔 ID: #{vacancy.id}\n"
                f"🟢 Статус: active\n\n"
                f"Теперь студенты могут видеть её в поиске и откликаться!"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Не удалось отправить уведомление пользователю {user.telegram_id}: {e}")


async def notify_creator_rejected(session: AsyncSession, vacancy: Vacancy, comment: str):
    """Отправка уведомления создателю об отклонении вакансии"""
    user_result = await session.execute(
        select(User).where(User.id == vacancy.author_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        return
    
    try:
        await router.bot.send_message(
            chat_id=user.telegram_id,
            text=(
                f"❌ <b>Вакансия отклонена</b>\n\n"
                f"К сожалению, ваша вакансия не прошла модерацию.\n\n"
                f"📄 <b>{vacancy.title}</b>\n"
                f"🆔 ID: #{vacancy.id}\n"
                f"🔴 Статус: rejected\n\n"
                f"💬 <b>Комментарий модератора:</b>\n"
                f"{comment}\n\n"
                f"Вы можете исправить замечания и создать вакансию снова."
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Не удалось отправить уведомление пользователю {user.telegram_id}: {e}")


# ==================== Проверка прав модератора ====================

async def check_moderator_access(message: types.Message, session: AsyncSession) -> bool:
    """Проверка, является ли пользователь модератором или админом"""
    telegram_id = str(message.from_user.id)
    
    user_result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        await message.answer("❌ Пользователь не найден в системе.")
        return False
    
    if user.role not in ["moderator", "admin"]:
        await message.answer("❌ У вас нет прав модератора.")
        return False
    
    return True


# ==================== Список вакансий на модерации ====================

@router.message(F.text == "/moderation_queue")
async def show_moderation_queue(message: types.Message, session: AsyncSession):
    """Показ списка вакансий, ожидающих модерации"""
    if not await check_moderator_access(message, session):
        return
    
    result = await session.execute(
        select(Vacancy)
        .where(Vacancy.status == "moderation")
        .order_by(Vacancy.created_at.asc())
    )
    vacancies = result.scalars().all()
    
    if not vacancies:
        await message.answer("📭 Нет вакансий, ожидающих модерации.")
        return
    
    text = f"🟡 <b>Вакансии на модерации: {len(vacancies)}</b>\n\n"
    
    for v in vacancies:
        text += (
            f"📄 <b>#{v.id} {v.title}</b>\n"
            f"Автор: ID {v.author_id}\n"
            f"Категория: {v.category or 'Не указана'}\n"
            f"Создана: {v.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"/approve {v.id} | /reject {v.id} [причина]\n\n"
        )
    
    await message.answer(text, parse_mode="HTML")
