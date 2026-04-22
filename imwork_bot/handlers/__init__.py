"""__init__.py для модуля handlers"""

from .onboarding import router as onboarding_router
from .student_jobs import router as student_jobs_router
from .career_center import router as career_center_router
from .employer_jobs import router as employer_jobs_router
from .moderation import router as moderation_router

__all__ = [
    "onboarding_router",
    "student_jobs_router",
    "career_center_router",
    "employer_jobs_router",
    "moderation_router",
]
