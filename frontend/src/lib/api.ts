import type {
  ChatMessage,
  DocumentDeleteResponse,
  DocumentDetail,
  DocumentItem,
  Flashcard,
  FlashcardListResponse,
  FlashcardRating,
  FlashcardReviewResponse,
  HistoryItem,
  Mcq,
  QuizScore,
  RevisionQuestion,
  Summary
} from "../types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(API_URL + path, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || "Something went wrong. Please try again.");
  }
  return response.json() as Promise<T>;
}

export const api = {
  documents: () => request<DocumentItem[]>("/api/documents"),
  documentDetails: (id: string) => request<DocumentDetail>(`/api/documents/${id}`),
  deleteDocument: (id: string) =>
    request<DocumentDeleteResponse>(`/api/documents/${id}`, { method: "DELETE" }),
  upload: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<DocumentItem>("/api/documents/upload", { method: "POST", body: form });
  },
  chat: (documentIds: string | string[], question: string) => {
    const ids = Array.isArray(documentIds) ? documentIds : [documentIds];
    return request<{ answer: string; sources: ChatMessage["sources"]; grounded: boolean }>(
      "/api/study/chat",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document_ids: ids, question })
      }
    );
  },
  summary: (documentIds: string | string[], length: "short" | "detailed" = "short") => {
    const ids = Array.isArray(documentIds) ? documentIds : [documentIds];
    return request<Summary>("/api/study/summary", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_ids: ids, length })
    });
  },
  mcqs: (documentId: string, count: number, difficulty: string) =>
    request<{ document_id: string; questions: Mcq[] }>("/api/study/mcqs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_id: documentId, count, difficulty })
    }),
  revision: (documentId: string, count: number, difficulty: string) =>
    request<{ questions: RevisionQuestion[] }>("/api/study/revision", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_id: documentId, count, difficulty })
    }),
  generateFlashcards: (documentId: string, count: number, difficulty: string) =>
    request<Flashcard[]>("/api/study/flashcards", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_id: documentId, count, difficulty })
    }),
  listFlashcards: (documentId?: string, dueOnly?: boolean) => {
    const params = new URLSearchParams();
    if (documentId) params.append("document_id", documentId);
    if (dueOnly) params.append("due_only", "true");
    const query = params.toString() ? `?${params.toString()}` : "";
    return request<FlashcardListResponse>(`/api/study/flashcards${query}`);
  },
  reviewFlashcard: (flashcardId: string, rating: FlashcardRating) =>
    request<FlashcardReviewResponse>(`/api/study/flashcards/${flashcardId}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rating })
    }),
  scoreQuiz: (documentId: string, questions: Mcq[], answers: Record<string, number>) =>
    request<QuizScore>("/api/study/quiz/score", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_id: documentId, questions, answers })
    }),
  history: () => request<HistoryItem[]>("/api/study/history")
};

