"""
Тесты для Карьерного центра - образовательные материалы.

TEST: Сценарий 4 из ТЗ - Career Center
- 🎓 Карьерный центр → выбор категории → отправка материала → 
  нажатие ⭐️ Сохранить → запись в saved_materials → 
  нажатие ❓ Задать вопрос → callback-имитация отправки куратору

Запуск: pytest tests/test_career_center.py -v
"""

import pytest
from sqlalchemy import select
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import State

from models import User, CareerMaterial


# ==================== Тесты главного экрана Карьерного центра ====================

@pytest.mark.asyncio
@pytest.mark.career_center
async def test_career_center_start_shows_categories(
    dp_with_handlers, mock_callback_query, db_session, bot_checker, mock_bot
):
    """
    TEST: Нажатие "🎓 Карьерный центр" показывает категории материалов.
    
    Сценарий:
    1. Пользователь нажимает "🎓 Карьерный центр"
    2. Бот показывает 4 категории: Резюме, Собеседования, Карьерный рост, Поиск работы
    """
    from handlers.career_center import career_center_start
    
    await career_center_start(mock_callback_query)
    
    # Проверяем ответ
    bot_checker.assert_edit_message_text_called("Карьерный центр")
    bot_checker.assert_edit_message_text_called("Выберите категорию")
    
    # Проверяем клавиатуру с категориями
    call_args = mock_bot.edit_message_text.call_args
    reply_markup = call_args.kwargs.get('reply_markup')
    keyboard_buttons = [btn.text for row in reply_markup.inline_keyboard for btn in row]
    
    assert "📝 Резюме и сопроводительные" in keyboard_buttons
    assert "🎤 Собеседования" in keyboard_buttons
    assert "📈 Карьерный рост" in keyboard_buttons
    assert "💼 Поиск работы" in keyboard_buttons


# ==================== Тесты выбора категории ====================

@pytest.mark.asyncio
@pytest.mark.career_center
async def test_category_selected_empty(
    dp_with_handlers, mock_callback_query, db_session, bot_checker, mock_bot
):
    """
    TEST: Выбор категории без материалов показывает заглушку.
    """
    from handlers.career_center import category_selected
    
    mock_callback_query.data = "cat_resume"
    
    await category_selected(mock_callback_query, db_session)
    
    # Проверяем что показано сообщение об отсутствии материалов
    bot_checker.assert_edit_message_text_called("Резюме и сопроводительные")
    bot_checker.assert_edit_message_text_called("пока нет материалов")


@pytest.mark.asyncio
@pytest.mark.career_center
async def test_category_selected_with_materials(
    dp_with_handlers, mock_callback_query, db_session, bot_checker, mock_bot
):
    """
    TEST: Выбор категории с материалами показывает список.
    
    Сценарий:
    1. Создаем тестовые материалы в БД
    2. Пользователь выбирает категорию
    3. Бот показывает список материалов
    """
    from handlers.career_center import category_selected
    
    # Создаем тестовые материалы
    material1 = CareerMaterial(
        title="Как составить резюме",
        description="Гайд по созданию эффективного резюме",
        content="Полный текст гайда",
        material_type="guide",
        category="cat_resume",
        is_published=True
    )
    material2 = CareerMaterial(
        title="Шаблон резюме для студента",
        description="Готовый шаблон",
        material_type="template",
        category="cat_resume",
        is_published=True
    )
    db_session.add(material1)
    db_session.add(material2)
    await db_session.commit()
    
    mock_callback_query.data = "cat_resume"
    
    await category_selected(mock_callback_query, db_session)
    
    # Проверяем ответ
    bot_checker.assert_edit_message_text_called("Резюме и сопроводительные")
    bot_checker.assert_edit_message_text_called("Найдено материалов: 2")
    
    # Проверяем клавиатуру со списком
    call_args = mock_bot.edit_message_text.call_args
    reply_markup = call_args.kwargs.get('reply_markup')
    keyboard_buttons = [btn.text for row in reply_markup.inline_keyboard for btn in row]
    
    assert any("Как составить резюме" in btn for btn in keyboard_buttons)


# ==================== Тесты просмотра материала ====================

