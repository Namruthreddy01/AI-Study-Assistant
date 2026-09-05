from datetime import UTC, datetime, timedelta
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_analytics_service, get_study_service
from app.core.config import Settings
from app.main import app
from app.services.analytics_service import AnalyticsService
from app.services.study_service import StudyService
from tests.conftest import make_pdf


@pytest.fixture
def analytics_fixture(tmp_path: Path):
    settings = Settings(
        upload_dir=str(tmp_path / "uploads"),
        vector_dir=str(tmp_path / "vectors"),
        database_url=f"sqlite:///{tmp_path / 'analytics_test.db'}",
        max_upload_mb=2,
    )
    study_service = StudyService(settings)
    analytics_service = AnalyticsService(study_service.repository)
    return study_service, analytics_service


def test_overview_empty_state(analytics_fixture) -> None:
    _, analytics_service = analytics_fixture
    fixed_now = datetime(2026, 9, 10, 12, 0, 0, tzinfo=UTC)

    overview = analytics_service.get_overview(now=fixed_now)
    assert overview.total_study_sessions == 0
    assert overview.questions_asked == 0
    assert overview.quizzes_completed == 0
    assert overview.flashcards_reviewed == 0
    assert overview.overall_quiz_accuracy == 0.0
    assert overview.current_streak == 0
    assert overview.longest_streak == 0
    assert overview.active_study_days == 0
    assert overview.last_study_date is None
    assert overview.total_documents == 0
    assert overview.total_flashcards == 0
    assert overview.mastery_score == 0.0


def test_streak_calculations(analytics_fixture) -> None:
    study_service, analytics_service = analytics_fixture
    repo = study_service.repository

    # Use fixed dates: 2026-09-08, 2026-09-09, 2026-09-10
    day1 = datetime(2026, 9, 8, 10, 0, 0, tzinfo=UTC)
    day2 = datetime(2026, 9, 9, 14, 0, 0, tzinfo=UTC)
    day3 = datetime(2026, 9, 10, 9, 0, 0, tzinfo=UTC)

    # Add history on day 1 and day 2
    repo.add_history("Asked AI", "doc-1", "Doc 1.pdf", "Question 1")
    # Manually update created_at for deterministic streak test
    with repo.sessions.begin() as session:
        from app.storage.repository import HistoryRow
        rows = session.query(HistoryRow).all()
        rows[0].created_at = day1

    # Check streak on day 1
    ov1 = analytics_service.get_overview(now=day1)
    assert ov1.current_streak == 1
    assert ov1.longest_streak == 1
    assert ov1.active_study_days == 1

    # Check streak on day 2 before day 2 activity
    ov2_before = analytics_service.get_overview(now=day2)
    assert ov2_before.current_streak == 0  # no activity yet on day 2

    # Add day 2 activity
    repo.add_history("Completed quiz", "doc-1", "Doc 1.pdf", "Score 4/5")
    with repo.sessions.begin() as session:
        from app.storage.repository import HistoryRow
        rows = session.query(HistoryRow).all()
        rows[1].created_at = day2

    ov2_after = analytics_service.get_overview(now=day2)
    assert ov2_after.current_streak == 2
    assert ov2_after.longest_streak == 2
    assert ov2_after.active_study_days == 2

    # Add day 3 activity
    repo.add_history("Reviewed flashcard", "doc-1", "Doc 1.pdf", "Rated 'good'")
    with repo.sessions.begin() as session:
        from app.storage.repository import HistoryRow
        rows = session.query(HistoryRow).all()
        rows[2].created_at = day3

    ov3 = analytics_service.get_overview(now=day3)
    assert ov3.current_streak == 3
    assert ov3.longest_streak == 3
    assert ov3.active_study_days == 3

    # Check day 5 (broken streak)
    day5 = datetime(2026, 9, 12, 10, 0, 0, tzinfo=UTC)
    ov5 = analytics_service.get_overview(now=day5)
    assert ov5.current_streak == 0
    assert ov5.longest_streak == 3
    assert ov5.active_study_days == 3


def test_quiz_and_flashcard_analytics(analytics_fixture) -> None:
    study_service, analytics_service = analytics_fixture
    repo = study_service.repository

    # Ingest document
    pdf = make_pdf("Artificial Intelligence is the simulation of human intelligence by machines.")
    doc = study_service.ingest_pdf("AI_Basics.pdf", pdf)
    doc_id = doc["id"]

    # Record 2 quiz completions
    repo.add_history("Completed quiz", doc_id, "AI_Basics.pdf", "Score 8/10")
    repo.add_history("Completed quiz", doc_id, "AI_Basics.pdf", "Score 2/5")
    repo.add_history("Generated MCQs", doc_id, "AI_Basics.pdf", "10 medium")

    quiz_stats = analytics_service.get_quiz_analytics(document_id=doc_id)
    assert quiz_stats.quizzes_completed == 2
    assert quiz_stats.total_questions == 15
    assert quiz_stats.correct_answers == 10
    assert quiz_stats.incorrect_answers == 5
    assert quiz_stats.overall_accuracy == round((10 / 15) * 100, 1)
    assert len(quiz_stats.recent_quizzes) == 2
    assert quiz_stats.difficulty_breakdown.get("medium") == 1

    # Generate flashcards and review
    cards = repo.add_flashcards([
        {
            "document_id": doc_id,
            "question": "What is AI?",
            "answer": "Simulation of human intelligence",
            "source_page": 1,
            "source_filename": "AI_Basics.pdf",
        },
        {
            "document_id": doc_id,
            "question": "What are agents?",
            "answer": "Autonomous entities",
            "source_page": 1,
            "source_filename": "AI_Basics.pdf",
        },
    ])

    repo.record_flashcard_review(
        flashcard_id=cards[0]["id"],
        rating="good",
        repetitions=1,
        ease_factor=2.5,
        interval_days=1,
        next_review=datetime.now(UTC) + timedelta(days=1),
    )
    repo.record_flashcard_review(
        flashcard_id=cards[1]["id"],
        rating="again",
        repetitions=0,
        ease_factor=2.3,
        interval_days=0,
        next_review=datetime.now(UTC),
    )

    fc_stats = analytics_service.get_flashcard_analytics(document_id=doc_id)
    assert fc_stats.total_cards == 2
    assert fc_stats.total_reviews == 2
    assert fc_stats.ratings.good == 1
    assert fc_stats.ratings.again == 1
    assert fc_stats.retention_rate == 50.0  # 1 good out of 2 reviews
    assert fc_stats.average_ease_factor > 0


