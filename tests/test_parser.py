import pytest
from io import BytesIO
import fitz
from docx import Document
from app.services.resume_parser import (
    validate_extension,
    parse_resume,
    ALLOWED_EXTENSIONS,
)

def test_allowed_extensions():
    assert ".pdf" in ALLOWED_EXTENSIONS
    assert ".docx" in ALLOWED_EXTENSIONS
    assert ".txt" in ALLOWED_EXTENSIONS

def test_validate_extension_valid():
    validate_extension("resume.pdf")
    validate_extension("MY_RESUME.DOCX")
    validate_extension("notes.txt")

def test_validate_extension_invalid():
    with pytest.raises(ValueError, match="Unsupported file type"):
        validate_extension("malicious.exe")
    with pytest.raises(ValueError, match="Unsupported file type"):
        validate_extension("image.png")

def test_valid_txt_extraction():
    content = b"Senior Software Engineer\nPython, Docker, AWS"
    text = parse_resume("resume.txt", content)
    assert "Senior Software Engineer" in text
    assert "Python, Docker, AWS" in text

def test_valid_pdf_extraction():
    # Create in-memory PDF with fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Jane Doe - Full Stack Developer\nFastAPI and React experience")
    pdf_bytes = doc.tobytes()
    doc.close()

    text = parse_resume("candidate.pdf", pdf_bytes)
    assert "Jane Doe" in text
    assert "FastAPI and React" in text

def test_valid_docx_extraction():
    # Create in-memory DOCX with python-docx
    doc = Document()
    doc.add_paragraph("Alice Smith")
    doc.add_paragraph("DevOps Engineer skilled in Kubernetes and Terraform")
    bio = BytesIO()
    doc.save(bio)
    docx_bytes = bio.getvalue()

    text = parse_resume("alice.docx", docx_bytes)
    assert "Alice Smith" in text
    assert "DevOps Engineer" in text

def test_empty_txt_raises():
    with pytest.raises(ValueError, match="empty or contains no readable text"):
        parse_resume("empty.txt", b"")

def test_whitespace_only_txt_raises():
    with pytest.raises(ValueError, match="empty or contains no readable text"):
        parse_resume("spaces.txt", b"   \n\n  \t  ")

def test_oversized_extracted_text_raises():
    # 15,001 characters
    long_content = b"a" * 15_001
    with pytest.raises(ValueError, match="Extracted resume text is too long"):
        parse_resume("huge.txt", long_content)

def test_txt_latin1_fallback():
    # Encode with latin-1 characters that aren't valid UTF-8
    latin1_bytes = "Résumé with accents: José café".encode("latin-1")
    text = parse_resume("accent.txt", latin1_bytes)
    assert "José" in text or "café" in text or "accents" in text
