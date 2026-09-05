import { useEffect, useState } from "react";
import {
  Activity,
  AlertCircle,
  Award,
  BarChart3,
  BookOpen,
  Brain,
  Calendar,
  CheckCircle2,
  FileText,
  Flame,
  HelpCircle,
  Layers,
  ListChecks,
  Lock,
  RefreshCw,
  Sparkles,
  Target,
  Trophy,
  Zap
} from "lucide-react";
import { api } from "../lib/api";
import type {
  Achievement,
  AnalyticsOverview,
  DailyActivity,
  DocumentAnalytics,
  FlashcardAnalytics,
  QuizAnalytics
} from "../types";

export function ProgressDashboard() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [activity, setActivity] = useState<DailyActivity[]>([]);
  const [quizStats, setQuizStats] = useState<QuizAnalytics | null>(null);
  const [flashcardStats, setFlashcardStats] = useState<FlashcardAnalytics | null>(null);
  const [docAnalytics, setDocAnalytics] = useState<DocumentAnalytics[]>([]);
  const [achievements, setAchievements] = useState<Achievement[]>([]);

  const [timeframeDays, setTimeframeDays] = useState<number>(14);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAllData = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const [ov, act, qz, fc, docs, ach] = await Promise.all([
        api.analyticsOverview(),
        api.analyticsActivity(timeframeDays),
        api.analyticsQuiz(),
        api.analyticsFlashcards(),
        api.analyticsDocuments(),
        api.analyticsAchievements()
      ]);

      setOverview(ov);
      setActivity(act);
      setQuizStats(qz);
      setFlashcardStats(fc);
      setDocAnalytics(docs);
      setAchievements(ach);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load learning analytics.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    void loadAllData();
  }, [timeframeDays]);

  if (loading && !overview) {
    return (
      <div className="analytics-loading-state">
        <RefreshCw size={28} className="spin-icon" />
        <p>Analyzing your study activity and retention…</p>
      </div>
    );
  }

  if (error && !overview) {
    return (
      <div className="analytics-error-state">
        <AlertCircle size={32} />
        <h3>Could not load progress data</h3>
        <p>{error}</p>
        <button type="button" className="primary-button" onClick={() => void loadAllData()}>
          <RefreshCw size={16} /> Try Again
        </button>
      </div>
    );
  }

  // Max session value for activity bar scaling
  const maxSessions = Math.max(1, ...activity.map((a) => a.study_sessions));

  return (
    <div className="progress-dashboard">
      {/* Top Header Controls */}
      <div className="dashboard-top-bar">
        <div>
          <h2>Learning Analytics &amp; Student Progress</h2>
          <p className="subtitle">Track your recall consistency, quiz accuracy, and subject mastery over time.</p>
        </div>
        <button
          type="button"
          className="refresh-btn"
          disabled={refreshing}
          onClick={() => void loadAllData(true)}
          title="Refresh analytics data"
        >
          <RefreshCw size={15} className={refreshing ? "spin-icon" : ""} />
          <span>{refreshing ? "Refreshing…" : "Refresh"}</span>
        </button>
      </div>

      {/* 1. Overview Statistics Cards */}
      <section className="overview-metrics-grid">
        <div className="metric-card highlight">
          <div className="metric-header">
            <span className="metric-label">Mastery Score</span>
            <Sparkles size={18} className="metric-icon gold" />
          </div>
          <div className="metric-value-row">
            <span className="metric-number">{overview?.mastery_score ?? 0}%</span>
          </div>
          <div className="metric-progress-bar">
            <div
              className="metric-progress-fill gold"
              style={{ width: `${Math.min(100, overview?.mastery_score ?? 0)}%` }}
            />
          </div>
          <span className="metric-caption">
            Heuristic: Quiz (40%) + Retention (40%) + Activity (20%)
          </span>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Current Streak</span>
            <Flame size={18} className={`metric-icon ${(overview?.current_streak ?? 0) > 0 ? "orange" : ""}`} />
          </div>
          <div className="metric-value-row">
            <span className="metric-number">{overview?.current_streak ?? 0}</span>
            <span className="metric-unit">days</span>
          </div>
          <span className="metric-subtext">
            Longest streak: <strong>{overview?.longest_streak ?? 0} days</strong>
          </span>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Quiz Accuracy</span>
            <Target size={18} className="metric-icon green" />
          </div>
          <div className="metric-value-row">
            <span className="metric-number">{overview?.overall_quiz_accuracy ?? 0}%</span>
          </div>
          <span className="metric-subtext">
            Across <strong>{overview?.quizzes_completed ?? 0}</strong> quizzes completed
          </span>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Flashcard Reviews</span>
            <Brain size={18} className="metric-icon purple" />
          </div>
          <div className="metric-value-row">
            <span className="metric-number">{overview?.flashcards_reviewed ?? 0}</span>
            <span className="metric-unit">reviews</span>
          </div>
          <span className="metric-subtext">
            In <strong>{overview?.total_flashcards ?? 0}</strong> total cards
          </span>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Study Sessions</span>
            <Activity size={18} className="metric-icon blue" />
          </div>
          <div className="metric-value-row">
            <span className="metric-number">{overview?.total_study_sessions ?? 0}</span>
          </div>
          <span className="metric-subtext">
            Over <strong>{overview?.active_study_days ?? 0}</strong> active days
          </span>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Questions Asked</span>
            <HelpCircle size={18} className="metric-icon indigo" />
          </div>
          <div className="metric-value-row">
            <span className="metric-number">{overview?.questions_asked ?? 0}</span>
          </div>
          <span className="metric-subtext">
            Across <strong>{overview?.total_documents ?? 0}</strong> materials
          </span>
        </div>
      </section>

      {/* 2. Study Activity Timeline */}
      <section className="dashboard-section">
        <div className="section-header-row">
          <div>
            <h3><Calendar size={18} /> Study Activity Over Time</h3>
            <p>Daily sessions, quiz submissions, and spaced repetition card reviews.</p>
          </div>
          <div className="timeframe-selector">
            <button
              type="button"
              className={`time-btn ${timeframeDays === 7 ? "active" : ""}`}
              onClick={() => setTimeframeDays(7)}
            >
              7 Days
            </button>
            <button
              type="button"
              className={`time-btn ${timeframeDays === 14 ? "active" : ""}`}
              onClick={() => setTimeframeDays(14)}
            >
              14 Days
            </button>
            <button
              type="button"
              className={`time-btn ${timeframeDays === 30 ? "active" : ""}`}
              onClick={() => setTimeframeDays(30)}
            >
              30 Days
            </button>
          </div>
        </div>

        {activity.length === 0 ? (
          <div className="empty-analytics-box">
            <Calendar size={24} />
            <p>No activity logged yet for this period. Upload a document or ask a question to start!</p>
          </div>
        ) : (
          <div className="activity-chart-container">
            <div className="activity-bars-grid">
              {activity.map((day) => {
                const totalDaily = day.study_sessions;
                const heightPercent = totalDaily === 0 ? 4 : Math.max(12, Math.round((totalDaily / maxSessions) * 100));
                const dateLabel = new Date(day.date + "T00:00:00").toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric"
                });

                return (
                  <div key={day.date} className="activity-col" title={`${day.date}: ${totalDaily} session(s) (${day.quiz_attempts} quizzes, ${day.flashcard_reviews} reviews, ${day.questions_asked} queries)`}>
                    <div className="bar-wrapper">
                      <div
                        className={`bar-fill ${totalDaily > 0 ? "has-activity" : "empty"}`}
                        style={{ height: `${heightPercent}%` }}
                      >
                        {totalDaily > 0 && <span className="bar-val">{totalDaily}</span>}
                      </div>
                    </div>
                    <span className="date-caption">{dateLabel}</span>
                  </div>
                );
              })}
            </div>
            <div className="chart-legend">
              <span className="legend-item"><span className="legend-dot active" /> Active Study Day</span>
              <span className="legend-item"><span className="legend-dot inactive" /> Rest Day</span>
            </div>
          </div>
        )}
      </section>

      {/* 3 & 4. Quiz & Flashcard Performance Two-Column */}
      <div className="dashboard-two-col">
        {/* Quiz Performance */}
        <section className="dashboard-section">
          <div className="section-header-row">
            <div>
              <h3><ListChecks size={18} /> Quiz Performance</h3>
              <p>Test retention and question breakdown.</p>
            </div>
          </div>

          <div className="stats-pill-grid">
            <div className="stat-pill-box">
              <span className="pill-title">Quizzes</span>
              <strong>{quizStats?.quizzes_completed ?? 0}</strong>
            </div>
            <div className="stat-pill-box">
              <span className="pill-title">Questions</span>
              <strong>{quizStats?.total_questions ?? 0}</strong>
            </div>
            <div className="stat-pill-box success">
              <span className="pill-title">Correct</span>
              <strong>{quizStats?.correct_answers ?? 0}</strong>
            </div>
            <div className="stat-pill-box danger">
              <span className="pill-title">Incorrect</span>
              <strong>{quizStats?.incorrect_answers ?? 0}</strong>
            </div>
          </div>

          {(!quizStats || quizStats.quizzes_completed === 0) ? (
            <div className="empty-analytics-box small">
              <ListChecks size={20} />
              <p>No quizzes completed yet. Generate a quiz from any document to test your knowledge!</p>
            </div>
          ) : (
            <div className="recent-quizzes-list">
              <h4>Recent Quiz Attempts</h4>
              {quizStats.recent_quizzes.slice(0, 4).map((q) => (
                <div key={q.id} className="quiz-history-item">
                  <div className="quiz-history-info">
                    <strong>{q.document_name}</strong>
                    <span>{new Date(q.created_at).toLocaleDateString()}</span>
                  </div>
                  <div className="quiz-history-score">
                    <span className="score-badge">{q.score} / {q.total}</span>
                    <strong className={q.accuracy >= 75 ? "text-green" : q.accuracy >= 50 ? "text-amber" : "text-red"}>
                      {q.accuracy}%
                    </strong>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Flashcard Performance */}
        <section className="dashboard-section">
          <div className="section-header-row">
            <div>
              <h3><Layers size={18} /> Flashcard Retention (SM-2)</h3>
              <p>Spaced repetition recall ratings distribution.</p>
            </div>
          </div>

          <div className="stats-pill-grid">
            <div className="stat-pill-box">
              <span className="pill-title">Total Cards</span>
              <strong>{flashcardStats?.total_cards ?? 0}</strong>
            </div>
            <div className="stat-pill-box">
              <span className="pill-title">Total Reviews</span>
              <strong>{flashcardStats?.total_reviews ?? 0}</strong>
            </div>
            <div className="stat-pill-box success">
              <span className="pill-title">Retention</span>
              <strong>{flashcardStats?.retention_rate ?? 0}%</strong>
            </div>
            <div className="stat-pill-box warning">
              <span className="pill-title">Due Cards</span>
              <strong>{flashcardStats?.due_cards ?? 0}</strong>
            </div>
          </div>

          <div className="rating-distribution-panel">
            <h4>Recall Rating Distribution</h4>
            <div className="rating-bars-stack">
              <div className="rating-bar-row">
                <span className="rating-name again">Again</span>
                <div className="rating-track">
                  <div
                    className="rating-track-fill again"
                    style={{
                      width: `${
                        (flashcardStats?.total_reviews ?? 0) > 0
                          ? Math.round(((flashcardStats?.ratings.again ?? 0) / flashcardStats!.total_reviews) * 100)
                          : 0
                      }%`
                    }}
                  />
                </div>
                <span className="rating-count">{flashcardStats?.ratings.again ?? 0}</span>
              </div>

              <div className="rating-bar-row">
                <span className="rating-name hard">Hard</span>
                <div className="rating-track">
                  <div
                    className="rating-track-fill hard"
                    style={{
                      width: `${
                        (flashcardStats?.total_reviews ?? 0) > 0
                          ? Math.round(((flashcardStats?.ratings.hard ?? 0) / flashcardStats!.total_reviews) * 100)
                          : 0
                      }%`
                    }}
                  />
                </div>
                <span className="rating-count">{flashcardStats?.ratings.hard ?? 0}</span>
              </div>

              <div className="rating-bar-row">
                <span className="rating-name good">Good</span>
                <div className="rating-track">
                  <div
                    className="rating-track-fill good"
                    style={{
                      width: `${
                        (flashcardStats?.total_reviews ?? 0) > 0
                          ? Math.round(((flashcardStats?.ratings.good ?? 0) / flashcardStats!.total_reviews) * 100)
                          : 0
                      }%`
                    }}
                  />
                </div>
                <span className="rating-count">{flashcardStats?.ratings.good ?? 0}</span>
              </div>

              <div className="rating-bar-row">
                <span className="rating-name easy">Easy</span>
                <div className="rating-track">
                  <div
                    className="rating-track-fill easy"
                    style={{
                      width: `${
                        (flashcardStats?.total_reviews ?? 0) > 0
                          ? Math.round(((flashcardStats?.ratings.easy ?? 0) / flashcardStats!.total_reviews) * 100)
                          : 0
                      }%`
                    }}
                  />
                </div>
                <span className="rating-count">{flashcardStats?.ratings.easy ?? 0}</span>
              </div>
            </div>
            <div className="ease-factor-note">
              <span>Average Card Ease Factor: <strong>{flashcardStats?.average_ease_factor ?? 2.5}</strong></span>
            </div>
          </div>
        </section>
      </div>

      {/* 5. Document / Subject Progress */}
      <section className="dashboard-section">
        <div className="section-header-row">
          <div>
            <h3><BookOpen size={18} /> Subject &amp; Document Progress</h3>
            <p>Individual completion metrics and estimated mastery per material.</p>
          </div>
        </div>

        {docAnalytics.length === 0 ? (
          <div className="empty-analytics-box">
            <FileText size={24} />
            <p>No study materials uploaded yet. Add your PDFs to view subject progress!</p>
          </div>
        ) : (
          <div className="document-progress-grid">
            {docAnalytics.map((doc) => (
              <div key={doc.id} className="doc-progress-card">
                <div className="doc-card-header">
                  <div className="doc-icon-wrap">
                    <FileText size={18} />
                  </div>
                  <div className="doc-titles">
                    <h4 title={doc.filename}>{doc.filename}</h4>
                    <span>{doc.pages} pages · {doc.chunks} chunks</span>
                  </div>
                  <div className="doc-mastery-badge">
                    <strong>{doc.mastery_score}%</strong>
                    <small>Mastery</small>
                  </div>
                </div>

                <div className="doc-mastery-bar">
                  <div
                    className="doc-mastery-fill"
                    style={{ width: `${Math.min(100, doc.mastery_score)}%` }}
                  />
                </div>

                <div className="doc-metrics-row">
                  <div>
                    <span className="lbl">Flashcards</span>
                    <strong>{doc.flashcards_count}</strong>
                  </div>
                  <div>
                    <span className="lbl">Reviews</span>
                    <strong>{doc.flashcards_reviewed_count}</strong>
                  </div>
                  <div>
                    <span className="lbl">Quizzes</span>
                    <strong>{doc.quizzes_completed}</strong>
                  </div>
                  <div>
                    <span className="lbl">Quiz Acc.</span>
                    <strong>{doc.quiz_accuracy}%</strong>
                  </div>
                  <div>
                    <span className="lbl">Activity</span>
                    <strong>{doc.study_sessions}</strong>
                  </div>
                </div>

                {doc.last_studied_at && (
                  <div className="doc-last-active">
                    Last active: {new Date(doc.last_studied_at).toLocaleDateString()}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* 6. Achievements & Milestones */}
      <section className="dashboard-section">
        <div className="section-header-row">
          <div>
            <h3><Trophy size={18} /> Learning Milestones &amp; Achievements</h3>
            <p>Deterministic milestones earned from consistent study effort.</p>
          </div>
          <div className="achievements-badge-count">
            <Award size={16} />
            <span>
              {achievements.filter((a) => a.unlocked).length} / {achievements.length} Unlocked
            </span>
          </div>
        </div>

        <div className="achievements-grid">
          {achievements.map((ach) => {
            const isUnlocked = ach.unlocked;

            return (
              <div key={ach.id} className={`achievement-card ${isUnlocked ? "unlocked" : "locked"}`}>
                <div className="ach-icon-circle">
                  {isUnlocked ? <Trophy size={20} className="trophy-gold" /> : <Lock size={18} className="lock-icon" />}
                </div>
                <div className="ach-body">
                  <div className="ach-title-row">
                    <h4>{ach.title}</h4>
                    {isUnlocked && <span className="unlocked-tag"><CheckCircle2 size={12} /> Earned</span>}
                  </div>
                  <p>{ach.description}</p>
                  {!isUnlocked && (
                    <div className="ach-progress-wrap">
                      <div className="ach-progress-bar">
                        <div className="ach-progress-fill" style={{ width: `${ach.progress}%` }} />
                      </div>
                      <span className="ach-progress-pct">{ach.progress}%</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
