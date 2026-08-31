"""
Answer evaluation: scores each answer for relevance/depth so the interview can
adapt difficulty and the final report can give real insight, not just a
transcript dump.

Gemini mode: LLM scores 0-1 with a one-line rationale.
Offline mode: heuristic combining answer length and lexical overlap with the
source excerpt/topic.
"""
import re
from app.config import settings

STOPWORDS = {"the", "a", "an", "is", "are", "and", "or", "to", "of", "in", "for", "on", "with", "it", "this", "that"}


def _offline_score(answer: str, source_excerpt: str, topic: str) -> tuple[float, str]:
    if not answer or not answer.strip():
        return 0.0, "No answer provided."

    words = len(answer.split())
    length_score = min(words / 80, 1.0)

    def tokenize(t):
        return {w for w in re.findall(r"[a-z]+", t.lower()) if w not in STOPWORDS and len(w) > 2}

    answer_tokens = tokenize(answer)
    ref_tokens = tokenize(source_excerpt + " " + topic)
    overlap = len(answer_tokens & ref_tokens) / max(len(ref_tokens), 1)
    overlap_score = min(overlap * 2, 1.0)

    score = round(0.5 * length_score + 0.5 * overlap_score, 2)
    if score >= 0.7:
        feedback = "Solid, on-topic answer with good relevant detail."
    elif score >= 0.4:
        feedback = "Reasonable attempt, but could go deeper or be more specific to the topic."
    else:
        feedback = "Answer was brief or off-topic relative to the question focus."
    return score, feedback


def _gemini_score(answer: str, question: str, source_excerpt: str) -> tuple[float, str] | None:
    if not settings.GEMINI_API_KEY:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-3.6-flash")
        prompt = (
            "Score this candidate interview answer from 0.0 to 1.0 for relevance, "
            "correctness and depth, grounded in the reference material. "
            "Reply strictly as SCORE|feedback with SCORE a number and feedback one short sentence.\n"
            f"Question: {question}\nReference: {source_excerpt}\nAnswer: {answer}"
        )
        resp = model.generate_content(prompt).text.strip()
        score_str, _, feedback = resp.partition("|")
        return round(float(re.findall(r"[\d.]+", score_str)[0]), 2), feedback.strip() or "Evaluated."
    except Exception:
        return None


def evaluate_answer(answer: str, question: str, source_excerpt: str, topic: str) -> dict:
    result = _gemini_score(answer, question, source_excerpt)
    if result is None:
        result = _offline_score(answer, source_excerpt, topic)
    score, feedback = result
    return {"score": score, "feedback": feedback}


def next_difficulty(current: str, last_score: float | None) -> str:
    """Adaptive difficulty: strong answers escalate difficulty, weak answers
    ease off."""
    order = ["easy", "medium", "hard"]
    if last_score is None:
        return current
    idx = order.index(current)
    if last_score >= 0.75 and idx < 2:
        return order[idx + 1]
    if last_score < 0.35 and idx > 0:
        return order[idx - 1]
    return current
