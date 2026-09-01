from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_study_service
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    FlashcardGenerateRequest,
    FlashcardListResponse,
    FlashcardResponse,
    FlashcardReviewRequest,
    FlashcardReviewResponse,
    HistoryItem,
    McqRequest,
    McqResponse,
    QuizScoreResponse,
    QuizSubmission,
    RevisionRequest,
    RevisionResponse,
    SummaryRequest,
    SummaryResponse,
)
from app.services.study_service import StudyService


router = APIRouter(prefix="/api/study", tags=["Study"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest, service: StudyService = Depends(get_study_service)
) -> ChatResponse:
    return await service.answer_question(request.document_id, request.question)


@router.post("/summary", response_model=SummaryResponse)
async def summary(
    request: SummaryRequest, service: StudyService = Depends(get_study_service)
) -> SummaryResponse:
    return await service.generate_summary(request.document_id, request.length)


@router.post("/mcqs", response_model=McqResponse)
async def mcqs(
    request: McqRequest, service: StudyService = Depends(get_study_service)
) -> McqResponse:
    return await service.generate_mcqs(
        request.document_id, request.count, request.difficulty
    )


@router.post("/revision", response_model=RevisionResponse)
async def revision(
    request: RevisionRequest, service: StudyService = Depends(get_study_service)
) -> RevisionResponse:
    return await service.generate_revision(
        request.document_id, request.count, request.difficulty
    )


@router.post("/flashcards", response_model=list[FlashcardResponse])
async def generate_flashcards(
    request: FlashcardGenerateRequest, service: StudyService = Depends(get_study_service)
) -> list[FlashcardResponse]:
    return await service.generate_flashcards(
        request.document_id, request.count, request.difficulty
    )


@router.get("/flashcards", response_model=FlashcardListResponse)
def list_flashcards(
    document_id: str | None = Query(default=None),
    due_only: bool = Query(default=False),
    service: StudyService = Depends(get_study_service),
) -> FlashcardListResponse:
    return service.list_flashcards(document_id=document_id, due_only=due_only)


@router.post("/flashcards/{flashcard_id}/review", response_model=FlashcardReviewResponse)
def review_flashcard(
    flashcard_id: str,
    request: FlashcardReviewRequest,
    service: StudyService = Depends(get_study_service),
) -> FlashcardReviewResponse:
    return service.review_flashcard(flashcard_id, request.rating)


@router.post("/quiz/score", response_model=QuizScoreResponse)
def score_quiz(
    request: QuizSubmission, service: StudyService = Depends(get_study_service)
) -> QuizScoreResponse:
    return service.score_quiz(request)


@router.get("/history", response_model=list[HistoryItem])
def history(service: StudyService = Depends(get_study_service)) -> list[HistoryItem]:
    return service.history()

