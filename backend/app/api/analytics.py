from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_analytics_service
from app.models.schemas import (
    AchievementItem,
    AnalyticsOverviewResponse,
    DailyActivityItem,
    DocumentAnalyticsItem,
    FlashcardAnalyticsResponse,
    QuizAnalyticsResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def get_overview(
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsOverviewResponse:
    return service.get_overview()


@router.get("/activity", response_model=list[DailyActivityItem])
def get_activity(
    days: int = Query(default=30, ge=1, le=365),
    document_id: str | None = Query(default=None),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[DailyActivityItem]:
    if document_id:
        service.repository.get_document(document_id)
    return service.get_activity(days=days, document_id=document_id)


@router.get("/quiz", response_model=QuizAnalyticsResponse)
def get_quiz_analytics(
    document_id: str | None = Query(default=None),
    service: AnalyticsService = Depends(get_analytics_service),
) -> QuizAnalyticsResponse:
    if document_id:
        service.repository.get_document(document_id)
    return service.get_quiz_analytics(document_id=document_id)


@router.get("/flashcards", response_model=FlashcardAnalyticsResponse)
def get_flashcard_analytics(
    document_id: str | None = Query(default=None),
    service: AnalyticsService = Depends(get_analytics_service),
) -> FlashcardAnalyticsResponse:
    if document_id:
        service.repository.get_document(document_id)
    return service.get_flashcard_analytics(document_id=document_id)


@router.get("/documents", response_model=list[DocumentAnalyticsItem])
def get_documents_analytics(
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[DocumentAnalyticsItem]:
    return service.get_documents_analytics()


@router.get("/achievements", response_model=list[AchievementItem])
def get_achievements(
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[AchievementItem]:
    return service.get_achievements()
