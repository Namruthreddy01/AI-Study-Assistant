from functools import lru_cache

from app.core.config import get_settings
from app.services.analytics_service import AnalyticsService
from app.services.study_service import StudyService


@lru_cache
def get_study_service() -> StudyService:
    return StudyService(get_settings())


@lru_cache
def get_analytics_service() -> AnalyticsService:
    return AnalyticsService(get_study_service().repository)


