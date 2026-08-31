import { useEffect, useMemo, useState } from "react";
import {
  BookOpenCheck,
  BrainCircuit,
  ChevronRight,
  ClipboardList,
  FileQuestion,
  FileText,
  History,
  LayoutDashboard,
  Lightbulb,
  ListChecks,
  Sparkles,
  UploadCloud
} from "lucide-react";
import { api } from "./lib/api";
import { ChatPanel } from "./components/ChatPanel";
import { DocumentUploader } from "./components/DocumentUploader";
import { QuizPanel } from "./components/QuizPanel";
import type {
  ChatMessage,
  DocumentItem,
  HistoryItem,
  Mcq,
  QuizScore,
  RevisionQuestion,
  Summary
} from "./types";

type View = "dashboard" | "ask" | "summary" | "mcqs" | "revision" | "history";

const nav = [
  { id: "dashboard" as View, label: "Overview", icon: LayoutDashboard },
  { id: "ask" as View, label: "Ask AI", icon: BrainCircuit },
  { id: "summary" as View, label: "Summary", icon: FileText },
  { id: "mcqs" as View, label: "MCQ Quiz", icon: ListChecks },
  { id: "revision" as View, label: "Revision", icon: FileQuestion },
  { id: "history" as View, label: "Study history", icon: History }
];

