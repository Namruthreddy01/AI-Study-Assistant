import { FormEvent, useState } from "react";
import { ArrowUp, Bot, FileText, Layers } from "lucide-react";
import type { ChatMessage } from "../types";

type Props = {
  messages: ChatMessage[];
  selectedDocNames: string[];
  busy: boolean;
  disabled: boolean;
  onSend: (question: string) => Promise<void>;
};

export function ChatPanel({ messages, selectedDocNames, busy, disabled, onSend }: Props) {
  const [question, setQuestion] = useState("");

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const clean = question.trim();
    if (!clean || busy || disabled) return;
    setQuestion("");
    await onSend(clean);
  };

  const hasMultiple = selectedDocNames.length > 1;
  const docSummary = hasMultiple
    ? `Searching across ${selectedDocNames.length} materials: ${selectedDocNames.join(", ")}`
    : selectedDocNames.length === 1
    ? `Searching: ${selectedDocNames[0]}`
    : "No materials selected";

  return (
    <section className="chat-shell">
      <div className="chat-intro">
        <div className="chat-intro-top">
          <span className="eyebrow"><Bot size={15} /> Grounded Cross-Document AI</span>
          <span className="active-scope-badge" title={docSummary}>
            <Layers size={13} /> {hasMultiple ? `${selectedDocNames.length} Materials Active` : selectedDocNames[0] || "No Material"}
          </span>
        </div>
        <h2>Ask your material anything</h2>
        <p className="search-scope-note">{docSummary}</p>
      </div>
      <div className="messages">
        {!messages.length && (
          <div className="empty-chat">
            <Bot size={28} />
            <p>Try &ldquo;Compare the key concepts discussed in these notes&rdquo; or &ldquo;Summarize the main definitions&rdquo;</p>
          </div>
        )}
        {messages.map((message, index) => (
          <article key={index} className={"message " + message.role}>
            <p>{message.content}</p>
            {message.sources && message.sources.length > 0 && (
              <div className="sources-container">
                <span className="sources-label">Sources:</span>
                {message.sources.map((source) => (
                  <div className="source" key={source.chunk_id}>
                    <FileText size={13} />
                    <span><strong>{source.filename}</strong> · Page {source.page}</span>
                  </div>
                ))}
              </div>
            )}
          </article>
        ))}
        {busy && <article className="message assistant typing">Searching across selected materials and formulating answer…</article>}
      </div>
      <form className="chat-form" onSubmit={(event) => void submit(event)}>
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          disabled={disabled}
          placeholder={disabled ? "Select at least one study material first" : "Ask a question across your selected notes…"}
        />
        <button aria-label="Send question" disabled={disabled || busy || !question.trim()}>
          <ArrowUp size={18} />
        </button>
      </form>
    </section>
  );
}

