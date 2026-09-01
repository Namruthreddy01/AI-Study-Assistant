import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  BookOpenCheck,
  BrainCircuit,
  ChevronRight,
  ClipboardList,
  FileQuestion,
  Files,
  FileText,
  History,
  Layers,
  LayoutDashboard,
  Lightbulb,
  ListChecks,
  Sparkles
} from "lucide-react";
import { api } from "./lib/api";
import { ChatPanel } from "./components/ChatPanel";
import { DocumentLibrary } from "./components/DocumentLibrary";
import { DocumentUploader } from "./components/DocumentUploader";
import { FlashcardPanel } from "./components/FlashcardPanel";
import { QuizPanel } from "./components/QuizPanel";
import type {
  ChatMessage,
  DocumentItem,
  Flashcard,
  FlashcardRating,
  HistoryItem,
  Mcq,
  QuizScore,
  RevisionQuestion,
  Summary
} from "./types";

type View =
  | "dashboard"
  | "materials"
  | "ask"
  | "summary"
  | "mcqs"
  | "flashcards"
  | "revision"
  | "history";

const nav = [
  { id: "dashboard" as View, label: "Overview", icon: LayoutDashboard },
  { id: "materials" as View, label: "Materials", icon: Files },
  { id: "ask" as View, label: "Ask AI", icon: BrainCircuit },
  { id: "summary" as View, label: "Summary", icon: FileText },
  { id: "mcqs" as View, label: "MCQ Quiz", icon: ListChecks },
  { id: "flashcards" as View, label: "Flashcards", icon: Layers },
  { id: "revision" as View, label: "Revision", icon: FileQuestion },
  { id: "history" as View, label: "Study history", icon: History }
];

