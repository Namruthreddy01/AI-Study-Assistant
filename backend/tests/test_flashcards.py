import asyncio
from datetime import UTC, datetime, timedelta
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_study_service
from app.core.errors import NotFoundError, StudyAssistantError
from app.main import app
from app.models.schemas import FlashcardResponse


def test_flashcard_generation_and_source_metadata(service, pdf_bytes: bytes) -> None:
    doc = service.ingest_pdf("networks.pdf", pdf_bytes)
    cards = asyncio.run(service.generate_flashcards(doc["id"], count=4, difficulty="medium"))

    assert len(cards) == 4
    for card in cards:
        assert isinstance(card, FlashcardResponse)
        assert card.document_id == doc["id"]
        assert card.source_filename == "networks.pdf"
        assert card.source_page == 1
        assert card.repetitions == 0
        assert card.ease_factor == 2.5
        assert card.interval_days == 0
        assert card.is_due is True
        assert card.question
        assert card.answer


def test_flashcard_review_lifecycle(service, pdf_bytes: bytes) -> None:
    doc = service.ingest_pdf("networks.pdf", pdf_bytes)
    cards = asyncio.run(service.generate_flashcards(doc["id"], count=1, difficulty="easy"))
    card_id = cards[0].id

    # 1. Review with Good (rep 0 -> interval 1)
    res1 = service.review_flashcard(card_id, "good")
    assert res1.card.repetitions == 1
    assert res1.card.interval_days == 1
    assert res1.card.ease_factor == 2.5
    assert res1.new_interval == 1

    # 2. Review with Good again (rep 1 -> interval 6)
    res2 = service.review_flashcard(card_id, "good")
    assert res2.card.repetitions == 2
    assert res2.card.interval_days == 6
    assert res2.new_interval == 6

    # 3. Review with Hard (rep 2 -> interval max(1, int(6 * 1.2)) = 7, ease down by 0.15)
    res3 = service.review_flashcard(card_id, "hard")
    assert res3.card.repetitions == 3
    assert res3.card.interval_days == 7
    assert res3.card.ease_factor == 2.35

    # 4. Review with Easy (rep 3 -> interval max(1, int(7 * 2.35 * 1.3)) = 21, ease up by 0.15)
    res4 = service.review_flashcard(card_id, "easy")
    assert res4.card.repetitions == 4
    assert res4.card.interval_days == 21
    assert res4.card.ease_factor == 2.5

    # 5. Review with Again (resets repetitions & interval)
    res5 = service.review_flashcard(card_id, "again")
    assert res5.card.repetitions == 0
    assert res5.card.interval_days == 0
    assert res5.card.ease_factor == 2.3


def test_flashcard_due_filtering_and_stats(service, pdf_bytes: bytes) -> None:
    doc = service.ingest_pdf("networks.pdf", pdf_bytes)
    cards = asyncio.run(service.generate_flashcards(doc["id"], count=2, difficulty="medium"))
    
    # Both cards initially due
    deck = service.list_flashcards(document_id=doc["id"])
    assert deck.total == 2
    assert deck.due_count == 2
    assert deck.new_count == 2
    assert deck.learning_count == 0

    # Review one card with Easy (scheduled 4 days into future, no longer due)
    service.review_flashcard(cards[0].id, "easy")

    deck_after = service.list_flashcards(document_id=doc["id"])
    assert deck_after.total == 2
    assert deck_after.due_count == 1
    assert deck_after.new_count == 1
    assert deck_after.learning_count == 1

    due_only = service.list_flashcards(document_id=doc["id"], due_only=True)
    assert len(due_only.cards) == 1
    assert due_only.cards[0].id == cards[1].id


def test_flashcard_api_endpoints(service, pdf_bytes: bytes) -> None:
    app.dependency_overrides[get_study_service] = lambda: service
    try:
        with TestClient(app) as client:
            upload = client.post(
                "/api/documents/upload",
                files={"file": ("notes.pdf", pdf_bytes, "application/pdf")},
            )
            assert upload.status_code == 201
            doc_id = upload.json()["id"]

            # 1. Generate flashcards endpoint
            gen_res = client.post(
                "/api/study/flashcards",
                json={"document_id": doc_id, "count": 3, "difficulty": "hard"},
            )
            assert gen_res.status_code == 200
            cards = gen_res.json()
            assert len(cards) == 3
            card_id = cards[0]["id"]
            assert cards[0]["source_page"] == 1
            assert cards[0]["source_filename"] == "notes.pdf"

            # 2. List flashcards endpoint
            list_res = client.get(f"/api/study/flashcards?document_id={doc_id}")
            assert list_res.status_code == 200
            data = list_res.json()
            assert data["total"] == 3
            assert data["due_count"] == 3

            # 3. Review flashcard endpoint
            review_res = client.post(
                f"/api/study/flashcards/{card_id}/review",
                json={"rating": "good"},
            )
            assert review_res.status_code == 200
            rev_data = review_res.json()
            assert rev_data["card"]["repetitions"] == 1
            assert rev_data["card"]["interval_days"] == 1
            assert rev_data["rating"] == "good"

            # 4. Check study history reflects generation & review
            history_res = client.get("/api/study/history")
            assert history_res.status_code == 200
            history_items = history_res.json()
            activities = [h["activity"] for h in history_items]
            assert "Generated flashcards" in activities
            assert "Reviewed flashcard" in activities
    finally:
        app.dependency_overrides.clear()


def test_flashcard_error_handling(service) -> None:
    with pytest.raises(NotFoundError):
        service.get_flashcard("non-existent-id")

    with pytest.raises(NotFoundError):
        service.review_flashcard("non-existent-id", "good")

    with pytest.raises(NotFoundError):
        asyncio.run(service.generate_flashcards("non-existent-doc", count=3, difficulty="medium"))
