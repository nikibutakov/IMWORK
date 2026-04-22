"""
Тесты для сценария онбординга пользователей.

TEST: Сценарий 1 из ТЗ - Онбординг
- /start → приветствие → выбор роли → курс/направление/предпочтения → 
  сохранение в users → показ правильного главного меню (студент/работодатель)

Запуск: pytest tests/test_onboarding.py -v
"""

import pytest
from sqlalchemy import select, func
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import State

from models import User
from states import OnboardingStudent, OnboardingEmployer


# ==================== Тесты команды /start ====================

@pytest.mark.asyncio
@pytest.mark.onboarding
async def test_start_new_user_shows_role_selection(
    dp_with_handlers, mock_message, db_session, bot_checker, mock_bot
):
    """
    TEST: /start для нового пользователя показывает выбор роли.
    
    Сценарий:
    1. Пользователь отправляет /start
    2. Бот проверяет БД - пользователя нет
    3. Бот показывает приветствие и кнопки выбора роли
    """
    # Проверяем что пользователь действительно отсутствует
    result = await db_session.execute(
        select(User).where(User.telegram_id == str(mock_message.from_user.id))
    )
    assert result.scalar_one_or_none() is None
    
    # Вызываем хендлер напрямую
    from handlers.onboarding import cmd_start
    await cmd_start(mock_message, db_session)
    
    # Проверяем ответ бота
    bot_checker.assert_send_message_called("Добро пожаловать в ImWork Bot")
    bot_checker.assert_send_message_called("выберите вашу роль")
    
    # Проверяем что была отправлена клавиатура с выбором роли
    call_args = mock_bot.send_message.call_args
    reply_markup = call_args.kwargs.get('reply_markup')
    assert reply_markup is not None
    
    # Проверяем наличие кнопок ролей
    keyboard_buttons = [btn.text for row in reply_markup.inline_keyboard for btn in row]
    assert "👨‍🎓 Я студент" in keyboard_buttons
    assert "🏢 Я работодатель" in keyboard_buttons


@pytest.mark.asyncio
@pytest.mark.onboarding
async def test_start_existing_student_shows_student_menu(
    dp_with_handlers, mock_message, db_session, bot_checker, mock_bot
):
    """
    TEST: /start для существующего студента показывает меню студента.
    
    Сценарий:
    1. Создаем пользователя с ролью student в БД
    2. Пользователь отправляет /start
    3. Бот показывает главное меню студента
    """
    # Создаем тестового пользователя-студента
    user = User(
        telegram_id=str(mock_message.from_user.id),
        username="test_user",
        first_name="Test",
        role="student",
        course="3 курс",
        direction="Программирование"
    )
    db_session.add(user)
    await db_session.commit()
    
    # Вызываем хендлер
    from handlers.onboarding import cmd_start
    await cmd_start(mock_message, db_session)
    
    # Проверяем ответ - должно быть меню студента
    bot_checker.assert_send_message_called("Главное меню студента")
    
    # Проверяем клавиатуру студента
    call_args = mock_bot.send_message.call_args
    reply_markup = call_args.kwargs.get('reply_markup')
    keyboard_buttons = [btn.text for row in reply_markup.inline_keyboard for btn in row]
    
    assert "🔍 Найти стажировку" in keyboard_buttons
    assert "🎓 Карьерный центр" in keyboard_buttons


@pytest.mark.asyncio
@pytest.mark.onboarding
async def test_start_existing_employer_shows_employer_menu(
    dp_with_handlers, mock_message, db_session, bot_checker, mock_bot
):
    """
    TEST: /start для существующего работодателя показывает меню работодателя.
    """
    # Создаем тестового пользователя-работодателя
    user = User(
        telegram_id=str(mock_message.from_user.id),
        username="employer_user",
        first_name="Employer",
        role="employer"
    )
    db_session.add(user)
    await db_session.commit()
    
    # Вызываем хендлер
    from handlers.onboarding import cmd_start
    await cmd_start(mock_message, db_session)
    
    # Проверяем ответ - должно быть меню работодателя
    bot_checker.assert_send_message_called("Главное меню работодателя")
    
    # Проверяем клавиатуру работодателя
    call_args = mock_bot.send_message.call_args
    reply_markup = call_args.kwargs.get('reply_markup')
    keyboard_buttons = [btn.text for row in reply_markup.inline_keyboard for btn in row]
    
    assert "➕ Разместить вакансию" in keyboard_buttons
    assert "📊 Мои вакансии" in keyboard_buttons


# ==================== Тесты выбора роли студента ====================

