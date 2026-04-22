"""Хендлеры для онбординга и главного меню"""

import re
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User
from states import OnboardingStudent, OnboardingEmployer
from keyboards.main_menu import (
    get_role_selection_keyboard,
    get_student_main_menu,
    get_employer_main_menu,
    get_back_to_menu_keyboard,
    get_course_selection_keyboard,
    get_specialization_keyboard,
    get_company_field_keyboard,
    get_contact_admin_keyboard,
)

router = Router()


# ==================== /start и выбор роли ====================

@router.message(Command("start"))
async def cmd_start(message: types.Message, session: AsyncSession):
    """Обработчик команды /start - начало онбординга или главное меню"""
    telegram_id = str(message.from_user.id)
    
    # Проверяем, есть ли пользователь в БД
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if user and user.role:
        # Пользователь уже прошел онбординг - показываем главное меню
        await show_main_menu(message, user)
    else:
        # Новый пользователь - предлагаем выбрать роль
        await message.answer(
            "👋 Добро пожаловать в ImWork Bot!\n\n"
            "Для начала выберите вашу роль:",
            reply_markup=get_role_selection_keyboard()
        )


@router.callback_query(F.data == "role_student")
async def role_student_selected(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """Выбрана роль студента - начинаем онбординг"""
    await state.set_state(OnboardingStudent.course)
    await callback.message.edit_text(
        "👨‍🎓 Отлично! Вы выбрали роль студента.\n\n"
        "На каком курсе вы учитесь?",
        reply_markup=get_course_selection_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "role_employer")
async def role_employer_selected(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """Выбрана роль работодателя - начинаем онбординг"""
    await state.set_state(OnboardingEmployer.company_name)
    await callback.message.edit_text(
        "🏢 Отлично! Вы выбрали роль работодателя.\n\n"
        "Введите название вашей компании:",
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()


# ==================== Онбординг студента ====================

@router.callback_query(OnboardingStudent.course, F.data.startswith("course_"))
async def student_course_selected(callback: types.CallbackQuery, state: FSMContext):
    """Студент выбрал курс"""
    course_data = callback.data.replace("course_", "")
    course_map = {
        "1": "1 курс",
        "2": "2 курс",
        "3": "3 курс",
        "4": "4 курс",
        "masters": "Магистратура"
    }
    course_name = course_map.get(course_data, course_data)
    
    await state.update_data(course=course_name)
    await state.set_state(OnboardingStudent.specialization)
    
    await callback.message.edit_text(
        f"✅ Курс: {course_name}\n\n"
        "Выберите вашу специализацию:",
        reply_markup=get_specialization_keyboard()
    )
    await callback.answer()


@router.callback_query(OnboardingStudent.specialization, F.data.startswith("spec_"))
async def student_spec_selected(callback: types.CallbackQuery, state: FSMContext):
    """Студент выбрал специализацию"""
    specialization = callback.data.replace("spec_", "")
    await state.update_data(specialization=specialization)
    await state.set_state(OnboardingStudent.preferences)
    
    await callback.message.edit_text(
        f"✅ Специализация: {specialization}\n\n"
        "Опишите ваши предпочтения по стажировке (тип работы, график, направление):\n"
        "(или нажмите 'Вернуться в меню', чтобы пропустить)",
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()


@router.message(OnboardingStudent.preferences)
async def student_preferences_received(message: types.Message, state: FSMContext, session: AsyncSession):
    """Получены предпочтения студента - завершаем онбординг"""
    if message.text == "↩️ Вернуться в меню":
        await state.clear()
        await message.answer("Онбординг прерван. Возврат в меню.", reply_markup=get_back_to_menu_keyboard())
        return
    
    preferences = message.text
    data = await state.get_data()
    
    # Сохраняем профиль студента в БД
    await save_student_profile(message, state, session, data, preferences)
    
    await state.clear()
    await message.answer(
        "✅ Профиль успешно создан!\n\n"
        "Теперь вы можете пользоваться всеми функциями бота.",
        reply_markup=get_student_main_menu()
    )


# ==================== Онбординг работодателя ====================

@router.message(OnboardingEmployer.company_name)
async def employer_company_name_received(message: types.Message, state: FSMContext):
    """Получено название компании"""
    if message.text == "↩️ Вернуться в меню":
        await state.clear()
        await message.answer("Онбординг прерван. Возврат в меню.", reply_markup=get_back_to_menu_keyboard())
        return
    
    company_name = message.text.strip()
    if not company_name:
        await message.answer("❌ Название компании не может быть пустым. Введите название:")
        return
    
    await state.update_data(company_name=company_name)
    await state.set_state(OnboardingEmployer.company_field)
    
    await message.answer(
        f"✅ Компания: {company_name}\n\n"
        "Выберите сферу деятельности вашей компании:",
        reply_markup=get_company_field_keyboard()
    )


@router.callback_query(OnboardingEmployer.company_field, F.data.startswith("field_"))
async def employer_company_field_selected(callback: types.CallbackQuery, state: FSMContext):
    """Работодатель выбрал сферу деятельности"""
    company_field = callback.data.replace("field_", "")
    await state.update_data(company_field=company_field)
    await state.set_state(OnboardingEmployer.verification_step)
    
    await callback.message.edit_text(
        f"✅ Сфера деятельности: {company_field}\n\n"
        "📋 Последний шаг: верификация компании.\n\n"
        "В MVP-версии верификация упрощена. Ваш аккаунт будет проверен администратором.\n"
        "Вы можете написать админу для ускорения процесса.",
        reply_markup=get_contact_admin_keyboard()
    )
    await callback.answer()


@router.callback_query(OnboardingEmployer.verification_step, F.data == "back_to_menu")
async def employer_verification_back(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """Работодатель вернулся в меню после верификации"""
    data = await state.get_data()
    
    # Сохраняем профиль работодателя (is_verified=False)
    await save_employer_profile(callback.message, state, session, data, is_verified=False)
    
    await state.clear()
    await callback.message.edit_text(
        "✅ Профиль компании создан!\n\n"
        "⚠️ Ваш аккаунт ожидает проверки администратором.\n"
        "Некоторые функции могут быть ограничены до верификации.",
        reply_markup=get_employer_main_menu()
    )
    await callback.answer()


# ==================== Сохранение профилей в БД ====================

async def save_student_profile(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
    data: dict,
    preferences: str
):
    """Сохранение профиля студента в БД"""
    telegram_id = str(message.from_user.id)
    
    # Проверяем, есть ли уже пользователь
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        # Обновляем существующего пользователя
        user.role = "student"
        user.course = data.get("course")
        user.direction = data.get("specialization")
    else:
        # Создаем нового пользователя
        user = User(
            telegram_id=telegram_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            role="student",
            course=data.get("course"),
            direction=data.get("specialization")
        )
        session.add(user)
    
    await session.commit()


async def save_employer_profile(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
    data: dict,
    is_verified: bool = False
):
    """Сохранение профиля работодателя в БД"""
    telegram_id = str(message.from_user.id)
    
    # Проверяем, есть ли уже пользователь
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        # Обновляем существующего пользователя
        user.role = "employer"
        # company_name и company_field можно сохранить в дополнительные поля при необходимости
    else:
        # Создаем нового пользователя
        user = User(
            telegram_id=telegram_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            role="employer"
        )
        session.add(user)
    
    await session.commit()


# ==================== Главное меню ====================

async def show_main_menu(message: types.Message, user: User):
    """Показывает главное меню в зависимости от роли пользователя"""
    if user.role == "student":
        await message.answer(
            "📱 Главное меню студента\n\n"
            "Выберите раздел:",
            reply_markup=get_student_main_menu()
        )
    elif user.role == "employer":
        verification_status = "" if True else "\n⚠️ Ваш аккаунт ожидает проверки."
        await message.answer(
            "📱 Главное меню работодателя\n\n"
            "Выберите раздел:" + verification_status,
            reply_markup=get_employer_main_menu()
        )
    else:
        await message.answer(
            "⚠️ Неизвестная роль. Обратитесь к администратору.",
            reply_markup=get_back_to_menu_keyboard()
        )


# ==================== Обработка кнопок главного меню ====================

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(callback: types.CallbackQuery, session: AsyncSession):
    """Возврат в главное меню из любого состояния"""
    telegram_id = str(callback.from_user.id)
    
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    await callback.state.clear()
    
    if user:
        await callback.message.edit_text(
            "📱 Главное меню",
            reply_markup=get_student_main_menu() if user.role == "student" else get_employer_main_menu()
        )
    else:
        await callback.message.edit_text(
            "👋 Добро пожаловать! Выберите вашу роль:",
            reply_markup=get_role_selection_keyboard()
        )
    
    await callback.answer()


@router.callback_query(F.data == "student_find_internship")
async def student_find_internship_handler(callback: types.CallbackQuery):
    """Поиск стажировки - заглушка"""
    await callback.message.answer("🔍 Раздел 'Найти стажировку' в разработке.")
    await callback.answer()


@router.callback_query(F.data == "student_career_center")
async def student_career_center_handler(callback: types.CallbackQuery):
    """Карьерный центр - заглушка"""
    await callback.message.answer("🎓 Раздел 'Карьерный центр' в разработке.")
    await callback.answer()


@router.callback_query(F.data == "student_forum")
async def student_forum_handler(callback: types.CallbackQuery):
    """Форум - заглушка"""
    await callback.message.answer("💬 Раздел 'Форум' в разработке.")
    await callback.answer()


@router.callback_query(F.data == "student_profile")
async def student_profile_handler(callback: types.CallbackQuery, session: AsyncSession):
    """Профиль студента"""
    telegram_id = str(callback.from_user.id)
    
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        profile_text = (
            "👤 Ваш профиль\n\n"
            f"Роль: Студент\n"
            f"Курс: {user.course or 'Не указан'}\n"
            f"Специализация: {user.direction or 'Не указана'}\n"
            f"Тариф: {user.tariff}"
        )
        await callback.message.answer(profile_text, reply_markup=get_back_to_menu_keyboard())
    else:
        await callback.message.answer("❌ Профиль не найден.")
    
    await callback.answer()


@router.callback_query(F.data == "employer_post_vacancy")
async def employer_post_vacancy_handler(callback: types.CallbackQuery):
    """Разместить вакансию - заглушка"""
    await callback.message.answer("➕ Раздел 'Разместить вакансию' в разработке.")
    await callback.answer()


@router.callback_query(F.data == "employer_my_vacancies")
async def employer_my_vacancies_handler(callback: types.CallbackQuery):
    """Мои вакансии - заглушка"""
    await callback.message.answer("📊 Раздел 'Мои вакансии' в разработке.")
    await callback.answer()


@router.callback_query(F.data == "employer_tariffs")
async def employer_tariffs_handler(callback: types.CallbackQuery):
    """Тарифы - заглушка"""
    await callback.message.answer("💳 Раздел 'Тарифы' в разработке.")
    await callback.answer()


@router.callback_query(F.data == "employer_settings")
async def employer_settings_handler(callback: types.CallbackQuery):
    """Настройки - заглушка"""
    await callback.message.answer("⚙️ Раздел 'Настройки' в разработке.")
    await callback.answer()


# ==================== Fallback для невалидного ввода ====================

@router.message(OnboardingStudent.course)
async def student_course_invalid(message: types.Message):
    """Невалидный ввод курса (если ввел текстом вместо кнопки)"""
    await message.answer(
        "❌ Пожалуйста, выберите курс из предложенных вариантов:",
        reply_markup=get_course_selection_keyboard()
    )


@router.message(OnboardingStudent.specialization)
async def student_spec_invalid(message: types.Message):
    """Невалидный ввод специализации"""
    await message.answer(
        "❌ Пожалуйста, выберите специализацию из предложенных вариантов:",
        reply_markup=get_specialization_keyboard()
    )


@router.message(OnboardingEmployer.company_field)
async def employer_field_invalid(message: types.Message):
    """Невалидный ввод сферы деятельности"""
    await message.answer(
        "❌ Пожалуйста, выберите сферу деятельности из предложенных вариантов:",
        reply_markup=get_company_field_keyboard()
    )
