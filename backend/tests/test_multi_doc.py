import asyncio
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_study_service
from app.core.errors import InvalidDocumentError, NotFoundError
from app.main import app
from tests.conftest import make_pdf


@pytest.fixture
def multi_doc_service(tmp_path: Path):
    from app.core.config import Settings
    from app.services.study_service import StudyService

    settings = Settings(
        upload_dir=str(tmp_path / "uploads"),
        vector_dir=str(tmp_path / "vectors"),
        database_url=f"sqlite:///{tmp_path / 'study.db'}",
        max_upload_mb=2,
    )
    return StudyService(settings)


def test_multi_document_ingestion_and_details(multi_doc_service) -> None:
    pdf1 = make_pdf("The physical layer is layer 1 of the OSI model. It transmits raw bits.")
    pdf2 = make_pdf("The data link layer is layer 2. It uses MAC addresses for framing.")

    doc1 = multi_doc_service.ingest_pdf("OSI_Layer1.pdf", pdf1)
    doc2 = multi_doc_service.ingest_pdf("OSI_Layer2.pdf", pdf2)

    docs = multi_doc_service.list_documents()
    assert len(docs) == 2
    filenames = {d["filename"] for d in docs}
    assert "OSI_Layer1.pdf" in filenames
    assert "OSI_Layer2.pdf" in filenames

    # Check details and flashcard count
    asyncio.run(multi_doc_service.generate_flashcards(doc1["id"], count=2, difficulty="easy"))
    details1 = multi_doc_service.get_document_details(doc1["id"])
    assert details1.id == doc1["id"]
    assert details1.filename == "OSI_Layer1.pdf"
    assert details1.flashcard_count == 2

    details2 = multi_doc_service.get_document_details(doc2["id"])
    assert details2.flashcard_count == 0


def test_cross_document_retrieval_and_chat(multi_doc_service) -> None:
    pdf1 = make_pdf("Computer Networks Chapter 1: TCP provides reliable transport stream delivery.")
    pdf2 = make_pdf("Operating Systems Chapter 1: Processes execute threads and allocate virtual address space.")

    doc1 = multi_doc_service.ingest_pdf("Networks_Ch1.pdf", pdf1)
    doc2 = multi_doc_service.ingest_pdf("OS_Ch1.pdf", pdf2)

    # 1. Multi-document chat querying both topics
    response = asyncio.run(
        multi_doc_service.answer_question(
            [doc1["id"], doc2["id"]],
            "Explain TCP transport delivery and virtual address space",
        )
    )

    assert response.grounded is True
    sources = response.sources
    assert len(sources) >= 2
    source_files = {s.filename for s in sources}
    assert "Networks_Ch1.pdf" in source_files
    assert "OS_Ch1.pdf" in source_files
    assert all(s.page >= 1 for s in sources)

    # 2. Single document chat backward compatibility
    single_res = asyncio.run(
        multi_doc_service.answer_question(doc1["id"], "What does TCP provide?")
    )
    assert single_res.grounded is True
    assert all(s.filename == "Networks_Ch1.pdf" for s in single_res.sources)


def test_multi_document_validation_errors(multi_doc_service) -> None:
    pdf1 = make_pdf("Software Engineering Principles and Clean Code.")
    doc1 = multi_doc_service.ingest_pdf("SE.pdf", pdf1)

    # Missing document ID in list
    with pytest.raises(NotFoundError):
        asyncio.run(
            multi_doc_service.answer_question(
                [doc1["id"], "non-existent-doc-id"], "Explain software principles"
            )
        )

    # Empty list
    with pytest.raises(InvalidDocumentError):
        asyncio.run(multi_doc_service.answer_question([], "Explain software principles"))

    # Duplicate IDs are deduplicated and succeed
    dup_res = asyncio.run(
        multi_doc_service.answer_question(
            [doc1["id"], doc1["id"]], "Explain software principles"
        )
    )
    assert dup_res.grounded is True


