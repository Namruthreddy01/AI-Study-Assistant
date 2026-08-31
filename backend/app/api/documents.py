from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.dependencies import get_study_service
from app.core.errors import InvalidDocumentError
from app.models.schemas import DocumentResponse
from app.services.study_service import StudyService


router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.get("", response_model=list[DocumentResponse])
def list_documents(service: StudyService = Depends(get_study_service)) -> list[dict]:
    return service.list_documents()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    service: StudyService = Depends(get_study_service),
) -> dict:
    if file.content_type and file.content_type not in {
        "application/pdf",
        "application/x-pdf",
    }:
        raise InvalidDocumentError("Only PDF files can be uploaded.")
    maximum_bytes = service.settings.max_upload_mb * 1024 * 1024
    file_bytes = await file.read(maximum_bytes + 1)
    if len(file_bytes) > maximum_bytes:
        raise InvalidDocumentError(
            f"This file is larger than the {service.settings.max_upload_mb} MB upload limit."
        )
    return service.ingest_pdf(file.filename, file_bytes)

