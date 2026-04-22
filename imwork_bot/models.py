from datetime import datetime
from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class UserRole(str, Enum):
    """Роли пользователей в системе"""
    STUDENT = "student"
    MENTOR = "mentor"
    MODERATOR = "moderator"
    ADMIN = "admin"


class VacancyStatus(str, Enum):
    """Статусы вакансий"""
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    MODERATION = "moderation"
    REJECTED = "rejected"


class ApplicationStatus(str, Enum):
    """Статусы откликов на вакансии"""
    PENDING = "pending"
    REVIEWED = "reviewed"
    INTERVIEW = "interview"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class TariffType(str, Enum):
    """Типы тарифов"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    VIP = "vip"


class User(Base):
    """Таблица пользователей"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String(50), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)

    # Профиль пользователя
    role = Column(String(20), default=UserRole.STUDENT.value, nullable=False)
    course = Column(String(100), nullable=True)  # Название курса
    direction = Column(String(100), nullable=True)  # Направление обучения

    # Тариф и доступы
    tariff = Column(String(20), default=TariffType.FREE.value, nullable=False)
    tariff_expires_at = Column(DateTime, nullable=True)

    # Статусы
    is_active = Column(Boolean, default=True, nullable=False)
    is_banned = Column(Boolean, default=False, nullable=False)

    # Даты
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Связи
    vacancies = relationship("Vacancy", back_populates="author", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="applicant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, role={self.role})>"


class Vacancy(Base):
    """Таблица вакансий"""
    __tablename__ = "vacancies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Информация о вакансии
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    conditions = Column(Text, nullable=True)
    salary = Column(String(100), nullable=True)  # Диапазон или фиксированная сумма

    # Категоризация
    category = Column(String(50), nullable=True)  # Категория вакансии
    direction = Column(String(100), nullable=True)  # Направление

    # Статус и модерация
    status = Column(String(20), default=VacancyStatus.DRAFT.value, nullable=False)
    moderation_comment = Column(Text, nullable=True)  # Комментарий модератора при отклонении
    moderated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    moderated_at = Column(DateTime, nullable=True)

    # Даты
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # Дата истечения вакансии

    # Связи
    author = relationship("User", back_populates="vacancies", foreign_keys=[author_id])
    applications = relationship("Application", back_populates="vacancy", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Vacancy(id={self.id}, title={self.title}, status={self.status})>"


class Application(Base):
    """Таблица откликов на вакансии"""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vacancy_id = Column(Integer, ForeignKey("vacancies.id"), nullable=False)
    applicant_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Данные отклика
    cover_letter = Column(Text, nullable=True)  # Сопроводительное письмо
    resume_link = Column(String(500), nullable=True)  # Ссылка на резюме
    portfolio_link = Column(String(500), nullable=True)  # Ссылка на портфолио

    # Статус
    status = Column(String(20), default=ApplicationStatus.PENDING.value, nullable=False)
    status_comment = Column(Text, nullable=True)  # Комментарий к статусу

    # Даты
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)

    # Связи
    vacancy = relationship("Vacancy", back_populates="applications")
    applicant = relationship("User", back_populates="applications")

    def __repr__(self):
        return f"<Application(id={self.id}, vacancy_id={self.vacancy_id}, status={self.status})>"


class CareerMaterial(Base):
    """Таблица материалов по карьере (статьи, гайды, видео)"""
    __tablename__ = "career_materials"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Информация о материале
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)  # Полный текст или ссылка
    material_type = Column(String(20), nullable=True)  # article, video, guide, template

    # Категоризация
    category = Column(String(50), nullable=True)
    direction = Column(String(100), nullable=True)
    tags = Column(String(500), nullable=True)  # Теги через запятую

    # Доступ
    is_free = Column(Boolean, default=True, nullable=False)  # Бесплатный или для тарифа
    required_tariff = Column(String(20), nullable=True)  # Минимальный требуемый тариф

    # Статус модерации
    is_published = Column(Boolean, default=False, nullable=False)
    moderation_status = Column(String(20), default="pending", nullable=False)
    moderated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    moderated_at = Column(DateTime, nullable=True)

    # Метрики
    views_count = Column(Integer, default=0, nullable=False)

    # Даты
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<CareerMaterial(id={self.id}, title={self.title}, type={self.material_type})>"