from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String, Text, create_engine, select
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
