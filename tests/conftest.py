import sys
from pathlib import Path

# Ensure backend directory is on sys.path
_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import Base, get_db
from app.schemas.analysis import GeminiAnalysis, SkillItem, SkillImportance

# Pure in-memory SQLite with StaticPool - single shared memory DB across threads
_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_SessionFactory = sessionmaker(bind=_ENGINE, autocommit=False, autoflush=False)

@pytest.fixture()
def db_session():
    """
    Each test gets a fresh isolated database schema.
    Tables are created before the test and dropped after.
    """
    Base.metadata.create_all(_ENGINE)
    session = _SessionFactory()
    yield session
    session.close()
    Base.metadata.drop_all(_ENGINE)

@pytest.fixture()
def client(db_session):
    """TestClient with DB dependency overridden to the isolated session."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture()
def mock_gemini_result() -> GeminiAnalysis:
    """A realistic mock GeminiAnalysis for testing without real API calls."""
    return GeminiAnalysis(
        required_skill_coverage=80.0,
        preferred_skill_coverage=60.0,
        experience_relevance=75.0,
        matched_skills=[
            SkillItem(
                name="Python",
                importance=SkillImportance.required,
                explanation="Explicitly listed in resume and required by JD.",
            ),
            SkillItem(
                name="FastAPI",
                importance=SkillImportance.required,
                explanation="Resume highlights building APIs with FastAPI.",
            ),
        ],
        missing_skills=[
            SkillItem(
                name="Kubernetes",
                importance=SkillImportance.preferred,
                explanation="Mentioned as preferred in JD, not found in resume.",
            ),
        ],
        partial_matches=[
            SkillItem(
                name="CI/CD",
                importance=SkillImportance.required,
                explanation="Resume mentions GitHub Actions which is a CI/CD tool.",
            ),
        ],
        strengths=["Strong Python background", "FastAPI web services experience"],
        weaknesses=["No mention of container orchestration or Kubernetes"],
        improvement_suggestions=[
            "Highlight GitHub Actions workflows explicitly under a CI/CD section.",
            "Describe database optimization techniques used with PostgreSQL.",
        ],
        overall_assessment="Strong candidate profile for backend API roles with some DevOps gaps.",
    )

@pytest.fixture()
def sample_txt_bytes() -> bytes:
    return (
        b"John Doe | Python Backend Developer\n"
        b"Skills: Python, FastAPI, PostgreSQL, Docker, GitHub Actions\n"
        b"Experience: 3 years building REST APIs and microservices."
    )

@pytest.fixture()
def sample_jd() -> str:
    return (
        "We seek a Python developer with FastAPI, PostgreSQL, and Docker skills. "
        "Experience with CI/CD and Kubernetes is preferred."
    )
