import pytest
from unittest.mock import patch
from pydantic import ValidationError
from app.services.analysis_service import run_analysis
from app.services.skill_matcher import classify_skills, normalize_skill_name
from app.models.analysis import Analysis
from app.schemas.analysis import GeminiAnalysis, SkillItem, SkillImportance

def test_normalize_skill_name():
    assert normalize_skill_name("  Python 3.11! ") == "python 3 11"
    assert normalize_skill_name("REST-API / Microservices") == "rest api microservices"

def test_cross_list_deduplication():
    # If Python is in both matched and missing, it should remain ONLY in matched
    gemini_data = GeminiAnalysis(
        required_skill_coverage=70.0,
        preferred_skill_coverage=50.0,
        experience_relevance=60.0,
        matched_skills=[
            SkillItem(name="Python", importance=SkillImportance.required, explanation="Found in resume"),
            SkillItem(name="SQL", importance=SkillImportance.required, explanation="Found in resume"),
        ],
        missing_skills=[
            SkillItem(name="python", importance=SkillImportance.required, explanation="Should be removed"),
            SkillItem(name="Docker", importance=SkillImportance.preferred, explanation="Missing"),
        ],
        partial_matches=[
            SkillItem(name="SQL", importance=SkillImportance.required, explanation="Should be removed"),
            SkillItem(name="AWS", importance=SkillImportance.preferred, explanation="Partial"),
        ],
        strengths=["Good foundations"],
        weaknesses=["Needs cloud experience"],
        improvement_suggestions=["Get AWS certified"],
        overall_assessment="Solid candidate",
    )

    matched, missing, partial = classify_skills(gemini_data)

    matched_names = [s["name"] for s in matched]
    missing_names = [s["name"] for s in missing]
    partial_names = [s["name"] for s in partial]

    assert "Python" in matched_names
    assert "SQL" in matched_names

    # Ensure "python" was filtered out of missing
    assert not any(s.lower() == "python" for s in missing_names)
    assert "Docker" in missing_names

    # Ensure "SQL" was filtered out of partial
    assert not any(s.lower() == "sql" for s in partial_names)
    assert "AWS" in partial_names

def test_within_list_deduplication():
    gemini_data = GeminiAnalysis(
        required_skill_coverage=80.0,
        preferred_skill_coverage=60.0,
        experience_relevance=70.0,
        matched_skills=[
            SkillItem(name="Docker", importance=SkillImportance.required, explanation="1st exp"),
            SkillItem(name="docker", importance=SkillImportance.required, explanation="2nd exp"),
        ],
        missing_skills=[],
        partial_matches=[],
        strengths=[],
        weaknesses=[],
        improvement_suggestions=[],
        overall_assessment="Test",
    )
    matched, _, _ = classify_skills(gemini_data)
    assert len(matched) == 1
    assert matched[0]["name"] == "Docker"
    assert matched[0]["explanation"] == "1st exp"

def test_pydantic_valid_gemini_output(mock_gemini_result):
    json_str = mock_gemini_result.model_dump_json()
    parsed = GeminiAnalysis.model_validate_json(json_str)
    assert parsed.required_skill_coverage == 80.0
    assert len(parsed.matched_skills) == 2

def test_pydantic_invalid_coverage_raises():
    with pytest.raises(ValidationError):
        GeminiAnalysis(
            required_skill_coverage=150.0,  # Invalid: > 100
            preferred_skill_coverage=50.0,
            experience_relevance=50.0,
            matched_skills=[],
            missing_skills=[],
            partial_matches=[],
            strengths=[],
            weaknesses=[],
            improvement_suggestions=[],
            overall_assessment="Invalid",
        )

def test_pydantic_invalid_importance_raises():
    with pytest.raises(ValidationError):
        SkillItem(
            name="Python",
            importance="super_critical",  # Invalid enum
            explanation="Test",
        )

@patch("app.services.analysis_service.semantic_similarity_score", return_value=82.5)
@patch("app.services.analysis_service.analyze_resume")
def test_run_analysis_pipeline_and_db_persistence(
    mock_analyze, mock_sem, db_session, sample_txt_bytes, sample_jd, mock_gemini_result
):
    mock_analyze.return_value = mock_gemini_result

    res = run_analysis(
        db=db_session,
        filename="resume.txt",
        file_content=sample_txt_bytes,
        jd_text=sample_jd,
        job_title="Software Architect",
    )

    assert res.compatibility_score > 0
    assert res.overall_assessment == mock_gemini_result.overall_assessment

    # Verify directly in SQLite DB
    records = db_session.query(Analysis).all()
    assert len(records) == 1
    db_rec = records[0]
    assert db_rec.resume_filename == "resume.txt"
    assert db_rec.job_title == "Software Architect"
    assert db_rec.overall_assessment == mock_gemini_result.overall_assessment

    # Verify resume text is NEVER stored in the database model
    columns = [c.name for c in Analysis.__table__.columns]
    assert "resume_text" not in columns
    assert "content" not in columns
    assert "raw_text" not in columns

@patch("app.services.analysis_service.semantic_similarity_score", side_effect=RuntimeError("AI Failed"))
def test_no_db_write_on_pipeline_failure(mock_sem, db_session, sample_txt_bytes, sample_jd):
    with pytest.raises(RuntimeError):
        run_analysis(
            db=db_session,
            filename="resume.txt",
            file_content=sample_txt_bytes,
            jd_text=sample_jd,
            job_title="Dev",
        )
    # Confirm DB has 0 records
    assert db_session.query(Analysis).count() == 0