@pytest.mark.asyncio
@pytest.mark.onboarding
async def test_role_student_selected_starts_onboarding(
    dp_with_handlers, mock_callback_query, db_session, bot_checker, mock_bot, state_storage
):
    """
    TEST: Выбор роли студента запускает онбординг с выбора курса.
    
    Сценарий:
    1. Пользователь нажимает "👨‍🎓 Я студент"
    2. Бот устанавливает состояние OnboardingStudent.course
    3. Бот показывает выбор курса
    """
    from handlers.onboarding import role_student_selected
    from aiogram.fsm.context import FSMContext
    
    state = FSMContext(storage=state_storage, key=(mock_callback_query.from_user.id,))
    
    # Вызываем хендлер
    await role_student_selected(mock_callback_query, state, db_session)
    
    # Проверяем изменение текста сообщения
    bot_checker.assert_edit_message_text_called("Вы выбрали роль студента")
    bot_checker.assert_edit_message_text_called("На каком курсе вы учитесь?")
    
    # Проверяем клавиатуру с курсами
    call_args = mock_bot.edit_message_text.call_args
    reply_markup = call_args.kwargs.get('reply_markup')
    keyboard_buttons = [btn.text for row in reply_markup.inline_keyboard for btn in row]
    
    assert "1 курс" in keyboard_buttons
    assert "2 курс" in keyboard_buttons
    assert "3 курс" in keyboard_buttons
    assert "4 курс" in keyboard_buttons
    assert "Магистратура" in keyboard_buttons
    
    # Проверяем состояние FSM
    current_state = await state.get_state()
    assert current_state == OnboardingStudent.course.__fsm_value__


# ==================== Тесты выбора курса ====================

@pytest.mark.asyncio
@pytest.mark.onboarding
@pytest.mark.parametrize("course_data,course_name", [
    ("course_1", "1 курс"),
    ("course_2", "2 курс"),
    ("course_3", "3 курс"),
    ("course_4", "4 курс"),
    ("course_masters", "Магистратура"),
])
async def test_student_course_selected(
    dp_with_handlers, mock_callback_query, db_session, bot_checker, 
    mock_bot, state_storage, course_data, course_name
):
    """
    TEST: Студент выбирает курс - переход к выбору специализации.
    """
    from handlers.onboarding import student_course_selected
    from aiogram.fsm.context import FSMContext
    
    # Устанавливаем callback_data
    mock_callback_query.data = course_data
    
    state = FSMContext(storage=state_storage, key=(mock_callback_query.from_user.id,))
    
    # Вызываем хендлер
    await student_course_selected(mock_callback_query, state, db_session)
    
    # Проверяем ответ
    bot_checker.assert_edit_message_text_called(f"Курс: {course_name}")
    bot_checker.assert_edit_message_text_called("Выберите вашу специализацию")
    
    # Проверяем клавиатуру специализаций
    call_args = mock_bot.edit_message_text.call_args
    reply_markup = call_args.kwargs.get('reply_markup')
    keyboard_buttons = [btn.text for row in reply_markup.inline_keyboard for btn in row]
    
    assert "Программирование" in keyboard_buttons
    assert "Дизайн" in keyboard_buttons
    assert "Маркетинг" in keyboard_buttons
    
    # Проверяем состояние
    current_state = await state.get_state()
    assert current_state == OnboardingStudent.specialization.__fsm_value__
    
    # Проверяем сохранение данных в FSM
    data = await state.get_data()
    assert data.get("course") == course_name


# ==================== Тесты выбора специализации ====================

@pytest.mark.asyncio
@pytest.mark.onboarding
async def test_student_spec_selected(
    dp_with_handlers, mock_callback_query, db_session, bot_checker,
    mock_bot, state_storage
):
    """
    TEST: Студент выбирает специализацию - переход к предпочтениям.
    """
    from handlers.onboarding import student_spec_selected
    from aiogram.fsm.context import FSMContext
    
    mock_callback_query.data = "spec_Программирование"
    
    # Предварительно сохраняем курс
    state = FSMContext(storage=state_storage, key=(mock_callback_query.from_user.id,))
    await state.update_data(course="3 курс")
    await state.set_state(OnboardingStudent.specialization)
    
    # Вызываем хендлер
    await student_spec_selected(mock_callback_query, state, db_session)
    
    # Проверяем ответ
    bot_checker.assert_edit_message_text_called("Специализация: Программирование")
    bot_checker.assert_edit_message_text_called("Опишите ваши предпочтения по стажировке")
    
    # Проверяем состояние
    current_state = await state.get_state()
    assert current_state == OnboardingStudent.preferences.__fsm_value__


# ==================== Тесты завершения онбординга студента ====================

