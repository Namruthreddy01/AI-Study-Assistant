import pytest

from app.core.errors import InvalidDocumentError
from app.services.pdf_processor import PdfProcessor


def test_extracts_text_from_valid_pdf(pdf_bytes: bytes) -> None:
    pages = PdfProcessor().extract_pages(pdf_bytes)

    assert len(pages) == 1
    assert pages[0][0] == 1
    assert "OSI model" in pages[0][1]


def test_rejects_invalid_pdf() -> None:
    with pytest.raises(InvalidDocumentError, match="valid PDF"):
        PdfProcessor().extract_pages(b"not a pdf")


def test_rejects_empty_pdf() -> None:
    import fitz

    document = fitz.open()
    document.new_page()
    empty_pdf = document.tobytes()
    document.close()
    with pytest.raises(InvalidDocumentError, match="No readable text"):
        PdfProcessor().extract_pages(empty_pdf)

