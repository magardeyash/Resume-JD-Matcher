import uuid
from sqlalchemy.orm import Session
from app.services.resume_parser import validate_extension, parse_resume
from app.services.embedding_service import semantic_similarity_score
from app.services.gemini_service import analyze_resume
from app.services.skill_matcher import classify_skills
from app.services.scoring_service import calculate_score
from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisResponse

def run_analysis(
    db: Session,
    filename: str,
    file_content: bytes,         # already size-checked in routes
    jd_text: str,                # already length-checked in routes
    job_title: str | None,
    user_id: uuid.UUID | None = None,
) -> AnalysisResponse:
    """
    Full analysis pipeline. All validations raise ValueError or RuntimeError.
    Nothing is saved to the DB unless all steps succeed.
    Resume text is NOT stored.
    """
    # Step 1: Validate extension
    validate_extension(filename)

    # Step 2: Extract text (also validates extracted length)
    resume_text = parse_resume(filename, file_content)

    # Step 3: Semantic similarity (validates key, calls embedding API twice)
    sem_score = semantic_similarity_score(resume_text, jd_text)

    # Step 4: Gemini structured analysis
    gemini_result = analyze_resume(resume_text, jd_text)

    # Step 5: Cross-list skill deduplication
    matched, missing, partial = classify_skills(gemini_result)

    # Step 6: Weighted score
    scores = calculate_score(
        semantic_score=sem_score,
        required_skills_score=gemini_result.required_skill_coverage,
        experience_score=gemini_result.experience_relevance,
        preferred_skills_score=gemini_result.preferred_skill_coverage,
    )

    # Step 7: Persist - resume text NOT saved
    record = Analysis(
        id=uuid.uuid4(),
        user_id=user_id,
        resume_filename=filename,
        job_title=job_title,
        compatibility_score=scores.compatibility_score,
        semantic_score=scores.semantic_score,
        required_skills_score=scores.required_skills_score,
        experience_score=scores.experience_score,
        preferred_skills_score=scores.preferred_skills_score,
        matched_skills=matched,
        missing_skills=missing,
        partial_skills=partial,
        strengths=gemini_result.strengths,
        weaknesses=gemini_result.weaknesses,
        suggestions=gemini_result.improvement_suggestions,
        overall_assessment=gemini_result.overall_assessment,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return _record_to_response(record)

def _record_to_response(record: Analysis) -> AnalysisResponse:
    return AnalysisResponse(
        id=str(record.id),
        user_id=str(record.user_id) if record.user_id else None,
        resume_filename=record.resume_filename,
        job_title=record.job_title,
        compatibility_score=record.compatibility_score,
        semantic_score=record.semantic_score,
        required_skills_score=record.required_skills_score,
        experience_score=record.experience_score,
        preferred_skills_score=record.preferred_skills_score,
        matched_skills=record.matched_skills,
        missing_skills=record.missing_skills,
        partial_skills=record.partial_skills,
        strengths=record.strengths,
        weaknesses=record.weaknesses,
        suggestions=record.suggestions,
        overall_assessment=record.overall_assessment,
        created_at=record.created_at,
    )
