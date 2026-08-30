from pydantic import BaseModel
from typing import Optional


class SessionOut(BaseModel):
    id: str
    role: str
    resume_filename: Optional[str]
    extracted_skills: list[str]
    extracted_technologies: list[str]
    extracted_domains: list[str]
    experience_level: str
    status: str

    class Config:
        from_attributes = True


class QuestionOut(BaseModel):
    id: int
    order_index: int
    topic: Optional[str]
    difficulty: str
    prompt_text: str
    source_excerpt: Optional[str]
    generation_mode: str

    class Config:
        from_attributes = True


class AnswerIn(BaseModel):
    answer_text: str


class AnswerOut(BaseModel):
    id: int
    eval_score: Optional[float]
    eval_feedback: Optional[str]

    class Config:
        from_attributes = True


class SummaryOut(BaseModel):
    role: str
    candidate_experience_level: str
    questions_asked: int
    questions_answered: int
    average_score: float
    topic_breakdown: list[dict]
    strengths: list[str]
    growth_areas: list[str]
    resume_skills_detected: list[str]
    resume_technologies_detected: list[str]
    generation_mode: str
