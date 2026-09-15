import os
import shutil
from typing import List

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from . import models, schemas, auth, rag, matching, related_papers, export as export_module
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Research AI Platform API")

@app.on_event("startup")
def preload_rag_model():
    rag.get_embedder()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_or_create_skill(db: Session, name: str) -> models.Skill:
    name = name.strip()
    skill = db.query(models.Skill).filter(models.Skill.name.ilike(name)).first()
    if not skill:
        skill = models.Skill(name=name)
        db.add(skill)
        db.flush()
    return skill


def get_or_create_interest(db: Session, name: str) -> models.Interest:
    name = name.strip()
    interest = db.query(models.Interest).filter(models.Interest.name.ilike(name)).first()
    if not interest:
        interest = models.Interest(name=name)
        db.add(interest)
        db.flush()
    return interest


def user_to_out(user: models.User) -> schemas.UserOut:
    return schemas.UserOut(
        id=user.id, name=user.name, email=user.email,
        education=user.education, bio=user.bio,
        skills=[s.name for s in user.skills],
        interests=[i.name for i in user.interests],
    )


def paper_sample_text(paper: models.Paper) -> str:
    """Pull a representative sample of the paper's text (first ~6000 chars)
    for prompts that need the whole document rather than a retrieved slice
    (summarize / gap-finding / idea generation)."""
    pages = rag.extract_text_by_page(paper.file_path)
    full_text = "\n".join(pages)
    return full_text[:6000]


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.post("/auth/register", response_model=schemas.Token)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        name=payload.name,
        email=payload.email,
        hashed_password=auth.hash_password(payload.password),
        education=payload.education or "",
        bio=payload.bio or "",
    )
    for skill_name in payload.skills or []:
        user.skills.append(get_or_create_skill(db, skill_name))
    for interest_name in payload.interests or []:
        user.interests.append(get_or_create_interest(db, interest_name))

    db.add(user)
    db.commit()
    db.refresh(user)

    token = auth.create_access_token({"sub": str(user.id)})
    return schemas.Token(access_token=token, user=user_to_out(user))


