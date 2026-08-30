from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.database import get_db
from app import models, schemas
from app.services import interview_service

router = APIRouter(prefix="/api/interview", tags=["interview"])


def _get_session_or_404(db: DBSession, session_id: str) -> models.Session:
    session = db.get(models.Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/start", response_model=schemas.SessionOut)
async def start(role: str = Form(...), resume: UploadFile = File(...), db: DBSession = Depends(get_db)):
    raw_bytes = await resume.read()
    try:
        session = interview_service.start_session(db, role, resume.filename, raw_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return session


@router.get("/{session_id}/next-question", response_model=schemas.QuestionOut | None)
def next_question(session_id: str, db: DBSession = Depends(get_db)):
    session = _get_session_or_404(db, session_id)
    question = interview_service.generate_next_question(db, session)
    if question is None:
        return None
    return question


@router.post("/{session_id}/questions/{question_id}/answer", response_model=schemas.AnswerOut)
def answer(session_id: str, question_id: int, payload: schemas.AnswerIn, db: DBSession = Depends(get_db)):
    session = _get_session_or_404(db, session_id)
    question = db.get(models.Question, question_id)
    if not question or question.session_id != session.id:
        raise HTTPException(status_code=404, detail="Question not found")
    return interview_service.submit_answer(db, question, payload.answer_text)


@router.post("/{session_id}/finish", response_model=schemas.SummaryOut)
def finish(session_id: str, db: DBSession = Depends(get_db)):
    session = _get_session_or_404(db, session_id)
    return interview_service.finalize_session(db, session)


@router.get("/{session_id}", response_model=schemas.SessionOut)
def get_session(session_id: str, db: DBSession = Depends(get_db)):
    return _get_session_or_404(db, session_id)
