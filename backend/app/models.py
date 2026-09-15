from sqlalchemy import (
    Column, Integer, String, Float, Text, ForeignKey, DateTime, Table
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# ---------------------------------------------------------------------------
# Association tables (many-to-many)
# ---------------------------------------------------------------------------

user_skills = Table(
    "user_skills",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id"), primary_key=True),
    Column("level", String, default="intermediate"),
)

user_interests = Table(
    "user_interests",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("interest_id", Integer, ForeignKey("interests.id"), primary_key=True),
)

project_required_skills = Table(
    "project_required_skills",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id"), primary_key=True),
)

project_members = Table(
    "project_members",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
)


# ---------------------------------------------------------------------------
# Core entities
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    education = Column(String, default="")
    bio = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    skills = relationship("Skill", secondary=user_skills, back_populates="users")
    interests = relationship("Interest", secondary=user_interests, back_populates="users")
    papers = relationship("Paper", back_populates="owner")
    ideas = relationship("ResearchIdea", back_populates="creator")
    projects = relationship("Project", secondary=project_members, back_populates="members")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    users = relationship("User", secondary=user_skills, back_populates="skills")
    projects = relationship("Project", secondary=project_required_skills, back_populates="required_skills")


class Interest(Base):
    __tablename__ = "interests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    users = relationship("User", secondary=user_interests, back_populates="interests")


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    author = Column(String, default="")
    year = Column(String, default="")
    topics = Column(String, default="")  # comma separated, quick & simple
    num_chunks = Column(Integer, default=0)
    summary = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="papers")
    ideas = relationship("ResearchIdea", back_populates="source_paper")


class ResearchIdea(Base):
    __tablename__ = "research_ideas"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    parent_idea_id = Column(Integer, ForeignKey("research_ideas.id"), nullable=True)
    title = Column(String, nullable=False)
    problem = Column(Text, default="")
    approach = Column(Text, default="")
    required_skills_text = Column(String, default="")  # comma separated
    difficulty = Column(String, default="Intermediate")
    created_at = Column(DateTime, default=datetime.utcnow)

    source_paper = relationship("Paper", back_populates="ideas")
    creator = relationship("User", back_populates="ideas")
    parent_idea = relationship("ResearchIdea", remote_side=[id], backref="child_ideas")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    status = Column(String, default="Planning")
    created_at = Column(DateTime, default=datetime.utcnow)

    required_skills = relationship("Skill", secondary=project_required_skills, back_populates="projects")
    members = relationship("User", secondary=project_members, back_populates="projects")
