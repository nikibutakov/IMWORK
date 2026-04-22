"""Клавиатуры для работодателя: создание вакансии, тарифы, меню"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_employer_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню работодателя"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Создать вакансию", callback_data="employer_create_vacancy")
    builder.button(text="💼 Мои вакансии", callback_data="employer_my_vacancies")
    builder.button(text="📊 Статистика", callback_data="employer_statistics")
    builder.button(text="💳 Тарифы и оплата", callback_data="employer_tariffs")
    builder.button(text="⚙️ Настройки компании", callback_data="employer_settings")
    builder.button(text="🔙 В главное меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_vacancy_creation_steps_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для пошагового создания вакансии"""
    builder = InlineKeyboardBuilder()
    builder.button(text="➡️ Далее", callback_data="vacancy_step_next")
    builder.button(text="❌ Отмена", callback_data="employer_cancel_creation")
    builder.adjust(2)
    return builder.as_markup()


def get_vacancy_draft_keyboard(vacancy_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для черновика вакансии"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Опубликовать", callback_data=f"vacancy_publish_{vacancy_id}")
    builder.button(text="✏️ Редактировать", callback_data=f"vacancy_edit_{vacancy_id}")
    builder.button(text="🗑️ Удалить", callback_data=f"vacancy_delete_{vacancy_id}")
    builder.button(text="🔙 Назад", callback_data="employer_my_vacancies")
    builder.adjust(2)
    return builder.as_markup()


def get_tariff_selection_keyboard() -> InlineKeyboardMarkup:
    """Выбор тарифа для публикации вакансии"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🟢 Стандарт (Бесплатно)", callback_data="tariff_standard")
    builder.button(text="🔵 Премиум (2000₽)", callback_data="tariff_premium")
    builder.button(text="🔙 Назад", callback_data="employer_tariffs")
    builder.adjust(1)
    return builder.as_markup()


def get_tariff_info_keyboard() -> InlineKeyboardMarkup:
    """Информация о тарифах с кнопкой выбора"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🟢 Выбрать Стандарт", callback_data="tariff_standard")
    builder.button(text="🔵 Выбрать Премиум", callback_data="tariff_premium")
    builder.button(text="🔙 Назад в меню", callback_data="employer_main_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_premium_payment_keyboard() -> InlineKeyboardMarkup:
    """Эмуляция оплаты премиум-тарифа"""
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Оплатить 2000₽", callback_data="premium_pay_confirm")
    builder.button(text="❌ Отмена", callback_data="employer_tariffs")
    builder.adjust(1)
    return builder.as_markup()


def get_vacancy_list_employer_keyboard(vacancies: list[tuple[int, str, str]]) -> InlineKeyboardMarkup:
    """
    Список вакансий работодателя.
    
    Args:
        vacancies: Список кортежей (id, title, status)
    """
    builder = InlineKeyboardBuilder()
    
    for vid, title, status in vacancies:
        # Эмодзи для статуса
        status_emoji = {"active": "🟢", "moderation": "🟡", "rejected": "🔴", "draft": "⚪", "closed": "⚫"}
        emoji = status_emoji.get(status, "⚪")
        short_title = title[:35] + "..." if len(title) > 35 else title
        builder.button(text=f"{emoji} {short_title}", callback_data=f"employer_vacancy_{vid}")
    
    builder.button(text="🔙 Назад в меню", callback_data="employer_main_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_vacancy_detail_employer_keyboard(vacancy_id: int, status: str) -> InlineKeyboardMarkup:
    """
    Детальная информация о вакансии для работодателя.
    
    Args:
        vacancy_id: ID вакансии
        status: Статус вакансии
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопки зависят от статуса
    if status == "draft":
        builder.button(text="✅ Опубликовать", callback_data=f"vacancy_publish_{vacancy_id}")
        builder.button(text="✏️ Редактировать", callback_data=f"vacancy_edit_{vacancy_id}")
    elif status == "moderation":
        builder.button(text="⏳ На модерации", callback_data="vacancy_moderation_wait")
    elif status == "active":
        builder.button(text="📊 Статистика", callback_data=f"vacancy_stats_{vacancy_id}")
        builder.button(text="🔒 Закрыть", callback_data=f"vacancy_close_{vacancy_id}")
    elif status == "rejected":
        builder.button(text="✏️ Исправить", callback_data=f"vacancy_edit_{vacancy_id}")
    
    builder.button(text="👥 Отклики", callback_data=f"vacancy_applications_{vacancy_id}")
    builder.button(text="🔙 Назад к списку", callback_data="employer_my_vacancies")
    builder.adjust(2)
    return builder.as_markup()


def get_vacancy_statistics_keyboard(vacancy_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для статистики вакансии"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить", callback_data=f"vacancy_stats_{vacancy_id}")
    builder.button(text="🔙 Назад", callback_data=f"employer_vacancy_{vacancy_id}")
    builder.adjust(2)
    return builder.as_markup()


def get_applications_list_keyboard(applications: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    """
    Список откликов на вакансию.
    
    Args:
        applications: Список кортежей (application_id, applicant_name)
    """
    builder = InlineKeyboardBuilder()
    
    for app_id, name in applications:
        builder.button(text=f"👤 {name}", callback_data=f"application_{app_id}")
    
    builder.button(text="🔙 Назад к вакансии", callback_data="employer_my_vacancies")
    builder.adjust(1)
    return builder.as_markup()


def get_application_detail_keyboard(application_id: int, vacancy_id: int) -> InlineKeyboardMarkup:
    """Детальный просмотр отклика"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Принять", callback_data=f"app_accept_{application_id}")
    builder.button(text="❌ Отклонить", callback_data=f"app_reject_{application_id}")
    builder.button(text="📩 Написать", callback_data=f"app_message_{application_id}")
    builder.button(text="🔙 Назад к откликам", callback_data=f"vacancy_applications_{vacancy_id}")
    builder.adjust(2)
    return builder.as_markup()


def get_company_settings_keyboard() -> InlineKeyboardMarkup:
    """Настройки компании"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить контакты", callback_data="settings_edit_contacts")
    builder.button(text="📄 Информация о компании", callback_data="settings_company_info")
    builder.button(text="🔙 Назад в меню", callback_data="employer_main_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_moderation_decision_keyboard(vacancy_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для модератора: approve/reject"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Одобрить", callback_data=f"mod_approve_{vacancy_id}")
    builder.button(text="❌ Отклонить", callback_data=f"mod_reject_{vacancy_id}")
    builder.adjust(2)
    return builder.as_markup()


def get_back_to_employer_menu_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в меню работодателя"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Меню работодателя", callback_data="employer_main_menu")
    builder.button(text="🏠 Главное меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()
