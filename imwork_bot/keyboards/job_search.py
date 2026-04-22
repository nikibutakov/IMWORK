"""Клавиатуры для поиска вакансий и фильтров"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_job_filters_keyboard(
    selected_sphere: str | None = None,
    selected_format: str | None = None,
    selected_salary: str | None = None,
) -> InlineKeyboardMarkup:
    """
    Клавиатура с фильтрами для поиска вакансий.
    Показывает текущие выбранные фильтры.
    """
    builder = InlineKeyboardBuilder()
    
    # Фильтр по сфере
    sphere_btn = f"✅ Сфера: {selected_sphere}" if selected_sphere else "🔷 Сфера деятельности"
    builder.button(text=sphere_btn, callback_data="filter_sphere")
    
    # Фильтр по формату работы
    format_btn = f"✅ Формат: {selected_format}" if selected_format else "🔷 Формат работы"
    builder.button(text=format_btn, callback_data="filter_format")
    
    # Фильтр по оплате
    salary_btn = f"✅ Оплата: {selected_salary}" if selected_salary else "🔷 Оплата"
    builder.button(text=salary_btn, callback_data="filter_salary")
    
    # Кнопки применения и сброса
    builder.button(text="🔍 Применить фильтры", callback_data="filter_apply")
    builder.button(text="🔄 Сбросить фильтры", callback_data="filter_reset")
    builder.button(text="🔙 Назад в меню", callback_data="back_to_menu")
    
    builder.adjust(1)
    return builder.as_markup()


def get_sphere_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора сферы деятельности"""
    builder = InlineKeyboardBuilder()
    spheres = [
        "IT и разработка",
        "Дизайн и креатив",
        "Маркетинг и реклама",
        "Финансы и банки",
        "Образование",
        "Продажи",
        "Менеджмент",
        "Другое"
    ]
    for sphere in spheres:
        builder.button(text=sphere, callback_data=f"sphere_{sphere}")
    builder.button(text="↩️ Назад к фильтрам", callback_data="filter_back")
    builder.adjust(2)
    return builder.as_markup()


def get_format_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора формата работы"""
    builder = InlineKeyboardBuilder()
    formats = [
        "Удаленно",
        "Офис",
        "Гибрид",
        "Проектная работа",
        "Стажировка"
    ]
    for fmt in formats:
        builder.button(text=fmt, callback_data=f"format_{fmt}")
    builder.button(text="↩️ Назад к фильтрам", callback_data="filter_back")
    builder.adjust(2)
    return builder.as_markup()


def get_salary_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора уровня оплаты"""
    builder = InlineKeyboardBuilder()
    salaries = [
        "Без оплаты",
        "До 30 000 ₽",
        "30 000 - 60 000 ₽",
        "60 000 - 100 000 ₽",
        "От 100 000 ₽",
        "По договоренности"
    ]
    for salary in salaries:
        builder.button(text=salary, callback_data=f"salary_{salary}")
    builder.button(text="↩️ Назад к фильтрам", callback_data="filter_back")
    builder.adjust(1)
    return builder.as_markup()


def get_vacancy_list_keyboard(vacancy_ids: list[int], page: int = 0, has_next: bool = False, has_prev: bool = False) -> InlineKeyboardMarkup:
    """
    Клавиатура для списка вакансий с пагинацией.
    
    Args:
        vacancy_ids: Список ID вакансий для отображения
        page: Текущая страница (0-indexed)
        has_next: Есть ли следующая страница
        has_prev: Есть ли предыдущая страница
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопки для каждой вакансии
    for vid in vacancy_ids:
        builder.button(text=f"📄 Вакансия #{vid}", callback_data=f"vacancy_{vid}")
    
    # Пагинация
    nav_buttons = []
    if has_prev:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page_{page - 1}"))
    if has_next:
        nav_buttons.append(InlineKeyboardButton(text="➡️ Вперед", callback_data=f"page_{page + 1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.button(text="🔙 Назад к фильтрам", callback_data="filter_back")
    builder.adjust(1)
    return builder.as_markup()


def get_vacancy_detail_keyboard(vacancy_id: int, is_favorite: bool = False) -> InlineKeyboardMarkup:
    """
    Клавиатура для карточки вакансии.
    
    Args:
        vacancy_id: ID вакансии
        is_favorite: Добавлена ли вакансия в избранное
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопка избранного
    fav_text = "⭐️ Убрать из избранного" if is_favorite else "⭐️ В избранное"
    fav_callback = "fav_remove" if is_favorite else "fav_add"
    builder.button(text=fav_text, callback_data=f"{fav_callback}_{vacancy_id}")
    
    # Кнопка отклика
    builder.button(text="📤 Откликнуться", callback_data=f"apply_{vacancy_id}")
    
    # Кнопка назад
    builder.button(text="🔙 Назад к списку", callback_data="back_to_list")
    
    builder.adjust(1)
    return builder.as_markup()


def get_application_type_keyboard(vacancy_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора типа отклика.
    
    Args:
        vacancy_id: ID вакансии
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="📄 Из профиля", callback_data=f"apply_profile_{vacancy_id}")
    builder.button(text="📁 Загрузить новый файл", callback_data=f"apply_upload_{vacancy_id}")
    builder.button(text="💬 Написать HR", callback_data=f"apply_message_{vacancy_id}")
    builder.button(text="❌ Отмена", callback_data=f"vacancy_{vacancy_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_career_center_categories_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура категорий карьерного центра"""
    builder = InlineKeyboardBuilder()
    categories = [
        ("📝 Резюме и сопроводительные", "cat_resume"),
        ("🎤 Собеседования", "cat_interviews"),
        ("📈 Карьерный рост", "cat_growth"),
        ("💼 Поиск работы", "cat_job_search"),
    ]
    for text, callback in categories:
        builder.button(text=text, callback_data=callback)
    builder.button(text="🔙 Назад в меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_material_list_keyboard(materials: list[tuple[int, str]], category_callback: str) -> InlineKeyboardMarkup:
    """
    Клавиатура списка материалов.
    
    Args:
        materials: Список кортежей (id, title)
        category_callback: Callback для возврата к категории
    """
    builder = InlineKeyboardBuilder()
    
    for mat_id, title in materials:
        # Обрезаем длинные заголовки
        short_title = title[:40] + "..." if len(title) > 40 else title
        builder.button(text=f"📄 {short_title}", callback_data=f"material_{mat_id}")
    
    builder.button(text="↩️ Назад к категориям", callback_data=category_callback)
    builder.adjust(1)
    return builder.as_markup()


def get_material_detail_keyboard(material_id: int, category_callback: str) -> InlineKeyboardMarkup:
    """
    Клавиатура для просмотра материала.
    
    Args:
        material_id: ID материала
        category_callback: Callback для возврата к категории
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="📥 Скачать", callback_data=f"material_download_{material_id}")
    builder.button(text="💾 Сохранить", callback_data=f"material_save_{material_id}")
    builder.button(text="❓ Задать вопрос куратору", callback_data=f"material_question_{material_id}")
    builder.button(text="↩️ Назад к списку", callback_data=category_callback)
    builder.adjust(1)
    return builder.as_markup()


def get_back_to_vacancy_list_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой возврата к списку вакансий"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад к списку вакансий", callback_data="back_to_list")
    builder.button(text="🏠 В главное меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()
