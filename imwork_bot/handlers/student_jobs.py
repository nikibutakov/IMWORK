"""Хендлеры для поиска вакансий, карточки вакансии и откликов"""

import re
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, Vacancy, Application, Favorite
from states import ApplicationState
from keyboards.job_search import (
    get_job_filters_keyboard,
    get_sphere_selection_keyboard,
    get_format_selection_keyboard,
    get_salary_selection_keyboard,
    get_vacancy_list_keyboard,
    get_vacancy_detail_keyboard,
    get_application_type_keyboard,
    get_back_to_vacancy_list_keyboard,
)

router = Router()

# Константы для пагинации
VACANCIES_PER_PAGE = 5


# ==================== Поиск вакансий - главный экран ====================

@router.callback_query(F.data == "student_find_internship")
async def job_search_start(callback: types.CallbackQuery, session: AsyncSession):
    """Начало поиска вакансий - показ фильтров"""
    await callback.message.edit_text(
        "🔍 <b>Поиск стажировок и вакансий</b>\n\n"
        "Выберите фильтры для поиска или нажмите 'Применить фильтры' для просмотра всех доступных вакансий.",
        reply_markup=get_job_filters_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== Фильтры ====================

@router.callback_query(F.data == "filter_sphere")
async def filter_sphere_selected(callback: types.CallbackQuery, state: FSMContext):
    """Выбор фильтра по сфере деятельности"""
    data = await state.get_data()
    await callback.message.edit_text(
        "🌐 <b>Выберите сферу деятельности:</b>",
        reply_markup=get_sphere_selection_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sphere_"))
async def sphere_chosen(callback: types.CallbackQuery, state: FSMContext):
    """Пользователь выбрал сферу"""
    sphere = callback.data.replace("sphere_", "")
    data = await state.get_data()
    data["sphere"] = sphere
    await state.set_data(data)
    
    await callback.message.edit_text(
        f"✅ Сфера: <b>{sphere}</b>\n\n"
        "Выберите другие фильтры или нажмите 'Применить фильтры'",
        reply_markup=get_job_filters_keyboard(selected_sphere=sphere),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "filter_format")
async def filter_format_selected(callback: types.CallbackQuery, state: FSMContext):
    """Выбор фильтра по формату работы"""
    await callback.message.edit_text(
        "💼 <b>Выберите формат работы:</b>",
        reply_markup=get_format_selection_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("format_"))
async def format_chosen(callback: types.CallbackQuery, state: FSMContext):
    """Пользователь выбрал формат работы"""
    fmt = callback.data.replace("format_", "")
    data = await state.get_data()
    data["format"] = fmt
    await state.set_data(data)
    
    await callback.message.edit_text(
        f"✅ Формат: <b>{fmt}</b>\n\n"
        "Выберите другие фильтры или нажмите 'Применить фильтры'",
        reply_markup=get_job_filters_keyboard(
            selected_sphere=data.get("sphere"),
            selected_format=fmt
        ),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "filter_salary")
async def filter_salary_selected(callback: types.CallbackQuery, state: FSMContext):
    """Выбор фильтра по оплате"""
    await callback.message.edit_text(
        "💰 <b>Выберите уровень оплаты:</b>",
        reply_markup=get_salary_selection_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("salary_"))
async def salary_chosen(callback: types.CallbackQuery, state: FSMContext):
    """Пользователь выбрал оплату"""
    salary = callback.data.replace("salary_", "")
    data = await state.get_data()
    data["salary"] = salary
    await state.set_data(data)
    
    await callback.message.edit_text(
        f"✅ Оплата: <b>{salary}</b>\n\n"
        "Выберите другие фильтры или нажмите 'Применить фильтры'",
        reply_markup=get_job_filters_keyboard(
            selected_sphere=data.get("sphere"),
            selected_format=data.get("format"),
            selected_salary=salary
        ),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "filter_reset")
async def filter_reset(callback: types.CallbackQuery, state: FSMContext):
    """Сброс всех фильтров"""
    await state.clear()
    await callback.message.edit_text(
        "🔍 <b>Поиск стажировок и вакансий</b>\n\n"
        "Фильтры сброшены. Выберите новые фильтры или нажмите 'Применить фильтры' для просмотра всех вакансий.",
        reply_markup=get_job_filters_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "filter_back")
async def filter_back(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к главному экрану фильтров"""
    data = await state.get_data()
    await callback.message.edit_text(
        "🔍 <b>Поиск стажировок и вакансий</b>\n\n"
        "Выберите фильтры для поиска или нажмите 'Применить фильтры' для просмотра всех доступных вакансий.",
        reply_markup=get_job_filters_keyboard(
            selected_sphere=data.get("sphere"),
            selected_format=data.get("format"),
            selected_salary=data.get("salary")
        ),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== Применение фильтров и поиск ====================

@router.callback_query(F.data == "filter_apply")
async def apply_filters(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    """Применение фильтров и показ результатов"""
    data = await state.get_data()
    
    # Строим запрос с фильтрами
    query = select(Vacancy).where(Vacancy.status == "active")
    
    filters_applied = []
    
    if data.get("sphere"):
        query = query.where(Vacancy.category == data["sphere"])
        filters_applied.append(f"Сфера: {data['sphere']}")
    
    if data.get("format"):
        # Для MVP считаем, что формат хранится в conditions или description
        # В реальной БД нужно добавить поле format
        filters_applied.append(f"Формат: {data['format']}")
    
    if data.get("salary"):
        # Для MVP фильтрация по salary строковая
        filters_applied.append(f"Оплата: {data['salary']}")
    
    # Получаем общее количество вакансий
    count_query = select(func.count()).select_from(query.subquery())
    total_count_result = await session.execute(count_query)
    total_count = total_count_result.scalar() or 0
    
    # Получаем первую страницу результатов
    query = query.offset(0).limit(VACANCIES_PER_PAGE)
    result = await session.execute(query)
    vacancies = result.scalars().all()
    
    # Сохраняем текущие фильтры и общее количество в состоянии
    await state.update_data(filters=filters_applied, total_count=total_count, current_page=0)
    
    if not vacancies:
        await callback.message.edit_text(
            "😔 <b>Нет вакансий</b>\n\n"
            "По вашим фильтрам ничего не найдено. Попробуйте изменить фильтры.",
            reply_markup=get_job_filters_keyboard(),
            parse_mode="HTML"
        )
    else:
        vacancy_ids = [v.id for v in vacancies]
        has_next = len(vacancies) == VACANCIES_PER_PAGE
        
        filters_text = "\n".join(filters_applied) if filters_applied else "Все вакансии"
        
        await callback.message.edit_text(
            f"📋 <b>Найдено вакансий: {total_count}</b>\n\n"
            f"📊 Активные фильтры:\n{filters_text}\n\n"
            f"Страница 1 из {(total_count + VACANCIES_PER_PAGE - 1) // VACANCIES_PER_PAGE}",
            reply_markup=get_vacancy_list_keyboard(vacancy_ids, page=0, has_next=has_next),
            parse_mode="HTML"
        )
    
    await callback.answer()


# ==================== Пагинация ====================

@router.callback_query(F.data.startswith("page_"))
async def paginate_vacancies(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    """Пагинация списка вакансий"""
    page = int(callback.data.replace("page_", ""))
    data = await state.get_data()
    
    # Строим запрос с фильтрами
    query = select(Vacancy).where(Vacancy.status == "active")
    
    if data.get("sphere"):
        query = query.where(Vacancy.category == data["sphere"])
    
    # Получаем общее количество
    count_query = select(func.count()).select_from(query.subquery())
    total_count_result = await session.execute(count_query)
    total_count = total_count_result.scalar() or 0
    
    # Пагинация
    offset = page * VACANCIES_PER_PAGE
    query = query.offset(offset).limit(VACANCIES_PER_PAGE)
    result = await session.execute(query)
    vacancies = result.scalars().all()
    
    vacancy_ids = [v.id for v in vacancies]
    has_next = offset + len(vacancies) < total_count
    has_prev = page > 0
    
    filters_text = "\n".join(data.get("filters", ["Все вакансии"]))
    total_pages = (total_count + VACANCIES_PER_PAGE - 1) // VACANCIES_PER_PAGE
    
    await callback.message.edit_text(
        f"📋 <b>Найдено вакансий: {total_count}</b>\n\n"
        f"📊 Активные фильтры:\n{filters_text}\n\n"
        f"Страница {page + 1} из {total_pages}",
        reply_markup=get_vacancy_list_keyboard(vacancy_ids, page=page, has_next=has_next, has_prev=has_prev),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== Карточка вакансии ====================

@router.callback_query(F.data.startswith("vacancy_"))
async def show_vacancy_detail(callback: types.CallbackQuery, session: AsyncSession):
    """Показ детальной информации о вакансии"""
    vacancy_id = int(callback.data.replace("vacancy_", ""))
    
    result = await session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        await callback.message.answer("❌ Вакансия не найдена.")
        await callback.answer()
        return
    
    # Проверяем, в избранном ли вакансия
    telegram_id = str(callback.from_user.id)
    user_result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = user_result.scalar_one_or_none()
    
    is_favorite = False
    if user:
        fav_result = await session.execute(
            select(Favorite).where(
                and_(Favorite.user_id == user.id, Favorite.vacancy_id == vacancy_id)
            )
        )
        is_favorite = fav_result.scalar_one_or_none() is not None
    
    # Формируем текст карточки
    text = (
        f"📄 <b>{vacancy.title}</b>\n\n"
        f"🏢 <b>Компания:</b> ID {vacancy.author_id}\n"
        f"📂 <b>Категория:</b> {vacancy.category or 'Не указана'}\n"
        f"💰 <b>Зарплата:</b> {vacancy.salary or 'По договоренности'}\n\n"
        f"📝 <b>Описание:</b>\n{vacancy.description or 'Нет описания'}\n\n"
        f"✅ <b>Требования:</b>\n{vacancy.requirements or 'Не указаны'}\n\n"
        f"🎁 <b>Условия:</b>\n{vacancy.conditions or 'Не указаны'}"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_vacancy_detail_keyboard(vacancy_id, is_favorite),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_list")
async def back_to_vacancy_list(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    """Возврат к списку вакансий"""
    data = await state.get_data()
    
    if data.get("total_count", 0) == 0:
        # Если списка не было, возвращаемся к фильтрам
        await callback.message.edit_text(
            "🔍 <b>Поиск стажировок и вакансий</b>\n\n"
            "Выберите фильтры для поиска или нажмите 'Применить фильтры' для просмотра всех доступных вакансий.",
            reply_markup=get_job_filters_keyboard(
                selected_sphere=data.get("sphere"),
                selected_format=data.get("format"),
                selected_salary=data.get("salary")
            ),
            parse_mode="HTML"
        )
    else:
        # Возвращаемся к текущей странице
        page = data.get("current_page", 0)
        
        query = select(Vacancy).where(Vacancy.status == "active")
        if data.get("sphere"):
            query = query.where(Vacancy.category == data["sphere"])
        
        count_query = select(func.count()).select_from(query.subquery())
        total_count_result = await session.execute(count_query)
        total_count = total_count_result.scalar() or 0
        
        offset = page * VACANCIES_PER_PAGE
        query = query.offset(offset).limit(VACANCIES_PER_PAGE)
        result = await session.execute(query)
        vacancies = result.scalars().all()
        
        vacancy_ids = [v.id for v in vacancies]
        has_next = offset + len(vacancies) < total_count
        has_prev = page > 0
        
        filters_text = "\n".join(data.get("filters", ["Все вакансии"]))
        total_pages = (total_count + VACANCIES_PER_PAGE - 1) // VACANCIES_PER_PAGE
        
        await callback.message.edit_text(
            f"📋 <b>Найдено вакансий: {total_count}</b>\n\n"
            f"📊 Активные фильтры:\n{filters_text}\n\n"
            f"Страница {page + 1} из {total_pages}",
            reply_markup=get_vacancy_list_keyboard(vacancy_ids, page=page, has_next=has_next, has_prev=has_prev),
            parse_mode="HTML"
        )
    
    await callback.answer()


# ==================== Избранное ====================

@router.callback_query(F.data.startswith("fav_add_"))
async def add_to_favorites(callback: types.CallbackQuery, session: AsyncSession):
    """Добавление вакансии в избранное"""
    vacancy_id = int(callback.data.replace("fav_add_", ""))
    telegram_id = str(callback.from_user.id)
    
    # Получаем пользователя
    user_result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    # Проверяем, нет ли уже в избранном
    existing = await session.execute(
        select(Favorite).where(
            and_(Favorite.user_id == user.id, Favorite.vacancy_id == vacancy_id)
        )
    )
    
    if existing.scalar_one_or_none():
        await callback.answer("⚠️ Уже в избранном", show_alert=True)
        return
    
    # Добавляем в избранное
    favorite = Favorite(user_id=user.id, vacancy_id=vacancy_id)
    session.add(favorite)
    await session.commit()
    
    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=get_vacancy_detail_keyboard(vacancy_id, is_favorite=True)
    )
    
    await callback.answer("⭐️ Добавлено в избранное!", show_alert=False)


@router.callback_query(F.data.startswith("fav_remove_"))
async def remove_from_favorites(callback: types.CallbackQuery, session: AsyncSession):
    """Удаление вакансии из избранного"""
    vacancy_id = int(callback.data.replace("fav_remove_", ""))
    telegram_id = str(callback.from_user.id)
    
    user_result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    # Находим и удаляем запись
    result = await session.execute(
        select(Favorite).where(
            and_(Favorite.user_id == user.id, Favorite.vacancy_id == vacancy_id)
        )
    )
    favorite = result.scalar_one_or_none()
    
    if favorite:
        await session.delete(favorite)
        await session.commit()
    
    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=get_vacancy_detail_keyboard(vacancy_id, is_favorite=False)
    )
    
    await callback.answer("⭐️ Удалено из избранного", show_alert=False)


# ==================== Отклик на вакансию ====================

@router.callback_query(F.data.startswith("apply_"))
async def start_application(callback: types.CallbackQuery, state: FSMContext):
    """Начало процесса отклика на вакансию"""
    # Пропускаем apply без суффикса (это кнопка выбора типа отклика)
    if callback.data == "apply_" or not callback.data.split("_")[1].isdigit():
        vacancy_id = int(callback.data.replace("apply_", ""))
        await callback.message.edit_text(
            "📤 <b>Отклик на вакансию</b>\n\n"
            "Выберите способ отклика:",
            reply_markup=get_application_type_keyboard(vacancy_id),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    vacancy_id = int(callback.data.replace("apply_", ""))
    
    # Проверяем существование вакансии
    async with callback.bot.session() as temp_session:
        result = await temp_session.execute(
            select(Vacancy).where(Vacancy.id == vacancy_id)
        )
        vacancy = result.scalar_one_or_none()
        
        if not vacancy:
            await callback.answer("❌ Вакансия не найдена", show_alert=True)
            return
    
    await state.set_state(ApplicationState.selecting_type)
    await state.update_data(vacancy_id=vacancy_id)
    
    await callback.message.edit_text(
        "📤 <b>Отклик на вакансию</b>\n\n"
        "Выберите способ отклика:",
        reply_markup=get_application_type_keyboard(vacancy_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("apply_profile_"))
async def apply_with_profile(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    """Отклик с использованием профиля (MVP - заглушка)"""
    vacancy_id = int(callback.data.replace("apply_profile_", ""))
    telegram_id = str(callback.from_user.id)
    
    # Получаем пользователя и вакансию
    user_result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = user_result.scalar_one_or_none()
    
    vacancy_result = await session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    vacancy = vacancy_result.scalar_one_or_none()
    
    if not user or not vacancy:
        await callback.answer("❌ Ошибка: пользователь или вакансия не найдены", show_alert=True)
        return
    
    # Создаем заявку (MVP - без реального резюме)
    application = Application(
        vacancy_id=vacancy_id,
        applicant_id=user.id,
        cover_letter=f"Отклик через профиль пользователя {user.username or user.first_name}",
        resume_link="Из профиля (MVP)",
        status="pending"
    )
    session.add(application)
    await session.commit()
    
    await state.clear()
    
    await callback.message.edit_text(
        "✅ <b>Отклик отправлен!</b>\n\n"
        f"Ваш отклик на вакансию '{vacancy.title}' успешно сохранен.\n"
        "HR-менеджер рассмотрит вашу кандидатуру в ближайшее время.",
        reply_markup=get_back_to_vacancy_list_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("apply_upload_"))
async def apply_with_upload(callback: types.CallbackQuery, state: FSMContext):
    """Отклик с загрузкой нового файла"""
    vacancy_id = int(callback.data.replace("apply_upload_", ""))
    
    await state.set_state(ApplicationState.uploading_resume)
    await state.update_data(vacancy_id=vacancy_id)
    
    await callback.message.edit_text(
        "📁 <b>Загрузка резюме</b>\n\n"
        "Отправьте файл с резюме (PDF, DOC, DOCX) или текстовую ссылку на ваше резюме.\n\n"
        "Для отмены нажмите /cancel",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(ApplicationState.uploading_resume)
async def receive_resume_file(message: types.Message, state: FSMContext, session: AsyncSession):
    """Получение файла резюме или ссылки"""
    data = await state.get_data()
    vacancy_id = data.get("vacancy_id")
    
    telegram_id = str(message.from_user.id)
    
    # Получаем пользователя и вакансию
    user_result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = user_result.scalar_one_or_none()
    
    vacancy_result = await session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    vacancy = vacancy_result.scalar_one_or_none()
    
    if not user or not vacancy:
        await message.answer("❌ Ошибка: пользователь или вакансия не найдены.")
        await state.clear()
        return
    
    # Обрабатываем файл или текст
    resume_file_id = None
    resume_link = None
    
    if message.document:
        # Эмуляция загрузки - сохраняем file_id
        resume_file_id = message.document.file_id
        resume_link = f"Файл: {message.document.file_name}"
    elif message.text:
        # Считаем текст ссылкой или путем
        resume_link = message.text
    else:
        await message.answer("❌ Пожалуйста, отправьте файл или текстовую ссылку.")
        return
    
    # Создаем заявку
    application = Application(
        vacancy_id=vacancy_id,
        applicant_id=user.id,
        cover_letter="Отклик с загруженным резюме",
        resume_link=resume_link,
        resume_file_id=resume_file_id,
        status="pending"
    )
    session.add(application)
    await session.commit()
    
    await state.clear()
    
    await message.answer(
        "✅ <b>Отклик отправлен!</b>\n\n"
        f"Ваш отклик на вакансию '{vacancy.title}' успешно сохранен.\n"
        "HR-менеджер рассмотрит вашу кандидатуру в ближайшее время.",
        reply_markup=get_back_to_vacancy_list_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("apply_message_"))
async def apply_with_message(callback: types.CallbackQuery, state: FSMContext):
    """Отклик с написанием сообщения HR"""
    vacancy_id = int(callback.data.replace("apply_message_", ""))
    
    await state.set_state(ApplicationState.writing_message)
    await state.update_data(vacancy_id=vacancy_id)
    
    await callback.message.edit_text(
        "💬 <b>Написать HR-менеджеру</b>\n\n"
        "Напишите сопроводительное письмо или вопрос для HR.\n"
        "Ваше сообщение будет отправлено вместе с откликом.\n\n"
        "Для отмены нажмите /cancel",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(ApplicationState.writing_message)
async def receive_hr_message(message: types.Message, state: FSMContext, session: AsyncSession):
    """Получение сообщения для HR"""
    data = await state.get_data()
    vacancy_id = data.get("vacancy_id")
    
    telegram_id = str(message.from_user.id)
    
    user_result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = user_result.scalar_one_or_none()
    
    vacancy_result = await session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    vacancy = vacancy_result.scalar_one_or_none()
    
    if not user or not vacancy:
        await message.answer("❌ Ошибка: пользователь или вакансия не найдены.")
        await state.clear()
        return
    
    # Создаем заявку с сопроводительным письмом
    application = Application(
        vacancy_id=vacancy_id,
        applicant_id=user.id,
        cover_letter=message.text,
        status="pending"
    )
    session.add(application)
    await session.commit()
    
    # Заглушка: отправка в админ-чат
    # В реальности здесь был бы bot.send_message(admin_chat_id, ...)
    
    await state.clear()
    
    await message.answer(
        "✅ <b>Отклик отправлен!</b>\n\n"
        f"Ваш отклик на вакансию '{vacancy.title}' успешно сохранен.\n"
        "HR-менеджер рассмотрит вашу кандидатуру в ближайшее время.",
        reply_markup=get_back_to_vacancy_list_keyboard(),
        parse_mode="HTML"
    )


# ==================== Отмена отклика ====================

@router.message(F.text == "/cancel")
async def cancel_application(message: types.Message, state: FSMContext):
    """Отмена процесса отклика"""
    current_state = await state.get_state()
    if current_state in [ApplicationState.uploading_resume, ApplicationState.writing_message]:
        await state.clear()
        await message.answer(
            "❌ Отклик отменен.",
            reply_markup=get_back_to_vacancy_list_keyboard()
        )
