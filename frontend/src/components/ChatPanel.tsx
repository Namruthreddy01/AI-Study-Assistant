import { FormEvent, useState } from "react";
import { ArrowUp, Bot, FileText } from "lucide-react";
import type { ChatMessage } from "../types";

type Props = {
  messages: ChatMessage[];
  busy: boolean;
  disabled: boolean;
  onSend: (question: string) => Promise<void>;
};

export function ChatPanel({ messages, busy, disabled, onSend }: Props) {
  const [question, setQuestion] = useState("");

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const clean = question.trim();
    if (!clean || busy || disabled) return;
    setQuestion("");
    await onSend(clean);
  };

  return (
    <section className="chat-shell">
      <div className="chat-intro">
        <span className="eyebrow"><Bot size={15} /> Grounded AI</span>
        <h2>Ask your material anything</h2>
        <p>Answers are based on the selected PDF, with page references when relevant.</p>
      </div>
      <div className="messages">
        {!messages.length && (
          <div className="empty-chat">
            <Bot size={28} />
            <p>Try “Explain the main concept in simple terms”</p>
          </div>
        )}
        {messages.map((message, index) => (
          <article key={index} className={"message " + message.role}>
            <p>{message.content}</p>
            {message.sources?.map((source) => (
              <div className="source" key={source.chunk_id}>
                <FileText size={14} />
                <span>{source.filename} · page {source.page}</span>
              </div>
            ))}
          </article>
        ))}
        {busy && <article className="message assistant typing">Finding the best passages…</article>}
      </div>
      <form className="chat-form" onSubmit={(event) => void submit(event)}>
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          disabled={disabled}
          placeholder={disabled ? "Upload and select a document first" : "Ask about this material…"}
        />
        <button aria-label="Send question" disabled={disabled || busy || !question.trim()}>
          <ArrowUp size={18} />
        </button>
      </form>
    </section>
  );
}