def test_daily_activity_and_document_analytics(analytics_fixture) -> None:
    study_service, analytics_service = analytics_fixture
    repo = study_service.repository

    fixed_now = datetime(2026, 9, 5, 12, 0, 0, tzinfo=UTC)

    pdf1 = make_pdf("Operating systems manage hardware resources like CPU, memory, and devices.")
    doc1 = study_service.ingest_pdf("OS.pdf", pdf1)

    repo.add_history("Asked AI", doc1["id"], "OS.pdf", "How does OS manage memory?")
    repo.add_history("Completed quiz", doc1["id"], "OS.pdf", "Score 5/5")

    # Activity test
    activity = analytics_service.get_activity(days=7, now=fixed_now)
    assert len(activity) == 7
    today_act = [a for a in activity if a.date == "2026-09-05"]
    assert len(today_act) == 1
    assert today_act[0].study_sessions >= 2
    assert today_act[0].quiz_attempts >= 1
    assert today_act[0].questions_asked >= 1

    # Document analytics test
    doc_analytics = analytics_service.get_documents_analytics()
    assert len(doc_analytics) == 1
    d = doc_analytics[0]
    assert d.filename == "OS.pdf"
    assert d.study_sessions >= 2
    assert d.quizzes_completed == 1
    assert d.quiz_accuracy == 100.0
    assert d.mastery_score > 0.0


def test_achievements_unlocking(analytics_fixture) -> None:
    study_service, analytics_service = analytics_fixture
    repo = study_service.repository

    fixed_now = datetime(2026, 9, 5, 12, 0, 0, tzinfo=UTC)

    # Initial achievements - all locked except library builder if docs exist
    initial = analytics_service.get_achievements(now=fixed_now)
    assert all(not a.unlocked for a in initial)

    # Perform activities
    pdf1 = make_pdf("Networks Chapter 1")
    pdf2 = make_pdf("Networks Chapter 2")
    d1 = study_service.ingest_pdf("Net1.pdf", pdf1)
    d2 = study_service.ingest_pdf("Net2.pdf", pdf2)

    repo.add_history("Asked AI", d1["id"], "Net1.pdf", "Explain TCP")
    repo.add_history("Completed quiz", d1["id"], "Net1.pdf", "Score 5/5")

    cards = repo.add_flashcards([
        {
            "document_id": d1["id"],
            "question": "Q1",
            "answer": "A1",
            "source_page": 1,
            "source_filename": "Net1.pdf",
        }
    ])
    repo.record_flashcard_review(
        flashcard_id=cards[0]["id"],
        rating="easy",
        repetitions=1,
        ease_factor=2.65,
        interval_days=4,
        next_review=fixed_now + timedelta(days=4),
    )

    achievements = analytics_service.get_achievements(now=fixed_now)
    unlocked_ids = {a.id for a in achievements if a.unlocked}
    assert "first_session" in unlocked_ids
    assert "first_quiz" in unlocked_ids
    assert "first_review" in unlocked_ids
    assert "high_accuracy" in unlocked_ids  # 100% accuracy >= 80%
    assert "multi_doc" in unlocked_ids  # 2 documents


def test_analytics_api_endpoints(analytics_fixture) -> None:
    study_service, analytics_service = analytics_fixture
    app.dependency_overrides[get_study_service] = lambda: study_service
    app.dependency_overrides[get_analytics_service] = lambda: analytics_service

    try:
        with TestClient(app) as client:
            # 1. Overview
            res = client.get("/api/analytics/overview")
            assert res.status_code == 200
            data = res.json()
            assert "total_study_sessions" in data
            assert "mastery_score" in data

            # 2. Activity
            res = client.get("/api/analytics/activity?days=14")
            assert res.status_code == 200
            act = res.json()
            assert len(act) == 14

            # 3. Quiz
            res = client.get("/api/analytics/quiz")
            assert res.status_code == 200
            assert "quizzes_completed" in res.json()

            # 4. Flashcards
            res = client.get("/api/analytics/flashcards")
            assert res.status_code == 200
            assert "total_cards" in res.json()

            # 5. Documents
            res = client.get("/api/analytics/documents")
            assert res.status_code == 200
            assert isinstance(res.json(), list)

            # 6. Achievements
            res = client.get("/api/analytics/achievements")
            assert res.status_code == 200
            ach = res.json()
            assert len(ach) >= 5

            # 7. Invalid document ID on quiz analytics
            res_invalid = client.get("/api/analytics/quiz?document_id=non-existent-doc")
            assert res_invalid.status_code in (400, 404)
    finally:
        app.dependency_overrides.clear()
