import numpy as np
from google import genai
from google.genai import types as genai_types
from google.genai.errors import ClientError, ServerError
from app.core.config import settings

def get_embedding(text: str, text_label: str = "text") -> list[float]:
    """
    Generate an embedding vector for the given text.

    Does NOT silently truncate. The caller must have already validated
    text length against the configured maximum.

    Args:
        text: The text to embed.
        text_label: Human-readable label for error messages (e.g., "resume", "job description").

    Raises:
        RuntimeError: If GEMINI_API_KEY is not configured.
        ValueError: If the embedding API returns an empty vector.
        RuntimeError: If the API call fails due to a provider error.
    """
    api_key = settings.require_gemini_key()
    client = genai.Client(api_key=api_key)

    try:
        response = client.models.embed_content(
            model=settings.gemini_embedding_model,
            contents=text,
            config=genai_types.EmbedContentConfig(
                output_dimensionality=settings.embedding_dimensions,
            ),
        )
    except ClientError as exc:
        if exc.code == 429:
            raise RuntimeError(
                "Embedding service is rate-limited. Please wait a moment and try again."
            ) from exc
        raise RuntimeError(
            f"Embedding service returned an error for the {text_label}. "
            "Please try again later."
        ) from exc
    except ServerError as exc:
        raise RuntimeError(
            "Embedding service is temporarily unavailable. Please try again later."
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            f"An unexpected error occurred while generating the {text_label} embedding."
        ) from exc

    values = response.embeddings[0].values
    if not values:
        raise ValueError(
            f"Embedding API returned an empty vector for the {text_label}."
        )
    return list(values)

def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    Returns a value in [-1.0, 1.0]:
      1.0  -> identical direction (highly similar)
      0.0  -> orthogonal (unrelated)
     -1.0  -> opposite direction (antonymous - rare in text)
    Returns 0.0 for zero vectors to avoid division by zero.
    """
    a = np.array(vec_a, dtype=float)
    b = np.array(vec_b, dtype=float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

def semantic_similarity_score(resume_text: str, jd_text: str) -> float:
    """
    Compute a 0-100 semantic similarity score between resume and JD.

    Heuristic normalization:
        raw in [-1.0, 1.0]  (cosine similarity)
        score = (raw + 1.0) / 2.0 * 100.0

    Mapping landmarks:
        raw = -1.0 -> score =   0  (perfectly opposite - theoretical minimum)
        raw =  0.0 -> score =  50  (orthogonal / unrelated)
        raw = +1.0 -> score = 100  (identical direction)

    In practice, text embeddings from Gemini rarely produce raw cosine values
    below ~0.3, so typical scores for unrelated documents are ~65 and for
    well-matched documents ~90+. This is a heuristic transform for scoring
    purposes and does NOT represent a calibrated probability.

    The compatibility_score disclaimer is shown in the UI:
        "This score is an approximate relevance estimate, not a hiring prediction."
    """
    resume_emb = get_embedding(resume_text, text_label="resume")
    jd_emb = get_embedding(jd_text, text_label="job description")
    raw = cosine_similarity(resume_emb, jd_emb)
    score = (raw + 1.0) / 2.0 * 100.0
    return round(max(0.0, min(100.0, score)), 2)
