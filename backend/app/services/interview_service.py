import uuid
import datetime
from sqlalchemy.orm import Session as DBSession

from app import models
from app.config import settings
from app.resume_parser import parse_resume
from app.rag.question_generator import generate_question, ROLE_TOPIC_ROTATION
from app.services.analysis_service import evaluate_answer, next_difficulty

ROLE_LABELS = {
    "ai_ml_engineer": "AI/ML Engineer",
    "backend_engineer": "Backend Engineer",
}


def start_session(db: DBSession, role_key: str, filename: str, raw_bytes: bytes) -> models.Session:
    if role_key not in ROLE_TOPIC_ROTATION:
        raise ValueError(f"Unknown role '{role_key}'. Valid roles: {list(ROLE_TOPIC_ROTATION)}")

    parsed = parse_resume(filename, raw_bytes)
    session = models.Session(
        id=str(uuid.uuid4()),
        role=role_key,
        resume_filename=filename,
        resume_raw_text=parsed["raw_text"][:20000],
        extracted_skills=parsed["skills"],
        extracted_technologies=parsed["technologies"],
        extracted_domains=parsed["domains"],
        experience_level=parsed["experience_level"],
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _covered_topics(session: models.Session) -> set:
    return {q.topic for q in session.questions}


def generate_next_question(db: DBSession, session: models.Session) -> models.Question | None:
    topics = ROLE_TOPIC_ROTATION[session.role]
    covered = _covered_topics(session)
    remaining = [t for t in topics if t not in covered]
    if not remaining or len(session.questions) >= settings.MAX_QUESTIONS:
        return None

    topic = remaining[0]
    last_q = session.questions[-1] if session.questions else None
    difficulty = next_difficulty(last_q.difficulty if last_q else "medium",
                                  last_q.eval_score if last_q else None)

    resume_skills = list(session.extracted_skills) + list(session.extracted_technologies)
    gen = generate_question(session.role, ROLE_LABELS[session.role], topic, resume_skills, difficulty)

    question = models.Question(
        session_id=session.id,
        order_index=len(session.questions) + 1,
        topic=gen["topic"],
        difficulty=gen["difficulty"],
        prompt_text=gen["prompt_text"],
        source_chunk_ids=gen["source_chunk_ids"],
        source_excerpt=gen["source_excerpt"],
        generation_mode=gen["generation_mode"],
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def submit_answer(db: DBSession, question: models.Question, answer_text: str) -> models.Question:
    result = evaluate_answer(answer_text, question.prompt_text, question.source_excerpt or "", question.topic or "")
    question.answer_text = answer_text
    question.answer_submitted_at = datetime.datetime.utcnow()
    question.eval_score = result["score"]
    question.eval_feedback = result["feedback"]
    db.commit()
    db.refresh(question)
    return question


def finalize_session(db: DBSession, session: models.Session) -> dict:
    answered = [q for q in session.questions if q.answer_text]
    avg_score = round(sum(q.eval_score or 0 for q in answered) / len(answered), 2) if answered else 0.0

    topic_breakdown = [
        {"topic": q.topic, "difficulty": q.difficulty, "score": q.eval_score, "feedback": q.eval_feedback}
        for q in session.questions
    ]
    strengths = [t["topic"] for t in topic_breakdown if (t["score"] or 0) >= 0.7]
    growth_areas = [t["topic"] for t in topic_breakdown if (t["score"] or 0) < 0.4]

    summary = {
        "role": ROLE_LABELS.get(session.role, session.role),
        "candidate_experience_level": session.experience_level,
        "questions_asked": len(session.questions),
        "questions_answered": len(answered),
        "average_score": avg_score,
        "topic_breakdown": topic_breakdown,
        "strengths": strengths,
        "growth_areas": growth_areas,
        "resume_skills_detected": session.extracted_skills,
        "resume_technologies_detected": session.extracted_technologies,
        "generation_mode": settings.LLM_MODE,
    }
    session.summary_json = summary
    session.status = "completed"
    session.completed_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(session)
    return summary
