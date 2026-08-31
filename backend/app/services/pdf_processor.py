from pathlib import Path

import fitz

from app.core.errors import InvalidDocumentError


class PdfProcessor:
    """Extracts selectable text while preserving its source page."""

    def extract_pages(self, file_bytes: bytes) -> list[tuple[int, str]]:
        if not file_bytes.startswith(b"%PDF"):
            raise InvalidDocumentError("Please upload a valid PDF file.")
        try:
            document = fitz.open(stream=file_bytes, filetype="pdf")
        except (fitz.FileDataError, RuntimeError, ValueError) as error:
            raise InvalidDocumentError("This PDF could not be opened.") from error

        try:
            if document.page_count == 0:
                raise InvalidDocumentError("This PDF does not contain any pages.")
            pages = [
                (page_number + 1, document.load_page(page_number).get_text("text").strip())
                for page_number in range(document.page_count)
            ]
        finally:
            document.close()

        if not any(text for _, text in pages):
            raise InvalidDocumentError(
                "No readable text was found. This may be a scanned or image-only PDF."
            )
        return pages

    @staticmethod
    def safe_filename(filename: str | None) -> str:
        candidate = Path(filename or "study-material.pdf").name
        if not candidate.lower().endswith(".pdf"):
            candidate = f"{candidate}.pdf"
        return "".join(char if char.isalnum() or char in " ._-()" else "_" for char in candidate)