export default function App() {
  const [view, setView] = useState<View>("dashboard");
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [mcqs, setMcqs] = useState<Mcq[]>([]);
  const [revision, setRevision] = useState<RevisionQuestion[]>([]);
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);
  const [flashcardStats, setFlashcardStats] = useState({
    due_count: 0,
    new_count: 0,
    learning_count: 0
  });
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [quizResult, setQuizResult] = useState<QuizScore | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [difficulty, setDifficulty] = useState("medium");
  const [working, setWorking] = useState(false);
  const [notice, setNotice] = useState("");

  const selectedDocs = useMemo(
    () => documents.filter((doc) => selectedDocIds.includes(doc.id)),
    [documents, selectedDocIds]
  );

  const singleActiveDoc = selectedDocIds.length === 1 ? selectedDocs[0] : null;

  const refreshDocuments = async () => {
    try {
      const items = await api.documents();
      setDocuments(items);
      return items;
    } catch {
      setNotice("Start the FastAPI server to connect your study workspace.");
      return [];
    }
  };

  useEffect(() => {
    void refreshDocuments().then((items) => {
      if (items.length > 0) {
        setSelectedDocIds(items.map((d) => d.id));
        void loadFlashcards(items[0].id);
      }
    });
  }, []);

  const execute = async (action: () => Promise<void>) => {
    setWorking(true);
    setNotice("");
    try {
      await action();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Something went wrong.");
    } finally {
      setWorking(false);
    }
  };

  const loadFlashcards = async (docId?: string) => {
    const targetId = docId ?? (selectedDocIds.length === 1 ? selectedDocIds[0] : undefined);
    if (!targetId) return;
    try {
      const response = await api.listFlashcards(targetId);
      setFlashcards(response.cards);
      setFlashcardStats({
        due_count: response.due_count,
        new_count: response.new_count,
        learning_count: response.learning_count
      });
    } catch {
      // Handled gracefully
    }
  };

  const upload = async (file: File) => {
    await execute(async () => {
      const document = await api.upload(file);
      setDocuments((items) => [document, ...items]);
      setSelectedDocIds((prev) => [document.id, ...prev]);
      setMessages([]);
      setFlashcards([]);
      setFlashcardStats({ due_count: 0, new_count: 0, learning_count: 0 });
      setNotice(document.filename + " is processed and ready to study.");
    });
  };

  const toggleDoc = (id: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const selectAllDocs = () => {
    setSelectedDocIds(documents.map((d) => d.id));
  };

  const deselectAllDocs = () => {
    setSelectedDocIds([]);
  };

  const deleteDoc = async (id: string) => {
    await execute(async () => {
      const res = await api.deleteDocument(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
      setSelectedDocIds((prev) => prev.filter((item) => item !== id));
      setNotice(res.message);
    });
  };

  const ask = async (question: string) => {
    if (selectedDocIds.length === 0) {
      setNotice("Please select at least one study material.");
      return;
    }
    setMessages((items) => [...items, { role: "student", content: question }]);
    await execute(async () => {
      const response = await api.chat(selectedDocIds, question);
      setMessages((items) => [
        ...items,
        { role: "assistant", content: response.answer, sources: response.sources }
      ]);
    });
  };

  const makeSummary = async () => {
    if (selectedDocIds.length === 0) {
      setNotice("Please select at least one study material.");
      return;
    }
    await execute(async () => {
      setSummary(await api.summary(selectedDocIds));
      setView("summary");
    });
  };

  const makeMcqs = async () => {
    if (!singleActiveDoc) {
      setNotice("Please select exactly one material for MCQ practice.");
      return;
    }
    await execute(async () => {
      const response = await api.mcqs(singleActiveDoc.id, 8, difficulty);
      setMcqs(response.questions);
      setAnswers({});
      setQuizResult(null);
      setView("mcqs");
    });
  };

  const makeRevision = async () => {
    if (!singleActiveDoc) {
      setNotice("Please select exactly one material for revision questions.");
      return;
    }
    await execute(async () => {
      const response = await api.revision(singleActiveDoc.id, 8, difficulty);
      setRevision(response.questions);
      setView("revision");
    });
  };

  const makeFlashcards = async (count: number) => {
    if (!singleActiveDoc) {
      setNotice("Please select exactly one material to generate flashcards.");
      return;
    }
    await execute(async () => {
      await api.generateFlashcards(singleActiveDoc.id, count, difficulty);
      await loadFlashcards(singleActiveDoc.id);
      setNotice(`Generated ${count} flashcards for ${singleActiveDoc.filename}.`);
    });
  };

  const reviewCard = async (cardId: string, rating: FlashcardRating) => {
    if (!singleActiveDoc) return;
    await execute(async () => {
      await api.reviewFlashcard(cardId, rating);
      await loadFlashcards(singleActiveDoc.id);
    });
  };

  const submitQuiz = async () => {
    if (!singleActiveDoc || !mcqs.length) return;
    await execute(async () => setQuizResult(await api.scoreQuiz(singleActiveDoc.id, mcqs, answers)));
  };

  const loadHistory = async () => {
    setView("history");
    await execute(async () => setHistory(await api.history()));
  };

  const title: Record<View, string> = {
    dashboard: "Your study space",
    materials: "Study materials library",
    ask: "Ask AI (Cross-Document)",
    summary: "Smart summary",
    mcqs: "Knowledge check",
    flashcards: "AI Flashcards & SRS",
    revision: "Revision questions",
    history: "Study history"
  };

  const selectedCountLabel =
    selectedDocIds.length === 0
      ? "No material selected"
      : selectedDocIds.length === 1
      ? singleActiveDoc?.filename || "1 material selected"
      : `${selectedDocIds.length} materials selected`;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Sparkles size={19} /></div>
          <span>study<span>wise</span></span>
        </div>
        <nav>
          <p className="nav-label">WORKSPACE</p>
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                className={"nav-item " + (view === item.id ? "active" : "")}
                onClick={() => {
                  if (item.id === "history") void loadHistory();
                  else if (item.id === "flashcards") {
                    if (singleActiveDoc) void loadFlashcards(singleActiveDoc.id);
                    setView("flashcards");
                  } else setView(item.id);
                }}
              >
                <Icon size={18} /> {item.label}
              </button>
            );
          })}
        </nav>
        <div className="sidebar-tip">
          <Lightbulb size={19} />
          <strong>Study smarter</strong>
          <p>Select multiple documents to synthesize across your course modules.</p>
        </div>
      </aside>

      <main>
        <header className="topbar">
          <div>
            <p className="eyebrow">STUDENT WORKSPACE</p>
            <h1>{title[view]}</h1>
          </div>
          <div className="topbar-scope-widget">
            <button
              type="button"
              className={`scope-pill-btn ${selectedDocIds.length > 0 ? "has-selection" : ""}`}
              onClick={() => setView("materials")}
              title="Click to manage and select materials"
            >
              <BookOpenCheck size={16} />
              <span>{selectedCountLabel}</span>
            </button>
          </div>
        </header>

        {notice && <div className="notice">{notice}</div>}

        {view === "dashboard" && (
          <div className="page">
            <section className="hero">
              <div>
                <span className="eyebrow">MULTI-DOCUMENT STUDY COMPANION</span>
                <h2>Turn multiple lecture notes into connected understanding.</h2>
                <p>Upload and select your materials. Ask questions across chapters, generate combined summaries, and test with flashcards.</p>
                <div className="hero-button-group">
                  <button className="hero-link" onClick={() => setView("materials")}>
                    Manage Materials ({documents.length}) <ChevronRight size={17} />
                  </button>
                  <button className="secondary-button" onClick={() => setView("ask")}>
                    Ask AI Cross-Document
                  </button>
                </div>
              </div>
              <div className="hero-orb"><BrainCircuit size={68} /></div>
            </section>
            <DocumentUploader busy={working} onUpload={upload} />
            <section className="stats">
              <div><span>Total Materials</span><strong>{documents.length}</strong><small>in your library</small></div>
              <div><span>Pages indexed</span><strong>{documents.reduce((sum, item) => sum + item.pages, 0)}</strong><small>across your PDFs</small></div>
              <div><span>Active Scope</span><strong>{selectedDocIds.length}</strong><small>selected for study</small></div>
            </section>
            {singleActiveDoc ? (
              <DocumentCard document={singleActiveDoc} />
            ) : selectedDocs.length > 1 ? (
              <div className="multi-doc-active-card">
                <Files size={24} />
                <div>
                  <strong>{selectedDocs.length} Materials Active in Study Scope</strong>
                  <p>{selectedDocs.map((d) => d.filename).join(" · ")}</p>
                </div>
              </div>
            ) : (
              <div className="empty-state">Your uploaded materials will appear here.</div>
            )}
          </div>
        )}

        {view === "materials" && (
          <div className="page">
            <section className="section-heading">
              <div>
                <span className="eyebrow">COURSE MODULES &amp; PDFs</span>
                <h2>Manage your study materials</h2>
              </div>
            </section>
            <DocumentLibrary
              documents={documents}
              selectedDocIds={selectedDocIds}
              busy={working}
              onToggleDoc={toggleDoc}
              onSelectAll={selectAllDocs}
              onDeselectAll={deselectAllDocs}
              onUpload={upload}
              onDeleteDoc={deleteDoc}
              onStudySelected={() => setView("ask")}
            />
          </div>
        )}

        {view === "ask" && (
          <div className="page narrow">
            <ChatPanel
              messages={messages}
              selectedDocNames={selectedDocs.map((d) => d.filename)}
              busy={working}
              disabled={selectedDocIds.length === 0}
              onSend={ask}
            />
          </div>
        )}

        {view === "summary" && (
          <div className="page">
            <section className="section-heading">
              <div>
                <span className="eyebrow">
                  {selectedDocs.length > 1
                    ? `ACROSS ${selectedDocs.length} MATERIALS`
                    : selectedDocs[0]?.filename || "YOUR MATERIALS"}
                </span>
                <h2>Get the big picture in minutes</h2>
              </div>
              <button
                className="primary-button"
                disabled={working || selectedDocIds.length === 0}
                onClick={() => void makeSummary()}
              >
                {working ? "Creating…" : selectedDocIds.length > 1 ? `Generate multi-doc summary (${selectedDocIds.length})` : "Generate summary"}
              </button>
            </section>
            {summary ? <SummaryView summary={summary} /> : <div className="empty-state">Generate a focused overview, key ideas, and exam cues across your selected materials.</div>}
          </div>
        )}

        {view === "mcqs" && (
          <div className="page narrow">
            <section className="section-heading">
              <div><span className="eyebrow">PRACTICE MODE</span><h2>Test what stuck</h2></div>
              {singleActiveDoc && (
                <div className="generator-controls">
                  <select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
                    <option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option>
                  </select>
                  <button className="primary-button" disabled={working} onClick={() => void makeMcqs()}>
                    {working ? "Generating…" : "Generate 8 MCQs"}
                  </button>
                </div>
              )}
            </section>

            {!singleActiveDoc ? (
              <SingleDocRequiredNotice
                toolName="MCQ Quiz"
                selectedDocs={selectedDocs}
                allDocs={documents}
                onSelectOne={(id) => setSelectedDocIds([id])}
                onOpenMaterials={() => setView("materials")}
              />
            ) : (
              <QuizPanel
                questions={mcqs}
                answers={answers}
                result={quizResult}
                busy={working}
                onChoose={(questionId, answer) => setAnswers((items) => ({ ...items, [questionId]: answer }))}
                onSubmit={submitQuiz}
              />
            )}
          </div>
        )}

        {view === "flashcards" && (
          <div className="page narrow">
            <section className="section-heading">
              <div>
                <span className="eyebrow">SPACED REPETITION (SM-2)</span>
                <h2>Active Recall &amp; Memory Practice</h2>
              </div>
            </section>

            {!singleActiveDoc ? (
              <SingleDocRequiredNotice
                toolName="Flashcards"
                selectedDocs={selectedDocs}
                allDocs={documents}
                onSelectOne={(id) => {
                  setSelectedDocIds([id]);
                  void loadFlashcards(id);
                }}
                onOpenMaterials={() => setView("materials")}
              />
            ) : (
              <FlashcardPanel
                cards={flashcards}
                dueCount={flashcardStats.due_count}
                newCount={flashcardStats.new_count}
                learningCount={flashcardStats.learning_count}
                busy={working}
                disabled={!singleActiveDoc}
                difficulty={difficulty}
                onDifficultyChange={setDifficulty}
                onGenerate={makeFlashcards}
                onReview={reviewCard}
                onRefresh={() => singleActiveDoc && loadFlashcards(singleActiveDoc.id)}
              />
            )}
          </div>
        )}

        {view === "revision" && (
          <div className="page narrow">
            <section className="section-heading">
              <div><span className="eyebrow">ACTIVE RECALL</span><h2>Questions worth thinking about</h2></div>
              {singleActiveDoc && (
                <div className="generator-controls">
                  <select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
                    <option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option><option value="exam">Exam focused</option>
                  </select>
                  <button className="primary-button" disabled={working} onClick={() => void makeRevision()}>
                    {working ? "Generating…" : "Create questions"}
                  </button>
                </div>
              )}
            </section>

            {!singleActiveDoc ? (
              <SingleDocRequiredNotice
                toolName="Revision Questions"
                selectedDocs={selectedDocs}
                allDocs={documents}
                onSelectOne={(id) => setSelectedDocIds([id])}
                onOpenMaterials={() => setView("materials")}
              />
            ) : (
              <div className="revision-list">
                {!revision.length && <div className="empty-state">Generate questions that make you retrieve and connect ideas.</div>}
                {revision.map((question, index) => (
                  <article key={question.id} className="revision-card">
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    <div><small>{question.type} · {question.difficulty}</small><h3>{question.question}</h3></div>
                  </article>
                ))}
              </div>
            )}
          </div>
        )}

        {view === "history" && (
          <div className="page narrow">
            <section className="section-heading"><div><span className="eyebrow">YOUR ACTIVITY</span><h2>Keep the momentum going</h2></div></section>
            <div className="history-list">
              {!history.length && <div className="empty-state">Your summaries, quizzes, and questions will be tracked here.</div>}
              {history.map((item) => (
                <article className="history-item" key={item.id}>
                  <ClipboardList size={18} />
                  <div>
                    <strong>{item.activity}</strong>
                    <p>{item.document_name} · {item.detail}</p>
                  </div>
                  <time>{new Date(item.created_at).toLocaleDateString()}</time>
                </article>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function SingleDocRequiredNotice({
  toolName,
  selectedDocs,
  allDocs,
  onSelectOne,
  onOpenMaterials
}: {
  toolName: string;
  selectedDocs: DocumentItem[];
  allDocs: DocumentItem[];
  onSelectOne: (id: string) => void;
  onOpenMaterials: () => void;
}) {
  if (selectedDocs.length === 0) {
    return (
      <div className="single-doc-notice-card">
        <AlertCircle size={32} className="notice-icon-alert" />
        <h3>No Study Material Selected</h3>
        <p>
          <strong>{toolName}</strong> operates on a specific document. Please select a material from your library to start studying.
        </p>
        <div className="doc-quick-list">
          {allDocs.map((doc) => (
            <button
              key={doc.id}
              type="button"
              className="quick-pick-btn"
              onClick={() => onSelectOne(doc.id)}
            >
              <FileText size={15} />
              <span>{doc.filename}</span>
            </button>
          ))}
        </div>
        <button type="button" className="action-link-btn" onClick={onOpenMaterials}>
          Open Materials Library
        </button>
      </div>
    );
  }

  return (
    <div className="single-doc-notice-card">
      <Layers size={32} className="notice-icon-layers" />
      <h3>Please select one material for {toolName}</h3>
      <p>
        <strong>{toolName}</strong> creates targeted study items per document. You currently have <strong>{selectedDocs.length} materials selected</strong>. Click one below to focus on it:
      </p>
      <div className="doc-quick-list">
        {selectedDocs.map((doc) => (
          <button
            key={doc.id}
            type="button"
            className="quick-pick-btn active"
            onClick={() => onSelectOne(doc.id)}
          >
            <FileText size={15} />
            <span>{doc.filename}</span>
          </button>
        ))}
      </div>
      <button type="button" className="action-link-btn" onClick={onOpenMaterials}>
        Manage all materials in Library
      </button>
    </div>
  );
}

function DocumentCard({ document }: { document: DocumentItem }) {
  return (
    <section className="document-card">
      <div className="document-icon"><FileText size={25} /></div>
      <div className="document-title"><span className="status-dot" /> <strong>Active Material</strong><h3>{document.filename}</h3></div>
      <dl><div><dt>Pages</dt><dd>{document.pages}</dd></div><div><dt>Chunks</dt><dd>{document.chunks}</dd></div><div><dt>Source</dt><dd>PDF</dd></div></dl>
    </section>
  );
}

function SummaryView({ summary }: { summary: Summary }) {
  return (
    <section className="summary-grid">
      <article className="overview-card"><span className="eyebrow">OVERVIEW</span><p>{summary.overview}</p></article>
      <article><h3>Key points</h3><ul>{summary.key_points.map((point, index) => <li key={index}>{point}</li>)}</ul></article>
      <article><h3>Important concepts</h3><div className="concepts">{summary.important_concepts.map((concept, index) => <span key={index}>{concept}</span>)}</div></article>
      <article className="exam-card"><h3>Exam focus</h3><ul>{summary.exam_focus.map((point, index) => <li key={index}>{point}</li>)}</ul></article>
    </section>
  );
}