def test_document_deletion_and_artifact_cleanup(multi_doc_service) -> None:
    pdf1 = make_pdf("Database Management Systems: Relational algebra and ACID transactions.")
    pdf2 = make_pdf("Compiler Design: Lexical analysis and Abstract Syntax Trees.")

    doc1 = multi_doc_service.ingest_pdf("DBMS.pdf", pdf1)
    doc2 = multi_doc_service.ingest_pdf("Compilers.pdf", pdf2)

    # Generate flashcard and review for doc1
    cards = asyncio.run(multi_doc_service.generate_flashcards(doc1["id"], count=2, difficulty="medium"))
    multi_doc_service.review_flashcard(cards[0].id, "good")

    # Verify artifacts exist before deletion
    pdf1_path = multi_doc_service.settings.upload_path / f"{doc1['id']}.pdf"
    vec1_faiss = multi_doc_service.settings.vector_path / f"{doc1['id']}.faiss"
    vec1_npz = multi_doc_service.settings.vector_path / f"{doc1['id']}.npz"
    vec1_json = multi_doc_service.settings.vector_path / f"{doc1['id']}.json"

    assert pdf1_path.exists()
    assert vec1_npz.exists()
    assert vec1_json.exists()

    # Delete doc1
    del_res = multi_doc_service.delete_document(doc1["id"])
    assert del_res.deleted is True
    assert del_res.id == doc1["id"]

    # Verify doc1 artifacts are deleted
    assert not pdf1_path.exists()
    assert not vec1_faiss.exists()
    assert not vec1_npz.exists()
    assert not vec1_json.exists()

    # Verify doc1 flashcards and reviews are gone
    deck1 = multi_doc_service.list_flashcards(document_id=doc1["id"])
    assert len(deck1.cards) == 0

    # Verify doc1 cannot be fetched (404)
    with pytest.raises(NotFoundError):
        multi_doc_service.get_document(doc1["id"])

    with pytest.raises(NotFoundError):
        multi_doc_service.get_document_details(doc1["id"])

    # Verify doc2 and its artifacts are completely intact and searchable
    doc2_details = multi_doc_service.get_document_details(doc2["id"])
    assert doc2_details.filename == "Compilers.pdf"

    chat2 = asyncio.run(
        multi_doc_service.answer_question(doc2["id"], "Explain lexical analysis")
    )
    assert chat2.grounded is True
    assert chat2.sources[0].filename == "Compilers.pdf"

    # Verify history recorded the deletion
    history_items = multi_doc_service.history()
    deletion_logs = [h for h in history_items if h.activity == "Deleted document"]
    assert len(deletion_logs) >= 1
    assert deletion_logs[0].document_name == "DBMS.pdf"


def test_api_multi_doc_endpoints(multi_doc_service) -> None:
    app.dependency_overrides[get_study_service] = lambda: multi_doc_service
    try:
        with TestClient(app) as client:
            pdf1 = make_pdf("Algorithms: Dynamic programming and greedy strategies.")
            pdf2 = make_pdf("Discrete Math: Graph theory, trees, and vertices.")

            u1 = client.post("/api/documents/upload", files={"file": ("Algorithms.pdf", pdf1, "application/pdf")})
            u2 = client.post("/api/documents/upload", files={"file": ("DiscreteMath.pdf", pdf2, "application/pdf")})
            id1, id2 = u1.json()["id"], u2.json()["id"]

            # 1. GET /api/documents/{id}
            det = client.get(f"/api/documents/{id1}")
            assert det.status_code == 200
            assert det.json()["filename"] == "Algorithms.pdf"

            # 2. POST /api/study/chat with multi-docs
            chat = client.post(
                "/api/study/chat",
                json={
                    "document_ids": [id1, id2],
                    "question": "Compare dynamic programming and graph theory vertices",
                },
            )
            assert chat.status_code == 200
            assert chat.json()["grounded"] is True

            # 3. DELETE /api/documents/{id}
            del_resp = client.delete(f"/api/documents/{id1}")
            assert del_resp.status_code == 200
            assert del_resp.json()["deleted"] is True

            # 4. Check 404 on deleted document
            not_found = client.get(f"/api/documents/{id1}")
            assert not_found.status_code == 400 or not_found.status_code == 404
    finally:
        app.dependency_overrides.clear()
