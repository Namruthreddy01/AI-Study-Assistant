import { useState } from "react";
import {
  ArrowLeft,
  BookOpen,
  Calendar,
  CheckCircle,
  Eye,
  FileText,
  Flame,
  GraduationCap,
  Layers,
  RotateCcw,
  Sparkles,
  Zap
} from "lucide-react";
import type { Flashcard, FlashcardRating } from "../types";

type Props = {
  cards: Flashcard[];
  dueCount: number;
  newCount: number;
  learningCount: number;
  busy: boolean;
  disabled: boolean;
  difficulty: string;
  onDifficultyChange: (diff: string) => void;
  onGenerate: (count: number) => Promise<void>;
  onReview: (cardId: string, rating: FlashcardRating) => Promise<void>;
  onRefresh: () => Promise<void>;
};

export function FlashcardPanel({
  cards,
  dueCount,
  newCount,
  learningCount,
  busy,
  disabled,
  difficulty,
  onDifficultyChange,
  onGenerate,
  onReview,
  onRefresh
}: Props) {
  const [studying, setStudying] = useState(false);
  const [filterDueOnly, setFilterDueOnly] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [countToGenerate, setCountToGenerate] = useState(10);
  const [sessionRatings, setSessionRatings] = useState<Record<FlashcardRating, number>>({
    again: 0,
    hard: 0,
    good: 0,
    easy: 0
  });
  const [sessionCompleted, setSessionCompleted] = useState(false);

  const activeCards = filterDueOnly ? cards.filter((c) => c.is_due) : cards;
  const currentCard = activeCards[currentIndex];

  const startSession = (dueOnly: boolean) => {
    setFilterDueOnly(dueOnly);
    setCurrentIndex(0);
    setIsFlipped(false);
    setSessionCompleted(false);
    setSessionRatings({ again: 0, hard: 0, good: 0, easy: 0 });
    setStudying(true);
  };

  const handleRating = async (rating: FlashcardRating) => {
    if (!currentCard || busy) return;
    setSessionRatings((prev) => ({ ...prev, [rating]: prev[rating] + 1 }));
    await onReview(currentCard.id, rating);

    if (currentIndex + 1 < activeCards.length) {
      setIsFlipped(false);
      setCurrentIndex((idx) => idx + 1);
    } else {
      setSessionCompleted(true);
    }
  };

  const finishSession = () => {
    setStudying(false);
    setSessionCompleted(false);
    void onRefresh();
  };

  // 1. Session Complete View
  if (studying && sessionCompleted) {
    const totalReviewed = Object.values(sessionRatings).reduce((a, b) => a + b, 0);
    return (
      <section className="flashcard-complete-card">
        <div className="complete-icon">
          <GraduationCap size={44} />
        </div>
        <h2>Session Complete!</h2>
        <p>You reviewed {totalReviewed} flashcard{totalReviewed === 1 ? "" : "s"} and scheduled your next reviews.</p>

        <div className="session-stats-grid">
          <div className="stat-pill again">
            <strong>{sessionRatings.again}</strong>
            <span>Again</span>
          </div>
          <div className="stat-pill hard">
            <strong>{sessionRatings.hard}</strong>
            <span>Hard</span>
          </div>
          <div className="stat-pill good">
            <strong>{sessionRatings.good}</strong>
            <span>Good</span>
          </div>
          <div className="stat-pill easy">
            <strong>{sessionRatings.easy}</strong>
            <span>Easy</span>
          </div>
        </div>

        <div className="complete-actions">
          <button className="secondary-button" onClick={finishSession}>
            <ArrowLeft size={16} /> Back to Deck
          </button>
          <button className="primary-button" onClick={() => startSession(false)}>
            <RotateCcw size={16} /> Study Deck Again
          </button>
        </div>
      </section>
    );
  }

  // 2. Interactive Study Mode
  if (studying && currentCard) {
    const progressPercent = Math.round(((currentIndex + 1) / activeCards.length) * 100);

    return (
      <section className="flashcard-study-shell">
        <div className="study-header">
          <button className="back-link" onClick={() => setStudying(false)}>
            <ArrowLeft size={16} /> Exit Review
          </button>
          <div className="study-progress">
            <span>
              Card <strong>{currentIndex + 1}</strong> of <strong>{activeCards.length}</strong>
            </span>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progressPercent}%` }} />
            </div>
          </div>
        </div>

        <div className={`flashcard-item ${isFlipped ? "flipped" : ""}`} onClick={() => !isFlipped && setIsFlipped(true)}>
          <div className="card-face card-front">
            <div className="card-header">
              <span className="card-badge question-badge">QUESTION</span>
              <span className="difficulty-badge">{currentCard.difficulty}</span>
            </div>
            <div className="card-body">
              <h3>{currentCard.question}</h3>
            </div>
            <div className="card-footer">
              <span className="hint-text">
                <BookOpen size={14} /> Page {currentCard.source_page}
              </span>
              <button
                type="button"
                className="flip-prompt-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsFlipped(true);
                }}
              >
                <Eye size={16} /> Show Answer
              </button>
            </div>
          </div>

          <div className="card-face card-back">
            <div className="card-header">
              <span className="card-badge answer-badge">ANSWER</span>
              <span className="difficulty-badge">{currentCard.difficulty}</span>
            </div>
            <div className="card-body">
              <p className="answer-text">{currentCard.answer}</p>
              <div className="source-citation">
                <FileText size={15} />
                <span>
                  <strong>{currentCard.source_filename}</strong> · Page {currentCard.source_page}
                </span>
              </div>
            </div>
            <div className="card-srs-panel">
              <p className="rating-prompt">How well did you remember this?</p>
              <div className="rating-buttons">
                <button
                  type="button"
                  className="rating-btn again"
                  disabled={busy}
                  onClick={(e) => {
                    e.stopPropagation();
                    void handleRating("again");
                  }}
                >
                  <strong>Again</strong>
                  <small>&lt; 1 day</small>
                </button>
                <button
                  type="button"
                  className="rating-btn hard"
                  disabled={busy}
                  onClick={(e) => {
                    e.stopPropagation();
                    void handleRating("hard");
                  }}
                >
                  <strong>Hard</strong>
                  <small>+1d / slow</small>
                </button>
                <button
                  type="button"
                  className="rating-btn good"
                  disabled={busy}
                  onClick={(e) => {
                    e.stopPropagation();
                    void handleRating("good");
                  }}
                >
                  <strong>Good</strong>
                  <small>Standard</small>
                </button>
                <button
                  type="button"
                  className="rating-btn easy"
                  disabled={busy}
                  onClick={(e) => {
                    e.stopPropagation();
                    void handleRating("easy");
                  }}
                >
                  <strong>Easy</strong>
                  <small>+4d / boost</small>
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
    );
  }

  // 3. Deck Overview Mode
  return (
    <section className="flashcard-deck-overview">
      <div className="deck-stats-banner">
        <div className="stat-box">
          <Layers size={20} className="stat-icon" />
          <div>
            <strong>{cards.length}</strong>
            <span>Total Cards</span>
          </div>
        </div>
        <div className="stat-box due">
          <Flame size={20} className="stat-icon due-icon" />
          <div>
            <strong>{dueCount}</strong>
            <span>Due Today</span>
          </div>
        </div>
        <div className="stat-box new">
          <Sparkles size={20} className="stat-icon new-icon" />
          <div>
            <strong>{newCount}</strong>
            <span>New Cards</span>
          </div>
        </div>
        <div className="stat-box learning">
          <Zap size={20} className="stat-icon learning-icon" />
          <div>
            <strong>{learningCount}</strong>
            <span>In Review</span>
          </div>
        </div>
      </div>

      <div className="deck-actions-bar">
        <div className="generator-inputs">
          <select
            value={countToGenerate}
            onChange={(e) => setCountToGenerate(Number(e.target.value))}
            disabled={busy || disabled}
          >
            <option value={5}>5 Cards</option>
            <option value={10}>10 Cards</option>
            <option value={15}>15 Cards</option>
            <option value={20}>20 Cards</option>
          </select>
          <select
            value={difficulty}
            onChange={(e) => onDifficultyChange(e.target.value)}
            disabled={busy || disabled}
          >
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
          <button
            type="button"
            className="primary-button"
            disabled={busy || disabled}
            onClick={() => void onGenerate(countToGenerate)}
          >
            <Sparkles size={16} />
            {busy ? "Generating…" : `Generate ${countToGenerate} Flashcards`}
          </button>
        </div>

        {cards.length > 0 && (
          <div className="study-start-actions">
            {dueCount > 0 && (
              <button
                type="button"
                className="study-due-btn"
                onClick={() => startSession(true)}
              >
                <Flame size={16} /> Review {dueCount} Due Card{dueCount === 1 ? "" : "s"}
              </button>
            )}
            <button
              type="button"
              className="study-all-btn"
              onClick={() => startSession(false)}
            >
              <GraduationCap size={16} /> Study All ({cards.length})
            </button>
          </div>
        )}
      </div>

      {!cards.length ? (
        <div className="empty-state">
          <Layers size={36} />
          <p>No flashcards generated for this document yet. Click &ldquo;Generate Flashcards&rdquo; above to create your spaced repetition deck!</p>
        </div>
      ) : (
        <div className="flashcard-deck-preview">
          <h3>Deck Cards ({cards.length})</h3>
          <div className="cards-grid">
            {cards.map((card, idx) => {
              const reviewDate = new Date(card.next_review).toLocaleDateString();
              return (
                <article key={card.id} className="preview-card">
                  <div className="preview-header">
                    <span className="card-number">#{idx + 1}</span>
                    <div className="preview-badges">
                      {card.is_due ? (
                        <span className="due-tag">DUE</span>
                      ) : (
                        <span className="scheduled-tag">
                          <Calendar size={12} /> {reviewDate}
                        </span>
                      )}
                      <span className="difficulty-tag">{card.difficulty}</span>
                    </div>
                  </div>
                  <h4>{card.question}</h4>
                  <p className="preview-answer">{card.answer}</p>
                  <div className="preview-footer">
                    <span className="source-tag">
                      <FileText size={12} /> Page {card.source_page}
                    </span>
                    <span className="srs-stats">
                      Rep: {card.repetitions} · {card.interval_days}d interval
                    </span>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      )}
    </section>
  );
}
