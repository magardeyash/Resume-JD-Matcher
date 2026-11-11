from google import genai
from google.genai import types as genai_types
from google.genai.errors import ClientError, ServerError
from app.core.config import settings
from app.schemas.analysis import GeminiAnalysis

_SYSTEM_PROMPT = """
You are a professional resume analyst. Compare the candidate's resume against the
job description and return a structured JSON analysis.

You MUST follow these rules:
1. NEVER invent skills, certifications, projects, or experience not present in the resume.
2. NEVER assume a skill is absent just because it isn't explicitly named - the candidate
   may use it under a different terminology. Flag such cases as partial_matches.
3. Distinguish REQUIRED from PREFERRED qualifications in the job description.
4. Base improvement_suggestions strictly on what is already in the resume.
   Suggest better presentation of existing experience - never fabricate new experience.
5. Never recommend keyword stuffing.
6. For each skill in matched_skills, missing_skills, and partial_matches, explain
   specifically why it is relevant to this role.
7. Keep all float scores in the range 0-100.
8. Be specific. Avoid generic statements like "add more skills".
"""

def analyze_resume(resume_text: str, jd_text: str) -> GeminiAnalysis:
    """
    Call Gemini with structured output. Returns a validated GeminiAnalysis.

    Raises:
        RuntimeError: Missing API key, rate limit, provider error, or timeout.
        ValueError: Gemini returned a structurally invalid response.
    """
    api_key = settings.require_gemini_key()
    client = genai.Client(api_key=api_key)

    prompt = (
        f"RESUME:\n{resume_text}\n\n"
        f"{'-' * 40}\n\n"
        f"JOB DESCRIPTION:\n{jd_text}"
    )

    try:
        response = client.models.generate_content(
            model=settings.gemini_chat_model,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=GeminiAnalysis,
            ),
        )
    except ClientError as exc:
        if exc.code == 429:
            raise RuntimeError(
                "AI analysis service is rate-limited. Please wait a moment and try again."
            ) from exc
        if exc.code in (401, 403):
            raise RuntimeError(
                "AI analysis service authentication failed. "
                "Please check the GEMINI_API_KEY configuration."
            ) from exc
        raise RuntimeError(
            "AI analysis service returned an error. Please try again later."
        ) from exc
    except ServerError as exc:
        raise RuntimeError(
            "AI analysis service is temporarily unavailable. Please try again later."
        ) from exc
    except TimeoutError as exc:
        raise RuntimeError(
            "AI analysis request timed out. Please try again."
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            "An unexpected error occurred during AI analysis."
        ) from exc

    # Validate the structured response - do not silently accept malformed output
    try:
        return GeminiAnalysis.model_validate_json(response.text)
    except Exception as exc:
        raise ValueError(
            "AI analysis returned an unexpected response format. "
            "The analysis cannot be completed. Please try again."
        ) from exc
