from __future__ import annotations

import re
from datetime import UTC, date, datetime, timedelta
from typing import Any

from app.models.schemas import (
    AchievementItem,
    AnalyticsOverviewResponse,
    DailyActivityItem,
    DocumentAnalyticsItem,
    FlashcardAnalyticsResponse,
    FlashcardRatingsBreakdown,
    QuizAnalyticsResponse,
    QuizAttemptItem,
)
from app.storage.repository import DatabaseRepository


class AnalyticsService:
    """Dedicated service for calculating student learning analytics, streaks, and progress."""

    def __init__(self, repository: DatabaseRepository) -> None:
        self.repository = repository

    @staticmethod
    def _parse_quiz_detail(detail: str) -> tuple[int, int]:
        """Extracts score and total from detail string like 'Score 3/8'."""
        match = re.search(r"Score\s+(\d+)/(\d+)", detail)
        if match:
            return int(match.group(1)), int(match.group(2))
        return 0, 0

    @staticmethod
    def _calculate_streaks(active_dates: set[date], ref_date: date) -> tuple[int, int]:
        """Calculates current and longest study streak deterministically."""
        if not active_dates:
            return 0, 0

        # Current streak: consecutive calendar days ending on ref_date (today)
        current_streak = 0
        if ref_date in active_dates:
            check_date = ref_date
            while check_date in active_dates:
                current_streak += 1
                check_date -= timedelta(days=1)
        else:
            current_streak = 0

        # Longest streak: max consecutive days across all recorded history
        sorted_dates = sorted(active_dates)
        longest = 1
        current_run = 1
        for i in range(1, len(sorted_dates)):
            if sorted_dates[i] == sorted_dates[i - 1] + timedelta(days=1):
                current_run += 1
            else:
                current_run = 1
            if current_run > longest:
                longest = current_run

        return current_streak, longest

    @staticmethod
    def _calculate_mastery(
        quiz_accuracy: float,
        quizzes_completed: int,
        retention_rate: float,
        review_count: int,
        learning_cards: int,
        total_cards: int,
        session_count: int,
    ) -> float:
        """Deterministic mastery score heuristic (0-100).

        Formula:
        - Quiz performance: 40%
        - Flashcard retention & review: 40%
        - Study activity: 20%
        """
        quiz_component = (
            min(100.0, max(0.0, quiz_accuracy)) if quizzes_completed > 0 else 0.0
        )

        if review_count > 0:
            coverage = (learning_cards / total_cards * 100.0) if total_cards > 0 else 0.0
            flashcard_component = min(
                100.0, max(0.0, (retention_rate * 0.6) + (coverage * 0.4))
            )
        else:
            flashcard_component = 0.0

        activity_component = min(100.0, (session_count / 10.0) * 100.0)

        mastery = (
            (quiz_component * 0.40)
            + (flashcard_component * 0.40)
            + (activity_component * 0.20)
        )
        return round(mastery, 1)

    def get_overview(self, now: datetime | None = None) -> AnalyticsOverviewResponse:
        ref_now = now or datetime.now(UTC)
        ref_date = ref_now.date()

        history = self.repository.get_all_history()
        reviews = self.repository.list_flashcard_reviews()
        cards = self.repository.list_flashcards()
        documents = self.repository.list_documents()

        total_study_sessions = len(history)
        questions_asked = sum(1 for h in history if "Asked AI" in h["activity"])
        quizzes_completed = sum(1 for h in history if h["activity"] == "Completed quiz")
        flashcards_reviewed = len(reviews)

        # Quiz accuracy
        total_questions = 0
        correct_answers = 0
        for h in history:
            if h["activity"] == "Completed quiz":
                s, t = self._parse_quiz_detail(h["detail"])
                correct_answers += s
                total_questions += t

        overall_quiz_accuracy = (
            round((correct_answers / total_questions) * 100.0, 1)
            if total_questions > 0
            else 0.0
        )

        # Active study dates from study_history and flashcard_reviews
        active_dates: set[date] = set()
        for h in history:
            active_dates.add(h["created_at"].date())
        for r in reviews:
            active_dates.add(r["reviewed_at"].date())

        current_streak, longest_streak = self._calculate_streaks(active_dates, ref_date)
        active_study_days = len(active_dates)
        last_study_date = max(active_dates).isoformat() if active_dates else None

        # Flashcards stats
        total_cards = len(cards)
        learning_cards = sum(1 for c in cards if c.get("repetitions", 0) > 0)
        good_easy_count = sum(1 for r in reviews if r["rating"] in ("good", "easy"))
        retention_rate = (
            (good_easy_count / len(reviews) * 100.0) if reviews else 0.0
        )

        mastery_score = self._calculate_mastery(
            quiz_accuracy=overall_quiz_accuracy,
            quizzes_completed=quizzes_completed,
            retention_rate=retention_rate,
            review_count=len(reviews),
            learning_cards=learning_cards,
            total_cards=total_cards,
            session_count=total_study_sessions,
        )

        return AnalyticsOverviewResponse(
            total_study_sessions=total_study_sessions,
            questions_asked=questions_asked,
            quizzes_completed=quizzes_completed,
            flashcards_reviewed=flashcards_reviewed,
            overall_quiz_accuracy=overall_quiz_accuracy,
            current_streak=current_streak,
            longest_streak=longest_streak,
            active_study_days=active_study_days,
            last_study_date=last_study_date,
            total_documents=len(documents),
            total_flashcards=total_cards,
            mastery_score=mastery_score,
        )

    def get_activity(
        self, days: int = 30, document_id: str | None = None, now: datetime | None = None
    ) -> list[DailyActivityItem]:
        ref_now = now or datetime.now(UTC)
        ref_date = ref_now.date()

        history = self.repository.get_all_history(document_id=document_id)
        reviews = self.repository.list_flashcard_reviews(document_id=document_id)

        # Build chronological list of days
        daily_map: dict[str, dict[str, int]] = {}
        for i in range(days - 1, -1, -1):
            d_str = (ref_date - timedelta(days=i)).isoformat()
            daily_map[d_str] = {
                "study_sessions": 0,
                "quiz_attempts": 0,
                "flashcard_reviews": 0,
                "questions_asked": 0,
            }

        for h in history:
            d_str = h["created_at"].date().isoformat()
            if d_str in daily_map:
                daily_map[d_str]["study_sessions"] += 1
                if h["activity"] == "Completed quiz":
                    daily_map[d_str]["quiz_attempts"] += 1
                elif "Asked AI" in h["activity"]:
                    daily_map[d_str]["questions_asked"] += 1

        for r in reviews:
            d_str = r["reviewed_at"].date().isoformat()
            if d_str in daily_map:
                daily_map[d_str]["flashcard_reviews"] += 1

        return [
            DailyActivityItem(
                date=d_str,
                study_sessions=stats["study_sessions"],
                quiz_attempts=stats["quiz_attempts"],
                flashcard_reviews=stats["flashcard_reviews"],
                questions_asked=stats["questions_asked"],
            )
            for d_str, stats in daily_map.items()
        ]

    def get_quiz_analytics(
        self, document_id: str | None = None
    ) -> QuizAnalyticsResponse:
        history = self.repository.get_all_history(document_id=document_id)

        quizzes_completed = 0
        total_questions = 0
        correct_answers = 0
        recent_quizzes: list[QuizAttemptItem] = []
        difficulty_breakdown: dict[str, int] = {}

        # Collect difficulty tags if available from Generated MCQs events
        for h in history:
            if h["activity"] == "Generated MCQs":
                # Detail format is e.g. "8 medium"
                parts = h["detail"].split()
                if len(parts) >= 2:
                    diff = parts[1].lower()
                    difficulty_breakdown[diff] = difficulty_breakdown.get(diff, 0) + 1

        for h in reversed(history):
            if h["activity"] == "Completed quiz":
                quizzes_completed += 1
                score, total = self._parse_quiz_detail(h["detail"])
                correct_answers += score
                total_questions += total
                acc = round((score / total) * 100.0, 1) if total > 0 else 0.0
                recent_quizzes.append(
                    QuizAttemptItem(
                        id=h["id"],
                        document_id=h["document_id"],
                        document_name=h["document_name"],
                        score=score,
                        total=total,
                        accuracy=acc,
                        created_at=h["created_at"],
                    )
                )

        incorrect_answers = max(0, total_questions - correct_answers)
        overall_accuracy = (
            round((correct_answers / total_questions) * 100.0, 1)
            if total_questions > 0
            else 0.0
        )

        return QuizAnalyticsResponse(
            quizzes_completed=quizzes_completed,
            total_questions=total_questions,
            correct_answers=correct_answers,
            incorrect_answers=incorrect_answers,
            overall_accuracy=overall_accuracy,
            difficulty_breakdown=difficulty_breakdown,
            recent_quizzes=recent_quizzes[:20],
        )

    def get_flashcard_analytics(
        self, document_id: str | None = None
    ) -> FlashcardAnalyticsResponse:
        cards = self.repository.list_flashcards(document_id=document_id)
        reviews = self.repository.list_flashcard_reviews(document_id=document_id)

        total_cards = len(cards)
        new_cards = sum(1 for c in cards if c.get("repetitions", 0) == 0)
        learning_cards = sum(1 for c in cards if c.get("repetitions", 0) > 0)
        due_cards = sum(1 for c in cards if c.get("is_due"))
        reviewed_cards = sum(1 for c in cards if c.get("last_reviewed") is not None)

        ratings_count = {"again": 0, "hard": 0, "good": 0, "easy": 0}
        for r in reviews:
            r_tag = r["rating"].lower()
            if r_tag in ratings_count:
                ratings_count[r_tag] += 1

        total_reviews = len(reviews)
        good_easy = ratings_count["good"] + ratings_count["easy"]
        retention_rate = (
            round((good_easy / total_reviews) * 100.0, 1) if total_reviews > 0 else 0.0
        )
        average_ease_factor = (
            round(sum(c["ease_factor"] for c in cards) / total_cards, 2)
            if total_cards > 0
            else 2.5
        )

        return FlashcardAnalyticsResponse(
            total_cards=total_cards,
            new_cards=new_cards,
            learning_cards=learning_cards,
            due_cards=due_cards,
            reviewed_cards=reviewed_cards,
            total_reviews=total_reviews,
            ratings=FlashcardRatingsBreakdown(**ratings_count),
            average_ease_factor=average_ease_factor,
            retention_rate=retention_rate,
        )

    def get_documents_analytics(self) -> list[DocumentAnalyticsItem]:
        documents = self.repository.list_documents()
        all_history = self.repository.get_all_history()
        all_cards = self.repository.list_flashcards()
        all_reviews = self.repository.list_flashcard_reviews()

        items: list[DocumentAnalyticsItem] = []
        for doc in documents:
            doc_id = doc["id"]
            doc_history = [
                h
                for h in all_history
                if h["document_id"] == doc_id or doc_id in h["document_id"].split(",")
            ]
            doc_cards = [c for c in all_cards if c["document_id"] == doc_id]
            doc_card_ids = {c["id"] for c in doc_cards}
            doc_reviews = [
                r for r in all_reviews if r["flashcard_id"] in doc_card_ids
            ]

            study_sessions = len(doc_history)
            questions_asked = sum(
                1 for h in doc_history if "Asked AI" in h["activity"]
            )

            quizzes_completed = 0
            correct_answers = 0
            total_questions = 0
            for h in doc_history:
                if h["activity"] == "Completed quiz":
                    quizzes_completed += 1
                    s, t = self._parse_quiz_detail(h["detail"])
                    correct_answers += s
                    total_questions += t

            quiz_accuracy = (
                round((correct_answers / total_questions) * 100.0, 1)
                if total_questions > 0
                else 0.0
            )

            total_fc = len(doc_cards)
            learning_fc = sum(1 for c in doc_cards if c.get("repetitions", 0) > 0)
            good_easy_fc = sum(
                1 for r in doc_reviews if r["rating"] in ("good", "easy")
            )
            fc_retention = (
                (good_easy_fc / len(doc_reviews) * 100.0) if doc_reviews else 0.0
            )

            mastery = self._calculate_mastery(
                quiz_accuracy=quiz_accuracy,
                quizzes_completed=quizzes_completed,
                retention_rate=fc_retention,
                review_count=len(doc_reviews),
                learning_cards=learning_fc,
                total_cards=total_fc,
                session_count=study_sessions,
            )

            last_studied_at = None
            if doc_history:
                last_studied_at = max(h["created_at"] for h in doc_history)

            items.append(
                DocumentAnalyticsItem(
                    id=doc_id,
                    filename=doc["filename"],
                    pages=doc["pages"],
                    chunks=doc["chunks"],
                    flashcards_count=total_fc,
                    flashcards_reviewed_count=len(doc_reviews),
                    quizzes_completed=quizzes_completed,
                    quiz_accuracy=quiz_accuracy,
                    study_sessions=study_sessions,
                    questions_asked=questions_asked,
                    mastery_score=mastery,
                    last_studied_at=last_studied_at,
                )
            )

        return items

    def get_achievements(
        self, now: datetime | None = None
    ) -> list[AchievementItem]:
        overview = self.get_overview(now=now)

        sessions = overview.total_study_sessions
        quizzes = overview.quizzes_completed
        reviews = overview.flashcards_reviewed
        longest_streak = overview.longest_streak
        quiz_acc = overview.overall_quiz_accuracy
        docs = overview.total_documents

        achievements_defs = [
            (
                "first_session",
                "First Step",
                "Complete your first study session",
                "Footprints",
                sessions >= 1,
                min(100, sessions * 100),
            ),
            (
                "first_quiz",
                "Quiz Cadet",
                "Complete your first knowledge check quiz",
                "Award",
                quizzes >= 1,
                min(100, quizzes * 100),
            ),
            (
                "first_review",
                "Memory Builder",
                "Review your first flashcard with spaced repetition",
                "Brain",
                reviews >= 1,
                min(100, reviews * 100),
            ),
            (
                "study_streak_3",
                "Consistent Learner",
                "Reach a 3-day study streak",
                "Flame",
                longest_streak >= 3,
                min(100, int((longest_streak / 3) * 100)),
            ),
            (
                "study_streak_7",
                "Weekly Champion",
                "Reach a 7-day study streak",
                "Zap",
                longest_streak >= 7,
                min(100, int((longest_streak / 7) * 100)),
            ),
            (
                "quiz_5",
                "Quiz Enthusiast",
                "Complete at least 5 quizzes",
                "ListChecks",
                quizzes >= 5,
                min(100, int((quizzes / 5) * 100)),
            ),
            (
                "high_accuracy",
                "Sharp Mind",
                "Achieve 80% or higher overall quiz accuracy",
                "Target",
                quizzes >= 1 and quiz_acc >= 80.0,
                min(100, int((quiz_acc / 80.0) * 100)) if quizzes > 0 else 0,
            ),
            (
                "cards_25",
                "Flashcard Pro",
                "Complete 25 flashcard reviews",
                "Layers",
                reviews >= 25,
                min(100, int((reviews / 25) * 100)),
            ),
            (
                "cards_50",
                "Recall Master",
                "Complete 50 flashcard reviews",
                "Trophy",
                reviews >= 50,
                min(100, int((reviews / 50) * 100)),
            ),
            (
                "multi_doc",
                "Library Builder",
                "Upload 2 or more study materials",
                "BookOpen",
                docs >= 2,
                min(100, int((docs / 2) * 100)),
            ),
        ]

        return [
            AchievementItem(
                id=a_id,
                title=title,
                description=desc,
                icon=icon,
                unlocked=unlocked,
                progress=progress,
            )
            for a_id, title, desc, icon, unlocked, progress in achievements_defs
        ]