@pytest.mark.asyncio
@pytest.mark.onboarding
async def test_student_preferences_received_saves_profile(
    dp_with_handlers, mock_message, db_session, bot_checker, mock_bot, state_storage
):
    """
    TEST: Ввод предпочтений завершает онбординг и сохраняет профиль в БД.
    
    Сценарий:
    1. Студент вводит текст с предпочтениями
    2. Бот сохраняет профиль в таблицу users
    3. Бот показывает главное меню студента
    """
    from handlers.onboarding import student_preferences_received
    from aiogram.fsm.context import FSMContext
    
    # Настраиваем сообщение с предпочтениями
    mock_message.text = "Ищу стажировку по Python, удаленно, частичная занятость"
    
    state = FSMContext(storage=state_storage, key=(mock_message.from_user.id,))
    await state.update_data(
        course="3 курс",
        specialization="Программирование"
    )
    await state.set_state(OnboardingStudent.preferences)
    
    # Вызываем хендлер
    await student_preferences_received(mock_message, state, db_session)
    
    # Проверяем что профиль сохранен в БД
    result = await db_session.execute(
        select(User).where(User.telegram_id == str(mock_message.from_user.id))
    )
    user = result.scalar_one_or_none()
    
    assert user is not None
    assert user.role == "student"
    assert user.course == "3 курс"
    assert user.direction == "Программирование"
    
    # Проверяем ответ бота
    bot_checker.assert_send_message_called("Профиль успешно создан")
    
    # Проверяем главное меню студента
    call_args = mock_bot.send_message.call_args
    reply_markup = call_args.kwargs.get('reply_markup')
    keyboard_buttons = [btn.text for row in reply_markup.inline_keyboard for btn in row]
    assert "🔍 Найти стажировку" in keyboard_buttons
    
    # Проверяем что состояние сброшено
    current_state = await state.get_state()
    assert current_state is None


@pytest.mark.asyncio
@pytest.mark.onboarding
async def test_student_onboarding_cancel(
    dp_with_handlers, mock_message, db_session, bot_checker, mock_bot, state_storage
):
    """
    TEST: Отмена онбординга кнопкой "Вернуться в меню".
    """
    from handlers.onboarding import student_preferences_received
    from aiogram.fsm.context import FSMContext
    
    mock_message.text = "↩️ Вернуться в меню"
    
    state = FSMContext(storage=state_storage, key=(mock_message.from_user.id,))
    await state.set_state(OnboardingStudent.preferences)
    
    # Вызываем хендлер
    await student_preferences_received(mock_message, state, db_session)
    
    # Проверяем что профиль НЕ сохранен
    result = await db_session.execute(
        select(func.count()).select_from(User).where(
            User.telegram_id == str(mock_message.from_user.id)
        )
    )
    count = result.scalar() or 0
    assert count == 0
    
    # Проверяем ответ
    bot_checker.assert_send_message_called("Онбординг прерван")


# ==================== Тесты онбординга работодателя ====================

@pytest.mark.asyncio
@pytest.mark.onboarding
async def test_role_employer_selected_starts_onboarding(
    dp_with_handlers, mock_callback_query, db_session, bot_checker, mock_bot, state_storage
):
    """
    TEST: Выбор роли работодателя запускает онбординг с ввода названия компании.
    """
    from handlers.onboarding import role_employer_selected
    from aiogram.fsm.context import FSMContext
    
    state = FSMContext(storage=state_storage, key=(mock_callback_query.from_user.id,))
    
    await role_employer_selected(mock_callback_query, state, db_session)
    
    # Проверяем ответ
    bot_checker.assert_edit_message_text_called("Вы выбрали роль работодателя")
    bot_checker.assert_edit_message_text_called("Введите название вашей компании")
    
    # Проверяем состояние
    current_state = await state.get_state()
    assert current_state == OnboardingEmployer.company_name.__fsm_value__


@pytest.mark.asyncio
@pytest.mark.onboarding
async def test_employer_company_name_received(
    dp_with_handlers, mock_message, db_session, bot_checker, mock_bot, state_storage
):
    """
    TEST: Работодатель вводит название компании - переход к выбору сферы.
    """
    from handlers.onboarding import employer_company_name_received
    from aiogram.fsm.context import FSMContext
    
    mock_message.text = "ООО Рога и Копыта"
    
    state = FSMContext(storage=state_storage, key=(mock_message.from_user.id,))
    
    await employer_company_name_received(mock_message, state, db_session)
    
    # Проверяем ответ
    bot_checker.assert_send_message_called("Компания: ООО Рога и Копыта")
    bot_checker.assert_send_message_called("Выберите сферу деятельности")
    
    # Проверяем состояние
    current_state = await state.get_state()
    assert current_state == OnboardingEmployer.company_field.__fsm_value__
    
    # Проверяем данные
    data = await state.get_data()
    assert data.get("company_name") == "ООО Рога и Копыта"


