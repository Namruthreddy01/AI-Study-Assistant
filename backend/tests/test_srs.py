from datetime import UTC, datetime, timedelta
import pytest

from app.core.errors import StudyAssistantError
from app.services.srs import calculate_review_schedule


def test_srs_initial_ratings() -> None:
    now = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)

    # Initial Again: reset repetitions and interval to 0 (due today), decrease ease factor
    again = calculate_review_schedule("again", repetitions=0, ease_factor=2.5, interval_days=0, now=now)
    assert again.repetitions == 0
    assert again.interval_days == 0
    assert again.ease_factor == 2.3
    assert again.next_review == now

    # Initial Hard: interval 1 day, ease factor reduced
    hard = calculate_review_schedule("hard", repetitions=0, ease_factor=2.5, interval_days=0, now=now)
    assert hard.repetitions == 1
    assert hard.interval_days == 1
    assert hard.ease_factor == 2.35
    assert hard.next_review == now + timedelta(days=1)

    # Initial Good: interval 1 day, ease factor unchanged
    good = calculate_review_schedule("good", repetitions=0, ease_factor=2.5, interval_days=0, now=now)
    assert good.repetitions == 1
    assert good.interval_days == 1
    assert good.ease_factor == 2.5
    assert good.next_review == now + timedelta(days=1)

    # Initial Easy: interval 4 days, ease factor increased
    easy = calculate_review_schedule("easy", repetitions=0, ease_factor=2.5, interval_days=0, now=now)
    assert easy.repetitions == 1
    assert easy.interval_days == 4
    assert easy.ease_factor == 2.65
    assert easy.next_review == now + timedelta(days=4)


def test_srs_subsequent_ratings() -> None:
    now = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)

    # Good at rep 1 -> interval becomes 6 days
    good_rep1 = calculate_review_schedule("good", repetitions=1, ease_factor=2.5, interval_days=1, now=now)
    assert good_rep1.repetitions == 2
    assert good_rep1.interval_days == 6
    assert good_rep1.ease_factor == 2.5
    assert good_rep1.next_review == now + timedelta(days=6)

    # Good at rep 2 -> interval becomes int(6 * 2.5) = 15 days
    good_rep2 = calculate_review_schedule("good", repetitions=2, ease_factor=2.5, interval_days=6, now=now)
    assert good_rep2.repetitions == 3
    assert good_rep2.interval_days == 15
    assert good_rep2.ease_factor == 2.5
    assert good_rep2.next_review == now + timedelta(days=15)

    # Easy at rep 1 -> interval becomes 10 days
    easy_rep1 = calculate_review_schedule("easy", repetitions=1, ease_factor=2.65, interval_days=4, now=now)
    assert easy_rep1.repetitions == 2
    assert easy_rep1.interval_days == 10
    assert easy_rep1.ease_factor == 2.80

    # Hard at rep 2 -> interval becomes max(1, int(15 * 1.2)) = 18 days
    hard_rep2 = calculate_review_schedule("hard", repetitions=2, ease_factor=2.5, interval_days=15, now=now)
    assert hard_rep2.repetitions == 3
    assert hard_rep2.interval_days == 18
    assert hard_rep2.ease_factor == 2.35

    # Again at high repetition -> resets repetitions and interval to 0
    again_reset = calculate_review_schedule("again", repetitions=5, ease_factor=2.5, interval_days=30, now=now)
    assert again_reset.repetitions == 0
    assert again_reset.interval_days == 0
    assert again_reset.ease_factor == 2.3


def test_srs_ease_factor_bounds() -> None:
    now = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)

    # Minimum ease floor 1.3
    low = calculate_review_schedule("again", repetitions=0, ease_factor=1.35, interval_days=0, now=now)
    assert low.ease_factor == 1.3

    # Maximum ease ceiling 3.0
    high = calculate_review_schedule("easy", repetitions=0, ease_factor=2.95, interval_days=0, now=now)
    assert high.ease_factor == 3.0


def test_srs_invalid_rating() -> None:
    with pytest.raises(StudyAssistantError, match="Invalid rating"):
        calculate_review_schedule("perfect", repetitions=0, ease_factor=2.5, interval_days=0)
