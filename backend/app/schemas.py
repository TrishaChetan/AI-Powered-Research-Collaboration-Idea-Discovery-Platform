from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime


# ---------- Users ----------

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    education: Optional[str] = ""
    bio: Optional[str] = ""
    skills: Optional[List[str]] = []
    interests: Optional[List[str]] = []


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    education: str
    bio: str
    skills: List[str] = []
    interests: List[str] = []

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Papers ----------

class PaperOut(BaseModel):
    id: int
    title: str
    author: str
    year: str
    topics: str
    num_chunks: int
    summary: str
    created_at: datetime

    class Config:
        from_attributes = True


class AskRequest(BaseModel):
    paper_id: int
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: List[dict]


# ---------- Ideas ----------

class ResearchIdeaOut(BaseModel):
    id: int
    title: str
    problem: str
    approach: str
    required_skills_text: str
    difficulty: str
    parent_idea_id: Optional[int] = None

    class Config:
        from_attributes = True


class GenerateIdeasRequest(BaseModel):
    paper_id: Optional[int] = None
    interests: Optional[List[str]] = []
    num_ideas: int = 3


class BuildOnIdeaRequest(BaseModel):
    num_ideas: int = 2


# ---------- Paper comparison ----------

class CompareRequest(BaseModel):
    paper_ids: List[int]


class ComparisonRow(BaseModel):
    dimension: str
    values: List[str]  # one value per paper, same order as paper_ids


class CompareResponse(BaseModel):
    paper_titles: List[str]
    rows: List[ComparisonRow]


# ---------- Related papers (arXiv) ----------

class RelatedPaper(BaseModel):
    title: str
    authors: List[str]
    summary: str
    url: str
    published: str


# ---------- Export ----------

class ExportIdeaRequest(BaseModel):
    idea_id: int


# ---------- Matching ----------

class MatchResult(BaseModel):
    user_id: int
    name: str
    match_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    explanation: str


class MatchRequest(BaseModel):
    required_skills: List[str]
    exclude_user_id: Optional[int] = None
    top_n: int = 5


# ---------- Projects ----------

class ProjectCreate(BaseModel):
    title: str
    description: str
    required_skills: List[str] = []
    member_ids: List[int] = []


class ProjectOut(BaseModel):
    id: int
    title: str
    description: str
    status: str
    required_skills: List[str] = []
    members: List[str] = []

    class Config:
        from_attributes = True
