import uuid
from unittest.mock import patch
import pytest

def test_register_success(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "alice@example.com", "password": "password123", "full_name": "Alice Smith"},
    )
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["full_name"] == "Alice Smith"

def test_register_duplicate_email(client):
    client.post(
        "/api/auth/register",
        json={"email": "duplicate@example.com", "password": "password123"},
    )
    res = client.post(
        "/api/auth/register",
        json={"email": "duplicate@example.com", "password": "password456"},
    )
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]

def test_register_invalid_email(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": "password123"},
    )
    assert res.status_code == 422

def test_register_short_password(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "short@example.com", "password": "123"},
    )
    assert res.status_code == 422
    assert "at least 6 characters" in res.json()["detail"][0]["msg"]

def test_login_success(client):
    client.post(
        "/api/auth/register",
        json={"email": "bob@example.com", "password": "securepassword123"},
    )
    res = client.post(
        "/api/auth/login",
        json={"email": "bob@example.com", "password": "securepassword123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "bob@example.com"

def test_login_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={"email": "carol@example.com", "password": "correctpassword"},
    )
    res = client.post(
        "/api/auth/login",
        json={"email": "carol@example.com", "password": "wrongpassword"},
    )
    assert res.status_code == 401
    assert "Incorrect email or password" in res.json()["detail"]

def test_login_nonexistent_user(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "ghost@example.com", "password": "password123"},
    )
    assert res.status_code == 401

def test_get_me_authenticated(client):
    reg = client.post(
        "/api/auth/register",
        json={"email": "dave@example.com", "password": "password123", "full_name": "Dave"},
    )
    token = reg.json()["access_token"]
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "dave@example.com"
    assert res.json()["full_name"] == "Dave"

def test_get_me_unauthenticated(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401

@patch("app.services.analysis_service.semantic_similarity_score", return_value=85.0)
@patch("app.services.analysis_service.analyze_resume")
def test_user_isolated_analyses(mock_analyze, mock_sem, client, sample_txt_bytes, sample_jd, mock_gemini_result):
    mock_analyze.return_value = mock_gemini_result

    # 1. Register User A and create an analysis
    reg_a = client.post("/api/auth/register", json={"email": "userA@example.com", "password": "password123"})
    token_a = reg_a.json()["access_token"]
    user_a_id = reg_a.json()["user"]["id"]

    res_a = client.post(
        "/api/analyze",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"resume": ("resumeA.txt", sample_txt_bytes, "text/plain")},
        data={"jd_text": sample_jd, "job_title": "Role A"},
    )
    assert res_a.status_code == 201
    analysis_a_id = res_a.json()["id"]

    # 2. Register User B
    reg_b = client.post("/api/auth/register", json={"email": "userB@example.com", "password": "password123"})
    token_b = reg_b.json()["access_token"]

    # User B list analyses: should be EMPTY
    res_list_b = client.get("/api/analyses", headers={"Authorization": f"Bearer {token_b}"})
    assert res_list_b.status_code == 200
    assert len(res_list_b.json()) == 0

    # User A list analyses: should contain 1 analysis
    res_list_a = client.get("/api/analyses", headers={"Authorization": f"Bearer {token_a}"})
    assert res_list_a.status_code == 200
    assert len(res_list_a.json()) == 1
    assert res_list_a.json()[0]["id"] == analysis_a_id

    # User B tries to view User A's analysis: 403 Forbidden!
    res_view_forbidden = client.get(f"/api/analyses/{analysis_a_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res_view_forbidden.status_code == 403

    # User A can view their own analysis: 200 OK
    res_view_ok = client.get(f"/api/analyses/{analysis_a_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert res_view_ok.status_code == 200
    assert res_view_ok.json()["id"] == analysis_a_id

    # User B tries to delete User A's analysis: 403 Forbidden!
    del_forbidden = client.delete(f"/api/analyses/{analysis_a_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert del_forbidden.status_code == 403

    # User A deletes their own analysis: 200 OK
    del_ok = client.delete(f"/api/analyses/{analysis_a_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert del_ok.status_code == 200

    # Confirm it is gone
    res_gone = client.get(f"/api/analyses/{analysis_a_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert res_gone.status_code == 404
