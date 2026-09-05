from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, Float, Integer, String, Text, create_engine, delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.core.errors import NotFoundError, StudyAssistantError


class Base(DeclarativeBase):
    pass


class DocumentRow(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    pages: Mapped[int] = mapped_column(Integer)
    chunks: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="processed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FlashcardRow(Base):
    __tablename__ = "flashcards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36), index=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    source_page: Mapped[int] = mapped_column(Integer)
    source_filename: Mapped[str] = mapped_column(String(255))
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    next_review: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_reviewed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FlashcardReviewRow(Base):
    __tablename__ = "flashcard_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    flashcard_id: Mapped[str] = mapped_column(String(36), index=True)
    rating: Mapped[str] = mapped_column(String(20))
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    previous_interval: Mapped[int] = mapped_column(Integer)
    new_interval: Mapped[int] = mapped_column(Integer)
    previous_ease_factor: Mapped[float] = mapped_column(Float)
    new_ease_factor: Mapped[float] = mapped_column(Float)


class HistoryRow(Base):
    __tablename__ = "study_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    activity: Mapped[str] = mapped_column(String(80))
    document_id: Mapped[str] = mapped_column(String(36), index=True)
    document_name: Mapped[str] = mapped_column(String(255))
    detail: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DatabaseRepository:
    """Supports simple SQLite development and PostgreSQL deployment."""

    def __init__(self, database_url: str) -> None:
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        try:
            if database_url.startswith("sqlite:///") and not database_url.endswith(":memory:"):
                Path(database_url.removeprefix("sqlite:///")).parent.mkdir(
                    parents=True, exist_ok=True
                )
            self.engine = create_engine(database_url, connect_args=connect_args)
            Base.metadata.create_all(self.engine)
            self.sessions = sessionmaker(self.engine, expire_on_commit=False)
        except SQLAlchemyError as error:
            raise StudyAssistantError(
                "The study database is unavailable. Check DATABASE_URL and try again."
            ) from error

    @staticmethod
    def _document_dict(row: DocumentRow) -> dict[str, Any]:
        return {
            "id": row.id,
            "filename": row.filename,
            "pages": row.pages,
            "chunks": row.chunks,
            "status": row.status,
            "created_at": row.created_at,
        }

    @staticmethod
    def _history_dict(row: HistoryRow) -> dict[str, Any]:
        return {
            "id": row.id,
            "activity": row.activity,
            "document_id": row.document_id,
            "document_name": row.document_name,
            "detail": row.detail,
            "created_at": row.created_at,
        }

    @staticmethod
    def _flashcard_dict(row: FlashcardRow) -> dict[str, Any]:
        now = datetime.now(UTC)
        is_due = (
            row.next_review is not None
            and (
                (row.next_review.tzinfo is not None and row.next_review <= now)
                or (row.next_review.tzinfo is None and row.next_review <= now.replace(tzinfo=None))
            )
        )
        return {
            "id": row.id,
            "document_id": row.document_id,
            "question": row.question,
            "answer": row.answer,
            "source_page": row.source_page,
            "source_filename": row.source_filename,
            "difficulty": row.difficulty,
            "repetitions": row.repetitions,
            "ease_factor": row.ease_factor,
            "interval_days": row.interval_days,
            "next_review": row.next_review,
            "last_reviewed": row.last_reviewed,
            "created_at": row.created_at,
            "is_due": is_due,
        }

    def add_document(
        self, document_id: str, filename: str, pages: int, chunks: int
    ) -> dict[str, Any]:
        record = DocumentRow(
            id=document_id,
            filename=filename,
            pages=pages,
            chunks=chunks,
            status="processed",
            created_at=datetime.now(UTC),
        )
        try:
            with self.sessions.begin() as session:
                session.add(record)
            return self._document_dict(record)
        except SQLAlchemyError as error:
            raise StudyAssistantError("Could not save the processed document.") from error

    def list_documents(self) -> list[dict[str, Any]]:
        try:
            with self.sessions() as session:
                rows = session.scalars(
                    select(DocumentRow).order_by(DocumentRow.created_at.desc())
                ).all()
                return [self._document_dict(row) for row in rows]
        except SQLAlchemyError as error:
            raise StudyAssistantError("Could not read saved documents.") from error

    def get_document(self, document_id: str) -> dict[str, Any]:
        try:
            with self.sessions() as session:
                row = session.get(DocumentRow, document_id)
                if row is None:
                    raise NotFoundError("The selected document was not found.")
                return self._document_dict(row)
        except SQLAlchemyError as error:
            raise StudyAssistantError("Could not read the selected document.") from error

    def get_document_details(self, document_id: str) -> dict[str, Any]:
        try:
            with self.sessions() as session:
                row = session.get(DocumentRow, document_id)
                if row is None:
                    raise NotFoundError("The selected document was not found.")
                flashcard_count = session.scalar(
                    select(func.count(FlashcardRow.id)).where(FlashcardRow.document_id == document_id)
                ) or 0
                data = self._document_dict(row)
                data["flashcard_count"] = int(flashcard_count)
                return data
        except NotFoundError:
            raise
        except SQLAlchemyError as error:
            raise StudyAssistantError("Could not read document details.") from error

    def delete_document(self, document_id: str) -> dict[str, Any]:
        try:
            with self.sessions.begin() as session:
                row = session.get(DocumentRow, document_id)
                if row is None:
                    raise NotFoundError("The selected document was not found.")
                doc_dict = self._document_dict(row)

                # Find flashcards for this document
                flashcard_ids = session.scalars(
                    select(FlashcardRow.id).where(FlashcardRow.document_id == document_id)
                ).all()

                # Delete review history for those flashcards
                if flashcard_ids:
                    session.execute(
                        delete(FlashcardReviewRow).where(
                            FlashcardReviewRow.flashcard_id.in_(flashcard_ids)
                        )
                    )

                # Delete flashcards
                session.execute(
                    delete(FlashcardRow).where(FlashcardRow.document_id == document_id)
                )

                # Delete document record
                session.delete(row)

                return doc_dict
        except NotFoundError:
            raise
        except SQLAlchemyError as error:
            raise StudyAssistantError("Could not delete document from database.") from error

    def add_flashcards(self, cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
        records = [
            FlashcardRow(
                id=card.get("id") or str(uuid4()),
                document_id=card["document_id"],
                question=card["question"],
                answer=card["answer"],
                source_page=card.get("source_page", 1),
                source_filename=card.get("source_filename", ""),
                difficulty=card.get("difficulty", "medium"),
                repetitions=card.get("repetitions", 0),
                ease_factor=card.get("ease_factor", 2.5),
                interval_days=card.get("interval_days", 0),
                next_review=card.get("next_review") or datetime.now(UTC),
                last_reviewed=card.get("last_reviewed"),
                created_at=card.get("created_at") or datetime.now(UTC),
            )
            for card in cards
        ]
        try:
            with self.sessions.begin() as session:
                session.add_all(records)
            return [self._flashcard_dict(record) for record in records]
        except SQLAlchemyError as error:
            raise StudyAssistantError("Could not save the generated flashcards.") from error

    def list_flashcards(
        self, document_id: str | None = None, due_only: bool = False
    ) -> list[dict[str, Any]]:
        try:
            with self.sessions() as session:
                query = select(FlashcardRow)
                if document_id:
                    query = query.where(FlashcardRow.document_id == document_id)
                if due_only:
                    now = datetime.now(UTC)
                    query = query.where(FlashcardRow.next_review <= now)
                query = query.order_by(FlashcardRow.created_at.asc())
                rows = session.scalars(query).all()
                return [self._flashcard_dict(row) for row in rows]
        except SQLAlchemyError as error:
            raise StudyAssistantError("Could not read saved flashcards.") from error

    def get_flashcard(self, flashcard_id: str) -> dict[str, Any]:
        try:
            with self.sessions() as session:
                row = session.get(FlashcardRow, flashcard_id)
                if row is None:
                    raise NotFoundError("The requested flashcard was not found.")
                return self._flashcard_dict(row)
        except SQLAlchemyError as error:
            raise StudyAssistantError("Could not read the flashcard.") from error

    def record_flashcard_review(
        self,
        flashcard_id: str,
        rating: str,
        repetitions: int,
        ease_factor: float,
        interval_days: int,
        next_review: datetime,
    ) -> dict[str, Any]:
        try:
            with self.sessions.begin() as session:
                row = session.get(FlashcardRow, flashcard_id)
                if row is None:
                    raise NotFoundError("The requested flashcard was not found.")
                prev_interval = row.interval_days
                prev_ease = row.ease_factor
                now = datetime.now(UTC)

                row.repetitions = repetitions
                row.ease_factor = ease_factor
                row.interval_days = interval_days
                row.next_review = next_review
                row.last_reviewed = now

                review_log = FlashcardReviewRow(
                    id=str(uuid4()),
                    flashcard_id=flashcard_id,
                    rating=rating,
                    reviewed_at=now,
                    previous_interval=prev_interval,
                    new_interval=interval_days,
                    previous_ease_factor=prev_ease,
                    new_ease_factor=ease_factor,
                )
                session.add(review_log)
                return {
                    "card": self._flashcard_dict(row),
                    "rating": rating,
                    "previous_interval": prev_interval,
                    "new_interval": interval_days,
                    "previous_ease_factor": prev_ease,
                    "new_ease_factor": ease_factor,
                    "next_review": next_review,
                }
        except NotFoundError:
            raise
        except SQLAlchemyError as error:
            raise StudyAssistantError("Could not record flashcard review.") from error

    def add_history(
        self, activity: str, document_id: str, document_name: str, detail: str
    ) -> None:
        event = HistoryRow(
            id=str(uuid4()),
            activity=activity,
            document_id=document_id,
            document_name=document_name,
            detail=detail,
            created_at=datetime.now(UTC),
        )
        try:
            with self.sessions.begin() as session:
                session.add(event)
        except SQLAlchemyError as error:
            raise StudyAssistantError("Could not save study history.") from error

    def list_history(self) -> list[dict[str, Any]]:
        try:
            with self.sessions() as session:
                rows = session.scalars(
                    select(HistoryRow).order_by(HistoryRow.created_at.desc()).limit(100)
                ).all()
                return [self._history_dict(row) for row in rows]
        except SQLAlchemyError as error:
            raise StudyAssistantError("Could not read study history.") from error

    def get_all_history(self, document_id: str | None = None) -> list[dict[str, Any]]:
        try:
            with self.sessions() as session:
                query = select(HistoryRow).order_by(HistoryRow.created_at.asc())
                if document_id:
                    query = query.where(HistoryRow.document_id == document_id)
                rows = session.scalars(query).all()
                return [self._history_dict(row) for row in rows]
        except SQLAlchemyError as error:
            raise StudyAssistantError("Could not read study history.") from error

    def list_flashcard_reviews(
        self, document_id: str | None = None
    ) -> list[dict[str, Any]]:
        try:
            with self.sessions() as session:
                if document_id:
                    query = (
                        select(FlashcardReviewRow)
                        .join(FlashcardRow, FlashcardReviewRow.flashcard_id == FlashcardRow.id)
                        .where(FlashcardRow.document_id == document_id)
                        .order_by(FlashcardReviewRow.reviewed_at.asc())
                    )
                else:
                    query = select(FlashcardReviewRow).order_by(FlashcardReviewRow.reviewed_at.asc())
                rows = session.scalars(query).all()
                return [
                    {
                        "id": row.id,
                        "flashcard_id": row.flashcard_id,
                        "rating": row.rating,
                        "reviewed_at": row.reviewed_at,
                        "previous_interval": row.previous_interval,
                        "new_interval": row.new_interval,
                        "previous_ease_factor": row.previous_ease_factor,
                        "new_ease_factor": row.new_ease_factor,
                    }
                    for row in rows
                ]
        except SQLAlchemyError as error:
            raise StudyAssistantError("Could not read flashcard reviews.") from error

