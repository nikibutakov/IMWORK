"""Хендлеры для Карьерного центра - образовательные материалы"""

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, CareerMaterial
from keyboards.job_search import (
    get_career_center_categories_keyboard,
    get_material_list_keyboard,
    get_material_detail_keyboard,
)
from keyboards.main_menu import get_back_to_menu_keyboard

router = Router()

# Хардкод категорий карьерного центра
CAREER_CATEGORIES = {
    "cat_resume": {
        "name": "📝 Резюме и сопроводительные",
        "description": "Материалы по созданию эффективного резюме и сопроводительных писем"
    },
    "cat_interviews": {
        "name": "🎤 Собеседования",
        "description": "Советы и рекомендации по прохождению собеседований"
    },
    "cat_growth": {
        "name": "📈 Карьерный рост",
        "description": "Материалы о построении карьеры и профессиональном развитии"
    },
    "cat_job_search": {
        "name": "💼 Поиск работы",
        "description": "Стратегии и инструменты для успешного поиска работы"
    }
}


# ==================== Главный экран Карьерного центра ====================

@router.callback_query(F.data == "student_career_center")
async def career_center_start(callback: types.CallbackQuery):
    """Главный экран Карьерного центра"""
    await callback.message.edit_text(
        "🎓 <b>Карьерный центр</b>\n\n"
        "Добро пожаловать в Карьерный центр! Здесь вы найдете полезные материалы "
        "для построения успешной карьеры.\n\n"
        "Выберите категорию:",
        reply_markup=get_career_center_categories_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== Выбор категории ====================

@router.callback_query(F.data.startswith("cat_"))
async def category_selected(callback: types.CallbackQuery, session: AsyncSession):
    """Пользователь выбрал категорию материалов"""
    category_callback = callback.data
    
    if category_callback not in CAREER_CATEGORIES:
        await callback.answer("❌ Категория не найдена", show_alert=True)
        return
    
    category_info = CAREER_CATEGORIES[category_callback]
    
    # Получаем материалы для этой категории из БД
    result = await session.execute(
        select(CareerMaterial).where(
            CareerMaterial.category == category_callback,
            CareerMaterial.is_published == True
        ).order_by(CareerMaterial.created_at.desc())
    )
    materials = result.scalars().all()
    
    if not materials:
        # Если материалов нет, показываем заглушку
        await callback.message.edit_text(
            f"{category_info['name']}\n\n"
            f"{category_info['description']}\n\n"
            "⚠️ В этой категории пока нет материалов.\n"
            "Загляните позже!",
            reply_markup=get_career_center_categories_keyboard(),
            parse_mode="HTML"
        )
    else:
        # Формируем список материалов
        materials_list = [(m.id, m.title) for m in materials]
        
        await callback.message.edit_text(
            f"{category_info['name']}\n\n"
            f"{category_info['description']}\n\n"
            f"📚 Найдено материалов: {len(materials)}\n\n"
            "Выберите материал:",
            reply_markup=get_material_list_keyboard(materials_list, category_callback),
            parse_mode="HTML"
        )
    
    await callback.answer()


# ==================== Просмотр материала ====================

@router.callback_query(F.data.startswith("material_") & ~F.data.startswith("material_download") & ~F.data.startswith("material_save") & ~F.data.startswith("material_question"))
async def material_detail(callback: types.CallbackQuery, session: AsyncSession):
    """Просмотр детальной информации о материале"""
    material_id = int(callback.data.replace("material_", ""))
    
    result = await session.execute(
        select(CareerMaterial).where(CareerMaterial.id == material_id)
    )
    material = result.scalar_one_or_none()
    
    if not material:
        await callback.answer("❌ Материал не найден", show_alert=True)
        return
    
    # Увеличиваем счетчик просмотров
    material.views_count += 1
    await session.commit()
    
    # Определяем callback для возврата к категории
    category_callback = material.category or "cat_resume"
    
    # Формируем текст материала
    text = (
        f"📄 <b>{material.title}</b>\n\n"
    )
    
    if material.description:
        text += f"📝 <b>Описание:</b>\n{material.description}\n\n"
    
    if material.content:
        text += f"📖 <b>Содержание:</b>\n{material.content}\n\n"
    
    text += f"👁️ Просмотров: {material.views_count}"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_material_detail_keyboard(material_id, category_callback),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== Действия с материалом ====================

@router.callback_query(F.data.startswith("material_download_"))
async def download_material(callback: types.CallbackQuery, session: AsyncSession):
    """Скачивание материала (MVP - эмуляция)"""
    material_id = int(callback.data.replace("material_download_", ""))
    
    result = await session.execute(
        select(CareerMaterial).where(CareerMaterial.id == material_id)
    )
    material = result.scalar_one_or_none()
    
    if not material:
        await callback.answer("❌ Материал не найден", show_alert=True)
        return
    
    # MVP: эмуляция скачивания
    if material.material_type == "video":
        download_text = "🎥 Ссылка на видео будет отправлена отдельно"
    elif material.material_type == "guide":
        download_text = "📚 Гайд доступен для скачивания"
    else:
        download_text = "📄 Материал готов к скачиванию"
    
    await callback.message.answer(
        f"📥 <b>Скачивание материала</b>\n\n"
        f"{material.title}\n\n"
        f"{download_text}\n\n"
        f"В MVP-версии файл не загружается реально. "
        f"В полной версии здесь будет отправка файла пользователю.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("material_save_"))
async def save_material(callback: types.CallbackQuery, session: AsyncSession):
    """Сохранение материала (MVP - эмуляция)"""
    material_id = int(callback.data.replace("material_save_", ""))
    
    result = await session.execute(
        select(CareerMaterial).where(CareerMaterial.id == material_id)
    )
    material = result.scalar_one_or_none()
    
    if not material:
        await callback.answer("❌ Материал не найден", show_alert=True)
        return
    
    # MVP: просто уведомление
    await callback.answer(f"💾 '{material.title}' сохранен в избранное!", show_alert=True)
    
    # В полной версии здесь было бы сохранение в таблицу saved_materials


@router.callback_query(F.data.startswith("material_question_"))
async def ask_question_about_material(callback: types.CallbackQuery, state: FSMContext):
    """Задать вопрос куратору о материале"""
    material_id = int(callback.data.replace("material_question_", ""))
    
    await state.set_state("waiting_question")
    await state.update_data(question_material_id=material_id)
    
    await callback.message.answer(
        "❓ <b>Задать вопрос куратору</b>\n\n"
        "Напишите ваш вопрос по материалу. Куратор ответит вам в ближайшее время.\n\n"
        "Для отмены нажмите /cancel",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(F.text and F.text != "/cancel")
async def receive_question(message: types.Message, state: FSMContext):
    """Получение вопроса от пользователя"""
    current_state = await state.get_state()
    
    if current_state != "waiting_question":
        return
    
    data = await state.get_data()
    material_id = data.get("question_material_id")
    
    # Заглушка: отправка в админ-чат
    # В реальности здесь был бы bot.send_message(admin_chat_id, ...)
    # question_text = f"Вопрос от @{message.from_user.username}:\n{message.text}\n\nМатериал ID: {material_id}"
    
    await state.clear()
    
    await message.answer(
        "✅ <b>Вопрос отправлен!</b>\n\n"
        "Ваш вопрос передан куратору. Ответ придет в личные сообщения.\n\n"
        "Обычно кураторы отвечают в течение 24 часов.",
        reply_markup=get_back_to_menu_keyboard(),
        parse_mode="HTML"
    )


# ==================== Отмена ====================

@router.message(F.text == "/cancel")
async def cancel_question(message: types.Message, state: FSMContext):
    """Отмена вопроса куратору"""
    current_state = await state.get_state()
    if current_state == "waiting_question":
        await state.clear()
        await message.answer(
            "❌ Вопрос отменен.",
            reply_markup=get_back_to_menu_keyboard()
        )
