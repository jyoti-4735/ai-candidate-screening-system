"""
Hybrid retriever.

Base layer (always available, zero external dependency): TF-IDF + cosine
similarity over the chunked knowledge base. Needs no API key and no model
download, so the system is always demoable offline.

Upgrade layer (used automatically when GEMINI_API_KEY is set): each candidate
chunk from the TF-IDF shortlist is re-scored using Gemini text embeddings
(dense/semantic similarity) and the two scores are blended. Degrades
gracefully when no API key is configured.
"""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings
from app.knowledge_base.chunker import load_and_chunk_role_docs

_role_indexes: dict[str, dict] = {}


def _build_index(role_key: str):
    chunks = load_and_chunk_role_docs(role_key)
    if not chunks:
        return None
    texts = [c["text"] for c in chunks]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(texts)
    index = {"chunks": chunks, "vectorizer": vectorizer, "matrix": matrix}
    _role_indexes[role_key] = index
    return index


def _get_index(role_key: str):
    if role_key not in _role_indexes:
        return _build_index(role_key)
    return _role_indexes[role_key]


def _gemini_semantic_rerank(query: str, candidates: list[dict]) -> dict:
    """Returns {chunk_id: semantic_score}. Silently no-ops without an API key
    or on any API error, so retrieval quality only ever improves opportunistically."""
    if not settings.GEMINI_API_KEY:
        return {}
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        query_emb = genai.embed_content(model="models/text-embedding-004", content=query)["embedding"]
        scores = {}
        for c in candidates:
            emb = genai.embed_content(model="models/text-embedding-004", content=c["text"])["embedding"]
            sim = float(np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb) + 1e-9))
            scores[c["chunk_id"]] = sim
        return scores
    except Exception:
        return {}


def retrieve(role_key: str, query: str, top_k: int | None = None) -> list[dict]:
    top_k = top_k or settings.TOP_K
    index = _get_index(role_key)
    if not index:
        return []

    query_vec = index["vectorizer"].transform([query])
    lexical_scores = cosine_similarity(query_vec, index["matrix"]).flatten()

    shortlist_n = min(len(lexical_scores), max(top_k * 2, top_k))
    shortlist_idx = np.argsort(-lexical_scores)[:shortlist_n]
    candidates = [dict(index["chunks"][i], lexical_score=float(lexical_scores[i])) for i in shortlist_idx]

    semantic_scores = _gemini_semantic_rerank(query, candidates)
    for c in candidates:
        sem = semantic_scores.get(c["chunk_id"])
        c["semantic_score"] = sem
        c["final_score"] = (0.35 * c["lexical_score"] + 0.65 * sem) if sem is not None else c["lexical_score"]

    candidates.sort(key=lambda c: -c["final_score"])
    return candidates[:top_k]
