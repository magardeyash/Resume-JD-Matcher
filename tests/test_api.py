import uuid
from unittest.mock import patch
import pytest
from app.schemas.analysis import GeminiAnalysis

def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

def test_analyze_missing_file(client, sample_jd):
    res = client.post(
        "/api/analyze",
        data={"jd_text": sample_jd},
    )
    assert res.status_code == 422

def test_analyze_empty_jd(client, sample_txt_bytes):
    res = client.post(
        "/api/analyze",
        files={"resume": ("resume.txt", sample_txt_bytes, "text/plain")},
        data={"jd_text": "   "},
    )
    assert res.status_code == 422
    assert "Job description cannot be empty" in res.json()["detail"]

def test_analyze_jd_too_long(client, sample_txt_bytes):
    long_jd = "x" * 10_001
    res = client.post(
        "/api/analyze",
        files={"resume": ("resume.txt", sample_txt_bytes, "text/plain")},
        data={"jd_text": long_jd},
    )
    assert res.status_code == 422
    assert "too long" in res.json()["detail"]

def test_analyze_job_title_too_long(client, sample_txt_bytes, sample_jd):
    long_title = "t" * 201
    res = client.post(
        "/api/analyze",
        files={"resume": ("resume.txt", sample_txt_bytes, "text/plain")},
        data={"jd_text": sample_jd, "job_title": long_title},
    )
    assert res.status_code == 422
    assert "Job title is too long" in res.json()["detail"]

def test_analyze_bad_extension(client, sample_jd):
    res = client.post(
        "/api/analyze",
        files={"resume": ("malware.exe", b"binarycontent", "application/octet-stream")},
        data={"jd_text": sample_jd},
    )
    assert res.status_code == 422
    assert "Unsupported file type" in res.json()["detail"]

def test_analyze_oversized_file(client, sample_jd):
    # 6 MB file
    big_file = b"x" * (6 * 1024 * 1024)
    res = client.post(
        "/api/analyze",
        files={"resume": ("huge.txt", big_file, "text/plain")},
        data={"jd_text": sample_jd},
    )
    assert res.status_code == 422
    assert "File is too large" in res.json()["detail"]

@patch("app.services.analysis_service.semantic_similarity_score", return_value=85.0)
@patch("app.services.analysis_service.analyze_resume")
def test_analyze_success(mock_analyze, mock_sem, client, sample_txt_bytes, sample_jd, mock_gemini_result):
    mock_analyze.return_value = mock_gemini_result

    res = client.post(
        "/api/analyze",
        files={"resume": ("resume.txt", sample_txt_bytes, "text/plain")},
        data={"jd_text": sample_jd, "job_title": "Python Engineer"},
    )
    assert res.status_code == 201
    data = res.json()
    assert "id" in data
    assert data["resume_filename"] == "resume.txt"
    assert data["job_title"] == "Python Engineer"
    assert data["semantic_score"] == 85.0
    assert data["compatibility_score"] > 0
    assert data["overall_assessment"] == mock_gemini_result.overall_assessment
    assert len(data["matched_skills"]) > 0

    # Verify retrieval via ID works and retains overall_assessment
    analysis_id = data["id"]
    get_res = client.get(f"/api/analyses/{analysis_id}")
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert retrieved["id"] == analysis_id
    assert retrieved["overall_assessment"] == mock_gemini_result.overall_assessment

def test_get_analysis_not_found(client):
    random_id = str(uuid.uuid4())
    res = client.get(f"/api/analyses/{random_id}")
    assert res.status_code == 404
    assert res.json()["detail"] == "Analysis not found."

def test_get_analysis_bad_uuid(client):
    res = client.get("/api/analyses/invalid-not-a-uuid")
    assert res.status_code == 400
    assert "Invalid analysis ID format" in res.json()["detail"]

def test_analyses_requires_auth(client):
    # GET /api/analyses requires authentication, so unauthenticated returns 401
    res = client.get("/api/analyses")
    assert res.status_code == 401

@patch("app.services.analysis_service.semantic_similarity_score", side_effect=RuntimeError("GEMINI_API_KEY is not configured."))
def test_analyze_gemini_key_missing(mock_sem, client, sample_txt_bytes, sample_jd):
    res = client.post(
        "/api/analyze",
        files={"resume": ("resume.txt", sample_txt_bytes, "text/plain")},
        data={"jd_text": sample_jd},
    )
    assert res.status_code == 503
    assert "GEMINI_API_KEY is not configured" in res.json()["detail"]
