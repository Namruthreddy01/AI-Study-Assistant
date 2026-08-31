from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: str
    filename: str
    pages: int
    chunks: int
    status: Literal["processed", "failed"]
    created_at: datetime


class SourceResponse(BaseModel):
    filename: str
    page: int
    chunk_id: str
    excerpt: str
    score: float


class ChatRequest(BaseModel):
    document_id: str
    question: str = Field(min_length=3, max_length=1000)


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]
    grounded: bool


class SummaryRequest(BaseModel):
    document_id: str
    length: Literal["short", "detailed"] = "short"


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