@app.post("/auth/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not auth.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = auth.create_access_token({"sub": str(user.id)})
    return schemas.Token(access_token=token, user=user_to_out(user))


@app.get("/auth/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return user_to_out(current_user)


# ---------------------------------------------------------------------------
# Users (browse for matching / directory)
# ---------------------------------------------------------------------------

@app.get("/users", response_model=List[schemas.UserOut])
def list_users(db: Session = Depends(get_db)):
    return [user_to_out(u) for u in db.query(models.User).all()]


# ---------------------------------------------------------------------------
# Papers
# ---------------------------------------------------------------------------

@app.post("/papers/upload", response_model=schemas.PaperOut)
def upload_paper(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    safe_name = f"user{current_user.id}_{file.filename}".replace(" ", "_")
    dest_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    paper = models.Paper(
        user_id=current_user.id,
        title=file.filename.rsplit(".", 1)[0],
        file_path=dest_path,
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)

    # Index into the vector store right away so chat/summarize work immediately.
    try:
        num_chunks = rag.index_paper(paper.id, dest_path)
        paper.num_chunks = num_chunks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {e}")

    db.commit()
    db.refresh(paper)
    return paper


@app.get("/papers", response_model=List[schemas.PaperOut])
def list_papers(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Paper).filter(models.Paper.user_id == current_user.id).all()


@app.get("/papers/{paper_id}", response_model=schemas.PaperOut)
def get_paper(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(models.Paper).filter(models.Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@app.post("/papers/{paper_id}/summarize", response_model=schemas.PaperOut)
def summarize_paper(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(models.Paper).filter(models.Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    sample = paper_sample_text(paper)
    try:
        summary = rag.summarize_paper(paper_id, sample)
    except rag.ollama_client.OllamaError as e:
        raise HTTPException(status_code=503, detail=str(e))

    paper.summary = summary
    db.commit()
    db.refresh(paper)
    return paper


@app.post("/papers/{paper_id}/ask", response_model=schemas.AskResponse)
def ask_paper(paper_id: int, payload: schemas.AskRequest, db: Session = Depends(get_db)):
    paper = db.query(models.Paper).filter(models.Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    try:
        result = rag.answer_question(paper_id, payload.question)
    except rag.ollama_client.OllamaError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return schemas.AskResponse(**result)


@app.get("/papers/{paper_id}/gaps")
def paper_gaps(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(models.Paper).filter(models.Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    sample = paper_sample_text(paper)
    try:
        gaps = rag.identify_research_gaps(sample)
    except rag.ollama_client.OllamaError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"gaps": gaps}


@app.get("/papers/{paper_id}/related", response_model=List[schemas.RelatedPaper])
def paper_related(paper_id: int, db: Session = Depends(get_db)):
    """Related Papers Finder â€” pulls real related papers from arXiv's free API."""
    paper = db.query(models.Paper).filter(models.Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    query = paper.topics if paper.topics else paper.title
    try:
        results = related_papers.search_related_papers(query or paper.title, max_results=6)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return results


@app.post("/papers/compare", response_model=schemas.CompareResponse)
def compare_papers(payload: schemas.CompareRequest, db: Session = Depends(get_db)):
    """Paper Comparison â€” compares 2+ uploaded papers side-by-side."""
    if len(payload.paper_ids) < 2:
        raise HTTPException(status_code=400, detail="Select at least 2 papers to compare")

    papers = []
    for pid in payload.paper_ids:
        paper = db.query(models.Paper).filter(models.Paper.id == pid).first()
        if not paper:
            raise HTTPException(status_code=404, detail=f"Paper {pid} not found")
        papers.append(paper)

    samples = [{"title": p.title, "text": paper_sample_text(p)} for p in papers]
    try:
        result = rag.compare_papers(samples)
    except rag.ollama_client.OllamaError as e:
        raise HTTPException(status_code=503, detail=str(e))

    rows = [
        schemas.ComparisonRow(dimension=r.get("dimension", ""), values=r.get("values", []))
        for r in result.get("rows", [])
    ]
    return schemas.CompareResponse(paper_titles=[p.title for p in papers], rows=rows)


# ---------------------------------------------------------------------------
# Research ideas
# ---------------------------------------------------------------------------

@app.post("/ideas/generate", response_model=List[schemas.ResearchIdeaOut])
def generate_ideas(
    payload: schemas.GenerateIdeasRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    sample = ""
    paper = None
    if payload.paper_id:
        paper = db.query(models.Paper).filter(models.Paper.id == payload.paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        sample = paper_sample_text(paper)

    interests = payload.interests or [i.name for i in current_user.interests]

    try:
        raw_ideas = rag.generate_research_ideas(sample, interests, payload.num_ideas)
    except rag.ollama_client.OllamaError as e:
        raise HTTPException(status_code=503, detail=str(e))

    saved = []
    for idea in raw_ideas:
        record = models.ResearchIdea(
            paper_id=paper.id if paper else None,
            user_id=current_user.id,
            title=idea.get("title", "Untitled idea"),
            problem=idea.get("problem", ""),
            approach=idea.get("approach", ""),
            required_skills_text=", ".join(idea.get("required_skills", [])),
            difficulty=idea.get("difficulty", "Intermediate"),
        )
        db.add(record)
        saved.append(record)

    db.commit()
    for r in saved:
        db.refresh(r)
    return saved


@app.get("/ideas", response_model=List[schemas.ResearchIdeaOut])
def list_ideas(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.ResearchIdea).filter(models.ResearchIdea.user_id == current_user.id).all()


@app.post("/ideas/{idea_id}/build-on", response_model=List[schemas.ResearchIdeaOut])
def build_on_idea(
    idea_id: int,
    payload: schemas.BuildOnIdeaRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Idea Lineage â€” generates follow-up ideas that extend an existing saved idea."""
    parent = db.query(models.ResearchIdea).filter(models.ResearchIdea.id == idea_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Idea not found")

    try:
        raw_ideas = rag.build_on_idea(
            {"title": parent.title, "problem": parent.problem, "approach": parent.approach},
            num_ideas=payload.num_ideas,
        )
    except rag.ollama_client.OllamaError as e:
        raise HTTPException(status_code=503, detail=str(e))

    saved = []
    for idea in raw_ideas:
        record = models.ResearchIdea(
            paper_id=parent.paper_id,
            user_id=current_user.id,
            parent_idea_id=parent.id,
            title=idea.get("title", "Untitled idea"),
            problem=idea.get("problem", ""),
            approach=idea.get("approach", ""),
            required_skills_text=", ".join(idea.get("required_skills", [])),
            difficulty=idea.get("difficulty", "Intermediate"),
        )
        db.add(record)
        saved.append(record)

    db.commit()
    for r in saved:
        db.refresh(r)
    return saved


@app.get("/ideas/{idea_id}/export")
def export_idea(idea_id: int, db: Session = Depends(get_db)):
    """Export to Document â€” downloads a saved idea as a research-proposal PDF."""
    idea = db.query(models.ResearchIdea).filter(models.ResearchIdea.id == idea_id).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    file_path = export_module.export_idea_to_pdf({
        "id": idea.id,
        "title": idea.title,
        "problem": idea.problem,
        "approach": idea.approach,
        "required_skills_text": idea.required_skills_text,
        "difficulty": idea.difficulty,
    })
    return FileResponse(
        file_path, media_type="application/pdf",
        filename=os.path.basename(file_path),
    )


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

@app.post("/match", response_model=List[schemas.MatchResult])
def match_collaborators(
    payload: schemas.MatchRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    results = matching.find_matches_for_skills(
        db,
        required_skills=payload.required_skills,
        exclude_user_id=payload.exclude_user_id or current_user.id,
        top_n=payload.top_n,
    )
    return [
        schemas.MatchResult(
            user_id=r["user_id"], name=r["name"], match_score=r["match_score"],
            matched_skills=r["matched_skills"], missing_skills=r["missing_skills"],
            explanation=r["explanation"],
        )
        for r in results
    ]


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

def project_to_out(project: models.Project) -> schemas.ProjectOut:
    return schemas.ProjectOut(
        id=project.id, title=project.title, description=project.description,
        status=project.status,
        required_skills=[s.name for s in project.required_skills],
        members=[m.name for m in project.members],
    )


@app.post("/projects", response_model=schemas.ProjectOut)
def create_project(
    payload: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    project = models.Project(title=payload.title, description=payload.description)
    for skill_name in payload.required_skills:
        project.required_skills.append(get_or_create_skill(db, skill_name))

    project.members.append(current_user)
    for uid in payload.member_ids:
        member = db.query(models.User).filter(models.User.id == uid).first()
        if member and member.id != current_user.id:
            project.members.append(member)

    db.add(project)
    db.commit()
    db.refresh(project)
    return project_to_out(project)


@app.get("/projects", response_model=List[schemas.ProjectOut])
def list_projects(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return [project_to_out(p) for p in current_user.projects]


@app.get("/")
def root():
    return {"status": "ok", "message": "Research AI Platform API is running"}
