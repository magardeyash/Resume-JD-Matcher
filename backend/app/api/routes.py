import uuid
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.database import get_db
from app.services.analysis_service import run_analysis, _record_to_response
from app.models.analysis import Analysis
from app.models.user import User
from app.schemas.analysis import AnalysisResponse
from app.api.deps import get_current_user, get_optional_current_user
from app.api.auth import auth_router

router = APIRouter(prefix="/api")
router.include_router(auth_router)

async def _read_upload_safely(file: UploadFile, max_bytes: int) -> bytes:
    """
    Read an uploaded file in chunks, enforcing the size limit without
    loading an unlimited amount of data into memory first.
    Raises ValueError if the file exceeds max_bytes.
    """
    content = bytearray()
    chunk_size = 65_536  # 64 KB chunks
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        content.extend(chunk)
        if len(content) > max_bytes:
            limit_mb = max_bytes // (1024 * 1024)
            raise ValueError(
                f"File is too large. Maximum allowed size is {limit_mb} MB."
            )
    return bytes(content)

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/analyze", response_model=AnalysisResponse, status_code=201)
async def analyze(
    resume: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT)"),
    jd_text: str = Form(..., description="Job description text"),
    job_title: str | None = Form(default=None, description="Optional job title"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Run a full resume-job description analysis.
    If authenticated, links the analysis to the logged-in user.
    """
    # 1. JD text validation
    if not jd_text or not jd_text.strip():
        raise HTTPException(status_code=422, detail="Job description cannot be empty.")
    if len(jd_text) > settings.max_jd_length:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Job description is too long ({len(jd_text):,} characters). "
                f"Maximum allowed is {settings.max_jd_length:,} characters."
            ),
        )

    # 2. Job title validation
    if job_title and len(job_title) > settings.max_job_title_length:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Job title is too long ({len(job_title)} characters). "
                f"Maximum allowed is {settings.max_job_title_length} characters."
            ),
        )

    # 3. Safe chunked file read (enforces size limit without loading everything first)
    try:
        file_content = await _read_upload_safely(resume, settings.max_upload_size_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # 4. Run full analysis pipeline
    user_id = current_user.id if current_user else None
    try:
        return run_analysis(
            db=db,
            filename=resume.filename or "upload",
            file_content=file_content,
            jd_text=jd_text.strip(),
            job_title=job_title.strip() if job_title else None,
            user_id=user_id,
        )
    except RuntimeError as exc:
        # Missing key, rate limit, provider down, timeout
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        # Bad extension, empty resume, text too long, malformed Gemini response
        raise HTTPException(status_code=422, detail=str(exc))

@router.get("/analyses", response_model=list[AnalysisResponse])
def list_user_analyses(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve analyses created by the authenticated user.
    Each user only sees their own analyses.
    """
    records = (
        db.query(Analysis)
        .filter(Analysis.user_id == current_user.id)
        .order_by(Analysis.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [_record_to_response(r) for r in records]

@router.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Retrieve a previously saved analysis by ID.
    If the analysis belongs to a user, verifies the requesting user is the owner.
    """
    try:
        uid = uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid analysis ID format.")

    record = db.get(Analysis, uid)
    if record is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    # Authorization check: If record has a user, only that user may view it
    if record.user_id is not None:
        if not current_user or current_user.id != record.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this analysis."
            )

    return _record_to_response(record)

@router.delete("/analyses/{analysis_id}")
def delete_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete an analysis belonging to the authenticated user.
    """
    try:
        uid = uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid analysis ID format.")

    record = db.get(Analysis, uid)
    if record is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    if record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this analysis."
        )

    db.delete(record)
    db.commit()
    return {"deleted": True, "id": analysis_id}
