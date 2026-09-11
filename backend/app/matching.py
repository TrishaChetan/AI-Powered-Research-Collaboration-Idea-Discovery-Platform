"""
Researcher <-> project skill matching.

Keeps it simple and explainable rather than a black box: we compute a
weighted overlap between a project's required skills and each user's
skills, with a small semantic-similarity boost (via embeddings) so
near-matches like "Computer Vision" vs "OpenCV" still count for something.
This is far easier to justify to a reviewer than an opaque single score.
"""
from typing import List, Dict
from sqlalchemy.orm import Session
from . import models
from .rag import get_embedder
import numpy as np


def _normalize(skill: str) -> str:
    return skill.strip().lower()


def compute_match_score(required_skills: List[str], user_skills: List[str]) -> Dict:
    """
    Returns a dict with an overall score (0-100), exact matched skills,
    missing skills, and a short human-readable explanation.
    """
    required_norm = [_normalize(s) for s in required_skills]
    user_norm = [_normalize(s) for s in user_skills]

    exact_matches = [s for s in required_norm if s in user_norm]
    missing = [s for s in required_norm if s not in user_norm]

    exact_ratio = len(exact_matches) / len(required_norm) if required_norm else 0.0

    # Semantic boost: for skills that aren't an exact match, see if the user
    # has something conceptually close (cosine similarity on embeddings).
    semantic_bonus = 0.0
    if missing and user_norm:
        embedder = get_embedder()
        missing_emb = embedder.encode(missing)
        user_emb = embedder.encode(user_norm)

        missing_emb = missing_emb / np.linalg.norm(missing_emb, axis=1, keepdims=True)
        user_emb = user_emb / np.linalg.norm(user_emb, axis=1, keepdims=True)
        sims = missing_emb @ user_emb.T  # shape: (missing, user)
        best_per_missing = sims.max(axis=1) if sims.size else np.array([])
        # Only count reasonably strong semantic matches
        semantic_hits = best_per_missing[best_per_missing > 0.55]
        semantic_bonus = (semantic_hits.sum() / len(required_norm)) if required_norm else 0.0

    raw_score = exact_ratio + 0.5 * semantic_bonus
    score = round(min(raw_score, 1.0) * 100, 1)

    if exact_matches:
        explanation = (
            f"Matches {len(exact_matches)} of {len(required_norm)} required skills directly"
        )
        if semantic_bonus > 0:
            explanation += ", plus related experience in the remaining areas."
        else:
            explanation += "."
    elif semantic_bonus > 0:
        explanation = "No exact skill matches, but has related/adjacent experience."
    else:
        explanation = "No matching or closely related skills found."

    return {
        "score": score,
        "matched_skills": exact_matches,
        "missing_skills": missing,
        "explanation": explanation,
    }


def find_matches_for_skills(db: Session, required_skills: List[str],
                             exclude_user_id: int = None, top_n: int = 5) -> List[Dict]:
    users = db.query(models.User).all()
    results = []
    for user in users:
        if exclude_user_id and user.id == exclude_user_id:
            continue
        user_skill_names = [s.name for s in user.skills]
        if not user_skill_names:
            continue
        match = compute_match_score(required_skills, user_skill_names)
        if match["score"] <= 0:
            continue
        results.append({
            "user_id": user.id,
            "name": user.name,
            "match_score": match["score"],
            "matched_skills": match["matched_skills"],
            "missing_skills": match["missing_skills"],
            "explanation": match["explanation"],
        })

    results.sort(key=lambda r: r["match_score"], reverse=True)
    return results[:top_n]
