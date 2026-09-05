export type DocumentItem = {
  id: string;
  filename: string;
  pages: number;
  chunks: number;
  status: "processed" | "failed";
  created_at: string;
  flashcard_count?: number;
};

export type DocumentDetail = {
  id: string;
  filename: string;
  pages: number;
  chunks: number;
  status: "processed" | "failed";
  created_at: string;
  flashcard_count: number;
};

export type DocumentDeleteResponse = {
  id: string;
  filename: string;
  deleted: boolean;
  message: string;
};

export type Source = {
  filename: string;
  page: number;
  chunk_id: string;
  excerpt: string;
  score: number;
};

export type ChatMessage = {
  role: "student" | "assistant";
  content: string;
  sources?: Source[];
};

export type Summary = {
  overview: string;
  key_points: string[];
  important_concepts: string[];
  exam_focus: string[];
};

export type Mcq = {
  id: string;
  question: string;
  options: string[];
  correct_answer: number;
  explanation: string;
};

export type RevisionQuestion = {
  id: string;
  question: string;
  type: "short-answer" | "conceptual" | "long-answer";
  difficulty: string;
};

export type QuizScore = {
  score: number;
  total: number;
  percentage: number;
  results: {
    question_id: string;
    selected_answer: number | null;
    correct_answer: number;
    is_correct: boolean;
    explanation: string;
  }[];
};

export type HistoryItem = {
  id: string;
  activity: string;
  document_id: string;
  document_name: string;
  created_at: string;
  detail: string;
};

export type Flashcard = {
  id: string;
  document_id: string;
  question: string;
  answer: string;
  source_page: number;
  source_filename: string;
  difficulty: string;
  repetitions: number;
  ease_factor: number;
  interval_days: number;
  next_review: string;
  last_reviewed?: string | null;
  created_at: string;
  is_due: boolean;
};

export type FlashcardRating = "again" | "hard" | "good" | "easy";

export type FlashcardListResponse = {
  document_id?: string | null;
  cards: Flashcard[];
  total: number;
  due_count: number;
  new_count: number;
  learning_count: number;
};

export type FlashcardReviewResponse = {
  card: Flashcard;
  rating: FlashcardRating;
  previous_interval: number;
  new_interval: number;
  previous_ease_factor: number;
  new_ease_factor: number;
  next_review: string;
};

export type AnalyticsOverview = {
  total_study_sessions: number;
  questions_asked: number;
  quizzes_completed: number;
  flashcards_reviewed: number;
  overall_quiz_accuracy: number;
  current_streak: number;
  longest_streak: number;
  active_study_days: number;
  last_study_date: string | null;
  total_documents: number;
  total_flashcards: number;
  mastery_score: number;
};

export type DailyActivity = {
  date: string;
  study_sessions: number;
  quiz_attempts: number;
  flashcard_reviews: number;
  questions_asked: number;
};

export type QuizAttempt = {
  id: string;
  document_id: string;
  document_name: string;
  score: number;
  total: number;
  accuracy: number;
  created_at: string;
};

export type QuizAnalytics = {
  quizzes_completed: number;
  total_questions: number;
  correct_answers: number;
  incorrect_answers: number;
  overall_accuracy: number;
  difficulty_breakdown: Record<string, number>;
  recent_quizzes: QuizAttempt[];
};

export type FlashcardRatingsBreakdown = {
  again: number;
  hard: number;
  good: number;
  easy: number;
};

export type FlashcardAnalytics = {
  total_cards: number;
  new_cards: number;
  learning_cards: number;
  due_cards: number;
  reviewed_cards: number;
  total_reviews: number;
  ratings: FlashcardRatingsBreakdown;
  average_ease_factor: number;
  retention_rate: number;
};

export type DocumentAnalytics = {
  id: string;
  filename: string;
  pages: number;
  chunks: number;
  flashcards_count: number;
  flashcards_reviewed_count: number;
  quizzes_completed: number;
  quiz_accuracy: number;
  study_sessions: number;
  questions_asked: number;
  mastery_score: number;
  last_studied_at: string | null;
};

export type Achievement = {
  id: string;
  title: string;
  description: string;
  icon: string;
  unlocked: boolean;
  progress: number;
  unlocked_at?: string | null;
};



