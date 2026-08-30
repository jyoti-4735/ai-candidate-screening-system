import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)                 # uuid
    role = Column(String, nullable=False)
    resume_filename = Column(String, nullable=True)
    resume_raw_text = Column(Text, nullable=True)
    extracted_skills = Column(JSON, default=list)
    extracted_technologies = Column(JSON, default=list)
    extracted_domains = Column(JSON, default=list)
    experience_level = Column(String, default="fresher")
    status = Column(String, default="in_progress")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    summary_json = Column(JSON, nullable=True)

    questions = relationship("Question", back_populates="session", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    order_index = Column(Integer, nullable=False)
    topic = Column(String, nullable=True)
    difficulty = Column(String, default="medium")
    prompt_text = Column(Text, nullable=False)
    source_chunk_ids = Column(JSON, default=list)
    source_excerpt = Column(Text, nullable=True)
    generation_mode = Column(String, default="offline")

    answer_text = Column(Text, nullable=True)
    answer_submitted_at = Column(DateTime, nullable=True)
    eval_score = Column(Float, nullable=True)
    eval_feedback = Column(Text, nullable=True)

    session = relationship("Session", back_populates="questions")
