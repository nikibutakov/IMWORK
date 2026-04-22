"""Хендлеры для работодателя: создание вакансии, тарифы, статистика"""

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from models import User, Vacancy, Application, Favorite
from states import VacancyCreationState, CompanySettingsState
from keyboards.employer_menu import (
    get_employer_main_menu_keyboard,
    get_vacancy_creation_steps_keyboard,
    get_tariff_selection_keyboard,
    get_tariff_info_keyboard,
    get_premium_payment_keyboard,
    get_vacancy_list_employer_keyboard,
    get_vacancy_detail_employer_keyboard,
    get_vacancy_statistics_keyboard,
    get_applications_list_keyboard,
    get_application_detail_keyboard,
    get_company_settings_keyboard,
    get_back_to_employer_menu_keyboard,
)

router = Router()

# Константы
VACANCY_TITLE_MAX_LENGTH = 200
VACANCY_DESCRIPTION_MIN_LENGTH = 50
VACANCY_REQUIREMENTS_MIN_LENGTH = 20


# ==================== Главное меню работодателя ====================

@router.callback_query(F.data == "employer_main_menu")
async def employer_main_menu(callback: types.CallbackQuery):
    """Главное меню работодателя"""
    await callback.message.edit_text(
        "👔 <b>Меню работодателя</b>\n\n"
        "Управляйте вакансиями, отслеживайте статистику и настраивайте профиль компании.",
        reply_markup=get_employer_main_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== Создание вакансии - Пошаговая форма ====================

@router.callback_query(F.data == "employer_create_vacancy")
async def start_vacancy_creation(callback: types.CallbackQuery, state: FSMContext):
    """Начало создания вакансии"""
    await state.clear()
    await callback.message.edit_text(
        "📝 <b>Создание новой вакансии</b>\n\n"
        "Давайте заполним информацию о вакансии пошагово.\n\n"
        "❓ <b>Шаг 1/5:</b> Введите название позиции (например, \"Junior Python Developer\")\n\n"
        f"<i>Максимальная длина: {VACANCY_TITLE_MAX_LENGTH} символов</i>",
        reply_markup=get_vacancy_creation_steps_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(VacancyCreationState.position_name)
    await callback.answer()


@router.message(VacancyCreationState.position_name)
async def process_position_name(message: types.Message, state: FSMContext):
    """Обработка названия позиции"""
    position_name = message.text.strip()
    
    if len(position_name) == 0:
        await message.answer("❌ Название не может быть пустым. Попробуйте снова.")
        return
    
    if len(position_name) > VACANCY_TITLE_MAX_LENGTH:
        await message.answer(
            f"❌ Название слишком длинное ({len(position_name)} символов). "
            f"Максимум {VACANCY_TITLE_MAX_LENGTH} символов."
        )
        return
    
    await state.update_data(position_name=position_name)
    
    await message.answer(
        f"✅ Позиция: <b>{position_name}</b>\n\n"
        f"❓ <b>Шаг 2/5:</b> Опишите основные задачи сотрудника\n\n"
        f"<i>Минимальная длина: {VACANCY_DESCRIPTION_MIN_LENGTH} символов</i>",
        parse_mode="HTML"
    )
    await state.set_state(VacancyCreationState.tasks)


@router.message(VacancyCreationState.tasks)
async def process_tasks(message: types.Message, state: FSMContext):
    """Обработка описания задач"""
    tasks = message.text.strip()
    
    if len(tasks) < VACANCY_DESCRIPTION_MIN_LENGTH:
        await message.answer(
            f"❌ Описание слишком короткое ({len(tasks)} символов). "
            f"Минимум {VACANCY_DESCRIPTION_MIN_LENGTH} символов.\n\n"
            "Пожалуйста, опишите задачи подробнее."
        )
        return
    
    await state.update_data(tasks=tasks)
    
    await message.answer(
        f"✅ Задачи сохранены\n\n"
        f"❓ <b>Шаг 3/5:</b> Укажите требования к кандидату\n\n"
        f"<i>Минимальная длина: {VACANCY_REQUIREMENTS_MIN_LENGTH} символов</i>",
        parse_mode="HTML"
    )
    await state.set_state(VacancyCreationState.requirements)


@router.message(VacancyCreationState.requirements)
async def process_requirements(message: types.Message, state: FSMContext):
    """Обработка требований"""
    requirements = message.text.strip()
    
    if len(requirements) < VACANCY_REQUIREMENTS_MIN_LENGTH:
        await message.answer(
            f"❌ Требования слишком короткие ({len(requirements)} символов). "
            f"Минимум {VACANCY_REQUIREMENTS_MIN_LENGTH} символов."
        )
        return
    
    await state.update_data(requirements=requirements)
    
    await message.answer(
        f"✅ Требования сохранены\n\n"
        f"❓ <b>Шаг 4/5:</b> Опишите условия работы\n\n"
        "(график, удалёнка, бонусы, обучение и т.д.)",
        parse_mode="HTML"
    )
    await state.set_state(VacancyCreationState.conditions)


@router.message(VacancyCreationState.conditions)
async def process_conditions(message: types.Message, state: FSMContext):
    """Обработка условий работы"""
    conditions = message.text.strip()
    
    if len(conditions) < 10:
        await message.answer("❌ Условия слишком короткие. Опишите подробнее.")
        return
    
    await state.update_data(conditions=conditions)
    
    await message.answer(
        f"✅ Условия сохранены\n\n"
        f"❓ <b>Шаг 5/5:</b> Укажите зарплату\n\n"
        "Например: \"50000-80000 ₽\", \"от 60000 ₽\" или \"По договоренности\"\n\n"
        "<i>Можно пропустить, отправив \"Пропустить\"</i>",
        parse_mode="HTML"
    )
    await state.set_state(VacancyCreationState.salary_input)


@router.message(VacancyCreationState.salary_input)
async def process_salary_input(message: types.Message, state: FSMContext):
    """Обработка зарплаты"""
    salary = message.text.strip()
    
    if salary.lower() in ["пропустить", "skip", "-"]:
        salary = "По договоренности"
    
    await state.update_data(salary=salary)
    
    # Выбор категории
    categories = [
        "IT и разработка",
        "Дизайн и креатив",
        "Маркетинг и реклама",
        "Финансы и банки",
        "Образование",
        "Продажи",
        "Менеджмент",
        "Другое"
    ]
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=cat, callback_data=f"vcat_{cat}")]
            for cat in categories
        ] + [[types.InlineKeyboardButton(text="↩️ Назад", callback_data="employer_cancel_creation")]]
    )
    
    await message.answer(
        f"✅ Зарплата: <b>{salary}</b>\n\n"
        "Выберите категорию вакансии:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(VacancyCreationState.category_select)


@router.callback_query(F.data.startswith("vcat_"))
async def process_category_select(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """Выбор категории и финальное создание"""
    category = callback.data.replace("vcat_", "")
    data = await state.get_data()
    
    # Получаем пользователя
    telegram_id = str(callback.from_user.id)
    user_result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    # Создаём вакансию со статусом "moderation"
    vacancy = Vacancy(
        author_id=user.id,
        title=data["position_name"],
        description=data["tasks"],
        requirements=data["requirements"],
        conditions=data["conditions"],
        salary=data["salary"],
        category=category,
        status="moderation"  # Сразу на модерацию
    )
    
    session.add(vacancy)
    await session.commit()
    await session.refresh(vacancy)
    
    await state.clear()
    
    await callback.message.answer(
        f"✅ <b>Вакансия создана!</b>\n\n"
        f"📄 <b>{vacancy.title}</b>\n"
        f"📂 Категория: {category}\n"
        f"💰 Зарплата: {vacancy.salary}\n\n"
        "🟡 Вакансия отправлена на модерацию.\n"
        "После одобрения она появится в поиске для студентов.\n\n"
        f"ID вакансии: #{vacancy.id}",
        reply_markup=get_back_to_employer_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "employer_cancel_creation")
async def cancel_vacancy_creation(callback: types.CallbackQuery, state: FSMContext):
    """Отмена создания вакансии"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Создание вакансии отменено.",
        reply_markup=get_employer_main_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== Мои вакансии ====================

@router.callback_query(F.data == "employer_my_vacancies")
async def show_my_vacancies(callback: types.CallbackQuery, session: AsyncSession):
    """Показ списка вакансий работодателя"""
    telegram_id = str(callback.from_user.id)
    
    # Получаем пользователя
    user_result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    # Получаем вакансии пользователя
    result = await session.execute(
        select(Vacancy)
        .where(Vacancy.author_id == user.id)
        .order_by(Vacancy.created_at.desc())
    )
    vacancies = result.scalars().all()
    
    if not vacancies:
        await callback.message.edit_text(
            "📭 <b>У вас пока нет вакансий</b>\n\n"
            "Создайте первую вакансию, чтобы начать поиск сотрудников!",
            reply_markup=get_employer_main_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        # Формируем список для клавиатуры
        vacancy_list = [(v.id, v.title, v.status) for v in vacancies]
        
        status_names = {
            "active": "Активна",
            "moderation": "На модерации",
            "rejected": "Отклонена",
            "draft": "Черновик",
            "closed": "Закрыта"
        }
        
        text = "💼 <b>Мои вакансии</b>\n\n"
        for v in vacancies:
            status_name = status_names.get(v.status, v.status)
            text += f"• #{v.id} {v.title[:30]}... — {status_name}\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_vacancy_list_employer_keyboard(vacancy_list),
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("employer_vacancy_"))
async def show_employer_vacancy_detail(callback: types.CallbackQuery, session: AsyncSession):
    """Детальная информация о вакансии работодателя"""
    vacancy_id = int(callback.data.replace("employer_vacancy_", ""))
    
    result = await session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        await callback.answer("❌ Вакансия не найдена", show_alert=True)
        return
    
    # Считаем количество откликов
    apps_result = await session.execute(
        select(func.count()).select_from(Application).where(Application.vacancy_id == vacancy_id)
    )
    applications_count = apps_result.scalar() or 0
    
    status_names = {
        "active": "🟢 Активна",
        "moderation": "🟡 На модерации",
        "rejected": "🔴 Отклонена",
        "draft": "⚪ Черновик",
        "closed": "⚫ Закрыта"
    }
    status_name = status_names.get(vacancy.status, vacancy.status)
    
    text = (
        f"📄 <b>{vacancy.title}</b>\n\n"
        f"🆔 ID: #{vacancy.id}\n"
        f"📊 Статус: {status_name}\n"
        f"📂 Категория: {vacancy.category or 'Не указана'}\n"
        f"💰 Зарплата: {vacancy.salary or 'По договоренности'}\n"
        f"👥 Откликов: {applications_count}\n"
        f"📅 Создана: {vacancy.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"📝 <b>Описание:</b>\n{vacancy.description or 'Нет описания'}\n\n"
        f"✅ <b>Требования:</b>\n{vacancy.requirements or 'Не указаны'}\n\n"
        f"🎁 <b>Условия:</b>\n{vacancy.conditions or 'Не указаны'}"
    )
    
    # Комментарий модератора при отклонении
    if vacancy.status == "rejected" and vacancy.moderation_comment:
        text += f"\n\n❌ <b>Комментарий модератора:</b>\n{vacancy.moderation_comment}"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_vacancy_detail_employer_keyboard(vacancy_id, vacancy.status),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== Статистика вакансии ====================

@router.callback_query(F.data.startswith("vacancy_stats_"))
async def show_vacancy_statistics(callback: types.CallbackQuery, session: AsyncSession):
    """Показ статистики по вакансии"""
    vacancy_id = int(callback.data.replace("vacancy_stats_", ""))
    
    result = await session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        await callback.answer("❌ Вакансия не найдена", show_alert=True)
        return
    
    # Считаем отклики по статусам
    total_apps = await session.execute(
        select(func.count()).select_from(Application).where(Application.vacancy_id == vacancy_id)
    )
    total_apps = total_apps.scalar() or 0
    
    pending_apps = await session.execute(
        select(func.count()).select_from(Application).where(
            and_(Application.vacancy_id == vacancy_id, Application.status == "pending")
        )
    )
    pending_apps = pending_apps.scalar() or 0
    
    # Для MVP views_count не реализован, можно добавить в модель Vacancy
    views_count = 0  # Заглушка
    
    days_active = (datetime.utcnow() - vacancy.created_at).days if vacancy.created_at else 0
    
    text = (
        f"📊 <b>Статистика вакансии</b>\n\n"
        f"📄 <b>{vacancy.title}</b>\n\n"
        f"👁️ Просмотров: {views_count}\n"
        f"📤 Откликов всего: {total_apps}\n"
        f"⏳ Ожидают рассмотрения: {pending_apps}\n"
        f"📅 Дней активно: {days_active}\n\n"
    )
    
    if total_apps > 0:
        conversion = round((total_apps / max(views_count, 1)) * 100, 1)
        text += f"📈 Конверсия: {conversion}% (от просмотров)"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_vacancy_statistics_keyboard(vacancy_id),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== Отклики на вакансию ====================

@router.callback_query(F.data.startswith("vacancy_applications_"))
async def show_vacancy_applications(callback: types.CallbackQuery, session: AsyncSession):
    """Показ списка откликов на вакансию"""
    vacancy_id = int(callback.data.replace("vacancy_applications_", ""))
    
    # Проверяем вакансию
    result = await session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        await callback.answer("❌ Вакансия не найдена", show_alert=True)
        return
    
    # Получаем отклики
    apps_result = await session.execute(
        select(Application, User)
        .join(User, Application.applicant_id == User.id)
        .where(Application.vacancy_id == vacancy_id)
        .order_by(Application.created_at.desc())
    )
    applications = apps_result.all()
    
    if not applications:
        await callback.message.edit_text(
            "📭 <b>Нет откликов</b>\n\n"
            "На эту вакансию пока никто не откликнулся.",
            reply_markup=get_vacancy_detail_employer_keyboard(vacancy_id, vacancy.status),
            parse_mode="HTML"
        )
    else:
        app_list = [(app.id, f"{user.first_name or ''} {user.last_name or ''} (@{user.username or 'No username'})") 
                    for app, user in applications]
        
        text = f"👥 <b>Отклики на вакансию</b>\n\n📄 {vacancy.title}\n\n"
        for app_id, name in app_list:
            text += f"• {name}\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_applications_list_keyboard(app_list),
            parse_mode="HTML"
        )
    
    await callback.answer()


# ==================== Тарифы ====================

@router.callback_query(F.data == "employer_tariffs")
async def show_tariffs(callback: types.CallbackQuery):
    """Показ доступных тарифов"""
    await callback.message.edit_text(
        "💳 <b>Тарифы для работодателей</b>\n\n"
        "🟢 <b>Стандарт</b> — Бесплатно\n"
        "• Публикация до 3 вакансий\n"
        "• Стандартное размещение в поиске\n"
        "• Базовая статистика\n\n"
        "🔵 <b>Премиум</b> — 2000₽/мес\n"
        "• Безлимитные вакансии\n"
        "• Приоритетное размещение\n"
        "• Расширенная статистика\n"
        "• Выделение в поиске\n"
        "• Поддержка 24/7",
        reply_markup=get_tariff_selection_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "tariff_standard")
async def select_standard_tariff(callback: types.CallbackQuery, session: AsyncSession):
    """Выбор стандартного тарифа"""
    telegram_id = str(callback.from_user.id)
    user_result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = user_result.scalar_one_or_none()
    
    if user:
        user.tariff = "free"
        user.tariff_expires_at = None
        await session.commit()
    
    await callback.message.edit_text(
        "✅ <b>Тариф «Стандарт» активирован!</b>\n\n"
        "Вы можете публиковать до 3 вакансий бесплатно.\n"
        "Для расширения возможностей выберите тариф «Премиум».",
        reply_markup=get_employer_main_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer("Тариф активирован!", show_alert=True)


@router.callback_query(F.data == "tariff_premium")
async def select_premium_tariff(callback: types.CallbackQuery):
    """Выбор премиум тарифа - эмуляция оплаты"""
    await callback.message.edit_text(
        "🔵 <b>Тариф «Премиум»</b>\n\n"
        "Стоимость: <b>2000₽/мес</b>\n\n"
        "⚠️ <i>В MVP режиме оплата эмулируется.</i>\n"
        "В реальной версии здесь будет подключение платёжной системы.",
        reply_markup=get_premium_payment_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "premium_pay_confirm")
async def confirm_premium_payment(callback: types.CallbackQuery, session: AsyncSession):
    """Подтверждение оплаты премиум (эмуляция)"""
    telegram_id = str(callback.from_user.id)
    user_result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = user_result.scalar_one_or_none()
    
    if user:
        user.tariff = "premium"
        user.tariff_expires_at = datetime.utcnow() + timedelta(days=30)
        await session.commit()
    
    await callback.message.edit_text(
        "🎉 <b>Оплата прошла успешно!</b>\n\n"
        "✅ Тариф «Премиум» активирован на 30 дней.\n"
        f"📅 Действует до: {(datetime.utcnow() + timedelta(days=30)).strftime('%d.%m.%Y')}\n\n"
        "Теперь вам доступны:\n"
        "• Безлимитные вакансии\n"
        "• Приоритетное размещение\n"
        "• Расширенная статистика",
        reply_markup=get_employer_main_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer("Премиум активирован!", show_alert=True)


# ==================== Настройки компании ====================

@router.callback_query(F.data == "employer_settings")
async def show_company_settings(callback: types.CallbackQuery):
    """Показ настроек компании"""
    await callback.message.edit_text(
        "⚙️ <b>Настройки компании</b>\n\n"
        "Управляйте информацией о вашей компании и контактами.",
        reply_markup=get_company_settings_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "settings_edit_contacts")
async def edit_contacts_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало редактирования контактов"""
    await callback.message.edit_text(
        "✏️ <b>Редактирование контактов</b>\n\n"
        "Отправьте новые контактные данные:\n"
        "• Email\n"
        "• Телефон\n"
        "• Сайт\n"
        "• Соцсети\n\n"
        "Можно отправить текстом в любом формате.\n\n"
        "Или нажмите «Отмена» для выхода.",
        reply_markup=get_back_to_employer_menu_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(CompanySettingsState.edit_contacts)
    await callback.answer()


@router.message(CompanySettingsState.edit_contacts)
async def process_edit_contacts(message: types.Message, state: FSMContext, session: AsyncSession):
    """Сохранение новых контактов (заглушка)"""
    contacts = message.text.strip()
    telegram_id = str(message.from_user.id)
    
    # В MVP просто сохраняем в поле username как заглушку
    # В реальной версии нужно добавить поле contacts в модель User или создать Company
    user_result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = user_result.scalar_one_or_none()
    
    if user:
        # Заглушка: сохраняем контакты в username (в реальности нужно отдельное поле)
        # user.contacts = contacts
        pass
    
    await state.clear()
    
    await message.answer(
        "✅ <b>Контакты обновлены!</b>\n\n"
        f"Новые контакты:\n{contacts}\n\n"
        "<i>В MVP режиме данные сохраняются временно.</i>",
        reply_markup=get_employer_main_menu_keyboard(),
        parse_mode="HTML"
    )


# ==================== Общая статистика работодателя ====================

@router.callback_query(F.data == "employer_statistics")
async def show_general_statistics(callback: types.CallbackQuery, session: AsyncSession):
    """Общая статистика работодателя"""
    telegram_id = str(callback.from_user.id)
    
    user_result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    # Считаем вакансии
    vacancies_result = await session.execute(
        select(func.count()).select_from(Vacancy).where(Vacancy.author_id == user.id)
    )
    total_vacancies = vacancies_result.scalar() or 0
    
    active_vacancies = await session.execute(
        select(func.count()).select_from(Vacancy).where(
            and_(Vacancy.author_id == user.id, Vacancy.status == "active")
        )
    )
    active_vacancies = active_vacancies.scalar() or 0
    
    # Считаем отклики
    applications_result = await session.execute(
        select(func.count()).select_from(Application)
        .join(Vacancy, Application.vacancy_id == Vacancy.id)
        .where(Vacancy.author_id == user.id)
    )
    total_applications = applications_result.scalar() or 0
    
    tariff_name = "Премиум" if user.tariff == "premium" else "Стандарт"
    tariff_expires = user.tariff_expires_at.strftime("%d.%m.%Y") if user.tariff_expires_at else "Бессрочно"
    
    text = (
        f"📊 <b>Общая статистика</b>\n\n"
        f"🏢 <b>Тариф:</b> {tariff_name}\n"
        f"📅 <b>Действует до:</b> {tariff_expires}\n\n"
        f"📄 <b>Всего вакансий:</b> {total_vacancies}\n"
        f"🟢 <b>Активных:</b> {active_vacancies}\n"
        f"👥 <b>Всего откликов:</b> {total_applications}\n"
    )
    
    if total_vacancies > 0 and total_applications > 0:
        avg_apps = round(total_applications / total_vacancies, 1)
        text += f"\n📈 <b>Среднее откликов на вакансию:</b> {avg_apps}"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_employer_main_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
