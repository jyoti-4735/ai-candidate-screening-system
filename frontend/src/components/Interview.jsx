import { useState, useEffect, useCallback, useRef } from "react";
import { api } from "../api";
import ProfilePanel from "./ProfilePanel";

export default function Interview({ session, onFinished }) {
  const isFetching = useRef(false);
  const [question, setQuestion] = useState(null);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [lastFeedback, setLastFeedback] = useState(null);
  const [askedCount, setAskedCount] = useState(0);
  const [showSource, setShowSource] = useState(false);

  const loadNext = useCallback(async () => {
    if (isFetching.current) return;
    isFetching.current = true;
    setLoading(true);
    setLastFeedback(null);
    setShowSource(false);
    const q = await api.nextQuestion(session.id);
    setQuestion(q);
    if (q) setAskedCount((c) => c + 1);
    setLoading(false);
    isFetching.current = false;
    if (!q) {
      const summary = await api.finishSession(session.id);
      onFinished(summary);
    }
  }, [session.id, onFinished]);

  useEffect(() => { loadNext(); }, [loadNext]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!answer.trim()) return;
    setSubmitting(true);
    const result = await api.submitAnswer(session.id, question.id, answer);
    setLastFeedback(result);
    setAnswer("");
    setSubmitting(false);
    setTimeout(loadNext, 900);
  };

  if (loading) return <div className="card">Preparing your next question...</div>;
  if (!question) return <div className="card">Wrapping up your interview...</div>;

  return (
    <div>
      <ProfilePanel session={session} />
      <div className="card">
        <div className="q-meta">
          <span className="chip chip-topic">{question.topic}</span>
          <span className={`chip chip-diff diff-${question.difficulty}`}>{question.difficulty}</span>
          <span className="muted">Question {askedCount}</span>
        </div>
        <h2>{question.prompt_text}</h2>

        <button type="button" className="link-btn" onClick={() => setShowSource((s) => !s)}>
          {showSource ? "Hide" : "Why this question?"}
        </button>
        {showSource && (
          <div className="source-excerpt">
            Grounded in this retrieved knowledge-base excerpt:
            <blockquote>{question.source_excerpt}</blockquote>
          </div>
        )}

        {lastFeedback ? (
          <div className={`feedback ${lastFeedback.eval_score >= 0.6 ? "good" : "meh"}`}>
            <strong>Score: {lastFeedback.eval_score}</strong> - {lastFeedback.eval_feedback}
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <textarea
              rows={6}
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Type your answer here..."
              disabled={submitting}
            />
            <button type="submit" disabled={submitting || !answer.trim()}>
              {submitting ? "Evaluating..." : "Submit Answer"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
