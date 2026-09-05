from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class DocumentResponse(BaseModel):
    id: str
    filename: str
    pages: int
    chunks: int
    status: Literal["processed", "failed"]
    created_at: datetime


class DocumentDetailResponse(BaseModel):
    id: str
    filename: str
    pages: int
    chunks: int
    status: Literal["processed", "failed"]
    created_at: datetime
    flashcard_count: int = 0


class DocumentDeleteResponse(BaseModel):
    id: str
    filename: str
    deleted: bool = True
    message: str


class SourceResponse(BaseModel):
    filename: str
    page: int
    chunk_id: str
    excerpt: str
    score: float


class ChatRequest(BaseModel):
    document_id: str | None = None
    document_ids: list[str] = Field(default_factory=list)
    question: str = Field(min_length=3, max_length=1000)

    @model_validator(mode="after")
    def validate_and_normalize_ids(self) -> "ChatRequest":
        ids = list(self.document_ids)
        if self.document_id and self.document_id not in ids:
            ids.insert(0, self.document_id)
        unique_ids = list(dict.fromkeys(ids))
        if not unique_ids:
            raise ValueError("At least one document must be selected.")
        self.document_ids = unique_ids
        if not self.document_id:
            self.document_id = unique_ids[0]
        return self


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]
    grounded: bool


class SummaryRequest(BaseModel):
    document_id: str | None = None
    document_ids: list[str] = Field(default_factory=list)
    length: Literal["short", "detailed"] = "short"

    @model_validator(mode="after")
    def validate_and_normalize_ids(self) -> "SummaryRequest":
        ids = list(self.document_ids)
        if self.document_id and self.document_id not in ids:
            ids.insert(0, self.document_id)
        unique_ids = list(dict.fromkeys(ids))
        if not unique_ids:
            raise ValueError("At least one document must be selected.")
        self.document_ids = unique_ids
        if not self.document_id:
            self.document_id = unique_ids[0]
        return self


class SummaryResponse(BaseModel):
    overview: str
    key_points: list[str]
    important_concepts: list[str]
    exam_focus: list[str]


class McqRequest(BaseModel):
    document_id: str
    count: int = Field(default=10, ge=1, le=20)
    difficulty: Literal["easy", "medium", "hard"] = "medium"


class Mcq(BaseModel):
    id: str
    question: str
    options: list[str] = Field(min_length=4, max_length=4)
    correct_answer: int = Field(ge=0, le=3)
    explanation: str


class McqResponse(BaseModel):
    document_id: str
    questions: list[Mcq]


class RevisionRequest(BaseModel):
    document_id: str
    difficulty: Literal["easy", "medium", "hard", "exam"] = "medium"
    count: int = Field(default=8, ge=1, le=20)


class RevisionQuestion(BaseModel):
    id: str
    question: str
    type: Literal["short-answer", "conceptual", "long-answer"]
    difficulty: str


class RevisionResponse(BaseModel):
    questions: list[RevisionQuestion]


class QuizSubmission(BaseModel):
    document_id: str
    questions: list[Mcq] = Field(min_length=1)
    answers: dict[str, int]


class QuizResult(BaseModel):
    question_id: str
    selected_answer: int | None
    correct_answer: int
    is_correct: bool
    explanation: str


class QuizScoreResponse(BaseModel):
    score: int
    total: int
    percentage: float
    results: list[QuizResult]


class HistoryItem(BaseModel):
    id: str
    activity: str
    document_id: str
    document_name: str
    created_at: datetime
    detail: str


class FlashcardGenerateRequest(BaseModel):
    document_id: str
    count: int = Field(default=10, ge=1, le=30)
    difficulty: Literal["easy", "medium", "hard"] = "medium"


class FlashcardResponse(BaseModel):
    id: str
    document_id: str
    question: str
    answer: str
    source_page: int
    source_filename: str
    difficulty: str
    repetitions: int
    ease_factor: float
    interval_days: int
    next_review: datetime
    last_reviewed: datetime | None = None
    created_at: datetime
    is_due: bool = True


class FlashcardListResponse(BaseModel):
    document_id: str | None = None
    cards: list[FlashcardResponse]
    total: int
    due_count: int
    new_count: int
    learning_count: int


class FlashcardReviewRequest(BaseModel):
    rating: Literal["again", "hard", "good", "easy"]


class FlashcardReviewResponse(BaseModel):
    card: FlashcardResponse
    rating: str
    previous_interval: int
    new_interval: int
    previous_ease_factor: float
    new_ease_factor: float
    next_review: datetime


class AnalyticsOverviewResponse(BaseModel):
    total_study_sessions: int
    questions_asked: int
    quizzes_completed: int
    flashcards_reviewed: int
    overall_quiz_accuracy: float
    current_streak: int
    longest_streak: int
    active_study_days: int
    last_study_date: str | None = None
    total_documents: int
    total_flashcards: int
    mastery_score: float


class DailyActivityItem(BaseModel):
    date: str
    study_sessions: int
    quiz_attempts: int
    flashcard_reviews: int
    questions_asked: int


class QuizAttemptItem(BaseModel):
    id: str
    document_id: str
    document_name: str
    score: int
    total: int
    accuracy: float
    created_at: datetime


class QuizAnalyticsResponse(BaseModel):
    quizzes_completed: int
    total_questions: int
    correct_answers: int
    incorrect_answers: int
    overall_accuracy: float
    difficulty_breakdown: dict[str, int] = Field(default_factory=dict)
    recent_quizzes: list[QuizAttemptItem] = Field(default_factory=list)


class FlashcardRatingsBreakdown(BaseModel):
    again: int = 0
    hard: int = 0
    good: int = 0
    easy: int = 0


class FlashcardAnalyticsResponse(BaseModel):
    total_cards: int
    new_cards: int
    learning_cards: int
    due_cards: int
    reviewed_cards: int
    total_reviews: int
    ratings: FlashcardRatingsBreakdown
    average_ease_factor: float
    retention_rate: float


class DocumentAnalyticsItem(BaseModel):
    id: str
    filename: str
    pages: int
    chunks: int
    flashcards_count: int
    flashcards_reviewed_count: int
    quizzes_completed: int
    quiz_accuracy: float
    study_sessions: int
    questions_asked: int
    mastery_score: float
    last_studied_at: datetime | None = None


class AchievementItem(BaseModel):
    id: str
    title: str
    description: str
    icon: str
    unlocked: bool
    progress: int
    unlocked_at: datetime | None = None

