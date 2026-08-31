"""
Resume parsing: extract raw text (PDF or plain text), then extract
skills / technologies / domain exposure.

Two extraction modes:
  - Gemini mode: ask the LLM for structured JSON extraction (catches skills
    phrased in free text, e.g. "built ETL pipelines").
  - Offline mode: keyword-match against a curated taxonomy. Deterministic,
    needs no API key, and transparent about what it can and can't catch.
"""
import io
import json
import re
from pypdf import PdfReader

from app.config import settings

SKILL_TAXONOMY = {
    "languages": ["python", "java", "javascript", "typescript", "c++", "c#", "go", "sql"],
    "ai_ml": [
        "machine learning", "deep learning", "nlp", "cnn", "resnet", "pytorch",
        "tensorflow", "scikit-learn", "rag", "retrieval-augmented generation",
        "llm", "large language model", "gemini", "openai", "hugging face",
        "langchain", "prompt engineering", "fine-tuning", "embeddings",
        "vector database", "agent", "adk",
    ],
    "backend": [
        "fastapi", "flask", "django", "node.js", "express", "rest api",
        "graphql", "microservices", "docker", "kubernetes", "ci/cd",
        "jwt", "oauth", "redis", "rabbitmq",
    ],
    "frontend": ["react", "next.js", "vue", "angular", "html", "css", "redux"],
    "databases": ["mysql", "postgresql", "postgres", "mongodb", "sqlite", "nosql"],
    "cloud_devops": ["gcp", "aws", "azure", "cloud logging", "git", "github"],
}

ALL_KEYWORDS = sorted({kw for group in SKILL_TAXONOMY.values() for kw in group}, key=len, reverse=True)


def extract_text_from_upload(filename: str, raw_bytes: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(raw_bytes))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    return raw_bytes.decode("utf-8", errors="ignore")


def _offline_extract(resume_text: str) -> dict:
    text_lower = resume_text.lower()
    found = []
    for kw in ALL_KEYWORDS:
        if re.search(r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])", text_lower):
            found.append(kw)

    technologies = [k for k in found if k in SKILL_TAXONOMY["languages"] + SKILL_TAXONOMY["frontend"] + SKILL_TAXONOMY["databases"]]
    skills = [k for k in found if k in SKILL_TAXONOMY["ai_ml"] + SKILL_TAXONOMY["backend"] + SKILL_TAXONOMY["cloud_devops"]]

    domains = []
    if any(k in found for k in SKILL_TAXONOMY["ai_ml"]):
        domains.append("AI/ML & NLP")
    if any(k in found for k in SKILL_TAXONOMY["backend"]):
        domains.append("Backend/API engineering")
    if any(k in found for k in SKILL_TAXONOMY["frontend"]):
        domains.append("Frontend development")
    if "cloud logging" in found or "gcp" in found or "aws" in found or "azure" in found:
        domains.append("Cloud deployment")

    years_match = re.search(r"(\d+)\+?\s+years?", text_lower)
    experience_level = "fresher"
    if "intern" in text_lower and not years_match:
        experience_level = "fresher"
    if years_match and int(years_match.group(1)) >= 2:
        experience_level = "junior"

    return {
        "skills": sorted(set(skills)),
        "technologies": sorted(set(technologies)),
        "domains": domains,
        "experience_level": experience_level,
    }


def _gemini_extract(resume_text: str) -> dict | None:
    if not settings.GEMINI_API_KEY:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-3.6-flash")
        prompt = (
            "Extract structured info from this resume as strict JSON with keys "
            "skills (list[str]), technologies (list[str]), domains (list[str]), "
            "experience_level (one of: fresher, junior, mid, senior). "
            "No prose, JSON only.\n\nRESUME:\n" + resume_text[:6000]
        )
        resp = model.generate_content(prompt)
        cleaned = re.sub(r"```json|```", "", resp.text).strip()
        data = json.loads(cleaned)
        return {
            "skills": data.get("skills", []),
            "technologies": data.get("technologies", []),
            "domains": data.get("domains", []),
            "experience_level": data.get("experience_level", "fresher"),
        }
    except Exception:
        return None


def parse_resume(filename: str, raw_bytes: bytes) -> dict:
    resume_text = extract_text_from_upload(filename, raw_bytes)
    result = _gemini_extract(resume_text) or _offline_extract(resume_text)
    result["raw_text"] = resume_text
    return result
