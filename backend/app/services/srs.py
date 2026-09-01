"""Spaced Repetition System (SRS) implementation.

Inspired by the SuperMemo SM-2 algorithm, adapted for simple, robust
flashcard scheduling in a student study companion.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from app.core.errors import StudyAssistantError

RatingType = Literal["again", "hard", "good", "easy"]

MIN_EASE_FACTOR = 1.3
MAX_EASE_FACTOR = 3.0
DEFAULT_EASE_FACTOR = 2.5


@dataclass(frozen=True)
class ReviewSchedule:
    repetitions: int
    ease_factor: float
    interval_days: int
    next_review: datetime


def calculate_review_schedule(
    rating: str,
    repetitions: int = 0,
    ease_factor: float = DEFAULT_EASE_FACTOR,
    interval_days: int = 0,
    now: datetime | None = None,
) -> ReviewSchedule:
    """Calculate the next review schedule for a flashcard based on student rating.

    Numerical rules:
    - 'again': Reset repetitions to 0, interval to 0 days (due today), decrease ease factor by 0.2 (min 1.3).
    - 'hard': Increment repetitions, set interval to 1 day (if rep 0) or 1.2x current interval, decrease ease factor by 0.15 (min 1.3).
    - 'good': Increment repetitions, progression: 1 day (rep 0) -> 6 days (rep 1) -> interval * ease_factor (rep 2+), ease factor unchanged.
    - 'easy': Increment repetitions, progression: 4 days (rep 0) -> 10 days (rep 1) -> interval * ease_factor * 1.3 (rep 2+), increase ease factor by 0.15 (max 3.0).
    """
    normalized_rating = rating.lower().strip()
    if normalized_rating not in {"again", "hard", "good", "easy"}:
        raise StudyAssistantError(
            f"Invalid rating '{rating}'. Allowed ratings are 'again', 'hard', 'good', 'easy'."
        )

    current_time = now or datetime.now(UTC)
    clamped_ease = max(MIN_EASE_FACTOR, min(MAX_EASE_FACTOR, ease_factor))

    if normalized_rating == "again":
        new_repetitions = 0
        new_interval_days = 0
        new_ease_factor = max(MIN_EASE_FACTOR, clamped_ease - 0.2)

    elif normalized_rating == "hard":
        new_repetitions = repetitions + 1
        if repetitions == 0:
            new_interval_days = 1
        else:
            new_interval_days = max(1, int(interval_days * 1.2))
        new_ease_factor = max(MIN_EASE_FACTOR, clamped_ease - 0.15)

    elif normalized_rating == "good":
        new_repetitions = repetitions + 1
        if repetitions == 0:
            new_interval_days = 1
        elif repetitions == 1:
            new_interval_days = 6
        else:
            new_interval_days = max(1, int(interval_days * clamped_ease))
        new_ease_factor = clamped_ease

    else:  # easy
        new_repetitions = repetitions + 1
        if repetitions == 0:
            new_interval_days = 4
        elif repetitions == 1:
            new_interval_days = 10
        else:
            new_interval_days = max(1, int(interval_days * clamped_ease * 1.3))
        new_ease_factor = min(MAX_EASE_FACTOR, clamped_ease + 0.15)

    next_review = current_time + timedelta(days=new_interval_days)

    return ReviewSchedule(
        repetitions=new_repetitions,
        ease_factor=round(new_ease_factor, 2),
        interval_days=new_interval_days,
        next_review=next_review,
    )
