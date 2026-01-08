# AI Job Tracker (FastAPI)

A lightweight job application tracker that assigns an explainable priority score based on:
1) skill match (TF-IDF similarity), and 2) deadline urgency.

## MVP Features
- Add / edit / delete job applications
- Status tracking: Wishlist / Applied / Interview / Offer / Rejection
- Dashboard UI (FastAPI + Jinja) with filters and sorting
- Explainable priority scoring:
  - `skill_match_score` (0–1)
  - `deadline_urgency_score` (0–1)
  - `priority_score` (0–100)

## Tech Stack
- Python 3.9.6
- FastAPI + Uvicorn
- SQLAlchemy + SQLite
- Jinja2 templates
- scikit-learn (TF-IDF)
- pytest (unit + API tests)

## Architecture (high-level)

Browser (Jinja UI)
   |
   |  HTTP
   v
FastAPI app (routes)
   |
   |  CRUD + scoring
   v
SQLAlchemy (SQLite)  +  Scoring (TF-IDF + deadline urgency)
   |
   v
jobtracker.db

## How Scoring Works
- **Skill match**: TF-IDF cosine similarity between `skills.txt` and job text (stored in `notes`).
- **Deadline urgency**: closer deadline → higher urgency (simple decay function).
- **Priority score**: weighted combination mapped to 0–100.

## Local Setup (Run from backend/)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
