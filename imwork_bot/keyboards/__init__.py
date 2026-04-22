"""__init__.py для модуля keyboards"""

from .main_menu import (
    get_role_selection_keyboard,
    get_student_main_menu,
    get_employer_main_menu,
    get_back_to_menu_keyboard,
    get_course_selection_keyboard,
    get_specialization_keyboard,
    get_company_field_keyboard,
    get_contact_admin_keyboard,
)

__all__ = [
    "get_role_selection_keyboard",
    "get_student_main_menu",
    "get_employer_main_menu",
    "get_back_to_menu_keyboard",
    "get_course_selection_keyboard",
    "get_specialization_keyboard",
    "get_company_field_keyboard",
    "get_contact_admin_keyboard",
]
