# AI-Powered Candidate Screening System

A role-based technical screening system that simulates a structured interview.
Questions are not pulled from a static bank - they are generated live from a
Retrieval-Augmented Generation (RAG) pipeline over a role-specific knowledge
base, dynamically steered by the candidate own resume.

Built for the PGAGI AI/ML & Backend Engineering Intern assignment.

---

## 1. Quick Start

### Backend

cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --reload-dir app


### Frontend

cd frontend
npm install
copy .env.example .env
npm run dev


Open http://localhost:5173. The backend must be running on port 8000.

No API key is required to run and demo the full system. See "Dual-mode
operation" below. To enable Gemini mode, add a free API key from
https://aistudio.google.com/apikey to `GEMINI_API_KEY` in `backend/.env`.

---

## 2. System Flow

1. Candidate Entry - upload a resume (PDF or .txt) and pick a role
   (AI/ML Engineer or Backend Engineer).
2. Resume Processing - resume_parser.py extracts skills, technologies,
   domain exposure, and an experience-level heuristic.
3. Context Construction - for each interview turn, build_query() in
   question_generator.py combines the current topic with the candidate
   own extracted skills, so retrieval is resume-influenced, not generic.
4. Knowledge Retrieval (RAG) - retriever.py retrieves the most relevant
   chunks from the role knowledge base.
5. Question Generation - the retrieved chunk(s) are turned into a single
   grounded interview question, calibrated to a difficulty level.
6. Interactive Interview - the frontend asks one question at a time, the
   candidate answers, and a session ties the whole exchange together.
7. Response Handling - every question, its retrieval source, and the
   candidate answer are persisted in SQLite.
8. Final Output - a structured summary with per-topic scores, strengths,
   growth areas, and the detected resume skill set.

---

## 3. Architecture

frontend/ (React + Vite)
ResumeUpload -> Interview -> Summary
|
v REST (multipart upload, JSON)
backend/ (FastAPI)
routers/ HTTP layer - validation, request/response shapes
services/ business logic - interview_service, analysis_service
rag/ retrieval + question generation
resume_parser.py resume -> structured skills/technologies/domains
models.py SQLAlchemy ORM (SQLite by default)


Routers never touch the DB or RAG pipeline directly - they call into
services/, which call into rag/ and models.py. Swapping SQLite for
Postgres, or the vector layer for a different store, does not touch the
router or frontend code.

---

## 4. Key Design Decisions

### 4.1 Dual-mode operation (offline / Gemini)
Every AI-dependent component has two code paths:

- Offline mode (default, no API key): TF-IDF + cosine similarity for
  retrieval, keyword-taxonomy extraction for resumes, template-filled
  questions built from the actual retrieved chunk, and a lexical-overlap
  + length heuristic for answer scoring.
- Gemini mode (GEMINI_API_KEY set): dense semantic re-ranking on top of
  the TF-IDF shortlist, LLM-based structured resume extraction, LLM
  generated questions, and LLM-based answer scoring. Currently uses
  gemini-3.6-flash.

Every function tries Gemini first and silently falls back to offline on
any error or missing key, so the system is always demoable with zero
setup cost, and genuinely upgrades in quality when a key is provided.

This was verified during real development, not just designed in theory:
while testing, the API key hit three different issues in the same
session - two Gemini model names becoming deprecated/unavailable within
hours of each other (gemini-1.5-flash, then gemini-2.5-flash), and a
free-tier rate limit (429) on a newer preview model. In every case, the
interview kept running end-to-end by falling back to offline mode
automatically, with no crash and no broken UI state - exactly the
resilience this design is meant to provide.

### 4.2 Retrieval: TF-IDF baseline, semantic rerank as the upgrade
TF-IDF is dependency-light, deterministic, and a well-established
retrieval baseline on its own. When a Gemini key is present, each
shortlisted chunk is re-scored with real embeddings and blended with the
lexical score - a hybrid approach used in production retrieval systems.

### 4.3 Chunking: section-aware, not naive fixed-size
The knowledge base is chunked by markdown ## section headers first
(natural topic boundaries), and only splits further with a sliding
window + overlap if a section exceeds the target size, so a chunk almost
never straddles two unrelated concepts.

### 4.4 Adaptive difficulty
After each answer is scored, next_difficulty() escalates difficulty on
strong answers (>= 0.75) and eases off on weak ones (< 0.35). This was
verified live during testing: a detailed, on-topic answer pushed
difficulty from Medium to Hard; a one-line weak answer dropped it back
down on the following question.

### 4.5 Traceability
Every stored Question row keeps source_chunk_ids and source_excerpt. The
frontend exposes this via a "Why this question?" toggle, so the summary
report is fully reconstructable: Context -> Question -> Answer -> Score.

### 4.6 Resume-driven topic rotation
Topics are drawn from a per-role rotation, but the query sent to the
retriever for each topic is biased toward the candidate own resume
skills. Two candidates targeting the same role with different resumes
get differently-worded, differently-grounded questions on the same topic.

---

## 5. Tech Stack

- Backend: Python, FastAPI, SQLAlchemy (SQLite), scikit-learn (TF-IDF
  retrieval), pypdf (resume parsing), optional google-generativeai
  (Gemini, model: gemini-3.6-flash).
- Frontend: React (Vite), plain CSS.
- Data layer: SQLite by default; DATABASE_URL in .env can point to
  Postgres with no code changes.

## 6. Extending

- Add a new role: drop a role_name.md file (with ## Section headers)
  into backend/app/knowledge_base/seed_data/, add the role to
  ROLE_TOPIC_ROTATION and ROLE_LABELS.
- Swap the vector layer: retriever.py is the only file that knows about
  TF-IDF/embeddings - everything else calls retrieve().
- Swap the Gemini model: the model name is set in three places
  (resume_parser.py, rag/question_generator.py,
  services/analysis_service.py) - Google occasionally deprecates model
  names, so check https://ai.google.dev/gemini-api/docs/models if a
  NotFound error appears.
