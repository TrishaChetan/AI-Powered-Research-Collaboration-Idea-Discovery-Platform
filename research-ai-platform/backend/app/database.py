"""
Database connection setup (SQLite via SQLAlchemy).
Swap SQLALCHEMY_DATABASE_URL for a Postgres URL later without changing
any other code, since we only use the ORM layer everywhere else.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./research_platform.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
