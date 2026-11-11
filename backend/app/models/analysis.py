import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Float, DateTime, JSON, Text, ForeignKey, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.user import User

class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    resume_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Score components (all 0-100)
    compatibility_score: Mapped[float] = mapped_column(Float, nullable=False)
    semantic_score: Mapped[float] = mapped_column(Float, nullable=False)
    required_skills_score: Mapped[float] = mapped_column(Float, nullable=False)
    experience_score: Mapped[float] = mapped_column(Float, nullable=False)
    preferred_skills_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Skill lists (JSON arrays of SkillItem dicts)
    matched_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    missing_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    partial_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Textual analysis
    strengths: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    weaknesses: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    suggestions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    overall_assessment: Mapped[str] = mapped_column(Text, nullable=False, default="")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User | None"] = relationship("User", back_populates="analyses")
