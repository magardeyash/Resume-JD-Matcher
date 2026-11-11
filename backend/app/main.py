import sys
from pathlib import Path

# Ensure 'backend' directory is on sys.path so 'app.*' imports work from anywhere
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, FileResponse
from app.api.routes import router as api_router

app = FastAPI(
    title="ResumeMatch",
    description="AI-powered resume and job description matcher.",
    version="1.0.0",
)

# Enable CORS for React frontend (Vite default is http://localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIST = BACKEND_DIR.parent / "frontend" / "dist"

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

app.include_router(api_router)

# Mount React static assets if built
if FRONTEND_DIST.exists() and (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="frontend-assets")

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/results/{analysis_id}", response_class=HTMLResponse)
def results_page(request: Request, analysis_id: str):
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return templates.TemplateResponse(
        "results.html", {"request": request, "analysis_id": analysis_id}
    )

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/history", response_class=HTMLResponse)
def history_page(request: Request):
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return templates.TemplateResponse("history.html", {"request": request})
