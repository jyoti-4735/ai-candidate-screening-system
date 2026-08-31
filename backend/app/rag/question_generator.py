"""
Context -> Question generation.

Query construction (dynamic, resume + role driven):
  For each interview turn we pick the next uncovered topic from a role-specific
  topic rotation, then bias the retrieval query toward the candidate's actual
  resume skills that relate to that topic.

Generation:
  - Gemini mode: LLM writes a single open-ended interview question grounded
    strictly in the retrieved chunk(s), calibrated to the requested difficulty.
  - Offline mode: a small set of question frames per difficulty level are
    filled in with the retrieved topic/content.
"""
import random
import re

from app.config import settings
from app.rag.retriever import retrieve

ROLE_TOPIC_ROTATION = {
    "ai_ml_engineer": [
        "Supervised Learning Fundamentals", "Bias-Variance Tradeoff",
        "Neural Networks and Backpropagation", "Convolutional Neural Networks",
        "Transfer Learning and Fine-Tuning", "Large Language Models and Prompt Engineering",
        "Retrieval-Augmented Generation (RAG)", "Chunking Strategy and Context Preservation",
        "Embeddings and Vector Similarity", "Model Evaluation Metrics",
        "Data Preprocessing and Feature Engineering", "Deployment and MLOps Basics",
    ],
    "backend_engineer": [
        "REST API Design Principles", "FastAPI and Async Request Handling",
        "Relational Database Design", "NoSQL Databases",
        "Authentication and Authorization", "Caching and Message Queues",
        "Containerization and CI/CD", "Vector Databases for AI-Integrated Backends",
        "Session and State Management", "Error Handling and Validation",
        "System Design and Separation of Concerns",
    ],
}

_OFFLINE_FRAMES = {
    "easy": [
        "In your own words, what is {topic.lower} and why does it matter in practice? "
        "Feel free to ground your answer in a project you have worked on.",
        "Can you explain the core idea behind {topic.lower} to someone new to the field?",
    ],
    "medium": [
        "Walk me through how you would apply {topic.lower} in a system you are building. "
        "What tradeoffs would you consider?",
        "Based on the following concept: \"{excerpt}\" how would you decide the right "
        "approach for {topic.lower} in a real project, and what could go wrong?",
    ],
    "hard": [
        "Given this context: \"{excerpt}\" critique a naive implementation of "
        "{topic.lower} and describe how you would make it production-grade at scale.",
        "Suppose {topic.lower} is failing silently in production. How would you diagnose "
        "it, and what design changes would you make to prevent it recurring?",
    ],
}


def build_query(topic: str, resume_skills: list[str]) -> str:
    related = [s for s in resume_skills if s.split()[0].lower() in topic.lower() or topic.split()[0].lower() in s.lower()]
    if not related:
        related = resume_skills[:3]
    return f"{topic} {' '.join(related)}".strip()


def _offline_generate(topic: str, excerpt: str, difficulty: str) -> str:
    frame = random.choice(_OFFLINE_FRAMES[difficulty])
    short_excerpt = re.sub(r"\s+", " ", excerpt)[:220].rsplit(" ", 1)[0] + "..."
    return frame.replace("{topic.lower}", topic).replace("{excerpt}", short_excerpt)


def _gemini_generate(topic: str, context: str, difficulty: str, candidate_skills: list[str], role_label: str) -> str | None:
    if not settings.GEMINI_API_KEY:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-flash-latest")
        prompt = (
            f"You are interviewing a fresher candidate for a {role_label} role. "
            f"Their resume shows familiarity with: {', '.join(candidate_skills) or 'general CS fundamentals'}.\n"
            f"Write ONE {difficulty}-difficulty interview question about the topic '{topic}', "
            f"strictly grounded in this reference material (do not introduce facts not implied by it):\n"
            f"---\n{context}\n---\n"
            "Return ONLY the question text, no preamble, no numbering, no quotes."
        )
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except Exception:
        return None


def generate_question(role_key: str, role_label: str, topic: str, resume_skills: list[str],
                       difficulty: str = "medium") -> dict:
    query = build_query(topic, resume_skills)
    chunks = retrieve(role_key, query, top_k=2)
    if not chunks:
        chunks = retrieve(role_key, topic, top_k=2)

    context = "\n\n".join(c["text"] for c in chunks) if chunks else topic
    excerpt = chunks[0]["text"] if chunks else topic

    question_text = _gemini_generate(topic, context, difficulty, resume_skills, role_label)
    mode = "gemini"
    if not question_text:
        question_text = _offline_generate(topic, excerpt, difficulty)
        mode = "offline"

    return {
        "topic": topic,
        "prompt_text": question_text,
        "difficulty": difficulty,
        "source_chunk_ids": [c["chunk_id"] for c in chunks],
        "source_excerpt": excerpt[:400],
        "generation_mode": mode,
    }
