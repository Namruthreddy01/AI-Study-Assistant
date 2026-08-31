from pathlib import Path

import fitz
import pytest

from app.core.config import Settings
from app.services.study_service import StudyService


def make_pdf(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    result = document.tobytes()
    document.close()
    return result


@pytest.fixture
def pdf_bytes() -> bytes:
    return make_pdf(
        "The OSI model has seven layers. The transport layer provides end-to-end "
        "communication. A router forwards packets between networks."
    )


@pytest.fixture
def service(tmp_path: Path) -> StudyService:
    settings = Settings(
        upload_dir=str(tmp_path / "uploads"),
        vector_dir=str(tmp_path / "vectors"),
        database_url=f"sqlite:///{tmp_path / 'study.db'}",
        max_upload_mb=2,
    )
    return StudyService(settings)
