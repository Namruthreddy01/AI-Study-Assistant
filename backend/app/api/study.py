from fastapi import APIRouter, Depends

from app.api.dependencies import get_study_service
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
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


@router.post("/quiz/score", response_model=QuizScoreResponse)
def score_quiz(
    request: QuizSubmission, service: StudyService = Depends(get_study_service)
) -> QuizScoreResponse:
    return service.score_quiz(request)


@router.get("/history", response_model=list[HistoryItem])
def history(service: StudyService = Depends(get_study_service)) -> list[HistoryItem]:
    return service.history()

