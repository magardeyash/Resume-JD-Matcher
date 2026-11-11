from app.schemas.analysis import ScoreBreakdown

def calculate_score(
    semantic_score: float,
    required_skills_score: float,
    experience_score: float,
    preferred_skills_score: float,
) -> ScoreBreakdown:
    """
    Weighted compatibility score.

    Weights:
        Semantic Similarity:      30%
        Required Skills Match:    40%
        Experience Relevance:     20%
        Preferred Skills Match:   10%
        -----------------------------
        Total:                   100%

    All inputs must be in [0, 100]. Output is in [0, 100].
    Deterministic - no randomness, no external calls.
    """
    compatibility = round(
        semantic_score * 0.30
        + required_skills_score * 0.40
        + experience_score * 0.20
        + preferred_skills_score * 0.10,
        1,
    )
    return ScoreBreakdown(
        compatibility_score=compatibility,
        semantic_score=round(semantic_score, 1),
        required_skills_score=round(required_skills_score, 1),
        experience_score=round(experience_score, 1),
        preferred_skills_score=round(preferred_skills_score, 1),
    )
