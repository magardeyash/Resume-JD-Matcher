from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file, independent of CWD.
# config.py is at: backend/app/core/config.py
# 4 parents up -> project root where .env lives
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"

class Settings(BaseSettings):
    # --- Database ---
    database_url: str = "postgresql://postgres:postgres@localhost:5433/resumematch"

    # --- Gemini ---
    gemini_api_key: Optional[str] = None
    gemini_chat_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 768      # passed to output_dimensionality

    # --- Authentication ---
    jwt_secret_key: str = "super-secret-jwt-key-change-in-production-resume-matcher-2026"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # --- Upload limits ---
    max_upload_size_mb: int = 5

    # --- Text length limits (validation BEFORE API calls) ---
    max_resume_text_length: int = 15_000   # chars after extraction
    max_jd_length: int = 10_000            # chars of pasted JD
    max_job_title_length: int = 200        # chars of optional title

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    def get_database_url(self) -> str:
        """Normalize postgresql:// -> postgresql+psycopg2:// for SQLAlchemy."""
        url = self.database_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url

    def require_gemini_key(self) -> str:
        """Raises RuntimeError if GEMINI_API_KEY is not set."""
        if not self.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. "
                "Add it to your .env file or Render environment variables."
            )
        return self.gemini_api_key

settings = Settings()
