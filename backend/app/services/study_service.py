from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.config import Settings
from app.core.errors import GenerationError, InvalidDocumentError
from app.models.schemas import (
    ChatResponse,
    HistoryItem,
    Mcq,
    McqResponse,
    QuizResult,
    QuizScoreResponse,
    QuizSubmission,
    RevisionQuestion,
    RevisionResponse,
    SourceResponse,
    SummaryResponse,
)
from app.services.chunking import TextChunk, chunk_page_text
from app.services.embeddings import EmbeddingProvider, HashEmbeddingProvider
from app.services.llm import LlmProvider, OfflineStudyProvider, create_llm_provider
from app.services.pdf_processor import PdfProcessor
from app.services.vector_store import VectorStore
from app.storage.repository import DatabaseRepository


class StudyService:
    MIN_RELEVANCE = 0.14

    def __init__(
        self,
        settings: Settings,
        repository: DatabaseRepository | None = None,
        embedder: EmbeddingProvider | None = None,
        vector_store: VectorStore | None = None,
        llm: LlmProvider | None = None,
        pdf_processor: PdfProcessor | None = None,
    ) -> None:
        self.settings = settings
        settings.data_path.mkdir(parents=True, exist_ok=True)
        settings.upload_path.mkdir(parents=True, exist_ok=True)
        self.repository = repository or DatabaseRepository(settings.resolved_database_url)
        self.embedder = embedder or HashEmbeddingProvider()
        self.vector_store = vector_store or VectorStore(settings.vector_path)
        self.llm = llm or create_llm_provider(settings)
        self.pdf_processor = pdf_processor or PdfProcessor()

    def ingest_pdf(self, filename: str | None, file_bytes: bytes) -> dict[str, Any]:
        maximum = self.settings.max_upload_mb * 1024 * 1024
        if len(file_bytes) > maximum:
            raise InvalidDocumentError(
                f"This file is larger than the {self.settings.max_upload_mb} MB upload limit."
            )
        safe_filename = self.pdf_processor.safe_filename(filename)
        if not safe_filename.lower().endswith(".pdf"):
            raise InvalidDocumentError("Only PDF files can be uploaded.")
        pages = self.pdf_processor.extract_pages(file_bytes)
        document_id = str(uuid4())
        chunks: list[TextChunk] = []
        for page_number, page_text in pages:
            chunks.extend(chunk_page_text(page_text, document_id, safe_filename, page_number))
        if not chunks:
            raise InvalidDocumentError(
                "No readable text was found. This may be a scanned or image-only PDF."
            )
        embeddings = self.embedder.embed([chunk.text for chunk in chunks])
        self.vector_store.save(document_id, embeddings, chunks)
        (self.settings.upload_path / f"{document_id}.pdf").write_bytes(file_bytes)
        return self.repository.add_document(
            document_id, safe_filename, len(pages), len(chunks)
        )

    def list_documents(self) -> list[dict[str, Any]]:
        return self.repository.list_documents()

    def _document_and_chunks(self, document_id: str) -> tuple[dict[str, Any], list[TextChunk]]:
        document = self.repository.get_document(document_id)
        chunks = self.vector_store.load_chunks(document_id)
        if not chunks:
            raise InvalidDocumentError("The document index is unavailable. Please upload it again.")
        return document, chunks

    def _full_context(self, document_id: str, limit: int = 18000) -> str:
        _, chunks = self._document_and_chunks(document_id)
        context = "\n\n".join(
            f"[Page {chunk.page}] {chunk.text}" for chunk in chunks
        )
        return context[:limit]

    @staticmethod
    def _source(chunk: TextChunk, score: float) -> SourceResponse:
        excerpt = chunk.text[:220].rstrip()
        return SourceResponse(
            filename=chunk.filename,
            page=chunk.page,
            chunk_id=chunk.id,
            excerpt=f"{excerpt}{'…' if len(chunk.text) > len(excerpt) else ''}",
            score=round(score, 3),
        )

    async def answer_question(self, document_id: str, question: str) -> ChatResponse:
        self._document_and_chunks(document_id)
        query = self.embedder.embed([question])[0]
        matches = self.vector_store.search(document_id, query, limit=4)
        grounded_matches = [
            (chunk, score) for chunk, score in matches if score >= self.MIN_RELEVANCE
        ]
        if not grounded_matches:
            return ChatResponse(
                answer="I couldn't find enough information about this topic in the uploaded material.",
                sources=[],
                grounded=False,
            )
        context = "\n\n".join(
            f"Source: {chunk.filename}, page {chunk.page}\n{chunk.text}"
            for chunk, _ in grounded_matches
        )
        answer = await self.llm.answer(question, context)
        document = self.repository.get_document(document_id)
        self.repository.add_history("Asked AI", document_id, document["filename"], question[:100])
        return ChatResponse(
            answer=answer,
            sources=[self._source(chunk, score) for chunk, score in grounded_matches],
            grounded=True,
        )

    async def generate_summary(self, document_id: str, length: str) -> SummaryResponse:
        document = self.repository.get_document(document_id)
        context = self._full_context(document_id)
        instruction = (
            "Return keys overview, key_points, important_concepts, and exam_focus. "
            f"Make a {length} summary. Every list must contain concise strings."
        )
        payload = await self.llm.generate_json("summary", context, instruction)
        try:
            summary = SummaryResponse(**payload)
        except Exception as error:
            raise GenerationError("Could not create a structured summary.") from error
        self.repository.add_history("Generated summary", document_id, document["filename"], length)
        return summary

    @staticmethod
    def _sentences(context: str) -> list[str]:
        values = re.split(r"(?<=[.!?])\s+", context.replace("\n", " "))
        return [value.strip() for value in values if len(value.strip()) > 35]

    @staticmethod
    def _topic(sentence: str) -> str:
        words = re.findall(r"[A-Za-z][A-Za-z-]{2,}", sentence)
        ignored = {"the", "and", "that", "with", "from", "this", "which", "into", "for"}
        selected = [word for word in words if word.lower() not in ignored][:6]
        return " ".join(selected) or "this material"

    def _offline_mcqs(self, context: str, count: int, difficulty: str) -> list[Mcq]:
        sentences = self._sentences(context)
        if not sentences:
            raise GenerationError("The document does not contain enough text to create MCQs.")
        questions: list[Mcq] = []
        for index in range(count):
            fact = sentences[index % len(sentences)][:210].rstrip()
            topic = self._topic(fact)
            correct = index % 4
            options = [
                "It is not discussed in the uploaded material.",
                "It is always unrelated to the topic.",
                "It can be ignored for examination preparation.",
                "It is defined only by an external source.",
            ]
            options[correct] = fact
            questions.append(
                Mcq(
                    id=f"mcq-{index + 1}",
                    question=f"Which statement is supported by the material about {topic}?",
                    options=options,
                    correct_answer=correct,
                    explanation=f"The material states: {fact}",
                )
            )
        return questions

    async def generate_mcqs(
        self, document_id: str, count: int, difficulty: str
    ) -> McqResponse:
        document = self.repository.get_document(document_id)
        context = self._full_context(document_id)
        if isinstance(self.llm, OfflineStudyProvider):
            questions = self._offline_mcqs(context, count, difficulty)
        else:
            instruction = (
                f"Create exactly {count} {difficulty} MCQs. Return an object with a questions "
                "array. Each item must have id, question, options (exactly four strings), "
                "correct_answer (zero-based option index), and explanation."
            )
            payload = await self.llm.generate_json("mcqs", context, instruction)
            try:
                questions = [Mcq(**item) for item in payload["questions"]][:count]
            except (KeyError, TypeError, ValueError) as error:
                raise GenerationError("Could not create valid MCQs.") from error
            if len(questions) != count:
                raise GenerationError("The AI returned fewer MCQs than requested. Try again.")
        self.repository.add_history(
            "Generated MCQs", document_id, document["filename"], f"{count} {difficulty}"
        )
        return McqResponse(document_id=document_id, questions=questions)

    def _offline_revision(
        self, context: str, count: int, difficulty: str
    ) -> list[RevisionQuestion]:
        sentences = self._sentences(context)
        if not sentences:
            raise GenerationError("The document does not contain enough text for revision.")
        templates = [
            ("short-answer", "Define or describe {topic}."),
            ("conceptual", "Explain the significance of {topic} using the material."),
            ("long-answer", "Discuss {topic} in detail and include the important points."),
        ]
        return [
            RevisionQuestion(
                id=f"revision-{index + 1}",
                question=templates[index % len(templates)][1].format(
                    topic=self._topic(sentences[index % len(sentences)])
                ),
                type=templates[index % len(templates)][0],
                difficulty=difficulty,
            )
            for index in range(count)
        ]

    async def generate_revision(
        self, document_id: str, count: int, difficulty: str
    ) -> RevisionResponse:
        document = self.repository.get_document(document_id)
        context = self._full_context(document_id)
        if isinstance(self.llm, OfflineStudyProvider):
            questions = self._offline_revision(context, count, difficulty)
        else:
            instruction = (
                f"Create exactly {count} {difficulty} revision questions. Return an object with "
                "a questions array. Each item must have id, question, type (short-answer, "
                "conceptual, or long-answer), and difficulty."
            )
            payload = await self.llm.generate_json("revision", context, instruction)
            try:
                questions = [RevisionQuestion(**item) for item in payload["questions"]][:count]
            except (KeyError, TypeError, ValueError) as error:
                raise GenerationError("Could not create valid revision questions.") from error
        self.repository.add_history(
            "Generated revision", document_id, document["filename"], difficulty
        )
        return RevisionResponse(questions=questions)

    def score_quiz(self, submission: QuizSubmission) -> QuizScoreResponse:
        document = self.repository.get_document(submission.document_id)
        results: list[QuizResult] = []
        for question in submission.questions:
            selected = submission.answers.get(question.id)
            results.append(
                QuizResult(
                    question_id=question.id,
                    selected_answer=selected,
                    correct_answer=question.correct_answer,
                    is_correct=selected == question.correct_answer,
                    explanation=question.explanation,
                )
            )
        score = sum(result.is_correct for result in results)
        total = len(results)
        self.repository.add_history(
            "Completed quiz",
            submission.document_id,
            document["filename"],
            f"Score {score}/{total}",
        )
        return QuizScoreResponse(
            score=score,
            total=total,
            percentage=round((score / total) * 100, 1) if total else 0,
            results=results,
        )

    def history(self) -> list[HistoryItem]:
        return [HistoryItem(**item) for item in self.repository.list_history()]