@pytest.mark.asyncio
@pytest.mark.onboarding
async def test_employer_company_field_selected(
    dp_with_handlers, mock_callback_query, db_session, bot_checker, mock_bot, state_storage
):
    """
    TEST: Работодатель выбирает сферу деятельности - шаг верификации.
    """
    from handlers.onboarding import employer_company_field_selected
    from aiogram.fsm.context import FSMContext
    
    mock_callback_query.data = "field_IT и разработка"
    
    state = FSMContext(storage=state_storage, key=(mock_callback_query.from_user.id,))
    await state.update_data(company_name="Test Company")
    await state.set_state(OnboardingEmployer.company_field)
    
    await employer_company_field_selected(mock_callback_query, state, db_session)
    
    # Проверяем ответ
    bot_checker.assert_edit_message_text_called("Сфера деятельности: IT и разработка")
    bot_checker.assert_edit_message_text_called("верификация компании")
    
    # Проверяем состояние
    current_state = await state.get_state()
    assert current_state == OnboardingEmployer.verification_step.__fsm_value__


@pytest.mark.asyncio
@pytest.mark.onboarding
async def test_employer_verification_complete_saves_profile(
    dp_with_handlers, mock_callback_query, db_session, bot_checker, mock_bot, state_storage
):
    """
    TEST: Завершение онбординга работодателя сохраняет профиль.
    """
    from handlers.onboarding import employer_verification_back
    from aiogram.fsm.context import FSMContext
    
    mock_callback_query.data = "back_to_menu"
    
    state = FSMContext(storage=state_storage, key=(mock_callback_query.from_user.id,))
    await state.update_data(
        company_name="Test Company",
        company_field="IT и разработка"
    )
    await state.set_state(OnboardingEmployer.verification_step)
    
    await employer_verification_back(mock_callback_query, state, db_session)
    
    # Проверяем что профиль сохранен
    result = await db_session.execute(
        select(User).where(User.telegram_id == str(mock_callback_query.from_user.id))
    )
    user = result.scalar_one_or_none()
    
    assert user is not None
    assert user.role == "employer"
    
    # Проверяем ответ
    bot_checker.assert_edit_message_text_called("Профиль компании создан")
    bot_checker.assert_edit_message_text_called("ожидает проверки")


# ==================== Тесты возврата в меню ====================

@pytest.mark.asyncio
@pytest.mark.onboarding
async def test_back_to_menu_from_any_state(
    dp_with_handlers, mock_callback_query, db_session, bot_checker, mock_bot, state_storage
):
    """
    TEST: Кнопка "Вернуться в меню" сбрасывает FSM и показывает меню.
    """
    from handlers.onboarding import back_to_menu_handler
    from aiogram.fsm.context import FSMContext
    
    mock_callback_query.data = "back_to_menu"
    
    # Создаем пользователя-студента
    user = User(
        telegram_id=str(mock_callback_query.from_user.id),
        role="student"
    )
    db_session.add(user)
    await db_session.commit()
    
    # Устанавливаем какое-то состояние
    state = FSMContext(storage=state_storage, key=(mock_callback_query.from_user.id,))
    await state.set_state(OnboardingStudent.course)
    
    # Вызываем хендлер
    await back_to_menu_handler(mock_callback_query, db_session, state)
    
    # Проверяем что состояние сброшено
    current_state = await state.get_state()
    assert current_state is None
    
    # Проверяем ответ
    bot_checker.assert_edit_message_text_called("Главное меню")


# ==================== Fallback тесты ====================

@pytest.mark.asyncio
@pytest.mark.onboarding
async def test_invalid_course_input_fallback(
    dp_with_handlers, mock_message, db_session, bot_checker, mock_bot, state_storage
):
    """
    TEST: Ввод текста вместо выбора курса вызывает fallback.
    """
    from handlers.onboarding import student_course_invalid
    from aiogram.fsm.context import FSMContext
    
    mock_message.text = "пятый курс"
    
    state = FSMContext(storage=state_storage, key=(mock_message.from_user.id,))
    await state.set_state(OnboardingStudent.course)
    
    # Вызываем fallback хендлер
    await student_course_invalid(mock_message)
    
    # Проверяем ответ с просьбой выбрать из кнопок
    bot_checker.assert_send_message_called("Пожалуйста, выберите курс из предложенных вариантов")
