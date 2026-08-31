import { CheckCircle2, Circle, Trophy } from "lucide-react";
import type { Mcq, QuizScore } from "../types";

type Props = {
  questions: Mcq[];
  answers: Record<string, number>;
  result: QuizScore | null;
  busy: boolean;
  onChoose: (questionId: string, answer: number) => void;
  onSubmit: () => Promise<void>;
};

export function QuizPanel({ questions, answers, result, busy, onChoose, onSubmit }: Props) {
  if (!questions.length) {
    return <div className="empty-state">Generate MCQs to begin a quiz.</div>;
  }

  return (
    <section className="quiz-panel">
      {result && (
        <div className="score-banner">
          <Trophy size={24} />
          <div><strong>{result.percentage}%</strong><span>{result.score} of {result.total} correct</span></div>
        </div>
      )}
      {questions.map((question, questionIndex) => {
        const answer = result?.results.find((item) => item.question_id === question.id);
        return (
          <article className="quiz-question" key={question.id}>
            <span>Question {questionIndex + 1}</span>
            <h3>{question.question}</h3>
            <div className="options">
              {question.options.map((option, optionIndex) => {
                const selected = answers[question.id] === optionIndex;
                const resultClass = !answer ? "" : optionIndex === answer.correct_answer
                  ? "correct"
                  : selected ? "incorrect" : "";
                return (
                  <button
                    className={"option " + (selected ? "selected " : "") + resultClass}
                    key={optionIndex}
                    disabled={Boolean(result)}
                    onClick={() => onChoose(question.id, optionIndex)}
                  >
                    {selected ? <CheckCircle2 size={18} /> : <Circle size={18} />}
                    {option}
                  </button>
                );
              })}
            </div>
            {answer && <p className="explanation"><strong>Why:</strong> {answer.explanation}</p>}
          </article>
        );
      })}
      {!result && (
        <button className="primary-button" disabled={busy} onClick={() => void onSubmit()}>
          {busy ? "Scoring…" : "Submit quiz"}
        </button>
      )}
    </section>
  );
}

