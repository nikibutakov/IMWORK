"""Файл состояний FSM для онбординга пользователей"""

from aiogram.fsm.state import StatesGroup, State


class OnboardingStudent(StatesGroup):
    """Состояния для онбординга студента"""
    course = State()        # Выбор курса (1-4 или магистратура)
    specialization = State()  # Выбор специализации/направления
    preferences = State()   # Предпочтения по стажировкам


class OnboardingEmployer(StatesGroup):
    """Состояния для онбординга работодателя"""
    company_name = State()      # Название компании
    company_field = State()     # Сфера деятельности компании
    verification_step = State()  # Шаг верификации
