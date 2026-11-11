import pytest
from app.services.scoring_service import calculate_score
from app.services.embedding_service import cosine_similarity

def test_all_zero_inputs():
    res = calculate_score(0.0, 0.0, 0.0, 0.0)
    assert res.compatibility_score == 0.0
    assert res.semantic_score == 0.0
    assert res.required_skills_score == 0.0
    assert res.experience_score == 0.0
    assert res.preferred_skills_score == 0.0

def test_all_hundred_inputs():
    res = calculate_score(100.0, 100.0, 100.0, 100.0)
    assert res.compatibility_score == 100.0

def test_semantic_weight_only():
    # Only semantic is 100 (30% weight)
    res = calculate_score(100.0, 0.0, 0.0, 0.0)
    assert res.compatibility_score == 30.0

def test_required_skills_weight_only():
    # Only required is 100 (40% weight)
    res = calculate_score(0.0, 100.0, 0.0, 0.0)
    assert res.compatibility_score == 40.0

def test_experience_weight_only():
    # Only experience is 100 (20% weight)
    res = calculate_score(0.0, 0.0, 100.0, 0.0)
    assert res.compatibility_score == 20.0

def test_preferred_skills_weight_only():
    # Only preferred is 100 (10% weight)
    res = calculate_score(0.0, 0.0, 0.0, 100.0)
    assert res.compatibility_score == 10.0

def test_deterministic_scoring():
    r1 = calculate_score(75.5, 80.0, 65.0, 50.0)
    r2 = calculate_score(75.5, 80.0, 65.0, 50.0)
    assert r1.compatibility_score == r2.compatibility_score
    assert r1.model_dump() == r2.model_dump()

def test_mixed_known_values():
    # 70 * 0.30 = 21.0
    # 80 * 0.40 = 32.0
    # 60 * 0.20 = 12.0
    # 90 * 0.10 = 9.0
    # Total = 21 + 32 + 12 + 9 = 74.0
    res = calculate_score(70.0, 80.0, 60.0, 90.0)
    assert res.compatibility_score == 74.0

# --- Cosine Similarity Tests ---

def test_cosine_identical_vectors():
    vec_a = [1.0, 2.0, 3.0]
    vec_b = [1.0, 2.0, 3.0]
    sim = cosine_similarity(vec_a, vec_b)
    assert pytest.approx(sim, 0.001) == 1.0
    # Normalization check: (1 + 1)/2 * 100 = 100
    normalized = (sim + 1.0) / 2.0 * 100.0
    assert pytest.approx(normalized, 0.01) == 100.0

def test_cosine_orthogonal_vectors():
    vec_a = [1.0, 0.0]
    vec_b = [0.0, 1.0]
    sim = cosine_similarity(vec_a, vec_b)
    assert pytest.approx(sim, 0.001) == 0.0
    # Normalization check: (0 + 1)/2 * 100 = 50
    normalized = (sim + 1.0) / 2.0 * 100.0
    assert pytest.approx(normalized, 0.01) == 50.0

def test_cosine_opposite_vectors():
    vec_a = [1.0, 0.0]
    vec_b = [-1.0, 0.0]
    sim = cosine_similarity(vec_a, vec_b)
    assert pytest.approx(sim, 0.001) == -1.0
    # Normalization check: (-1 + 1)/2 * 100 = 0
    normalized = (sim + 1.0) / 2.0 * 100.0
    assert pytest.approx(normalized, 0.01) == 0.0

def test_cosine_zero_vector_safe():
    vec_a = [0.0, 0.0, 0.0]
    vec_b = [1.0, 2.0, 3.0]
    sim = cosine_similarity(vec_a, vec_b)
    assert sim == 0.0
