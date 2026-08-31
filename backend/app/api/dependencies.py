from functools import lru_cache

from app.core.config import get_settings
from app.services.study_service import StudyService


@lru_cache
def get_study_service() -> StudyService:
    return StudyService(get_settings())

