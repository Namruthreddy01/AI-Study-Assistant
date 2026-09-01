export type DocumentItem = {
  id: string;
  filename: string;
  pages: number;
  chunks: number;
  status: "processed" | "failed";
  created_at: string;
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


