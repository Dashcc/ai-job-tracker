from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from .db import Base, engine, SessionLocal
from . import models  # noqa: F401
from . import schemas, crud

import os
from .scoring import load_skills, compute_priority

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Job Tracker")
SKILLS_PATH = os.path.join(os.path.dirname(__file__), "skills.txt")
SKILLS_TEXT = load_skills(SKILLS_PATH)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/applications", response_model=schemas.JobApplicationOut)
def create_application(payload: schemas.JobApplicationCreate, db: Session = Depends(get_db)):
    return crud.create_application(db, payload)

@app.get("/applications", response_model=list[schemas.JobApplicationScored])
def list_applications(db: Session = Depends(get_db)):
    rows = crud.list_applications(db)
    scored = []
    for r in rows:
        s = compute_priority(
            skills_text=SKILLS_TEXT,
            job_text=r.notes,       # for MVP, use notes as “job text”
            deadline=r.deadline,
        )
        scored.append({
            **schemas.JobApplicationOut.model_validate(r).model_dump(),
            "skill_match_score": s.skill_match_score,
            "deadline_urgency_score": s.deadline_urgency_score,
            "priority_score": s.priority_score,
        })
    return scored


@app.get("/applications/{app_id}", response_model=schemas.JobApplicationScored)
def get_application(app_id: int, db: Session = Depends(get_db)):
    r = crud.get_application(db, app_id)
    if not r:
        raise HTTPException(status_code=404, detail="Application not found")

    s = compute_priority(
        skills_text=SKILLS_TEXT,
        job_text=r.notes,
        deadline=r.deadline,
    )
    return {
        **schemas.JobApplicationOut.model_validate(r).model_dump(),
        "skill_match_score": s.skill_match_score,
        "deadline_urgency_score": s.deadline_urgency_score,
        "priority_score": s.priority_score,
    }


@app.put("/applications/{app_id}", response_model=schemas.JobApplicationOut)
def update_application(app_id: int, payload: schemas.JobApplicationUpdate, db: Session = Depends(get_db)):
    updated = crud.update_application(db, app_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Application not found")
    return updated

@app.delete("/applications/{app_id}")
def delete_application(app_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_application(db, app_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"deleted": True}