export default function App() {
  const [view, setView] = useState<View>("dashboard");
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [activeId, setActiveId] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [mcqs, setMcqs] = useState<Mcq[]>([]);
  const [revision, setRevision] = useState<RevisionQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [quizResult, setQuizResult] = useState<QuizScore | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [difficulty, setDifficulty] = useState("medium");
  const [working, setWorking] = useState(false);
  const [notice, setNotice] = useState("");

  const selected = useMemo(
    () => documents.find((document) => document.id === activeId),
    [documents, activeId]
  );

  useEffect(() => {
    void api.documents()
      .then((items) => {
        setDocuments(items);
        if (items[0]) setActiveId(items[0].id);
      })
      .catch(() => setNotice("Start the FastAPI server to connect your study workspace."));
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

  const withDocument = () => {
    if (!activeId) {
      setNotice("Upload and select a PDF before using this study tool.");
      return false;
    }
    return true;
  };

  const upload = async (file: File) => {
    await execute(async () => {
      const document = await api.upload(file);
      setDocuments((items) => [document, ...items]);
      setActiveId(document.id);
      setMessages([]);
      setNotice(document.filename + " is processed and ready to study.");
    });
  };

  const ask = async (question: string) => {
    if (!withDocument()) return;
    setMessages((items) => [...items, { role: "student", content: question }]);
    await execute(async () => {
      const response = await api.chat(activeId, question);
      setMessages((items) => [
        ...items,
        { role: "assistant", content: response.answer, sources: response.sources }
      ]);
    });
  };

  const makeSummary = async () => {
    if (!withDocument()) return;
    await execute(async () => {
      setSummary(await api.summary(activeId));
      setView("summary");
    });
  };

  const makeMcqs = async () => {
    if (!withDocument()) return;
    await execute(async () => {
      const response = await api.mcqs(activeId, 8, difficulty);
      setMcqs(response.questions);
      setAnswers({});
      setQuizResult(null);
      setView("mcqs");
    });
  };

  const makeRevision = async () => {
    if (!withDocument()) return;
    await execute(async () => {
      const response = await api.revision(activeId, 8, difficulty);
      setRevision(response.questions);
      setView("revision");
    });
  };

  const submitQuiz = async () => {
    if (!withDocument() || !mcqs.length) return;
    await execute(async () => setQuizResult(await api.scoreQuiz(activeId, mcqs, answers)));
  };

  const loadHistory = async () => {
    setView("history");
    await execute(async () => setHistory(await api.history()));
  };

  const title: Record<View, string> = {
    dashboard: "Your study space",
    ask: "Ask AI",
    summary: "Smart summary",
    mcqs: "Knowledge check",
    revision: "Revision questions",
    history: "Study history"
  };

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
                onClick={() => item.id === "history" ? void loadHistory() : setView(item.id)}
              >
                <Icon size={18} /> {item.label}
              </button>
            );
          })}
        </nav>
        <div className="sidebar-tip">
          <Lightbulb size={19} />
          <strong>Study smarter</strong>
          <p>Ask questions in your own words for clearer explanations.</p>
        </div>
      </aside>

      <main>
        <header className="topbar">
          <div>
            <p className="eyebrow">STUDENT WORKSPACE</p>
            <h1>{title[view]}</h1>
          </div>
          <div className="document-select">
            <BookOpenCheck size={17} />
            <select value={activeId} onChange={(event) => setActiveId(event.target.value)}>
              <option value="">Select material</option>
              {documents.map((document) => (
                <option value={document.id} key={document.id}>{document.filename}</option>
              ))}
            </select>
          </div>
        </header>

        {notice && <div className="notice">{notice}</div>}

        {view === "dashboard" && (
          <div className="page">
            <section className="hero">
              <div>
                <span className="eyebrow">PERSONAL LEARNING COMPANION</span>
                <h2>Turn dense notes into your next <em>aha!</em> moment.</h2>
                <p>Upload your material once. Get grounded answers, sharp summaries, and targeted practice whenever you need them.</p>
                <button className="hero-link" onClick={() => setView("ask")}>Ask a question <ChevronRight size={17} /></button>
              </div>
              <div className="hero-orb"><BrainCircuit size={68} /></div>
            </section>
            <DocumentUploader busy={working} onUpload={upload} />
            <section className="stats">
              <div><span>Materials</span><strong>{documents.length}</strong><small>ready to study</small></div>
              <div><span>Pages indexed</span><strong>{documents.reduce((sum, item) => sum + item.pages, 0)}</strong><small>across your PDFs</small></div>
              <div><span>Study tools</span><strong>4</strong><small>available now</small></div>
            </section>
            {selected ? <DocumentCard document={selected} /> : <div className="empty-state">Your uploaded materials will appear here.</div>}
          </div>
        )}

        {view === "ask" && (
          <div className="page narrow"><ChatPanel messages={messages} busy={working} disabled={!activeId} onSend={ask} /></div>
        )}

        {view === "summary" && (
          <div className="page">
            <section className="section-heading">
              <div><span className="eyebrow">FROM {selected?.filename || "YOUR PDF"}</span><h2>Get the big picture in minutes</h2></div>
              <button className="primary-button" disabled={working || !activeId} onClick={() => void makeSummary()}>{working ? "Creating…" : "Generate summary"}</button>
            </section>
            {summary ? <SummaryView summary={summary} /> : <div className="empty-state">Generate a focused overview, key ideas, and exam cues.</div>}
          </div>
        )}

        {view === "mcqs" && (
          <div className="page narrow">
            <section className="section-heading">
              <div><span className="eyebrow">PRACTICE MODE</span><h2>Test what stuck</h2></div>
              <div className="generator-controls">
                <select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
                  <option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option>
                </select>
                <button className="primary-button" disabled={working || !activeId} onClick={() => void makeMcqs()}>{working ? "Generating…" : "Generate 8 MCQs"}</button>
              </div>
            </section>
            <QuizPanel
              questions={mcqs}
              answers={answers}
              result={quizResult}
              busy={working}
              onChoose={(questionId, answer) => setAnswers((items) => ({ ...items, [questionId]: answer }))}
              onSubmit={submitQuiz}
            />
          </div>
        )}

        {view === "revision" && (
          <div className="page narrow">
            <section className="section-heading">
              <div><span className="eyebrow">ACTIVE RECALL</span><h2>Questions worth thinking about</h2></div>
              <div className="generator-controls">
                <select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
                  <option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option><option value="exam">Exam focused</option>
                </select>
                <button className="primary-button" disabled={working || !activeId} onClick={() => void makeRevision()}>{working ? "Generating…" : "Create questions"}</button>
              </div>
            </section>
            <div className="revision-list">
              {!revision.length && <div className="empty-state">Generate questions that make you retrieve and connect ideas.</div>}
              {revision.map((question, index) => (
                <article key={question.id} className="revision-card">
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <div><small>{question.type} · {question.difficulty}</small><h3>{question.question}</h3></div>
                </article>
              ))}
            </div>
          </div>
        )}

        {view === "history" && (
          <div className="page narrow">
            <section className="section-heading"><div><span className="eyebrow">YOUR ACTIVITY</span><h2>Keep the momentum going</h2></div></section>
            <div className="history-list">
              {!history.length && <div className="empty-state">Your summaries, quizzes, and questions will be tracked here.</div>}
              {history.map((item) => <article className="history-item" key={item.id}><ClipboardList size={18} /><div><strong>{item.activity}</strong><p>{item.document_name} · {item.detail}</p></div><time>{new Date(item.created_at).toLocaleDateString()}</time></article>)}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function DocumentCard({ document }: { document: DocumentItem }) {
  return (
    <section className="document-card">
      <div className="document-icon"><FileText size={25} /></div>
      <div className="document-title"><span className="status-dot" /> <strong>Processed</strong><h3>{document.filename}</h3></div>
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