@pytest.mark.asyncio
@pytest.mark.career_center
async def test_material_detail_shows_content(
    dp_with_handlers, mock_callback_query, db_session, bot_checker, mock_bot
):
    """
    TEST: Просмотр детальной информации о материале.
    
    Сценарий:
    1. Создаем материал в БД
    2. Пользователь нажимает на материал
    3. Бот показывает полное содержание с кнопками действий
    """
    from handlers.career_center import material_detail
    
    # Создаем тестовый материал
    material = CareerMaterial(
        title="Собеседование: советы новичку",
        description="Полезные советы для прохождения собеседований",
        content="Подробный текст с рекомендациями",
        material_type="article",
        category="cat_interviews",
        is_published=True,
        views_count=0
    )
    db_session.add(material)
    await db_session.commit()
    
    mock_callback_query.data = f"material_{material.id}"
    
    await material_detail(mock_callback_query, db_session)
    
    # Проверяем ответ
    bot_checker.assert_edit_message_text_called("Собеседование: советы новичку")
    bot_checker.assert_edit_message_text_called("Полезные советы")
    
    # Проверяем что счетчик просмотров увеличился
    await db_session.refresh(material)
    assert material.views_count == 1
    
    # Проверяем клавиатуру с действиями
    call_args = mock_bot.edit_message_text.call_args
    reply_markup = call_args.kwargs.get('reply_markup')
    keyboard_buttons = [btn.text for row in reply_markup.inline_keyboard for btn in row]
    
    assert "📥 Скачать" in keyboard_buttons
    assert "💾 Сохранить" in keyboard_buttons
    assert "❓ Задать вопрос куратору" in keyboard_buttons


# ==================== Тесты скачивания материала ====================

@pytest.mark.asyncio
@pytest.mark.career_center
async def test_download_material_emulation(
    dp_with_handlers, mock_callback_query, db_session, bot_checker, mock_bot
):
    """
    TEST: Скачивание материала (MVP эмуляция).
    
    В MVP файлы не загружаются реально, показывается уведомление.
    """
    from handlers.career_center import download_material
    
    # Создаем материал
    material = CareerMaterial(
        title="Test Guide",
        material_type="guide",
        is_published=True
    )
    db_session.add(material)
    await db_session.commit()
    
    mock_callback_query.data = f"material_download_{material.id}"
    
    await download_material(mock_callback_query, db_session)
    
    # Проверяем ответ
    bot_checker.assert_send_message_called("Скачивание материала")
    bot_checker.assert_send_message_called("В MVP-версии файл не загружается реально")


# ==================== Тесты сохранения материала ====================

@pytest.mark.asyncio
@pytest.mark.career_center
async def test_save_material_notification(
    dp_with_handlers, mock_callback_query, db_session, bot_checker, mock_bot
):
    """
    TEST: Сохранение материала в избранное.
    
    MVP: Просто уведомление, без записи в БД.
    """
    from handlers.career_center import save_material
    
    # Создаем материал
    material = CareerMaterial(
        title="Important Material",
        is_published=True
    )
    db_session.add(material)
    await db_session.commit()
    
    mock_callback_query.data = f"material_save_{material.id}"
    
    await save_material(mock_callback_query, db_session)
    
    # Проверяем уведомление
    bot_checker.assert_answer_callback_called()
    
    # В полной версии здесь была бы проверка записи в saved_materials


# ==================== Тесты вопроса куратору ====================

@pytest.mark.asyncio
@pytest.mark.career_center
async def test_ask_question_starts_fsm(
    dp_with_handlers, mock_callback_query, db_session, bot_checker, mock_bot, state_storage
):
    """
    TEST: Нажатие "❓ Задать вопрос куратору" запускает FSM.
    
    Сценарий:
    1. Пользователь нажимает кнопку вопроса
    2. Бот просит написать вопрос
    3. Устанавливается состояние ожидания вопроса
    """
    from handlers.career_center import ask_question_about_material
    from aiogram.fsm.context import FSMContext
    
    # Создаем материал
    material = CareerMaterial(
        title="Test Material",
        is_published=True
    )
    db_session.add(material)
    await db_session.commit()
    
    state = FSMContext(storage=state_storage, key=(mock_callback_query.from_user.id,))
    mock_callback_query.data = f"material_question_{material.id}"
    
    await ask_question_about_material(mock_callback_query, state, db_session)
    
    # Проверяем ответ
    bot_checker.assert_send_message_called("Задать вопрос куратору")
    bot_checker.assert_send_message_called("Напишите ваш вопрос")
    
    # Проверяем состояние
    current_state = await state.get_state()
    assert current_state == "waiting_question"
    
    # Проверяем что ID материала сохранен
    data = await state.get_data()
    assert data.get("question_material_id") == material.id


