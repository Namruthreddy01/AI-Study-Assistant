from fastapi.testclient import TestClient

from app.api.dependencies import get_study_service
from app.main import app


def test_upload_and_chat_endpoint(service, pdf_bytes: bytes) -> None:
    app.dependency_overrides[get_study_service] = lambda: service
    try:
        with TestClient(app) as client:
            upload = client.post(
                "/api/documents/upload",
                files={"file": ("networks.pdf", pdf_bytes, "application/pdf")},
            )
            assert upload.status_code == 201
            document_id = upload.json()["id"]

            chat = client.post(
                "/api/study/chat",
                json={"document_id": document_id, "question": "What is the OSI model?"},
            )
            assert chat.status_code == 200
            assert chat.json()["grounded"] is True
    finally:
        app.dependency_overrides.clear()
