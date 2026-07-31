from __future__ import annotations

import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    TESTING = False
    DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
    AI_MODE = os.getenv("AI_MODE", "mock").strip().lower()
    AI_API_KEY = os.getenv("AI_API_KEY", "").strip()
    MAX_REQUIREMENT_CHARS = int(os.getenv("MAX_REQUIREMENT_CHARS", "30000"))
    MAX_CONTENT_LENGTH = 128 * 1024
    CREATE_SCHEMA = False

    @classmethod
    def validate(cls) -> None:
        if cls.AI_MODE != "mock":
            raise RuntimeError("Phase 1 supports AI_MODE=mock only.")
