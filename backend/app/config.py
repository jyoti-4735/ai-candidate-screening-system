import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY") or None
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./interview.db")
    KB_DIR: str = os.path.join(os.path.dirname(__file__), "knowledge_base", "seed_data")
    CHUNK_SIZE: int = 700          # characters per chunk
    CHUNK_OVERLAP: int = 120       # characters of overlap (context preservation)
    TOP_K: int = 4                 # chunks retrieved per query
    MAX_QUESTIONS: int = 6

    @property
    def LLM_MODE(self) -> str:
        return "gemini" if self.GEMINI_API_KEY else "offline"

settings = Settings()
