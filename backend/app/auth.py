"""
Minimal JWT-based auth.

The signing key comes from the JWT_SECRET_KEY environment variable. If it
isn't set, a random key is generated once and saved to backend/.jwt_secret
(git-ignored), so logins survive restarts but the key is never in the repo.
Previously the key was hard-coded, which let anyone who read the source
forge a token for any user.
"""
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import models
from .database import get_db

SECRET_FILE = Path(__file__).resolve().parent.parent / ".jwt_secret"


def _load_or_create_secret(path: Path = SECRET_FILE) -> str:
    if path.exists():
        existing = path.read_text().strip()
        if existing:
            return existing
    key = secrets.token_urlsafe(48)
    path.write_text(key)
    try:
        path.chmod(0o600)  # owner-only; no-op on Windows
    except OSError:
        pass
    return key


SECRET_KEY = os.getenv("JWT_SECRET_KEY") or _load_or_create_secret()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week, convenient for a demo

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user
