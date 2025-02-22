from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Resume Ranking API"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MAX_FILES: int = 20
    MAX_CRITERIA: int = 15
    ALLOWED_MIME_TYPES: dict = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx"
    }
    CORS_ORIGINS: List[str] = ["*"]
    MODEL_NAME: str = "gpt-3.5-turbo-0125"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