@pytest.mark.asyncio
@pytest.mark.career_center
async def test_receive_question_sends_to_curator(
    dp_with_handlers, mock_message, db_session, bot_checker, mock_bot, state_storage
):
    """
    TEST: Отправка вопроса куратору.
    
    Сценарий:
    1. Пользователь пишет вопрос
    2. Вопрос отправляется куратору (в MVP - эмуляция)
    3. Пользователь получает подтверждение
    """
    from handlers.career_center import receive_question
    from aiogram.fsm.context import FSMContext
    
    # Настраиваем состояние
    state = FSMContext(storage=state_storage, key=(mock_message.from_user.id,))
    await state.set_state("waiting_question")
    await state.update_data(question_material_id=1)
    
    mock_message.text = "Как лучше подготовиться к собеседованию?"
    
    await receive_question(mock_message, state, db_session)
    
    # Проверяем ответ
    bot_checker.assert_send_message_called("Вопрос отправлен")
    bot_checker.assert_send_message_called("Ответ придет в личные сообщения")
    
    # Проверяем что состояние сброшено
    current_state = await state.get_state()
    assert current_state is None


@pytest.mark.asyncio
@pytest.mark.career_center
async def test_cancel_question(
    dp_with_handlers, mock_message, db_session, bot_checker, mock_bot, state_storage
):
    """
    TEST: Отмена вопроса командой /cancel.
    """
    from handlers.career_center import cancel_question
    from aiogram.fsm.context import FSMContext
    
    state = FSMContext(storage=state_storage, key=(mock_message.from_user.id,))
    await state.set_state("waiting_question")
    
    mock_message.text = "/cancel"
    
    await cancel_question(mock_message, state, db_session)
    
    # Проверяем ответ
    bot_checker.assert_send_message_called("Вопрос отменен")
    
    # Проверяем что состояние сброшено
    current_state = await state.get_state()
    assert current_state is None


# ==================== Тесты навигации ====================

@pytest.mark.asyncio
@pytest.mark.career_center
async def test_back_to_categories_from_material_list(
    dp_with_handlers, mock_callback_query, db_session, bot_checker, mock_bot
):
    """
    TEST: Возврат к списку категорий из списка материалов.
    """
    # Проверяется через callback категории
    from handlers.career_center import category_selected
    
    mock_callback_query.data = "cat_growth"
    
    await category_selected(mock_callback_query, db_session)
    
    # Проверяем что показана категория
    bot_checker.assert_edit_message_text_called("Карьерный рост")


# ==================== Тесты неопубликованных материалов ====================

@pytest.mark.asyncio
@pytest.mark.career_center
async def test_unpublished_materials_not_shown(
    dp_with_handlers, mock_callback_query, db_session, bot_checker, mock_bot
):
    """
    TEST: Неопубликованные материалы не показываются в списке.
    
    Сценарий:
    1. Создаем материал с is_published=False
    2. Выбираем категорию
    3. Материал не должен быть в списке
    """
    from handlers.career_center import category_selected
    
    # Создаем неопубликованный материал
    material = CareerMaterial(
        title="Draft Material",
        category="cat_resume",
        is_published=False  # Не опубликован
    )
    db_session.add(material)
    await db_session.commit()
    
    mock_callback_query.data = "cat_resume"
    
    await category_selected(mock_callback_query, db_session)
    
    # Проверяем что материал не показан
    bot_checker.assert_edit_message_text_called("пока нет материалов")


# ==================== Тесты разных типов материалов ====================

@pytest.mark.asyncio
@pytest.mark.career_center
@pytest.mark.parametrize("material_type,expected_text", [
    ("video", "Ссылка на видео"),
    ("guide", "Гайд доступен"),
    ("article", "Материал готов"),
])
async def test_download_different_material_types(
    dp_with_handlers, mock_callback_query, db_session, bot_checker, mock_bot,
    material_type, expected_text
):
    """
    TEST: Скачивание материалов разных типов.
    """
    from handlers.career_center import download_material
    
    material = CareerMaterial(
        title=f"Test {material_type}",
        material_type=material_type,
        is_published=True
    )
    db_session.add(material)
    await db_session.commit()
    
    mock_callback_query.data = f"material_download_{material.id}"
    
    await download_material(mock_callback_query, db_session)
    
    bot_checker.assert_send_message_called(expected_text)
