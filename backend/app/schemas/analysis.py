from __future__ import annotations
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime

class SkillImportance(str, Enum):
    required = "required"
    preferred = "preferred"

class SkillItem(BaseModel):
    name: str
    importance: SkillImportance
    explanation: str

class GeminiAnalysis(BaseModel):
    """Validated structured output from Gemini. Used as response_schema."""
    required_skill_coverage: float = Field(ge=0, le=100)
    preferred_skill_coverage: float = Field(ge=0, le=100)
    experience_relevance: float = Field(ge=0, le=100)
    matched_skills: list[SkillItem]
    missing_skills: list[SkillItem]
    partial_matches: list[SkillItem]
    strengths: list[str]
    weaknesses: list[str]
    improvement_suggestions: list[str]
    overall_assessment: str

class ScoreBreakdown(BaseModel):
    compatibility_score: float
    semantic_score: float
    required_skills_score: float
    experience_score: float
    preferred_skills_score: float

class AnalysisResponse(BaseModel):
    """Full API response - mirrors DB columns."""
    id: str
    user_id: Optional[str] = None
    resume_filename: str
    job_title: Optional[str]
    compatibility_score: float
    semantic_score: float
    required_skills_score: float
    experience_score: float
    preferred_skills_score: float
    matched_skills: list[SkillItem]
    missing_skills: list[SkillItem]
    partial_skills: list[SkillItem]
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]
    overall_assessment: str
    created_at: datetime

    model_config = {"from_attributes": True}
