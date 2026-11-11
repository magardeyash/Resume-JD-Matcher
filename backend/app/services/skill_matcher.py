import re
from app.schemas.analysis import SkillItem, GeminiAnalysis

def normalize_skill_name(name: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace for comparison."""
    name = name.lower()
    name = re.sub(r"[^\w\s]", " ", name)
    return " ".join(name.split())

def _deduplicate_within(skills: list[SkillItem]) -> list[SkillItem]:
    """Remove duplicates within a single skill list (by normalized name)."""
    seen: set[str] = set()
    result: list[SkillItem] = []
    for skill in skills:
        key = normalize_skill_name(skill.name)
        if key not in seen:
            seen.add(key)
            result.append(skill)
    return result

def classify_skills(
    gemini_result: GeminiAnalysis,
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Post-process and deduplicate Gemini skill lists.

    Priority order for cross-list deduplication:
        1. matched_skills (highest priority - skill is confirmed present)
        2. partial_matches (second - skill is partially demonstrated)
        3. missing_skills (lowest - skill is absent)

    A skill key appearing in matched cannot also appear in partial or missing.
    A skill key appearing in partial cannot also appear in missing.
    Within-list duplicates are also removed.
    Explanations from the highest-priority list are preserved.

    Returns: (matched_dicts, missing_dicts, partial_dicts)
    """
    matched = _deduplicate_within(gemini_result.matched_skills)
    partial = _deduplicate_within(gemini_result.partial_matches)
    missing = _deduplicate_within(gemini_result.missing_skills)

    matched_keys = {normalize_skill_name(s.name) for s in matched}

    # Remove from partial if already matched
    partial = [s for s in partial if normalize_skill_name(s.name) not in matched_keys]

    # Remove from missing if already matched or partial
    all_higher_keys = matched_keys | {normalize_skill_name(s.name) for s in partial}
    missing = [s for s in missing if normalize_skill_name(s.name) not in all_higher_keys]

    return (
        [s.model_dump() for s in matched],
        [s.model_dump() for s in missing],
        [s.model_dump() for s in partial],
    )
