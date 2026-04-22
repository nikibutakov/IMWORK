"""Файл состояний FSM для онбординга пользователей, откликов и создания вакансий"""

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


class ApplicationState(StatesGroup):
    """Состояния для процесса отклика на вакансию"""
    selecting_type = State()      # Выбор типа отклика
    uploading_resume = State()    # Загрузка резюме
    writing_message = State()     # Написание сообщения HR


class VacancyCreationState(StatesGroup):
    """Состояния для пошагового создания вакансии работодателем"""
    position_name = State()     # Название позиции
    tasks = State()             # Описание задач
    requirements = State()      # Требования к кандидату
    conditions = State()        # Условия работы
    salary_input = State()      # Зарплата (опционально)
    category_select = State()   # Выбор категории
    tariff_select = State()     # Выбор тарифа


class CompanySettingsState(StatesGroup):
    """Состояния для редактирования настроек компании"""
    edit_contacts = State()     # Редактирование контактов
    edit_description = State()  # Редактирование описания компании


class ModeratorActionState(StatesGroup):
    """Состояния для действий модератора при отклонении вакансии"""
    reject_comment = State()    # Ввод комментария при отклонении


class QuestionToCuratorState(StatesGroup):
    """Состояния для вопроса куратору из карьерного центра"""
    question_text = State()     # Текст вопроса
