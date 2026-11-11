from pathlib import Path
from io import BytesIO
import fitz
from docx import Document
from app.core.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

def validate_extension(filename: str) -> None:
    """Check file extension. Raises ValueError for unsupported types."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. Accepted formats: PDF, DOCX, TXT."
        )

def parse_resume(filename: str, content: bytes) -> str:
    """
    Extract text from resume content.
    Raises ValueError for empty, unreadable, or oversized extracted text.
    File size has already been enforced before this is called.
    """
    ext = Path(filename).suffix.lower()
    try:
        if ext == ".pdf":
            text = _extract_pdf(content)
        elif ext == ".docx":
            text = _extract_docx(content)
        else:
            text = _extract_txt(content)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Could not read the uploaded file: {exc}") from exc

    # Normalize whitespace
    text = " ".join(text.split())

    if not text:
        raise ValueError(
            "The uploaded document appears to be empty or contains no readable text."
        )

    # Enforce extracted text length BEFORE making any API calls
    if len(text) > settings.max_resume_text_length:
        raise ValueError(
            f"Extracted resume text is too long ({len(text):,} characters). "
            f"Maximum allowed is {settings.max_resume_text_length:,} characters. "
            f"Please upload a shorter resume or trim it to the essential content."
        )

    return text

def _extract_pdf(content: bytes) -> str:
    with fitz.open(stream=content, filetype="pdf") as doc:
        pages = [page.get_text() for page in doc]
    return "\n".join(pages)

def _extract_docx(content: bytes) -> str:
    doc = Document(BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def _extract_txt(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1")
