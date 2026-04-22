"""Клавиатуры для главного меню и онбординга"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_role_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора роли при старте"""
    builder = InlineKeyboardBuilder()
    builder.button(text="👨‍🎓 Я студент", callback_data="role_student")
    builder.button(text="🏢 Я работодатель", callback_data="role_employer")
    builder.adjust(1)
    return builder.as_markup()


def get_student_main_menu() -> InlineKeyboardMarkup:
    """Главное меню для студента"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Найти стажировку", callback_data="student_find_internship")
    builder.button(text="🎓 Карьерный центр", callback_data="student_career_center")
    builder.button(text="💬 Форум", callback_data="student_forum")
    builder.button(text="👤 Мой профиль", callback_data="student_profile")
    builder.adjust(1)
    return builder.as_markup()


def get_employer_main_menu() -> InlineKeyboardMarkup:
    """Главное меню для работодателя"""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Разместить вакансию", callback_data="employer_post_vacancy")
    builder.button(text="📊 Мои вакансии", callback_data="employer_my_vacancies")
    builder.button(text="💳 Тарифы", callback_data="employer_tariffs")
    builder.button(text="⚙️ Настройки", callback_data="employer_settings")
    builder.adjust(1)
    return builder.as_markup()


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой возврата в меню"""
    builder = InlineKeyboardBuilder()
    builder.button(text="↩️ Вернуться в меню", callback_data="back_to_menu")
    return builder.as_markup()


def get_course_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора курса для студента"""
    builder = InlineKeyboardBuilder()
    builder.button(text="1 курс", callback_data="course_1")
    builder.button(text="2 курс", callback_data="course_2")
    builder.button(text="3 курс", callback_data="course_3")
    builder.button(text="4 курс", callback_data="course_4")
    builder.button(text="Магистратура", callback_data="course_masters")
    builder.button(text="↩️ Вернуться в меню", callback_data="back_to_menu")
    builder.adjust(2)
    return builder.as_markup()


def get_specialization_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора специализации"""
    builder = InlineKeyboardBuilder()
    specializations = [
        "Программирование",
        "Дизайн",
        "Маркетинг",
        "Аналитика",
        "Менеджмент",
        "Другое"
    ]
    for spec in specializations:
        builder.button(text=spec, callback_data=f"spec_{spec}")
    builder.button(text="↩️ Вернуться в меню", callback_data="back_to_menu")
    builder.adjust(2)
    return builder.as_markup()


def get_company_field_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора сферы деятельности компании"""
    builder = InlineKeyboardBuilder()
    fields = [
        "IT и разработка",
        "Дизайн и креатив",
        "Маркетинг и реклама",
        "Финансы и банки",
        "Образование",
        "Другое"
    ]
    for field in fields:
        builder.button(text=field, callback_data=f"field_{field}")
    builder.button(text="↩️ Вернуться в меню", callback_data="back_to_menu")
    builder.adjust(2)
    return builder.as_markup()


def get_contact_admin_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для связи с админом (верификация работодателя)"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📩 Написать админу", url="https://t.me/admin_placeholder")
    builder.button(text="↩️ Вернуться в меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()
