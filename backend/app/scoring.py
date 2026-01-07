from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class ScoreResult:
    skill_match_score: float          # 0..1
    deadline_urgency_score: float     # 0..1
    priority_score: int               # 0..100


def load_skills(skills_path: str) -> str:
    """
    Returns a single text blob of skills.
    Keep it simple: one skill per line in skills.txt.
    """
    with open(skills_path, "r", encoding="utf-8") as f:
        skills = [line.strip() for line in f.readlines()]
    skills = [s for s in skills if s]
    return " ".join(skills)


def skill_match_tfidf(skills_text: str, job_text: Optional[str]) -> float:
    """
    TF-IDF cosine similarity between (skills) and (job_text).
    Returns 0 if job_text is missing/empty.
    """
    if not job_text or not job_text.strip():
        return 0.0

    corpus = [skills_text, job_text]
    vec = TfidfVectorizer(stop_words="english")
    X = vec.fit_transform(corpus)
    sim = cosine_similarity(X[0:1], X[1:2])[0][0]
    # numerical safety
    return float(max(0.0, min(1.0, sim)))


def deadline_urgency(deadline: Optional[date], today: Optional[date] = None) -> float:
    """
    Map deadline proximity to 0..1.
    - No deadline => 0
    - Past or today => 1
    - Otherwise: urgency decays with days remaining (simple, explainable).
    """
    if deadline is None:
        return 0.0
    today = today or date.today()
    days_left = (deadline - today).days

    if days_left <= 0:
        return 1.0

    # Simple curve: 1 / (1 + days_left/7)
    # ~0.5 at 7 days, ~0.33 at 14 days, etc.
    score = 1.0 / (1.0 + (days_left / 7.0))
    return float(max(0.0, min(1.0, score)))


def compute_priority(
    skills_text: str,
    job_text: Optional[str],
    deadline: Optional[date],
    w_skill: float = 0.65,
    w_deadline: float = 0.35,
) -> ScoreResult:
    sm = skill_match_tfidf(skills_text, job_text)
    du = deadline_urgency(deadline)

    # weighted 0..1
    combined = (w_skill * sm) + (w_deadline * du)
    priority = int(round(combined * 100))

    return ScoreResult(
        skill_match_score=sm,
        deadline_urgency_score=du,
        priority_score=priority,
    )
